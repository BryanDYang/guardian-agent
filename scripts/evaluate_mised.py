"""MISeD RAG evaluation through the app's real retrieval and chat code.

Loads each MISeD meeting into LOCAL Supabase as a transcript-only meeting, indexes
it with the app's chunking and embeddings, then runs every dialog turn through the
same path as POST /api/v1/conversations/{id}/messages: retrieval_text -> embed ->
rag.search (this meeting only, top 8) -> build_sources -> chat.answer. Scores
retrieval, citations and refusals against MISeD's gold attribution spans.

Usage (from the repo root, after `supabase start`):

    uv run --locked --env-file .env --extra server \
        python scripts/evaluate_mised.py --provider claude --answer-sample 200 \
        --output artifacts/mised/test-run1

Retrieval metrics use every turn. Answer and citation metrics use the turns sent
to the model: all of them by default, a stratified seeded sample with
--answer-sample N, or none with --retrieval-only.

Writes run.json, meetings.json, per_turn.jsonl, per_turn.csv, summary.csv,
summary.json and spot_check.csv (false refusals and answers to unanswerable turns,
for hand review). Never point --database-url at the hosted project.
"""

import argparse
import csv
import hashlib
import importlib.metadata
import json
import logging
import platform
import random
import re
import statistics
import subprocess
import time
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from labsync import chat, chunking, providers
from labsync.db import meetings, rag
from labsync.embeddings import MODEL as EMBEDDING_MODEL
from labsync.embeddings import OpenAIEmbedder
from labsync.extraction import Transcript

LOCAL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
MEETING_DATE = date(2026, 1, 1)  # MISeD has no dates; one fixed placeholder
SEGMENT_MS = 10_000  # MISeD has no timestamps; segment i starts at i * 10 s
SPEAKER_CHARS = 64  # meeting_transcripts.speaker_label is VARCHAR(64)
EMPTY_EXTRACTION = {
    "summary": "",
    "decisions": [],
    "commitments": [],
    "suggestions": [],
}


def domain(meeting_id: str) -> str:
    if re.fullmatch(r"(ES|IS|TS|EN)\d{4}[a-d]", meeting_id):
        return "AMI"
    if re.fullmatch(r"B[a-z]{2}\d{3}", meeting_id):
        return "ICSI"
    return "parliament"


def gold_segments(turn: dict) -> set[int]:
    """Inclusive index ranges. Omitted fields are 0 (protobuf JSON drops zeros)."""
    segments = set()
    for r in turn.get("responseAttribution", {}).get("indexRanges", []):
        segments.update(range(r.get("startIndex", 0), r.get("endIndex", 0) + 1))
    return segments


def load_meeting(conn, project_id, meeting: dict) -> tuple[str, int]:
    """Insert one MISeD transcript as a meeting and index it like the app does."""
    meeting_uuid = str(uuid4())
    turns = [
        {
            "id": f"{meeting_uuid}:turn:{i}",
            # A few parliament names carry long titles, e.g. "Hon. Mary Ng
            # (Minister of ...)"; the name itself comes first and is kept.
            "speaker": s["speakerName"][:SPEAKER_CHARS],
            "start_time_ms": i * SEGMENT_MS,
            "end_time_ms": (i + 1) * SEGMENT_MS - 1,
            "content": s["text"],
        }
        for i, s in enumerate(meeting["transcriptSegments"])
    ]
    transcript = Transcript.model_validate(
        {"project_id": str(project_id), "meeting_id": meeting_uuid, "turns": turns}
    )
    with conn.transaction():
        meetings.create_meeting(
            conn,
            meeting_id=meeting_uuid,
            project_id=project_id,
            name=meeting["meetingId"],
            meeting_date=MEETING_DATE,
            audio_file_path=None,
        )
        meetings.save_results(
            conn, meeting_uuid, transcript, {"extraction": EMPTY_EXTRACTION}, {}
        )
        meetings.update_status(conn, meeting_uuid, "completed", 1, None)
        chunks = rag.index_meeting(conn, meeting_uuid, OpenAIEmbedder())
    return meeting_uuid, chunks


