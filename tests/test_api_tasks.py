"""Runs against a local database only, e.g. after `supabase start`:
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
Never point this at the Supabase project."""

import os
from datetime import date
from uuid import uuid4

import psycopg
import pytest
from conftest import JWT_SECRET, SUPABASE_URL
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from labsync.db import meetings
from labsync.extraction import Transcript
from labsync.server import create_app

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")


@pytest.fixture
def seeded(make_user):
    """One meeting with two extracted tasks, neither with a due date, plus a
    project member and a signed-in outsider."""
    member_id, member = make_user("Member")
    outsider_id, outsider = make_user("Outsider")
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        project_id = conn.execute(
            "INSERT INTO projects (name) VALUES ('pytest tasks') RETURNING id"
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO project_members (project_id, user_id, role) "
            "VALUES (%s, %s, 'member')",
            (project_id, member_id),
        )
        meeting_id = str(uuid4())
        meetings.create_meeting(
            conn,
            meeting_id=meeting_id,
            project_id=project_id,
            name="TA check-in",
            meeting_date=date(2026, 9, 25),
            audio_file_path="/tmp/recording.mp3",
        )
        turn = f"{meeting_id}:turn:0"
        transcript = Transcript.model_validate(
            {
                "project_id": str(project_id),
                "meeting_id": meeting_id,
                "turns": [
                    {
                        "id": turn,
                        "speaker": "SPEAKER_01",
                        "start_time_ms": 0,
                        "end_time_ms": 900,
                        "content": "I will share the recording and follow up.",
                    }
                ],
            }
        )
        commitments = [
            {
                "title": title,
                "owner": "SPEAKER_01",
                "due_date_text": None,
                "evidence": [{"transcript_id": turn, "quote": quote}],
            }
            for title, quote in [
                ("Share the recording", "share the recording"),
                ("Follow up on cloud access", "follow up"),
            ]
        ]
        extraction = {
            "summary": "",
            "decisions": [],
            "commitments": commitments,
            "suggestions": [],
        }
        meetings.save_results(
            conn, meeting_id, transcript, {"extraction": extraction}, {}
        )
        ids = {
            row["title"]: str(row["id"])
            for row in conn.execute(
                "SELECT id, title FROM tasks WHERE meeting_id = %s", (meeting_id,)
            )
        }
    yield {
        "project_id": str(project_id),
        "member_id": member_id,
        "member": member,
        "outsider_id": outsider_id,
        "outsider": outsider,
        **ids,
    }
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("DELETE FROM projects WHERE name = 'pytest tasks'")


@pytest.fixture
def client(tmp_path, seeded):
    """Sends the project member's token unless a test passes other headers."""
    app = create_app(
        tmp_path,
        tmp_path,
        database_url=DATABASE_URL,
        supabase_url=SUPABASE_URL,
        jwt_secret=JWT_SECRET,
    )
    with TestClient(app, headers=seeded["member"]) as client:
        yield client


def review(client, task_id, headers=None, **body):
    url = f"/api/v1/tasks/{task_id}/review"
    return client.patch(url, json=body, headers=headers)


def calendar(client, project_id, start="2026-10-01", end="2026-10-31", headers=None):
    params = {"project_id": project_id, "start_date": start, "end_date": end}
    return client.get("/api/v1/tasks", params=params, headers=headers)


def approve(client, task_id, due_date="2026-10-02"):
    response = review(client, task_id, action="approve", due_date=due_date)
    assert response.status_code == 200
    return response.json()


def test_approval_requires_a_due_date(client, seeded):
    task_id = seeded["Share the recording"]
    response = review(client, task_id, action="approve")
    assert response.status_code == 422
    assert "due date" in response.json()["detail"]
    assert calendar(client, seeded["project_id"]).json() == []

    body = approve(client, task_id)
    assert body["task"]["review_status"] == "approved"
    assert body["eventkit"] == {
        "title": "Share the recording",
        "due_date": "2026-10-02",
    }


def test_calendar_shows_only_approved_tasks_in_range(client, seeded):
    approve(client, seeded["Share the recording"], "2026-10-02")
    review(
        client,
        seeded["Follow up on cloud access"],
        action="edit",
        due_date="2026-10-05",
    )
    october = calendar(client, seeded["project_id"]).json()
    assert [t["title"] for t in october] == ["Share the recording"]
    november = calendar(client, seeded["project_id"], "2026-11-01", "2026-11-30")
    assert november.json() == []


