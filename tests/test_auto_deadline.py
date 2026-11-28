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
