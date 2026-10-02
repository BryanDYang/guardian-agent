"""Project invitations (Accounts & Voice Identity spec, Sections 5.4 and 6.5).

Runs against a local database only, e.g. after `supabase start`:
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
Never point this at the Supabase project."""

import os
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import psycopg
import pytest
from conftest import JWT_SECRET, SUPABASE_URL
from fastapi.testclient import TestClient

from labsync.server import create_app

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")


def email_of(user_id):
    return f"pytest-{user_id}@example.com"


def token_of(created):
    return parse_qs(urlparse(created["invite_url"]).query)["token"][0]


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
        conn.execute("DELETE FROM projects WHERE name LIKE 'pytest %'")


@pytest.fixture
def team(client, make_user):
    """Alice's project, and Carol, who isn't in it yet."""
    _, alice = make_user("Alice")
    carol_id, carol = make_user("Carol")
    project = client.post(
        "/api/v1/projects", json={"name": "pytest invites"}, headers=alice
    ).json()
    return project["id"], alice, email_of(carol_id), carol


def invite(client, project_id, email, headers):
    url = f"/api/v1/projects/{project_id}/invitations"
    return client.post(url, json={"email": email}, headers=headers)


def test_invite_then_accept_by_link(client, team):
    project_id, alice, carol_email, carol = team
    created = invite(client, project_id, f"  {carol_email.upper()} ", alice)
    assert created.status_code == 201
    body = created.json()
    assert body["invite_url"].startswith("meetingmemory://invite?token=")
    assert body["invitation"]["email"] == carol_email  # trimmed and lowercased
    assert body["invitation"]["invited_by_name"] == "Alice"

    accepted = client.post(
        "/api/v1/invitations/accept-token",
        json={"token": token_of(body)},
        headers=carol,
    )
    assert accepted.status_code == 200
    assert accepted.json()["project_name"] == "pytest invites"
    projects = client.get("/api/v1/projects", headers=carol).json()
    assert project_id in [project["id"] for project in projects]

    # Single use: the link can't add anyone again.
    again = client.post(
        "/api/v1/invitations/accept-token",
        json={"token": token_of(body)},
        headers=carol,
    )
    assert (again.status_code, again.json()["detail"]) == (409, "already_member")
    assert invite(client, project_id, carol_email, alice).status_code == 409


def test_pending_invitations_show_up_without_the_link(client, team):
    project_id, alice, carol_email, carol = team
    invitation = invite(client, project_id, carol_email, alice).json()["invitation"]
    mine = client.get("/api/v1/invitations", headers=carol).json()
    assert [i["id"] for i in mine] == [invitation["id"]]
    assert (
        client.get("/api/v1/me", headers=carol).json()["pending_invitation_count"] == 1
    )
    response = client.post(
        f"/api/v1/invitations/{invitation['id']}/accept", headers=carol
    )
    assert response.status_code == 200
    assert client.get("/api/v1/invitations", headers=carol).json() == []


def test_reinvite_replaces_the_old_link(client, team):
    project_id, alice, carol_email, carol = team
    first = invite(client, project_id, carol_email, alice).json()
    second = invite(client, project_id, carol_email, alice).json()
    assert second["invitation"]["id"] == first["invitation"]["id"]
    old = client.post(
        "/api/v1/invitations/accept-token",
        json={"token": token_of(first)},
        headers=carol,
    )
    assert old.status_code == 404
    listed = client.get(f"/api/v1/projects/{project_id}/invitations", headers=alice)
    assert len(listed.json()) == 1


def test_link_for_another_email_is_refused(client, team, make_user):
    project_id, alice, carol_email, _ = team
    _, dave = make_user("Dave")
    created = invite(client, project_id, carol_email, alice).json()
    response = client.post(
        "/api/v1/invitations/accept-token",
        json={"token": token_of(created)},
        headers=dave,
    )
    assert (response.status_code, response.json()["detail"]) == (403, "email_mismatch")
    # Dave can't see or act on Carol's invitation by id either.
    invitation_id = created["invitation"]["id"]
    assert client.get("/api/v1/invitations", headers=dave).json() == []
    for action in ["accept", "decline"]:
        url = f"/api/v1/invitations/{invitation_id}/{action}"
        assert client.post(url, headers=dave).status_code == 404


def test_revoked_declined_and_expired_invitations(client, team):
    project_id, alice, carol_email, carol = team
    created = invite(client, project_id, carol_email, alice).json()
    invitation_id = created["invitation"]["id"]
    revoke = client.delete(
        f"/api/v1/projects/{project_id}/invitations/{invitation_id}", headers=alice
    )
    assert revoke.status_code == 200
    accept = client.post(f"/api/v1/invitations/{invitation_id}/accept", headers=carol)
    assert (accept.status_code, accept.json()["detail"]) == (410, "revoked")

    declined = invite(client, project_id, carol_email, alice).json()["invitation"]
    url = f"/api/v1/invitations/{declined['id']}"
    assert client.post(f"{url}/decline", headers=carol).status_code == 200
    accept = client.post(f"{url}/accept", headers=carol)
    assert (accept.status_code, accept.json()["detail"]) == (410, "already_used")

    expired = invite(client, project_id, carol_email, alice).json()
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "UPDATE project_invitations SET expires_at = now() - interval '1 minute' "
            "WHERE id = %s",
            (expired["invitation"]["id"],),
        )
    accept = client.post(
        "/api/v1/invitations/accept-token",
        json={"token": token_of(expired)},
        headers=carol,
    )
    assert (accept.status_code, accept.json()["detail"]) == (410, "expired")
    projects = client.get("/api/v1/projects", headers=carol).json()
    assert project_id not in [project["id"] for project in projects]


def test_bad_email_and_unknown_invitation(client, team):
    project_id, alice, _, carol = team
    assert invite(client, project_id, "not-an-email", alice).status_code == 400
    other = client.post(
        "/api/v1/projects", json={"name": "pytest other"}, headers=carol
    ).json()["id"]
    url = f"/api/v1/projects/{other}/invitations/{uuid4()}"
    assert client.delete(url, headers=carol).status_code == 404