def answer_sample(dialogs: list[dict], size: int, seed: int) -> set[tuple[str, int]]:
    """Seeded sample of turns to answer, stratified by domain and answerability
    so the sample keeps the split's mix."""
    strata: dict[tuple[str, bool], list[tuple[str, int]]] = {}
    for d in dialogs:
        group = domain(d["meeting"]["meetingId"])
        for i, turn in enumerate(d["dialog"]["dialogTurns"]):
            key = (group, bool(gold_segments(turn)))
            strata.setdefault(key, []).append((d["dialogId"], i))
    total = sum(len(keys) for keys in strata.values())
    if size >= total:
        return {key for keys in strata.values() for key in keys}
    # Proportional quotas; leftover slots go to the largest remainders.
    quotas = {s: size * len(keys) / total for s, keys in strata.items()}
    counts = {s: int(q) for s, q in quotas.items()}
    leftover = size - sum(counts.values())
    for s in sorted(quotas, key=lambda s: (counts[s] - quotas[s], s))[:leftover]:
        counts[s] += 1
    rng = random.Random(seed)
    return {
        key for s in sorted(strata) for key in rng.sample(sorted(strata[s]), counts[s])
    }


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record):
        self.messages.append(record.getMessage())


# Why a reply became NO_ANSWER. "model_*" means the model declined; the others
# mean chat.finalize rejected an answer the model did give.
REASONS = [
    "model_unanswerable",  # model set answerable=false
    "model_no_citations",  # answerable, but empty text or no citations
    "quote_not_in_source",  # a quote is not verbatim in its cited source
    "invalid_ref",  # cited a source ref that was not shown
    "marker_mismatch",  # [T#] markers in the text != the cited refs
    "no_sources",  # retrieval returned nothing; no model call
]


def refusal_reason(reply, sources, raw, messages) -> str:
    if reply != chat.NO_ANSWER:
        return ""
    if not sources:
        return "no_sources"
    if raw is not None and raw.get("answerable") is False:
        return "model_unanswerable"
    text = " ".join(messages)
    if "quote not in source" in text:
        return "quote_not_in_source"
    if "was not shown" in text:
        return "invalid_ref"
    if "markers and verified citations disagree" in text:
        return "marker_mismatch"
    return "model_no_citations"


def ask(conn, project_id, meeting_uuid, question, history, args, answer) -> dict:
    """The app's answer path for one question, with timings. With answer=False,
    stop after retrieval: no model call."""
    started = time.perf_counter()
    query = chat.retrieval_text(question, history)
    [vector] = OpenAIEmbedder().encode([query])
    hits = rag.search(
        conn,
        project_id=project_id,
        meeting_id=meeting_uuid,
        text=query,
        vector=vector,
        limit=chat.SEARCH_LIMIT,
    )
    sources = chat.build_sources(conn, hits)
    retrieved = time.perf_counter()
    result = {
        "hits": [
            [h["first_turn_order"], h["last_turn_order"]]
            for h in hits
            if h["kind"] == "transcript"
        ],
        "retrieval_seconds": round(retrieved - started, 3),
        "sampled": answer,
    }
    if not answer:
        return result

    # Observe the app's answer path without changing it: keep the model's raw
    # reply and the warnings chat.finalize logs when it rejects an answer.
    raw_replies, warnings = [], _Capture()
    original = providers.structured

    def keep_raw(*a, **k):
        raw = original(*a, **k)
        raw_replies.append(raw)
        return raw

    providers.structured = keep_raw
    chat.log.addHandler(warnings)
    try:
        reply, citations = chat.answer(
            question,
            history,
            sources,
            provider=args.provider,
            model=args.model,
            timeout=args.timeout,
        )
    except RuntimeError as exc:
        # Keep what the model sent and why it failed to parse, for the record.
        exc.raw_reply = raw_replies[-1] if raw_replies else None
        exc.detail = str(exc.__cause__) if exc.__cause__ else ""
        raise
    finally:
        providers.structured = original
        chat.log.removeHandler(warnings)
    raw = raw_replies[-1] if raw_replies else None
    return result | {
        "answer": reply,
        "refused": reply == chat.NO_ANSWER,
        "refusal_reason": refusal_reason(reply, sources, raw, warnings.messages),
        "validator_log": warnings.messages,
        "raw_reply": raw,
        "cited_turns": sorted(
            {int(c["turn_key"].rsplit(":", 1)[1]) for c in citations if c["turn_key"]}
        ),
        "answer_seconds": round(time.perf_counter() - retrieved, 3),
    }


