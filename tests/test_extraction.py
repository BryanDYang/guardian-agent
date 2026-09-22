"""Offline validation and process-boundary checks; no real model calls in CI."""

import json
import os
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest
from pydantic import ValidationError

from labsync.ami import load_ami
from labsync.codex_client import extract
from labsync.extraction import Extraction, Transcript

FIXTURE = Path(__file__).parent / "fixtures" / "meeting.json"


@pytest.fixture
def transcript():
    return Transcript.model_validate_json(FIXTURE.read_text())


@pytest.fixture
def prediction():
    return {
        "summary": "The team plans its first extraction test.",
        "decisions": [],
        "suggestions": [],
        "commitments": [
            {
                "title": "Prepare the transcript fixture",
                "owner": "Sam",
                "due_date_text": "Friday",
                "evidence": [
                    {
                        "transcript_id": "t2",
                        "quote": "I will prepare the transcript fixture by Friday.",
                    }
                ],
            }
        ],
    }


def test_valid_evidence(transcript, prediction):
    Extraction.model_validate(prediction).check_evidence(transcript)


@pytest.mark.parametrize(
    "field,value", [("transcript_id", "missing"), ("quote", "I completed it")]
)
def test_rejects_invented_evidence(transcript, prediction, field, value):
    prediction["commitments"][0]["evidence"][0][field] = value
    with pytest.raises(ValueError, match="Evidence does not match"):
        Extraction.model_validate(prediction).check_evidence(transcript)


def test_unknown_owner(transcript, prediction):
    prediction["commitments"][0]["owner"] = "Invented Person"
    with pytest.raises(ValueError, match="Unknown commitment owner"):
        Extraction.model_validate(prediction).check_evidence(transcript)


def test_invented_deadline(transcript, prediction):
    prediction["commitments"][0]["due_date_text"] = "2026-09-25"
    with pytest.raises(ValueError, match="Deadline text"):
        Extraction.model_validate(prediction).check_evidence(transcript)


@pytest.mark.parametrize("invalid", ["duplicate", "time", "type"])
def test_invalid_transcript(transcript, invalid):
    data = transcript.model_dump()
    if invalid == "duplicate":
        data["turns"][1]["id"] = "t1"
    elif invalid == "time":
        data["turns"][1]["end_time_ms"] = 0
    else:
        data["turns"][0]["start_time_ms"] = "0"
    with pytest.raises(ValidationError):
        Transcript.model_validate(data)


@pytest.fixture
def fake_codex(tmp_path, monkeypatch, prediction):
    executable = tmp_path / "codex"
    executable.write_text(
        f"#!{sys.executable}\n"
        "import json, os, pathlib, sys\n"
        "if '--version' in sys.argv:\n"
        "    print('codex-test-double'); sys.exit(0)\n"
        "assert '--ignore-user-config' in sys.argv\n"
        "assert sys.argv[sys.argv.index('--sandbox') + 1] == 'read-only'\n"
        "prompt = sys.stdin.read()\n"
        "assert 'TRANSCRIPT:' in prompt\n"
        "mode = os.environ.get('FAKE_CODEX_MODE', 'success')\n"
        "if mode == 'failure': sys.exit(1)\n"
        "path = pathlib.Path(sys.argv[sys.argv.index('--output-last-message') + 1])\n"
        f"prediction = json.loads({json.dumps(prediction)!r})\n"
        "if mode == 'citation':\n"
        "    prediction['commitments'][0]['evidence'][0]['quote'] = 'invented'\n"
        "path.write_text('not json' if mode == 'invalid' else json.dumps(prediction))\n"
        "if mode == 'tool':\n"
        "    print(json.dumps({'type':'item.completed',"
        "'item':{'type':'command_execution'}}))\n"
        "if mode != 'incomplete':\n"
        "    print(json.dumps({'type':'turn.completed',"
        "'usage':{'input_tokens':10,'output_tokens':20}}))\n"
    )
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])


def test_cli_extract_process_boundary(fake_codex, tmp_path):
    output = tmp_path / "result.json"
    command = [
        sys.executable,
        "-m",
        "labsync",
        "extract",
        str(FIXTURE),
        "--model",
        "test-model",
        "--output",
        str(output),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
    result = json.loads(output.read_text())
    assert result["extraction"]["commitments"][0]["owner"] == "Sam"
    assert result["usage"]["input_tokens"] == 10
    assert result["codex_version"] == "codex-test-double"
    original = output.read_bytes()
    rerun = subprocess.run(command, capture_output=True, text=True)
    assert rerun.returncode == 1
    assert "already exists" in rerun.stderr
    assert output.read_bytes() == original


@pytest.mark.parametrize(
    "mode", ["failure", "invalid", "incomplete", "citation", "tool"]
)
def test_failed_run_does_not_save_output(fake_codex, tmp_path, monkeypatch, mode):
    monkeypatch.setenv("FAKE_CODEX_MODE", mode)
    output = tmp_path / "result.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "labsync",
            "extract",
            str(FIXTURE),
            "--model",
            "test-model",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert not output.exists()
    assert "Traceback" not in result.stderr


def test_timeout_is_actionable(transcript, monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("codex", 1)

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(RuntimeError, match="timed out"):
        extract(transcript, model="test-model", timeout=1)


def test_ami_import_uses_word_ranges_and_ignores_labels(tmp_path):
    archive = tmp_path / "ami.zip"
    root = '<root xmlns:nite="http://nite.sourceforge.net/">'
    with ZipFile(archive, "w") as output:
        output.writestr(
            "words/TS3005a.A.words.xml",
            root
            + '<w nite:id="w0">I</w><w nite:id="w1">agree</w>'
            + '<w nite:id="w2">.</w></root>',
        )
        output.writestr(
            "segments/TS3005a.A.segments.xml",
            root
            + '<segment nite:id="s1" transcriber_start="1.25" transcriber_end="2.5">'
            + '<nite:child href="TS3005a.A.words.xml#id(w0)..id(w2)"/>'
            + "</segment></root>",
        )
        output.writestr("abstractive/TS3005a.abssumm.xml", "gold must never be read")
    result = load_ami(archive, "TS3005a")
    assert result.turns[0].content == "I agree ."
    assert result.turns[0].start_time_ms == 1250
    assert result.turns[0].speaker == "A"
    with pytest.raises(ValueError, match="No AMI segments"):
        load_ami(archive, "TS3005b")


def test_cli_invalid_archive_is_actionable(tmp_path):
    archive = tmp_path / "broken.zip"
    archive.write_text("not a zip")
    output = tmp_path / "meeting.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "labsync",
            "import-ami",
            str(archive),
            "--meeting",
            "TS3005a",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "zip" in result.stderr
    assert "Traceback" not in result.stderr
    assert not output.exists()
