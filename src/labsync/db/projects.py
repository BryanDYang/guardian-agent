"""SQL for projects. No HTTP concerns here."""

from psycopg import Connection

COLUMNS = "p.id, p.name, p.image_url AS image_path, p.created_at, p.updated_at"


def list_projects(conn: Connection) -> list[dict]:
    return conn.execute(
        f"""
        SELECT {COLUMNS}, count(m.id) AS meeting_count
        FROM projects p
        LEFT JOIN meetings m ON m.project_id = p.id
        GROUP BY p.id
        ORDER BY p.created_at DESC
        """
    ).fetchall()


def create_project(conn: Connection, name: str, image_path: str | None) -> dict:
    row = conn.execute(
        f"""
        INSERT INTO projects AS p (name, image_url) VALUES (%s, %s)
        RETURNING {COLUMNS}
        """,
        (name, image_path),
    ).fetchone()
    return row | {"meeting_count": 0}