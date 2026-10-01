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
