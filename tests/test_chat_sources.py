"""Runs against a local database only, e.g. after `supabase start`:
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
Never point this at the Supabase project."""

import os
import re
from datetime import date
from uuid import uuid4

import psycopg
import pytest
from psycopg.rows import dict_row

from labsync import chat
from labsync.db import meetings, rag
from labsync.extraction import Transcript

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")
PROJECT = "pytest chat sources"


def connect():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


@pytest.fixture
def seeded(embedder):
    with connect() as conn:
        project = conn.execute(
            "INSERT INTO projects (name) VALUES (%s) RETURNING id", (PROJECT,)
        ).fetchone()["id"]
        meeting_id = str(uuid4())
        meetings.create_meeting(
            conn,
            meeting_id=meeting_id,
            project_id=project,
            name="Tuning sync",
            meeting_date=date(2026, 9, 25),
            audio_file_path="/tmp/recording.mp3",
        )
        turn = f"{meeting_id}:turn:"
        lines = [
            ("SPEAKER_01", "Let's go with 3e-4 for the learning rate."),
            ("SPEAKER_02", "I will rerun the ablation by Friday."),
            ("SPEAKER_03", "Maybe try sentencepiece for the tokenizer."),
        ]
        transcript = Transcript.model_validate(
            {
                "project_id": str(project),
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
        extraction = {
            "summary": "Tuning sync for the thesis model.",
            "decisions": [
                {
                    "statement": "Lower the learning rate to 3e-4",
                    "evidence": [
                        {"transcript_id": turn + "0", "quote": "go with 3e-4"}
                    ],
                }
            ],
            "commitments": [
                {
                    "title": "Rerun the ablation",
                    "owner": "SPEAKER_02",
                    "due_date_text": "Friday",
                    "evidence": [
                        {
                            "transcript_id": turn + "1",
                            "quote": "rerun the ablation by Friday",
                        }
                    ],
                }
            ],
            "suggestions": [
                {
                    "statement": "Switch the tokenizer to sentencepiece",
                    "evidence": [
                        {"transcript_id": turn + "2", "quote": "sentencepiece"}
                    ],
                }
            ],
        }
        meetings.save_results(
            conn, meeting_id, transcript, {"extraction": extraction}, {}
        )
        rag.index_meeting(conn, meeting_id, embedder)
        # Later changes that chat must reflect without re-indexing:
        conn.execute(
            "UPDATE meeting_transcripts SET speaker_name = 'Bryan' "
            "WHERE meeting_id = %s AND speaker_label = 'SPEAKER_02'",
            (meeting_id,),
        )
        conn.execute(
            "UPDATE tasks SET review_status = 'approved', due_date = '2026-10-02' "
            "WHERE meeting_id = %s AND category = 'commitment'",
            (meeting_id,),
        )
    yield {"project": project, "meeting": meeting_id}
    with connect() as conn:
        conn.execute("DELETE FROM projects WHERE name = %s", (PROJECT,))


def sources_for(embedder, seeded, question):
    [vector] = embedder.encode([question])
    with connect() as conn:
        hits = rag.search(
            conn,
            project_id=seeded["project"],
            meeting_id=None,
            text=question,
            vector=vector,
            limit=chat.SEARCH_LIMIT,
        )
        return chat.build_sources(conn, hits)


def test_sources_use_live_names_and_status(embedder, seeded):
    sources = sources_for(embedder, seeded, "Who will rerun the ablation?")
    prompt = chat.build_prompt("Who will rerun the ablation?", [], sources)
    assert 'Meeting "Tuning sync" (2026-09-25):' in prompt
    assert "01:00 Bryan: I will rerun the ablation by Friday." in prompt
    assert (
        "Task: Rerun the ablation (commitment, approved, open, owner SPEAKER_02, "
        "due 2026-10-02)" in prompt
    )
    refs = [s.ref for s in sources]
    assert len(refs) == len(set(refs))  # every handle is unique
    assert all(re.fullmatch(r"[TDKS]\d+", ref) for ref in refs)
    turns = [s for s in sources if s.kind == "transcript"]
    assert len({s.turn_key for s in turns}) == len(turns)  # no turn twice


def test_answer_maps_citation_to_turn_and_time(embedder, seeded, monkeypatch):
    sources = sources_for(embedder, seeded, "Who will rerun the ablation?")
    [source] = [s for s in sources if s.speaker == "Bryan"]

    def fake_model(prompt, schema, *, provider, model, timeout):
        assert f"[{source.ref}]" in prompt
        return {
            "answerable": True,
            "answer": f"Bryan will rerun it by Friday [{source.ref}].",
            "citations": [{"ref": source.ref, "quote": "rerun the ablation"}],
        }

    monkeypatch.setattr(chat.providers, "structured", fake_model)
    text, [citation] = chat.answer(
        "Who will rerun the ablation?",
        [],
        sources,
        provider="claude",
        model=None,
        timeout=5,
    )
    assert text == "Bryan will rerun it by Friday [1]."
    assert citation["turn_key"] == f"{seeded['meeting']}:turn:1"
    assert citation["start_time_ms"] == 60_000
    assert citation["speaker"] == "Bryan"
    assert citation["meeting_name"] == "Tuning sync"


def test_dismissed_task_is_not_a_source(embedder, seeded):
    with connect() as conn:
        conn.execute(
            "UPDATE tasks SET review_status = 'dismissed' WHERE meeting_id = %s",
            (seeded["meeting"],),
        )
    sources = sources_for(embedder, seeded, "sentencepiece tokenizer suggestion")
    assert not [s for s in sources if s.kind == "task"]
