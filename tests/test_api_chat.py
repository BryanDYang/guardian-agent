"""Runs against a local database only, e.g. after `supabase start`:
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
Never point this at the Supabase project."""

import os
import re
from datetime import date
from uuid import UUID, uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from labsync import chat
from labsync.db import meetings, rag
from labsync.extraction import Transcript
from labsync.server import create_app

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")
AUTH = {"Authorization": "Bearer test-token"}
PROJECTS = ("pytest chat", "pytest chat other")


def add_meeting(conn, embedder, project_id, name, day, lines, extraction=None):
    meeting_id = str(uuid4())
    meetings.create_meeting(
        conn,
        meeting_id=meeting_id,
        project_id=project_id,
        name=name,
        meeting_date=day,
        audio_file_path="/tmp/recording.mp3",
    )
    transcript = Transcript.model_validate(
        {
            "project_id": str(project_id),
            "meeting_id": meeting_id,
            "turns": [
                {
                    "id": f"{meeting_id}:turn:{i}",
                    "speaker": speaker,
                    "start_time_ms": i * 60_000,
                    "end_time_ms": i * 60_000 + 5_000,
                    "content": content,
                }
                for i, (speaker, content) in enumerate(lines)
            ],
        }
    )
    empty = {"summary": "", "decisions": [], "commitments": [], "suggestions": []}
    result = {"extraction": extraction(meeting_id) if extraction else empty}
    meetings.save_results(conn, meeting_id, transcript, result, {})
    rag.index_meeting(conn, meeting_id, embedder)
    return meeting_id


@pytest.fixture
def seeded(embedder):
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        project, other = (
            conn.execute(
                "INSERT INTO projects (name) VALUES (%s) RETURNING id", (name,)
            ).fetchone()["id"]
            for name in PROJECTS
        )

        def sync_results(meeting_id):
            turn = f"{meeting_id}:turn:"
            return {
                "summary": "Tuning sync for the thesis model.",
                "decisions": [
                    {
                        "statement": "Lower the learning rate to 3e-4",
                        "evidence": [
                            {"transcript_id": turn + "1", "quote": "go with 3e-4"}
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
                                "transcript_id": turn + "2",
                                "quote": "rerun the ablation",
                            },
                            {"transcript_id": turn + "2", "quote": "Friday"},
                        ],
                    }
                ],
                "suggestions": [
                    {
                        "statement": "Switch the tokenizer to sentencepiece",
                        "evidence": [
                            {"transcript_id": turn + "3", "quote": "sentencepiece"}
                        ],
                    }
                ],
            }

        kickoff = add_meeting(
            conn,
            embedder,
            project,
            "Kickoff",
            date(2026, 9, 18),
            [
                ("SPEAKER_01", "Welcome everyone to the thesis kickoff."),
                ("SPEAKER_02", "The baseline learning rate is 1e-3 for now."),
            ],
        )
        sync = add_meeting(
            conn,
            embedder,
            project,
            "Tuning sync",
            date(2026, 9, 25),
            [
                ("SPEAKER_01", "The loss is diverging after epoch three."),
                ("SPEAKER_01", "Let's go with 3e-4 for the learning rate."),
                ("SPEAKER_02", "I will rerun the ablation by Friday."),
                ("SPEAKER_03", "Maybe try sentencepiece for the tokenizer."),
            ],
            sync_results,
        )
        leak = add_meeting(
            conn,
            embedder,
            other,
            "Other project",
            date(2026, 9, 26),
            [("SPEAKER_01", "The learning rate here is 0.1 and nobody else knows.")],
        )
    yield {
        "project": str(project),
        "other": str(other),
        "kickoff": kickoff,
        "sync": sync,
        "leak": leak,
    }
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("DELETE FROM projects WHERE name = ANY(%s)", (list(PROJECTS),))


class FakeModel:
    """Stands in for the provider call. It answers by citing the first prompt
    source that contains `keyword`, quoting `quote` (or the keyword)."""

    def __init__(self):
        self.keyword = None
        self.quote = None
        self.prompts = []
        self.error = None

    def __call__(self, prompt, schema, *, provider, model, timeout):
        self.prompts.append(prompt)
        if self.error:
            raise RuntimeError(self.error)
        for ref, line in re.findall(r"^\[([TDKS]\d+)\] (.*)$", prompt, re.M):
            if self.keyword and self.keyword in line:
                return {
                    "answerable": True,
                    "answer": f"Found it [{ref}].",
                    "citations": [{"ref": ref, "quote": self.quote or self.keyword}],
                }
        return {"answerable": False, "answer": "", "citations": []}


@pytest.fixture
def model(monkeypatch):
    fake = FakeModel()
    monkeypatch.setattr(chat.providers, "structured", fake)
    return fake


@pytest.fixture
def client(tmp_path, embedder):
    app = create_app(
        tmp_path,
        tmp_path,
        token="test-token",
        database_url=DATABASE_URL,
        embedder=embedder,
    )
    with TestClient(app) as client:
        yield client


def start(client, project, meeting=None):
    body = {"project_id": project} | ({"meeting_id": meeting} if meeting else {})
    response = client.post("/api/v1/conversations", json=body, headers=AUTH)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def ask(client, conversation, question):
    return client.post(
        f"/api/v1/conversations/{conversation}/messages",
        json={"content": question},
        headers=AUTH,
    )


