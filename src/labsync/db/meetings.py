"""SQL for meetings and the pipeline results saved with them. No HTTP concerns here."""

from datetime import date
from uuid import UUID

from psycopg import Connection
from psycopg.types.json import Jsonb

from ..extraction import Evidence, Extraction, Transcript

RESULT_TABLES = ("tasks", "meeting_decisions", "meeting_summaries", "meeting_transcripts")


def project_exists(conn: Connection, project_id: UUID) -> bool:
    row = conn.execute("SELECT 1 FROM projects WHERE id = %s", (project_id,))
    return row.fetchone() is not None


def list_meetings(
    conn: Connection, project_id: UUID, limit: int, offset: int
) -> list[dict]:
    return conn.execute(
        """
        SELECT id, project_id, name, meeting_date, status, duration_seconds,
               audio_file_path, created_at
        FROM meetings
        WHERE project_id = %s
        ORDER BY meeting_date DESC, created_at DESC
        LIMIT %s OFFSET %s
        """,
        (project_id, limit, offset),
    ).fetchall()


def get_meeting_detail(conn: Connection, meeting_id: UUID) -> dict | None:
    meeting = conn.execute(
        """
        SELECT id, project_id, name, meeting_date, audio_file_path, duration_seconds,
               status, processing_attempt, error_message, created_at
        FROM meetings
        WHERE id = %s
        """,
        (meeting_id,),
    ).fetchone()
    if meeting is None:
        return None
    summary = conn.execute(
        """
        SELECT overview, bullet_points
        FROM meeting_summaries
        WHERE meeting_id = %s
        """,
        (meeting_id,),
    ).fetchone()
    transcript = conn.execute(
        """
        SELECT speaker_label AS speaker, turn_key, start_time_ms, end_time_ms,
               content, turn_order
        FROM meeting_transcripts
        WHERE meeting_id = %s
        ORDER BY turn_order
        """,
        (meeting_id,),
    ).fetchall()
    decisions = conn.execute(
        """
        SELECT id, decision_statement AS statement, timestamp_ms
        FROM meeting_decisions
        WHERE meeting_id = %s
        ORDER BY created_at, id
        """,
        (meeting_id,),
    ).fetchall()
    tasks = conn.execute(
        """
        SELECT id, title, owner_label, due_date, due_date_text, review_status, category
        FROM tasks
        WHERE meeting_id = %s
        ORDER BY created_at, id
        """,
        (meeting_id,),
    ).fetchall()
    storylines = conn.execute(
        """
        SELECT id, attendee_id, what_they_want, what_they_see, what_they_discuss
        FROM meeting_attendee_storylines
        WHERE meeting_id = %s
        ORDER BY created_at, id
        """,
        (meeting_id,),
    ).fetchall()
    for decision in decisions:
        decision["evidence"] = _evidence(conn, "decision_id", decision["id"])
    for task in tasks:
        task["evidence"] = _evidence(conn, "task_id", task["id"])
    return meeting | {
        "summary": summary,
        "decisions": decisions,
        "tasks": tasks,
        "transcript": transcript,
        "storylines": storylines,
    }


def create_meeting(
    conn: Connection,
    *,
    meeting_id: str,
    project_id: UUID,
    name: str,
    meeting_date: date,
    audio_file_path: str,
) -> dict:
    return conn.execute(
        """
        INSERT INTO meetings
            (id, project_id, name, meeting_date, audio_file_path, consent_given)
        VALUES (%s, %s, %s, %s, %s, true)
        RETURNING id, project_id, name, meeting_date, status, processing_attempt,
                  created_at
        """,
        (meeting_id, project_id, name, meeting_date, audio_file_path),
    ).fetchone()


def delete_project_meetings(conn: Connection, project_id: UUID) -> int:
    # Project-wide chats quote the purged meetings, so they go too.
    conn.execute(
        "DELETE FROM chat_conversations WHERE project_id = %s", (project_id,)
    )
    return conn.execute(
        "DELETE FROM meetings WHERE project_id = %s", (project_id,)
    ).rowcount

def update_status(
    conn: Connection, meeting_id: str, status: str, attempt: int, error: str | None
) -> None:
    conn.execute(
        """
        UPDATE meetings
        SET status = %s, processing_attempt = %s, error_message = %s, updated_at = now()
        WHERE id = %s
        """,
        (status, attempt, error, meeting_id),
    )


