import argparse
import hashlib
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from uuid import UUID

from labsync import chat, codex_client

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    raise SystemExit("Output already exists; choose a new file")
args.output.parent.mkdir(parents=True, exist_ok=True)
original = json.loads(Path("docs/evidence/rag_2026-10-21.json").read_text())
out = args.output
questions = {q["id"]: q for q in original["dataset"]["questions"]}
result = {
    "experiment": "m4-frozen-source-rerun",
    "source": "docs/evidence/rag_2026-10-21.json",
    "source_sha256": hashlib.sha256(
        Path("docs/evidence/rag_2026-10-21.json").read_bytes()
    ).hexdigest(),
    "model": "gpt-5.6-sol",
    "cli": subprocess.check_output(["codex", "--version"], text=True).strip(),
    "prompt_version": chat.PROMPT_VERSION,
    "retrieval_rerun": False,
    "runs": [],
}
result["expected_calls"] = len(original["runs"])
failures = 0
for row in original["runs"]:
    sources = [
        chat.Source(
            **{
                **s,
                "meeting_id": UUID(str(s["meeting_id"])),
                "meeting_date": datetime.fromisoformat(s["meeting_date"]),
            }
        )
        for s in row["sources"]
    ]
    prompt = chat.build_prompt(questions[row["question_id"]]["question"], [], sources)
    r = {
        "question_id": row["question_id"],
        "mode": row["mode"],
        "status": "running",
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
    }
    result["runs"].append(r)
    out.write_text(json.dumps(result, indent=2, default=str))
    start = time.perf_counter()
    try:
        raw, usage = codex_client.run(
            prompt,
            chat.ChatAnswer.model_json_schema(),
            model="gpt-5.6-sol",
            timeout=180,
            task="m4-frozen-rag",
        )
        answer, citations = chat.finalize(
            chat.ChatAnswer.model_validate_json(raw), sources
        )
        r.update(
            status="completed",
            raw=json.loads(raw),
            usage=usage,
            answer=answer,
            citations=citations,
            refused=answer == chat.NO_ANSWER,
            human_correctness="not reviewed",
        )
    except KeyboardInterrupt:
        r.update(status="interrupted")
        result["stop_reason"] = "operator interruption"
    except (RuntimeError, ValueError) as e:
        r.update(status="failed", error=str(e))
        failures += 1
    r["seconds"] = time.perf_counter() - start
    out.write_text(json.dumps(result, indent=2, default=str))
    print(r["question_id"], r["mode"], r["status"], round(r["seconds"], 2), flush=True)
    if failures >= 3 or r["status"] == "interrupted":
        result.setdefault("stop_reason", "three failed calls")
        out.write_text(json.dumps(result, indent=2, default=str))
        break
