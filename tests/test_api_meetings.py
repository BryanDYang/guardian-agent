"""Runs against a local database only, e.g. after `supabase start`:
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
Never point this at the Supabase project."""

import json
import os
import time
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

import labsync.server
from labsync.server import create_app

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")
AUTH = {"Authorization": "Bearer test-token"}


def query(sql, *params):
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        return conn.execute(sql, params).fetchall()


def fake_pipeline(command, **kwargs):
    """Stand-in for the transcribe and extract subprocesses."""
    if "transcribe" in command:
        meeting = command[command.index("--meeting-id") + 1]
        work = Path(command[command.index("--output-dir") + 1])
        work.mkdir(parents=True)
        turns = [
            ("SPEAKER_01", "I will share the recording."),
            ("SPEAKER_04", "Let's keep this time for now."),
            ("SPEAKER_01", "You could try S3 vector indexing."),
        ]
        transcript = {
            "project_id": command[command.index("--project-id") + 1],
            "meeting_id": meeting,
            "turns": [
                {
                    "id": f"{meeting}:turn:{i}",
                    "speaker": speaker,
                    "start_time_ms": i * 1000,
                    "end_time_ms": i * 1000 + 900,
                    "content": content,
                }
                for i, (speaker, content) in enumerate(turns)
            ],
        }
        (work / "transcript.json").write_text(json.dumps(transcript))
        (work / "ccb-transcript.json").write_text(
            json.dumps({"metadata": {"whisper_model": "medium"}, "segments": []})
        )
    else:
        transcript = Path(command[command.index("extract") + 1])
        meeting = json.loads(transcript.read_text())["meeting_id"]
        turn = f"{meeting}:turn:"
        extraction = {
            "summary": "TA check-in.",
            "decisions": [
                {
                    "statement": "Keep the meeting time",
                    "evidence": [
                        {"transcript_id": turn + "1", "quote": "keep this time"}
                    ],
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
            "suggestions": [
                {
                    "statement": "Try S3 vector indexing",
                    "evidence": [{"transcript_id": turn + "2", "quote": "S3 vector"}],
                }
            ],
        }
        output = Path(command[command.index("--output") + 1])
        output.write_text(json.dumps({"provider": "fake", "extraction": extraction}))


@pytest.fixture
def project_id():
    project = query(
        "INSERT INTO projects (name) VALUES ('pytest meetings') RETURNING id"
    )
    yield str(project[0]["id"])
    query("DELETE FROM projects WHERE name = 'pytest meetings' RETURNING id")


@pytest.fixture
def client(tmp_path, monkeypatch, embedder):
    monkeypatch.setattr(labsync.server.subprocess, "run", fake_pipeline)
    app = create_app(
        tmp_path,
        tmp_path,
        token="test-token",
        database_url=DATABASE_URL,
        embedder=embedder,
    )
    with TestClient(app) as client:
        yield client


def upload(client, project_id, overrides=None):
    form = {
        "project_id": project_id,
        "title": "TA check-in",
        "meeting_date": "2026-09-25",
        "consent_confirmed": "true",
    } | (overrides or {})
    files = {"file": ("recording.mp3", b"fake audio", "audio/mpeg")}
    return client.post("/api/v1/meetings/upload", data=form, files=files, headers=AUTH)


def wait_for(meeting_id, status):
    for _ in range(50):
        rows = query("SELECT * FROM meetings WHERE id = %s", meeting_id)
        if rows and rows[0]["status"] == status:
            return rows[0]
        time.sleep(0.1)
    raise AssertionError(f"Meeting never reached {status}: {rows}")


def test_upload_processes_and_saves_results(client, project_id):
    response = upload(client, project_id)
    assert response.status_code == 202
    meeting_id = response.json()["job_id"]
    meeting = wait_for(meeting_id, "completed")
    assert meeting["processing_attempt"] == 1 and meeting["error_message"] is None
    assert meeting["model_metadata"]["transcription"] == {"whisper_model": "medium"}

    turns = query(
        "SELECT speaker_label, turn_key FROM meeting_transcripts WHERE meeting_id = %s "
        "ORDER BY turn_order",
        meeting_id,
    )
    assert [t["speaker_label"] for t in turns] == [
        "SPEAKER_01",
        "SPEAKER_04",
        "SPEAKER_01",
    ]
    summary = query(
        "SELECT overview FROM meeting_summaries WHERE meeting_id = %s", meeting_id
    )
    assert summary[0]["overview"] == "TA check-in."

    tasks = query(
        "SELECT title, owner_label, category FROM tasks WHERE meeting_id = %s ORDER BY title",
        meeting_id,
    )
    assert [(t["title"], t["owner_label"], t["category"]) for t in tasks] == [
        ("Share the recording", "SPEAKER_01", "commitment"),
        ("Try S3 vector indexing", None, "advisor_suggestion"),
    ]
    evidence = query(
        "SELECT e.position, e.quote, t.content FROM item_evidence e "
        "JOIN tasks k ON k.id = e.task_id "
        "JOIN meeting_transcripts t ON t.meeting_id = k.meeting_id AND t.turn_key = e.turn_key "
        "WHERE k.title = 'Share the recording' ORDER BY e.position",
    )
    assert [(e["position"], e["quote"]) for e in evidence] == [
        (0, "I will share"),
        (1, "the recording"),
    ]
    assert all(e["quote"] in e["content"] for e in evidence)
    decision = query(
        "SELECT d.timestamp_ms, e.quote FROM meeting_decisions d "
        "JOIN item_evidence e ON e.decision_id = d.id WHERE d.meeting_id = %s",
        meeting_id,
    )
    assert decision == [{"timestamp_ms": 1000, "quote": "keep this time"}]

    chunks = query(
        "SELECT kind, start_time_ms, content FROM rag_chunks "
        "WHERE meeting_id = %s ORDER BY kind, content",
        meeting_id,
    )
    assert [(c["kind"], c["start_time_ms"]) for c in chunks] == [
        ("decision", 1000),
        ("summary", None),
        ("task", 0),
        ("task", 2000),
        ("transcript", 0),
    ]


def test_retry_replaces_results_and_mirrors_attempt(client, project_id, tmp_path):
    meeting_id = upload(client, project_id).json()["job_id"]
    wait_for(meeting_id, "completed")
    record_path = tmp_path / meeting_id / "meeting.json"
    record = json.loads(record_path.read_text()) | {"status": "failed"}
    record_path.write_text(json.dumps(record))

    assert (
        client.post(f"/api/meetings/{meeting_id}/retry", headers=AUTH).status_code
        == 202
    )
    meeting = wait_for(meeting_id, "completed")
    assert meeting["processing_attempt"] == 2
    counts = query(
        "SELECT (SELECT count(*) FROM meeting_transcripts WHERE meeting_id = %s) AS turns, "
        "(SELECT count(*) FROM tasks WHERE meeting_id = %s) AS tasks, "
        "(SELECT count(*) FROM rag_chunks WHERE meeting_id = %s) AS chunks",
        meeting_id,
        meeting_id,
        meeting_id,
    )
    assert counts == [{"turns": 3, "tasks": 2, "chunks": 5}]


@pytest.mark.parametrize(
    ("overrides", "status"),
    [
        ({"consent_confirmed": "false"}, 400),
        ({"title": "   "}, 400),
        ({"project_id": "00000000-0000-0000-0000-000000000000"}, 404),
        ({"project_id": "not-a-uuid"}, 422),
    ],
)
def test_upload_rejections(client, project_id, overrides, status, tmp_path):
    assert upload(client, project_id, overrides).status_code == status
    assert not list(tmp_path.glob("*/meeting.json"))