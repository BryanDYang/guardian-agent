"""Reviewed continuity requires evidence and stable task IDs."""

from datetime import date
from uuid import uuid4

import psycopg
import pytest
from psycopg.rows import dict_row
from test_api_tasks import DATABASE_URL, approve, calendar
from test_api_tasks import client as task_client
from test_api_tasks import seeded as task_seeded

pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")


@pytest.fixture
def seeded(make_user):
    yield from task_seeded.__wrapped__(make_user)


@pytest.fixture
def client(tmp_path, seeded):
    yield from task_client.__wrapped__(tmp_path, seeded)


@pytest.fixture
def sequence(client, seeded):
    target = seeded["Share the recording"]
    source = seeded["Follow up on cloud access"]
    accepted = approve(client, target)["task"]
    meeting = uuid4()
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        original = conn.execute(
            "SELECT meeting_id FROM tasks WHERE id = %s", (target,)
        ).fetchone()["meeting_id"]
        conn.execute(
            "INSERT INTO meetings (id, project_id, name, meeting_date, status) VALUES "
            "(%s,%s,'Later meeting',%s,'completed')",
            (meeting, seeded["project_id"], date(2026, 10, 3)),
        )
        conn.execute(
            "UPDATE tasks SET meeting_id = %s WHERE id = %s", (meeting, source)
        )
        conn.execute(
            "INSERT INTO meeting_transcripts (meeting_id, turn_key, speaker_label, "
            "content, start_time_ms, end_time_ms, turn_order) VALUES "
            "(%s,'later:0','SPEAKER_01','The recording is complete. Its deadline "
            "moved to October 9.',1000,4000,0)",
            (meeting,),
        )
    return {
        "source": source,
        "target": target,
        "original": original,
        "body": {
            "target_task_id": target,
            "action": "duplicate",
            "expected_updated_at": accepted["updated_at"],
            "transcript_id": "later:0",
            "quote": "The recording is complete.",
        },
    }


@pytest.mark.parametrize("action", ["duplicate", "deadline", "complete"])
def test_reviewed_continuity(client, seeded, sequence, action):
    body = sequence["body"] | {"action": action}
    if action == "deadline":
        body |= {"due_date": "2026-10-09", "quote": "Its deadline moved to October 9."}
    response = client.post(f"/api/v1/tasks/{sequence['source']}/reconcile", json=body)
    assert response.status_code == 200, response.text
    task = response.json()["task"]
    assert task["id"] == sequence["target"]
    assert task["meeting_id"] == str(sequence["original"])
    assert task["lifecycle_status"] == ("done" if action == "complete" else "open")
    assert task["due_date"] == ("2026-10-09" if action == "deadline" else "2026-10-02")
    assert (
        len(
            client.get(
                "/api/v1/tasks/accepted", params={"project_id": seeded["project_id"]}
            ).json()
        )
        == 1
    )
    assert (
        client.post(
            f"/api/v1/tasks/{sequence['source']}/reconcile", json=body
        ).status_code
        == 409
    )
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        audit = conn.execute(
            "SELECT * FROM task_audit_log WHERE task_id = %s", (sequence["target"],)
        ).fetchone()
        assert audit["actor_id"] == seeded["member_id"]
        assert audit["new_value"]["quote"] == body["quote"]
        assert audit["new_value"]["timestamp_ms"] == 1000


def test_uncertainty_stale_and_access_do_not_mutate(client, seeded, sequence):
    url = f"/api/v1/tasks/{sequence['source']}/reconcile"
    body = sequence["body"]
    assert client.post(url, json=body, headers=seeded["outsider"]).status_code == 404
    assert client.post(url, json=body | {"quote": "invented"}).status_code == 400
    assert client.post(url, json=body | {"action": "deadline"}).status_code == 400
    assert (
        client.post(
            url, json=body | {"expected_updated_at": "2020-01-01T00:00:00Z"}
        ).status_code
        == 409
    )
    task = calendar(client, seeded["project_id"]).json()[0]
    assert task["due_date"] == "2026-10-02" and task["lifecycle_status"] == "open"


def test_user_completed_task_does_not_reopen(client, sequence):
    done = client.post(
        f"/api/v1/tasks/{sequence['target']}/state", json={"state": "done"}
    ).json()
    body = sequence["body"] | {
        "expected_updated_at": done["task"]["updated_at"],
        "action": "deadline",
        "due_date": "2026-10-09",
    }
    assert (
        client.post(
            f"/api/v1/tasks/{sequence['source']}/reconcile", json=body
        ).status_code
        == 409
    )
