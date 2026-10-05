"""Voice enrollment and speaker identification
(Accounts & Voice Identity spec, Sections 9.1 and 9.2).

A user records three clips: two read passages (A, B) and one in their own words
(C). Each clip must contain enough clear speech from one voice. The voiceprint
is the average of the three clip embeddings, from the same speaker model the
diarization pipeline uses, so it can be compared with meeting speakers (D9).

In each processed meeting, the diarized speakers are matched against the
voiceprints of the project's enrolled members. A matched speaker shows the
member's name; everyone else is SPEAKER_1, SPEAKER_2, ... by first appearance.

The checks and the matching are plain Python so they run without the audio
extras. Decoding needs ffmpeg (the `audio` extra) and embedding needs pyannote
(the `diarize` extra).
"""

import math
import os
import subprocess
import sys
from array import array
from collections import Counter
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from threading import Lock

from .extraction import Transcript

SAMPLE_RATE = 16_000
CLIPS = ("A", "B", "C")

# The speaker model inside pyannote/speaker-diarization-3.1. Stored with each
# voiceprint; voiceprints from another model are never compared (FR-SPK-8).
EMBEDDING_MODEL_ID = "pyannote/wespeaker-voxceleb-resnet34-LM"

# Quality gates (NFR-MAIN-1). Provisional, from the spec's defaults: calibrate
# them on real phone recordings before relying on them.
FRAME_SECONDS = 0.03
MIN_SPEECH_SECONDS = {"A": 8.0, "B": 8.0, "C": 10.0}
MIN_TOTAL_SPEECH_SECONDS = 30.0
# A frame is speech when it is louder than this and well above the room noise.
SPEECH_FLOOR_DBFS = -45.0
SPEECH_ABOVE_NOISE_DB = 10.0
QUIET_DBFS = -40.0  # average speech level below this: too_quiet
LOUD_DBFS = -3.0  # average speech level above this: too_loud
MAX_CLIPPED_FRACTION = 0.01  # samples at full scale: too_loud
MAX_NOISE_DBFS = -35.0  # room noise louder than this: noisy
MIN_SNR_DB = 15.0  # speech this close to the room noise: noisy
# Every pair of clips must sound like the same person (cosine similarity).
CONSISTENCY_MIN = 0.65

# Speaker matching (Section 9.2). Provisional and NOT calibrated yet: run the
# identification benchmark (Section 14.3), then record the date and dataset
# here. When in doubt, a speaker stays unmatched.
MIN_CLUSTER_SPEECH_SECONDS = 5.0  # less speech than this is never matched
SPEAKER_MATCH_THRESHOLD = 0.60  # cosine similarity to the member's voiceprint
SPEAKER_MATCH_MARGIN = 0.10  # lead over the next most similar member


class VoiceUnavailable(RuntimeError):
    """This server can't decode or embed audio (missing extras or HF_TOKEN)."""


@dataclass
class ClipCheck:
    speech_seconds: float
    speech_dbfs: float | None
    noise_dbfs: float
    clipped_fraction: float
    reason: str | None  # too_short, too_quiet, too_loud, noisy, or None

    def summary(self) -> dict:
        level = self.speech_dbfs
        return {
            "speech_seconds": round(self.speech_seconds, 2),
            "speech_dbfs": None if level is None else round(level, 1),
            "noise_dbfs": round(self.noise_dbfs, 1),
            "clipped_fraction": round(self.clipped_fraction, 4),
        }


@dataclass
class Enrollment:
    """Either an embedding, or failures saying which clip to record again."""

    embedding: list[float] | None = None
    quality: dict = field(default_factory=dict)
    failures: list[dict] = field(default_factory=list)


