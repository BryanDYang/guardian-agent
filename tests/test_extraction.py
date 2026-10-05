"""Offline validation and process-boundary checks; no real model calls in CI."""

import copy
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from zipfile import ZipFile

import pytest
from pydantic import ValidationError

from labsync import claude_client
from labsync.ami import load_ami
from labsync.codex_client import extract
from labsync.extraction import Extraction, Transcript, build_prompt
from labsync.providers import setup_error

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


def test_repair_moves_quote_to_its_only_turn(transcript, prediction):
    prediction["commitments"][0]["evidence"][0]["transcript_id"] = "t1"
    extraction, repairs = Extraction.model_validate(prediction).repair_evidence(
        transcript
    )
    extraction.check_evidence(transcript)
    assert extraction.commitments[0].evidence[0].transcript_id == "t2"
    assert repairs == ["commitments[0]: moved quote from t1 to t2"]


def test_repair_drops_unverifiable_evidence(transcript, prediction):
    agreed = {"transcript_id": "t1", "quote": "We agree to use the public AMI"}
    prediction["decisions"] = [
        {
            "statement": "Use AMI transcripts",
            "evidence": [agreed, {"transcript_id": "t1", "quote": "invented"}],
        },
        {
            "statement": "Across turns",
            "evidence": [{"transcript_id": "t2", "quote": "test. I will prepare"}],
        },
    ]
    extraction, repairs = Extraction.model_validate(prediction).repair_evidence(
        transcript
    )
    extraction.check_evidence(transcript)
    assert [item.statement for item in extraction.decisions] == ["Use AMI transcripts"]
    assert extraction.decisions[0].evidence[0].model_dump() == agreed
    assert len(extraction.decisions[0].evidence) == 1
    assert repairs == [
        "decisions[0]: dropped quote 'invented'",
        "decisions[1]: dropped quote 'test. I will prepare'",
        "decisions[1]: dropped item with no verifiable evidence",
    ]


def test_repair_clears_a_reworded_deadline(transcript, prediction):
    prediction["commitments"][0]["due_date_text"] = "by this Friday"
    extraction, repairs = Extraction.model_validate(prediction).repair_evidence(
        transcript
    )
    extraction.check_evidence(transcript)
    assert extraction.commitments[0].due_date_text is None
    assert extraction.commitments[0].title == prediction["commitments"][0]["title"]
    assert repairs == ["commitments[0]: cleared unquoted deadline 'by this Friday'"]


def test_repair_leaves_valid_extraction_unchanged(transcript, prediction):
    original = Extraction.model_validate(prediction)
    extraction, repairs = original.repair_evidence(transcript)
    assert extraction == original
    assert repairs == []


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
        "if mode == 'owner':\n"
        "    prediction['commitments'][0]['owner'] = 'Invented Person'\n"
        "if mode == 'citation':\n"
        "    prediction['commitments'][0]['evidence'][0]['transcript_id'] = 't1'\n"
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
    monkeypatch.delenv("LABSYNC_PROVIDER", raising=False)


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


def test_cli_reports_evidence_repairs(fake_codex, tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_CODEX_MODE", "citation")
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
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Repaired evidence: commitments[0]: moved quote from t1 to t2" in (
        result.stdout
    )
    saved = json.loads(output.read_text())
    assert saved["extraction"]["commitments"][0]["evidence"][0]["transcript_id"] == (
        "t2"
    )
    assert saved["evidence_repairs"] == ["commitments[0]: moved quote from t1 to t2"]


@pytest.mark.parametrize("mode", ["failure", "invalid", "incomplete", "owner", "tool"])
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
    rejected = tmp_path / "extraction-rejected.json"
    assert rejected.exists() == (mode in {"owner", "invalid"})
    if mode == "owner":
        assert "Unknown commitment owner" in result.stderr
        saved = json.loads(rejected.read_text())
        assert saved["commitments"][0]["owner"] == "Invented Person"
    elif mode == "invalid":
        assert rejected.read_text() == "not json"