def score(record: dict) -> dict:
    """Per-turn metrics against MISeD's gold attribution segments."""
    gold = set(record["gold_segments"])
    row = {
        "dialog": record["dialog_id"],
        "turn": record["turn"],
        "meeting": record["meeting"],
        "domain": record["domain"],
        "query_type": record["query_type"],
        "answerable": bool(gold),
        "error": record.get("error", ""),
    }
    if row["error"]:
        return row
    retrieved = {t for first, last in record["hits"] for t in range(first, last + 1)}
    row["sampled"] = sampled = record.get("sampled", True)
    row["retrieval_seconds"] = record["retrieval_seconds"]
    if sampled:
        row["refused"] = record["refused"]
        row["refusal_reason"] = record.get("refusal_reason", "")
        row["answer_seconds"] = record["answer_seconds"]
        cited = set(record["cited_turns"])
    if gold:
        ranks = [
            rank
            for rank, (first, last) in enumerate(record["hits"], 1)
            if gold & set(range(first, last + 1))
        ]
        row["hit_at_8"] = bool(ranks)
        row["reciprocal_rank"] = 1 / ranks[0] if ranks else 0.0
        row["evidence_recall_at_8"] = len(gold & retrieved) / len(gold)
        if sampled and not record["refused"]:
            row["cited"] = len(cited)
            row["cited_gold"] = len(cited & gold)
            row["gold"] = len(gold)
    return row


