"""Authenticated task-to-inbox acceptance on disposable PostgreSQL only."""

import os
from uuid import uuid4

import pytest
from conftest import JWT_SECRET, SUPABASE_URL
from fastapi.testclient import TestClient

from labsync.db import meetings, rag
from labsync.extraction import Transcript
from labsync.followup import EmailWorker, auto_approve
from labsync.server import create_app

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")


@pytest.fixture
def flow(tmp_path, make_user, embedder, monkeypatch):
    monkeypatch.setenv("LABSYNC_EMAIL_MODE", "capture")
    monkeypatch.setattr(EmailWorker, "start", lambda self: None)
    owner_id, auth = make_user("Organizer")
    recipient_id, recipient_auth = make_user("Recipient")
    _, outsider = make_user("Outsider")
    app = create_app(
        tmp_path,
        database_url=DATABASE_URL,
        embedder=embedder,
        supabase_url=SUPABASE_URL,
        jwt_secret=JWT_SECRET,
    )
    with TestClient(app, headers=auth) as client:
        project = client.post(
            "/api/v1/projects", json={"name": "Email acceptance"}
        ).json()["id"]
        with app.state.pool.connection() as conn:
            conn.execute(
                "INSERT INTO project_members(project_id,user_id,role) "
                "VALUES(%s,%s,'member')",
                (project, recipient_id),
            )
        meeting = str(uuid4())
        turn = meeting + ":turn:0"
        with app.state.pool.connection() as conn:
            meetings.create_meeting(
                conn,
                meeting_id=meeting,
                project_id=project,
                name="Real task review",
                meeting_date="2026-10-17",
                audio_file_path="",
            )
            transcript = Transcript.model_validate(
                {
                    "project_id": project,
                    "meeting_id": meeting,
                    "turns": [
                        {
                            "id": turn,
                            "speaker": "SPEAKER_2",
                            "start_time_ms": 5000,
                            "end_time_ms": 10000,
                            "content": "I will share the recording.",
                        }
                    ],
                }
            )
            meetings.save_results(
                conn,
                meeting,
                transcript,
                {
                    "extraction": {
                        "summary": "Sharing agreed.",
                        "decisions": [],
                        "suggestions": [],
                        "commitments": [
                            {
                                "title": "Share the recording",
                                "owner": "SPEAKER_2",
                                "due_date_text": None,
                                "evidence": [
                                    {
                                        "transcript_id": turn,
                                        "quote": "I will share the recording.",
                                    }
                                ],
                            }
                        ],
                    }
                },
                {},
            )
            meetings.update_status(conn, meeting, "completed", 1, None)
            rag.index_meeting(conn, meeting, embedder)
            task = str(
                conn.execute(
                    "SELECT id FROM tasks WHERE meeting_id=%s", (meeting,)
                ).fetchone()["id"]
            )
        yield dict(
            app=app,
            client=client,
            project=project,
            meeting=meeting,
            task=task,
            recipient_id=recipient_id,
            recipient_auth=recipient_auth,
            outsider=outsider,
            turn=turn,
            owner_id=owner_id,
        )
        with app.state.pool.connection() as conn:
            conn.execute("DELETE FROM projects WHERE id=%s", (project,))


def configure(f, auto=False):
    return f["client"].put(
        f"/api/v1/projects/{f['project']}/followup",
        json={"email_enabled": True, "auto_approve": auto},
    )


def connect(f):
    return f["client"].put(
        f"/api/v1/meetings/{f['meeting']}/speakers/SPEAKER_2",
        json={"name": "Recipient", "assignee_user_id": str(f["recipient_id"])},
    )


def logs(f, headers=None):
    return (
        f["client"]
        .get(f"/api/v1/projects/{f['project']}/followup/emails", headers=headers)
        .json()
    )


