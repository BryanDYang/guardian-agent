"""SQL for projects. No HTTP concerns here."""

from uuid import UUID

from psycopg import Connection


class ProjectBusyError(Exception):
    """A project still has meetings being processed."""


COLUMNS = "p.id, p.name, p.image_url AS image_path, p.created_at, p.updated_at"


def list_projects(conn: Connection, user_id: UUID) -> list[dict]:
    """Only projects this user is a member of."""
    return conn.execute(
        f"""
        SELECT {COLUMNS}, count(m.id) AS meeting_count
        FROM projects p
        JOIN project_members pm ON pm.project_id = p.id AND pm.user_id = %s
        LEFT JOIN meetings m ON m.project_id = p.id
        GROUP BY p.id
        ORDER BY p.created_at DESC
        """,
        (user_id,),
    ).fetchall()


def create_project(
    conn: Connection, name: str, image_path: str | None, created_by: UUID
) -> dict:
    """The creator becomes the first member, in the same transaction."""
    row = conn.execute(
        f"""
        INSERT INTO projects AS p (name, image_url, created_by) VALUES (%s, %s, %s)
        RETURNING {COLUMNS}
        """,
        (name, image_path, created_by),
    ).fetchone()
    conn.execute(
        "INSERT INTO project_members (project_id, user_id, role) "
        "VALUES (%s, %s, 'owner')",
        (row["id"], created_by),
    )
    return row | {"meeting_count": 0}


def delete_project(conn: Connection, project_id: UUID) -> bool:
    # Lock the parent before checking children so concurrent inserts cannot slip in.
    if not conn.execute(
        "SELECT id FROM projects WHERE id = %s FOR UPDATE", (project_id,)
    ).fetchone():
        return False
    if conn.execute(
        "SELECT id FROM meetings WHERE project_id = %s "
        "AND status IN ('queued', 'transcribing', 'diarizing', 'extracting') LIMIT 1",
        (project_id,),
    ).fetchone():
        raise ProjectBusyError
    return (
        conn.execute(
            "DELETE FROM projects WHERE id = %s RETURNING id", (project_id,)
        ).fetchone()
        is not None
    )
