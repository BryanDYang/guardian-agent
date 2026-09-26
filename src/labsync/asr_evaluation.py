"""Evaluate the actual CCB acoustic path on a frozen, series-disjoint AMI pilot."""

import argparse
import json
import platform
import random
import re
import subprocess
import time
import wave
from datetime import UTC, datetime
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

from .ccb import transcribe

PROTOCOL = "ami-word-midpoint-lower-punctuation-v1"


def file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        result = sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def normalize(text: str) -> str:
    # Keep fillers and numbers as spoken/written; no output-dependent corrections.
    text = text.lower().replace("’", "'").replace("'", "")
    return " ".join(re.sub(r"[^\w\s]", " ", text).split())


def validate_manifest(manifest: dict) -> None:
    series_splits = {}
    ids = set()
    for meeting in manifest["meetings"]:
        if meeting["split"] not in {"development", "validation", "test"}:
            raise ValueError("Unknown split")
        if meeting["meeting_id"] in ids:
            raise ValueError("Duplicate meeting ID")
        ids.add(meeting["meeting_id"])
        series = meeting["series"]
        if series in series_splits and series_splits[series] != meeting["split"]:
            raise ValueError("Meeting series crosses splits")
        series_splits[series] = meeting["split"]
        previous_end = 0
        for start, end in meeting["windows"]:
            if start < previous_end or end <= start:
                raise ValueError("Invalid or overlapping audio windows")
            previous_end = end
    if not ids:
        raise ValueError("Empty manifest")


def reference_words(archive: Path, meeting: str, start: float, end: float) -> list:
    words = []
    with ZipFile(archive) as source:
        names = sorted(
            n
            for n in source.namelist()
            if re.fullmatch(rf"words/{re.escape(meeting)}\.[A-D]\.words.xml", n)
        )
        if len(names) != 4:
            raise ValueError(f"Expected four AMI speaker word files for {meeting}")
        for name in names:
            root = ElementTree.fromstring(source.read(name))
            for index, node in enumerate(root):
                if node.tag != "w" or node.get("punc") == "true":
                    continue
                if node.get("starttime") is None or node.get("endtime") is None:
                    continue
                begin, finish = float(node.get("starttime")), float(node.get("endtime"))
                text = (node.text or "").strip()
                if text and start <= (begin + finish) / 2 < end:
                    words.append(
                        {
                            "start": begin,
                            "end": finish,
                            "text": text,
                            "speaker": name.split(".")[1],
                            "index": index,
                        }
                    )
    return sorted(words, key=lambda w: (w["start"], w["speaker"], w["index"]))


def prepare(manifest_path: Path, output: Path) -> None:
    manifest = json.loads(manifest_path.read_text())
    validate_manifest(manifest)
    archive = Path(manifest["annotation_archive"])
    if output.exists():
        raise ValueError("Prepared output already exists")
    # Fail before creating partial data when a source recording is unavailable.
    for meeting in manifest["meetings"]:
        with wave.open(meeting["audio_path"], "rb") as audio:
            if max(end for _, end in meeting["windows"]) > (
                audio.getnframes() / audio.getframerate()
            ):
                raise ValueError("Audio window exceeds recording duration")
    output.mkdir(parents=True)
    dataset = {
        "protocol": PROTOCOL,
        "manifest": manifest,
        "manifest_sha256": file_hash(manifest_path),
        "annotation_sha256": file_hash(archive),
        "clips": [],
    }
    for meeting in manifest["meetings"]:
        audio_path = Path(meeting["audio_path"])
        audio_hash = file_hash(audio_path)
        for start, end in meeting["windows"]:
            clip_id = f"{meeting['meeting_id']}-{start}-{end}"
            words = reference_words(archive, meeting["meeting_id"], start, end)
            reference = " ".join(word["text"] for word in words)
            if not normalize(reference):
                raise ValueError(f"Empty reference for {clip_id}")
            with wave.open(str(audio_path), "rb") as audio:
                with wave.open(str(output / f"{clip_id}.wav"), "wb") as clip:
                    clip.setparams(audio.getparams())
                    audio.setpos(round(start * audio.getframerate()))
                    clip.writeframes(
                        audio.readframes(round((end - start) * audio.getframerate()))
                    )
            dataset["clips"].append(
                {
                    "id": clip_id,
                    "meeting_id": meeting["meeting_id"],
                    "series": meeting["series"],
                    "split": meeting["split"],
                    "audio": f"{clip_id}.wav",
                    "duration_seconds": end - start,
                    "source_audio_sha256": audio_hash,
                    "audio_sha256": file_hash(output / f"{clip_id}.wav"),
                    "reference": reference,
                    "reference_words": words,
                }
            )
    write_json(output / "dataset.json", dataset)
    print(f"Prepared {len(dataset['clips'])} clips", flush=True)


