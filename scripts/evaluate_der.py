"""Diarization error rate (DER) on the diarizers-community/ami `ihm` test split.

Runs the same pyannote pipeline the app uses (speaker-diarization-3.1, no speaker
count hints) on each meeting and scores it against the dataset's reference turns.

Usage (from the repo root, HF_TOKEN set in .env):

    uv run --locked --env-file .env --extra diarize --with pyarrow \
        python scripts/evaluate_der.py --output artifacts/der/ami-ihm-test-run1

Writes run.json, per_meeting.csv, summary.json and ref/ + hyp/ RTTM files.
"""

import argparse
import csv
import glob
import hashlib
import importlib.metadata
import io
import json
import os
import platform
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import soundfile as sf
import torch
from pyannote.core import Annotation, Segment, Timeline
from pyannote.metrics.diarization import DiarizationErrorRate

MODEL = "pyannote/speaker-diarization-3.1"
COMPONENTS = ["missed detection", "false alarm", "confusion", "total"]


def meetings(data_dir: Path, only: set[str] | None):
    """Yield (meeting_id, waveform, sample_rate, reference) one meeting at a time."""
    for path in sorted(glob.glob(str(data_dir / "test-*.parquet"))):
        table = pq.ParquetFile(path)
        for group in range(table.num_row_groups):
            for row in table.read_row_group(group).to_pylist():
                meeting_id = Path(row["audio"]["path"]).name.split(".")[0]
                if only and meeting_id not in only:
                    continue
                audio, rate = sf.read(
                    io.BytesIO(row["audio"]["bytes"]), dtype="float32"
                )
                if audio.ndim > 1:
                    audio = audio.mean(axis=1)
                reference = Annotation(uri=meeting_id)
                for start, end, speaker in zip(
                    row["timestamps_start"], row["timestamps_end"], row["speakers"]
                ):
                    reference[Segment(start, end), len(reference)] = speaker
                yield meeting_id, audio, rate, reference


def load_pipeline(device: str):
    from pyannote.audio import Pipeline

    # pyannote 3.x checkpoints hold more than plain tensors, which torch 2.6+
    # refuses by default. Allow it for this trusted model only, as the app does
    # (meeting_transcriber.py, src/labsync/voice.py).
    original_load = torch.load

    def load_trusted(*args, **kwargs):
        kwargs["weights_only"] = False
        return original_load(*args, **kwargs)

    torch.load = load_trusted
    try:
        pipeline = Pipeline.from_pretrained(
            MODEL, use_auth_token=os.environ["HF_TOKEN"]
        )
    finally:
        torch.load = original_load
    if pipeline is None:  # pyannote returns None when access is denied
        raise RuntimeError(f"no access to {MODEL}; check HF_TOKEN and model terms")
    pipeline.to(torch.device(device))
    return pipeline


