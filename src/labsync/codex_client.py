"""Small structured-output client using the supported Codex CLI login path."""

import json
import subprocess
import tempfile
import time
from hashlib import sha256
from pathlib import Path

from .extraction import (
    PROMPT_VERSION,
    Extraction,
    Transcript,
    build_prompt,
    save_rejected,
)


def extract(
    transcript: Transcript,
    *,
    model: str,
    timeout: int = 180,
    rejected: Path | None = None,
) -> dict:
    """Run one independent meeting; never read or copy Codex credentials."""
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    prompt = build_prompt(transcript)
    started = time.monotonic()
    raw, usage = run(
        prompt,
        Extraction.model_json_schema(),
        model=model,
        timeout=timeout,
        task="extraction",
    )
    try:
        extraction, repairs = Extraction.model_validate_json(raw).repair_evidence(
            transcript
        )
        extraction.check_evidence(transcript)
    except ValueError:
        if rejected is not None:
            save_rejected(rejected, raw)
        raise
    version = subprocess.run(
        ["codex", "--version"],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    ).stdout.strip()
    return {
        "project_id": transcript.project_id,
        "meeting_id": transcript.meeting_id,
        "provider": "codex-cli",
        "model_requested": model,
        "codex_version": version,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": sha256(prompt.encode("utf-8")).hexdigest(),
        "transcript_sha256": sha256(
            transcript.model_dump_json().encode("utf-8")
        ).hexdigest(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "usage": usage,
        "evidence_repairs": repairs,
        "extraction": extraction.model_dump(),
    }


def structured(prompt: str, schema: dict, *, model: str, timeout: int) -> dict:
    """One schema-constrained reply for chat."""
    raw, _ = run(prompt, schema, model=model, timeout=timeout, task="chat")
    try:
        return json.loads(raw)
    except ValueError as exc:
        raise RuntimeError("Codex returned invalid JSON.") from exc


def run(
    prompt: str, schema: dict, *, model: str, timeout: int, task: str
) -> tuple[str, dict | None]:
    """Run one text-only Codex turn constrained to `schema`. Returns the raw
    final message and the turn's token usage."""
    with tempfile.TemporaryDirectory(prefix="labsync-codex-") as directory:
        root = Path(directory)
        schema_path = root / "schema.json"
        output = root / "output.json"
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
        command = [
            "codex",
            "exec",
            "--ignore-user-config",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--cd",
            directory,
            "--model",
            model,
            "--json",
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output),
            "-",
        ]
        try:
            result = subprocess.run(
                command,
                input=prompt,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "Codex CLI is missing. Install it and run codex login."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"Codex {task} timed out after {timeout}s.") from exc
        if result.returncode:
            raise RuntimeError(
                f"Codex {task} failed. Check codex login status and runtime/network "
                f"access; no {task} was saved."
            )
        events = [
            json.loads(line) for line in result.stdout.splitlines() if line.strip()
        ]
        completed = [event for event in events if event.get("type") == "turn.completed"]
        if not completed or any(
            event.get("type") in {"turn.failed", "error"} for event in events
        ):
            raise RuntimeError(f"Codex did not complete the {task}.")
        # These calls are text-only. Unexpected tool use invalidates the run.
        tool_items = {"command_execution", "file_change", "mcp_tool_call", "web_search"}
        if any(event.get("item", {}).get("type") in tool_items for event in events):
            raise RuntimeError(f"Codex used a tool during text-only {task}.")
        if not output.is_file():
            raise RuntimeError("Codex returned no structured output.")
        return output.read_text(encoding="utf-8"), completed[-1].get("usage")