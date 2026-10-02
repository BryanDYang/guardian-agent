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


def task_summary(conn: Connection, user_id: UUID) -> dict:
    """Approved tasks assigned to this user, in projects they still belong to."""
    return conn.execute(
        """
        SELECT
            count(*) FILTER (WHERE t.lifecycle_status = 'open') AS open,
            count(*) FILTER (
                WHERE t.lifecycle_status = 'open' AND t.due_date < current_date
            ) AS overdue,
            count(*) FILTER (WHERE t.lifecycle_status = 'done') AS done
        FROM tasks t
        JOIN project_members pm ON pm.project_id = t.project_id AND pm.user_id = %s
        WHERE t.assignee_user_id = %s AND t.review_status = 'approved'
        """,
        (user_id, user_id),
    ).fetchone()


def delete_account(conn: Connection, user_id: UUID) -> None:
    """FR-ACCT-4. Deleting the auth user cascades to the profile, memberships,
    and chat conversations. Shared content stays; its attribution columns
    become NULL through their foreign keys (FR-ACCT-5)."""
    conn.execute(
        "DELETE FROM project_invitations WHERE invited_by = %s AND status = 'pending'",
        (user_id,),
    )
    conn.execute("DELETE FROM auth.users WHERE id = %s", (user_id,))
