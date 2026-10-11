"""Durable job claims. Every write is fenced by a fresh claim token and lease."""

from uuid import uuid4

from psycopg.types.json import Jsonb


class LeaseLost(RuntimeError):
    pass


def claim(conn, worker_id, lease_seconds):
    # Serialize claims per project so connected meetings retain ingestion order.
    # Different projects can process concurrently on different workers.
    project = conn.execute(
        """SELECT p.id FROM projects p
        WHERE EXISTS (
            SELECT 1 FROM meeting_jobs j JOIN meetings m ON m.id=j.meeting_id
            WHERE m.project_id=p.id AND (j.state='queued' OR
                (j.state='running' AND j.lease_until < now())))
        AND NOT EXISTS (
            SELECT 1 FROM meeting_jobs j JOIN meetings m ON m.id=j.meeting_id
            WHERE m.project_id=p.id AND j.state='running' AND j.lease_until > now())
        ORDER BY (SELECT min(j.created_at) FROM meeting_jobs j
            JOIN meetings m ON m.id=j.meeting_id WHERE m.project_id=p.id
            AND j.state IN ('queued','running'))
        FOR UPDATE OF p SKIP LOCKED LIMIT 1"""
    ).fetchone()
    if not project:
        return None
    row = conn.execute(
        """SELECT j.* FROM meeting_jobs j JOIN meetings m ON m.id=j.meeting_id
        WHERE m.project_id=%s AND (j.state='queued' OR
            (j.state='running' AND j.lease_until < now()))
        ORDER BY j.created_at FOR UPDATE OF j SKIP LOCKED LIMIT 1""",
        (project["id"],),
    ).fetchone()
    if not row:
        return None
    record = row["record"]
    if row["state"] == "running":
        record["attempt"] += 1
    record.update(status="transcribing", error=None)
    token = uuid4()
    conn.execute(
        """UPDATE meeting_jobs SET state='running', claim_token=%s, worker_id=%s,
        lease_until=now() + %s * interval '1 second', record=%s, updated_at=now()
        WHERE meeting_id=%s""",
        (token, worker_id, lease_seconds, Jsonb(record), row["meeting_id"]),
    )
    conn.execute(
        """UPDATE meetings SET status='transcribing', processing_attempt=%s,
        error_message=NULL, updated_at=now() WHERE id=%s""",
        (record["attempt"], row["meeting_id"]),
    )
    return row | {"record": record, "claim_token": token}


def guard(conn, meeting_id, token):
    row = conn.execute(
        """SELECT * FROM meeting_jobs WHERE meeting_id=%s AND claim_token=%s
        AND state='running' AND lease_until > now() FOR UPDATE""",
        (meeting_id, token),
    ).fetchone()
    if not row:
        raise LeaseLost("Processing claim expired or was replaced")
    return row


def heartbeat(conn, meeting_id, token, lease_seconds):
    return (
        conn.execute(
            """UPDATE meeting_jobs SET lease_until=now() + %s * interval '1 second'
        WHERE meeting_id=%s AND claim_token=%s AND state='running'
        AND lease_until > now()""",
            (lease_seconds, meeting_id, token),
        ).rowcount
        == 1
    )


def finish(conn, meeting_id, token, record, state):
    guard(conn, meeting_id, token)
    conn.execute(
        """UPDATE meeting_jobs SET record=%s, state=%s, lease_until=NULL,
        updated_at=now() WHERE meeting_id=%s""",
        (Jsonb(record), state, meeting_id),
    )


def clean_uploads(conn):
    # An upload interrupted before it was queued is never processed as complete.
    rows = conn.execute(
        """SELECT * FROM meeting_jobs WHERE state='uploading'
        AND created_at < now() - interval '1 hour' FOR UPDATE SKIP LOCKED"""
    ).fetchall()
    for row in rows:
        conn.execute("DELETE FROM meetings WHERE id=%s", (row["meeting_id"],))
