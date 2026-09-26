"""Bridge CCB's on-disk transcript format and local acoustic functions."""

import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from hashlib import sha256
from pathlib import Path

from .extraction import Transcript, Turn

BACKENDS = {"mlx": "mlx-whisper", "openai": "openai-whisper-local"}

MLX_WEIGHTS = {
    "tiny": "mlx-community/whisper-tiny-mlx",
    "base": "mlx-community/whisper-base-mlx",
    "small": "mlx-community/whisper-small-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    "large": "mlx-community/whisper-large-v3-mlx",
    "turbo": "mlx-community/whisper-large-v3-turbo",
}
MERGE_GAP_MS = 1500


def import_transcript(path: Path, *, project_id: str, meeting_id: str) -> Transcript:
    """Preserve raw text, timing, and labels; do not infer speaker identities."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("segments"), list):
        raise ValueError("CCB transcript must contain a segments array")
    turns = []
    for index, segment in enumerate(data["segments"]):
        if not isinstance(segment, dict):
            raise ValueError(f"Segment {index} must be an object")
        text = segment.get("text")
        if not isinstance(text, str):
            raise ValueError(f"Segment {index} must contain text")
        times = [segment.get("start"), segment.get("end")]
        if (
            any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
                for value in times
            )
            or times[1] < times[0]
        ):
            raise ValueError(f"Segment {index} has invalid start/end seconds")
        if not text.strip():
            continue
        speaker = segment.get("speaker")
        if speaker is None or speaker == "":
            speaker = "UNKNOWN"
        if not isinstance(speaker, str) or not speaker.strip():
            raise ValueError(f"Segment {index} has an invalid speaker label")
        turns.append(
            Turn(
                id=f"{meeting_id}:segment:{index}",
                speaker=speaker,
                start_time_ms=round(times[0] * 1000),
                end_time_ms=round(times[1] * 1000),
                content=text,
            )
        )
    return Transcript(project_id=project_id, meeting_id=meeting_id, turns=turns)


def merge_turns(
    transcript: Transcript, max_gap_ms: int = MERGE_GAP_MS
) -> tuple[Transcript, dict[str, list[str]]]:
    """Join consecutive same-speaker segments separated by <= max_gap_ms.

    UNKNOWN segments are never joined: the label may cover several people.
    Returns the merged transcript and a map of new turn ID -> source segment IDs.
    """
    merged: list[dict] = []
    sources: list[list[str]] = []
    for turn in transcript.turns:
        prev = merged[-1] if merged else None
        if (
            prev
            and prev["speaker"] == turn.speaker
            and turn.speaker.upper() != "UNKNOWN"
            and turn.start_time_ms - prev["end_time_ms"] <= max_gap_ms
        ):
            prev["end_time_ms"] = max(prev["end_time_ms"], turn.end_time_ms)
            prev["content"] += " " + turn.content.strip()
            sources[-1].append(turn.id)
        else:
            merged.append(turn.model_dump() | {"content": turn.content.strip()})
            sources.append([turn.id])
    for i, m in enumerate(merged):
        m["id"] = f"{transcript.meeting_id}:turn:{i}"
    result = transcript.model_copy(update={"turns": [Turn(**m) for m in merged]})
    return (
        Transcript.model_validate(result.model_dump()),
        {m["id"]: s for m, s in zip(merged, sources)},
    )


def transcribe(
    recording: Path,
    *,
    source: Path,
    output: Path,
    project_id: str,
    meeting_id: str,
    whisper_model: str,
    backend: str,
    diarize: bool = False,
) -> Path:
    """Call acoustic functions only, avoiding the personal-workflow entry point."""
    recording = recording.resolve()
    source = source.resolve()
    script = source / "meeting_transcriber.py"
    if not recording.is_file():
        raise ValueError(f"Recording not found: {recording}")
    if not script.is_file():
        raise ValueError(f"CCB source not found: {script}")
    if output.exists():
        raise ValueError(f"Output directory already exists: {output}")
    if not project_id.strip() or not meeting_id.strip():
        raise ValueError("Project and meeting IDs must not be blank")
    if backend not in BACKENDS:
        raise ValueError(
            f"Unknown Whisper backend: {backend}; choose from " + ", ".join(BACKENDS)
        )
    if backend == "mlx" and whisper_model not in MLX_WEIGHTS:
        raise ValueError(f"No MLX-Whisper weights for model {whisper_model!r}")
    if diarize and not os.environ.get("HF_TOKEN"):
        raise ValueError("Diarization requires HF_TOKEN and accepted model access")
    try:
        import imageio_ffmpeg
        import whisper  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("Install audio dependencies: uv sync --extra audio") from exc

    # Upstream expects sibling imports. Its __main__ block is never executed.
    sys.path.insert(0, str(source))
    try:
        spec = importlib.util.spec_from_file_location("ccb_meeting_transcriber", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    if diarize and not module.DIARIZATION_AVAILABLE:
        raise RuntimeError("Install CCB's pyannote dependencies before using --diarize")
    if backend == "mlx" and not module.MLX_AVAILABLE:
        raise RuntimeError(
            "MLX-Whisper requires an Apple Silicon Mac and the audio extra; "
            "use --whisper-backend openai instead"
        )
    weights = MLX_WEIGHTS[whisper_model] if backend == "mlx" else None

    original_path = os.environ.get("PATH", "")
    with tempfile.TemporaryDirectory(prefix="labsync-audio-") as directory:
        temp = Path(directory)
        ffmpeg = shutil.which("ffmpeg") or imageio_ffmpeg.get_ffmpeg_exe()
        # Whisper invokes ffmpeg by name; keep the fallback local to this run.
        (temp / "ffmpeg").symlink_to(ffmpeg)
        os.environ["PATH"] = str(temp) + os.pathsep + original_path
        try:
            wav = temp / "audio.wav"
            subprocess.run(
                [
                    ffmpeg,
                    "-nostdin",
                    "-v",
                    "error",
                    "-i",
                    str(recording),
                    "-vn",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    str(wav),
                ],
                check=True,
                capture_output=True,
                timeout=300,
            )
            model = (
                ("mlx", weights)
                if backend == "mlx"
                else module.load_whisper_model(whisper_model, "openai")
            )
            result = module.transcribe_audio(
                wav, model, condition_on_previous_text=False
            )
            if diarize:
                pipeline = module.load_diarization_pipeline(os.environ["HF_TOKEN"])
                annotation, _ = module.diarize_audio(wav, pipeline)
                result = module.align_transcription_with_diarization(result, annotation)
        finally:
            os.environ["PATH"] = original_path

    metadata = {
        "source_file": str(recording),
        "source_audio_sha256": sha256(recording.read_bytes()).hexdigest(),
        "ccb_script_sha256": sha256(script.read_bytes()).hexdigest(),
        "whisper_model": whisper_model,
        "backend": BACKENDS[backend],
        "whisper_weights": weights,
        "language": result.get("language", "unknown"),
        "diarization": "pyannote" if diarize else "not_run",
        "llm_cleanup": "not_run",
        "turn_merge_max_gap_ms": MERGE_GAP_MS,
    }
    # Normalize and validate before publishing either artifact.
    raw = {"metadata": metadata, "segments": result.get("timestamped", [])}
    with tempfile.TemporaryDirectory(prefix="labsync-import-") as directory:
        raw_path = Path(directory) / "ccb-transcript.json"
        raw_path.write_text(json.dumps(raw), encoding="utf-8")
        transcript, sources = merge_turns(
            import_transcript(raw_path, project_id=project_id, meeting_id=meeting_id)
        )
    output.mkdir(parents=True, exist_ok=False)
    (output / "ccb-transcript.json").write_text(
        json.dumps(raw, indent=2) + "\n", encoding="utf-8"
    )
    (output / "turn-sources.json").write_text(
        json.dumps(sources, indent=2) + "\n", encoding="utf-8"
    )
    normalized = output / "transcript.json"
    normalized.write_text(transcript.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return normalized
