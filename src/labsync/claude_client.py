"""Small structured-output client for the Anthropic Messages API."""

import json
import os
import time
from hashlib import sha256
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .extraction import PROMPT_VERSION, Extraction, Transcript, build_prompt

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
TOOL = "record_extraction"
MAX_TOKENS = 8192


def extract(transcript: Transcript, *, model: str, timeout: int = 180) -> dict:
    """Run one independent meeting; the key is read from ANTHROPIC_API_KEY only."""
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("Set ANTHROPIC_API_KEY to use the Claude provider.")
    prompt = build_prompt(transcript)
    payload = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        # The shared instructions forbid tools. This forced tool is only the API's
        # schema-constrained output channel, so name it explicitly.
        "system": f"Return the requested JSON as the input to the {TOOL} tool.",
        "messages": [{"role": "user", "content": prompt}],
        "tools": [
            {
                "name": TOOL,
                "description": "Record the meeting extraction.",
                "input_schema": Extraction.model_json_schema(),
            }
        ],
        "tool_choice": {"type": "tool", "name": TOOL},
    }
    request = Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": API_VERSION,
        },
    )
    started = time.monotonic()
    try:
        with urlopen(request, timeout=timeout) as response:
            message = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(describe(exc)) from exc
    except (TimeoutError, URLError) as exc:
        if isinstance(exc, TimeoutError) or isinstance(exc.reason, TimeoutError):
            raise RuntimeError(
                f"Claude extraction timed out after {timeout}s."
            ) from exc
        raise RuntimeError(
            "Could not reach the Anthropic API. Check network access; "
            "no extraction was saved."
        ) from exc
    if message.get("stop_reason") == "max_tokens":
        raise RuntimeError("Claude output was truncated; no extraction was saved.")
    calls = [
        block
        for block in message.get("content", [])
        if block.get("type") == "tool_use" and block.get("name") == TOOL
    ]
    if len(calls) != 1:
        raise RuntimeError("Claude returned no structured output.")
    extraction = Extraction.model_validate(calls[0]["input"])
    extraction.check_evidence(transcript)
    return {
        "project_id": transcript.project_id,
        "meeting_id": transcript.meeting_id,
        "provider": "anthropic-api",
        "model_requested": model,
        "model_used": message.get("model"),
        "api_version": API_VERSION,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": sha256(prompt.encode("utf-8")).hexdigest(),
        "transcript_sha256": sha256(
            transcript.model_dump_json().encode("utf-8")
        ).hexdigest(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "usage": message.get("usage"),
        "extraction": extraction.model_dump(),
    }


def describe(error: HTTPError) -> str:
    try:
        detail = json.load(error)["error"]["message"]
    except (OSError, ValueError, KeyError, TypeError):
        detail = error.reason
    hint = " Check ANTHROPIC_API_KEY." if error.code in {401, 403} else ""
    return f"Claude extraction failed (HTTP {error.code}): {detail.rstrip('.')}.{hint}"
