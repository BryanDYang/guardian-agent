"""HTTP rehearsal of a later recording revising one accepted commitment."""

from uuid import uuid4

import pytest
from test_followup import DATABASE_URL, configure, connect
from test_followup import flow as followup_flow

from labsync.db import meetings
from labsync.extraction import Transcript

pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")

QUOTE = (
    "Yeah, I know I originally said Monday, December 7th, but that's too late now. "
    "I'll process this recording tonight and have all three meetings connected "
    "by tomorrow at 9 a.m."
)


@pytest.fixture
def flow(tmp_path, make_user, embedder, monkeypatch):
    yield from followup_flow.__wrapped__(tmp_path, make_user, embedder, monkeypatch)


@pytest.fixture
def revision(flow):
    f = flow
    configure(f)
    connect(f)
    c = f["client"]
    response = c.patch(
        f"/api/v1/tasks/{f['task']}/review",
        json={
            "action": "approve",
            "title": "Process all three demo recordings",
            "due_date": "2026-12-07",
        },
    )
    assert response.status_code == 200, response.text
    mid, turn = str(uuid4()), "later:0"
    with f["app"].state.pool.connection() as conn:
        conn.execute(
            "UPDATE meetings SET meeting_date='2026-12-02' WHERE id=%s", (f["meeting"],)
        )
        meetings.create_meeting(
            conn,
            meeting_id=mid,
            project_id=f["project"],
            name="Next team meeting",
            meeting_date="2026-12-03",
            audio_file_path="",
        )
        transcript = Transcript.model_validate(
            {
                "project_id": f["project"],
                "meeting_id": mid,
                "turns": [
                    {
                        "id": turn,
                        "speaker": "SPEAKER_2",
                        "start_time_ms": 227480,
                        "end_time_ms": 250800,
                        "content": QUOTE,
                    }
                ],
            }
        )
        meetings.save_results(
            conn,
            mid,
            transcript,
            {
                "extraction": {
                    "summary": "",
                    "decisions": [],
                    "suggestions": [],
                    "commitments": [
                        {
                            "title": (
                                "Process this recording and have all three "
                                "meetings connected"
                            ),
                            "owner": "SPEAKER_2",
                            "due_date_text": "tomorrow at 9 a.m.",
                            "evidence": [{"transcript_id": turn, "quote": QUOTE}],
                        }
                    ],
                }
            },
            {},
        )
        meetings.update_status(conn, mid, "completed", 1, None)
        source = conn.execute(
            "SELECT id FROM tasks WHERE meeting_id=%s", (mid,)
        ).fetchone()["id"]
    return f | {"later": mid, "source": source}


def trigger(f):
    assert configure(f, auto=True).status_code == 200
    r = f["client"].put(
        f"/api/v1/meetings/{f['later']}/speakers/SPEAKER_2",
        json={"name": "Recipient", "assignee_user_id": str(f["recipient_id"])},
    )
    assert r.status_code == 200, r.text


def test_deadline_revision_http(revision):
    f = revision
    trigger(f)
    accepted = (
        f["client"]
        .get("/api/v1/tasks/accepted", params={"project_id": f["project"]})
        .json()
    )
    assert len(accepted) == 1
    assert accepted[0]["id"] == f["task"]
    assert accepted[0]["due_date"] == "2026-12-04"
    assert accepted[0]["meeting_id"] == f["meeting"]
    with f["app"].state.pool.connection() as conn:
        assert (
            conn.execute(
                "SELECT review_status FROM tasks WHERE id=%s", (f["source"],)
            ).fetchone()["review_status"]
            == "dismissed"
        )
        audit = conn.execute(
            "SELECT new_value FROM task_audit_log WHERE task_id=%s "
            "AND action='AUTO_DEADLINE'",
            (f["task"],),
        ).fetchone()["new_value"]
        assert audit["quote"] == QUOTE
        assert audit["timestamp_ms"] == 227480
    trigger(f)  # Re-confirmation is idempotent.
    changes = f["client"].get(f"/api/v1/tasks/{f['task']}/changes").json()
    assert len([x for x in changes if x["action"] == "AUTO_DEADLINE"]) == 1


