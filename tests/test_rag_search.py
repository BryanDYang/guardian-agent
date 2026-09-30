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
PROJECT = "pytest rag search"


def connect():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def add_meeting(conn, embedder, project_id, name, day, lines, suggestion=None):
    meeting_id = str(uuid4())
    meetings.create_meeting(
        conn,
        meeting_id=meeting_id,
        project_id=project_id,
        name=name,
        meeting_date=day,
        audio_file_path="/tmp/recording.mp3",
    )
    turn = f"{meeting_id}:turn:"
    transcript = Transcript.model_validate(
        {
            "project_id": str(project_id),
            "meeting_id": meeting_id,
            "turns": [
                {
                    "id": turn + str(i),
                    "speaker": speaker,
                    "start_time_ms": i * 60_000,
                    "end_time_ms": i * 60_000 + 5_000,
                    "content": content,
                }
                for i, (speaker, content) in enumerate(lines)
            ],
        }
    )
    suggestions = []
    if suggestion:
        index, quote = suggestion
        suggestions = [
            {
                "statement": quote,
                "evidence": [{"transcript_id": turn + str(index), "quote": quote}],
            }
        ]
    extraction = {
        "summary": "",
        "decisions": [],
        "commitments": [],
        "suggestions": suggestions,
    }
    meetings.save_results(conn, meeting_id, transcript, {"extraction": extraction}, {})
    rag.index_meeting(conn, meeting_id, embedder)
    return meeting_id


# Each line is 150 words or more once padded, so every turn is its own chunk.
PAD = " ".join(["filler"] * 150)


@pytest.fixture
def seeded(embedder):
    with connect() as conn:
        project, other = (
            conn.execute(
                "INSERT INTO projects (name) VALUES (%s) RETURNING id", (PROJECT,)
            ).fetchone()["id"]
            for _ in range(2)
        )
        kickoff = add_meeting(
            conn,
            embedder,
            project,
            "Kickoff",
            date(2026, 9, 18),
            [
                ("SPEAKER_01", "Welcome everyone to the thesis kickoff. " + PAD),
                ("SPEAKER_02", "The baseline learning rate is 1e-3 for now. " + PAD),
            ],
        )
        sync = add_meeting(
            conn,
            embedder,
            project,
            "Tuning sync",
            date(2026, 9, 25),
            [
                ("SPEAKER_01", "The loss is diverging after epoch three. " + PAD),
                ("SPEAKER_01", "Let's go with 3e-4 for the learning rate. " + PAD),
                ("SPEAKER_03", "Maybe try sentencepiece for the tokenizer."),
            ],
            suggestion=(2, "try sentencepiece for the tokenizer"),
        )
        leak = add_meeting(
            conn,
            embedder,
            other,
            "Other project",
            date(2026, 9, 26),
            [("SPEAKER_01", "The learning rate here is 0.1, nobody else knows.")],
        )
    yield {"project": project, "kickoff": kickoff, "sync": sync, "leak": leak}
    with connect() as conn:
        conn.execute("DELETE FROM projects WHERE name = %s", (PROJECT,))


def search(embedder, project, question, meeting=None, limit=8):
    [vector] = embedder.encode([question])
    with connect() as conn:
        return rag.search(
            conn,
            project_id=project,
            meeting_id=meeting,
            text=question,
            vector=vector,
            limit=limit,
        )


def test_results_stay_inside_the_project(embedder, seeded):
    hits = search(embedder, seeded["project"], "What is the learning rate?")
    assert hits
    assert {str(h["meeting_id"]) for h in hits} <= {seeded["kickoff"], seeded["sync"]}
    assert not any("nobody else knows" in h["content"] for h in hits)


def test_meeting_filter(embedder, seeded):
    hits = search(
        embedder, seeded["project"], "learning rate", meeting=seeded["kickoff"]
    )
    assert hits and {str(h["meeting_id"]) for h in hits} == {seeded["kickoff"]}


def test_both_legs_beat_one(embedder, seeded):
    """The question's vector points at the kickoff welcome, but its words match
    the tokenizer lines. Chunks found by both legs outrank dense-only ones, and a
    keyword-only match still shows up."""
    [vector] = embedder.encode(["Welcome everyone to the thesis kickoff."])
    with connect() as conn:
        hits = rag.search(
            conn,
            project_id=seeded["project"],
            meeting_id=None,
            text="sentencepiece tokenizer",
            vector=vector,
            limit=10,
        )
    assert "sentencepiece" in hits[0]["content"]
    assert any("Welcome everyone" in h["content"] for h in hits)
    scores = [h["score"] for h in hits]
    assert scores == sorted(scores, reverse=True)
    assert hits[0]["meeting_name"] == "Tuning sync"


def test_dismissed_tasks_are_hidden(embedder, seeded):
    question = "Should we switch to sentencepiece for the tokenizer?"
    kinds = {h["kind"] for h in search(embedder, seeded["project"], question)}
    assert "task" in kinds
    with connect() as conn:
        conn.execute(
            "UPDATE tasks SET review_status = 'dismissed' WHERE meeting_id = %s",
            (seeded["sync"],),
        )
    kinds = {h["kind"] for h in search(embedder, seeded["project"], question)}
    assert "task" not in kinds


def test_limit_and_stopword_only_question(embedder, seeded):
    assert len(search(embedder, seeded["project"], "learning rate", limit=2)) == 2
    # "what is the" has no searchable words; the dense leg still answers.
    assert search(embedder, seeded["project"], "what is the")