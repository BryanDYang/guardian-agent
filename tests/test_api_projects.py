"""Runs against a local database only, e.g. after `supabase start`:
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
Never point this at the Supabase project."""

import os
import uuid

import psycopg
import pytest
from conftest import JWT_SECRET, SUPABASE_URL
from fastapi.testclient import TestClient

from labsync.server import create_app

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")


@pytest.fixture
def client(tmp_path):
    app = create_app(
        tmp_path,
        tmp_path,
        token="test-token",
        database_url=DATABASE_URL,
        supabase_url=SUPABASE_URL,
        jwt_secret=JWT_SECRET,
    )
    with TestClient(app) as client:
        yield client
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("DELETE FROM projects WHERE name LIKE 'pytest %'")


def test_create_then_list(client, make_user):
    user_id, auth = make_user()
    created = client.post(
        "/api/v1/projects", json={"name": " pytest AI Thesis "}, headers=auth
    )
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "pytest AI Thesis"
    assert body["meeting_count"] == 0 and body["image_path"] is None
    listed = client.get("/api/v1/projects", headers=auth).json()
    assert body["id"] in [project["id"] for project in listed]
    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute(
            "SELECT p.created_by, pm.role FROM projects p "
            "JOIN project_members pm ON pm.project_id = p.id WHERE p.id = %s",
            (body["id"],),
        ).fetchone()
    assert row == (user_id, "owner")


def test_projects_are_private_to_their_members(client, make_user):
    _, alice = make_user("Alice")
    _, bob = make_user("Bob")
    project = client.post(
        "/api/v1/projects", json={"name": "pytest private"}, headers=alice
    ).json()
    listed = client.get("/api/v1/projects", headers=bob).json()
    assert project["id"] not in [p["id"] for p in listed]
    url = f"/api/v1/projects/{project['id']}"
    assert client.delete(url, headers=bob).status_code == 404
    still_there = client.get("/api/v1/projects", headers=alice).json()
    assert project["id"] in [p["id"] for p in still_there]


def test_blank_name_is_rejected(client, make_user):
    _, auth = make_user()
    response = client.post("/api/v1/projects", json={"name": "  "}, headers=auth)
    assert response.status_code == 400


def test_sign_in_is_required(client):
    assert client.get("/api/v1/projects").status_code == 401
    assert client.delete(f"/api/v1/projects/{uuid.uuid4()}").status_code == 401
    shared = {"Authorization": "Bearer test-token"}
    assert client.get("/api/v1/projects", headers=shared).status_code == 401


def test_without_database_url_returns_503(tmp_path):
    with TestClient(create_app(tmp_path, tmp_path, token="test-token")) as client:
        assert client.get("/api/v1/projects").status_code == 503


def test_delete_project_cascades_meetings_and_chats(client, make_user):
    _, auth = make_user()
    project = client.post(
        "/api/v1/projects", json={"name": "pytest delete"}, headers=auth
    ).json()
    with psycopg.connect(DATABASE_URL) as conn:
        meeting_id = conn.execute(
            "INSERT INTO meetings (project_id, name, meeting_date, status) "
            "VALUES (%s, 'pytest meeting', now(), 'completed') RETURNING id",
            (project["id"],),
        ).fetchone()[0]
        conversation_id = conn.execute(
            "INSERT INTO chat_conversations (project_id, meeting_id) "
            "VALUES (%s, %s) RETURNING id",
            (project["id"], meeting_id),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO chat_messages (conversation_id, role, content) "
            "VALUES (%s, 'assistant', 'A quote from this meeting')",
            (conversation_id,),
        )
    url = f"/api/v1/projects/{project['id']}"
    assert client.delete(url, headers=auth).status_code == 200
    assert client.delete(url, headers=auth).status_code == 404
    with psycopg.connect(DATABASE_URL) as conn:
        assert (
            conn.execute(
                "SELECT id FROM meetings WHERE id = %s", (meeting_id,)
            ).fetchone()
            is None
        )
        assert (
            conn.execute(
                "SELECT id FROM chat_conversations WHERE id = %s", (conversation_id,)
            ).fetchone()
            is None
        )
        assert (
            conn.execute(
                "SELECT id FROM chat_messages WHERE conversation_id = %s",
                (conversation_id,),
            ).fetchone()
            is None
        )


@pytest.mark.parametrize(
    "status", ["queued", "transcribing", "diarizing", "extracting"]
)
def test_cannot_delete_project_with_active_meeting(client, make_user, status):
    _, auth = make_user()
    project = client.post(
        "/api/v1/projects", json={"name": "pytest active"}, headers=auth
    ).json()
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "INSERT INTO meetings (project_id, name, meeting_date, status) "
            "VALUES (%s, 'pytest active meeting', now(), %s)",
            (project["id"], status),
        )
    response = client.delete(f"/api/v1/projects/{project['id']}", headers=auth)
    assert response.status_code == 409
    assert project["id"] in [
        p["id"] for p in client.get("/api/v1/projects", headers=auth).json()
    ]
