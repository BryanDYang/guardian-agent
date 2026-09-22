"""Exercise the CCB file boundary offline without importing the audio stack."""

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from labsync.ccb import import_transcript, transcribe
from labsync.extraction import Extraction

ROOT = Path(__file__).parents[1]


@pytest.fixture
def ccb_file(tmp_path):
    path = tmp_path / "ccb.json"
    path.write_text(
        json.dumps(
            {
                "metadata": {"language": "en"},
                "segments": [
                    {"start": 0, "end": 0.5, "text": " ", "speaker": "UNKNOWN"},
                    {
                        "start": 1.234,
                        "end": 4.567,
                        "text": " I will send it Friday. ",
                        "speaker": "SPEAKER_00",
                    },
                    {"start": 5, "end": 6, "text": "Thank you."},
                ],
            }
        )
    )
    return path


def test_import_preserves_evidence_and_source_indices(ccb_file):
    transcript = import_transcript(ccb_file, project_id="p", meeting_id="m")
    assert len(transcript.turns) == 2
    first, second = transcript.turns
    assert first.id == "m:segment:1"
    assert first.start_time_ms == 1234
    assert first.end_time_ms == 4567
    assert first.content == " I will send it Friday. "
    assert first.speaker == "SPEAKER_00"
    assert second.speaker == "UNKNOWN"


@pytest.mark.parametrize("value", [-1, "1", True, float("nan"), float("inf")])
def test_invalid_times_rejected(ccb_file, value):
    data = json.loads(ccb_file.read_text())
    data["segments"][1]["start"] = value
    ccb_file.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="invalid start/end"):
        import_transcript(ccb_file, project_id="p", meeting_id="m")


def test_unknown_speaker_is_not_a_task_owner(ccb_file):
    transcript = import_transcript(ccb_file, project_id="p", meeting_id="m")
    extraction = Extraction.model_validate(
        {
            "summary": "",
            "decisions": [],
            "suggestions": [],
            "commitments": [
                {
                    "title": "Send it",
                    "owner": "UNKNOWN",
                    "due_date_text": None,
                    "evidence": [
                        {
                            "transcript_id": "m:segment:1",
                            "quote": "I will send it Friday.",
                        }
                    ],
                }
            ],
        }
    )
    with pytest.raises(ValueError, match="Unknown commitment owner"):
        extraction.check_evidence(transcript)


def test_import_cli_and_overwrite_protection(ccb_file, tmp_path):
    output = tmp_path / "normalized.json"
    command = [
        sys.executable,
        "-m",
        "labsync",
        "import-ccb",
        str(ccb_file),
        "--project-id",
        "p",
        "--meeting-id",
        "m",
        "--output",
        str(output),
    ]
    subprocess.run(command, check=True, capture_output=True)
    original = output.read_bytes()
    result = subprocess.run(command, capture_output=True)
    assert result.returncode == 1
    assert output.read_bytes() == original


def test_audio_calls_core_functions_only(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "meeting_transcriber.py").write_text(
        "def load_whisper_model(name, backend):\n"
        "    assert name == 'tiny' and backend == 'openai'\n"
        "    return object()\n"
        "def transcribe_audio(path, model, condition_on_previous_text):\n"
        "    assert path.is_file() and not condition_on_previous_text\n"
        "    return {'language': 'en', 'timestamped': ["
        "{'start': 0.1, 'end': 2.5, 'text': 'An example.'}]}\n"
        "def process_recording(*args):\n"
        "    raise AssertionError('Personal workflow must not be called')\n"
    )
    recording = tmp_path / "original.wav"
    recording.write_bytes(b"original audio")
    binary = tmp_path / "binary"
    binary.touch()
    monkeypatch.setitem(
        sys.modules,
        "imageio_ffmpeg",
        SimpleNamespace(get_ffmpeg_exe=lambda: str(binary)),
    )
    monkeypatch.setitem(sys.modules, "whisper", SimpleNamespace())
    monkeypatch.setattr("labsync.ccb.shutil.which", lambda name: None)
    monkeypatch.setattr(
        "labsync.ccb.subprocess.run",
        lambda command, **kw: Path(command[-1]).write_bytes(b"wav"),
    )
    output = tmp_path / "output"
    normalized = transcribe(
        recording,
        source=source,
        output=output,
        project_id="p",
        meeting_id="m",
        whisper_model="tiny",
    )
    assert recording.read_bytes() == b"original audio"
    assert json.loads(normalized.read_text())["turns"][0]["speaker"] == "UNKNOWN"
    raw = json.loads((output / "ccb-transcript.json").read_text())
    assert raw["metadata"]["diarization"] == "not_run"
    assert len(raw["metadata"]["ccb_script_sha256"]) == 64
    with pytest.raises(ValueError, match="already exists"):
        transcribe(
            recording,
            source=source,
            output=output,
            project_id="p",
            meeting_id="m",
            whisper_model="tiny",
        )


def test_diarization_missing_token_fails_before_model_load(tmp_path, monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    recording = tmp_path / "input.wav"
    recording.touch()
    source = tmp_path / "source"
    source.mkdir()
    (source / "meeting_transcriber.py").touch()
    with pytest.raises(ValueError, match="HF_TOKEN"):
        transcribe(
            recording,
            source=source,
            output=tmp_path / "output",
            project_id="p",
            meeting_id="m",
            whisper_model="tiny",
            diarize=True,
        )
