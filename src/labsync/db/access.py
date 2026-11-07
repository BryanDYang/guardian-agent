"""Project membership checks (spec D15): a user reaches project data only
through a membership in a project outside Recently Deleted. Destructive project
actions additionally require an owner role. No HTTP concerns here."""

from uuid import UUID

from psycopg import Connection


def is_member(conn: Connection, user_id: UUID, project_id: UUID) -> bool:
    row = conn.execute(
        "SELECT 1 FROM project_members pm JOIN projects p ON p.id=pm.project_id "
        "WHERE pm.user_id = %s AND pm.project_id = %s "
        "AND p.deleted_at IS NULL FOR SHARE OF p",
        (user_id, project_id),
    ).fetchone()
    return row is not None


def can_see_meeting(conn: Connection, user_id: UUID, meeting_id: UUID) -> bool:
    """A meeting is visible to the members of its project."""
    row = conn.execute(
        """
        SELECT 1 FROM meetings m
        JOIN project_members pm ON pm.project_id = m.project_id
        JOIN projects p ON p.id=m.project_id
        WHERE m.id = %s AND pm.user_id = %s AND p.deleted_at IS NULL
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
        JOIN projects p ON p.id=t.project_id
        WHERE t.id = %s AND pm.user_id = %s AND p.deleted_at IS NULL
        """,
        (task_id, user_id),
    ).fetchone()
    return row is not None