def test_edit_can_clear_a_due_date(client, seeded):
    task_id = seeded["Follow up on cloud access"]
    review(client, task_id, action="edit", due_date="2026-10-05")
    kept = review(client, task_id, action="edit", title="Follow up on cloud access")
    assert kept.json()["task"]["due_date"] == "2026-10-05"
    cleared = review(client, task_id, action="edit", due_date=None)
    assert cleared.status_code == 200
    assert cleared.json()["task"]["due_date"] is None


def test_edit_then_dismiss(client, seeded):
    task_id = seeded["Follow up on cloud access"]
    edited = review(client, task_id, action="edit", title=" Follow up on AWS access ")
    assert edited.json()["task"]["title"] == "Follow up on AWS access"
    assert edited.json()["task"]["review_status"] == "pending"
    assert review(client, task_id, action="edit", title="  ").status_code == 400
    assert (
        review(client, task_id, action="dismiss").json()["task"]["review_status"]
        == "dismissed"
    )
    assert (
        review(client, task_id, action="approve", due_date="2026-10-02").status_code
        == 409
    )


def test_state_changes_and_undo(client, seeded):
    task_id = seeded["Share the recording"]
    url = f"/api/v1/tasks/{task_id}/state"
    assert client.post(url, json={"state": "done"}).status_code == 409
    approve(client, task_id)

    done = client.post(url, json={"state": "done"}).json()
    assert done["task"]["lifecycle_status"] == "done"
    assert client.post(url, json={"state": "done"}).status_code == 409

    undo = client.post(f"/api/v1/tasks/revert/{done['revert_token']}")
    assert undo.status_code == 200
    assert undo.json()["task"]["lifecycle_status"] == "open"
    again = client.post(f"/api/v1/tasks/revert/{done['revert_token']}")
    assert again.status_code == 409  # only the most recent change can be undone
    redo = client.post(f"/api/v1/tasks/revert/{undo.json()['revert_token']}")
    assert redo.json()["task"]["lifecycle_status"] == "done"

    with psycopg.connect(DATABASE_URL) as conn:
        actions = conn.execute(
            "SELECT action FROM task_audit_log WHERE task_id = %s ORDER BY created_at",
            (task_id,),
        ).fetchall()
    assert [a[0] for a in actions] == ["STATUS_CHANGE", "REVERT", "REVERT"]


def test_errors(client, seeded):
    unknown = "00000000-0000-0000-0000-000000000000"
    assert review(client, unknown, action="edit").status_code == 404
    assert client.post(f"/api/v1/tasks/revert/{unknown}").status_code == 404
    assert (
        review(client, seeded["Share the recording"], action="archive").status_code
        == 422
    )
    assert (
        calendar(client, seeded["project_id"], "2026-10-31", "2026-10-01").status_code
        == 400
    )
    assert calendar(client, unknown).status_code == 404
    bad_assignee = review(
        client, seeded["Share the recording"], action="edit", assignee_user_id=unknown
    )
    assert bad_assignee.status_code == 400


def summary(client):
    return client.get("/api/v1/me/tasks/summary").json()


def test_assigning_to_me_counts_in_my_task_summary(client, seeded):
    task_id = seeded["Share the recording"]
    assert summary(client) == {"open": 0, "overdue": 0, "done": 0}
    mine = review(
        client, task_id, action="edit", assignee_user_id=str(seeded["member_id"])
    ).json()["task"]
    assert mine["assignee_user_id"] == str(seeded["member_id"])
    assert mine["assignee_name"] == "Member"
    assert mine["owner_label"] is None  # a member replaces the speaker label
    assert summary(client)["open"] == 0  # pending tasks don't count yet
    approve(client, task_id, "2099-01-01")  # never overdue, whatever today is
    assert summary(client) == {"open": 1, "overdue": 0, "done": 0}


def test_assign_to_a_speaker_or_nobody(client, seeded):
    task_id = seeded["Share the recording"]
    speaker = review(client, task_id, action="edit", owner_label="SPEAKER_01")
    assert speaker.json()["task"]["owner_label"] == "SPEAKER_01"
    assert speaker.json()["task"]["assignee_user_id"] is None

    for bad in [
        {"owner_label": "SPEAKER_09"},  # not in this meeting
        {"owner_label": "UNKNOWN"},
        {"assignee_user_id": str(seeded["outsider_id"])},  # not a project member
        {"assignee_user_id": str(seeded["member_id"]), "owner_label": "SPEAKER_01"},
    ]:
        assert review(client, task_id, action="edit", **bad).status_code == 400, bad

    # Leaving both fields out keeps the assignee; nulls clear it.
    kept = review(client, task_id, action="edit", title="Share the recording")
    assert kept.json()["task"]["owner_label"] == "SPEAKER_01"
    nobody = review(
        client, task_id, action="edit", assignee_user_id=None, owner_label=None
    ).json()["task"]
    assert (nobody["assignee_user_id"], nobody["owner_label"]) == (None, None)


