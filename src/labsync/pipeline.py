"""One processing attempt; persistence and worker ownership belong to the caller."""

import json
import sys

from . import voice
from .extraction import Extraction, Transcript


def run_pipeline(record, directory, work, source, settings, identify, stage, run):
    stage("transcribing")
    with (directory / "processing.log").open("a") as log:
        command = [
            sys.executable,
            "-m",
            "labsync",
            "transcribe",
            str(directory / record["filename"]),
            "--source",
            str(source),
            "--project-id",
            record["project"],
            "--meeting-id",
            record["id"],
            "--whisper-model",
            settings["whisper_model"],
            "--whisper-backend",
            settings["whisper_backend"],
            "--output-dir",
            str(work),
        ]
        command.append("--diarize" if settings["diarize"] else "--no-diarize")
        run(command, check=True, stdout=log, stderr=log, timeout=7200)
        transcript = Transcript.model_validate_json(
            (work / "transcript.json").read_text()
        )
        identification = identify(record["project"], transcript, work)
        named = voice.relabel(transcript, identification)
        labeled = work / "labeled-transcript.json"
        labeled.write_text(named.model_dump_json(indent=2) + "\n")
        stage("extracting")
        run(
            [
                sys.executable,
                "-m",
                "labsync",
                "extract",
                str(labeled),
                "--provider",
                settings["provider"],
                "--model",
                settings["model"],
                "--output",
                str(work / "extraction.json"),
                "--timeout",
                "300",
            ],
            check=True,
            stdout=log,
            stderr=log,
            timeout=330,
        )
        result = json.loads((work / "extraction.json").read_text())
        Extraction.model_validate(result["extraction"]).check_evidence(named)
        path = work / "ccb-transcript.json"
        metadata = (
            json.loads(path.read_text()).get("metadata") if path.is_file() else {}
        )
        return (
            transcript,
            named,
            result,
            identification,
            (metadata if isinstance(metadata, dict) else {}),
        )
