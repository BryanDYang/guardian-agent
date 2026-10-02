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


def add_meeting(conn, project_id, name, meeting_date, with_results=False):
    meeting_id = str(uuid4())
    meetings.create_meeting(
        conn,
        meeting_id=meeting_id,
        project_id=project_id,
        name=name,
        meeting_date=meeting_date,
        audio_file_path="/tmp/recording.mp3",
    )
    if not with_results:
        return meeting_id
    turn = f"{meeting_id}:turn:"
    transcript = Transcript.model_validate(
        {
            "project_id": str(project_id),
            "meeting_id": meeting_id,
            "turns": [
                {
                    "id": turn + "0",
                    "speaker": "SPEAKER_01",
                    "start_time_ms": 0,
                    "end_time_ms": 900,
                    "content": "I will share the recording.",
                },
                {
                    "id": turn + "1",
                    "speaker": "SPEAKER_04",
                    "start_time_ms": 1000,
                    "end_time_ms": 1900,
                    "content": "Let's keep this time for now.",
                },
            ],
        }
    )
    extraction = {
        "summary": "TA check-in.",
        "decisions": [
            {
                "statement": "Keep the meeting time",
                "evidence": [{"transcript_id": turn + "1", "quote": "keep this time"}],
            }
        ],
        "commitments": [
            {
                "title": "Share the recording",
                "owner": "SPEAKER_01",
                "due_date_text": None,
                "evidence": [
                    {"transcript_id": turn + "0", "quote": "I will share"},
                    {"transcript_id": turn + "0", "quote": "the recording"},
                ],
            }
        ],
        "suggestions": [],
    }
    meetings.save_results(conn, meeting_id, transcript, {"extraction": extraction}, {})
    return meeting_id


@pytest.fixture
def seeded(make_user):
    """A project with two meetings, one member, and one signed-in outsider."""
    member_id, member = make_user("Member")
    _, outsider = make_user("Outsider")
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        project_id = conn.execute(
            "INSERT INTO projects (name) VALUES ('pytest reads') RETURNING id"
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO project_members (project_id, user_id, role) "
            "VALUES (%s, %s, 'member')",
            (project_id, member_id),
        )
        older = add_meeting(conn, project_id, "Week 1", date(2026, 9, 18))
        newer = add_meeting(conn, project_id, "Week 2", date(2026, 9, 25), True)
    yield {
        "project_id": str(project_id),
        "older": older,
        "newer": newer,
        "auth": member,
        "outsider": outsider,
    }
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("DELETE FROM projects WHERE name = 'pytest reads'")


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


def test_list_is_newest_first_and_paginates(client, seeded):
    url = f"/api/v1/projects/{seeded['project_id']}/meetings"
    auth = seeded["auth"]
    listed = client.get(url, headers=auth).json()
    assert [m["id"] for m in listed] == [seeded["newer"], seeded["older"]]
    page = client.get(url, params={"limit": 1, "offset": 1}, headers=auth).json()
    assert [m["id"] for m in page] == [seeded["older"]]


def test_list_errors(client, seeded):
    auth = seeded["auth"]
    unknown = "/api/v1/projects/00000000-0000-0000-0000-000000000000/meetings"
    assert client.get(unknown, headers=auth).status_code == 404
    url = f"/api/v1/projects/{seeded['project_id']}/meetings"
    assert client.get(url, params={"limit": 0}, headers=auth).status_code == 422


def test_detail_has_everything_the_screen_needs(client, seeded):
    url = f"/api/v1/meetings/{seeded['newer']}"
    detail = client.get(url, headers=seeded["auth"]).json()
    assert detail["name"] == "Week 2" and detail["status"] == "queued"
    assert detail["summary"] == {"overview": "TA check-in.", "bullet_points": None}
    assert detail["decisions"][0]["statement"] == "Keep the meeting time"
    assert detail["decisions"][0]["evidence"][0]["quote"] == "keep this time"
    task = detail["tasks"][0]
    assert (task["title"], task["owner_label"], task["review_status"]) == (
        "Share the recording",
        "SPEAKER_01",
        "pending",
    )
    assert task["due_date"] is None
    assert [e["quote"] for e in task["evidence"]] == ["I will share", "the recording"]
    assert [t["speaker"] for t in detail["transcript"]] == ["SPEAKER_01", "SPEAKER_04"]
    assert detail["storylines"] == []
    assert detail["audio_url"] == f"/api/meetings/{seeded['newer']}/audio"


def test_detail_before_processing_finishes(client, seeded):
    url = f"/api/v1/meetings/{seeded['older']}"
    detail = client.get(url, headers=seeded["auth"]).json()
    assert detail["summary"] is None
    assert detail["decisions"] == detail["tasks"] == detail["transcript"] == []


def test_detail_unknown_meeting(client, seeded):
    unknown = "/api/v1/meetings/00000000-0000-0000-0000-000000000000"
    assert client.get(unknown, headers=seeded["auth"]).status_code == 404


def test_outsiders_and_strangers_cannot_read_meetings(client, seeded):
    project = f"/api/v1/projects/{seeded['project_id']}/meetings"
    meeting = f"/api/v1/meetings/{seeded['newer']}"
    for url in (project, meeting):
        assert client.get(url, headers=seeded["outsider"]).status_code == 404
        assert client.get(url).status_code == 401