def test_manual_approval_to_captured_inbox_once(flow):
    f, c = flow, flow["client"]
    assert configure(f).status_code == 200
    assert connect(f).status_code == 200
    assert not logs(f)
    response = c.patch(f"/api/v1/tasks/{f['task']}/review", json={"action": "approve"})
    assert response.status_code == 200, response.text
    assert logs(f)[0]["state"] == "queued"
    worker = EmailWorker(f["app"].state.pool)
    assert worker.process_one()
    assert not worker.process_one()
    email = logs(f)[0]
    assert email["state"] == "captured"
    assert "I will share the recording." in email["preview"]
    assert "No deadline set" in email["preview"]
    assert "Real task review" in email["preview"]
    assert (
        c.patch(
            f"/api/v1/tasks/{f['task']}/review", json={"action": "approve"}
        ).status_code
        == 409
    )
    assert len(logs(f)) == 1
    assert len(logs(f, f["recipient_auth"])) == 1
    assert (
        c.get(
            f"/api/v1/projects/{f['project']}/followup/emails", headers=f["outsider"]
        ).status_code
        == 404
    )


def test_confirmed_speaker_auto_approves_and_queues(flow):
    f = flow
    assert configure(f, auto=True).status_code == 200
    assert not logs(f)  # A diarization label is insufficient.
    response = connect(f)
    assert response.status_code == 200, response.text
    assert response.json()["auto_approved_tasks"] == 1
    assert connect(f).json()["auto_approved_tasks"] == 0
    with f["app"].state.pool.connection() as conn:
        assert auto_approve(conn, f["meeting"]) == 0
        audit = conn.execute(
            "SELECT new_value FROM task_audit_log WHERE task_id=%s "
            "AND action='AUTO_APPROVE'",
            (f["task"],),
        ).fetchone()
        assert audit["new_value"]["policy"] == "explicit-self-commitment-v1"
    assert len(logs(f)) == 1
    assert EmailWorker(f["app"].state.pool).process_one()
    assert logs(f)[0]["state"] == "captured"


@pytest.mark.parametrize(
    "reason",
    [
        "conditional",
        "negation",
        "question",
        "suggestion",
        "deadline",
        "unsupported_title",
        "no_embedding",
        "duplicate",
        "voice_only",
    ],
)
def test_uncertain_candidates_stay_pending(flow, reason):
    f = flow
    configure(f, auto=True)
    with f["app"].state.pool.connection() as conn:
        if reason in {"conditional", "negation", "question"}:
            content = {
                "conditional": "I will share the recording if allowed.",
                "negation": "I will not share the recording.",
                "question": "I will share the recording?",
            }[reason]
            conn.execute(
                "UPDATE meeting_transcripts SET content=%s WHERE meeting_id=%s",
                (content, f["meeting"]),
            )
            conn.execute(
                "UPDATE item_evidence SET quote=%s WHERE task_id=%s",
                (content, f["task"]),
            )
        elif reason == "suggestion":
            conn.execute(
                "UPDATE tasks SET category='advisor_suggestion' WHERE id=%s",
                (f["task"],),
            )
        elif reason == "deadline":
            conn.execute(
                "UPDATE tasks SET due_date_text='next Friday' WHERE id=%s", (f["task"],)
            )
        elif reason == "unsupported_title":
            conn.execute(
                "UPDATE tasks SET title='Delete private recordings' WHERE id=%s",
                (f["task"],),
            )
        elif reason == "no_embedding":
            conn.execute("UPDATE tasks SET embedding=NULL WHERE id=%s", (f["task"],))
        elif reason == "duplicate":
            conn.execute(
                "INSERT INTO tasks(project_id,title,embedding,review_status,"
                "lifecycle_status) "
                "SELECT project_id,title,embedding,'approved','done' FROM tasks "
                "WHERE id=%s",
                (f["task"],),
            )
        elif reason == "voice_only":
            conn.execute(
                "UPDATE tasks SET assignee_user_id=%s WHERE id=%s",
                (f["recipient_id"], f["task"]),
            )
            assert auto_approve(conn, f["meeting"]) == 0
            return
    response = connect(f)
    assert response.status_code == 200, response.text
    assert response.json()["auto_approved_tasks"] == 0
    assert not logs(f)


def test_opt_out_permissions_and_cancellation(flow):
    f, c = flow, flow["client"]
    path = f"/api/v1/projects/{f['project']}/followup"
    assert (
        c.put(
            path,
            headers=f["recipient_auth"],
            json={"email_enabled": True, "auto_approve": True},
        ).status_code
        == 403
    )
    configure(f)
    connect(f)
    c.patch(f"/api/v1/tasks/{f['task']}/review", json={"action": "approve"})
    assert (
        c.put(
            path + "/me", headers=f["recipient_auth"], json={"receive_email": False}
        ).status_code
        == 200
    )
    assert EmailWorker(f["app"].state.pool).process_one()
    assert logs(f)[0]["state"] == "cancelled"


