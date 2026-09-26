"""Small structured-output client using the supported Codex CLI login path."""

import json
import subprocess
import tempfile
import time
from hashlib import sha256
from pathlib import Path

from .extraction import PROMPT_VERSION, Extraction, Transcript, build_prompt


def extract(transcript: Transcript, *, model: str, timeout: int = 180) -> dict:
    """Run one independent meeting; never read or copy Codex credentials."""
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    prompt = build_prompt(transcript)
    with tempfile.TemporaryDirectory(prefix="labsync-codex-") as directory:
        root = Path(directory)
        schema = root / "schema.json"
        output = root / "extraction.json"
        schema.write_text(json.dumps(Extraction.model_json_schema()), encoding="utf-8")
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
            str(schema),
            "--output-last-message",
            str(output),
            "-",
        ]
        started = time.monotonic()
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
            raise RuntimeError(f"Codex extraction timed out after {timeout}s.") from exc
        if result.returncode:
            raise RuntimeError(
                "Codex extraction failed. Check codex login status and runtime/network "
                "access; no extraction was saved."
            )
        events = [
            json.loads(line) for line in result.stdout.splitlines() if line.strip()
        ]
        completed = [event for event in events if event.get("type") == "turn.completed"]
        if not completed or any(
            event.get("type") in {"turn.failed", "error"} for event in events
        ):
            raise RuntimeError("Codex did not complete the extraction.")
        # The extraction path is text-only. Unexpected tool use invalidates the run.
        tool_items = {"command_execution", "file_change", "mcp_tool_call", "web_search"}
        if any(event.get("item", {}).get("type") in tool_items for event in events):
            raise RuntimeError("Codex used a tool during text-only extraction.")
        if not output.is_file():
            raise RuntimeError("Codex returned no structured output.")
        extraction = Extraction.model_validate_json(output.read_text(encoding="utf-8"))
        extraction.check_evidence(transcript)
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
            "usage": completed[-1].get("usage"),
            "extraction": extraction.model_dump(),
        }
