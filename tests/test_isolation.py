"""Every route, tried by someone outside the project (Accounts & Voice Identity
spec, D15). A new route must be added to one of the tables below, or
test_every_route_is_listed fails, so a forgotten membership check can't slip in.

Runs against a local database only, e.g. after `supabase start`:
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
Never point this at the Supabase project."""

import os
from datetime import date
from uuid import uuid4

import psycopg
import pytest
from conftest import JWT_SECRET, SUPABASE_URL
from fastapi.testclient import TestClient
from psycopg.types.json import Jsonb

from labsync.db import meetings
from labsync.server import create_app

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")

RECORDING = {"file": ("meeting.wav", b"RIFF-test-audio", "audio/wav")}


def upload_form(ids):
    return {
        "data": {
            "project_id": ids["project_id"],
            "title": "Sneaky upload",
            "meeting_date": "2026-10-01",
            "consent_confirmed": "true",
        },
        "files": RECORDING,
    }


# Routes that act on one project's data. An outsider must get 404 from each.
# Each entry: (method, route path exactly as declared, request options).
PROJECT_ROUTES = [
    ("GET", "/api/v1/projects/{project_id}/meetings", lambda ids: {}),
    ("DELETE", "/api/v1/projects/{project_id}", lambda ids: {}),
    ("GET", "/api/v1/meetings/{meeting_id}", lambda ids: {}),
    ("POST", "/api/v1/meetings/upload", upload_form),
    (
        "GET",
        "/api/v1/tasks",
        lambda ids: {
            "params": {
                "project_id": ids["project_id"],
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
            }
        },
    ),
    (
        "PATCH",
        "/api/v1/tasks/{task_id}/review",
        lambda ids: {"json": {"action": "dismiss"}},
    ),
    ("PATCH", "/api/v1/tasks/{task_id}", lambda ids: {"json": {"title": "Hijacked"}}),
    ("POST", "/api/v1/tasks/{task_id}/state", lambda ids: {"json": {"state": "done"}}),
    ("POST", "/api/v1/tasks/revert/{revert_token}", lambda ids: {}),
    (
        "POST",
        "/api/v1/conversations",
        lambda ids: {"json": {"project_id": ids["project_id"]}},
    ),
    ("GET", "/api/v1/conversations/{conversation_id}", lambda ids: {}),
    (
        "POST",
        "/api/v1/conversations/{conversation_id}/messages",
        lambda ids: {"json": {"content": "What did they decide?"}},
    ),
    ("GET", "/api/meetings/{meeting_id}", lambda ids: {}),
    ("GET", "/api/meetings/{meeting_id}/audio", lambda ids: {}),
    ("POST", "/api/meetings/{meeting_id}/retry", lambda ids: {}),
    ("DELETE", "/api/projects/{project_id}/meetings", lambda ids: {}),
    (
        "POST",
        "/api/v1/projects/{project_id}/invitations",
        lambda ids: {"json": {"email": "eve@example.com"}},
    ),
    ("GET", "/api/v1/projects/{project_id}/invitations", lambda ids: {}),
    ("GET", "/api/v1/projects/{project_id}/members", lambda ids: {}),
    ("DELETE", "/api/v1/projects/{project_id}/members/{member_id}", lambda ids: {}),
    (
        "DELETE",
        "/api/v1/projects/{project_id}/invitations/{invitation_id}",
        lambda ids: {},
    ),
    ("POST", "/api/v1/invitations/{invitation_id}/accept", lambda ids: {}),
    ("POST", "/api/v1/invitations/{invitation_id}/decline", lambda ids: {}),
    (
        "POST",
        "/api/v1/invitations/accept-token",
        lambda ids: {"json": {"token": "not-a-real-token"}},
    ),
]

# Routes that only ever show the caller's own data, so they answer an outsider
# with 200 and nothing of the project's. Checked one by one below.
OWN_DATA_ROUTES = [
    ("GET", "/api/v1/me"),
    ("PATCH", "/api/v1/me"),
    ("POST", "/api/v1/me/onboarding/complete"),
    ("GET", "/api/v1/me/tasks/summary"),
    ("GET", "/api/v1/me/voice"),
    ("POST", "/api/v1/me/voice-consent"),
    ("DELETE", "/api/v1/me/voice-consent"),
    ("POST", "/api/v1/me/voice-enrollments"),
    ("DELETE", "/api/v1/me"),
    ("GET", "/api/v1/projects"),
    ("GET", "/api/v1/projects/events"),  # nudges about the caller's own projects
    ("POST", "/api/v1/projects"),
    ("GET", "/api/v1/conversations"),
    ("GET", "/api/v1/invitations"),
]

PUBLIC_ROUTES = [("GET", "/api/health")]


@pytest.fixture
def app(tmp_path, embedder):
    return create_app(
        tmp_path,
        tmp_path,
        database_url=DATABASE_URL,
        embedder=embedder,
        supabase_url=SUPABASE_URL,
        jwt_secret=JWT_SECRET,
    )


