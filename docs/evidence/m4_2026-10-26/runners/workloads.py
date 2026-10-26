import argparse
import json
import platform
import subprocess
import sys
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
root = Path.cwd()
out = args.output
saved = json.loads((root / "docs/evidence/rag_2026-10-21.json").read_text())
qs = {q["id"]: q for q in saved["dataset"]["questions"]}
result = {
    "environment": platform.platform(),
    "processor": platform.machine(),
    "model": "gpt-5.6-sol",
    "whisper": "mlx/base",
    "diarize": False,
    "cli": subprocess.check_output(["codex", "--version"], text=True).strip(),
    "scope": (
        "local audio-to-extraction and frozen-source chat, "
        "excludes upload/auth/database/retrieval/mobile UI"
    ),
    "runs": [],
}
for workload in ["recording-to-results", "supported-chat", "unsupported-chat"]:
    for i in range(3):
        t = time.perf_counter()
        r = {
            "workload": workload,
            "repeat": i + 1,
            "cache": "existing model weights; new process; provider cache uncontrolled",
        }
        try:
            if workload == "recording-to-results":
                directory = args.output.parent / f"{args.output.stem}-audio-{i + 1}"
                cmd = [
                    sys.executable,
                    "-m",
                    "labsync",
                    "transcribe",
                    str(root / "tests/fixtures/ami/TS3005a-90s-135s.wav"),
                    "--source",
                    str(root / "contexts/meeting_transcriber-master"),
                    "--project-id",
                    "m4-public-ami",
                    "--meeting-id",
                    f"m4-workload-{i + 1}",
                    "--whisper-backend",
                    "mlx",
                    "--whisper-model",
                    "base",
                    "--no-diarize",
                    "--output-dir",
                    str(directory),
                ]
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if p.returncode:
                    raise RuntimeError(p.stderr[-1200:])
                r["transcription_seconds"] = time.perf_counter() - t
                from labsync.extraction import Transcript

                extraction = codex_client.extract(
                    Transcript.model_validate_json(
                        (directory / "transcript.json").read_text()
                    ),
                    model="gpt-5.6-sol",
                    timeout=180,
                )
                (directory / "extraction.json").write_text(
                    json.dumps(extraction, indent=2)
                )
                r["usage"] = extraction["usage"]
                r["extraction_seconds"] = extraction["elapsed_seconds"]
                r["audio_seconds"] = 45
            else:
                qid = "price" if workload == "supported-chat" else "unicorn"
                row = next(
                    r
                    for r in saved["runs"]
                    if r["question_id"] == qid and r["mode"] == "hybrid"
                )
                sources = [
                    chat.Source(
                        **{
                            **s,
                            "meeting_id": UUID(s["meeting_id"]),
                            "meeting_date": datetime.fromisoformat(s["meeting_date"]),
                        }
                    )
                    for s in row["sources"]
                ]
                prompt = chat.build_prompt(qs[qid]["question"], [], sources)
                raw, usage = codex_client.run(
                    prompt,
                    chat.ChatAnswer.model_json_schema(),
                    model="gpt-5.6-sol",
                    timeout=180,
                    task="m4-workload",
                )
                answer, citations = chat.finalize(
                    chat.ChatAnswer.model_validate_json(raw), sources
                )
                r.update(
                    question_id=qid,
                    raw=json.loads(raw),
                    usage=usage,
                    answer=answer,
                    citations=citations,
                    refused=answer == chat.NO_ANSWER,
                )
            r["status"] = "completed"
        except Exception as e:
            r.update(status="failed", error=str(e))
        r["seconds"] = time.perf_counter() - t
        result["runs"].append(r)
        out.write_text(json.dumps(result, indent=2))
        print(workload, i + 1, r["status"], round(r["seconds"], 2), flush=True)