@pytest.mark.parametrize(
    "change", ["complete", "remove_member", "disable_project", "delete_project"]
)
def test_pending_email_does_not_outlive_task_or_access(flow, change):
    f, c = flow, flow["client"]
    configure(f)
    connect(f)
    c.patch(f"/api/v1/tasks/{f['task']}/review", json={"action": "approve"})
    if change == "complete":
        c.post(f"/api/v1/tasks/{f['task']}/state", json={"state": "done"})
    elif change == "remove_member":
        c.delete(f"/api/v1/projects/{f['project']}/members/{f['recipient_id']}")
    elif change == "disable_project":
        c.put(
            f"/api/v1/projects/{f['project']}/followup",
            json={"email_enabled": False, "auto_approve": False},
        )
    else:
        with f["app"].state.pool.connection() as conn:
            conn.execute("DELETE FROM projects WHERE id=%s", (f["project"],))
    EmailWorker(f["app"].state.pool).process_one()
    with f["app"].state.pool.connection() as conn:
        rows = conn.execute(
            "SELECT state FROM task_followup_emails WHERE task_id=%s", (f["task"],)
        ).fetchall()
        assert not rows or rows[0]["state"] == "cancelled"


def test_retry_uses_same_payload_and_provider_key(flow):
    f = flow
    os_mode = os.environ["LABSYNC_EMAIL_MODE"]
    os.environ["LABSYNC_EMAIL_MODE"] = "resend"
    try:
        configure(f)
        connect(f)
        f["client"].patch(
            f"/api/v1/tasks/{f['task']}/review", json={"action": "approve"}
        )
    finally:
        os.environ["LABSYNC_EMAIL_MODE"] = os_mode

    class Sender:
        sender = "LabSync <test@example.test>"
        calls = []

        def send(self, key, payload):
            self.calls.append((key, payload))
            if len(self.calls) == 1:
                raise TimeoutError("provider may have accepted")
            return "provider-123"

    sender = Sender()
    worker = EmailWorker(f["app"].state.pool, mode="resend", sender=sender)
    assert worker.process_one()
    with f["app"].state.pool.connection() as conn:
        conn.execute(
            "UPDATE task_followup_emails SET next_attempt_at=now() WHERE task_id=%s",
            (f["task"],),
        )
    assert worker.process_one()
    assert sender.calls[0] == sender.calls[1]
    assert logs(f)[0]["state"] == "sent"
    assert not worker.process_one()


def test_retry_stops_before_provider_deduplication_expires(flow):
    f = flow
    configure(f)
    connect(f)
    f["client"].patch(f"/api/v1/tasks/{f['task']}/review", json={"action": "approve"})
    with f["app"].state.pool.connection() as conn:
        conn.execute(
            "UPDATE task_followup_emails SET "
            "first_attempt_at=now()-interval '24 hours' "
            "WHERE task_id=%s",
            (f["task"],),
        )
    assert EmailWorker(f["app"].state.pool).process_one()
    assert logs(f)[0]["state"] == "failed"


def test_default_settings_do_not_send_or_auto_approve(flow):
    f = flow
    response = connect(f)
    assert response.json()["auto_approved_tasks"] == 0
    assert (
        f["client"]
        .patch(f"/api/v1/tasks/{f['task']}/review", json={"action": "approve"})
        .status_code
        == 200
    )
    assert not logs(f)
    assert not EmailWorker(f["app"].state.pool).process_one()


def test_expired_worker_claim_recovers_on_another_worker(flow):
    f = flow
    configure(f)
    connect(f)
    f["client"].patch(f"/api/v1/tasks/{f['task']}/review", json={"action": "approve"})
    with f["app"].state.pool.connection() as conn:
        conn.execute(
            "UPDATE task_followup_emails SET state='sending',claim_token=%s,"
            "lease_until=now()-interval '1 second' WHERE task_id=%s",
            (uuid4(), f["task"]),
        )
    assert EmailWorker(f["app"].state.pool).process_one()
    assert logs(f)[0]["state"] == "captured"
    assert not EmailWorker(f["app"].state.pool).process_one()