@pytest.fixture
def seeded(make_user):
    """Alice's project with a meeting, a task with an undo token, and a chat.
    Bob is signed in but belongs to nothing."""
    alice_id, alice = make_user("Alice")
    _, bob = make_user("Bob")
    with psycopg.connect(DATABASE_URL) as conn:
        project_id = conn.execute(
            "INSERT INTO projects (name, created_by) VALUES ('pytest isolation', %s) "
            "RETURNING id",
            (alice_id,),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO project_members (project_id, user_id, role) "
            "VALUES (%s, %s, 'owner')",
            (project_id, alice_id),
        )
        meeting_id = str(uuid4())
        meetings.create_meeting(
            conn,
            meeting_id=meeting_id,
            project_id=project_id,
            name="Private sync",
            meeting_date=date(2026, 9, 30),
            audio_file_path="/tmp/recording.wav",
        )
        task_id = conn.execute(
            "INSERT INTO tasks (project_id, meeting_id, title) "
            "VALUES (%s, %s, 'Private task') RETURNING id",
            (project_id, meeting_id),
        ).fetchone()[0]
        revert_token = conn.execute(
            "INSERT INTO task_audit_log (task_id, action, old_value, new_value) "
            "VALUES (%s, 'STATUS_CHANGE', %s, %s) RETURNING revert_token",
            (
                task_id,
                Jsonb({"lifecycle_status": "open"}),
                Jsonb({"lifecycle_status": "done"}),
            ),
        ).fetchone()[0]
        conversation_id = conn.execute(
            "INSERT INTO chat_conversations (project_id, user_id) "
            "VALUES (%s, %s) RETURNING id",
            (project_id, alice_id),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO chat_messages (conversation_id, role, content) "
            "VALUES (%s, 'user', 'A private question')",
            (conversation_id,),
        )
        invitation_id = conn.execute(
            "INSERT INTO project_invitations (project_id, email, token_hash, "
            "expires_at) VALUES (%s, 'carol@example.com', %s, "
            "now() + interval '7 days') RETURNING id",
            (project_id, os.urandom(32)),
        ).fetchone()[0]
    ids = {
        "project_id": str(project_id),
        "meeting_id": meeting_id,
        "task_id": str(task_id),
        "revert_token": str(revert_token),
        "conversation_id": str(conversation_id),
        "invitation_id": str(invitation_id),
        "member_id": str(alice_id),
    }
    yield ids, alice, bob
    with psycopg.connect(DATABASE_URL) as conn:
        # By name, so the project Bob creates in one test goes too.
        conn.execute("DELETE FROM projects WHERE name = 'pytest isolation'")


def test_every_route_is_listed(app):
    # The OpenAPI schema lists every route, including those from routers.
    declared = {
        (method.upper(), path)
        for path, operations in app.openapi()["paths"].items()
        for method in operations
    }
    listed = {(method, path) for method, path, _ in PROJECT_ROUTES}
    listed |= set(OWN_DATA_ROUTES) | set(PUBLIC_ROUTES)
    assert declared - listed == set(), "add the new route to a table in this file"
    assert listed - declared == set(), "remove routes that no longer exist"


def test_outsiders_get_not_found_and_change_nothing(app, seeded):
    ids, alice, bob = seeded
    with TestClient(app) as client:
        for method, path, options in PROJECT_ROUTES:
            url = path.format(**ids)
            response = client.request(method, url, headers=bob, **options(ids))
            assert response.status_code == 404, f"{method} {path}: {response.text}"

        # Alice still has everything, untouched.
        meeting = client.get(f"/api/v1/meetings/{ids['meeting_id']}", headers=alice)
        assert meeting.status_code == 200
        [task] = meeting.json()["tasks"]
        assert task["review_status"] == "pending"  # Bob's dismiss didn't land
        chat = client.get(
            f"/api/v1/conversations/{ids['conversation_id']}", headers=alice
        )
        assert len(chat.json()["messages"]) == 1
        invites = client.get(
            f"/api/v1/projects/{ids['project_id']}/invitations", headers=alice
        )
        assert len(invites.json()) == 1  # Bob's revoke didn't land


def test_own_data_routes_show_outsiders_nothing(app, seeded):
    ids, _, bob = seeded
    with TestClient(app, headers=bob) as client:
        assert client.get("/api/v1/me").json()["display_name"] == "Bob"
        renamed = client.patch("/api/v1/me", json={"display_name": "Bobby"})
        assert renamed.json()["display_name"] == "Bobby"
        projects = client.get("/api/v1/projects").json()
        assert ids["project_id"] not in [p["id"] for p in projects]
        assert client.get("/api/v1/conversations").json() == []
        assert client.get("/api/v1/invitations").json() == []
        summary = client.get("/api/v1/me/tasks/summary").json()
        assert summary == {"open": 0, "overdue": 0, "done": 0}
        created = client.post("/api/v1/projects", json={"name": "pytest isolation"})
        assert created.status_code == 201  # Bob's own new project, not Alice's


def test_every_route_needs_a_token(app, seeded):
    ids, _, _ = seeded
    routes = [(method, path, options) for method, path, options in PROJECT_ROUTES]
    routes += [(method, path, lambda ids: {}) for method, path in OWN_DATA_ROUTES]
    with TestClient(app) as client:
        for method, path, options in routes:
            response = client.request(method, path.format(**ids), **options(ids))
            assert response.status_code == 401, f"{method} {path}"
        assert client.get("/api/health").status_code == 200


def test_project_data_waits_for_onboarding(app, seeded, make_user):
    """FR-ONB-3: until onboarding is complete, only the /me routes answer."""
    ids, _, _ = seeded
    _, newcomer = make_user("Newcomer", onboarded=False)
    routes = [(method, path, options) for method, path, options in PROJECT_ROUTES]
    routes += [
        (method, path, lambda ids: {})
        for method, path in OWN_DATA_ROUTES
        if not path.startswith("/api/v1/me")
    ]
    with TestClient(app, headers=newcomer) as client:
        for method, path, options in routes:
            response = client.request(method, path.format(**ids), **options(ids))
            assert response.status_code == 403, f"{method} {path}"
            assert response.json()["detail"] == "onboarding_incomplete"
        assert client.get("/api/v1/me").json()["onboarding_step"] == "needs_voice"
        done = client.post(
            "/api/v1/me/onboarding/complete", json={"voice_step": "skipped"}
        )
        assert done.json()["onboarding_step"] == "complete"
        assert client.get("/api/v1/projects").status_code == 200
