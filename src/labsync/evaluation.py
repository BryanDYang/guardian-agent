"""Reproducible development evaluation; live inference is separate from scoring."""

import argparse
import json
import platform
import re
import subprocess
import time
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen

from .extraction import INSTRUCTIONS, PROMPT_VERSION, Extraction, Transcript

SCORER_VERSION = "action-terms-v1"


def digest(value: dict) -> str:
    return sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def load_suite(path: Path) -> dict:
    suite = json.loads(path.read_text())
    ids = [case["id"] for case in suite["cases"]]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("Suite must have unique, nonempty case IDs")
    for case in suite["cases"]:
        transcript = Transcript.model_validate(case["transcript"])
        turns = {turn.id for turn in transcript.turns}
        gold_ids = [gold["id"] for gold in case["gold"]]
        if len(gold_ids) != len(set(gold_ids)):
            raise ValueError("Duplicate gold task IDs")
        for gold in case["gold"]:
            if not gold["action_terms"] or not all(gold["action_terms"]):
                raise ValueError("Gold tasks require action terms")
            if not gold["evidence_ids"] or not set(gold["evidence_ids"]) <= turns:
                raise ValueError("Gold evidence IDs must exist")
    return suite


def rule_extract(transcript: Transcript) -> dict:
    """Deliberately simple first-person promise detector, frozen before runs."""
    commitments = []
    for turn in transcript.turns:
        if re.search(r"\bI (?:will|shall)\b|\bI'll\b", turn.content, re.I):
            due = re.search(
                r"\b(?:by|on) (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|"
                r"Sunday)\b|\b(tomorrow)\b",
                turn.content,
                re.I,
            )
            commitments.append(
                {
                    "title": turn.content,
                    "owner": None
                    if turn.speaker.upper() == "UNKNOWN"
                    else turn.speaker,
                    "due_date_text": next(g for g in due.groups() if g)
                    if due
                    else None,
                    "evidence": [{"transcript_id": turn.id, "quote": turn.content}],
                }
            )
    return {
        "summary": "",
        "decisions": [],
        "suggestions": [],
        "commitments": commitments,
    }


def ollama_request(path: str, payload: dict | None = None) -> dict:
    request = Request(
        "http://127.0.0.1:11434/api/" + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=240) as response:
        return json.load(response)


def ollama_extract(transcript: Transcript, model: str) -> dict:
    schema = Extraction.model_json_schema()
    prompt = INSTRUCTIONS + "\nJSON SCHEMA:\n" + json.dumps(schema)
    prompt += "\nTRANSCRIPT:\n" + transcript.model_dump_json()
    settings = {"temperature": 0, "seed": 42, "num_ctx": 4096, "num_predict": 1536}
    response = ollama_request(
        "generate",
        {
            "model": model,
            "prompt": prompt,
            "format": schema,
            "stream": False,
            "options": settings,
        },
    )
    return {
        "extraction": json.loads(response["response"]),
        "prompt_sha256": sha256(prompt.encode()).hexdigest(),
        "prompt_version": PROMPT_VERSION,
        "settings": settings,
        "response_metadata": {
            k: v for k, v in response.items() if k not in {"response", "context"}
        },
    }


def run(suite: dict, output: Path, method: str, model: str | None) -> None:
    # Fresh directories prevent accidental mixing of different experiment runs.
    output.mkdir(parents=True, exist_ok=False)
    metadata = {
        "suite_sha256": digest(suite),
        "suite_version": suite["version"],
        "method": method,
        "model": model,
        "started_at": datetime.now(UTC).isoformat(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "git_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "source_sha256": digest(
            {
                name: Path(__file__).with_name(name).read_text()
                for name in [
                    "evaluation.py",
                    "extraction.py",
                    "providers.py",
                    "codex_client.py",
                    "claude_client.py",
                ]
            }
        ),
    }
    if method == "ollama":
        metadata["ollama_version"] = ollama_request("version")
        metadata["model_details"] = ollama_request("show", {"model": model})
        metadata["model_tags"] = ollama_request("tags")
    (output / "run.json").write_text(json.dumps(metadata, indent=2) + "\n")
    for case in suite["cases"]:
        started = time.monotonic()
        transcript = Transcript.model_validate(case["transcript"])
        record = {
            "case_id": case["id"],
            "input_sha256": digest(case["transcript"]),
        }
        try:
            if method == "rules":
                record["extraction"] = rule_extract(transcript)
            elif method == "ollama":
                record.update(ollama_extract(transcript, model))
            else:
                from .providers import extract

                record.update(
                    extract(transcript, provider=method, model=model, timeout=240)
                )
            Extraction.model_validate(record["extraction"])
        except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"
        record["wall_seconds"] = round(time.monotonic() - started, 3)
        (output / f"{case['id']}.json").write_text(json.dumps(record, indent=2) + "\n")
        print(f"{case['id']}: {record.get('error', 'saved')}", flush=True)


