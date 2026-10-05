"""SQL for meetings and the pipeline results saved with them. No HTTP concerns here."""

from datetime import date
from uuid import UUID

from psycopg import Connection
from psycopg.types.json import Jsonb

from ..extraction import Evidence, Extraction, Transcript

# A pending task matches an open task when their title embeddings are at
# least this similar (cosine). Provisional: tune it on real project data.
TASK_MATCH_MIN_SIMILARITY = 0.80

RESULT_TABLES = (
    "tasks",
    "meeting_decisions",
    "meeting_summaries",
    "meeting_transcripts",
    "meeting_attendees",
)


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
        SELECT coalesce(speaker_name, speaker_label) AS speaker, turn_key,
               start_time_ms, end_time_ms, content, turn_order
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
    # For each pending task, the closest approved, still-open task created
    # earlier in the same project from another meeting, if it is similar enough.
    tasks = conn.execute(
        """
        SELECT t.id, t.title, t.owner_label, t.assignee_user_id,
               (SELECT p.display_name FROM profiles p
                WHERE p.id = t.assignee_user_id) AS assignee_name,
               t.due_date, t.due_date_text, t.review_status, t.category,
               match.id AS match_id, match.title AS match_title
        FROM tasks t
        LEFT JOIN LATERAL (
            SELECT o.id, o.title
            FROM tasks o
            WHERE t.review_status = 'pending' AND t.embedding IS NOT NULL
              AND o.project_id = t.project_id
              AND o.meeting_id IS DISTINCT FROM t.meeting_id
              AND o.created_at < t.created_at
              AND o.review_status = 'approved' AND o.lifecycle_status = 'open'
              AND o.embedding <=> t.embedding <= %s
            ORDER BY o.embedding <=> t.embedding
            LIMIT 1
        ) match ON true
        WHERE t.meeting_id = %s
        ORDER BY t.created_at, t.id
        """,
        (1 - TASK_MATCH_MIN_SIMILARITY, meeting_id),
    ).fetchall()
    for task in tasks:
        match_id, match_title = task.pop("match_id"), task.pop("match_title")
        task["matches_task"] = (
            {"id": match_id, "title": match_title} if match_id else None
        )
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
    uploaded_by: UUID | None = None,
) -> dict:
    return conn.execute(
        """
        INSERT INTO meetings (id, project_id, name, meeting_date, audio_file_path,
                              consent_given, uploaded_by)
        VALUES (%s, %s, %s, %s, %s, true, %s)
        RETURNING id, project_id, name, meeting_date, status, processing_attempt,
                  created_at
        """,
        (meeting_id, project_id, name, meeting_date, audio_file_path, uploaded_by),
    ).fetchone()


def delete_project_meetings(conn: Connection, project_id: UUID) -> int:
    # Project-wide chats quote the purged meetings, so they go too.
    conn.execute("DELETE FROM chat_conversations WHERE project_id = %s", (project_id,))
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
    identification: dict | None = None,
) -> None:
    """Replace this meeting's transcript and extraction rows in one transaction.

    `transcript` has the diarizer's tags. `identification` (voice.identify)
    gives each tag its shown name; extraction ran on the transcript with those
    names, and its evidence must already have passed Extraction.check_evidence.
    """
    row = conn.execute("SELECT project_id FROM meetings WHERE id = %s", (meeting_id,))
    meeting = row.fetchone()
    if meeting is None:
        raise ValueError(f"Meeting {meeting_id} has no database row")
    extraction = Extraction.model_validate(result["extraction"])

    # A retried meeting starts clean. Deleting tasks/decisions cascades evidence.
    for table in RESULT_TABLES:
        conn.execute(f"DELETE FROM {table} WHERE meeting_id = %s", (meeting_id,))

    speakers = identification["speakers"] if identification else {}
    attendees = {}  # diarizer tag -> the matched member's attendee row
    for tag, speaker in speakers.items():
        if speaker["user_id"] is None:
            continue
        attendees[tag] = _member_attendee(conn, speaker["user_id"], speaker["display"])
        conn.execute(
            """
            INSERT INTO meeting_attendees (meeting_id, attendee_id, speaker_label,
                display_label, match_score, match_method, embedding_model_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                meeting_id,
                attendees[tag],
                tag,
                speaker["display"],
                speaker["score"],
                speaker["method"],
                identification["embedding_model_id"],
            ),
        )

    with conn.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO meeting_transcripts (
                meeting_id, attendee_id, speaker_label, speaker_name, turn_key,
                start_time_ms, end_time_ms, content, turn_order
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    meeting_id,
                    attendees.get(turn.speaker),
                    turn.speaker,
                    speakers.get(turn.speaker, {}).get("display"),
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
            "SELECT id, turn_key, start_time_ms FROM meeting_transcripts "
            "WHERE meeting_id = %s",
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

    # A commitment owned by a recognized member is assigned to them (FR-SPK-5).
    members = {s["display"]: s["user_id"] for s in speakers.values() if s["user_id"]}
    tasks = [
        (item.title, item.owner, item.due_date_text, "commitment", item.evidence)
        for item in extraction.commitments
    ] + [
        (item.statement, None, None, "advisor_suggestion", item.evidence)
        for item in extraction.suggestions
    ]
    for title, owner, due_date_text, category, evidence in tasks:
        assignee = members.get(owner)
        task_id = conn.execute(
            """
            INSERT INTO tasks (project_id, meeting_id, owner_label, assignee_user_id,
                               title, due_date_text, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (
                meeting["project_id"],
                meeting_id,
                None if assignee else owner,
                assignee,
                title,
                due_date_text,
                category,
            ),
        ).fetchone()["id"]
        _add_evidence(conn, "task_id", task_id, evidence, turns)

    metadata = {key: value for key, value in result.items() if key != "extraction"}
    model_metadata = {"transcription": transcription_metadata, "extraction": metadata}
    if identification is not None:
        model_metadata["speaker_identification"] = identification  # FR-SPK-6, 7
    conn.execute(
        "UPDATE meetings SET model_metadata = %s, updated_at = now() WHERE id = %s",
        (Jsonb(model_metadata), meeting_id),
    )


def _member_attendee(conn: Connection, user_id: str, name: str) -> UUID:
    """The member's one attendee row, created on first match (FR-SPK-4)."""
    return conn.execute(
        """
        INSERT INTO attendees (name, user_id) VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (name, user_id),
    ).fetchone()["id"]


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
