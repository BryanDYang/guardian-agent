"""SQL for the chat retrieval index. No HTTP concerns here."""

from typing import Protocol
from uuid import UUID

from psycopg import Connection

from ..chunking import Turn, windows
from ..embeddings import TASK_DIMENSIONS, to_pgvector

RRF_K = 60  # Reciprocal Rank Fusion smoothing constant
LEG_DEPTH = 40  # candidates each leg contributes before fusion


class Embedder(Protocol):
    name: str

    def encode(self, texts: list[str]) -> list[list[float]]: ...


def index_meeting(conn: Connection, meeting_id: str | UUID, embedder: Embedder) -> int:
    """Rebuild one meeting's rag_chunks from its stored results and return how
    many chunks were written. Safe to run again: old chunks are replaced.

    Also stores each task's title embedding, which the meeting screen uses to
    flag a new task that matches an open task from an earlier meeting."""
    meeting = conn.execute(
        "SELECT project_id FROM meetings WHERE id = %s", (meeting_id,)
    ).fetchone()
    if meeting is None:
        raise ValueError(f"Meeting {meeting_id} has no database row")

    # Each row: (kind, source_id, first_turn, last_turn, start_time_ms, content)
    rows = []

    # Transcript windows. A resolved speaker name wins over the diarizer label.
    turns = [
        Turn(r["turn_order"], r["speaker"], r["start_time_ms"], r["content"])
        for r in conn.execute(
            """
            SELECT turn_order, coalesce(speaker_name, speaker_label) AS speaker,
                start_time_ms, content
            FROM meeting_transcripts WHERE meeting_id = %s ORDER BY turn_order
            """,
            (meeting_id,),
        )
    ]
    for w in windows(turns):
        rows.append(
            (
                "transcript",
                None,
                w.first_order,
                w.last_order,
                w.start_time_ms,
                w.content,
            )
        )

    summary = conn.execute(
        "SELECT overview FROM meeting_summaries WHERE meeting_id = %s", (meeting_id,)
    ).fetchone()
    if summary and (summary["overview"] or "").strip():
        rows.append(
            ("summary", None, None, None, None, "Summary: " + summary["overview"])
        )

    for d in conn.execute(
        """
        SELECT id, decision_statement, timestamp_ms
        FROM meeting_decisions WHERE meeting_id = %s
        """,
        (meeting_id,),
    ):
        rows.append(
            (
                "decision",
                d["id"],
                None,
                None,
                d["timestamp_ms"],
                "Decision: " + d["decision_statement"],
            )
        )

    # Tasks start at their first evidence quote. The assigned member's name wins,
    # then an attendee's name, then the raw diarizer owner label.
    for t in conn.execute(
        """
        SELECT t.id, t.title, t.category, t.due_date_text,
               coalesce(pr.display_name, a.name, t.owner_label) AS owner,
               (SELECT e.timestamp_ms FROM item_evidence e
                WHERE e.task_id = t.id ORDER BY e.position LIMIT 1) AS timestamp_ms
        FROM tasks t
        LEFT JOIN profiles pr ON pr.id = t.assignee_user_id
        LEFT JOIN attendees a ON a.id = t.attendee_id
        WHERE t.meeting_id = %s
        """,
        (meeting_id,),
    ):
        label = "Commitment" if t["category"] == "commitment" else "Suggestion"
        text = f"{label}: {t['title']}"
        if t["owner"]:
            text += f"\nOwner: {t['owner']}"
        if t["due_date_text"]:
            text += f"\nDeadline: {t['due_date_text']}"
        rows.append(("task", t["id"], None, None, t["timestamp_ms"], text))

    titles = conn.execute(
        "SELECT id, title FROM tasks WHERE meeting_id = %s", (meeting_id,)
    ).fetchall()
    # One request for both: chunk texts first, then task titles.
    vectors = embedder.encode([row[-1] for row in rows] + [t["title"] for t in titles])
    vectors, title_vectors = vectors[: len(rows)], vectors[len(rows) :]
    with conn.cursor() as cursor:
        cursor.executemany(
            "UPDATE tasks SET embedding = %s::vector WHERE id = %s",
            [
                (to_pgvector(vector[:TASK_DIMENSIONS]), task["id"])
                for task, vector in zip(titles, title_vectors, strict=True)
            ],
        )
    conn.execute("DELETE FROM rag_chunks WHERE meeting_id = %s", (meeting_id,))
    with conn.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO rag_chunks
                (project_id, meeting_id, kind, source_id, first_turn_order,
                 last_turn_order, start_time_ms, content, embedding, embedding_model)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector, %s)
            """,
            [
                (
                    meeting["project_id"],
                    meeting_id,
                    *row,
                    to_pgvector(vector),
                    embedder.name,
                )
                for row, vector in zip(rows, vectors, strict=True)
            ],
        )
    return len(rows)


def search(
    conn: Connection,
    *,
    project_id: UUID,
    meeting_id: UUID | None,
    text: str,
    vector: list[float],
    limit: int = 8,
) -> list[dict]:
    """Hybrid search inside one project, or one meeting of it.

    Dense leg: cosine distance between the question vector and each chunk.
    Sparse leg: full-text search with the question's words OR-ed together, so
    a chunk needs only some of them. Reciprocal Rank Fusion merges the two
    rankings. Tasks the user dismissed are never returned.
    """
    return conn.execute(
        """
        WITH candidates AS MATERIALIZED (
            SELECT c.id, c.embedding, c.tsv
            FROM rag_chunks c
            LEFT JOIN tasks t ON c.kind = 'task' AND t.id = c.source_id
            WHERE c.project_id = %(project_id)s
            AND (%(meeting_id)s::uuid IS NULL OR c.meeting_id = %(meeting_id)s::uuid)
            AND (t.id IS NULL OR t.review_status <> 'dismissed')
        ),
        dense AS (
            SELECT id, row_number() OVER (
                ORDER BY embedding <=> %(vector)s::vector, id
            ) AS rank
            FROM candidates
            ORDER BY rank
            LIMIT %(depth)s
        ),
        query AS (
            SELECT replace(
                plainto_tsquery('english', %(text)s)::text, '&', '|'
            )::tsquery AS q
        ),
        sparse AS (
            SELECT c.id, row_number() OVER (
                ORDER BY ts_rank(c.tsv, query.q) DESC, c.id
            ) AS rank
            FROM candidates c, query
            WHERE c.tsv @@ query.q
            ORDER BY rank
            LIMIT %(depth)s
        ),
        fused AS (
            SELECT id, sum(1.0 / (%(k)s + rank)) AS score
            FROM (SELECT * FROM dense UNION ALL SELECT * FROM sparse) ranked
            GROUP BY id
        )
        SELECT r.id, r.meeting_id, r.kind, r.source_id, r.first_turn_order,
            r.last_turn_order, r.start_time_ms, r.content,
            m.name AS meeting_name, m.meeting_date, f.score
        FROM fused f
        JOIN rag_chunks r ON r.id = f.id
        JOIN meetings m ON m.id = r.meeting_id
        ORDER BY f.score DESC, m.meeting_date DESC, r.id
        LIMIT %(limit)s
        """,
        {
            "project_id": project_id,
            "meeting_id": meeting_id,
            "text": text,
            "vector": to_pgvector(vector),
            "depth": LEG_DEPTH,
            "k": RRF_K,
            "limit": limit,
        },
    ).fetchall()


# Live rows behind search hits. Chat reads these instead of the chunk text so
# answers reflect current names, review status, and lifecycle state.


def turns(conn: Connection, meeting_id: UUID, first: int, last: int) -> list[dict]:
    return conn.execute(
        """
        SELECT turn_order, turn_key, start_time_ms, content,
            coalesce(speaker_name, speaker_label) AS speaker
        FROM meeting_transcripts
        WHERE meeting_id = %s AND turn_order BETWEEN %s AND %s
        ORDER BY turn_order
        """,
        (meeting_id, first, last),
    ).fetchall()


def summary(conn: Connection, meeting_id: UUID) -> str | None:
    row = conn.execute(
        "SELECT overview FROM meeting_summaries WHERE meeting_id = %s", (meeting_id,)
    ).fetchone()
    return row["overview"] if row else None


def decision(conn: Connection, decision_id: UUID) -> dict | None:
    row = conn.execute(
        "SELECT decision_statement AS statement FROM meeting_decisions WHERE id = %s",
        (decision_id,),
    ).fetchone()
    if row is not None:
        row["evidence"] = _evidence(conn, "decision_id", decision_id)
    return row


def task(conn: Connection, task_id: UUID) -> dict | None:
    row = conn.execute(
        """
        SELECT t.title, t.category, t.due_date, t.due_date_text,
            t.review_status, t.lifecycle_status,
            coalesce(pr.display_name, a.name, t.owner_label) AS owner
        FROM tasks t
        LEFT JOIN profiles pr ON pr.id = t.assignee_user_id
        LEFT JOIN attendees a ON a.id = t.attendee_id
        WHERE t.id = %s
        """,
        (task_id,),
    ).fetchone()
    if row is not None:
        row["evidence"] = _evidence(conn, "task_id", task_id)
    return row


def _evidence(conn: Connection, column: str, parent_id: UUID) -> list[dict]:
    sql = {
        "decision_id": "SELECT turn_key, quote, timestamp_ms FROM item_evidence "
        "WHERE decision_id = %s ORDER BY position",
        "task_id": "SELECT turn_key, quote, timestamp_ms FROM item_evidence "
        "WHERE task_id = %s ORDER BY position",
    }[column]
    return conn.execute(sql, (parent_id,)).fetchall()
