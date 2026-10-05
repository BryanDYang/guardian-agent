"""Runs against a local database only, e.g. after `supabase start`:
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
Never point this at the Supabase project."""

import os
from datetime import date
from uuid import uuid4

import psycopg
import pytest
from psycopg.rows import dict_row

from labsync.db import meetings, rag
from labsync.extraction import Transcript

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")


def connect():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def stored(conn, meeting_id):
    return conn.execute(
        """
        SELECT kind, source_id, first_turn_order, last_turn_order, start_time_ms,
               content, embedding_model, vector_dims(embedding) AS dimensions
        FROM rag_chunks WHERE meeting_id = %s ORDER BY kind, content
        """,
        (meeting_id,),
    ).fetchall()


def add_meeting(conn):
    project_id = conn.execute(
        "INSERT INTO projects (name) VALUES ('pytest rag') RETURNING id"
    ).fetchone()["id"]
    meeting_id = str(uuid4())
    meetings.create_meeting(
        conn,
        meeting_id=meeting_id,
        project_id=project_id,
        name="TA check-in",
        meeting_date=date(2026, 9, 25),
        audio_file_path="/tmp/recording.mp3",
    )
    turn = f"{meeting_id}:turn:"
    transcript = Transcript.model_validate(
        {
            "project_id": str(project_id),
            "meeting_id": meeting_id,
            "turns": [
                {
                    "id": turn + "0",
                    "speaker": "SPEAKER_01",
                    "start_time_ms": 0,
                    "end_time_ms": 900,
                    "content": "I will share the recording by Friday.",
                },
                {
                    "id": turn + "1",
                    "speaker": "SPEAKER_04",
                    "start_time_ms": 1000,
                    "end_time_ms": 1900,
                    "content": "Let's keep this time for now.",
                },
                {
                    "id": turn + "2",
                    "speaker": "SPEAKER_01",
                    "start_time_ms": 2000,
                    "end_time_ms": 2900,
                    "content": "You could try S3 vector indexing.",
                },
            ],
        }
    )
    extraction = {
        "summary": "TA check-in.",
        "decisions": [
            {
                "statement": "Keep the meeting time",
                "evidence": [{"transcript_id": turn + "1", "quote": "keep this time"}],
            }
        ],
        "commitments": [
            {
                "title": "Share the recording",
                "owner": "SPEAKER_01",
                "due_date_text": "Friday",
                "evidence": [
                    {
                        "transcript_id": turn + "0",
                        "quote": "I will share the recording by Friday",
                    }
                ],
            }
        ],
        "suggestions": [
            {
                "statement": "Try S3 vector indexing",
                "evidence": [{"transcript_id": turn + "2", "quote": "S3 vector"}],
            }
        ],
    }
    meetings.save_results(conn, meeting_id, transcript, {"extraction": extraction}, {})
    conn.execute(
        """
        UPDATE meeting_transcripts SET speaker_name = 'Ada'
        WHERE meeting_id = %s AND speaker_label = 'SPEAKER_01'
        """,
        (meeting_id,),
    )
    attendee = conn.execute(
        "INSERT INTO attendees (name) VALUES ('pytest Ada') RETURNING id"
    ).fetchone()["id"]
    conn.execute(
        """
        UPDATE tasks SET attendee_id = %s
        WHERE meeting_id = %s AND category = 'commitment'
        """,
        (attendee, meeting_id),
    )
    return meeting_id


@pytest.fixture
def meeting_id():
    with connect() as conn:
        created = add_meeting(conn)
    yield created
    with connect() as conn:
        conn.execute("DELETE FROM projects WHERE name = 'pytest rag'")
        conn.execute("DELETE FROM attendees WHERE name = 'pytest Ada'")


def test_indexes_every_kind_and_prefers_names(embedder, meeting_id):
    with connect() as conn:
        assert rag.index_meeting(conn, meeting_id, embedder) == 5
        rows = stored(conn, meeting_id)
        # Task titles are embedded too, shortened to fit tasks.embedding.
        title_dimensions = conn.execute(
            "SELECT vector_dims(embedding) AS n FROM tasks WHERE meeting_id = %s",
            (meeting_id,),
        ).fetchall()
    assert [row["n"] for row in title_dimensions] == [384, 384]
    assert [(row["kind"], row["start_time_ms"]) for row in rows] == [
        ("decision", 1000),
        ("summary", None),
        ("task", 0),
        ("task", 2000),
        ("transcript", 0),
    ]
    assert [row["content"] for row in rows] == [
        "Decision: Keep the meeting time",
        "Summary: TA check-in.",
        "Commitment: Share the recording\nOwner: pytest Ada\nDeadline: Friday",
        "Suggestion: Try S3 vector indexing",
        "Ada: I will share the recording by Friday.\n"
        "SPEAKER_04: Let's keep this time for now.\n"
        "Ada: You could try S3 vector indexing.",
    ]
    assert rows[0]["source_id"] is not None and rows[1]["source_id"] is None
    assert (rows[4]["first_turn_order"], rows[4]["last_turn_order"]) == (0, 2)
    assert {row["embedding_model"] for row in rows} == {embedder.name}
    assert {row["dimensions"] for row in rows} == {1536}


def test_reindex_replaces_without_duplicates(embedder, meeting_id):
    with connect() as conn:
        rag.index_meeting(conn, meeting_id, embedder)
        first = [
            row["id"]
            for row in conn.execute(
                "SELECT id FROM rag_chunks WHERE meeting_id = %s", (meeting_id,)
            )
        ]
        assert rag.index_meeting(conn, meeting_id, embedder) == 5
        second = [
            row["id"]
            for row in conn.execute(
                "SELECT id FROM rag_chunks WHERE meeting_id = %s", (meeting_id,)
            )
        ]
    assert len(first) == len(second) == 5
    assert set(first).isdisjoint(second)


def test_delete_cascades_chunks(embedder, meeting_id):
    with connect() as conn:
        rag.index_meeting(conn, meeting_id, embedder)
        conn.execute("DELETE FROM meetings WHERE id = %s", (meeting_id,))
        left = conn.execute(
            "SELECT count(*) AS n FROM rag_chunks WHERE meeting_id = %s",
            (meeting_id,),
        ).fetchone()["n"]
    assert left == 0


def test_unknown_meeting(embedder):
    with connect() as conn, pytest.raises(ValueError, match="no database row"):
        rag.index_meeting(conn, uuid4(), embedder)
