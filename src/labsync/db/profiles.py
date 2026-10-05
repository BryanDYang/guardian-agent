"""SQL for user profiles. Rows are created by the database trigger on auth.users."""

import json
from uuid import UUID

from psycopg import Connection
from psycopg.types.json import Jsonb

from ..embeddings import to_pgvector

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


def voice_status(conn: Connection, user_id: UUID) -> dict:
    """What the app may know about a voiceprint. Never the embedding (FR-VOICE-7)."""
    return conn.execute(
        """
        SELECT
            EXISTS (
                SELECT 1 FROM voice_consents
                WHERE user_id = %(user)s AND revoked_at IS NULL
            ) AS consented,
            vp.enrolled_at, vp.embedding_model_id
        FROM (SELECT 1) AS one
        LEFT JOIN voice_profiles vp ON vp.user_id = %(user)s
        """,
        {"user": user_id},
    ).fetchone()


def grant_voice_consent(conn: Connection, user_id: UUID, version: str) -> None:
    """Agreeing to a newer consent text replaces the older one in the history."""
    conn.execute(
        "UPDATE voice_consents SET revoked_at = now() "
        "WHERE user_id = %s AND revoked_at IS NULL AND consent_version <> %s",
        (user_id, version),
    )
    conn.execute(
        """
        INSERT INTO voice_consents (user_id, consent_version) VALUES (%s, %s)
        ON CONFLICT (user_id) WHERE revoked_at IS NULL DO NOTHING
        """,
        (user_id, version),
    )


def revoke_voice_consent(conn: Connection, user_id: UUID) -> None:
    """FR-VOICE-8: the voiceprint goes in the same transaction."""
    conn.execute(
        "UPDATE voice_consents SET revoked_at = now() "
        "WHERE user_id = %s AND revoked_at IS NULL",
        (user_id,),
    )
    conn.execute("DELETE FROM voice_profiles WHERE user_id = %s", (user_id,))


def save_voice_profile(
    conn: Connection,
    user_id: UUID,
    embedding: list[float],
    model_id: str,
    quality: dict,
) -> None:
    """Replaces any earlier voiceprint (FR-VOICE-5, FR-VOICE-9)."""
    conn.execute(
        """
        INSERT INTO voice_profiles (user_id, embedding, embedding_model_id, quality)
        VALUES (%s, %s::vector, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            embedding = EXCLUDED.embedding,
            embedding_model_id = EXCLUDED.embedding_model_id,
            quality = EXCLUDED.quality,
            enrolled_at = now()
        """,
        (user_id, to_pgvector(embedding), model_id, Jsonb(quality)),
    )


def voice_candidates(conn: Connection, project_id: UUID, model_id: str) -> list[dict]:
    """Members of the project who may be recognized in its meetings: active
    consent, a name, and a voiceprint from `model_id` (FR-SPK-3, FR-SPK-8)."""
    rows = conn.execute(
        """
        SELECT p.id AS user_id, p.display_name AS name, p.email::text AS email,
               vp.embedding::text AS embedding
        FROM project_members m
        JOIN profiles p ON p.id = m.user_id
        JOIN voice_profiles vp ON vp.user_id = m.user_id
        WHERE m.project_id = %s
          AND vp.embedding_model_id = %s
          AND btrim(coalesce(p.display_name, '')) <> ''
          AND EXISTS (
              SELECT 1 FROM voice_consents c
              WHERE c.user_id = m.user_id AND c.revoked_at IS NULL
          )
        ORDER BY p.display_name, p.id
        """,
        (project_id, model_id),
    ).fetchall()
    return [
        row
        | {"user_id": str(row["user_id"]), "embedding": json.loads(row["embedding"])}
        for row in rows
    ]


def delete_account(conn: Connection, user_id: UUID) -> None:
    """FR-ACCT-4. Deleting the auth user cascades to the profile, memberships,
    and chat conversations. Shared content stays; its attribution columns
    become NULL through their foreign keys (FR-ACCT-5)."""
    conn.execute(
        "DELETE FROM project_invitations WHERE invited_by = %s AND status = 'pending'",
        (user_id,),
    )
    conn.execute("DELETE FROM auth.users WHERE id = %s", (user_id,))
