"""CLI entry point for status and transcript-first extraction."""

import argparse
import json
import os
from importlib.metadata import version
from pathlib import Path
from subprocess import SubprocessError
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from .providers import DEFAULT_MODELS, default_provider, setup_error


def add_provider_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--provider",
        default=default_provider(),
        help="Extraction provider: codex or claude (default: $LABSYNC_PROVIDER "
        "or codex)",
    )
    parser.add_argument(
        "--model", help="Model for the provider (default: the provider's default)"
    )


def add_whisper_backend_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--whisper-backend",
        required=True,
        choices=["mlx", "openai"],
        help="mlx: local MLX-Whisper (Apple Silicon only); "
        "openai: local open-source OpenAI Whisper",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="labsync", description="Meeting follow-through assistant"
    )
    parser.add_argument("--version", action="version", version=version("ai-capstone"))
    commands = parser.add_subparsers(dest="command", required=True)
    status = commands.add_parser(
        "status", help="Show implementation and service status"
    )
    status.add_argument(
        "--json", action="store_true", help="Output machine-readable JSON"
    )
    extraction = commands.add_parser(
        "extract", help="Extract a transcript using Codex or Claude"
    )
    extraction.add_argument("transcript", type=Path)
    add_provider_options(extraction)
    extraction.add_argument("--output", required=True, type=Path)
    extraction.add_argument("--timeout", type=int, default=180)
    ami = commands.add_parser(
        "import-ami", help="Import AMI manual transcript segments"
    )
    ami.add_argument("archive", type=Path)
    ami.add_argument("--meeting", required=True)
    ami.add_argument("--output", type=Path, required=True)
    ccb = commands.add_parser("import-ccb", help="Import CCB's transcript.json")
    ccb.add_argument("transcript", type=Path)
    ccb.add_argument("--project-id", required=True)
    ccb.add_argument("--meeting-id", required=True)
    ccb.add_argument("--output", type=Path, required=True)
    audio = commands.add_parser(
        "transcribe", help="Transcribe audio with CCB and local Whisper"
    )
    audio.add_argument("recording", type=Path)
    audio.add_argument(
        "--source", type=Path, default=Path("contexts/meeting_transcriber-master")
    )
    audio.add_argument("--project-id", required=True)
    audio.add_argument("--meeting-id", required=True)
    audio.add_argument("--output-dir", type=Path, required=True)
    audio.add_argument(
        "--whisper-model",
        choices=["tiny", "base", "small", "medium", "large", "turbo"],
        default="base",
    )
    add_whisper_backend_option(audio)
    audio.add_argument(
        "--diarize", action="store_true", help="Requires pyannote and HF_TOKEN"
    )
    server = commands.add_parser("serve", help="Start the local UI backend")
    server.add_argument("--port", type=int, default=8000)
    server.add_argument("--storage", type=Path, default=Path("artifacts/server"))
    server.add_argument(
        "--source", type=Path, default=Path("contexts/meeting_transcriber-master")
    )
    add_provider_options(server)
    server.add_argument(
        "--whisper-model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large", "turbo"],
    )
    add_whisper_backend_option(server)
    server.add_argument("--diarize", action="store_true")
    args = parser.parse_args(argv)
    if args.command in {"extract", "serve"} and args.provider not in DEFAULT_MODELS:
        parser.error(
            f"unknown provider {args.provider!r}; choose from "
            + ", ".join(DEFAULT_MODELS)
        )
    if args.command == "serve":
        token = os.environ.get("API_SECRET_KEY")
        if not token:
            parser.exit(1, "Set API_SECRET_KEY before starting the server\n")
        if problem := setup_error(args.provider):
            parser.exit(1, problem + "\n")
        try:
            import uvicorn

            from .server import create_app
        except ImportError:
            parser.exit(1, "Install the server extra: uv sync --extra server\n")
        uvicorn.run(
            create_app(
                args.storage,
                args.source,
                provider=args.provider,
                model=args.model,
                whisper_model=args.whisper_model,
                whisper_backend=args.whisper_backend,
                diarize=args.diarize,
                token=token,
            ),
            host="127.0.0.1",
            port=args.port,
        )
        return 0
    if args.command in {"transcribe", "import-ccb"}:
        from .ccb import import_transcript, merge_turns, transcribe

        try:
            if args.command == "transcribe":
                output = transcribe(
                    args.recording,
                    source=args.source,
                    output=args.output_dir,
                    project_id=args.project_id,
                    meeting_id=args.meeting_id,
                    whisper_model=args.whisper_model,
                    diarize=args.diarize,
                    backend=args.whisper_backend,
                )
                print(f"Saved raw and normalized transcripts to {output.parent}")
                if not args.diarize:
                    print("Diarization was not run; speaker labels remain UNKNOWN.")
            else:
                segments = import_transcript(
                    args.transcript,
                    project_id=args.project_id,
                    meeting_id=args.meeting_id,
                )
                transcript, sources = merge_turns(segments)
                sidecar = args.output.with_name(args.output.stem + ".sources.json")
                if sidecar.exists():
                    raise ValueError(f"Output already exists: {sidecar}")
                args.output.parent.mkdir(parents=True, exist_ok=True)
                with args.output.open("x", encoding="utf-8") as destination:
                    destination.write(transcript.model_dump_json(indent=2) + "\n")
                with sidecar.open("x", encoding="utf-8") as destination:
                    destination.write(json.dumps(sources, indent=2) + "\n")
                print(
                    f"Imported {len(segments.turns)} segments as "
                    f"{len(transcript.turns)} turns to {args.output}"
                )
        except (OSError, ValueError, RuntimeError, ImportError, SubprocessError) as exc:
            parser.exit(1, f"labsync: {exc}\n")
        return 0
    if args.command == "import-ami":
        from .ami import load_ami

        try:
            transcript = load_ami(args.archive, args.meeting)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as destination:
                destination.write(transcript.model_dump_json(indent=2) + "\n")
        except (OSError, ValueError, KeyError, BadZipFile, ParseError) as exc:
            parser.exit(1, f"labsync: {exc}\n")
        print(f"Imported {len(transcript.turns)} turns to {args.output}")
        return 0
    if args.command == "extract":
        from .extraction import Transcript
        from .providers import extract

        try:
            if args.output.exists():
                raise ValueError(f"Output already exists: {args.output}")
            transcript = Transcript.model_validate_json(
                args.transcript.read_text(encoding="utf-8")
            )
            result = extract(
                transcript,
                provider=args.provider,
                model=args.model,
                timeout=args.timeout,
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as destination:
                destination.write(json.dumps(result, indent=2) + "\n")
        except (OSError, ValueError, RuntimeError, SubprocessError) as exc:
            parser.exit(1, f"labsync: {exc}\n")
        print(f"Saved extraction to {args.output}")
        return 0
    state = {
        "version": version("ai-capstone"),
        "implementation": "transcript_extraction",
        "service": "local_http_available",
        "meeting_processing": "audio_and_transcript",
    }
    if args.json:
        print(json.dumps(state))
    else:
        print(f"LabSync {state['version']} - transcript extraction via Codex")
        print("Run labsync serve for the local UI backend.")
    return 0