def compatible(title: str, gold: dict) -> bool:
    # This is a lexical action proxy, not a semantic judge. Owners and dates
    # deliberately do not influence matching, so their errors remain measurable.
    title = title.casefold()
    return all(
        any(re.search(r"\b" + re.escape(term), title) for term in group)
        for group in gold["action_terms"]
    )


def score_case(case: dict, record: dict | None) -> dict:
    gold = case["gold"]
    counts = dict.fromkeys(
        [
            "predicted",
            "matched",
            "duplicates",
            "owner_correct",
            "owner_total",
            "unknown_owner_correct",
            "unknown_owner_total",
            "deadline_correct",
            "deadline_total",
            "citation_valid",
            "citation_total",
            "evidence_complete",
            "failed",
            "schema_valid",
            "negative_correct",
            "negative_total",
        ],
        0,
    )
    counts["gold"] = len(gold)
    counts["negative_total"] = int(not gold)
    result = {
        "id": case["id"],
        "gold": gold,
        "matches": [],
        "errors": [],
        "counts": counts,
    }
    try:
        if record is None or record.get("error"):
            raise ValueError("Missing or failed prediction")
        prediction = Extraction.model_validate(record["extraction"])
    except (ValueError, KeyError) as exc:
        counts["failed"] = 1
        result["errors"] = [str(exc)]
        return result
    counts["schema_valid"] = 1
    tasks = prediction.commitments
    result["predictions"] = [task.model_dump() for task in tasks]
    counts["predicted"] = len(tasks)
    counts["negative_correct"] = int(not gold and not tasks)
    edges = [
        [j for j, target in enumerate(gold) if compatible(task.title, target)]
        for task in tasks
    ]
    # Maximum-cardinality bipartite matching, preventing order-dependent scores.
    assigned = {}

    def augment(i: int, visited: set[int]) -> bool:
        for j in edges[i]:
            if j in visited:
                continue
            visited.add(j)
            if j not in assigned or augment(assigned[j], visited):
                assigned[j] = i
                return True
        return False

    for i in range(len(tasks)):
        augment(i, set())
    counts["matched"] = len(assigned)
    matched_predictions = set(assigned.values())
    counts["duplicates"] = sum(
        bool(edges[i]) for i in range(len(tasks)) if i not in matched_predictions
    )
    turns = {turn["id"]: turn["content"] for turn in case["transcript"]["turns"]}
    for item in [
        *prediction.commitments,
        *prediction.decisions,
        *prediction.suggestions,
    ]:
        for evidence in item.evidence:
            counts["citation_total"] += 1
            counts["citation_valid"] += int(
                evidence.transcript_id in turns
                and evidence.quote in turns[evidence.transcript_id]
            )
    for j, i in sorted(assigned.items()):
        task, target = tasks[i], gold[j]
        prefix = "unknown_owner" if target["owner"] is None else "owner"
        counts[f"{prefix}_total"] += 1
        counts[f"{prefix}_correct"] += int(task.owner == target["owner"])
        counts["deadline_total"] += 1
        counts["deadline_correct"] += int(task.due_date_text == target["due_date_text"])
        cited = {
            e.transcript_id
            for e in task.evidence
            if e.transcript_id in turns and e.quote in turns[e.transcript_id]
        }
        counts["evidence_complete"] += int(set(target["evidence_ids"]) <= cited)
        result["matches"].append({"prediction": i, "gold": target["id"]})
        if task.owner != target["owner"]:
            result["errors"].append(f"owner: {target['id']}")
        if task.due_date_text != target["due_date_text"]:
            result["errors"].append(f"deadline: {target['id']}")
        if not set(target["evidence_ids"]) <= cited:
            result["errors"].append(f"incomplete evidence: {target['id']}")
    result["errors"] += [
        f"unmatched prediction: {i}"
        for i in range(len(tasks))
        if i not in matched_predictions
    ]
    result["errors"] += [
        f"missed gold: {target['id']}"
        for j, target in enumerate(gold)
        if j not in assigned
    ]
    if counts["citation_valid"] != counts["citation_total"]:
        result["errors"].append("invalid citation")
    return result