def save_results(
    conn: Connection,
    meeting_id: str,
    transcript: Transcript,
    result: dict,
    transcription_metadata: dict,
) -> None:
    """Replace this meeting's transcript and extraction rows in one transaction.

    `result` is the extraction.json content; its evidence must already have
    passed Extraction.check_evidence against `transcript`.
    """
    row = conn.execute("SELECT project_id FROM meetings WHERE id = %s", (meeting_id,))
    meeting = row.fetchone()
    if meeting is None:
        raise ValueError(f"Meeting {meeting_id} has no database row")
    extraction = Extraction.model_validate(result["extraction"])

    # A retried meeting starts clean. Deleting tasks/decisions cascades evidence.
    for table in RESULT_TABLES:
        conn.execute(f"DELETE FROM {table} WHERE meeting_id = %s", (meeting_id,))

    with conn.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO meeting_transcripts (meeting_id, speaker_label, turn_key, start_time_ms,
                                     end_time_ms, content, turn_order)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    meeting_id,
                    turn.speaker,
                    turn.id,
                    turn.start_time_ms,
                    turn.end_time_ms,
                    turn.content,
                    order,
                )
                for order, turn in enumerate(transcript.turns)
            ],
        )
    turns = {
        row["turn_key"]: row
        for row in conn.execute(
            "SELECT id, turn_key, start_time_ms FROM meeting_transcripts WHERE meeting_id = %s",
            (meeting_id,),
        )
    }

    conn.execute(
        "INSERT INTO meeting_summaries (meeting_id, overview) VALUES (%s, %s)",
        (meeting_id, extraction.summary),
    )
    for decision in extraction.decisions:
        decision_id = conn.execute(
            """
            INSERT INTO meeting_decisions (meeting_id, decision_statement, timestamp_ms)
            VALUES (%s, %s, %s) RETURNING id
            """,
            (
                meeting_id,
                decision.statement,
                turns[decision.evidence[0].transcript_id]["start_time_ms"],
            ),
        ).fetchone()["id"]
        _add_evidence(conn, "decision_id", decision_id, decision.evidence, turns)

    tasks = [
        (item.title, item.owner, item.due_date_text, "commitment", item.evidence)
        for item in extraction.commitments
    ] + [
        (item.statement, None, None, "advisor_suggestion", item.evidence)
        for item in extraction.suggestions
    ]
    for title, owner, due_date_text, category, evidence in tasks:
        task_id = conn.execute(
            """
            INSERT INTO tasks (project_id, meeting_id, owner_label, title,
                               due_date_text, category)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (meeting["project_id"], meeting_id, owner, title, due_date_text, category),
        ).fetchone()["id"]
        _add_evidence(conn, "task_id", task_id, evidence, turns)

    metadata = {key: value for key, value in result.items() if key != "extraction"}
    conn.execute(
        "UPDATE meetings SET model_metadata = %s, updated_at = now() WHERE id = %s",
        (
            Jsonb({"transcription": transcription_metadata, "extraction": metadata}),
            meeting_id,
        ),
    )


def _evidence(conn: Connection, parent_column: str, parent_id: UUID) -> list[dict]:
    sql = {
        "decision_id": """
            SELECT turn_key, position, quote, timestamp_ms
            FROM item_evidence
            WHERE decision_id = %s
            ORDER BY position
            """,
        "task_id": """
            SELECT turn_key, position, quote, timestamp_ms
            FROM item_evidence
            WHERE task_id = %s
            ORDER BY position
            """,
    }.get(parent_column)
    if sql is None:
        raise ValueError(f"Unknown evidence parent: {parent_column}")
    return conn.execute(sql, (parent_id,)).fetchall()


def _add_evidence(
    conn: Connection,
    parent_column: str,
    parent_id: UUID,
    evidence: list[Evidence],
    turns: dict[str, dict],
) -> None:
    for position, item in enumerate(evidence):
        turn = turns[item.transcript_id]
        conn.execute(
            f"""
            INSERT INTO item_evidence ({parent_column}, transcript_id, turn_key,
                                       position, quote, timestamp_ms)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                parent_id,
                turn["id"],
                item.transcript_id,
                position,
                item.quote,
                turn["start_time_ms"],
            ),
        )