@pytest.mark.parametrize(
    "block",
    [
        "disabled",
        "unconfirmed",
        "owner",
        "completed",
        "archived",
        "deleted",
        "old_date",
        "different_work",
        "ambiguous",
        "edited",
        "unquoted",
        "uncertain",
        "earlier",
        "newer_update",
        "busy",
        "source_archived",
    ],
)
def test_uncertain_revision_stays_pending(revision, block):
    f = revision
    pool = f["app"].state.pool
    with pool.connection() as conn:
        if block == "owner":
            conn.execute(
                "UPDATE tasks SET assignee_user_id=%s WHERE id=%s",
                (f["owner_id"], f["task"]),
            )
        elif block == "completed":
            conn.execute(
                "UPDATE tasks SET lifecycle_status='done' WHERE id=%s", (f["task"],)
            )
        elif block in {"archived", "deleted"}:
            conn.execute(f"UPDATE tasks SET {block}_at=now() WHERE id=%s", (f["task"],))
        elif block == "source_archived":
            conn.execute(
                "UPDATE tasks SET archived_at=now() WHERE id=%s", (f["source"],)
            )
        elif block == "old_date":
            conn.execute(
                "UPDATE tasks SET due_date='2026-12-08' WHERE id=%s", (f["task"],)
            )
        elif block == "different_work":
            conn.execute(
                "UPDATE tasks SET title='Process three interview recordings' "
                "WHERE id=%s",
                (f["task"],),
            )
        elif block == "ambiguous":
            conn.execute(
                "INSERT INTO tasks(project_id,meeting_id,title,assignee_user_id,"
                "due_date,review_status,category) SELECT project_id,meeting_id,title,"
                "assignee_user_id,due_date,review_status,category FROM tasks "
                "WHERE id=%s",
                (f["task"],),
            )
        elif block in {"edited", "newer_update"}:
            action = "DETAILS_EDIT" if block == "edited" else "AUTO_DEADLINE"
            conn.execute(
                "INSERT INTO task_audit_log(task_id,action) VALUES (%s,%s)",
                (f["task"], action),
            )
        elif block == "unquoted":
            conn.execute(
                "UPDATE meeting_transcripts SET content='No promise here.' "
                "WHERE meeting_id=%s",
                (f["later"],),
            )
        elif block == "uncertain":
            uncertain = QUOTE.replace("I'll process", "I might process")
            conn.execute(
                "UPDATE meeting_transcripts SET content=%s WHERE meeting_id=%s",
                (uncertain, f["later"]),
            )
            conn.execute(
                "UPDATE item_evidence SET quote=%s WHERE task_id=%s",
                (uncertain, f["source"]),
            )
        elif block == "earlier":
            conn.execute(
                "UPDATE meetings SET meeting_date='2026-12-03' WHERE id=%s",
                (f["meeting"],),
            )
    held = pool.getconn() if block == "busy" else None
    try:
        if held:
            held.execute("SELECT id FROM tasks WHERE id=%s FOR UPDATE", (f["task"],))
        if block == "disabled":
            r = f["client"].put(
                f"/api/v1/meetings/{f['later']}/speakers/SPEAKER_2",
                json={"name": "Recipient", "assignee_user_id": str(f["recipient_id"])},
            )
            assert r.status_code == 200
        elif block == "unconfirmed":
            assert configure(f, auto=True).status_code == 200
        else:
            trigger(f)
    finally:
        if held:
            held.rollback()
            pool.putconn(held)
    with pool.connection() as conn:
        source = conn.execute(
            "SELECT review_status FROM tasks WHERE id=%s", (f["source"],)
        ).fetchone()
        assert source["review_status"] == "pending"
        assert not conn.execute(
            "SELECT 1 FROM task_audit_log WHERE task_id=%s "
            "AND new_value->>'policy'='explicit-deadline-revision-v1'",
            (f["task"],),
        ).fetchone()