def check_clip(samples: array, min_speech_seconds: float) -> ClipCheck:
    """Speech duration, level, noise, and clipping of 16 kHz 16-bit mono audio."""
    frame = int(SAMPLE_RATE * FRAME_SECONDS)
    energies = [
        sum(s * s for s in samples[start : start + frame]) / frame / 32768.0**2
        for start in range(0, len(samples) - frame + 1, frame)
    ]
    if not energies:
        return ClipCheck(0.0, None, -120.0, 0.0, "too_short")
    levels = [10 * math.log10(max(energy, 1e-12)) for energy in energies]
    noise = sorted(levels)[len(levels) // 10]  # the quietest tenth of the clip
    threshold = max(SPEECH_FLOOR_DBFS, noise + SPEECH_ABOVE_NOISE_DB)
    speech = [e for e, level in zip(energies, levels, strict=True) if level > threshold]
    speech_seconds = len(speech) * FRAME_SECONDS
    speech_dbfs = 10 * math.log10(sum(speech) / len(speech)) if speech else None
    clipped = sum(1 for s in samples if abs(s) >= 32700) / len(samples)

    if clipped > MAX_CLIPPED_FRACTION or (speech_dbfs or -120) > LOUD_DBFS:
        reason = "too_loud"
    elif noise > MAX_NOISE_DBFS:  # loud rooms also hide speech, so check first
        reason = "noisy"
    elif speech_dbfs is None or speech_dbfs < QUIET_DBFS:
        reason = "too_quiet"
    elif speech_dbfs - noise < MIN_SNR_DB:
        reason = "noisy"
    elif speech_seconds < min_speech_seconds:
        reason = "too_short"
    else:
        reason = None
    return ClipCheck(speech_seconds, speech_dbfs, noise, clipped, reason)


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    return [x / norm for x in vector]


def enroll(clips: dict[str, Path]) -> Enrollment:
    """Check the three clips and, if they pass, compute the voiceprint."""
    samples = {name: decode(clips[name]) for name in CLIPS}
    checks = {
        name: check_clip(samples[name], MIN_SPEECH_SECONDS[name]) for name in CLIPS
    }
    total = sum(check.speech_seconds for check in checks.values())
    quality = {
        "clips": {name: check.summary() for name, check in checks.items()},
        "total_speech_seconds": round(total, 2),
    }
    failures = [
        {"clip": name, "reason": check.reason}
        for name, check in checks.items()
        if check.reason
    ]
    if not failures and total < MIN_TOTAL_SPEECH_SECONDS:
        # A and B are fixed passages, so re-recording them can't add much speech.
        # Clip C is open-ended, so ask for more there.
        failures = [{"clip": "C", "reason": "too_short"}]
    if failures:
        return Enrollment(quality=quality, failures=failures)

    vectors = {name: normalize(embed(samples[name])) for name in CLIPS}
    pairs = {
        f"{a}-{b}": cosine(vectors[a], vectors[b])
        for i, a in enumerate(CLIPS)
        for b in CLIPS[i + 1 :]
    }
    quality["pairwise_similarity"] = {pair: round(s, 3) for pair, s in pairs.items()}
    if min(pairs.values()) < CONSISTENCY_MIN:
        # The odd one out: the clip least like the other two.
        def likeness(name):
            return sum(s for pair, s in pairs.items() if name in pair.split("-"))

        odd = min(CLIPS, key=likeness)
        return Enrollment(
            quality=quality, failures=[{"clip": odd, "reason": "inconsistent"}]
        )

    dimension = len(vectors["A"])
    average = [sum(vectors[name][i] for name in CLIPS) / 3 for i in range(dimension)]
    return Enrollment(embedding=normalize(average), quality=quality)


def decode(path: Path) -> array:
    """Any recording (the app sends AAC .m4a) as 16 kHz 16-bit mono samples."""
    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise VoiceUnavailable("install the audio extra (ffmpeg)") from exc
    result = subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-nostdin",
            "-v",
            "error",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            str(SAMPLE_RATE),
            "-f",
            "s16le",
            "-",
        ],
        capture_output=True,
        timeout=60,
    )
    if result.returncode != 0:
        # An unreadable upload is treated like a clip with no speech in it.
        return array("h")
    samples = array("h")
    samples.frombytes(result.stdout[: len(result.stdout) // 2 * 2])
    if sys.byteorder == "big":
        samples.byteswap()
    return samples


_model_lock = Lock()
_inference = None


def embed(samples: array) -> list[float]:
    """The speaker embedding of one clip (256 numbers)."""
    global _inference
    with _model_lock:
        if _inference is None:
            try:
                import torch
                from pyannote.audio import Inference, Model
            except ImportError as exc:
                raise VoiceUnavailable("install the diarize extra (pyannote)") from exc
            # pyannote 3.x checkpoints hold more than plain tensors, which torch
            # 2.6+ refuses to load by default. Allow it for this trusted model
            # only, as meeting_transcriber.py does for the diarization pipeline.
            original_load = torch.load

            def load_trusted(*args, **kwargs):
                kwargs["weights_only"] = False
                return original_load(*args, **kwargs)

            torch.load = load_trusted
            try:
                model = Model.from_pretrained(
                    EMBEDDING_MODEL_ID, use_auth_token=os.environ.get("HF_TOKEN")
                )
            except Exception as exc:
                raise VoiceUnavailable(
                    f"could not load {EMBEDDING_MODEL_ID}: {exc}"
                ) from exc
            finally:
                torch.load = original_load
            if model is None:  # pyannote returns None when access is denied
                raise VoiceUnavailable(
                    f"no access to {EMBEDDING_MODEL_ID}; check HF_TOKEN and accept "
                    "its terms on huggingface.co"
                )
            _inference = Inference(model, window="whole")
        import torch

        waveform = torch.tensor(samples, dtype=torch.float32).unsqueeze(0) / 32768.0
        vector = _inference({"waveform": waveform, "sample_rate": SAMPLE_RATE})
    return [float(x) for x in vector.reshape(-1)]


# ------------------------------------------------------- speaker identification


def speaker_order(transcript: Transcript) -> list[str]:
    """Diarizer labels in order of first appearance. UNKNOWN is not a speaker."""
    labels = dict.fromkeys(turn.speaker for turn in transcript.turns)
    return [label for label in labels if label.upper() != "UNKNOWN"]


def assign(similarity: dict[str, list[float]]) -> dict[str, int]:
    """One-to-one speaker -> member pairs with the highest total similarity,
    using only pairs at or above the threshold (Section 9.2, step 4)."""
    labels = list(similarity)

    @cache
    def best(index: int, taken: int) -> tuple[float, tuple]:
        if index == len(labels):
            return 0.0, ()
        total, pairs = best(index + 1, taken)  # this speaker stays unmatched
        for member, score in enumerate(similarity[labels[index]]):
            if score >= SPEAKER_MATCH_THRESHOLD and not taken >> member & 1:
                rest, rest_pairs = best(index + 1, taken | 1 << member)
                if rest + score > total:
                    total, pairs = rest + score, ((labels[index], member), *rest_pairs)
        return total, pairs

    return dict(best(0, 0)[1])


def match_speakers(
    labels: list[str], clusters: dict[str, dict], candidates: list[dict]
) -> dict[str, dict]:
    """Section 9.2. `labels` are diarizer tags in order of first appearance,
    `clusters` maps a tag to its centroid ("embedding") and "speech_seconds",
    and `candidates` are the enrolled members ("user_id", "name", "email",
    "embedding"). Returns each tag's display name, member, score, and method."""
    similarity = {
        label: [
            cosine(clusters[label]["embedding"], c["embedding"]) for c in candidates
        ]
        for label in labels
        if label in clusters
        and clusters[label]["speech_seconds"] >= MIN_CLUSTER_SPEECH_SECONDS
    }
    matches = {}
    for label, member in assign(similarity).items():
        others = [s for i, s in enumerate(similarity[label]) if i != member]
        if (
            similarity[label][member] - max(others, default=-1.0)
            >= SPEAKER_MATCH_MARGIN
        ):
            matches[label] = member
    # Two members with the same name would get the same label.
    names = Counter(c["name"] for c in candidates)
    speakers, unmatched = {}, 0
    for label in labels:
        scores = similarity.get(label)
        if label in matches:
            member = candidates[matches[label]]
            name = member["name"]
            speakers[label] = {
                "display": name if names[name] == 1 else f"{name} ({member['email']})",
                "user_id": member["user_id"],
                "score": round(scores[matches[label]], 3),
                "method": "voice",
            }
        else:
            unmatched += 1
            speakers[label] = {
                "display": f"SPEAKER_{unmatched}",
                "user_id": None,
                # The closest member, kept for calibrating the thresholds.
                "score": round(max(scores), 3) if scores else None,
                "method": "none",
            }
        if label in clusters:
            speakers[label]["speech_seconds"] = clusters[label]["speech_seconds"]
    return speakers


def identify(
    transcript: Transcript, diarized: dict | None, candidates: list[dict]
) -> dict:
    """Who spoke in this meeting (FR-SPK-3, FR-SPK-7, FR-SPK-8). `diarized` is
    the speakers.json written by transcription, None if diarization didn't run.
    Never raises on missing data: it records why nobody could be matched."""
    if diarized is None:
        return unidentified(transcript, "diarization_not_run")
    if diarized["embedding_model_id"] != EMBEDDING_MODEL_ID:
        return unidentified(transcript, "embedding_model_mismatch")
    if not diarized["speakers"]:
        return unidentified(transcript, "no_speaker_embeddings")
    if not candidates:
        return unidentified(transcript, "no_enrolled_members")
    return {
        "reason": None,
        "embedding_model_id": EMBEDDING_MODEL_ID,
        "candidates": len(candidates),
        "thresholds": {
            "min_cluster_speech_seconds": MIN_CLUSTER_SPEECH_SECONDS,
            "match": SPEAKER_MATCH_THRESHOLD,
            "margin": SPEAKER_MATCH_MARGIN,
            "calibrated": False,
        },
        "speakers": match_speakers(
            speaker_order(transcript), diarized["speakers"], candidates
        ),
    }


def unidentified(transcript: Transcript, reason: str) -> dict:
    """Everyone as SPEAKER_N, with the reason nobody was matched."""
    return {
        "reason": reason,
        "embedding_model_id": None,
        "candidates": 0,
        "speakers": match_speakers(speaker_order(transcript), {}, []),
    }


def relabel(transcript: Transcript, identification: dict) -> Transcript:
    """The transcript extraction reads: names and SPEAKER_N instead of diarizer
    tags (FR-SPK-9). Turn IDs are unchanged, so evidence still lines up."""
    speakers = identification["speakers"]
    turns = [
        turn.model_copy(
            update={
                "speaker": speakers.get(turn.speaker, {}).get("display", turn.speaker)
            }
        )
        for turn in transcript.turns
    ]
    return transcript.model_copy(update={"turns": turns})
