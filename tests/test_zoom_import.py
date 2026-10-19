"""Summary-to-follow-up acceptance against a disposable local database."""

import os

import pytest
from conftest import JWT_SECRET, SUPABASE_URL
from fastapi.testclient import TestClient

from labsync import providers
from labsync.chat import build_sources
from labsync.extraction import Transcript
from labsync.followup import EmailWorker
from labsync.server import create_app

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")


@pytest.fixture
def flow(tmp_path, make_user, embedder, monkeypatch):
    monkeypatch.setenv("LABSYNC_EMAIL_MODE", "capture")
    monkeypatch.setattr(EmailWorker, "start", lambda self: None)
    member_id, auth = make_user("Bryan")
    _, outsider = make_user("Outsider")
    calls = []

    def extract(prompt, schema, **kwargs):
        transcript = Transcript.model_validate_json(prompt.split("DOCUMENT:\n", 1)[1])
        calls.append(transcript)
        return {
            "summary": "Checklist preparation agreed.",
            "decisions": [],
            "suggestions": [],
            "commitments": [
                {
                    "title": "Prepare the evaluation checklist",
                    "owner": "Bryan",
                    "due_date_text": None,
                    "evidence": [
                        {
                            "transcript_id": transcript.turns[0].id,
                            "quote": "Bryan will prepare the evaluation checklist.",
                        }
                    ],
                }
            ],
        }

    monkeypatch.setattr(providers, "structured", extract)
    app = create_app(
        tmp_path,
        database_url=DATABASE_URL,
        embedder=embedder,
        supabase_url=SUPABASE_URL,
        jwt_secret=JWT_SECRET,
    )
    with TestClient(app, headers=auth) as client:
        project = client.post("/api/v1/projects", json={"name": "Zoom test"}).json()[
            "id"
        ]
        body = dict(
            project_id=project,
            title="Solo Zoom summary",
            meeting_date="2026-10-19",
            source_instance="solo-2026-10-19-1",
            summary="Bryan will prepare the evaluation checklist.",
            consent_confirmed=True,
            is_sample=True,
        )
        yield app, client, member_id, outsider, body, calls
        with app.state.pool.connection() as conn:
            conn.execute("DELETE FROM projects WHERE id=%s", (project,))


def test_summary_review_to_captured_followup_and_idempotent_retry(flow):
    app, client, member, _, body, calls = flow
    imported = client.post("/api/v1/meetings/zoom-summary", json=body)
    assert imported.status_code == 201, imported.text
    meeting = imported.json()["id"]
    detail = client.get(f"/api/v1/meetings/{meeting}").json()
    assert detail["source"]["input_kind"] == "zoom_summary"
    assert detail["source"]["is_sample"] is True
    assert detail["audio_file_path"] is None
    assert detail["tasks"][0]["review_status"] == "pending"
    assert detail["tasks"][0]["assignee_user_id"] is None
    assert detail["tasks"][0]["evidence"][0]["timestamp_ms"] is None
    assert calls[0].turns[0].speaker == "UNKNOWN"
    assert client.get(f"/api/v1/meetings/{meeting}/speakers").json() == []
    with app.state.pool.connection() as conn:
        hits = conn.execute(
            "SELECT r.*,m.name AS meeting_name,m.meeting_date FROM rag_chunks r "
            "JOIN meetings m ON m.id=r.meeting_id "
            "WHERE r.meeting_id=%s AND r.kind='transcript'",
            (meeting,),
        ).fetchall()
        sources = build_sources(conn, hits)
    assert sources and all(s.kind == "summary" for s in sources)
    assert all(s.start_time_ms is None for s in sources)
    task = detail["tasks"][0]["id"]
    project = body["project_id"]
    assert (
        client.put(
            f"/api/v1/projects/{project}/followup",
            json={
                "email_enabled": True,
                "auto_approve": True,
            },
        ).status_code
        == 200
    )
    assert (
        client.put(
            f"/api/v1/projects/{project}/followup/me",
            json={
                "receive_email": True,
            },
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/v1/tasks/{task}/review",
            json={
                "action": "approve",
                "assignee_user_id": str(member),
            },
        ).status_code
        == 200
    )
    assert EmailWorker(app.state.pool).process_one()
    emails = client.get(f"/api/v1/projects/{project}/followup/emails").json()
    assert len(emails) == 1 and emails[0]["state"] == "captured"
    assert "checklist" in emails[0]["preview"]
    assert "Zoom summary evidence (not recorded speech)" in emails[0]["preview"]
    retry = client.post("/api/v1/meetings/zoom-summary", json=body)
    assert retry.json()["id"] == meeting
    assert len(calls) == 1
    assert len(client.get(f"/api/v1/meetings/{meeting}").json()["tasks"]) == 1


def test_permissions_validation_and_edited_summary_are_not_silently_imported(flow):
    _, client, _, outsider, body, calls = flow
    url = "/api/v1/meetings/zoom-summary"
    assert client.post(url, json=body, headers=outsider).status_code == 404
    assert client.post(url, json=body | {"consent_confirmed": False}).status_code == 400
    assert client.post(url, json=body | {"summary": "   "}).status_code == 422
    assert client.post(url, json=body | {"source_instance": " "}).status_code == 422
    assert client.post(url, json=body | {"summary": "x" * 30_001}).status_code == 422
    assert not calls
    assert client.post(url, json=body).status_code == 201
    assert (
        client.post(
            url, json=body | {"summary": body["summary"] + " Changed."}
        ).status_code
        == 409
    )
    assert len(calls) == 1


def test_extraction_failure_is_atomic_and_retryable(flow, monkeypatch):
    app, client, _, _, body, _ = flow

    def fail(*args, **kwargs):
        raise RuntimeError("Provider unavailable")

    monkeypatch.setattr(providers, "structured", fail)
    response = client.post("/api/v1/meetings/zoom-summary", json=body)
    assert response.status_code == 503
    with app.state.pool.connection() as conn:
        assert (
            conn.execute(
                "SELECT count(*) AS n FROM meetings WHERE project_id=%s",
                (body["project_id"],),
            ).fetchone()["n"]
            == 0
        )
