"""Offline scorer checks with deliberately wrong predictions; no live inference."""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from labsync.evaluation import digest, load_suite, ratio, score, score_case

SUITE = Path(__file__).parents[1] / "fixtures/evaluation/development.json"


@pytest.fixture
def case():
    return load_suite(SUITE)["cases"][0]


def prediction(case, **overrides):
    task = {
        "title": "Prepare the transcript fixture",
        "owner": "Sam",
        "due_date_text": "Friday",
        "evidence": [
            {"transcript_id": "t1", "quote": case["transcript"]["turns"][0]["content"]}
        ],
    }
    task.update(overrides)
    return {
        "extraction": {
            "summary": "",
            "decisions": [],
            "suggestions": [],
            "commitments": [task],
        }
    }


def test_perfect_prediction(case):
    row = score_case(case, prediction(case))
    assert row["errors"] == []
    assert row["counts"]["matched"] == 1
    assert row["counts"]["owner_correct"] == 1
    assert row["counts"]["deadline_correct"] == 1
    assert row["counts"]["citation_valid"] == 1


def test_wrong_fields_do_not_hide_task_match(case):
    row = score_case(case, prediction(case, owner="Will", due_date_text="Monday"))
    assert row["counts"]["matched"] == 1
    assert row["counts"]["owner_correct"] == 0
    assert row["counts"]["deadline_correct"] == 0


def test_duplicate_is_false_positive(case):
    record = prediction(case)
    record["extraction"]["commitments"] *= 2
    counts = score_case(case, record)["counts"]
    assert (counts["matched"], counts["predicted"], counts["duplicates"]) == (1, 2, 1)


@pytest.mark.parametrize("record", [None, {"error": "timeout"}, {"extraction": {}}])
def test_missing_failed_and_invalid_count_gold_as_missed(case, record):
    counts = score_case(case, record)["counts"]
    assert (counts["gold"], counts["matched"], counts["failed"]) == (1, 0, 1)


@pytest.mark.parametrize(
    "evidence",
    [
        [{"transcript_id": "missing", "quote": "I will prepare"}],
        [{"transcript_id": "t1", "quote": "invented text"}],
    ],
)
def test_invalid_citations_are_measured(case, evidence):
    counts = score_case(case, prediction(case, evidence=evidence))["counts"]
    assert (counts["citation_valid"], counts["citation_total"]) == (0, 1)
    assert counts["evidence_complete"] == 0


def test_maximum_matching_is_not_greedy(case):
    second = copy.deepcopy(case["gold"][0])
    second.update(id="g2", action_terms=[["send"], ["slides"]])
    case["gold"].append(second)
    record = prediction(case, title="Prepare transcript fixture and send slides")
    record["extraction"]["commitments"].append(
        prediction(case)["extraction"]["commitments"][0]
    )
    row = score_case(case, record)
    assert row["counts"]["matched"] == 2
    assert row["matches"] == [
        {"prediction": 1, "gold": "g1"},
        {"prediction": 0, "gold": "g2"},
    ]


def test_unrelated_title_is_not_matched_by_source_alone(case):
    row = score_case(case, prediction(case, title="Delete the production database"))
    assert row["counts"]["matched"] == 0
    assert row["counts"]["duplicates"] == 0


def test_empty_negative_does_not_invent_precision(case):
    case["gold"] = []
    record = prediction(case)
    record["extraction"]["commitments"] = []
    counts = score_case(case, record)["counts"]
    assert counts["negative_correct"] == counts["negative_total"] == 1
    assert ratio(counts["matched"], counts["predicted"])["value"] is None


def test_unknown_owner_scored_separately(case):
    case["gold"][0]["owner"] = None
    counts = score_case(case, prediction(case, owner=None))["counts"]
    assert counts["owner_total"] == 0
    assert counts["unknown_owner_correct"] == counts["unknown_owner_total"] == 1


def test_cli_run_score_and_refuse_overwrite(tmp_path):
    directory = tmp_path / "run"
    base = [sys.executable, "-m", "labsync.evaluation"]
    args = ["--suite", str(SUITE), "--directory", str(directory)]
    subprocess.run([*base, "run", *args], check=True, capture_output=True)
    subprocess.run([*base, "score", *args], check=True, capture_output=True)
    report = json.loads((directory / "scores.json").read_text())
    assert len(report["cases"]) == 24
    assert report["counts"]["gold"] == 15
    assert report["counts"]["matched"] == 11
    assert report["counts"]["failed"] == 0
    before = (directory / "explicit.json").read_bytes()
    rerun = subprocess.run([*base, "run", *args], capture_output=True)
    assert rerun.returncode == 1
    assert (directory / "explicit.json").read_bytes() == before
    suite = load_suite(SUITE)
    (directory / "explicit.json").unlink()
    assert score(suite, directory)["counts"]["failed"] == 1
    suite["version"] = "changed"
    with pytest.raises(ValueError, match="Suite hash"):
        score(suite, directory)


def test_reject_mismatched_input(tmp_path, case):
    suite = load_suite(SUITE)
    (tmp_path / "run.json").write_text(json.dumps({"suite_sha256": digest(suite)}))
    (tmp_path / "explicit.json").write_text(
        json.dumps(
            {
                "case_id": "explicit",
                "input_sha256": "wrong",
                "wall_seconds": 1,
            }
        )
    )
    with pytest.raises(ValueError, match="different input"):
        score(suite, tmp_path)


def test_duplicate_case_ids_rejected(tmp_path):
    suite = load_suite(SUITE)
    suite["cases"].append(suite["cases"][0])
    path = tmp_path / "suite.json"
    path.write_text(json.dumps(suite))
    with pytest.raises(ValueError, match="unique"):
        load_suite(path)