def test_edit_an_approved_task(client, seeded):
    task_id = seeded["Share the recording"]
    url = f"/api/v1/tasks/{task_id}"
    assert client.patch(url, json={"title": "Too early"}).status_code == 409
    approve(client, task_id, "2026-10-02")

    edited = client.patch(
        url,
        json={
            "title": " Share the edited recording ",
            "due_date": "2026-10-09",
            "assignee_user_id": str(seeded["member_id"]),
        },
    )
    assert edited.status_code == 200
    task = edited.json()["task"]
    assert task["title"] == "Share the edited recording"
    assert task["due_date"] == "2026-10-09"
    assert task["review_status"] == "approved"
    assert task["lifecycle_status"] == "open"
    assert task["meeting_name"] == "TA check-in"
    assert task["quote"] == "share the recording"
    assert task["timestamp_ms"] == 0
    assert summary(client)["open"] == 1

    assert client.patch(url, json={"due_date": None}).status_code == 422
    assert client.patch(url, json={"title": "  "}).status_code == 400
    assert client.patch(url, json={"owner_label": "SPEAKER_09"}).status_code == 400
    outsider = client.patch(url, json={"title": "x"}, headers=seeded["outsider"])
    assert outsider.status_code == 404
    [listed] = calendar(client, seeded["project_id"]).json()
    assert listed["title"] == "Share the edited recording"
    assert listed["due_date"] == "2026-10-09"


def test_removed_member_tasks_become_unassigned(client, seeded, make_user):
    owner_id, owner = make_user("Owner")
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "INSERT INTO project_members (project_id, user_id, role) "
            "VALUES (%s, %s, 'owner')",
            (seeded["project_id"], owner_id),
        )
    task_id = seeded["Share the recording"]
    review(client, task_id, action="edit", assignee_user_id=str(seeded["member_id"]))
    approve(client, task_id)

    url = f"/api/v1/projects/{seeded['project_id']}/members/{seeded['member_id']}"
    removed = client.delete(url, headers=owner)
    assert removed.json() == {"removed": 1, "unassigned_tasks": 1}
    [task] = calendar(client, seeded["project_id"], headers=owner).json()
    assert (task["assignee_user_id"], task["owner_label"]) == (None, None)
    assert task["review_status"] == "approved"


def test_approver_and_actor_are_recorded(client, seeded):
    task_id = seeded["Share the recording"]
    approve(client, task_id)
    done = client.post(f"/api/v1/tasks/{task_id}/state", json={"state": "done"})
    client.post(f"/api/v1/tasks/revert/{done.json()['revert_token']}")
    with psycopg.connect(DATABASE_URL) as conn:
        approved = conn.execute(
            "SELECT approved_by, approved_at IS NOT NULL FROM tasks WHERE id = %s",
            (task_id,),
        ).fetchone()
        actors = conn.execute(
            "SELECT actor_id FROM task_audit_log WHERE task_id = %s", (task_id,)
        ).fetchall()
    assert approved == (seeded["member_id"], True)
    assert [a[0] for a in actors] == [seeded["member_id"]] * 2


def test_outsiders_cannot_see_or_change_tasks(client, seeded):
    task_id = seeded["Share the recording"]
    approve(client, task_id)
    token = client.post(
        f"/api/v1/tasks/{task_id}/state", json={"state": "done"}
    ).json()["revert_token"]

    outsider = seeded["outsider"]
    assert calendar(client, seeded["project_id"], headers=outsider).status_code == 404
    assert review(client, task_id, outsider, action="edit").status_code == 404
    state = client.post(
        f"/api/v1/tasks/{task_id}/state", json={"state": "open"}, headers=outsider
    )
    assert state.status_code == 404
    undo = client.post(f"/api/v1/tasks/revert/{token}", headers=outsider)
    assert undo.status_code == 404

    # Nothing the outsider tried went through.
    [task] = calendar(client, seeded["project_id"]).json()
    assert task["lifecycle_status"] == "done"
    no_token = {"Authorization": ""}
    assert calendar(client, seeded["project_id"], headers=no_token).status_code == 401
