"""SQL for project invitations (spec Section 6.5). No HTTP concerns here.

Only a SHA-256 hash of each token is stored. The token itself exists once,
in the invite link the backend returns."""

import hashlib
import secrets
from uuid import UUID

from psycopg import Connection

COLUMNS = """
    i.id, i.project_id, p.name AS project_name, i.email, i.status, i.expires_at,
    i.created_at, inviter.display_name AS invited_by_name
"""
FROM = """
    FROM project_invitations i
    JOIN projects p ON p.id = i.project_id
    LEFT JOIN profiles inviter ON inviter.id = i.invited_by
"""
OPEN = "i.status = 'pending' AND i.expires_at > now()"


def token_hash(token: str) -> bytes:
    return hashlib.sha256(token.encode()).digest()


def is_member(conn: Connection, project_id: UUID, email: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM project_members m JOIN profiles u ON u.id = m.user_id "
            "WHERE m.project_id = %s AND u.email = %s",
            (project_id, email),
        ).fetchone()
        is not None
    )


def create(
    conn: Connection, project_id: UUID, email: str, invited_by: UUID
) -> tuple[dict, str]:
    """Returns (invitation, token). Re-inviting a pending email reuses its row
    with a fresh token and expiry, so an older link stops working (FR-INV-2)."""
    token = secrets.token_urlsafe(32)
    invitation_id = conn.execute(
        """
        INSERT INTO project_invitations
            (project_id, email, token_hash, invited_by, expires_at)
        VALUES (%s, %s, %s, %s, now() + interval '7 days')
        ON CONFLICT (project_id, email) WHERE status = 'pending' DO UPDATE
        SET token_hash = EXCLUDED.token_hash,
            invited_by = EXCLUDED.invited_by,
            expires_at = EXCLUDED.expires_at
        RETURNING id
        """,
        (project_id, email, token_hash(token), invited_by),
    ).fetchone()["id"]
    return get(conn, invitation_id), token


def get(conn: Connection, invitation_id: UUID) -> dict | None:
    return conn.execute(
        f"SELECT {COLUMNS} {FROM} WHERE i.id = %s", (invitation_id,)
    ).fetchone()


def find_by_token(conn: Connection, token: str) -> dict | None:
    return conn.execute(
        f"SELECT {COLUMNS} {FROM} WHERE i.token_hash = %s", (token_hash(token),)
    ).fetchone()


def list_for_project(conn: Connection, project_id: UUID) -> list[dict]:
    return conn.execute(
        f"SELECT {COLUMNS} {FROM} WHERE i.project_id = %s AND {OPEN} "
        "ORDER BY i.created_at DESC",
        (project_id,),
    ).fetchall()


def list_for_email(conn: Connection, email: str) -> list[dict]:
    return conn.execute(
        f"SELECT {COLUMNS} {FROM} WHERE i.email = %s AND {OPEN} "
        "ORDER BY i.created_at DESC",
        (email,),
    ).fetchall()


def resolve(
    conn: Connection, invitation_id: UUID, status: str, user_id: UUID | None = None
) -> bool:
    """Close a pending invitation as accepted, declined, or revoked. False if
    it was no longer pending (another request got there first)."""
    return (
        conn.execute(
            "UPDATE project_invitations "
            "SET status = %s, accepted_by = %s, resolved_at = now() "
            "WHERE id = %s AND status = 'pending' RETURNING id",
            (status, user_id, invitation_id),
        ).fetchone()
        is not None
    )


def accept(conn: Connection, invitation: dict, user_id: UUID) -> bool:
    """FR-INV-7: membership and the accepted status land in one transaction
    (the request's connection commits both or neither)."""
    if not resolve(conn, invitation["id"], "accepted", user_id):
        return False
    conn.execute(
        "INSERT INTO project_members (project_id, user_id, role) "
        "VALUES (%s, %s, 'member') ON CONFLICT DO NOTHING",
        (invitation["project_id"], user_id),
    )
    return True