def run(dataset_path: Path, output: Path, model: str, source: Path) -> None:
    import numpy as np
    import torch
    import whisper

    dataset = json.loads(dataset_path.read_text())
    if dataset["protocol"] != PROTOCOL:
        raise ValueError("Unknown dataset protocol")
    output.mkdir(parents=True, exist_ok=False)
    # Thread count changes performance, not the decoding configuration.
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.set_num_threads(4)
    started = time.monotonic()
    whisper.load_model(model)  # Separate first-time download from clip timings.
    setup_seconds = time.monotonic() - started
    metadata = {
        "protocol": PROTOCOL,
        "dataset_sha256": file_hash(dataset_path),
        "model": model,
        "model_weight_url": whisper._MODELS[model],
        "ccb_script_sha256": file_hash(source / "meeting_transcriber.py"),
        "runner_sha256": file_hash(Path(__file__)),
        "bridge_sha256": file_hash(Path(__file__).with_name("ccb.py")),
        "started_at": datetime.now(UTC).isoformat(),
        "platform": platform.platform(),
        "versions": {
            name: version(name) for name in ["openai-whisper", "torch", "jiwer"]
        },
        "threads": 4,
        "seed": 42,
        "setup_seconds": setup_seconds,
        "settings": {
            "backend": "openai",
            "language": "en",
            "word_timestamps": True,
            "condition_on_previous_text": False,
            "initial_prompt": None,
            "diarization": False,
            "llm_cleanup": False,
        },
    }
    write_json(output / "run.json", metadata)
    for clip in dataset["clips"]:
        audio = dataset_path.parent / clip["audio"]
        if file_hash(audio) != clip["audio_sha256"]:
            raise ValueError(f"Changed audio: {clip['id']}")
        record = {"id": clip["id"], "audio_sha256": clip["audio_sha256"]}
        started = time.monotonic()
        try:
            normalized = transcribe(
                audio,
                source=source,
                output=output / clip["id"],
                project_id=f"ami-{clip['series']}",
                meeting_id=clip["id"],
                whisper_model=model,
                backend="openai",
            )
            transcript = json.loads(normalized.read_text())
            record["hypothesis"] = " ".join(
                turn["content"] for turn in transcript["turns"]
            )
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"
        record["wall_seconds"] = time.monotonic() - started
        write_json(output / f"{clip['id']}.json", record)
        print(f"{clip['id']}: {record.get('error', 'saved')}", flush=True)


def word_counts(reference: str, hypothesis: str) -> dict:
    import jiwer

    result = jiwer.process_words(normalize(reference), normalize(hypothesis))
    return {
        "substitutions": result.substitutions,
        "deletions": result.deletions,
        "insertions": result.insertions,
        "hits": result.hits,
        "reference_words": result.hits + result.substitutions + result.deletions,
    }


def score(dataset_path: Path, directory: Path) -> dict:
    import jiwer

    dataset = json.loads(dataset_path.read_text())
    run_metadata = json.loads((directory / "run.json").read_text())
    if run_metadata["dataset_sha256"] != file_hash(dataset_path):
        raise ValueError("Dataset differs from inference run")
    rows = []
    for clip in dataset["clips"]:
        path = directory / f"{clip['id']}.json"
        record = json.loads(path.read_text()) if path.exists() else {"error": "missing"}
        if path.exists() and (
            record["id"] != clip["id"] or record["audio_sha256"] != clip["audio_sha256"]
        ):
            raise ValueError("Prediction/audio identity mismatch")
        failed = bool(record.get("error"))
        hypothesis = "" if failed else record["hypothesis"]
        counts = word_counts(clip["reference"], hypothesis)
        alignment = jiwer.process_words(
            normalize(clip["reference"]), normalize(hypothesis)
        )
        rows.append(
            {
                "id": clip["id"],
                "meeting_id": clip["meeting_id"],
                "split": clip["split"],
                "duration_seconds": clip["duration_seconds"],
                "failed": failed,
                "error": record.get("error"),
                "wall_seconds": record.get("wall_seconds"),
                "reference": clip["reference"],
                "hypothesis": hypothesis,
                "counts": counts,
                "wer": (
                    counts["substitutions"] + counts["deletions"] + counts["insertions"]
                )
                / counts["reference_words"]
                if counts["reference_words"]
                else None,
                "alignment": jiwer.visualize_alignment(alignment),
            }
        )
    groups = {}
    for split in ["development", "validation", "test"]:
        selected = [r for r in rows if r["split"] == split]
        if not selected:
            continue
        totals = {
            key: sum(r["counts"][key] for r in selected)
            for key in selected[0]["counts"]
        }
        errors = totals["substitutions"] + totals["deletions"] + totals["insertions"]
        complete_timing = all(r["wall_seconds"] is not None for r in selected)
        seconds = sum(r["duration_seconds"] for r in selected)
        groups[split] = {
            **totals,
            "errors": errors,
            "wer": errors / totals["reference_words"]
            if totals["reference_words"]
            else None,
            "clips": len(selected),
            "meetings": len({r["meeting_id"] for r in selected}),
            "audio_seconds": seconds,
            "failures": sum(r["failed"] for r in selected),
            "real_time_factor": sum(r["wall_seconds"] for r in selected) / seconds
            if complete_timing
            else None,
        }
    return {
        "protocol": PROTOCOL,
        "jiwer_version": version("jiwer"),
        "scorer_sha256": file_hash(Path(__file__)),
        "run": run_metadata,
        "splits": groups,
        "clips": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "run", "score"])
    parser.add_argument(
        "--manifest", type=Path, default=Path("tests/fixtures/asr/manifest.json")
    )
    parser.add_argument(
        "--dataset", type=Path, default=Path("artifacts/asr/prepared/dataset.json")
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", choices=["tiny", "base"], default="tiny")
    parser.add_argument(
        "--source", type=Path, default=Path("contexts/meeting_transcriber-master")
    )
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            prepare(args.manifest, args.output)
        elif args.command == "run":
            run(args.dataset, args.output, args.model, args.source)
        else:
            report = score(args.dataset, args.output)
            write_json(args.output / "scores.json", report)
            print(json.dumps(report["splits"], indent=2))
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        parser.exit(1, f"asr-evaluation: {exc}\n")


if __name__ == "__main__":
    main()