def summarize(rows: list[dict]) -> dict:
    ok = [r for r in rows if not r["error"]]
    answerable = [r for r in ok if r["answerable"]]
    unanswerable = [r for r in ok if not r["answerable"]]
    # Answer and citation metrics use only the turns that were sent to the model.
    sampled = [r for r in ok if r["sampled"]]
    s_answerable = [r for r in sampled if r["answerable"]]
    s_unanswerable = [r for r in sampled if not r["answerable"]]
    answered = [r for r in s_answerable if not r["refused"]]

    def mean(values):
        values = list(values)
        return round(sum(values) / len(values), 4) if values else None

    def median(values):
        values = list(values)
        return round(statistics.median(values), 2) if values else None

    cited = sum(r["cited"] for r in answered)
    return {
        "turns": len(rows),
        "errors": len(rows) - len(ok),
        "answerable": len(answerable),
        "unanswerable": len(unanswerable),
        # Retrieval: every answerable turn
        "hit_at_8": mean(r["hit_at_8"] for r in answerable),
        "mrr_at_8": mean(r["reciprocal_rank"] for r in answerable),
        "evidence_recall_at_8": mean(r["evidence_recall_at_8"] for r in answerable),
        "median_retrieval_seconds": median(r["retrieval_seconds"] for r in ok),
        # Answers: sampled turns only
        "answered_sample": len(sampled),
        "sample_answerable": len(s_answerable),
        "sample_unanswerable": len(s_unanswerable),
        "answer_rate_answerable": mean(not r["refused"] for r in s_answerable),
        # Lower bound: a "that wasn't discussed" answer counts as not refusing.
        "correct_refusal_unanswerable": mean(r["refused"] for r in s_unanswerable),
        # Why answerable turns were refused (counts of false refusals)
        **{
            f"false_refusal_{reason}": sum(
                r["refused"] and r["refusal_reason"] == reason for r in s_answerable
            )
            for reason in REASONS
        },
        # Citations, answered answerable turns, pooled over cited turns
        "citation_precision": (
            round(sum(r["cited_gold"] for r in answered) / cited, 4) if cited else None
        ),
        "citation_recall": (
            round(
                sum(r["cited_gold"] for r in answered)
                / sum(r["gold"] for r in answered),
                4,
            )
            if answered
            else None
        ),
        "cites_any_gold": mean(r["cited_gold"] > 0 for r in answered),
        "median_answer_seconds": median(r["answer_seconds"] for r in sampled),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--data", type=Path, default=Path("contexts/datasets/mised/test.jsonl")
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--database-url", default=LOCAL)
    parser.add_argument("--provider", default=providers.default_provider())
    parser.add_argument("--model", help="Default: the provider's default model")
    parser.add_argument("--timeout", type=int, default=90)  # the app's limit
    parser.add_argument("--max-dialogs", type=int, help="First N dialogs (smoke)")
    answers = parser.add_mutually_exclusive_group()
    answers.add_argument(
        "--retrieval-only", action="store_true", help="No model calls at all"
    )
    answers.add_argument(
        "--answer-sample",
        type=int,
        metavar="N",
        help="Answer a seeded sample of N turns; retrieve for every turn",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--resume", action="store_true", help="Skip turns already answered"
    )
    args = parser.parse_args()

    if urlparse(args.database_url).hostname not in {"127.0.0.1", "localhost"}:
        parser.error("--database-url must be a local database, never hosted")
    if args.provider not in providers.DEFAULT_MODELS:
        parser.error(f"unknown provider {args.provider!r}")
    if args.output.exists() and not args.resume:
        parser.error(f"{args.output} exists; use a new directory or --resume")
    try:
        psycopg.connect(args.database_url).close()
    except psycopg.OperationalError:
        parser.error(f"cannot reach {args.database_url}; run `supabase start` first")
    args.output.mkdir(parents=True, exist_ok=True)

    dialogs = [json.loads(line) for line in args.data.open() if line.strip()]
    dialogs = dialogs[: args.max_dialogs] if args.max_dialogs else dialogs
    model = args.model or providers.DEFAULT_MODELS[args.provider]
    if args.retrieval_only:
        to_answer, answer_mode = set(), "none"
    elif args.answer_sample:
        to_answer = answer_sample(dialogs, args.answer_sample, args.seed)
        answer_mode = f"sample of {len(to_answer)} (seed {args.seed})"
    else:
        to_answer = {
            (d["dialogId"], i)
            for d in dialogs
            for i in range(len(d["dialog"]["dialogTurns"]))
        }
        answer_mode = "all"
    run = {
        "started_at": datetime.now(UTC).isoformat(),
        "data": str(args.data),
        "data_sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(),
        "dialogs": len(dialogs),
        "provider": args.provider,
        "model": model,
        "answers": answer_mode,
        "chat_prompt_version": chat.PROMPT_VERSION,
        "search_limit": chat.SEARCH_LIMIT,
        "history_messages": chat.HISTORY_MESSAGES,
        "history": "MISeD gold responses (task-instance setup), last N messages",
        "scope": "one meeting per dialog; transcript only, no extraction",
        "embedding_model": EMBEDDING_MODEL,
        "chunk_max_words": chunking.MAX_WORDS,
        "rrf_k": rag.RRF_K,
        "leg_depth": rag.LEG_DEPTH,
        "synthetic": {
            "segment_ms": SEGMENT_MS,
            "meeting_date": str(MEETING_DATE),
            "speaker_names_truncated_to": SPEAKER_CHARS,
        },
        "git_revision": subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip(),
        "platform": platform.platform(),
        "versions": {"psycopg": importlib.metadata.version("psycopg")},
    }
    run_path = args.output / "run.json"
    if args.resume and run_path.exists():
        old = json.loads(run_path.read_text())
        keys = ["data_sha256", "dialogs", "provider", "model", "answers"]
        for key in keys + ["chat_prompt_version"]:
            if old[key] != run[key]:
                parser.error(f"--resume must keep the same {key} ({old[key]})")
        run = {**old, "resumed_at": run["started_at"]}
    run_path.write_text(json.dumps(run, indent=2) + "\n")

    records_path = args.output / "per_turn.jsonl"
    done = set()
    if records_path.exists():
        previous = [json.loads(line) for line in records_path.open()]
        kept = [r for r in previous if not r.get("error")]  # errors are retried
        # Keep failed attempts as evidence: the retry replaces them in the results.
        with (args.output / "failed_attempts.jsonl").open("a") as f:
            for r in previous:
                if r.get("error"):
                    retried = run.get("resumed_at", run["started_at"])
                    f.write(json.dumps(r | {"retried_at": retried}) + "\n")
        records_path.write_text("".join(json.dumps(r) + "\n" for r in kept))
        done = {(r["dialog_id"], r["turn"]) for r in kept}

    meetings_path = args.output / "meetings.json"
    loaded = json.loads(meetings_path.read_text()) if meetings_path.exists() else {}
    with psycopg.connect(
        args.database_url, row_factory=dict_row, autocommit=True
    ) as conn:
        name = f"MISeD eval {args.output.name}"
        project = (
            conn.execute("SELECT id FROM projects WHERE name = %s", (name,)).fetchone()
            or conn.execute(
                "INSERT INTO projects (name) VALUES (%s) RETURNING id", (name,)
            ).fetchone()
        )
        project_id = project["id"]

        for d in dialogs:
            meeting_id = d["meeting"]["meetingId"]
            exists = (
                meeting_id in loaded
                and conn.execute(
                    "SELECT 1 FROM meetings WHERE id = %s",
                    (loaded[meeting_id]["uuid"],),
                ).fetchone()
            )
            if not exists:
                meeting_uuid, chunks = load_meeting(conn, project_id, d["meeting"])
                loaded[meeting_id] = {"uuid": meeting_uuid, "chunks": chunks}
                meetings_path.write_text(json.dumps(loaded, indent=2) + "\n")
                print(f"indexed {meeting_id}: {chunks} chunks", flush=True)

        with records_path.open("a") as out:
            for d in dialogs:
                meeting_id = d["meeting"]["meetingId"]
                history = []
                for i, turn in enumerate(d["dialog"]["dialogTurns"]):
                    key = (d["dialogId"], i)
                    if key not in done:
                        record = {
                            "dialog_id": d["dialogId"],
                            "turn": i,
                            "meeting": meeting_id,
                            "domain": domain(meeting_id),
                            "query_type": turn["queryMetadata"]["queryType"]
                            .removeprefix("QUERY_TYPE_")
                            .lower(),
                            "question": turn["query"],
                            "reference": turn["response"],
                            "gold_segments": sorted(gold_segments(turn)),
                        }
                        try:
                            record |= ask(
                                conn,
                                project_id,
                                loaded[meeting_id]["uuid"],
                                turn["query"],
                                history[-chat.HISTORY_MESSAGES :],
                                args,
                                answer=key in to_answer,
                            )
                        except RuntimeError as exc:
                            record["error"] = str(exc)
                            record["error_detail"] = getattr(exc, "detail", "")
                            record["raw_reply"] = getattr(exc, "raw_reply", None)
                        out.write(json.dumps(record) + "\n")
                        out.flush()
                        r = score(record)
                        if r["error"]:
                            status = "ERROR"
                        elif not r["sampled"]:
                            status = "retrieved"
                        elif r["refused"]:
                            status = f"refused ({r['refusal_reason']})"
                        else:
                            status = "answered"
                        print(
                            f"{meeting_id} {d['dialogId'][:8]} turn {i}: {status} "
                            f"(gold {len(record['gold_segments'])}, "
                            f"hit@8 {r.get('hit_at_8', '-')})",
                            flush=True,
                        )
                    history += [
                        {"role": "user", "content": turn["query"]},
                        {"role": "assistant", "content": turn["response"]},
                    ]

    records = [json.loads(line) for line in records_path.open()]
    rows = [score(r) for r in records]
    with (args.output / "per_turn.csv").open("w", newline="") as f:
        fields = list(dict.fromkeys(k for r in rows for k in r))
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    # Hand review: refusals of answerable turns, and answers to turns MISeD marks
    # as unanswerable (often a correct "that wasn't discussed").
    with (args.output / "spot_check.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["case", "dialog", "turn", "meeting", "question", "mised_reference"]
            + ["app_answer", "refusal_reason", "model_raw_answer", "validator_log"]
            + ["judgment", "notes"]
        )
        for r in records:
            if r.get("error") or not r.get("sampled", True):
                continue
            gold = bool(r["gold_segments"])
            if gold and r["refused"]:
                case = "false_refusal"
            elif not gold and not r["refused"]:
                case = "answered_unanswerable"
            else:
                continue
            raw = r.get("raw_reply") or {}
            writer.writerow(
                [case, r["dialog_id"], r["turn"], r["meeting"], r["question"]]
                + [r.get("reference", ""), r["answer"], r.get("refusal_reason", "")]
                + [raw.get("answer", ""), " | ".join(r.get("validator_log", []))]
                + ["", ""]
            )

    groups = {"all": rows}
    for key in ["domain", "query_type", "answerable"]:
        for value in sorted({str(r[key]) for r in rows}):
            groups[f"{key}={value}"] = [r for r in rows if str(r[key]) == value]
    summary = {name: summarize(subset) for name, subset in groups.items()}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (args.output / "summary.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        columns = list(summary["all"])
        writer.writerow(["group", *columns])
        for name, s in summary.items():
            writer.writerow([name, *(s[c] for c in columns)])

    shown = [
        "turns",
        "hit_at_8",
        "mrr_at_8",
        "answered_sample",
        "answer_rate_answerable",
        "correct_refusal_unanswerable",
        "citation_precision",
        "citation_recall",
    ]
    print("\n| Group | " + " | ".join(shown) + " |")
    print("|" + " --- |" * (len(shown) + 1))
    for name, s in summary.items():
        cells = ["-" if s[c] is None else f"{s[c]}" for c in shown]
        print(f"| {name} | " + " | ".join(cells) + " |")
    print(f"Errors: {summary['all']['errors']}")


if __name__ == "__main__":
    main()
