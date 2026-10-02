"""Project membership checks (spec D15): a user reaches project data only
through a project_members row. Roles are stored but not enforced yet, so any
member may do anything in the project. No HTTP concerns here."""

from uuid import UUID

from psycopg import Connection


def is_member(conn: Connection, user_id: UUID, project_id: UUID) -> bool:
    row = conn.execute(
        "SELECT 1 FROM project_members WHERE user_id = %s AND project_id = %s",
        (user_id, project_id),
    ).fetchone()
    return row is not None


def can_see_meeting(conn: Connection, user_id: UUID, meeting_id: UUID) -> bool:
    """A meeting is visible to the members of its project."""
    row = conn.execute(
        """
        SELECT 1 FROM meetings m
        JOIN project_members pm ON pm.project_id = m.project_id
        WHERE m.id = %s AND pm.user_id = %s
        """,
        (meeting_id, user_id),
    ).fetchone()
    return row is not None


def can_see_task(conn: Connection, user_id: UUID, task_id: UUID) -> bool:
    """A task is visible to the members of its project."""
    row = conn.execute(
        """
        SELECT 1 FROM tasks t
        JOIN project_members pm ON pm.project_id = t.project_id
        WHERE t.id = %s AND pm.user_id = %s
        """,
        (task_id, user_id),
    ).fetchone()
    return row is not None