def ratio(numerator: int, denominator: int) -> dict:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / denominator if denominator else None,
    }


def score(suite: dict, directory: Path) -> dict:
    metadata = json.loads((directory / "run.json").read_text())
    if metadata["suite_sha256"] != digest(suite):
        raise ValueError("Suite hash differs from inference run")
    rows = []
    times = []
    for case in suite["cases"]:
        path = directory / f"{case['id']}.json"
        record = json.loads(path.read_text()) if path.exists() else None
        if record is not None:
            if record["case_id"] != case["id"] or record["input_sha256"] != digest(
                case["transcript"]
            ):
                raise ValueError("Prediction belongs to a different input")
            times.append(record["wall_seconds"])
        rows.append(score_case(case, record))
    totals = {key: sum(row["counts"][key] for row in rows) for key in rows[0]["counts"]}
    metrics = {
        "task_precision_proxy": ratio(totals["matched"], totals["predicted"]),
        "task_recall_proxy": ratio(totals["matched"], totals["gold"]),
        "task_f1_proxy": ratio(
            2 * totals["matched"], totals["predicted"] + totals["gold"]
        ),
        "duplicate_proxy": ratio(totals["duplicates"], totals["predicted"]),
        "evidence_completeness": ratio(totals["evidence_complete"], totals["matched"]),
    }
    for name in ["owner", "unknown_owner", "deadline", "negative"]:
        metrics[name] = ratio(totals[f"{name}_correct"], totals[f"{name}_total"])
    metrics["citation_validity"] = ratio(
        totals["citation_valid"], totals["citation_total"]
    )
    return {
        "scorer_version": SCORER_VERSION,
        "run": metadata,
        "counts": totals,
        "metrics": metrics,
        "cases": rows,
        "latency_sample_count": len(times),
        "mean_wall_seconds": sum(times) / len(times) if times else None,
        "limitations": "AI-authored development labels; lexical action matching proxy; "
        "no human adjudication, held-out quality, semantic support or state scoring.",
    }


def markdown(report: dict) -> str:
    lines = [
        "# Extraction development results",
        "",
        report["limitations"],
        "",
        f"Method: {report['run']['method']}; model: {report['run']['model']}.",
        f"Scorer: {report['scorer_version']}.",
        "",
        "| Metric | Numerator / denominator | Value |",
        "| --- | --- | --- |",
    ]
    for key, metric in report["metrics"].items():
        value = "N/A" if metric["value"] is None else f"{metric['value']:.3f}"
        lines.append(
            f"| {key} | {metric['numerator']}/{metric['denominator']} | {value} |"
        )
    lines += [
        "",
        f"Failed/missing cases: {report['counts']['failed']}.",
        f"Mean extraction wall time: {report['mean_wall_seconds']} seconds "
        f"({report['latency_sample_count']} attempts, includes failures and warmup).",
        "",
        "| Case | Expected tasks | Actual tasks | Observed errors |",
        "| --- | --- | --- | --- |",
    ]
    for row in report["cases"]:
        expected = "; ".join(g["title"] for g in row["gold"]) or "none"
        actual = "; ".join(p["title"] for p in row.get("predictions", [])) or "none"
        errors = "; ".join(row["errors"]) or "none under proxy"
        cells = [row["id"], expected, actual, errors]
        lines.append(
            "| "
            + " | ".join(c.replace("|", "\\|").replace("\n", " ") for c in cells)
            + " |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "score"])
    parser.add_argument(
        "--suite", type=Path, default=Path("tests/fixtures/evaluation/development.json")
    )
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument(
        "--method", choices=["rules", "codex", "claude", "ollama"], default="rules"
    )
    parser.add_argument("--model")
    args = parser.parse_args()
    try:
        suite = load_suite(args.suite)
        if args.command == "run":
            if args.method != "rules" and not args.model:
                parser.error("--model is required for live inference")
            run(suite, args.directory, args.method, args.model)
        else:
            report = score(suite, args.directory)
            (args.directory / "scores.json").write_text(
                json.dumps(report, indent=2) + "\n"
            )
            (args.directory / "report.md").write_text(markdown(report))
            print(markdown(report))
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        parser.exit(1, f"evaluation: {exc}\n")


if __name__ == "__main__":
    main()