def test_timeout_is_actionable(transcript, monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("codex", 1)

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(RuntimeError, match="timed out"):
        extract(transcript, model="test-model", timeout=1)


@pytest.fixture
def fake_claude(monkeypatch, prediction):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    state = {
        "requests": [],
        "reply": {
            "model": "claude-test-double",
            "stop_reason": "tool_use",
            "usage": {"input_tokens": 10, "output_tokens": 20},
            "content": [
                {
                    "type": "tool_use",
                    "name": claude_client.TOOL,
                    "input": copy.deepcopy(prediction),
                }
            ],
        },
    }

    def urlopen(request, timeout):
        assert request.get_header("X-api-key") == "test-key"
        state["requests"].append(json.loads(request.data))
        return io.BytesIO(json.dumps(state["reply"]).encode())

    monkeypatch.setattr(claude_client, "urlopen", urlopen)
    return state


def test_claude_extract(fake_claude, transcript):
    result = claude_client.extract(transcript, model="test-model", timeout=1)
    assert result["provider"] == "anthropic-api"
    assert result["model_used"] == "claude-test-double"
    assert result["usage"]["output_tokens"] == 20
    assert result["extraction"]["commitments"][0]["owner"] == "Sam"
    request = fake_claude["requests"][0]
    assert request["messages"][0]["content"] == build_prompt(transcript)
    assert request["tool_choice"] == {"type": "tool", "name": claude_client.TOOL}


@pytest.mark.parametrize("key", ["$parameter", "$PARAMETER_NAME"])
def test_claude_unwraps_placeholder_envelope(fake_claude, transcript, prediction, key):
    fake_claude["reply"]["content"][0]["input"] = {key: prediction}
    result = claude_client.extract(transcript, model="test-model", timeout=1)
    assert result["extraction"] == Extraction.model_validate(prediction).model_dump()
    assert result["evidence_repairs"] == []


def test_claude_repairs_evidence(fake_claude, transcript):
    tool_input = fake_claude["reply"]["content"][0]["input"]
    tool_input["commitments"][0]["evidence"][0]["transcript_id"] = "wrong"
    result = claude_client.extract(transcript, model="test-model", timeout=1)
    evidence = result["extraction"]["commitments"][0]["evidence"][0]
    assert evidence["transcript_id"] == "t2"
    assert result["evidence_repairs"] == [
        "commitments[0]: moved quote from wrong to t2"
    ]


@pytest.mark.parametrize(
    "mode,error",
    [
        ("owner", "Unknown commitment owner"),
        ("invalid", "validation error"),
        ("truncated", "truncated"),
        ("text", "no structured output"),
    ],
)
def test_claude_rejects_unusable_reply(fake_claude, transcript, mode, error):
    reply = fake_claude["reply"]
    tool_input = reply["content"][0]["input"]
    if mode == "owner":
        tool_input["commitments"][0]["owner"] = "Invented Person"
    elif mode == "invalid":
        del tool_input["summary"]
    elif mode == "truncated":
        reply["stop_reason"] = "max_tokens"
    else:
        reply["content"] = [{"type": "text", "text": "{}"}]
    with pytest.raises((ValueError, RuntimeError), match=error):
        claude_client.extract(transcript, model="test-model", timeout=1)


@pytest.mark.parametrize("mode", ["owner", "invalid"])
def test_claude_keeps_rejected_output(fake_claude, transcript, tmp_path, mode):
    tool_input = fake_claude["reply"]["content"][0]["input"]
    if mode == "owner":
        tool_input["commitments"][0]["owner"] = "Invented Person"
    else:
        del tool_input["summary"]
    rejected = tmp_path / "attempt-1" / "extraction-rejected.json"
    with pytest.raises(ValueError):
        claude_client.extract(
            transcript, model="test-model", timeout=1, rejected=rejected
        )
    assert json.loads(rejected.read_text()) == tool_input


def test_claude_success_writes_no_rejected_output(fake_claude, transcript, tmp_path):
    rejected = tmp_path / "extraction-rejected.json"
    claude_client.extract(transcript, model="test-model", timeout=1, rejected=rejected)
    assert not rejected.exists()


@pytest.mark.parametrize(
    "failure,error",
    [
        (
            HTTPError(
                claude_client.API_URL,
                401,
                "Unauthorized",
                {},
                io.BytesIO(b'{"error": {"message": "invalid x-api-key."}}'),
            ),
            r"HTTP 401\): invalid x-api-key\. Check ANTHROPIC_API_KEY",
        ),
        (TimeoutError(), "timed out"),
        (URLError(TimeoutError()), "timed out"),
        (URLError("no route"), "Could not reach"),
    ],
)
def test_claude_request_errors_are_actionable(
    fake_claude, transcript, monkeypatch, failure, error
):
    def fail(request, timeout):
        raise failure

    monkeypatch.setattr(claude_client, "urlopen", fail)
    with pytest.raises(RuntimeError, match=error):
        claude_client.extract(transcript, model="test-model", timeout=1)


def run_cli(*args, **env):
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"ANTHROPIC_API_KEY", "LABSYNC_PROVIDER"}
    }
    environment.update(env)
    return subprocess.run(
        [sys.executable, "-m", "labsync", *args],
        capture_output=True,
        text=True,
        env=environment,
    )


def test_provider_from_environment_needs_credentials(tmp_path):
    output = tmp_path / "result.json"
    result = run_cli(
        "extract", str(FIXTURE), "--output", str(output), LABSYNC_PROVIDER="claude"
    )
    assert result.returncode == 1
    assert "ANTHROPIC_API_KEY" in result.stderr
    assert "Traceback" not in result.stderr
    assert not output.exists()
    served = run_cli(
        "serve",
        "--provider",
        "claude",
        "--whisper-backend",
        "openai",
        SUPABASE_URL="http://127.0.0.1:54321",
    )
    assert served.returncode == 1
    assert "ANTHROPIC_API_KEY" in served.stderr


def test_unknown_provider_is_rejected(tmp_path):
    result = run_cli(
        "extract",
        str(FIXTURE),
        "--output",
        str(tmp_path / "result.json"),
        LABSYNC_PROVIDER="gemini",
    )
    assert result.returncode == 2
    assert "unknown provider 'gemini'" in result.stderr


def test_codex_setup_error_names_both_options(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))
    assert "LABSYNC_PROVIDER=claude" in setup_error("codex")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    assert setup_error("claude") is None


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
