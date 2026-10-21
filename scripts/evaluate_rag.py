"""Read-only dense/hybrid pilot using the production index, sources and chat prompt.

Run from repository root with DATABASE_URL, OPENAI_API_KEY and LABSYNC_CODEX_CLI
configured. Never writes database rows, changes prompts, or tunes labels.
"""

import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import time
from dataclasses import asdict
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from labsync import chat, codex_client
from labsync.db import rag
from labsync.embeddings import DIMENSIONS, MODEL, OpenAIEmbedder, to_pgvector
from labsync.providers import codex_executable


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, default=str).encode()
    ).hexdigest()


def target_rank(hits, target):
    return next((i + 1 for i, hit in enumerate(hits) if str(hit["id"]) == target), None)


def dense(conn, project, meeting, vector):
    return conn.execute(
        """
        SELECT c.id,c.meeting_id,c.kind,c.source_id,c.first_turn_order,
            c.last_turn_order,c.start_time_ms,c.content,m.name meeting_name,
            m.meeting_date,1-(c.embedding <=> %(vector)s::vector) score
        FROM rag_chunks c JOIN meetings m ON m.id=c.meeting_id
        LEFT JOIN tasks t ON c.kind='task' AND t.id=c.source_id
        WHERE c.project_id=%(project)s
          AND (%(meeting)s::uuid IS NULL OR c.meeting_id=%(meeting)s::uuid)
          AND (t.id IS NULL OR t.review_status <> 'dismissed')
        ORDER BY c.embedding <=> %(vector)s::vector,c.id LIMIT 8
        """,
        {"project": project, "meeting": meeting, "vector": to_pgvector(vector)},
    ).fetchall()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset", type=Path, default=Path("tests/fixtures/rag/development.json")
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--answers",
        action="store_true",
        help="Run live Codex on saved retrieval sources",
    )
    args = parser.parse_args()
    dataset = json.loads(args.dataset.read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    result = {
        "dataset": dataset,
        "dataset_sha256": digest(dataset),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "working_tree_changes": subprocess.check_output(
            ["git", "status", "--short"], text=True
        ),
        "platform": platform.platform(),
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config": {
            "embedding_model": MODEL,
            "dimensions": DIMENSIONS,
            "k": 8,
            "rrf_k": rag.RRF_K,
            "leg_depth": rag.LEG_DEPTH,
            "chat_prompt_version": chat.PROMPT_VERSION,
            "model_requested": "gpt-5.6-sol",
            "history": [],
            "database_read_only": True,
            "timing_repeats": 3,
        },
        "runs": [],
    }
    questions = dataset["questions"]
    started = time.perf_counter()
    vectors = OpenAIEmbedder().encode([q["question"] for q in questions])
    result["embedding_batch_seconds"] = time.perf_counter() - started
    result["query_vectors_sha256"] = digest(vectors)
    (args.output / "query_vectors.json").write_text(json.dumps(vectors))
    with psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row) as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        corpus = conn.execute(
            """SELECT c.id,c.meeting_id,c.kind,c.source_id,c.first_turn_order,
            c.last_turn_order,c.content,c.embedding::text,c.embedding_model,
            t.review_status FROM rag_chunks c
            LEFT JOIN tasks t ON c.kind='task' AND t.id=c.source_id
            WHERE c.project_id=%s ORDER BY c.id""",
            (dataset["project_id"],),
        ).fetchall()
        result["corpus_sha256"] = digest(corpus)
        result["corpus_manifest"] = [
            {
                "id": str(r["id"]),
                "meeting_id": str(r["meeting_id"]),
                "kind": r["kind"],
                "content_sha256": digest(r["content"]),
                "embedding_model": r["embedding_model"],
            }
            for r in corpus
        ]
        (args.output / "corpus.json").write_text(json.dumps(corpus, default=str))
        for i, (question, vector) in enumerate(zip(questions, vectors, strict=True)):
            # Alternate first variant to reduce a fixed warm-cache order advantage.
            modes = ["dense", "hybrid"] if i % 2 == 0 else ["hybrid", "dense"]
            for mode in modes:
                timings = []
                for _ in range(3):
                    started = time.perf_counter()
                    if mode == "dense":
                        hits = dense(
                            conn, dataset["project_id"], question["meeting_id"], vector
                        )
                    else:
                        hits = rag.search(
                            conn,
                            project_id=UUID(dataset["project_id"]),
                            meeting_id=question["meeting_id"],
                            text=question["question"],
                            vector=vector,
                        )
                    timings.append(time.perf_counter() - started)
                if question["meeting_id"] and any(
                    str(h["meeting_id"]) != question["meeting_id"] for h in hits
                ):
                    raise RuntimeError("Meeting scope violation")
                sources = chat.build_sources(conn, hits)
                row = {
                    "question_id": question["id"],
                    "mode": mode,
                    "retrieval_seconds": timings,
                    "target_rank": target_rank(hits, question["target_chunk_id"]),
                    "answer_status": "not_run",
                    "hits": hits,
                    "sources": [asdict(s) for s in sources],
                }
                result["runs"].append(row)
                print(
                    f"Retrieved {question['id']} {mode}: "
                    f"target rank {row['target_rank']}",
                    flush=True,
                )
    # End read-only snapshot before slow external model calls.
    result["codex_version"] = subprocess.check_output(
        [codex_executable(), "--version"], text=True
    ).strip()

    def save():
        (args.output / "results.json").write_text(
            json.dumps(result, indent=2, default=str) + "\n"
        )

    save()
    if args.answers:
        by_id = {q["id"]: q for q in questions}
        failures = 0
        for row in result["runs"]:
            q = by_id[row["question_id"]]
            sources = [
                chat.Source(**{**s, "meeting_id": UUID(str(s["meeting_id"]))})
                for s in row["sources"]
            ]
            prompt = chat.build_prompt(q["question"], [], sources)
            row["prompt_sha256"] = hashlib.sha256(prompt.encode()).hexdigest()
            row["prompt"] = prompt
            row["answer_status"] = "running"
            save()
            interrupted = False
            started = time.perf_counter()
            try:
                raw, usage = codex_client.run(
                    prompt,
                    chat.ChatAnswer.model_json_schema(),
                    model="gpt-5.6-sol",
                    timeout=180,
                    task="rag-evaluation",
                )
                reply = chat.ChatAnswer.model_validate_json(raw)
                answer, citations = chat.finalize(reply, sources)
                row.update(
                    {
                        "answer_status": "completed",
                        "raw_answer": json.loads(raw),
                        "answer": answer,
                        "citations": citations,
                        "usage": usage,
                        "refused": answer == chat.NO_ANSWER,
                        "human_correctness": "not reviewed",
                        "human_citation_entailment": "not reviewed",
                    }
                )
            except KeyboardInterrupt:
                row["answer_status"] = "interrupted"
                interrupted = True
            except (RuntimeError, ValueError) as exc:
                row["answer_status"] = "failed"
                row["error"] = str(exc)
                failures += 1
            row["answer_seconds"] = time.perf_counter() - started
            save()
            print(
                f"{row['answer_status']} {row['question_id']} {row['mode']}: "
                f"{row['answer_seconds']:.2f}s",
                flush=True,
            )
            if interrupted or failures >= 3:
                result["answer_stop_reason"] = (
                    "operator interruption" if interrupted else "three failed calls"
                )
                break
    summary = {}
    for mode in ["dense", "hybrid"]:
        rows = [r for r in result["runs"] if r["mode"] == mode]
        positive_ids = {q["id"] for q in questions if q["target_chunk_id"]}
        positive = [r for r in rows if r["question_id"] in positive_ids]
        summary[mode] = {
            "supported_target_denominator": len(positive),
            **{
                f"target_hit_at_{k}": sum(
                    r["target_rank"] is not None and r["target_rank"] <= k
                    for r in positive
                )
                for k in [1, 3, 8]
            },
            "target_mrr_at_8": statistics.mean(
                1 / r["target_rank"] if r["target_rank"] else 0 for r in positive
            ),
            "retrieval_median_seconds": statistics.median(
                t for r in rows for t in r["retrieval_seconds"]
            ),
            "answer_median_seconds": statistics.median(
                [r["answer_seconds"] for r in rows if "answer" in r]
            )
            if any("answer" in r for r in rows)
            else None,
        }
    result["summary"] = summary
    save()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
