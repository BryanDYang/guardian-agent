"""Runs against a local database only, e.g. after `supabase start`:
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
Never point this at the Supabase project."""

import os

import psycopg
import pytest
from fastapi.testclient import TestClient

from labsync.server import create_app

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")
AUTH = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path, tmp_path, token="test-token", database_url=DATABASE_URL)
    with TestClient(app) as client:
        yield client
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("DELETE FROM projects WHERE name LIKE 'pytest %'")


def test_create_then_list(client):
    created = client.post(
        "/api/v1/projects", json={"name": " pytest AI Thesis "}, headers=AUTH
    )
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "pytest AI Thesis"
    assert body["meeting_count"] == 0 and body["image_path"] is None
    listed = client.get("/api/v1/projects", headers=AUTH).json()
    assert body["id"] in [project["id"] for project in listed]


def test_blank_name_is_rejected(client):
    assert (
        client.post("/api/v1/projects", json={"name": "  "}, headers=AUTH).status_code
        == 400
    )


def test_token_is_required(client):
    assert client.get("/api/v1/projects").status_code == 401


def test_without_database_url_returns_503(tmp_path):
    with TestClient(create_app(tmp_path, tmp_path, token="test-token")) as client:
        assert client.get("/api/v1/projects", headers=AUTH).status_code == 503