def test_answer_cites_meeting_turn_and_time(client, seeded, model):
    model.keyword = "Let's go with 3e-4"
    response = ask(client, start(client, seeded["project"]), "What learning rate?")
    assert response.status_code == 200, response.text
    answer = response.json()["assistant_message"]
    assert answer["content"] == "Found it [1]."
    [citation] = answer["citations"]
    assert citation["meeting_id"] == seeded["sync"]
    assert citation["meeting_name"] == "Tuning sync"
    assert citation["turn_key"] == f"{seeded['sync']}:turn:1"
    assert citation["start_time_ms"] == 60_000
    assert citation["speaker"] == "SPEAKER_01"


def test_retrieval_never_leaves_the_project(client, seeded, model):
    ask(client, start(client, seeded["project"]), "What is the learning rate?")
    assert "nobody else knows" not in model.prompts[-1]
    assert "Other project" not in model.prompts[-1]
    ask(client, start(client, seeded["other"]), "What is the learning rate?")
    assert "nobody else knows" in model.prompts[-1]
    assert "Tuning sync" not in model.prompts[-1]


def test_meeting_scope_limits_retrieval(client, seeded, model):
    conversation = start(client, seeded["project"], seeded["kickoff"])
    ask(client, conversation, "What is the learning rate?")
    assert 'Meeting "Kickoff"' in model.prompts[-1]
    assert "Tuning sync" not in model.prompts[-1]


def test_decisions_and_tasks_carry_live_status(client, seeded, model):
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "UPDATE tasks SET review_status = 'approved', due_date = '2026-10-02' "
            "WHERE title = 'Rerun the ablation'"
        )
        conn.execute(
            "UPDATE tasks SET review_status = 'dismissed' "
            "WHERE title = 'Switch the tokenizer to sentencepiece'"
        )
    model.keyword, model.quote = "Rerun the ablation", "rerun the ablation"
    response = ask(
        client, start(client, seeded["project"]), "Who will rerun the ablation?"
    )
    prompt = model.prompts[-1]
    assert (
        "Task: Rerun the ablation (commitment, approved, open, owner SPEAKER_02, "
        "due 2026-10-02)" in prompt
    )
    assert "Task: Switch the tokenizer" not in prompt  # dismissed
    [citation] = response.json()["assistant_message"]["citations"]
    assert citation["kind"] == "task"
    assert citation["start_time_ms"] == 120_000  # first evidence quote


def test_refusals(client, seeded, model):
    conversation = start(client, seeded["project"])
    model.keyword = None  # the model says it cannot answer
    response = ask(client, conversation, "What is the office wifi password?")
    assert response.json()["assistant_message"]["content"] == chat.NO_ANSWER

    model.keyword, model.quote = "go with 3e-4", "we chose 5e-5"  # invented quote
    message = ask(client, conversation, "What learning rate?").json()
    answer = message["assistant_message"]
    assert (answer["content"], answer["citations"]) == (chat.NO_ANSWER, [])


def test_empty_project_refuses_without_the_model(client, seeded, model):
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        empty = conn.execute(
            "INSERT INTO projects (name) VALUES ('pytest chat') RETURNING id"
        ).fetchone()["id"]
    response = ask(client, start(client, str(empty)), "Anything?")
    assert response.json()["assistant_message"]["content"] == chat.NO_ANSWER
    assert model.prompts == []


def test_history_titles_and_follow_ups(client, seeded, model):
    conversation = start(client, seeded["project"])
    model.keyword = "go with 3e-4"
    ask(client, conversation, "What learning rate did we pick?")
    ask(client, conversation, "Why?")
    assert "USER: What learning rate did we pick?" in model.prompts[-1]

    thread = client.get(f"/api/v1/conversations/{conversation}", headers=AUTH).json()
    assert thread["title"] == "What learning rate did we pick?"
    assert [m["role"] for m in thread["messages"]] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    listed = client.get(
        "/api/v1/conversations", params={"project_id": seeded["project"]}, headers=AUTH
    ).json()
    assert [c["id"] for c in listed] == [conversation]  # empty threads are hidden
    other = client.get(
        "/api/v1/conversations", params={"project_id": seeded["other"]}, headers=AUTH
    ).json()
    assert other == []


def test_model_failure_stores_nothing(client, seeded, model):
    conversation = start(client, seeded["project"])
    model.error = "Claude chat timed out after 90s."
    response = ask(client, conversation, "What learning rate?")
    assert response.status_code == 502
    assert response.json()["detail"] == "Claude chat timed out after 90s."
    thread = client.get(f"/api/v1/conversations/{conversation}", headers=AUTH).json()
    assert thread["messages"] == []


def test_request_errors(client, seeded, model):
    missing = str(UUID(int=0))
    post = client.post
    assert (
        post("/api/v1/conversations", json={"project_id": missing}, headers=AUTH)
    ).status_code == 404
    foreign = {"project_id": seeded["project"], "meeting_id": seeded["leak"]}
    assert post("/api/v1/conversations", json=foreign, headers=AUTH).status_code == 404
    assert ask(client, missing, "Hi").status_code == 404
    conversation = start(client, seeded["project"])
    assert ask(client, conversation, "   ").status_code == 400
    assert ask(client, conversation, "x" * 2001).status_code == 422


def test_purge_deletes_project_chats(client, seeded, model):
    conversation = start(client, seeded["project"])
    model.keyword = "go with 3e-4"
    ask(client, conversation, "What learning rate?")
    response = client.delete(
        f"/api/projects/{seeded['project']}/meetings", headers=AUTH
    )
    assert response.status_code == 200
    got = client.get(f"/api/v1/conversations/{conversation}", headers=AUTH)
    assert got.status_code == 404