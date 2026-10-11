"""Speaker reviews use disposable PostgreSQL, never the team database."""

import os
from uuid import uuid4

import psycopg
import pytest
from conftest import JWT_SECRET, SUPABASE_URL
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from labsync.server import create_app

URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_DATABASE_URL not set")


def query(sql, *values):
    with psycopg.connect(URL, row_factory=dict_row) as conn:
        cursor = conn.execute(sql, values)
        return cursor.fetchall() if cursor.description else []


@pytest.fixture
def fixture(tmp_path, make_user, embedder):
    member, headers = make_user("Alex")
    outsider, outside_headers = make_user("Outsider")
    project, meeting = uuid4(), uuid4()
    query(
        "INSERT INTO projects(id,name) VALUES (%s,%s)", project, "speaker review test"
    )
    query(
        "INSERT INTO project_members(project_id,user_id,role) VALUES (%s,%s,%s)",
        project,
        member,
        "owner",
    )
    query(
        "INSERT INTO meetings(id,project_id,name,status,meeting_date) "
        "VALUES (%s,%s,'intro','completed',now())",
        meeting,
        project,
    )
    query(
        "INSERT INTO meeting_transcripts(meeting_id,speaker_label,speaker_name,"
        "turn_key,"
        "start_time_ms,end_time_ms,content,turn_order) VALUES "
        "(%s,'SPEAKER_00','SPEAKER_1','intro',1000,5000,'My name is Alex.',0)",
        meeting,
    )
    query(
        "INSERT INTO tasks(project_id,meeting_id,title,owner_label) "
        "VALUES (%s,%s,'Write report','SPEAKER_1')",
        project,
        meeting,
    )
    query(
        "INSERT INTO tasks(project_id,meeting_id,title,owner_label,review_status) "
        "VALUES (%s,%s,'Reviewed report','SPEAKER_1','approved')",
        project,
        meeting,
    )
    app = create_app(
        tmp_path,
        database_url=URL,
        embedder=embedder,
        supabase_url=SUPABASE_URL,
        jwt_secret=JWT_SECRET,
    )
    with TestClient(app) as client:
        yield client, headers, outside_headers, member, outsider, meeting
    query("DELETE FROM projects WHERE id=%s", project)
    query("DELETE FROM audio_deletions WHERE object_key LIKE %s", str(meeting) + "/%")


def test_review_proposes_names_but_does_not_guess_account(fixture):
    client, headers, _, _, _, meeting = fixture
    path = f"/api/v1/meetings/{meeting}/speakers"
    response = client.get(path, headers=headers)
    assert response.status_code == 200
    assert response.json()[0]["suggestions"][0]["name"] == "Alex"
    assert response.json()[0]["confirmed"] is False
    assert (
        client.put(
            path + "/SPEAKER_00", headers=headers, json={"name": "Alex"}
        ).status_code
        == 200
    )
    tasks = query(
        "SELECT owner_label,assignee_user_id,review_status FROM tasks "
        "WHERE meeting_id=%s",
        meeting,
    )
    assert (
        next(t for t in tasks if t["review_status"] == "pending")["owner_label"]
        == "Alex"
    )
    assert all(t["assignee_user_id"] is None for t in tasks)
    assert (
        next(t for t in tasks if t["review_status"] == "approved")["owner_label"]
        == "SPEAKER_1"
    )
    assert client.get(path, headers=headers).json()[0]["confirmed"] is True


def test_confirmed_mapping_assigns_pending_commitments_to_member(fixture):
    client, headers, _, member, _, meeting = fixture
    response = client.put(
        f"/api/v1/meetings/{meeting}/speakers/SPEAKER_00",
        headers=headers,
        json={"name": "Alex", "assignee_user_id": str(member)},
    )
    assert response.status_code == 200
    task = query(
        "SELECT * FROM tasks WHERE meeting_id=%s AND review_status='pending'", meeting
    )[0]
    assert task["assignee_user_id"] == member
    assert task["review_status"] == "pending"
    metadata = query("SELECT model_metadata FROM meetings WHERE id=%s", meeting)[0][
        "model_metadata"
    ]
    assert metadata["speaker_name_review_history"][0]["confirmed_by"] == str(member)