def test_approving_earlier_task_rechecks_already_confirmed_later_meeting(revision):
    f = revision
    # Fixture setup: both recordings already exist; the earlier task is still
    # pending when automation and the later speaker are confirmed.
    with f["app"].state.pool.connection() as conn:
        conn.execute(
            "UPDATE tasks SET review_status='pending',approved_at=NULL WHERE id=%s",
            (f["task"],),
        )
    trigger(f)
    response = f["client"].patch(
        f"/api/v1/tasks/{f['task']}/review", json={"action": "approve"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["task"]["due_date"] == "2026-12-04"
    assert response.json()["eventkit"]["due_date"] == "2026-12-04"
    accepted = (
        f["client"]
        .get("/api/v1/tasks/accepted", params={"project_id": f["project"]})
        .json()
    )
    assert len(accepted) == 1
    assert accepted[0]["id"] == f["task"]
    assert accepted[0]["due_date"] == "2026-12-04"
    changes = f["client"].get(f"/api/v1/tasks/{f['task']}/changes").json()
    assert sum(x["action"] == "AUTO_DEADLINE" for x in changes) == 1


def test_revision_uses_adjacent_transcript_context(revision):
    f = revision
    promise = QUOTE[QUOTE.index("I'll process") :]
    with f["app"].state.pool.connection() as conn:
        conn.execute(
            "UPDATE item_evidence SET quote=%s WHERE task_id=%s", (promise, f["source"])
        )
    trigger(f)
    accepted = (
        f["client"]
        .get("/api/v1/tasks/accepted", params={"project_id": f["project"]})
        .json()
    )
    assert accepted[0]["due_date"] == "2026-12-04"


def test_short_quote_cannot_borrow_unrelated_old_date(revision):
    f = revision
    promise = QUOTE[QUOTE.index("I'll process") :]
    content = QUOTE.replace(
        "I'll process", "We also discussed another task. I'll process"
    )
    with f["app"].state.pool.connection() as conn:
        conn.execute(
            "UPDATE item_evidence SET quote=%s WHERE task_id=%s", (promise, f["source"])
        )
        conn.execute(
            "UPDATE meeting_transcripts SET content=%s WHERE meeting_id=%s",
            (content, f["later"]),
        )
    trigger(f)
    task = (
        f["client"]
        .get("/api/v1/tasks/accepted", params={"project_id": f["project"]})
        .json()[0]
    )
    assert task["due_date"] == "2026-12-07"


def test_automatic_revision_sends_distinct_change_email_once(revision):
    from test_followup import logs

    from labsync.followup import EmailWorker, enqueue

    f = revision
    worker = EmailWorker(f["app"].state.pool)
    assert worker.process_one()
    assert "2026-12-07" in logs(f)[0]["preview"]
    trigger(f)
    assert worker.process_one()
    assert not worker.process_one()
    messages = logs(f)
    assert len(messages) == 2
    change = next(x for x in messages if x["title"].startswith("Deadline updated:"))
    assert "Previous deadline: 2026-12-07" in change["preview"]
    assert "New deadline: 2026-12-04" in change["preview"]
    assert QUOTE in change["preview"]
    with f["app"].state.pool.connection() as conn:
        audit = conn.execute(
            "SELECT id FROM task_audit_log WHERE task_id=%s AND action='AUTO_DEADLINE'",
            (f["task"],),
        ).fetchone()["id"]
        task = conn.execute("SELECT * FROM tasks WHERE id=%s", (f["task"],)).fetchone()
        enqueue(conn, task, change_id=audit)
    trigger(f)
    assert len(logs(f)) == 2


@pytest.mark.parametrize("block", ["project", "recipient", "superseded", "completed"])
def test_deadline_email_respects_current_state(revision, block):
    from test_followup import logs

    from labsync.followup import EmailWorker

    f = revision
    worker = EmailWorker(f["app"].state.pool)
    assert worker.process_one()
    trigger(f)
    with f["app"].state.pool.connection() as conn:
        if block == "project":
            conn.execute(
                "UPDATE projects SET followup_email_enabled=false WHERE id=%s",
                (f["project"],),
            )
        elif block == "recipient":
            conn.execute(
                "UPDATE project_members SET followup_email_enabled=false "
                "WHERE project_id=%s",
                (f["project"],),
            )
        elif block == "superseded":
            conn.execute(
                "UPDATE tasks SET due_date='2026-12-05',updated_at=now() WHERE id=%s",
                (f["task"],),
            )
        else:
            conn.execute(
                "UPDATE tasks SET lifecycle_status='done',updated_at=now() WHERE id=%s",
                (f["task"],),
            )
    assert worker.process_one()
    change = next(x for x in logs(f) if x["title"].startswith("Deadline updated:"))
    assert change["state"] == "cancelled"


def test_manual_date_edit_sends_change_email(revision):
    from test_followup import logs

    from labsync.followup import EmailWorker

    f = revision
    worker = EmailWorker(f["app"].state.pool)
    assert worker.process_one()
    response = f["client"].patch(
        f"/api/v1/tasks/{f['task']}", json={"due_date": "2026-12-04"}
    )
    assert response.status_code == 200, response.text
    assert worker.process_one()
    change = next(x for x in logs(f) if x["title"].startswith("Deadline updated:"))
    assert "Previous deadline: 2026-12-07" in change["preview"]
    assert "New deadline: 2026-12-04" in change["preview"]
    assert "Supporting meeting evidence" not in change["preview"]
