"""Account deletion and the Profile task summary (Accounts & Voice Identity
spec, FR-ACCT and FR-PROF-3).

Runs against a local database only, e.g. after `supabase start`:
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
Never point this at the Supabase project."""

import json
import os
from datetime import date, timedelta
from uuid import uuid4

import psycopg
import pytest
from conftest import JWT_SECRET, SUPABASE_URL
from fastapi.testclient import TestClient

from labsync.db import meetings
from labsync.server import create_app

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")


def query(sql, *params):
    with psycopg.connect(DATABASE_URL) as conn:
        return conn.execute(sql, params).fetchone()


@pytest.fixture
def client(tmp_path):
    app = create_app(
        tmp_path,
        tmp_path,
        database_url=DATABASE_URL,
        supabase_url=SUPABASE_URL,
        jwt_secret=JWT_SECRET,
    )
    with TestClient(app) as client:
        yield client
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("DELETE FROM projects WHERE name LIKE 'pytest account%'")


def add_project(name, *member_ids):
    with psycopg.connect(DATABASE_URL) as conn:
        project_id = conn.execute(
            "INSERT INTO projects (name) VALUES (%s) RETURNING id", (name,)
        ).fetchone()[0]
        for user_id in member_ids:
            conn.execute(
                "INSERT INTO project_members (project_id, user_id, role) "
                "VALUES (%s, %s, 'member')",
                (project_id, user_id),
            )
    return project_id


def add_meeting(storage, project_id, uploaded_by, status="completed"):
    """A meeting row plus its folder on disk, the way an upload leaves them."""
    meeting_id = str(uuid4())
    with psycopg.connect(DATABASE_URL) as conn:
        meetings.create_meeting(
            conn,
            meeting_id=meeting_id,
            project_id=project_id,
            name="pytest meeting",
            meeting_date=date(2026, 9, 30),
            audio_file_path="/tmp/recording.wav",
            uploaded_by=uploaded_by,
        )
        conn.execute(
            "UPDATE meetings SET status = %s WHERE id = %s", (status, meeting_id)
        )
    folder = storage / meeting_id
    folder.mkdir()
    record = {"id": meeting_id, "project": str(project_id), "status": status}
    (folder / "meeting.json").write_text(json.dumps(record))
    return meeting_id


def test_deleting_an_account(client, make_user, tmp_path):
    alice_id, alice = make_user("Alice")
    bob_id, bob = make_user("Bob")
    solo = add_project("pytest account solo", alice_id)
    shared = add_project("pytest account shared", alice_id, bob_id)
    solo_meeting = add_meeting(tmp_path, solo, alice_id)
    shared_meeting = add_meeting(tmp_path, shared, alice_id)
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "INSERT INTO chat_conversations (project_id, user_id) VALUES (%s, %s)",
            (shared, alice_id),
        )
        conn.execute(
            "INSERT INTO project_invitations (project_id, email, token_hash, "
            "invited_by, expires_at) VALUES (%s, 'pending@example.com', %s, %s, "
            "now() + interval '7 days')",
            (shared, os.urandom(32), alice_id),
        )

    response = client.delete("/api/v1/me", headers=alice)
    assert response.status_code == 200
    assert response.json() == {"deleted_projects": 1}

    # The project only Alice was in is gone, recording included (FR-ACCT-3).
    assert query("SELECT 1 FROM projects WHERE id = %s", solo) is None
    assert not (tmp_path / solo_meeting).exists()
    # The shared project keeps its meeting, now from a former member (FR-ACCT-5).
    assert query("SELECT uploaded_by FROM meetings WHERE id = %s", shared_meeting) == (
        None,
    )
    assert (tmp_path / shared_meeting).exists()
    projects = client.get("/api/v1/projects", headers=bob).json()
    assert [p["member_count"] for p in projects if p["id"] == str(shared)] == [1]
    # Her account, chats, and pending invitations are gone (FR-ACCT-4).
    assert query("SELECT 1 FROM auth.users WHERE id = %s", alice_id) is None
    assert (
        query("SELECT 1 FROM chat_conversations WHERE user_id = %s", alice_id) is None
    )
    assert (
        query("SELECT 1 FROM project_invitations WHERE project_id = %s", shared) is None
    )
    # Her old token no longer works.
    assert client.get("/api/v1/me", headers=alice).status_code == 401


def test_deletion_waits_for_processing(client, make_user, tmp_path):
    alice_id, alice = make_user("Alice")
    solo = add_project("pytest account busy", alice_id)
    add_meeting(tmp_path, solo, alice_id, status="transcribing")
    assert client.delete("/api/v1/me", headers=alice).status_code == 409
    assert query("SELECT 1 FROM auth.users WHERE id = %s", alice_id) == (1,)
    assert query("SELECT 1 FROM projects WHERE id = %s", solo) == (1,)


def test_task_summary_counts_my_approved_tasks(client, make_user):
    alice_id, alice = make_user("Alice")
    mine = add_project("pytest account tasks", alice_id)
    left = add_project("pytest account left")  # Alice is no longer a member
    today = date.today()
    tasks = [
        (mine, "approved", "open", today - timedelta(days=1)),  # open, overdue
        (mine, "approved", "open", today + timedelta(days=3)),  # open
        (mine, "approved", "done", today),  # done
        (mine, "pending", "open", today),  # not approved yet
        (left, "approved", "open", today),  # not her project anymore
    ]
    with psycopg.connect(DATABASE_URL) as conn:
        for project_id, review, lifecycle, due in tasks:
            conn.execute(
                "INSERT INTO tasks (project_id, title, review_status, "
                "lifecycle_status, due_date, assignee_user_id) "
                "VALUES (%s, 'pytest task', %s, %s, %s, %s)",
                (project_id, review, lifecycle, due, alice_id),
            )
        conn.execute(
            "INSERT INTO tasks (project_id, title, review_status, due_date) "
            "VALUES (%s, 'unassigned', 'approved', %s)",
            (mine, today),
        )
    summary = client.get("/api/v1/me/tasks/summary", headers=alice).json()
    assert summary == {"open": 2, "overdue": 1, "done": 1}
