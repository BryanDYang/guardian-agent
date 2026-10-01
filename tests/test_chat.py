from datetime import datetime, timezone
from uuid import uuid4

import pytest

from labsync import chat
from labsync.chat import NO_ANSWER, ChatAnswer, Source

MEETING = uuid4()
OTHER = uuid4()


def source(ref, text, meeting=MEETING, **fields):
    kind = {"T": "transcript", "D": "decision", "K": "task", "S": "summary"}[ref[0]]
    return Source(
        ref=ref,
        kind=kind,
        meeting_id=meeting,
        meeting_name="Week 2" if meeting == MEETING else "Week 1",
        meeting_date=datetime(2026, 9, 25, tzinfo=timezone.utc),
        text=text,
        line=text,
        **fields,
    )


SOURCES = [
    source(
        "T1",
        "We should  lower the learning rate.",
        turn_key="m:turn:4",
        speaker="SPEAKER_02",
        start_time_ms=754000,
    ),
    source("D1", "Use AdamW\nlet's go with AdamW", turn_key="m:turn:9"),
    source("T2", "I'll rerun it Friday.", meeting=OTHER, start_time_ms=5000),
]


def reply(answer, *citations, answerable=True):
    return ChatAnswer.model_validate(
        {
            "answerable": answerable,
            "answer": answer,
            "citations": [{"ref": r, "quote": q} for r, q in citations],
        }
    )


def test_citations_are_verified_mapped_and_renumbered():
    text, citations = chat.finalize(
        reply(
            "They chose AdamW [D1] and lowering the rate [T1] [T1].",
            ("T1", "lower the learning rate"),  # whitespace differences are fine
            ("D1", "go with AdamW"),  # evidence quotes count as the source text
        ),
        SOURCES,
    )
    assert text == "They chose AdamW [1] and lowering the rate [2] [2]."
    assert [(c["number"], c["kind"], c["quote"]) for c in citations] == [
        (1, "decision", "go with AdamW"),
        (2, "transcript", "lower the learning rate"),
    ]
    assert citations[1]["start_time_ms"] == 754000
    assert citations[1]["meeting_id"] == str(MEETING)
    assert citations[1]["speaker"] == "SPEAKER_02"


def test_unverified_citations_and_their_markers_are_dropped():
    text, citations = chat.finalize(
        reply(
            "Rate goes down [T1], and Bob approved it [T9] [T2].",
            ("T1", "lower the learning rate"),
            ("T9", "Bob approved"),  # not a source that was shown
            ("T2", "rerun it Monday"),  # quote not in the source
        ),
        SOURCES,
    )
    assert text == "Rate goes down [1], and Bob approved it."
    assert len(citations) == 1


@pytest.mark.parametrize(
    "model_reply",
    [
        reply("", answerable=False),
        reply("Nothing about that.", ("T1", "invented words")),
        reply("An answer with no citations."),
        reply("   ", ("T1", "lower the learning rate")),
    ],
)
def test_refuses_without_verified_support(model_reply):
    assert chat.finalize(model_reply, SOURCES) == (NO_ANSWER, [])


def test_no_sources_refuses_without_calling_the_model(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("model should not be called")

    monkeypatch.setattr(chat.providers, "structured", fail)
    assert chat.answer("q", [], [], provider="claude", model=None, timeout=5) == (
        NO_ANSWER,
        [],
    )


def test_invalid_model_output_is_an_error(monkeypatch):
    monkeypatch.setattr(chat.providers, "structured", lambda *a, **k: {"answer": 1})
    with pytest.raises(RuntimeError, match="invalid answer"):
        chat.answer("q", [], SOURCES, provider="claude", model=None, timeout=5)


def test_prompt_groups_sources_by_meeting_and_includes_history():
    history = [
        {"role": "user", "content": "What did we decide?"},
        {"role": "assistant", "content": "AdamW [1]."},
    ]
    prompt = chat.build_prompt("Who owns the rerun?", history, SOURCES)
    assert 'Meeting "Week 2" (2026-09-25):\n[T1] ' in prompt
    assert 'Meeting "Week 1" (2026-09-25):\n[T2] ' in prompt
    assert "USER: What did we decide?\nASSISTANT: AdamW [1]." in prompt
    assert prompt.endswith("QUESTION: Who owns the rerun?")


def test_follow_up_retrieval_includes_the_previous_question():
    history = [{"role": "user", "content": "What about the rerun?"}]
    assert chat.retrieval_text("Who owns it?", history) == (
        "What about the rerun?\nWho owns it?"
    )
    assert chat.retrieval_text("First question", []) == "First question"


def test_clock():
    assert chat.clock(754_000) == "12:34"
    assert chat.clock(3_723_000) == "1:02:03"
