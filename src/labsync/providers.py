"""Selectable extraction providers sharing one prompt and output contract."""

import os
import shutil

from .extraction import Transcript

DEFAULT_MODELS = {"codex": "gpt-5.6-sol", "claude": "claude-sonnet-4-5"}


def default_provider() -> str:
    return os.environ.get("LABSYNC_PROVIDER") or "codex"


def setup_error(provider: str) -> str | None:
    """Explain missing credentials before any meeting is accepted."""
    if provider == "codex" and not shutil.which("codex"):
        return (
            "Codex CLI is missing. Install it and run codex login, "
            "or set LABSYNC_PROVIDER=claude with ANTHROPIC_API_KEY."
        )
    if provider == "claude" and not os.environ.get("ANTHROPIC_API_KEY"):
        return "Set ANTHROPIC_API_KEY (for example in .env) to use the Claude provider."
    return None


def extract(
    transcript: Transcript, *, provider: str, model: str | None = None, timeout: int
) -> dict:
    if provider == "codex":
        from .codex_client import extract as run
    elif provider == "claude":
        from .claude_client import extract as run
    else:
        raise ValueError(f"Unknown extraction provider: {provider}")
    return run(transcript, model=model or DEFAULT_MODELS[provider], timeout=timeout)
