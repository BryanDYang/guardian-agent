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
        SELECT {COLUMNS}, count(m.id) AS meeting_count,
            (SELECT count(*) FROM project_members WHERE project_id = p.id)
                AS member_count,
            COALESCE(max(m.created_at), p.created_at) AS last_activity_at
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
    return row | {
        "meeting_count": 0,
        "member_count": 1,
        "last_activity_at": row["created_at"],
    }


def list_members(conn: Connection, project_id: UUID) -> list[dict]:
    return conn.execute(
        """
        SELECT pm.user_id, p.display_name, p.email, pm.role
        FROM project_members pm JOIN profiles p ON p.id = pm.user_id
        WHERE pm.project_id = %s
        ORDER BY lower(coalesce(p.display_name, p.email)), pm.user_id
        """,
        (project_id,),
    ).fetchall()


def member_ids(conn: Connection, project_id: UUID) -> list[UUID]:
    rows = conn.execute(
        "SELECT user_id FROM project_members WHERE project_id = %s", (project_id,)
    ).fetchall()
    return [row["user_id"] for row in rows]


def co_member_ids(conn: Connection, user_id: UUID) -> list[UUID]:
    """Everyone else who shares at least one project with this user."""
    rows = conn.execute(
        """
        SELECT DISTINCT other.user_id FROM project_members mine
        JOIN project_members other ON other.project_id = mine.project_id
        WHERE mine.user_id = %s AND other.user_id <> %s
        """,
        (user_id, user_id),
    ).fetchall()
    return [row["user_id"] for row in rows]


def member_role(conn: Connection, project_id: UUID, user_id: UUID) -> str | None:
    row = conn.execute(
        "SELECT role FROM project_members WHERE project_id = %s AND user_id = %s",
        (project_id, user_id),
    ).fetchone()
    return row["role"] if row else None


def lock_owners(conn: Connection, project_id: UUID) -> list[UUID]:
    """The project's owners, locked so two owners can't remove each other at once."""
    rows = conn.execute(
        "SELECT user_id FROM project_members "
        "WHERE project_id = %s AND role = 'owner' FOR UPDATE",
        (project_id,),
    ).fetchall()
    return [row["user_id"] for row in rows]


def remove_member(conn: Connection, project_id: UUID, user_id: UUID) -> int:
    """End the membership and unassign the member's tasks in this project, in
    the caller's transaction. Returns how many tasks became unassigned."""
    conn.execute(
        "DELETE FROM project_members WHERE project_id = %s AND user_id = %s",
        (project_id, user_id),
    )
    return conn.execute(
        """
        UPDATE tasks SET assignee_user_id = NULL, owner_label = NULL,
            updated_at = now()
        WHERE project_id = %s AND assignee_user_id = %s
        """,
        (project_id, user_id),
    ).rowcount


def solo_projects(conn: Connection, user_id: UUID) -> list[UUID]:
    """Projects where this user is the only member."""
    rows = conn.execute(
        """
        SELECT pm.project_id FROM project_members pm
        WHERE pm.user_id = %s AND NOT EXISTS (
            SELECT 1 FROM project_members other
            WHERE other.project_id = pm.project_id AND other.user_id <> pm.user_id
        )
        """,
        (user_id,),
    ).fetchall()
    return [row["project_id"] for row in rows]


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
