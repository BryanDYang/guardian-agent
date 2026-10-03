"""SQL for tasks and their audit log. No HTTP concerns here."""

from datetime import date
from uuid import UUID

from psycopg import Connection
from psycopg.types.json import Jsonb

# A task is assigned to a project member (assignee_user_id), to a speaker the
# diarizer found who isn't a member (owner_label, e.g. SPEAKER_1), or to nobody.
# The source fields let the Tasks tab show where a task came from.
COLUMNS = """
    t.id, t.project_id, t.meeting_id, t.title, t.category, t.owner_label,
    t.attendee_id, t.assignee_user_id, t.due_date, t.due_date_text,
    t.review_status, t.lifecycle_status, t.updated_at,
    (SELECT p.display_name FROM profiles p WHERE p.id = t.assignee_user_id)
        AS assignee_name,
    (SELECT m.name FROM meetings m WHERE m.id = t.meeting_id) AS meeting_name,
    (SELECT e.quote FROM item_evidence e WHERE e.task_id = t.id
     ORDER BY e.position LIMIT 1) AS quote,
    (SELECT e.timestamp_ms FROM item_evidence e WHERE e.task_id = t.id
     ORDER BY e.position LIMIT 1) AS timestamp_ms
"""


def list_calendar_tasks(
    conn: Connection, project_id: UUID, start: date, end: date
) -> list[dict]:
    """Approved tasks due within [start, end]. Pending and dismissed tasks never
    reach the calendar; approval requires a due date."""
    return conn.execute(
        f"""
        SELECT {COLUMNS} FROM tasks t
        WHERE t.project_id = %s AND t.review_status = 'approved'
          AND t.due_date BETWEEN %s AND %s
        ORDER BY t.due_date, t.created_at
        """,
        (project_id, start, end),
    ).fetchall()


def lock_task(conn: Connection, task_id: UUID) -> dict | None:
    """Read a task and hold its row until the transaction ends, so two requests
    can't change the same task at once."""
    return conn.execute(
        f"SELECT {COLUMNS} FROM tasks t WHERE t.id = %s FOR UPDATE", (task_id,)
    ).fetchone()


def update_review(
    conn: Connection,
    task_id: UUID,
    *,
    review_status: str,
    title: str,
    assignee_user_id: UUID | None,
    owner_label: str | None,
    due_date: date | None,
    approved_by: UUID | None,
) -> dict:
    """approved_by is the approving user, or None for edit and dismiss."""
    return conn.execute(
        f"""
        UPDATE tasks t
        SET review_status = %s, title = %s, assignee_user_id = %s,
            owner_label = %s, due_date = %s, approved_by = %s,
            approved_at = CASE WHEN %s::uuid IS NULL THEN NULL ELSE now() END,
            updated_at = now()
        WHERE t.id = %s
        RETURNING {COLUMNS}
        """,
        (
            review_status,
            title,
            assignee_user_id,
            owner_label,
            due_date,
            approved_by,
            approved_by,
            task_id,
        ),
    ).fetchone()


def update_details(
    conn: Connection,
    task_id: UUID,
    *,
    title: str,
    assignee_user_id: UUID | None,
    owner_label: str | None,
    due_date: date,
) -> dict:
    """Edit an approved task without touching its review or lifecycle status."""
    return conn.execute(
        f"""
        UPDATE tasks t
        SET title = %s, assignee_user_id = %s, owner_label = %s, due_date = %s,
            updated_at = now()
        WHERE t.id = %s
        RETURNING {COLUMNS}
        """,
        (title, assignee_user_id, owner_label, due_date, task_id),
    ).fetchone()


def is_speaker(conn: Connection, meeting_id: UUID | None, label: str) -> bool:
    """A diarizer label (e.g. SPEAKER_1) that speaks in this meeting. UNKNOWN is
    an unresolved label, so it can't own a task."""
    if meeting_id is None or label.upper() == "UNKNOWN":
        return False
    row = conn.execute(
        "SELECT 1 FROM meeting_transcripts "
        "WHERE meeting_id = %s AND speaker_label = %s LIMIT 1",
        (meeting_id, label),
    ).fetchone()
    return row is not None


def set_lifecycle(
    conn: Connection, task_id: UUID, old: str, new: str, action: str, actor_id: UUID
) -> tuple[dict, UUID]:
    """Change lifecycle_status and append the audit row that can undo it."""
    task = conn.execute(
        f"""
        UPDATE tasks t SET lifecycle_status = %s, updated_at = now()
        WHERE t.id = %s
        RETURNING {COLUMNS}
        """,
        (new, task_id),
    ).fetchone()
    token = conn.execute(
        """
        INSERT INTO task_audit_log (task_id, action, old_value, new_value, actor_id)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING revert_token
        """,
        (
            task_id,
            action,
            Jsonb({"lifecycle_status": old}),
            Jsonb({"lifecycle_status": new}),
            actor_id,
        ),
    ).fetchone()["revert_token"]
    return task, token


def find_audit(conn: Connection, revert_token: UUID) -> dict | None:
    return conn.execute(
        "SELECT id, task_id, old_value FROM task_audit_log WHERE revert_token = %s",
        (revert_token,),
    ).fetchone()


def latest_audit_id(conn: Connection, task_id: UUID) -> UUID:
    return conn.execute(
        """
        SELECT id FROM task_audit_log WHERE task_id = %s
        ORDER BY created_at DESC LIMIT 1
        """,
        (task_id,),
    ).fetchone()["id"]
