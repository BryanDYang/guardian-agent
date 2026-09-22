"""Exercise the installed CLI without API keys or network access."""

import json
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

CLI = str(Path(sysconfig.get_path("scripts")) / "labsync")


@pytest.mark.parametrize("command", [[CLI], [sys.executable, "-m", "labsync"]])
def test_status(command):
    result = subprocess.run(
        [*command, "status", "--json"], capture_output=True, text=True, check=True
    )
    state = json.loads(result.stdout)
    assert state["implementation"] == "transcript_extraction"
    assert state["service"] == "local_http_available"
    assert state["meeting_processing"] == "audio_and_transcript"


def test_unknown_command_fails():
    result = subprocess.run(
        [CLI, "unknown"], capture_output=True, text=True, check=False
    )
    assert result.returncode == 2
    assert "invalid choice" in result.stderr
