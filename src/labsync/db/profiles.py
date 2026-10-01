"""SQL for user profiles. Rows are created by the database trigger on auth.users."""

from uuid import UUID

from psycopg import Connection

COLUMNS = (
    "id, email, display_name, title, avatar_url, auth_provider, "
    "onboarding_completed_at, created_at, updated_at"
)


def get_profile(conn: Connection, user_id: UUID) -> dict | None:
    return conn.execute(
        f"SELECT {COLUMNS} FROM profiles WHERE id = %s", (user_id,)
    ).fetchone()


def update_profile(conn: Connection, user_id: UUID, **fields) -> dict:
    """Set only the given columns. Callers pass validated values."""
    assignments = ", ".join(f"{column} = %({column})s" for column in fields)
    return conn.execute(
        f"""
        UPDATE profiles SET {assignments}, updated_at = now()
        WHERE id = %(user_id)s
        RETURNING {COLUMNS}
        """,
        fields | {"user_id": user_id},
    ).fetchone()


def pending_invitation_count(conn: Connection, email: str) -> int:
    return conn.execute(
        "SELECT count(*) AS n FROM project_invitations "
        "WHERE email = %s AND status = 'pending' AND expires_at > now()",
        (email,),
    ).fetchone()["n"]
