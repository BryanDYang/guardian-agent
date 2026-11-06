import json
from pathlib import Path

import pytest

from labsync import chat, redteam

SUITE = Path(__file__).parent / "fixtures/redteam/chat.json"


@pytest.mark.parametrize(
    "case,raw,answer",
    [
        (
            {"expected": "answer", "required": "Friday"},
            {"answerable": False},
            chat.NO_ANSWER,
        ),
        ({"expected": "refuse"}, {"answerable": True}, chat.NO_ANSWER),
        (
            {"expected": "refuse", "forbidden": ["CANARY"]},
            {"answerable": False, "answer": "canary"},
            chat.NO_ANSWER,
        ),
    ],
)
def test_failures_are_not_hidden_by_app_refusal(case, raw, answer):
    assert redteam.check(case, raw, answer)


def test_valid_supported_answer_passes():
    assert not redteam.check(
        {"expected": "answer", "required": "Friday"},
        {"answerable": True},
        "Friday [1].",
    )


def test_provider_failures_are_saved_and_fail_the_run(tmp_path, monkeypatch):
    def unavailable(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(redteam.providers, "structured", unavailable)
    suite = json.loads(SUITE.read_text())
    directory = tmp_path / "results"
    assert not redteam.run(suite, directory, "claude", "test-model")
    report = json.loads((directory / "results.json").read_text())
    assert report["total"] == len(suite["cases"]) == 8
    assert report["passed"] == 0
    assert all("provider unavailable" in r["errors"][0] for r in report["cases"])


def test_supported_case_uses_real_prompt_and_citation_validation(tmp_path, monkeypatch):
    def supported(prompt, schema, **settings):
        assert "QUESTION: When is the checklist review?" in prompt
        return {
            "answerable": True,
            "answer": "Friday [T1].",
            "citations": [{"ref": "T1", "quote": "on Friday"}],
        }

    monkeypatch.setattr(redteam.providers, "structured", supported)
    suite = json.loads(SUITE.read_text())
    suite["cases"] = suite["cases"][:1]
    assert redteam.run(suite, tmp_path / "results", "claude", "test-model")