def test_speaker_review_checks_membership_and_processing_state(fixture):
    client, headers, outside_headers, _, outsider, meeting = fixture
    path = f"/api/v1/meetings/{meeting}/speakers"
    assert client.get(path, headers=outside_headers).status_code == 404
    assert (
        client.put(
            path + "/SPEAKER_00", headers=outside_headers, json={"name": "Alex"}
        ).status_code
        == 404
    )
    assert (
        client.put(
            path + "/SPEAKER_00",
            headers=headers,
            json={"name": "Alex", "assignee_user_id": str(outsider)},
        ).status_code
        == 400
    )
    assert (
        client.put(
            path + "/UNKNOWN", headers=headers, json={"name": "Alex"}
        ).status_code
        == 404
    )
    query("UPDATE meetings SET status='transcribing' WHERE id=%s", meeting)
    assert (
        client.put(
            path + "/SPEAKER_00", headers=headers, json={"name": "Alex"}
        ).status_code
        == 409
    )


def test_shared_snapshot_is_updated_and_duplicate_names_need_review(fixture):
    from psycopg.types.json import Jsonb

    client, headers, _, _, _, meeting = fixture
    query(
        "INSERT INTO meeting_jobs(meeting_id,object_key,state,record,settings) "
        "VALUES (%s,%s,'completed',%s,%s)",
        meeting,
        str(meeting) + "/recording.wav",
        Jsonb(
            {
                "transcript": {"turns": [{"speaker": "SPEAKER_1"}]},
                "extraction": {"commitments": [{"owner": "SPEAKER_1"}]},
            }
        ),
        Jsonb({}),
    )
    path = f"/api/v1/meetings/{meeting}/speakers/SPEAKER_00"
    assert client.put(path, headers=headers, json={"name": "Alex"}).status_code == 200
    record = query("SELECT record FROM meeting_jobs WHERE meeting_id=%s", meeting)[0][
        "record"
    ]
    assert record["transcript"]["turns"][0]["speaker"] == "Alex"
    assert record["extraction"]["commitments"][0]["owner"] == "Alex"
    query(
        "INSERT INTO meeting_transcripts(meeting_id,speaker_label,speaker_name,"
        "turn_key,start_time_ms,end_time_ms,content,turn_order) VALUES "
        "(%s,'SPEAKER_01','Sam','other',5000,6000,'Hello.',1)",
        meeting,
    )
    assert client.put(path, headers=headers, json={"name": "Sam"}).status_code == 409
    assert (
        query(
            "SELECT speaker_name FROM meeting_transcripts "
            "WHERE meeting_id=%s AND speaker_label='SPEAKER_00'",
            meeting,
        )[0]["speaker_name"]
        == "Alex"
    )


def test_reprocessing_keeps_review_history_but_invalidates_cluster_mapping(fixture):
    from labsync.db.meetings import save_results
    from labsync.extraction import Transcript, Turn

    client, headers, _, _, _, meeting = fixture
    assert (
        client.put(
            f"/api/v1/meetings/{meeting}/speakers/SPEAKER_00",
            headers=headers,
            json={"name": "Alex"},
        ).status_code
        == 200
    )
    project = query("SELECT project_id FROM meetings WHERE id=%s", meeting)[0][
        "project_id"
    ]
    transcript = Transcript(
        project_id=str(project),
        meeting_id=str(meeting),
        turns=[
            Turn(
                id="new",
                speaker="SPEAKER_99",
                start_time_ms=0,
                end_time_ms=1000,
                content="Hello.",
            )
        ],
    )
    with psycopg.connect(URL, row_factory=dict_row) as conn:
        save_results(
            conn,
            meeting,
            transcript,
            {
                "extraction": {
                    "summary": "Hello",
                    "decisions": [],
                    "commitments": [],
                    "suggestions": [],
                }
            },
            {},
        )
    metadata = query("SELECT model_metadata FROM meetings WHERE id=%s", meeting)[0][
        "model_metadata"
    ]
    assert len(metadata["speaker_name_review_history"]) == 1
    assert "speaker_name_reviews" not in metadata
    assert (
        client.get(f"/api/v1/meetings/{meeting}/speakers", headers=headers).json()[0][
            "confirmed"
        ]
        is False
    )
