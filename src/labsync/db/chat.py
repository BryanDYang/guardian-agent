"""SQL for chat conversations and messages. No HTTP concerns here."""

from uuid import UUID

from psycopg import Connection
from psycopg.types.json import Jsonb

CONVERSATION = """
    c.id, c.project_id, c.meeting_id, m.name AS meeting_name, c.title,
    c.created_at, c.updated_at
"""


def meeting_in_project(conn: Connection, meeting_id: UUID, project_id: UUID) -> bool:
    row = conn.execute(
        "SELECT 1 FROM meetings WHERE id = %s AND project_id = %s",
        (meeting_id, project_id),
    ).fetchone()
    return row is not None


def create_conversation(
    conn: Connection, project_id: UUID, meeting_id: UUID | None
) -> dict:
    created = conn.execute(
        """
        INSERT INTO chat_conversations (project_id, meeting_id)
        VALUES (%s, %s) RETURNING id
        """,
        (project_id, meeting_id),
    ).fetchone()
    return get_conversation(conn, created["id"])


def get_conversation(conn: Connection, conversation_id: UUID) -> dict | None:
    return conn.execute(
        f"""
        SELECT {CONVERSATION}
        FROM chat_conversations c LEFT JOIN meetings m ON m.id = c.meeting_id
        WHERE c.id = %s
        """,
        (conversation_id,),
    ).fetchone()


def list_conversations(conn: Connection, project_id: UUID | None) -> list[dict]:
    """Newest first. Conversations with no messages yet are left out."""
    return conn.execute(
        f"""
        SELECT {CONVERSATION}
        FROM chat_conversations c LEFT JOIN meetings m ON m.id = c.meeting_id
        WHERE (%(project_id)s::uuid IS NULL OR c.project_id = %(project_id)s::uuid)
          AND EXISTS (SELECT 1 FROM chat_messages x WHERE x.conversation_id = c.id)
        ORDER BY c.updated_at DESC, c.id
        LIMIT 200
        """,
        {"project_id": project_id},
    ).fetchall()


def list_messages(
    conn: Connection, conversation_id: UUID, limit: int | None = None
) -> list[dict]:
    """Oldest first. With a limit, the most recent `limit` messages."""
    return conn.execute(
        """
        SELECT * FROM (
            SELECT id, role, content, citations, created_at
            FROM chat_messages WHERE conversation_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT %s
        ) recent
        ORDER BY created_at, id
        """,
        (conversation_id, limit),
    ).fetchall()


def add_exchange(
    conn: Connection,
    conversation_id: UUID,
    question: str,
    answer: str,
    citations: list[dict],
) -> tuple[dict, dict]:
    """Store one question and its answer, and title the thread by its first
    question. Both rows commit together."""
    user = conn.execute(
        """
        INSERT INTO chat_messages (conversation_id, role, content)
        VALUES (%s, 'user', %s)
        RETURNING id, role, content, citations, created_at
        """,
        (conversation_id, question),
    ).fetchone()
    # clock_timestamp() so the answer sorts after the question within one
    # transaction; now() would give both rows the same time.
    assistant = conn.execute(
        """
        INSERT INTO chat_messages
            (conversation_id, role, content, citations, created_at)
        VALUES (%s, 'assistant', %s, %s, clock_timestamp())
        RETURNING id, role, content, citations, created_at
        """,
        (conversation_id, answer, Jsonb(citations)),
    ).fetchone()
    conn.execute(
        """
        UPDATE chat_conversations
        SET title = coalesce(title, left(%s, 80)), updated_at = now()
        WHERE id = %s
        """,
        (question, conversation_id),
    )
    return user, assistant