def write_rttm(annotation: Annotation, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        annotation.write_rttm(f)


def read_rttm(path: Path, uri: str) -> Annotation:
    annotation = Annotation(uri=uri)
    for line in path.read_text().splitlines():
        parts = line.split()
        start, duration, speaker = float(parts[3]), float(parts[4]), parts[7]
        annotation[Segment(start, start + duration), len(annotation)] = speaker
    return annotation


def default_device() -> str:
    # Same order as the app's transcriber.
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--data-dir", type=Path, default=Path("contexts/datasets/ami-diarization/ihm")
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--meetings", nargs="*", help="Only these meeting IDs")
    parser.add_argument("--collars", type=float, nargs="+", default=[0.0, 0.25])
    parser.add_argument("--device", default=default_device())
    parser.add_argument(
        "--oracle-speakers",
        action="store_true",
        help="Pass the true speaker count (not what the app does; report separately)",
    )
    parser.add_argument(
        "--resume", action="store_true", help="Reuse hyp RTTMs already in --output"
    )
    args = parser.parse_args()

    if args.output.exists() and not args.resume:
        parser.error(f"{args.output} exists; use a new directory or --resume")
    previous = args.output / "run.json"
    old_run, old_seconds = None, {}
    if args.resume and previous.exists():
        old_run = json.loads(previous.read_text())
        if old_run["oracle_speakers"] != args.oracle_speakers:
            parser.error("--resume must use the same --oracle-speakers setting")
        old_csv = args.output / "per_meeting.csv"
        if old_csv.exists():
            with old_csv.open() as f:
                old_seconds = {
                    r["meeting"]: r["diarization_seconds"] for r in csv.DictReader(f)
                }
    args.output.mkdir(parents=True, exist_ok=True)

    files = sorted(glob.glob(str(args.data_dir / "test-*.parquet")))
    if not files:
        parser.error(f"no test-*.parquet files in {args.data_dir}")
    run = {
        "started_at": datetime.now(UTC).isoformat(),
        "model": MODEL,
        "device": args.device,
        "oracle_speakers": args.oracle_speakers,
        "collars": args.collars,
        "skip_overlap": False,
        "data_files": {
            Path(f).name: hashlib.sha256(Path(f).read_bytes()).hexdigest()
            for f in files
        },
        "git_revision": subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip(),
        "platform": platform.platform(),
        "versions": {
            name: importlib.metadata.version(name)
            for name in ["torch", "pyannote.audio", "pyannote.metrics", "pyannote.core"]
        },
    }
    if old_run:
        # Keep the original run record; note when it was rescored.
        run = {**old_run, "rescored_at": run["started_at"]}
    (args.output / "run.json").write_text(json.dumps(run, indent=2) + "\n")

    pipeline = None
    metrics = {
        c: DiarizationErrorRate(collar=c, skip_overlap=False) for c in args.collars
    }
    rows = []
    for meeting_id, audio, rate, reference in meetings(
        args.data_dir, set(args.meetings) if args.meetings else None
    ):
        duration = len(audio) / rate
        hyp_path = args.output / "hyp" / f"{meeting_id}.rttm"
        write_rttm(reference, args.output / "ref" / f"{meeting_id}.rttm")

        seconds = None
        if args.resume and hyp_path.exists():
            hypothesis = read_rttm(hyp_path, meeting_id)
        else:
            pipeline = pipeline or load_pipeline(args.device)
            kwargs = (
                {"num_speakers": len(reference.labels())}
                if args.oracle_speakers
                else {}
            )
            started = time.perf_counter()
            hypothesis = pipeline(
                {
                    "waveform": torch.from_numpy(audio[np.newaxis, :]),
                    "sample_rate": rate,
                },
                **kwargs,
            )
            seconds = time.perf_counter() - started
            hypothesis.uri = meeting_id
            write_rttm(hypothesis, hyp_path)

        row = {
            "meeting": meeting_id,
            "series": meeting_id[:6],
            "type": "natural" if meeting_id.startswith("EN") else "scenario",
            "audio_minutes": round(duration / 60, 2),
            "ref_speakers": len(reference.labels()),
            "hyp_speakers": len(hypothesis.labels()),
            "diarization_seconds": (
                round(seconds, 1)
                if seconds is not None
                else old_seconds.get(meeting_id, "")
            ),
        }
        uem = Timeline([Segment(0, duration)])
        for collar, metric in metrics.items():
            detail = metric(reference, hypothesis, uem=uem, detailed=True)
            row[f"der_c{collar}"] = round(detail["diarization error rate"], 4)
            for name in COMPONENTS:
                row[f"{name.replace(' ', '_')}_c{collar}"] = round(detail[name], 2)
        rows.append(row)
        print(
            f"{meeting_id}: DER={row[f'der_c{args.collars[0]}']:.3f} "
            f"speakers {row['hyp_speakers']}/{row['ref_speakers']} "
            f"({'cached' if seconds is None else row['diarization_seconds']} s)",
            flush=True,
        )

    with (args.output / "per_meeting.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    def pooled(subset: list[dict], collar: float) -> dict:
        # Corpus DER = total error seconds / total reference speech seconds.
        sums = {
            n: sum(r[f"{n.replace(' ', '_')}_c{collar}"] for r in subset)
            for n in COMPONENTS
        }
        total = sums.pop("total")
        return {
            "meetings": len(subset),
            "der": round(sum(sums.values()) / total, 4),
            **{f"{n}_rate": round(v / total, 4) for n, v in sums.items()},
            "reference_speech_seconds": round(total, 1),
            "actual_speakers": sum(r["ref_speakers"] for r in subset),
            "predicted_speakers": sum(r["hyp_speakers"] for r in subset),
            "exact_count_meetings": sum(
                r["hyp_speakers"] == r["ref_speakers"] for r in subset
            ),
        }

    groups = {"all": rows}
    # meeting=<id> rows are single meetings, not pooled groups; don't sum them.
    for key in ["type", "series", "meeting"]:
        for value in sorted({r[key] for r in rows}):
            groups[f"{key}={value}"] = [r for r in rows if r[key] == value]
    summary = {
        f"collar={c}": {name: pooled(subset, c) for name, subset in groups.items()}
        for c in args.collars
    }
    summary["speaker_count_exact"] = (
        f"{sum(r['hyp_speakers'] == r['ref_speakers'] for r in rows)}/{len(rows)}"
    )
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (args.output / "summary.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["collar", "group", "meetings", "der", "missed_rate", "false_alarm_rate"]
            + ["confusion_rate", "reference_speech_seconds"]
            + ["actual_speakers", "predicted_speakers", "exact_count_meetings"]
        )
        for c in args.collars:
            for name, s in summary[f"collar={c}"].items():
                writer.writerow(
                    [c, name, s["meetings"], s["der"], s["missed detection_rate"]]
                    + [s["false alarm_rate"], s["confusion_rate"]]
                    + [s["reference_speech_seconds"]]
                    + [s["actual_speakers"], s["predicted_speakers"]]
                    + [s["exact_count_meetings"]]
                )

    print("\n| Group | Meetings | DER | Missed | False alarm | Confusion |")
    print("| --- | --- | --- | --- | --- | --- |")
    for name, s in summary[f"collar={args.collars[0]}"].items():
        rates = [
            s[f"{n}_rate"] for n in ["missed detection", "false alarm", "confusion"]
        ]
        cells = " | ".join(f"{v:.3f}" for v in [s["der"], *rates])
        print(f"| {name} | {s['meetings']} | {cells} |")
    print(f"Speaker count exact: {summary['speaker_count_exact']}")


if __name__ == "__main__":
    main()
