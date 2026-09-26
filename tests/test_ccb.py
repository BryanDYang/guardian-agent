"""Exercise the CCB file boundary offline without importing the audio stack."""

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from labsync.ccb import import_transcript, merge_turns, transcribe
from labsync.extraction import Extraction, Transcript, Turn

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


def segments(*specs):
    return Transcript(
        project_id="p",
        meeting_id="m",
        turns=[
            Turn(
                id=f"m:segment:{index}",
                speaker=speaker,
                start_time_ms=start,
                end_time_ms=end,
                content=content,
            )
            for index, (speaker, start, end, content) in enumerate(specs)
        ],
    )


def test_merge_joins_close_same_speaker_segments():
    transcript, sources = merge_turns(
        segments(
            ("SPEAKER_00", 0, 1000, " I will send "),
            ("SPEAKER_00", 2500, 3000, "it Friday. "),
            ("SPEAKER_00", 4501, 5000, "Later."),
            ("SPEAKER_01", 5000, 6000, "Agreed."),
            ("UNKNOWN", 6000, 7000, "One."),
            ("UNKNOWN", 7000, 8000, "Two."),
        )
    )
    assert [turn.id for turn in transcript.turns] == [f"m:turn:{i}" for i in range(5)]
    first = transcript.turns[0]
    assert first.content == "I will send it Friday."
    assert (first.start_time_ms, first.end_time_ms) == (0, 3000)
    assert sources == {
        "m:turn:0": ["m:segment:0", "m:segment:1"],
        "m:turn:1": ["m:segment:2"],
        "m:turn:2": ["m:segment:3"],
        "m:turn:3": ["m:segment:4"],
        "m:turn:4": ["m:segment:5"],
    }
    Extraction.model_validate(
        {
            "summary": "",
            "decisions": [],
            "suggestions": [],
            "commitments": [
                {
                    "title": "Send it",
                    "owner": "SPEAKER_00",
                    "due_date_text": "Friday",
                    "evidence": [
                        {"transcript_id": "m:turn:0", "quote": "send it Friday."}
                    ],
                }
            ],
        }
    ).check_evidence(transcript)


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
    sidecar = tmp_path / "normalized.sources.json"
    assert json.loads(output.read_text())["turns"][0]["id"] == "m:turn:0"
    assert json.loads(sidecar.read_text()) == {
        "m:turn:0": ["m:segment:1"],
        "m:turn:1": ["m:segment:2"],
    }
    original = output.read_bytes(), sidecar.read_bytes()
    result = subprocess.run(command, capture_output=True)
    assert result.returncode == 1
    assert (output.read_bytes(), sidecar.read_bytes()) == original
    output.unlink()
    result = subprocess.run(command, capture_output=True)
    assert result.returncode == 1
    assert not output.exists()


def fake_audio_stack(tmp_path, monkeypatch, *, mlx_available=True):
    source = tmp_path / "source"
    source.mkdir()
    (source / "meeting_transcriber.py").write_text(
        f"MLX_AVAILABLE = {mlx_available}\n"
        "def load_whisper_model(name, backend):\n"
        "    assert name == 'base' and backend == 'openai'\n"
        "    return ('openai', object())\n"
        "def transcribe_audio(path, model, condition_on_previous_text):\n"
        "    assert path.is_file() and not condition_on_previous_text\n"
        "    assert model[0] != 'mlx' or model[1] == 'mlx-community/whisper-base-mlx'\n"
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
    return source, recording


@pytest.mark.parametrize(
    ("backend", "mlx_available", "label"),
    [
        ("mlx", True, "mlx-whisper"),
        ("openai", True, "openai-whisper-local"),
        ("openai", False, "openai-whisper-local"),
    ],
)
def test_audio_calls_core_functions_only(
    tmp_path, monkeypatch, backend, mlx_available, label
):
    source, recording = fake_audio_stack(
        tmp_path, monkeypatch, mlx_available=mlx_available
    )
    output = tmp_path / "output"
    normalized = transcribe(
        recording,
        source=source,
        output=output,
        project_id="p",
        meeting_id="m",
        whisper_model="base",
        backend=backend,
    )
    assert recording.read_bytes() == b"original audio"
    turn = json.loads(normalized.read_text())["turns"][0]
    assert (turn["id"], turn["speaker"]) == ("m:turn:0", "UNKNOWN")
    assert json.loads((output / "turn-sources.json").read_text()) == {
        "m:turn:0": ["m:segment:0"]
    }
    raw = json.loads((output / "ccb-transcript.json").read_text())
    assert raw["metadata"]["turn_merge_max_gap_ms"] == 1500
    assert raw["metadata"]["backend"] == label
    assert raw["metadata"]["whisper_weights"] == (
        "mlx-community/whisper-base-mlx" if label == "mlx-whisper" else None
    )
    assert raw["metadata"]["diarization"] == "not_run"
    assert len(raw["metadata"]["ccb_script_sha256"]) == 64
    with pytest.raises(ValueError, match="already exists"):
        transcribe(
            recording,
            source=source,
            output=output,
            project_id="p",
            meeting_id="m",
            whisper_model="base",
            backend=backend,
        )


def test_explicit_mlx_fails_instead_of_falling_back(tmp_path, monkeypatch):
    source, recording = fake_audio_stack(tmp_path, monkeypatch, mlx_available=False)
    with pytest.raises(RuntimeError, match="MLX-Whisper"):
        transcribe(
            recording,
            source=source,
            output=tmp_path / "output",
            project_id="p",
            meeting_id="m",
            whisper_model="base",
            backend="mlx",
        )
    assert not (tmp_path / "output").exists()


def test_unknown_backend_rejected(tmp_path, monkeypatch):
    source, recording = fake_audio_stack(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="Unknown Whisper backend"):
        transcribe(
            recording,
            source=source,
            output=tmp_path / "output",
            project_id="p",
            meeting_id="m",
            whisper_model="base",
            backend="cuda",
        )


def test_transcribe_cli_requires_explicit_backend(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "labsync",
            "transcribe",
            str(tmp_path / "input.wav"),
            "--project-id",
            "p",
            "--meeting-id",
            "m",
            "--output-dir",
            str(tmp_path / "output"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "--whisper-backend" in result.stderr


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
            backend="openai",
            diarize=True,
        )
