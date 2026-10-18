#!/usr/bin/env python3
"""
Meeting Transcriber - Transcribe audio/video recordings with speaker identification.

Usage:
    python meeting_transcriber.py recording.mp4              # Transcribe with interactive speaker ID
    python meeting_transcriber.py recording.mp4 --auto       # Skip prompts, use SPEAKER_XX labels
    python meeting_transcriber.py recording.mp4 --match-calendar  # Use calendar for speaker names
    python meeting_transcriber.py recording.mp4 --dont-trash-recording  # Keep original file (default: moves to Trash)

Speaker Management:
    python meeting_transcriber.py --list-speakers            # List known voice profiles
    python meeting_transcriber.py recording.mp4 --enroll "Name"  # Enroll specific speaker
    python meeting_transcriber.py recording.mp4 --speakers "SPEAKER_00=Name1,SPEAKER_01=Name2"

Relabeling (fix speaker names after transcription):
    python meeting_transcriber.py --relabel "meetings/..." --speakers "SPEAKER_08=John Smith"
    python meeting_transcriber.py --relabel "meetings/..." --speakers "..." --enroll-relabeled

Transcription Quality:
    python meeting_transcriber.py recording.mp4 --no-clean-transcript  # Skip LLM post-processing
    python meeting_transcriber.py recording.mp4 --condition-on-previous-text  # Revert to old Whisper behavior

Backend (Apple Silicon Macs get 3-4x speedup):
    python meeting_transcriber.py recording.mp4              # Auto-detect (MLX on Apple Silicon)
    python meeting_transcriber.py recording.mp4 --backend mlx    # Force MLX
    python meeting_transcriber.py recording.mp4 --backend openai # Force OpenAI Whisper
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
import warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Some hosts (e.g. Claude Code) export these as empty strings. load_dotenv()
    # treats a present-but-empty var as already set, so drop the blanks first.
    for _key in ("ANTHROPIC_API_KEY", "HF_TOKEN"):
        if not os.environ.get(_key):
            os.environ.pop(_key, None)
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, rely on shell environment

# Fix threading conflict between numba (used by pyannote) and MLX OpenMP
# Must be set before importing torch/numba
os.environ.setdefault('NUMBA_THREADING_LAYER', 'workqueue')
os.environ.setdefault('OMP_NUM_THREADS', '1')

# Suppress third-party library warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torchaudio")
warnings.filterwarnings("ignore", category=UserWarning, module="pyannote")
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")

import numpy as np
import whisper
from scipy.spatial.distance import cosine as cosine_distance
from tqdm import tqdm

# Local modules
from contacts import (
    load_known_contacts,
    resolve_email_to_name,
    build_email_to_profile_index,
)

# Optional diarization imports
try:
    import torch
    _original_torch_load = torch.load
    def _patched_torch_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return _original_torch_load(*args, **kwargs)
    torch.load = _patched_torch_load

    from pyannote.audio import Pipeline as DiarizationPipeline
    DIARIZATION_AVAILABLE = True
except ImportError:
    DIARIZATION_AVAILABLE = False

# Optional MLX-Whisper for Apple Silicon acceleration
MLX_AVAILABLE = False
try:
    import platform
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        import mlx_whisper
        MLX_AVAILABLE = True
except ImportError:
    pass

# Default paths
SCRIPT_DIR = Path(__file__).parent.resolve()
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / 'meetings'
SPEAKER_PROFILES_FILE = DEFAULT_OUTPUT_DIR / 'speaker_profiles.json'

# Whisper model mapping for MLX
MLX_MODEL_MAP = {
    'tiny': 'mlx-community/whisper-tiny',
    'base': 'mlx-community/whisper-base',
    'small': 'mlx-community/whisper-small',
    'medium': 'mlx-community/whisper-medium',
    'large': 'mlx-community/whisper-large-v3-mlx',
    'turbo': 'mlx-community/whisper-large-v3-turbo',
}

# Supported file formats
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.webm', '.avi', '.mkv'}
AUDIO_EXTENSIONS = {'.mp3', '.m4a', '.wav', '.aac', '.flac', '.ogg'}


# ============================================================================
# Argument Parsing
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description='Transcribe meeting recordings with speaker identification.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Main input
    parser.add_argument('recording', nargs='?', help='Path to audio/video recording')

    # Transcription options
    parser.add_argument('--model', default='turbo',
                        choices=['tiny', 'base', 'small', 'medium', 'large', 'turbo'],
                        help='Whisper model size (default: turbo)')
    parser.add_argument('--backend', default='auto', choices=['auto', 'mlx', 'openai'],
                        help='Transcription backend (default: auto)')

    # Speaker identification
    parser.add_argument('--auto', action='store_true', default=True,
                        help='Skip interactive prompts (default: enabled)')
    parser.add_argument('--interactive', action='store_true',
                        help='Enable interactive speaker identification prompts')
    parser.add_argument('--speakers', metavar='MAPPING',
                        help='Non-interactive speaker mapping: "SPEAKER_00=Name1,SPEAKER_01=Name2". '
                             'Optionally attach an email to enroll on the profile: '
                             '"SPEAKER_00=Pat Lee <plee@example.org>"')
    parser.add_argument('--match-calendar', action='store_true',
                        help='Query calendar for meeting attendees')
    parser.add_argument('--min-speakers', type=int,
                        help='Minimum number of speakers expected')
    parser.add_argument('--max-speakers', type=int,
                        help='Maximum number of speakers expected')

    # Speaker management
    parser.add_argument('--list-speakers', action='store_true',
                        help='List all known speaker profiles')
    parser.add_argument('--enroll', metavar='NAME',
                        help='Enroll a specific speaker from the recording')
    parser.add_argument('--relabel', metavar='MEETING_DIR',
                        help='Relabel speakers in an existing transcript (use with --speakers)')
    parser.add_argument('--enroll-relabeled', action='store_true',
                        help='Enroll speaker profiles for relabeled speakers (requires source recording)')

    # Transcription tuning
    parser.add_argument('--condition-on-previous-text', action='store_true',
                        help='Enable conditioning on previous text (default: off for better formatting)')
    parser.add_argument('--no-clean-transcript', action='store_true',
                        help='Skip LLM post-processing (default: cleaning enabled)')
    parser.add_argument('--clean-transcript', action='store_true',
                        help='(deprecated, now default) Run LLM post-processing')

    # Output options
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT_DIR,
                        help=f'Output directory (default: {DEFAULT_OUTPUT_DIR})')
    parser.add_argument('--dont-trash-recording', action='store_true',
                        help='Keep the original recording file (default: moves to Trash after transcription)')
    parser.add_argument('--min-duration', type=int, default=300,
                        help='Minimum recording duration in seconds (default: 300 = 5 min)')

    # Batch processing
    parser.add_argument('--process-all', action='store_true',
                        help='Scan and process recordings from all sources (Ecamm, Zoom, Voice Memos)')
    parser.add_argument('--process-ecamm', action='store_true',
                        help='Process recordings from Ecamm Live')
    parser.add_argument('--process-zoom', action='store_true',
                        help='Process recordings from Zoom')
    parser.add_argument('--process-voicememos', action='store_true',
                        help='Process recordings from Voice Memos')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be processed without doing it')

    # Audio samples for unidentified speakers
    parser.add_argument('--save-samples', action='store_true', default=True,
                        help='Save audio clips for unidentified speakers (default: enabled)')
    parser.add_argument('--no-save-samples', action='store_false', dest='save_samples',
                        help='Disable saving audio samples for unidentified speakers')
    parser.add_argument('--cleanup-expired-samples', action='store_true',
                        help='Clean up audio samples older than 90 days')

    # Authentication
    parser.add_argument('--hf-token', help='HuggingFace token (or set HF_TOKEN env var)')

    return parser.parse_args()


# ============================================================================
# Audio/Video Processing
# ============================================================================

def is_video_file(path: Path) -> bool:
    """Check if file is a video format."""
    return path.suffix.lower() in VIDEO_EXTENSIONS


def is_audio_file(path: Path) -> bool:
    """Check if file is an audio format."""
    return path.suffix.lower() in AUDIO_EXTENSIONS


def get_media_duration(file_path: Path) -> float:
    """Get duration of audio/video file in seconds using ffprobe."""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(file_path)
        ], capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return 0.0


def extract_audio_from_video(video_path: Path, output_path: Path = None) -> Path:
    """Extract audio track from video file using ffmpeg.

    Args:
        video_path: Path to video file
        output_path: Optional output path (default: same name with .wav extension)

    Returns:
        Path to extracted audio file
    """
    if output_path is None:
        output_path = video_path.with_suffix('.wav')

    print(f"Extracting audio from video: {video_path.name}")

    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', str(video_path),
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # PCM 16-bit
            '-ar', '16000',  # 16kHz sample rate
            '-ac', '1',  # Mono
            str(output_path)
        ], check=True, capture_output=True)
        print(f"  Extracted to: {output_path.name}")
        return output_path
    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found. Install with: brew install ffmpeg")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg failed: {e.stderr.decode()}")


def convert_to_wav_for_diarization(audio_path: Path) -> Path:
    """Convert audio to WAV format for pyannote diarization.

    Pyannote has known bugs with MP3/M4A files causing tensor size mismatches.
    Converting to WAV first is the recommended workaround.
    """
    if audio_path.suffix.lower() == '.wav':
        return audio_path

    wav_path = audio_path.with_suffix('.wav')

    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', str(audio_path),
            '-ar', '16000', '-ac', '1',
            str(wav_path)
        ], check=True, capture_output=True)
        return wav_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to torchaudio
        try:
            import torchaudio
            waveform, sr = torchaudio.load(str(audio_path))
            if sr != 16000:
                resampler = torchaudio.transforms.Resample(sr, 16000)
                waveform = resampler(waveform)
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
            torchaudio.save(str(wav_path), waveform, 16000)
            return wav_path
        except Exception as e:
            print(f"Warning: Could not convert to WAV ({e}), trying original format")
            return audio_path


# ============================================================================
# Transcription
# ============================================================================

def get_transcription_backend(requested: str = 'auto') -> str:
    """Determine which transcription backend to use."""
    if requested == 'mlx':
        if not MLX_AVAILABLE:
            print("Warning: MLX requested but not available. Using OpenAI Whisper.")
            return 'openai'
        return 'mlx'
    elif requested == 'openai':
        return 'openai'
    else:  # auto
        return 'mlx' if MLX_AVAILABLE else 'openai'


def load_whisper_model(model_name: str, backend: str = 'auto'):
    """Load a Whisper model using the specified backend."""
    actual_backend = get_transcription_backend(backend)

    if actual_backend == 'mlx':
        mlx_model = MLX_MODEL_MAP.get(model_name, f'mlx-community/whisper-{model_name}')
        print(f"Using MLX-Whisper backend (Apple Silicon accelerated)")
        print(f"Model: {mlx_model}")
        return ('mlx', mlx_model)
    else:
        print(f"Loading Whisper model: {model_name}")
        model = whisper.load_model(model_name)
        return ('openai', model)


def transcribe_audio(audio_path: Path, model, initial_prompt: str = "",
                     condition_on_previous_text: bool = True) -> dict:
    """Transcribe audio using Whisper (OpenAI or MLX backend)."""
    print(f"Transcribing: {audio_path.name}")

    backend, model_obj = model

    if backend == 'mlx':
        result = mlx_whisper.transcribe(
            str(audio_path),
            path_or_hf_repo=model_obj,
            word_timestamps=True,
            language="en",
            initial_prompt=initial_prompt if initial_prompt else None,
            condition_on_previous_text=condition_on_previous_text
        )
    else:
        result = model_obj.transcribe(
            str(audio_path),
            word_timestamps=True,
            language="en",
            verbose=False,
            initial_prompt=initial_prompt if initial_prompt else None,
            condition_on_previous_text=condition_on_previous_text
        )

    plain_text = result['text'].strip()

    timestamped = []
    for segment in result.get('segments', []):
        timestamped.append({
            'start': round(float(segment['start']), 2),
            'end': round(float(segment['end']), 2),
            'text': segment['text'].strip()
        })

    print(f"Detected language: {result.get('language', 'unknown')}")

    return {
        'text': plain_text,
        'timestamped': timestamped,
        'language': result.get('language', 'unknown')
    }


# ============================================================================
# Speaker Diarization
# ============================================================================

def load_diarization_pipeline(hf_token: str, device: str = None):
    """Load the pyannote diarization pipeline."""
    if not DIARIZATION_AVAILABLE:
        raise RuntimeError(
            "Diarization not available. Install with: pip install pyannote.audio torch"
        )

    if not hf_token:
        raise ValueError(
            "HuggingFace token required for diarization. "
            "Set HF_TOKEN environment variable or pass --hf-token"
        )

    import torch
    if device is None:
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

    print(f"Loading diarization pipeline (device: {device})...")
    pipeline = DiarizationPipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token
    )
    pipeline.to(torch.device(device))

    return pipeline


def diarize_audio(audio_path: Path, pipeline, min_speakers: int = None,
                  max_speakers: int = None) -> tuple:
    """Run speaker diarization on audio file.

    Returns:
        tuple: (diarization_result, embeddings_dict)
               embeddings_dict maps speaker labels to numpy arrays
    """
    print(f"Diarizing: {audio_path.name}")

    wav_path = convert_to_wav_for_diarization(audio_path)
    converted = wav_path != audio_path
    if converted:
        print(f"  Converted to WAV for diarization compatibility")

    kwargs = {"return_embeddings": True}
    if min_speakers is not None:
        kwargs["min_speakers"] = min_speakers
    if max_speakers is not None:
        kwargs["max_speakers"] = max_speakers

    try:
        diarization, embeddings_array = pipeline(str(wav_path), **kwargs)
    finally:
        if converted and wav_path.exists():
            wav_path.unlink()

    # Get speaker labels and convert embeddings array to dict
    speaker_labels = list(diarization.labels())
    print(f"Detected {len(speaker_labels)} speaker(s)")

    # embeddings_array is numpy array with shape (num_speakers, embedding_dim)
    # Convert to dict mapping speaker label -> embedding
    embeddings_dict = {}
    for i, speaker in enumerate(speaker_labels):
        if i < len(embeddings_array):
            embeddings_dict[speaker] = embeddings_array[i]

    return diarization, embeddings_dict


def align_transcription_with_diarization(transcription: dict, diarization) -> dict:
    """Align whisper transcription segments with diarization speaker labels."""
    timestamped = transcription.get('timestamped', [])

    for segment in timestamped:
        seg_start = segment['start']
        seg_end = segment['end']

        speaker_overlaps = {}
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            overlap_start = max(seg_start, turn.start)
            overlap_end = min(seg_end, turn.end)
            overlap = max(0, overlap_end - overlap_start)

            if overlap > 0:
                speaker_overlaps[speaker] = speaker_overlaps.get(speaker, 0) + overlap

        if speaker_overlaps:
            segment['speaker'] = max(speaker_overlaps, key=speaker_overlaps.get)
        else:
            segment['speaker'] = 'UNKNOWN'

    return transcription


# ============================================================================
# Speaker Profiles
# ============================================================================

def load_speaker_profiles(profiles_path: Path = None) -> dict:
    """Load stored speaker voice profiles."""
    if profiles_path is None:
        profiles_path = SPEAKER_PROFILES_FILE

    if profiles_path.exists():
        with open(profiles_path, 'r') as f:
            data = json.load(f)
        for name, profile in data.get('profiles', {}).items():
            if 'embedding_b64' in profile:
                profile['embedding'] = np.frombuffer(
                    base64.b64decode(profile['embedding_b64']),
                    dtype=np.float32
                )
        return data
    return {'profiles': {}}


def save_speaker_profiles(profiles: dict, profiles_path: Path = None):
    """Save speaker voice profiles."""
    if profiles_path is None:
        profiles_path = SPEAKER_PROFILES_FILE

    profiles_path.parent.mkdir(parents=True, exist_ok=True)

    data = {'profiles': {}}
    for name, profile in profiles.get('profiles', {}).items():
        profile_data = {
            'embedding_b64': base64.b64encode(
                profile['embedding'].astype(np.float32).tobytes()
            ).decode('ascii'),
            'meetings_seen': profile.get('meetings_seen', 1),
            'last_updated': profile.get('last_updated', datetime.now().isoformat())
        }
        # Include email if present
        if profile.get('email'):
            profile_data['email'] = profile['email']
        data['profiles'][name] = profile_data

    with open(profiles_path, 'w') as f:
        json.dump(data, f, indent=2)


def match_speakers_to_profiles(embeddings: dict, profiles: dict,
                                threshold: float = 0.35) -> dict:
    """Match detected speaker embeddings against known profiles.

    Returns:
        dict: {"SPEAKER_00": "John Smith", ...} for matched speakers
    """
    if not profiles.get('profiles'):
        return {}

    matches = {}
    for speaker_id, embedding in embeddings.items():
        best_match = None
        best_distance = float('inf')

        for name, profile in profiles['profiles'].items():
            if 'embedding' not in profile:
                continue

            distance = cosine_distance(embedding, profile['embedding'])
            if distance < best_distance:
                best_match = name
                best_distance = distance

        if best_distance < threshold:
            matches[speaker_id] = best_match
            print(f"  Matched {speaker_id} -> {best_match} (confidence: {1-best_distance:.1%})")

    return matches


def match_profiles_to_attendees_by_email(profiles: dict, attendee_details: list) -> dict:
    """Match speaker profiles to calendar attendees by email address.

    This enables matching speakers even before voice embedding comparison,
    if we know a profile's email matches an attendee's email.

    Args:
        profiles: Speaker profiles dict with 'profiles' key
        attendee_details: List of dicts with 'name' and 'email' keys

    Returns:
        Dict mapping profile name to attendee email for matches found
    """
    matches = {}

    # Build index of profile emails
    profile_emails = {}
    for name, profile in profiles.get('profiles', {}).items():
        email = profile.get('email')
        if email:
            profile_emails[email.lower()] = name

    # Also check known_contacts.json
    known_contacts = load_known_contacts()

    # Match attendees to profiles
    for attendee in attendee_details:
        if not attendee:
            continue
        email = (attendee.get('email') or '').lower()
        if not email:
            continue

        # Check if this email matches a profile
        if email in profile_emails:
            profile_name = profile_emails[email]
            matches[profile_name] = email
            print(f"  Profile match by email: {profile_name} <{email}>")

        # Check known_contacts for name resolution
        elif email in known_contacts:
            name = known_contacts[email]
            if name in profiles.get('profiles', {}):
                matches[name] = email
                print(f"  Profile match via contacts: {name} <{email}>")

    return matches


def get_attendee_names_from_email(attendee_details: list) -> list:
    """Resolve attendee emails to full names using known_contacts.

    Args:
        attendee_details: List of dicts with 'name' and 'email' keys

    Returns:
        List of resolved full names
    """
    names = []
    seen = set()

    for attendee in attendee_details:
        if not attendee:
            continue
        email = attendee.get('email', '')
        provided_name = attendee.get('name', '')

        # Try to resolve email to a known name
        if email:
            resolved = resolve_email_to_name(email)
        else:
            resolved = provided_name

        if resolved and resolved.lower() not in seen:
            names.append(resolved)
            seen.add(resolved.lower())

    return names


def update_speaker_profiles(profiles: dict, embeddings: dict,
                            speaker_names: dict,
                            attendee_details: list = None,
                            manual_emails: dict = None) -> dict:
    """Update speaker profiles with new embeddings from identified speakers.

    Args:
        profiles: Existing profiles dict
        embeddings: Speaker embeddings from diarization
        speaker_names: Mapping of speaker_id to name
        attendee_details: Optional list of attendee dicts with 'name' and 'email'
        manual_emails: Optional {"Name": "email"} from --speakers (takes precedence)

    Returns:
        Updated profiles dict
    """
    alpha = 0.3  # Weight for new embedding

    # Build email lookup from attendee details
    name_to_email = {}
    if attendee_details:
        for att in attendee_details:
            email = att.get('email', '')
            name = att.get('name', '')
            if email and name:
                name_to_email[name.lower()] = email
            # Also check if resolved name maps to email
            if email:
                resolved = resolve_email_to_name(email)
                if resolved:
                    name_to_email[resolved.lower()] = email

    # Emails explicitly provided via --speakers take precedence
    if manual_emails:
        for name, email in manual_emails.items():
            if name and email:
                name_to_email[name.lower()] = email

    for speaker_id, name in speaker_names.items():
        if name in ('Unknown', 'UNKNOWN') or speaker_id not in embeddings:
            continue

        new_embedding = embeddings[speaker_id]

        if name in profiles.get('profiles', {}):
            old_embedding = profiles['profiles'][name]['embedding']
            profiles['profiles'][name]['embedding'] = (
                alpha * new_embedding + (1 - alpha) * old_embedding
            )
            profiles['profiles'][name]['meetings_seen'] = (
                profiles['profiles'][name].get('meetings_seen', 0) + 1
            )
            profiles['profiles'][name]['last_updated'] = datetime.now().isoformat()
            # Add email if we found one and profile doesn't have it
            if not profiles['profiles'][name].get('email'):
                email = name_to_email.get(name.lower())
                if email:
                    profiles['profiles'][name]['email'] = email
                    print(f"  Added email to profile: {name} <{email}>")
        else:
            if 'profiles' not in profiles:
                profiles['profiles'] = {}
            profile_data = {
                'embedding': new_embedding,
                'meetings_seen': 1,
                'last_updated': datetime.now().isoformat()
            }
            # Add email if available
            email = name_to_email.get(name.lower())
            if email:
                profile_data['email'] = email
            profiles['profiles'][name] = profile_data

        print(f"  Updated profile for: {name}")

    return profiles


def list_speaker_profiles(profiles_path: Path = None):
    """List all known speaker profiles."""
    profiles = load_speaker_profiles(profiles_path)

    if not profiles.get('profiles'):
        print("No speaker profiles found.")
        return

    print(f"\nKnown Speakers ({len(profiles['profiles'])}):")
    print("-" * 40)
    for name, profile in sorted(profiles['profiles'].items()):
        meetings = profile.get('meetings_seen', 1)
        last_updated = profile.get('last_updated', 'unknown')
        if last_updated != 'unknown':
            last_updated = last_updated.split('T')[0]
        print(f"  {name}: {meetings} meeting(s), last seen {last_updated}")


# ============================================================================
# Audio Samples for Unidentified Speakers
# ============================================================================

SAMPLES_RETENTION_DAYS = 90  # Auto-delete samples older than this


def select_speaker_clips(diarization, speaker_id: str,
                        num_clips: int = 3,
                        target_duration: float = 10.0) -> list:
    """Select good audio segments for a speaker.

    Selection criteria:
    - Duration: 5-15 seconds (long enough to recognize)
    - Spacing: From different parts of the recording
    - Quality: Prefer longer continuous segments

    Args:
        diarization: Pyannote diarization result
        speaker_id: The speaker label (e.g., "SPEAKER_01")
        num_clips: Number of clips to select
        target_duration: Target duration per clip in seconds

    Returns:
        List of (start_time, end_time) tuples in seconds
    """
    # Collect all segments for this speaker
    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        if speaker == speaker_id:
            segments.append((turn.start, turn.end, turn.end - turn.start))

    if not segments:
        return []

    # Sort by duration (prefer longer segments)
    segments.sort(key=lambda x: x[2], reverse=True)

    # Try to get segments from different parts of the recording
    if len(segments) <= num_clips:
        # Use all available segments
        selected = [(s[0], s[1]) for s in segments]
    else:
        # Get total duration to divide into regions
        total_end = max(s[1] for s in segments)

        # Divide recording into num_clips regions
        region_size = total_end / num_clips
        selected = []

        for i in range(num_clips):
            region_start = i * region_size
            region_end = (i + 1) * region_size

            # Find best segment in this region
            region_segments = [
                s for s in segments
                if s[0] >= region_start and s[0] < region_end
            ]

            if region_segments:
                # Pick longest in region
                best = max(region_segments, key=lambda x: x[2])
                selected.append((best[0], best[1]))
            elif segments:
                # Fallback: use any remaining long segment
                for s in segments:
                    if (s[0], s[1]) not in selected:
                        selected.append((s[0], s[1]))
                        break

    # Trim clips to target duration if too long
    trimmed = []
    for start, end in selected:
        duration = end - start
        if duration > target_duration + 5:  # Only trim if much longer
            # Take from the middle of the segment
            mid = (start + end) / 2
            new_start = mid - target_duration / 2
            new_end = mid + target_duration / 2
            trimmed.append((max(0, new_start), new_end))
        else:
            trimmed.append((start, end))

    return trimmed[:num_clips]


def extract_audio_clip(source_audio: Path, output_path: Path,
                       start_time: float, end_time: float) -> bool:
    """Extract a clip from the source audio using ffmpeg.

    Args:
        source_audio: Path to full audio file
        output_path: Where to save the clip
        start_time: Start time in seconds
        end_time: End time in seconds

    Returns:
        True if successful
    """
    try:
        cmd = [
            'ffmpeg', '-y',  # Overwrite output
            '-i', str(source_audio),
            '-ss', str(start_time),
            '-to', str(end_time),
            '-acodec', 'pcm_s16le',  # Convert to PCM WAV format
            '-ar', '16000',  # 16kHz sample rate (good for speech)
            '-ac', '1',  # Mono (smaller files, sufficient for voice ID)
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"  Warning: Failed to extract clip: {e}")
        return False


def get_transcript_for_timerange(transcription: dict,
                                  start_time: float, end_time: float) -> str:
    """Get transcript text for a time range.

    Args:
        transcription: Transcription dict with 'timestamped' segments
        start_time: Start time in seconds
        end_time: End time in seconds

    Returns:
        Concatenated transcript text for overlapping segments
    """
    texts = []
    for seg in transcription.get('timestamped', []):
        seg_start = seg.get('start', 0)
        seg_end = seg.get('end', 0)

        # Check for overlap
        if seg_start < end_time and seg_end > start_time:
            texts.append(seg.get('text', '').strip())

    return ' '.join(texts)


def save_speaker_samples(audio_path: Path, samples_dir: Path,
                         speaker_id: str, clips: list,
                         transcription: dict, embedding=None) -> dict:
    """Save audio samples and metadata for a speaker.

    Args:
        audio_path: Path to source audio
        samples_dir: Directory to save clips
        speaker_id: Speaker label (e.g., "SPEAKER_01")
        clips: List of (start, end) tuples
        transcription: Full transcription for text extraction
        embedding: Optional speaker embedding vector

    Returns:
        Dict with clip metadata
    """
    samples_dir.mkdir(parents=True, exist_ok=True)

    clip_data = []
    for i, (start, end) in enumerate(clips, 1):
        clip_filename = f"{speaker_id}_clip{i}.wav"
        clip_path = samples_dir / clip_filename

        if extract_audio_clip(audio_path, clip_path, start, end):
            transcript_text = get_transcript_for_timerange(transcription, start, end)
            clip_data.append({
                'file': clip_filename,
                'start': round(start, 2),
                'end': round(end, 2),
                'duration': round(end - start, 2),
                'transcript': transcript_text[:500]  # Limit length
            })

    speaker_data = {
        'clips': clip_data,
        'created': datetime.now().isoformat(),
        'expires': (datetime.now() + timedelta(days=SAMPLES_RETENTION_DAYS)).isoformat()
    }

    if embedding is not None:
        speaker_data['embedding_b64'] = base64.b64encode(
            embedding.astype(np.float32).tobytes()
        ).decode('ascii')

    return speaker_data


def save_samples_metadata(samples_dir: Path, samples_data: dict):
    """Save samples.json metadata file."""
    samples_file = samples_dir / 'samples.json'
    with open(samples_file, 'w') as f:
        json.dump(samples_data, f, indent=2)


def load_samples_metadata(samples_dir: Path) -> dict:
    """Load samples.json metadata file."""
    samples_file = samples_dir / 'samples.json'
    if samples_file.exists():
        with open(samples_file) as f:
            return json.load(f)
    return {}


def cleanup_identified_samples(samples_dir: Path, identified_speakers: list):
    """Remove samples for speakers that have been identified.

    Args:
        samples_dir: Path to unidentified_speakers directory
        identified_speakers: List of speaker IDs that were identified
    """
    if not samples_dir.exists():
        return

    samples_data = load_samples_metadata(samples_dir)
    updated = False

    for speaker_id in identified_speakers:
        if speaker_id in samples_data:
            # Delete clip files
            for clip in samples_data[speaker_id].get('clips', []):
                clip_path = samples_dir / clip['file']
                if clip_path.exists():
                    clip_path.unlink()

            # Remove from metadata
            del samples_data[speaker_id]
            updated = True
            print(f"  Removed samples for identified speaker: {speaker_id}")

    if updated:
        if samples_data:
            save_samples_metadata(samples_dir, samples_data)
        else:
            # Remove samples.json if empty
            (samples_dir / 'samples.json').unlink(missing_ok=True)


def cleanup_expired_samples(output_dir: Path = None):
    """Remove samples and stale speaker profiles older than retention period.

    Cleans up:
    1. Unidentified speaker audio samples older than SAMPLES_RETENTION_DAYS
    2. Enrolled speaker profiles not seen in SAMPLES_RETENTION_DAYS

    Args:
        output_dir: Base output directory to scan
    """
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    now = datetime.now()
    cleaned_count = 0

    # 1. Clean up expired unidentified speaker samples
    for meeting_dir in output_dir.iterdir():
        if not meeting_dir.is_dir():
            continue

        samples_dir = meeting_dir / 'unidentified_speakers'
        if not samples_dir.exists():
            continue

        samples_data = load_samples_metadata(samples_dir)
        expired_speakers = []

        for speaker_id, data in samples_data.items():
            expires_str = data.get('expires')
            if expires_str:
                try:
                    expires = datetime.fromisoformat(expires_str)
                    if now > expires:
                        expired_speakers.append(speaker_id)
                except ValueError:
                    pass

        if expired_speakers:
            cleanup_identified_samples(samples_dir, expired_speakers)
            cleaned_count += len(expired_speakers)

            # Remove directory if empty
            if not any(samples_dir.iterdir()):
                samples_dir.rmdir()
                print(f"  Removed empty samples dir: {meeting_dir.name}")

    if cleaned_count > 0:
        print(f"Cleaned up {cleaned_count} expired speaker samples")

    # 2. Prune enrolled speaker profiles not seen in retention period
    cutoff = now - timedelta(days=SAMPLES_RETENTION_DAYS)
    profiles = load_speaker_profiles()
    stale_names = []

    for name, profile in profiles.get('profiles', {}).items():
        last_updated_str = profile.get('last_updated')
        if not last_updated_str:
            continue
        try:
            last_updated = datetime.fromisoformat(last_updated_str)
            if last_updated < cutoff:
                stale_names.append(name)
        except ValueError:
            pass

    if stale_names:
        for name in stale_names:
            del profiles['profiles'][name]
            print(f"  Removed stale speaker profile: {name} (not seen in {SAMPLES_RETENTION_DAYS} days)")
        save_speaker_profiles(profiles)
        print(f"Pruned {len(stale_names)} stale speaker profile(s)")


def parse_speaker_arg(speakers_str: str) -> tuple:
    """Parse a --speakers mapping string into (mapping, emails).

    Accepts entries of the form "SPEAKER_XX=Full Name" with an optional
    trailing email in angle brackets:
        "SPEAKER_00=Pat Lee <plee@example.org>,SPEAKER_01=Jane Doe"

    Returns:
        (mapping, emails) where
          mapping = {"SPEAKER_XX": "Full Name"}        (email stripped from name)
          emails  = {"Full Name": "user@example.com"}  (only entries with an email)
    """
    mapping = {}
    emails = {}
    if not speakers_str:
        return mapping, emails

    for entry in speakers_str.split(','):
        if '=' not in entry:
            continue
        speaker_id, value = entry.split('=', 1)
        speaker_id = speaker_id.strip()
        value = value.strip()

        # Extract optional trailing <email>
        m = re.search(r'<([^>]+)>\s*$', value)
        if m:
            email = m.group(1).strip()
            name = value[:m.start()].strip()
        else:
            email = None
            name = value

        mapping[speaker_id] = name
        if email:
            emails[name] = email

    return mapping, emails


def enroll_from_unidentified(meeting_dir: Path, speaker_mappings: dict,
                             speaker_emails: dict = None) -> list:
    """Enroll speakers from unidentified_speakers.json embeddings.

    When a speaker is manually identified via --relabel, this function
    transfers their embedding from unidentified_speakers.json to
    speaker_profiles.json so they'll be automatically recognized in
    future meetings.

    Args:
        meeting_dir: Path to meeting folder
        speaker_mappings: {"SPEAKER_XX": "Full Name"} mappings
        speaker_emails: Optional {"Full Name": "email"} to attach to profiles

    Returns:
        List of successfully enrolled speaker names
    """
    speaker_emails = speaker_emails or {}
    unidentified_path = meeting_dir / 'unidentified_speakers.json'
    if not unidentified_path.exists():
        return []

    with open(unidentified_path) as f:
        unidentified = json.load(f)

    enrolled = []
    profiles = load_speaker_profiles()

    for speaker_label, full_name in speaker_mappings.items():
        # Skip generic/placeholder names
        if not speaker_label.startswith('SPEAKER_'):
            continue
        if full_name in ('Unknown', 'UNKNOWN', 'CROSS TALK', 'DEMO VOICE') or full_name.startswith('Student '):
            continue
        if full_name == speaker_label:  # Not actually relabeled
            continue

        if speaker_label in unidentified:
            embedding = unidentified[speaker_label].get('embedding')
            if embedding is None:
                continue

            # Convert to numpy array if needed
            embedding = np.array(embedding)

            if full_name in profiles.get('profiles', {}):
                # Update existing profile with weighted average
                alpha = 0.3
                old_embedding = np.array(profiles['profiles'][full_name]['embedding'])
                profiles['profiles'][full_name]['embedding'] = (
                    alpha * embedding + (1 - alpha) * old_embedding
                )  # Keep as numpy array for save_speaker_profiles
                profiles['profiles'][full_name]['meetings_seen'] += 1
                profiles['profiles'][full_name]['last_updated'] = datetime.now().isoformat()
                # Back-fill email if provided and not already set
                if speaker_emails.get(full_name) and not profiles['profiles'][full_name].get('email'):
                    profiles['profiles'][full_name]['email'] = speaker_emails[full_name]
                    print(f"  Added email to profile: {full_name} <{speaker_emails[full_name]}>")
                print(f"  Updated profile for: {full_name}")
            else:
                # Create new profile
                if 'profiles' not in profiles:
                    profiles['profiles'] = {}
                profiles['profiles'][full_name] = {
                    'embedding': embedding,  # Keep as numpy array for save_speaker_profiles
                    'meetings_seen': 1,
                    'last_updated': datetime.now().isoformat()
                }
                if speaker_emails.get(full_name):
                    profiles['profiles'][full_name]['email'] = speaker_emails[full_name]
                print(f"  Enrolled new speaker: {full_name}"
                      + (f" <{speaker_emails[full_name]}>" if speaker_emails.get(full_name) else ""))

            enrolled.append(full_name)
            del unidentified[speaker_label]

    if enrolled:
        # Save updated profiles
        save_speaker_profiles(profiles)

        # Update or remove unidentified_speakers.json
        if unidentified:
            with open(unidentified_path, 'w') as f:
                json.dump(unidentified, f, indent=2)
        else:
            unidentified_path.unlink()

    return enrolled


def relabel_transcript(meeting_dir: Path, speaker_mapping: dict,
                       enroll_speakers: bool = False, source_recording: Path = None,
                       speaker_emails: dict = None):
    """Relabel speakers in an existing transcript.

    Args:
        meeting_dir: Path to the meeting folder containing transcript files
        speaker_mapping: Dict of SPEAKER_XX -> "New Name" mappings
        enroll_speakers: If True, create speaker profiles for relabeled speakers
        source_recording: Path to original recording (required if enroll_speakers=True)
        speaker_emails: Optional {"New Name": "email"} to attach to enrolled profiles
    """
    speaker_emails = speaker_emails or {}
    meeting_dir = Path(meeting_dir)

    # Load existing transcript JSON
    json_path = meeting_dir / 'transcript.json'
    if not json_path.exists():
        print(f"Error: No transcript.json found in {meeting_dir}")
        return False

    with open(json_path, 'r') as f:
        data = json.load(f)

    # Track what we're changing
    changes = {}

    # Update segments
    for segment in data.get('segments', []):
        old_speaker = segment.get('speaker', '')
        if old_speaker in speaker_mapping:
            new_speaker = speaker_mapping[old_speaker]
            segment['speaker'] = new_speaker
            changes[old_speaker] = new_speaker

    # Update metadata speakers list
    if 'metadata' in data:
        old_speakers = data['metadata'].get('speakers', [])
        new_speakers = []
        for s in old_speakers:
            new_speakers.append(speaker_mapping.get(s, s))
        data['metadata']['speakers'] = list(set(new_speakers))

    # Save updated JSON
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)

    # Regenerate text transcript
    from meeting_transcriber import format_transcript_with_timestamps
    text_transcript = format_transcript_with_timestamps({'timestamped': data.get('segments', [])})
    with open(meeting_dir / 'transcript.txt', 'w') as f:
        f.write(text_transcript)

    # Update metadata.json
    metadata_path = meeting_dir / 'metadata.json'
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        old_speakers = metadata.get('speakers', [])
        metadata['speakers'] = [speaker_mapping.get(s, s) for s in old_speakers]
        metadata['speakers'] = list(set(metadata['speakers']))
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    print(f"\nRelabeled speakers in: {meeting_dir}")
    for old, new in changes.items():
        print(f"  {old} -> {new}")

    # Auto-enroll from unidentified_speakers.json (always try this first)
    enrolled = enroll_from_unidentified(meeting_dir, changes, speaker_emails)

    # Diarization-based enrollment fallback (only if explicitly requested and needed)
    # Check if there are any unenrolled speakers left
    unenrolled = [name for old, name in changes.items()
                  if old.startswith('SPEAKER_') and name not in enrolled
                  and name not in ('Unknown', 'UNKNOWN') and not name.startswith('Student ')]

    if enroll_speakers and unenrolled:
        if not source_recording:
            # Try to find source from metadata
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                source_recording = Path(metadata.get('source_file', ''))

        if not source_recording or not source_recording.exists():
            print(f"\nWarning: Cannot enroll {len(unenrolled)} speaker(s) - source recording not found")
            print(f"  Unenrolled: {', '.join(unenrolled)}")
            print("  Use --enroll-relabeled with the original recording available")
            # Continue to cleanup - don't return early
        else:
            # We need to re-run diarization to get embeddings
            print("\nExtracting speaker embeddings for enrollment...")

            # Extract audio if needed
            if is_video_file(source_recording):
                audio_path = meeting_dir / 'audio.wav'
                if not audio_path.exists():
                    audio_path = extract_audio_from_video(source_recording, audio_path)
            else:
                audio_path = source_recording

            # Get HF token
            hf_token = os.environ.get('HF_TOKEN')
            if not hf_token:
                print("Warning: HF_TOKEN not set - cannot run diarization for enrollment")
            else:
                # Run diarization to get embeddings
                pipeline = load_diarization_pipeline(hf_token)
                diarization, embeddings = diarize_audio(audio_path, pipeline)

                if embeddings:
                    # Load existing profiles
                    profiles = load_speaker_profiles()

                    # Map old SPEAKER_XX IDs to new names
                    for old_id, new_name in speaker_mapping.items():
                        # Skip generic names
                        if new_name.startswith('Student ') or new_name in ('Unknown', 'UNKNOWN', 'CROSS TALK', 'DEMO VOICE'):
                            continue
                        # Skip speakers already enrolled from unidentified_speakers.json
                        if new_name in enrolled:
                            continue

                        if old_id in embeddings:
                            embedding = embeddings[old_id]

                            if new_name in profiles.get('profiles', {}):
                                # Update existing profile
                                alpha = 0.3
                                old_embedding = profiles['profiles'][new_name]['embedding']
                                profiles['profiles'][new_name]['embedding'] = (
                                    alpha * embedding + (1 - alpha) * old_embedding
                                )
                                profiles['profiles'][new_name]['meetings_seen'] += 1
                                profiles['profiles'][new_name]['last_updated'] = datetime.now().isoformat()
                                if speaker_emails.get(new_name) and not profiles['profiles'][new_name].get('email'):
                                    profiles['profiles'][new_name]['email'] = speaker_emails[new_name]
                                    print(f"  Added email to profile: {new_name} <{speaker_emails[new_name]}>")
                                print(f"  Updated profile for: {new_name}")
                            else:
                                # Create new profile
                                if 'profiles' not in profiles:
                                    profiles['profiles'] = {}
                                profiles['profiles'][new_name] = {
                                    'embedding': embedding,
                                    'meetings_seen': 1,
                                    'last_updated': datetime.now().isoformat()
                                }
                                if speaker_emails.get(new_name):
                                    profiles['profiles'][new_name]['email'] = speaker_emails[new_name]
                                print(f"  Created profile for: {new_name}")

                    save_speaker_profiles(profiles)

            # Clean up temp audio
            if is_video_file(source_recording) and (meeting_dir / 'audio.wav').exists():
                (meeting_dir / 'audio.wav').unlink()

    # Clean up audio samples for identified speakers
    samples_dir = meeting_dir / 'unidentified_speakers'
    if samples_dir.exists():
        identified_speaker_ids = list(speaker_mapping.keys())
        cleanup_identified_samples(samples_dir, identified_speaker_ids)

        # Remove directory if empty
        try:
            remaining = list(samples_dir.iterdir())
            if not remaining or (len(remaining) == 1 and remaining[0].name == 'samples.json'):
                # Only samples.json left or empty - check if samples.json is empty
                samples_data = load_samples_metadata(samples_dir)
                if not samples_data:
                    for f in samples_dir.iterdir():
                        f.unlink()
                    samples_dir.rmdir()
                    print("  Removed unidentified_speakers/ (all identified)")
        except Exception:
            pass

    return True


# ============================================================================
# Calendar Integration
# ============================================================================

# Diagnostic breadcrumbs for calendar matching, written into metadata.json as
# 'calendar_debug' so silent failures (LLM timestamp parse, calendar query) are
# observable after the fact.
PIPELINE_DEBUG = {}


def parse_recording_timestamp_with_llm(recording_path: Path) -> Optional[datetime]:
    """Use an LLM to extract a recording's start datetime from its file path.

    The parent directory helps determine the recording source:
    - .../Documents/Zoom/2026-02-09 16.04.03 Meeting Name/video....mp4
      → Zoom recording, timestamp is in the parent folder name
    - .../Voice memo manual saves/2025-11-15 - Title.m4a
      → Voice Memo, date (and sometimes time) is in the filename
    - .../Ecamm Live Recordings/Ecamm Live Recording on 2026-02-04 at 08.35.17.mov
      → Ecamm recording, timestamp is in the filename

    Returns:
        datetime with time if available, or date-only (midnight) if only a date
        is present. None if the LLM call fails.
    """
    last_error = None
    for attempt in range(3):
        if attempt > 0:
            time.sleep(2 * attempt)  # 2s, 4s backoff on transient API errors
        try:
            result = _parse_timestamp_llm_once(recording_path)
            PIPELINE_DEBUG['timestamp_source'] = 'llm'
            PIPELINE_DEBUG['timestamp_attempts'] = attempt + 1
            return result
        except Exception as e:
            last_error = e
            print(f"  Warning: LLM timestamp parsing failed (attempt {attempt + 1}/3): {e}")

    PIPELINE_DEBUG['timestamp_source'] = f'mtime_fallback (LLM failed: {last_error})'
    return None


def _parse_timestamp_llm_once(recording_path: Path) -> Optional[datetime]:
    """Single LLM attempt at timestamp extraction. Raises on API errors."""
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": f"""Extract the recording start date and time from this file path. The parent directory name often contains the timestamp (especially for Zoom recordings).

File path: {recording_path}

Return ONLY a JSON object with these fields:
- "date": "YYYY-MM-DD" (required)
- "time": "HH:MM:SS" in 24-hour format (omit if no time is present)

IMPORTANT rules:
- For Zoom recordings, ALWAYS prefer the parent folder timestamp (e.g. "2026-02-10 10.56.59 Meeting Name" → time is 10:56:59). The parent folder has LOCAL time.
- NEVER use GMT filenames like "GMT20260210-155659_Recording.mp4" — these are UTC, not local time. Ignore them if a parent folder timestamp exists.
- For Voice Memos with a date like "2025-11-15 - Title.m4a", return only the date.
- For Ecamm recordings like "Ecamm Live Recording on 2024-09-03 at 12.00.12.mov", the time is 12:00:12.
- For files with times like "9:30 AM", convert to 24-hour format."""
            }]
        )
    text = response.content[0].text.strip()
    # Extract JSON from response
    match = re.search(r'\{[^}]+\}', text)
    if not match:
        return None
    data = json.loads(match.group())
    date_str = data.get('date', '')
    time_str = data.get('time', '')
    if not date_str:
        return None
    parts = date_str.split('-')
    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    if time_str:
        t_parts = time_str.split(':')
        H, M = int(t_parts[0]), int(t_parts[1])
        S = int(t_parts[2]) if len(t_parts) > 2 else 0
        return datetime(y, m, d, H, M, S)
    return datetime(y, m, d)  # Date-only


# Producers whose container creation_time is the recording START.
# Verified empirically: Apple Voice Memos stamps the recording start (UTC) and
# preserves it through share-sheet export to iCloud Drive. Zoom does NOT -- its
# creation_time is when the file was finalised, i.e. the recording END -- and
# re-encoded files carry the re-encode time. Hence a producer whitelist rather
# than trusting the tag wherever it appears.
_CREATION_TIME_TRUSTED_ENCODERS = ('com.apple.voicememos',)


def probe_container_creation_time(recording_path: Path) -> Optional[dict]:
    """Read container creation_time + producer hints via ffprobe, or None."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format_tags=creation_time,encoder,voice-memo-uuid',
             '-of', 'json', str(recording_path)],
            capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None
        tags = (json.loads(result.stdout).get('format') or {}).get('tags') or {}
    except Exception:
        return None

    raw = tags.get('creation_time')
    if not raw:
        return None
    try:
        dt = datetime.strptime(raw.split('.')[0].rstrip('Z'), '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        return None

    local = (dt.replace(tzinfo=timezone.utc).astimezone().replace(tzinfo=None)
             if raw.rstrip('0').endswith('Z') or raw.endswith('Z') else dt)
    encoder = (tags.get('encoder') or '').lower()
    return {
        'utc': dt,
        'local': local,
        'encoder': encoder,
        'is_voice_memo': ('voice-memo-uuid' in tags
                          or any(e in encoder for e in _CREATION_TIME_TRUSTED_ENCODERS)),
    }


def refine_date_only_timestamp(recording_path: Path, day: datetime) -> tuple:
    """Recover a time-of-day for a date-only (midnight) timestamp.

    Returns (timestamp, source, confidence):
      'high'   - container metadata from a producer known to stamp the
                 recording start, and its date agrees with the parsed date.
      'medium' - a clock time from the right day, but possibly a write/export
                 time rather than a recording start. A hint, not proof.
      'none'   - nothing trustworthy; the timestamp stays at midnight.
    """
    probe = probe_container_creation_time(recording_path)
    if probe and probe['local'].date() == day.date():
        if probe['is_voice_memo']:
            return probe['local'], 'container_creation_time (Voice Memos)', 'high'
        return (probe['local'],
                f"container_creation_time ({probe['encoder'] or 'unknown encoder'})",
                'medium')

    # mtime on iCloud Drive is the SYNC time, not the recording time: memos that
    # sat in the cloud for days all land with one stamp (observed: files named
    # 09-01/09-02/09-03 all carrying "Sep 3 19:0x"). Only usable when its DATE
    # already agrees with the date parsed from the filename.
    try:
        mtime = datetime.fromtimestamp(recording_path.stat().st_mtime)
    except OSError:
        return day, 'date_only', 'none'

    if mtime.date() == day.date():
        return mtime, 'mtime_same_day', 'medium'

    return day, 'date_only', 'none'


def get_recording_timestamp(recording_path: Path) -> datetime:
    """Get the timestamp for a recording from its file path using an LLM.

    The LLM examines the full path (including parent directory) to determine
    the recording source type and extract the correct timestamp.

    Returns a date-only timestamp (midnight) when only a date is available,
    so calendar matching will search the full day.
    """
    result = parse_recording_timestamp_with_llm(recording_path)
    if result is None:
        # Fallback: date-only from file modification time (for folder naming)
        mtime = recording_path.stat().st_mtime
        dt = datetime.fromtimestamp(mtime)
        result = datetime(dt.year, dt.month, dt.day)

    # A date-only result means calendar matching would search the whole day and
    # frequently pick the wrong event. Voice Memos stamps the true recording
    # start into the container, so recover the clock time when we can.
    if (result.hour, result.minute, result.second) == (0, 0, 0):
        refined, source, confidence = refine_date_only_timestamp(recording_path, result)
        PIPELINE_DEBUG['time_of_day_source'] = source
        PIPELINE_DEBUG['time_of_day_confidence'] = confidence
        if confidence != 'none':
            print(f"  Recovered time-of-day from {source}: "
                  f"{refined:%H:%M} ({confidence} confidence)")
        return refined

    PIPELINE_DEBUG['time_of_day_source'] = 'filename/path'
    PIPELINE_DEBUG['time_of_day_confidence'] = 'high'
    return result


# Primary work calendar(s) to use for meeting events (filter out personal
# calendars like Grocery/Family). Penn migrated the account from
# seas.upenn.edu -> engineering.upenn.edu, so we query both names; whichever
# exists is used. Add new names here if the account is ever renamed again.
PRIMARY_CALENDARS = ['ccb@engineering.upenn.edu', 'ccb@seas.upenn.edu']
PRIMARY_CALENDAR = PRIMARY_CALENDARS[0]  # back-compat alias


def query_calendar_events(start_time: datetime, end_time: datetime) -> list:
    """Query macOS Calendar for events in a time range.

    Returns list of dicts with 'title', 'start', 'end', 'attendees'

    Retries transient icalBuddy failures (observed after macOS restarts, before
    CalendarAgent has settled) before falling back to AppleScript.
    """
    # First try icalBuddy (cleaner output if installed)
    # Filter to primary calendar to avoid pulling events from personal calendars
    for attempt in range(3):
        if attempt > 0:
            time.sleep(3 * attempt)  # 3s, 6s backoff
        events = _query_calendar_icalbuddy(start_time, end_time,
                                           include_calendars=PRIMARY_CALENDARS)
        if events is not None:
            PIPELINE_DEBUG['calendar_method'] = 'icalbuddy'
            PIPELINE_DEBUG['calendar_attempts'] = attempt + 1
            PIPELINE_DEBUG['calendar_events_found'] = len(events)
            return events
        print(f"  Warning: icalBuddy query failed (attempt {attempt + 1}/3)")

    # Fall back to AppleScript (no calendar filtering available)
    events = _query_calendar_applescript(start_time, end_time)
    PIPELINE_DEBUG['calendar_method'] = 'applescript_fallback'
    PIPELINE_DEBUG['calendar_events_found'] = len(events)
    return events


def _query_calendar_icalbuddy(start_time: datetime, end_time: datetime,
                               include_calendars: list = None) -> Optional[list]:
    """Query calendar using icalBuddy (if installed).

    Install with: brew install ical-buddy

    Args:
        start_time: Start of time range
        end_time: End of time range
        include_calendars: Optional list of calendar names to include (e.g., ['ccb@seas.upenn.edu'])
    """
    try:
        # Check if icalBuddy is available
        subprocess.run(['which', 'icalBuddy'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None  # icalBuddy not installed

    try:
        # Format dates for icalBuddy (only accepts date, not datetime)
        start_str = start_time.strftime('%Y-%m-%d')
        end_str = end_time.strftime('%Y-%m-%d')

        # Build command
        cmd = [
            'icalBuddy',
            '-ea',  # Exclude all-day events
            '-nc',  # No calendar name in output
            '-nrd',  # No relative dates
            '-df', '%Y-%m-%d',  # Date format
            '-tf', '%H:%M',  # Time format
        ]

        # Filter to specific calendars if specified
        if include_calendars:
            cmd.extend(['-ic', ','.join(include_calendars)])

        cmd.extend([f'eventsFrom:{start_str}', f'to:{end_str}'])

        # Query events
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            return None

        return _parse_icalbuddy_output(result.stdout)
    except Exception as e:
        print(f"  icalBuddy error: {e}")
        return None


def _parse_icalbuddy_output(output: str) -> list:
    """Parse icalBuddy output format into event list.

    Format with -nc -df '%Y-%m-%d' -tf '%H:%M':
    • Event Title
        notes: ...
        attendees: person1, person2
        2026-02-04 at 08:30 - 09:00
    """
    events = []
    current_event = None

    for line in output.split('\n'):
        # New event starts with bullet point
        if line.startswith('• '):
            if current_event and current_event.get('title'):
                events.append(current_event)
            # Extract title (remove calendar name in parentheses at end if present)
            title = line[2:].strip()
            if ' (' in title and title.endswith(')'):
                title = title[:title.rfind(' (')]
            current_event = {
                'title': title,
                'start': None,
                'end': None,
                'attendees': []
            }
        elif current_event and line.strip():
            line = line.strip()

            # Check for attendees line
            if line.lower().startswith('attendees:'):
                attendee_str = line.split(':', 1)[1].strip()
                attendees = [a.strip() for a in attendee_str.split(',') if a.strip()]
                current_event['attendees'] = attendees

            # Check for datetime range: "2026-02-04 at 08:30 - 09:00"
            elif current_event['start'] is None:
                # Format: YYYY-MM-DD at HH:MM - HH:MM
                datetime_match = re.match(
                    r'(\d{4}-\d{2}-\d{2})\s+at\s+(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})',
                    line
                )
                if datetime_match:
                    date_str, start_time_str, end_time_str = datetime_match.groups()
                    try:
                        date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        start_time = datetime.strptime(start_time_str, '%H:%M').time()
                        end_time = datetime.strptime(end_time_str, '%H:%M').time()
                        current_event['start'] = datetime.combine(date, start_time)
                        current_event['end'] = datetime.combine(date, end_time)
                    except ValueError:
                        pass

    # Don't forget the last event
    if current_event and current_event.get('title'):
        events.append(current_event)

    return events


def _query_calendar_applescript(start_time: datetime, end_time: datetime) -> list:
    """Query calendar using AppleScript (fallback method)."""
    # AppleScript that outputs events in a parseable format
    # Using ||| as delimiter since it's unlikely to appear in event data
    script = f'''
    set outputText to ""
    set fieldSep to "|||"
    set recordSep to "###EVENT###"

    tell application "Calendar"
        set startDate to current date
        set year of startDate to {start_time.year}
        set month of startDate to {start_time.month}
        set day of startDate to {start_time.day}
        set hours of startDate to {start_time.hour}
        set minutes of startDate to {start_time.minute}
        set seconds of startDate to 0

        set endDate to current date
        set year of endDate to {end_time.year}
        set month of endDate to {end_time.month}
        set day of endDate to {end_time.day}
        set hours of endDate to {end_time.hour}
        set minutes of endDate to {end_time.minute}
        set seconds of endDate to 0

        repeat with cal in calendars
            try
                set calEvents to (every event of cal whose start date >= startDate and start date <= endDate)
                repeat with evt in calEvents
                    set evtTitle to summary of evt
                    set evtStart to start date of evt
                    set evtEnd to end date of evt

                    -- Format dates as ISO-ish strings
                    set startStr to (year of evtStart as string) & "-" & ¬
                        (my padNum(month of evtStart as integer)) & "-" & ¬
                        (my padNum(day of evtStart)) & " " & ¬
                        (my padNum(hours of evtStart)) & ":" & ¬
                        (my padNum(minutes of evtStart))

                    set endStr to (year of evtEnd as string) & "-" & ¬
                        (my padNum(month of evtEnd as integer)) & "-" & ¬
                        (my padNum(day of evtEnd)) & " " & ¬
                        (my padNum(hours of evtEnd)) & ":" & ¬
                        (my padNum(minutes of evtEnd))

                    -- Get attendees
                    set attendeeList to ""
                    try
                        set attList to attendees of evt
                        repeat with att in attList
                            if attendeeList is not "" then
                                set attendeeList to attendeeList & ","
                            end if
                            set attendeeList to attendeeList & (display name of att)
                        end repeat
                    end try

                    set outputText to outputText & recordSep & linefeed
                    set outputText to outputText & "TITLE" & fieldSep & evtTitle & linefeed
                    set outputText to outputText & "START" & fieldSep & startStr & linefeed
                    set outputText to outputText & "END" & fieldSep & endStr & linefeed
                    set outputText to outputText & "ATTENDEES" & fieldSep & attendeeList & linefeed
                end repeat
            end try
        end repeat
    end tell

    return outputText

    on padNum(n)
        if n < 10 then
            return "0" & (n as string)
        else
            return n as string
        end if
    end padNum
    '''

    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, timeout=60  # Increased timeout
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if 'not allowed' in stderr.lower() or 'permission' in stderr.lower():
                print("  Calendar access denied. Grant access in System Settings > Privacy > Calendars")
            else:
                print(f"  Calendar query failed: {stderr}")
            return []

        return _parse_applescript_output(result.stdout)
    except subprocess.TimeoutExpired:
        print("  Calendar query timed out (>60s). Try granting Calendar access in System Settings.")
        return []
    except Exception as e:
        print(f"  Calendar query error: {e}")
        return []


def _parse_applescript_output(output: str) -> list:
    """Parse AppleScript calendar output."""
    events = []
    current_event = None

    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue

        if line == '###EVENT###':
            if current_event and current_event.get('title'):
                events.append(current_event)
            current_event = {
                'title': '',
                'start': None,
                'end': None,
                'attendees': []
            }
        elif current_event is not None and '|||' in line:
            parts = line.split('|||', 1)
            if len(parts) == 2:
                key, value = parts[0].strip(), parts[1].strip()

                if key == 'TITLE':
                    current_event['title'] = value
                elif key == 'START':
                    try:
                        current_event['start'] = datetime.strptime(value, '%Y-%m-%d %H:%M')
                    except ValueError:
                        pass
                elif key == 'END':
                    try:
                        current_event['end'] = datetime.strptime(value, '%Y-%m-%d %H:%M')
                    except ValueError:
                        pass
                elif key == 'ATTENDEES':
                    if value:
                        current_event['attendees'] = [a.strip() for a in value.split(',') if a.strip()]

    # Don't forget the last event
    if current_event and current_event.get('title'):
        events.append(current_event)

    return events


def match_recording_to_event(recording_time: datetime, events: list,
                              tolerance_minutes: int = 30,
                              duration_seconds: float = 0) -> Optional[dict]:
    """Find the calendar event that best matches the recording time.

    Prefers events where:
    1. Recording started during or shortly after event start (within tolerance)
    2. Event start time is closest to recording time

    Args:
        recording_time: When the recording started
        events: List of calendar events
        tolerance_minutes: How much slack to allow for meeting start time

    Returns:
        Best matching event or None
    """
    if not events:
        return None

    tolerance = timedelta(minutes=tolerance_minutes)
    candidates = []

    for event in events:
        if not event.get('start') or not event.get('end'):
            continue

        event_start = event['start']
        event_end = event['end']

        # Check if recording falls within event window (with tolerance)
        # Recording should be after event start (minus tolerance) and before event end (plus tolerance)
        adjusted_start = event_start - tolerance
        adjusted_end = event_end + tolerance

        if adjusted_start <= recording_time <= adjusted_end:
            # How much wall-clock time the recording and the event actually share.
            recording_end = (recording_time + timedelta(seconds=duration_seconds)
                             if duration_seconds > 0 else recording_time)
            overlap = max(0.0, (min(recording_end, event_end)
                                - max(recording_time, event_start)).total_seconds())
            time_diff = abs((recording_time - event_start).total_seconds())
            candidates.append((event, overlap, time_diff))

    if not candidates:
        return None

    # Overlap wins; nearest start only breaks ties. A recording that begins two
    # minutes into a 30-minute slot but runs for an hour belongs to the
    # hour-long meeting, not the slot whose start it happened to sit closest to.
    candidates.sort(key=lambda c: (-c[1], c[2]))
    return candidates[0][0]


def match_event_by_title_keywords(filename: str, events: list,
                                  recording_time: Optional[datetime] = None,
                                  duration_seconds: float = 0,
                                  tolerance_minutes: int = 30) -> Optional[dict]:
    """Match a recording to a calendar event by comparing title keywords.

    Useful for Voice Memos where we only have a date, not a time.
    Looks for overlapping words between the filename and event titles.

    When recording_time is given, only events that plausibly overlap the
    recording are considered. The calendar is queried at day granularity, so
    without this filter a 09:00 event is a candidate for a 14:00 recording.

    Args:
        filename: Recording filename (cleaned, without extension)
        events: List of calendar events for the day
        recording_time: Recording start, when a trusted clock time is known
        duration_seconds: Recording length, used to bound the overlap window
        tolerance_minutes: Slack allowed on either side of the event

    Returns:
        Best matching event or None if no good match
    """
    if not filename or not events:
        return None

    # Restrict to events that could actually overlap this recording.
    if recording_time is not None:
        tol = timedelta(minutes=tolerance_minutes)
        rec_end = (recording_time + timedelta(seconds=duration_seconds)
                   if duration_seconds > 0 else recording_time)
        in_window = [e for e in events
                     if e.get('start') and e.get('end')
                     and e['start'] - tol <= rec_end and e['end'] + tol >= recording_time]
        if not in_window:
            return None
        events = in_window

    # Extract keywords from filename (lowercase, ignore common words)
    # Generic terms are excluded too: they appear in many unrelated event
    # titles and are not evidence of a match on their own.
    stop_words = {'the', 'a', 'an', 'and', 'or', 'for', 'with', 'on', 'at', 'to', 'of', 'in',
                  'ai', 'my', 'is', 'it', 'be', 'we', 'up', 'so', 'do', 'by', 'as', 'if',
                  'meeting', 'meetings', 'call', 'sync', 'chat', 'session', 'discussion',
                  'notes', 'recording', 'new', 'weekly', 'monthly', 'team'}
    filename_words = set(word.lower() for word in re.findall(r'\b[a-zA-Z]{2,}\b', filename)
                        if word.lower() not in stop_words)

    if not filename_words:
        return None

    best_match = None
    best_score = 0

    for event in events:
        event_title = event.get('title', '')
        if not event_title:
            continue

        # Extract keywords from event title
        event_words = set(word.lower() for word in re.findall(r'\b[a-zA-Z]{2,}\b', event_title)
                         if word.lower() not in stop_words)

        # Calculate overlap score
        if event_words:
            overlap = filename_words & event_words
            # Score based on number of matching words and percentage of filename words matched
            score = len(overlap) + (len(overlap) / len(filename_words) if filename_words else 0)

            # A single short token ("AI") is not evidence: require either two
            # distinct overlapping keywords, or one substantial word.
            strong = (len(overlap) >= 2
                      or any(len(w) >= 6 for w in overlap))
            if score > best_score and strong:
                best_score = score
                best_match = event

    return best_match if best_match is not None else None


def extract_names_from_transcript(transcript_text: str) -> set:
    """Extract likely person names from transcript text.

    Looks for speaker labels and capitalized name patterns.

    Returns:
        Set of lowercase name strings for matching
    """
    names = set()

    # Words to exclude (placeholder labels, common words that aren't names)
    exclude_words = {
        'unknown', 'speaker', 'ad', 'clip',  # Placeholder labels
        'to', 'my', 'have', 'the', 'for', 'you', 'and', 'is', 'it',  # Common words
        'so', 'but', 'not', 'that', 'this', 'what', 'there', 'all',
        'everyone', 'everybody', 'guys', 'folks', 'people', 'team',  # Group greetings
        'here', 'look', 'now', 'just', 'well', 'yeah', 'yes', 'okay',  # Filler words
    }

    # Extract speaker labels like "[00:52] Hana Park:" or "Chris Callison-Burch:"
    # Handle hyphenated last names and multi-part names
    speaker_pattern = r'\[[\d:]+\]\s*([A-Z][a-zA-Z\-]+(?:\s+[A-Z][a-zA-Z\-]+)*)\s*:'
    for match in re.finditer(speaker_pattern, transcript_text):
        name = match.group(1)
        # Skip placeholder labels like SPEAKER_02, UNKNOWN, AD
        if re.match(r'^(SPEAKER_?\d*|UNKNOWN|AD|CLIP)$', name, re.IGNORECASE):
            continue
        # Add full name and first name
        names.add(name.lower())
        first_name = name.split()[0].lower()
        if len(first_name) > 2 and first_name not in exclude_words:
            names.add(first_name)

    # Also look for "Thanks [Name]" or "Hi [Name]" patterns
    greeting_pattern = r'\b(?:thanks|thank you|hi|hey|bye|goodbye),?\s+([A-Z][a-z]+)\b'
    for match in re.finditer(greeting_pattern, transcript_text, re.IGNORECASE):
        word = match.group(1).lower()
        if word not in exclude_words:
            names.add(word)

    return names


def get_attendee_names_for_matching(event: dict) -> set:
    """Extract matchable names from calendar event attendees.

    Handles various formats: full names, emails, "Name <email>" format.

    Returns:
        Set of lowercase name strings for matching
    """
    names = set()

    # Get from event title (e.g., "Mira/Chris" or "Chris/Arjun")
    title = event.get('title', '')
    for part in re.split(r'[/\-,&]', title):
        part = part.strip()
        if part and not '@' in part and len(part) > 2:
            names.add(part.lower())
            # Also add first word if multi-word
            first = part.split()[0].lower()
            if len(first) > 2:
                names.add(first)

    # Get from attendees list
    for attendee in event.get('attendees', []):
        if not attendee:
            continue
        # Handle "Name <email>" format
        if '<' in attendee:
            name_part = attendee.split('<')[0].strip()
            if name_part:
                names.add(name_part.lower())
                first = name_part.split()[0].lower()
                if len(first) > 2:
                    names.add(first)
        elif '@' in attendee:
            # Email only - extract name from email prefix
            prefix = attendee.split('@')[0]
            # Handle patterns like "john.smith" or "jsmith" or just "mira"
            if '.' in prefix:
                parts = prefix.split('.')
                for p in parts:
                    if len(p) > 2 and p.isalpha():
                        names.add(p.lower())
            elif len(prefix) > 2 and prefix.isalpha():
                # Simple username like "mira"
                names.add(prefix.lower())
        else:
            # Plain name
            names.add(attendee.lower())
            first = attendee.split()[0].lower()
            if len(first) > 2:
                names.add(first)

    return names


def get_strategic_transcript_sample(transcript_text: str, total_chars: int = 9000) -> str:
    """Get a strategic sample from beginning, middle, and end of transcript.

    This ensures we capture:
    - Beginning: introductions, people joining
    - Middle: main discussion content
    - End: wrap-up, "thanks [name]" farewells

    Args:
        transcript_text: Full transcript
        total_chars: Total characters to sample

    Returns:
        Sampled text with [...] markers between sections
    """
    if len(transcript_text) <= total_chars:
        return transcript_text

    chunk_size = total_chars // 3

    # Beginning
    beginning = transcript_text[:chunk_size]

    # Middle
    mid_start = (len(transcript_text) - chunk_size) // 2
    middle = transcript_text[mid_start:mid_start + chunk_size]

    # End
    end = transcript_text[-chunk_size:]

    return f"{beginning}\n\n[... middle of transcript ...]\n\n{middle}\n\n[... end of transcript ...]\n\n{end}"


def match_event_by_transcript_content(transcript_text: str, events: list) -> Optional[dict]:
    """Match a transcript to the most likely calendar event using two-pass approach.

    Pass 1: Name-based matching (fast, no LLM)
        - Extract names from transcript
        - Score events by name overlap with attendees/title
        - If clear winner with 2+ matches, return it

    Pass 2: LLM matching with strategic sampling (if Pass 1 inconclusive)
        - Sample from beginning, middle, and end of transcript
        - Ask LLM to match based on content

    Args:
        transcript_text: Full transcript text
        events: List of calendar events for the day

    Returns:
        Best matching event or None if no confident match
    """
    if not transcript_text or not events:
        return None

    # ===== Pass 1: Name-based matching =====
    transcript_names = extract_names_from_transcript(transcript_text)

    if transcript_names:
        scores = []
        for event in events:
            event_names = get_attendee_names_for_matching(event)
            overlap = transcript_names & event_names
            # Normalise by roster size. Ranking on raw overlap count
            # systematically elects the biggest-roster event: a 20-person lab
            # meeting shares 2+ names with almost any lab transcript, which is
            # how 1:1s ended up misfiled as the weekly group meeting.
            coverage = len(overlap) / len(event_names) if event_names else 0.0
            scores.append((event, len(overlap), coverage, overlap))

        scores.sort(key=lambda x: (x[2], x[1]), reverse=True)

        top = scores[0]
        runner = scores[1] if len(scores) > 1 else None
        # Require 2+ names, at least half the roster present, and a clear margin
        # over the runner-up. Anything less falls through to the LLM check.
        if (top[1] >= 2 and top[2] >= 0.5
                and (runner is None or top[2] >= runner[2] + 0.25)):
            event, count, coverage, overlap = top
            print(f"  Name-based match: {event.get('title')} "
                  f"({count} names, {coverage:.0%} of roster: {', '.join(overlap)})")
            PIPELINE_DEBUG['calendar_match_basis'] = 'name_overlap'
            return event

    # ===== Pass 2: LLM matching with strategic sampling =====
    try:
        import anthropic
        client = anthropic.Anthropic()
    except (ImportError, Exception):
        return None

    # Format events for the prompt
    events_list = []
    for i, evt in enumerate(events):
        start_str = evt.get('start', datetime.min).strftime('%H:%M') if evt.get('start') else '??:??'
        attendees = evt.get('attendees', [])
        attendee_str = ', '.join(attendees[:5]) if attendees else 'No attendees listed'
        events_list.append(f"{i+1}. [{start_str}] {evt.get('title', 'Untitled')} (Attendees: {attendee_str})")

    events_formatted = '\n'.join(events_list)

    # Use strategic sampling instead of just the beginning
    transcript_sample = get_strategic_transcript_sample(transcript_text, 9000)

    prompt = f"""I have a meeting transcript and a list of calendar events from that day. Determine if this transcript matches one of the calendar events.

Calendar events for this day:
{events_formatted}

Transcript (sampled from beginning, middle, and end):
{transcript_sample}

Analyze: Does this transcript clearly match one of the calendar events above? Consider:
- Are any attendee names mentioned in the transcript?
- Does the discussion topic match an event title?
- Is there any direct evidence linking the transcript to a specific event?

IMPORTANT: Many of these recordings are not calendar events at all - personal
voice notes, walking notes, ad-hoc conversations, lectures, office hours.
Answer NO unless there is direct evidence tying the transcript to one specific
event: attendees of that event speaking or being named, or the event's specific
topic being discussed. A shared general subject area is NOT enough. A wrong
match silently misfiles the meeting, which is much worse than no match at all.

Respond in this exact format:
MATCH: YES or NO
EVENT: [number 1-{len(events)}] (only if MATCH is YES)
CONFIDENCE: HIGH or LOW
REASON: [brief explanation]"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.content[0].text.strip()

        # Parse the response. Only a HIGH-confidence YES is accepted: a wrong
        # match silently misfiles the meeting, whereas no match is visible and
        # can be resolved by asking a human what the recording actually was.
        upper = answer.upper()
        said_yes = "MATCH: YES" in upper or "MATCH:YES" in upper
        high_conf = "CONFIDENCE: HIGH" in upper or "CONFIDENCE:HIGH" in upper
        if said_yes and not high_conf:
            print(f"  LLM match declined (not high confidence) - leaving unmatched")
        if said_yes and high_conf:
            # Extract event number
            match = re.search(r'EVENT:\s*(\d+)', answer, re.IGNORECASE)
            if match:
                event_num = int(match.group(1))
                if 1 <= event_num <= len(events):
                    matched_event = events[event_num - 1]
                    # Extract reason for logging
                    reason_match = re.search(r'REASON:\s*(.+)', answer, re.IGNORECASE)
                    reason = reason_match.group(1) if reason_match else "LLM match"
                    print(f"  LLM match: {matched_event.get('title')} - {reason[:50]}")
                    PIPELINE_DEBUG['calendar_match_basis'] = 'llm_high'
                    return matched_event

    except Exception as e:
        print(f"  Warning: LLM event matching failed: {e}")

    return None


def generate_meeting_title_from_transcript(transcript_text: str) -> Optional[str]:
    """Use LLM to generate a concise meeting title from transcript content.

    Args:
        transcript_text: First portion of the transcript

    Returns:
        Generated title string or None if generation fails
    """
    if not transcript_text:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic()
    except (ImportError, Exception):
        return None

    # Use first ~2000 chars of transcript for context
    transcript_sample = transcript_text[:2000]

    prompt = f"""Based on this meeting transcript excerpt, generate a concise title (3-8 words) that captures the main topic or purpose of the meeting.

Transcript:
{transcript_sample}

Guidelines:
- Focus on the main topic being discussed
- Include relevant names if it's a 1:1 or small meeting
- Keep it brief and descriptive
- Do not include dates or times

Meeting title:"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=30,
            messages=[{"role": "user", "content": prompt}]
        )
        title = response.content[0].text.strip()
        # Remove quotes if present
        title = title.strip('"\'')
        # Limit length
        if len(title) > 80:
            title = title[:77] + "..."
        return title

    except Exception as e:
        print(f"  Warning: LLM title generation failed: {e}")

    return None


def parse_attendee_details(attendee_str: str) -> dict:
    """Parse an attendee string into name and email components.

    Handles formats like:
    - "John Smith <john.smith@example.com>"
    - "john.smith@example.com"
    - "John Smith"
    """
    if not attendee_str:
        return {'name': None, 'email': None}

    attendee_str = attendee_str.strip()
    name = None
    email = None

    # Format: "Name <email@example.com>"
    if '<' in attendee_str and '>' in attendee_str:
        name = attendee_str.split('<')[0].strip()
        email_match = re.search(r'<([^>]+)>', attendee_str)
        if email_match:
            email = email_match.group(1).strip()
    elif '@' in attendee_str:
        # It's just an email, try to derive name from it
        email = attendee_str
        # Try to make a name from email prefix
        prefix = attendee_str.split('@')[0]
        name = prefix.replace('.', ' ').replace('_', ' ').replace('-', ' ').title()
    else:
        # Just a name
        name = attendee_str

    return {'name': name or None, 'email': email or None}


def get_attendee_details(event: dict) -> list:
    """Extract full attendee details (name + email) from a calendar event.

    Returns list of dicts with 'name' and 'email' fields.
    """
    if not event:
        return []

    attendees = event.get('attendees', [])
    details = []

    for attendee in attendees:
        if not attendee:
            continue
        parsed = parse_attendee_details(attendee)
        if parsed['name'] or parsed['email']:
            details.append(parsed)

    return details


def get_event_attendees(event: dict) -> list:
    """Extract attendee names from a calendar event.

    Cleans up attendee names by:
    - Removing email addresses
    - Extracting just the display name portion
    """
    if not event:
        return []

    attendees = event.get('attendees', [])
    cleaned = []

    for attendee in attendees:
        if not attendee:
            continue

        parsed = parse_attendee_details(attendee)
        name = parsed['name']

        if name and name not in cleaned:
            cleaned.append(name)

    return cleaned


def format_event_for_display(event: dict) -> str:
    """Format a calendar event for display to user."""
    if not event:
        return "(no event)"

    title = event.get('title', 'Untitled')
    start = event.get('start')
    attendees = event.get('attendees', [])

    time_str = start.strftime('%I:%M %p') if start else '??:??'
    attendee_str = f" with {', '.join(attendees[:3])}" if attendees else ""
    if len(attendees) > 3:
        attendee_str += f" +{len(attendees)-3} more"

    return f"{title} @ {time_str}{attendee_str}"


# ============================================================================
# Heuristic Speaker Detection
# ============================================================================

def detect_names_in_transcript(segments: list) -> dict:
    """Detect potential speaker names from transcript patterns.

    Looks for patterns like:
    - "Hi [Name]", "Hello [Name]"
    - "Thanks, [Name]", "Thank you, [Name]"
    - "[Name], what do you think?"
    - "Go ahead, [Name]"

    Returns:
        dict: {detected_name: [segment_indices where mentioned]}
    """
    # Common false positives to exclude
    FALSE_POSITIVES = {
        'like', 'chat', 'oh', 'you', 'yeah', 'yes', 'no', 'well', 'so',
        'um', 'uh', 'ah', 'ok', 'okay', 'sure', 'right', 'now', 'then',
        'here', 'there', 'this', 'that', 'what', 'how', 'why', 'who',
        'all', 'just', 'very', 'really', 'actually', 'basically',
        'everyone', 'everybody', 'guys', 'folks', 'team', 'man', 'dude',
        'sir', 'ma', 'mam', 'dear', 'hey', 'hi', 'hello', 'bye', 'thanks',
        'great', 'good', 'nice', 'cool', 'awesome', 'amazing', 'fantastic',
    }

    patterns = [
        r'\b(?:hi|hello|hey)\s+([A-Z][a-z]+)\b',  # Hi John
        r'\b(?:thanks?|thank you),?\s+([A-Z][a-z]+)\b',  # Thanks, John
        r'\b([A-Z][a-z]+),?\s+(?:what do you|could you|can you|would you)',  # John, what do you
        r'\bgo ahead,?\s+([A-Z][a-z]+)\b',  # Go ahead, John
        r'\b(?:over to you),?\s+([A-Z][a-z]+)\b',  # Over to you, John
    ]

    detected = {}
    for i, segment in enumerate(segments):
        text = segment.get('text', '')
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for name in matches:
                name = name.capitalize()
                # Filter out false positives
                if name.lower() in FALSE_POSITIVES:
                    continue
                # Names should be at least 2 chars
                if len(name) < 2:
                    continue
                if name not in detected:
                    detected[name] = []
                detected[name].append(i)

    return detected


# ============================================================================
# Interactive Speaker Identification
# ============================================================================

def get_speaker_excerpt(segments: list, speaker_id: str, max_chars: int = 300) -> str:
    """Get a sample of what a speaker said for identification."""
    speaker_segments = [s for s in segments if s.get('speaker') == speaker_id]
    if not speaker_segments:
        return "(no speech found)"

    excerpt = []
    total = 0
    for seg in speaker_segments[:5]:
        text = seg.get('text', '').strip()
        if total + len(text) > max_chars:
            break
        excerpt.append(text)
        total += len(text)

    return ' '.join(excerpt) or "(no speech found)"


def prompt_speaker_identification(segments: list, speaker_id: str,
                                   suggestions: list = None) -> Optional[str]:
    """Interactively prompt user to identify a speaker.

    Args:
        segments: Transcript segments
        speaker_id: The speaker ID to identify (e.g., "SPEAKER_00")
        suggestions: List of suggested names (from calendar, heuristics)

    Returns:
        Speaker name or None to skip
    """
    excerpt = get_speaker_excerpt(segments, speaker_id)

    print(f"\n{'='*60}")
    print(f"Who is {speaker_id}?")
    print(f"{'='*60}")
    print(f"Sample: \"{excerpt}\"")

    if suggestions:
        print(f"\nSuggestions: {', '.join(suggestions)}")

    print("\nOptions:")
    print("  - Type a name to identify this speaker")
    print("  - Press Enter to skip (keep as {})".format(speaker_id))
    print("  - Type 'q' to skip all remaining speakers")

    try:
        response = input("\nName: ").strip()
    except (EOFError, KeyboardInterrupt):
        return None

    if response.lower() == 'q':
        return 'QUIT'
    if not response:
        return None

    return response


# ============================================================================
# Transcript Formatting
# ============================================================================

def format_transcript_with_speakers(transcription: dict) -> str:
    """Format transcript with speaker labels for display."""
    lines = []
    current_speaker = None

    for segment in transcription.get('timestamped', []):
        speaker = segment.get('speaker', 'UNKNOWN')
        text = segment.get('text', '').strip()

        if speaker != current_speaker:
            if lines:
                lines.append('')
            lines.append(f"[{speaker}]: {text}")
            current_speaker = speaker
        else:
            lines.append(f"  {text}")

    return '\n'.join(lines)


def format_transcript_with_timestamps(transcription: dict) -> str:
    """Format transcript with timestamps and speaker labels."""
    lines = []
    current_speaker = None

    for segment in transcription.get('timestamped', []):
        speaker = segment.get('speaker', 'UNKNOWN')
        text = segment.get('text', '').strip()
        start = segment.get('start', 0)

        minutes = int(start // 60)
        seconds = int(start % 60)
        timestamp = f"[{minutes:02d}:{seconds:02d}]"

        if speaker != current_speaker:
            if lines:
                lines.append('')
            lines.append(f"{timestamp} {speaker}: {text}")
            current_speaker = speaker
        else:
            lines.append(f"         {text}")

    return '\n'.join(lines)


def clean_transcript_with_llm(transcript_text: str) -> str:
    """Use Claude to clean up transcript: fix capitalization, punctuation, remove fillers."""
    import anthropic
    client = anthropic.Anthropic()

    # Process in chunks to handle long transcripts (max ~15K chars per chunk)
    MAX_CHUNK = 15000
    lines = transcript_text.split('\n')
    chunks = []
    current_chunk = []
    current_len = 0

    for line in lines:
        if current_len + len(line) > MAX_CHUNK and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_len = 0
        current_chunk.append(line)
        current_len += len(line) + 1

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    print(f"Cleaning transcript with LLM ({len(chunks)} chunk(s))...")

    cleaned_chunks = []
    for i, chunk in enumerate(chunks):
        if len(chunks) > 1:
            print(f"  Processing chunk {i+1}/{len(chunks)}...")

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": f"""Clean up this meeting transcript. Make these changes ONLY:
1. Fix capitalization (sentence-initial caps, "I", proper nouns like names, places, companies, products)
2. Add missing punctuation (periods, commas, question marks)
3. Remove filler words (um, uh, like, you know, I mean, sort of, kind of) ONLY when they don't carry meaning
4. Remove false starts and repeated words (e.g., "the the" → "the")
5. Remove hallucination artifacts (repeated words like "another another another..." or "treatment treatment...")

Do NOT change:
- The meaning or content of what was said
- Speaker labels or timestamps (lines starting with [MM:SS])
- The overall structure or line breaks
- Words that aren't filler (keep "like" when it means "similar to")

Return ONLY the cleaned transcript, no commentary.

{chunk}"""
            }]
        )
        cleaned_chunks.append(message.content[0].text)

    return '\n'.join(cleaned_chunks)


def generate_meeting_title_and_summary(transcript_text: str, participants: list = None) -> dict:
    """Use Claude to generate both title and summary from the full transcript.

    Generates both in one call to ensure the title reflects the whole meeting,
    not just the beginning.

    Args:
        transcript_text: Full transcript text
        participants: Optional list of participant names

    Returns:
        dict with 'title' and 'summary' keys
    """
    import anthropic
    client = anthropic.Anthropic()

    # Use a substantial portion of the transcript for context
    # Haiku can handle ~200k tokens, so 50k chars is safe
    sample = transcript_text[:50000]
    participants_str = ", ".join(participants) if participants else "Unknown"

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"""Analyze this meeting transcript and provide:

1. A short descriptive TITLE (3-8 words) that captures the main topic/purpose
2. A brief SUMMARY (2-3 sentences) covering key decisions, action items, or main topics

Examples of good titles:
- "CIS 2210 Staff Meeting"
- "DARPA Project Planning Session"
- "Interview with Jane Smith"
- "Budget Review and Approval"

Participants: {participants_str}

Transcript:
{sample}

Respond in exactly this format:
TITLE: [your title here]
SUMMARY: [your 2-3 sentence summary here]"""
        }]
    )

    response = message.content[0].text.strip()

    # Parse the response
    title = ""
    summary = ""

    for line in response.split('\n'):
        if line.startswith('TITLE:'):
            title = line[6:].strip().strip('"\'')
        elif line.startswith('SUMMARY:'):
            summary = line[8:].strip()

    # If parsing failed, try to extract something useful
    if not title and response:
        # Take first line as title
        title = response.split('\n')[0].strip().strip('"\'')
        if title.startswith('TITLE:'):
            title = title[6:].strip()

    return {'title': title, 'summary': summary}


def generate_meeting_title_with_llm(transcript_text: str, participants: list = None) -> str:
    """Use Claude to generate a short, descriptive meeting title from transcript content.

    This uses the combined title+summary function to ensure the title reflects
    the whole meeting, not just the beginning.
    """
    result = generate_meeting_title_and_summary(transcript_text, participants)
    return result.get('title', '')


def collapse_speaker_labels(text: str) -> str:
    """Collapse consecutive lines from the same speaker into one block."""
    lines = text.split('\n')
    result = []
    current_speaker = None
    current_text = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = re.match(r'\[([^\]]+)\]:\s*(.*)', line)
        if match:
            speaker, content = match.groups()
            if speaker == current_speaker:
                current_text.append(content)
            else:
                if current_speaker and current_text:
                    result.append(f"[{current_speaker}]: {' '.join(current_text)}")
                current_speaker = speaker
                current_text = [content] if content else []
        else:
            if current_text:
                current_text.append(line)
            else:
                result.append(line)

    if current_speaker and current_text:
        result.append(f"[{current_speaker}]: {' '.join(current_text)}")

    return '\n'.join(result)


# ============================================================================
# File Management
# ============================================================================

def trash_file(file_path: Path) -> bool:
    """Move file to macOS Trash.

    Returns True if successful, False otherwise.
    """
    try:
        # Use AppleScript to move to Trash (safer than permanent delete)
        script = f'''
        tell application "Finder"
            delete POSIX file "{file_path}"
        end tell
        '''
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"Moved to Trash: {file_path.name}")
            return True
        else:
            print(f"Failed to trash file: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error moving to trash: {e}")
        return False


# ============================================================================
# Zoom chat / caption capture
# ============================================================================
#
# Zoom writes a folder under ~/Documents/Zoom for every meeting it saves
# anything for -- including meetings it did NOT record, where the folder holds
# only the chat log. So the chat is recoverable whether a call was recorded by
# Zoom or by Ecamm, but the two cases need different lookups:
#
#   Zoom-recorded : the chat file is a sibling of the recording. Unambiguous.
#   Ecamm-recorded: no relationship on disk. Match by time instead.
#
# Four chat layouts exist in the archive, all reducible to a leading timestamp:
#   meeting_saved_chat.txt      "15:07:21 From X to Y : text"
#   meeting_saved_new_chat.txt  "[2026-09-09 ]19:49:16 From X to Y:" + tab body
#   chat.txt                    "16:38:30\t From X : text"
#   closed_caption.txt          "14:38:36 text"     (a real caption transcript)

ZOOM_ROOT = Path.home() / 'Documents' / 'Zoom'

# Richest first: chat.txt is a subset duplicate of meeting_saved_new_chat.txt
# (verified across the 50 folders that carry both -- same URLs, new_chat merely
# adds formatting), so only the best one is copied.
ZOOM_CHAT_FILENAMES = ('meeting_saved_new_chat.txt', 'meeting_saved_chat.txt', 'chat.txt')
ZOOM_CAPTION_FILENAMES = ('closed_caption.txt', 'meeting_saved_closed_caption.txt')

_ZOOM_TS_RE = re.compile(r'^(?:(\d{4})-(\d{2})-(\d{2})[ T]+)?(\d{2}):(\d{2}):(\d{2})\b')
_ZOOM_FOLDER_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})\s+(\d{2})\.(\d{2})\.(\d{2})')

_SECRET_PATTERNS = (
    re.compile(r'\b[0-9a-f]{32,}\b'),
    re.compile(r'\bsk-[A-Za-z0-9_\-]{16,}'),
    re.compile(r'\b(?:api[_ -]?key|secret|password|passwd|token)\b\s*[:=]', re.I),
)


def parse_zoom_chat_times(chat_path: Path, folder_date: Optional[datetime] = None) -> list:
    """Return the datetimes of messages in a Zoom chat/caption file.

    Lines carrying only a clock time inherit their date from the folder name.
    A time that jumps backwards by more than 12h is treated as passing
    midnight, so meetings that run past 00:00 still yield a monotonic series.
    """
    try:
        text = chat_path.read_text(errors='ignore')
    except OSError:
        return []
    times = []
    prev = None
    day_offset = 0
    for line in text.split('\n'):
        m = _ZOOM_TS_RE.match(line)
        if not m:
            continue
        y, mo, d, hh, mm, ss = m.groups()
        if y:
            dt = datetime(int(y), int(mo), int(d), int(hh), int(mm), int(ss))
        else:
            if folder_date is None:
                continue
            dt = folder_date.replace(hour=int(hh), minute=int(mm), second=int(ss),
                                     microsecond=0) + timedelta(days=day_offset)
            if prev is not None and (prev - dt).total_seconds() > 12 * 3600:
                day_offset += 1
                dt += timedelta(days=1)
        prev = dt
        times.append(dt)
    return times


def _zoom_folder_timestamp(folder: Path) -> Optional[datetime]:
    m = _ZOOM_FOLDER_RE.match(folder.name)
    if not m:
        return None
    y, mo, d, hh, mm, ss = (int(x) for x in m.groups())
    try:
        return datetime(y, mo, d, hh, mm, ss)
    except ValueError:
        return None


def _pick_chat_file(folder: Path) -> Optional[Path]:
    for name in ZOOM_CHAT_FILENAMES:
        p = folder / name
        if p.exists() and p.stat().st_size > 0:
            return p
    return None


def _pick_caption_file(folder: Path) -> Optional[Path]:
    for name in ZOOM_CAPTION_FILENAMES:
        p = folder / name
        if p.exists() and p.stat().st_size > 0:
            return p
    return None


def find_zoom_chat_for_recording(recording_path: Path, timestamp: datetime,
                                 duration_seconds: float = 0,
                                 zoom_root: Optional[Path] = None,
                                 pad_minutes: int = 15) -> Optional[dict]:
    """Locate the Zoom folder whose chat belongs to this recording.

    Returns {'folder', 'chat', 'captions', 'matched_by', 'score', 'messages',
    'other_candidates'} or None. Abstains rather than guessing: a chat attached
    to the wrong meeting is worse than no chat at all.
    """
    zoom_root = zoom_root or ZOOM_ROOT

    # --- Case 1: the recording sits inside a Zoom folder; chat is a sibling.
    parent = recording_path.parent
    if _zoom_folder_timestamp(parent) is not None and _pick_chat_file(parent):
        chat = _pick_chat_file(parent)
        return {'folder': parent, 'chat': chat, 'captions': _pick_caption_file(parent),
                'matched_by': 'sibling', 'score': 1.0,
                'messages': len(parse_zoom_chat_times(chat, _zoom_folder_timestamp(parent))),
                'other_candidates': 0}

    # --- Case 2: recorded elsewhere (Ecamm). Match on chat message times.
    if not zoom_root.is_dir():
        return None
    rec_start = timestamp
    rec_end = timestamp + timedelta(seconds=duration_seconds or 0)
    pad = timedelta(minutes=pad_minutes)
    day = timestamp.strftime('%Y-%m-%d')

    scored = []
    for folder in zoom_root.iterdir():
        if not folder.is_dir() or not folder.name.startswith(day):
            continue
        chat = _pick_chat_file(folder)
        if not chat:
            continue
        ftime = _zoom_folder_timestamp(folder)
        times = parse_zoom_chat_times(chat, ftime)
        if not times:
            continue
        inside = sum(1 for t in times if rec_start - pad <= t <= rec_end + pad)
        score = inside / len(times)
        # The folder's own stamp must also sit in the meeting. Padding here is
        # deliberately asymmetric: a Zoom call is often already running before
        # you start recording (so allow slack before), but a chat folder first
        # written after the recording stopped almost certainly belongs to the
        # NEXT meeting, so allow almost none after. Symmetric padding wrongly
        # attached a 15:17 chat to a meeting that ended at 15:14.
        stamp_inside = bool(ftime
                            and rec_start - timedelta(minutes=20) <= ftime
                            and ftime <= rec_end + timedelta(minutes=2))
        scored.append((score, stamp_inside, len(times), folder, chat))

    if not scored:
        return None
    scored.sort(key=lambda s: (s[0], s[1], s[2]), reverse=True)
    best = scored[0]
    if best[0] < 0.6 or not best[1]:
        return None
    if len(scored) > 1 and scored[1][0] >= best[0] - 0.2 and scored[1][1]:
        return None          # two plausible folders: abstain rather than guess
    return {'folder': best[3], 'chat': best[4], 'captions': _pick_caption_file(best[3]),
            'matched_by': 'time_overlap', 'score': round(best[0], 3),
            'messages': best[2], 'other_candidates': len(scored) - 1}


def copy_zoom_chat_into_meeting(meeting_dir: Path, match: dict) -> Optional[dict]:
    """Copy the matched Zoom chat (and captions) into the meeting folder.

    Files are copied verbatim -- Zoom's own layouts are already readable, and
    reformatting risks mangling content that may be the only surviving record
    once the source folder is deleted.
    """
    if not match:
        return None
    info = {'source_folder': str(match['folder']), 'source_file': match['chat'].name,
            'matched_by': match['matched_by'], 'messages': match['messages']}
    if match['matched_by'] == 'time_overlap':
        info['match_score'] = match['score']
        info['other_candidates'] = match['other_candidates']
    try:
        text = match['chat'].read_text(errors='ignore')
        (meeting_dir / 'zoom_chat.txt').write_text(text)
        print(f"  Saved Zoom chat ({match['messages']} messages, "
              f"{match['matched_by']}): zoom_chat.txt")
        # Strip URLs first: paper/commit IDs are long hex strings and would
        # otherwise trip the detector on every Semantic Scholar or GitHub link.
        scan_text = re.sub(r'https?://\S+', '', text)
        if any(p.search(scan_text) for p in _SECRET_PATTERNS):
            print("  WARNING: the Zoom chat looks like it contains a credential "
                  "(API key/token/password). It has been copied verbatim; "
                  "review zoom_chat.txt and rotate the secret if so.")
            info['possible_secret'] = True
        if match.get('captions'):
            (meeting_dir / 'zoom_captions.txt').write_text(
                match['captions'].read_text(errors='ignore'))
            info['captions_file'] = match['captions'].name
            print("  Saved Zoom captions: zoom_captions.txt")
    except OSError as e:
        print(f"  Warning: could not copy Zoom chat: {e}")
        return None
    return info


def update_meeting_log(meeting_dir: Path, metadata: dict, timestamp: datetime,
                       recording_path: Path) -> None:
    """Append an entry to the meeting_log.json file after transcription.

    Args:
        meeting_dir: Path to the meeting output directory
        metadata: Meeting metadata dict
        timestamp: Recording timestamp
        recording_path: Path to the source recording
    """
    log_path = meeting_dir.parent / 'meeting_log.json'

    # Load existing log or create new one
    if log_path.exists():
        try:
            with open(log_path) as f:
                log = json.load(f)
        except (json.JSONDecodeError, IOError):
            log = {"meetings": []}
    else:
        log = {"meetings": []}

    # Determine source type
    filename_lower = recording_path.name.lower()
    if 'ecamm' in filename_lower:
        source_type = 'ecamm'
    elif 'gmt' in filename_lower or 'zoom' in filename_lower:
        source_type = 'zoom'
    elif 'voice memo' in str(recording_path).lower() or filename_lower.startswith('20'):
        source_type = 'voice_memo'
    else:
        source_type = 'unknown'

    # Build folder-name-based ID
    folder_name = meeting_dir.name
    entry_id = re.sub(r'[^a-zA-Z0-9_]', '_', folder_name)

    # Skip if already logged
    existing_ids = {m.get('id') for m in log['meetings']}
    if entry_id in existing_ids:
        return

    # Get participants from metadata
    speakers = metadata.get('speakers', [])
    participants = [s for s in speakers if s != 'UNKNOWN' and not s.startswith('SPEAKER_')]

    # Get title from folder name (strip date prefix)
    title = re.sub(r'^\d{4}-\d{2}-\d{2}_', '', folder_name)

    # Get duration
    duration_secs = metadata.get('duration_seconds', 0)
    duration_mins = round(duration_secs / 60) if duration_secs else 0

    entry = {
        'id': entry_id,
        'date': timestamp.strftime('%Y-%m-%d'),
        'time': timestamp.strftime('%H:%M:%S'),
        'title': title,
        'participants': participants,
        'summary': '',
        'folder': str(meeting_dir.relative_to(meeting_dir.parent.parent)) if meeting_dir.parent.parent.exists() else str(meeting_dir),
        'duration_minutes': duration_mins,
        'source_type': source_type
    }

    log['meetings'].append(entry)

    # Sort by date and time
    log['meetings'].sort(key=lambda m: (m.get('date', ''), m.get('time', '')))

    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)


def is_generic_recording_filename(filename: str) -> bool:
    """Check if filename is a generic recording that needs calendar lookup.

    Detects:
    - Zoom: video1809307269, audio1234567890
    - Voice Memos timestamp: 20251003 130830-0E82E181, 20240525 145751
    - Voice Memos location-based: "University of Pennsylvania 12", "3333 Chestnut St 6"
      (iOS uses location + counter when recording isn't named)
    - Building/location names: "Evans Building", "Academic Research Building"
    - Generic recordings: "New Recording 38"
    """
    import re
    # Zoom: videoNNNNNNNNNN or audioNNNNNNNNNN
    if re.match(r'^(video|audio)\d{8,}$', filename, re.IGNORECASE):
        return True
    # Voice Memos: YYYYMMDD HHMMSS-HEXID or YYYYMMDD HHMMSS
    if re.match(r'^\d{8}\s+\d{6}(-[A-F0-9]+)?$', filename, re.IGNORECASE):
        return True
    # Voice Memos location-based: ends with space + number (counter)
    # e.g., "University of Pennsylvania 12", "McNeil Building 2", "3333 Chestnut St 6"
    if re.match(r'^.+\s+\d{1,3}$', filename):
        return True
    # Building/location names (common iOS Voice Memo auto-titles)
    # e.g., "Evans Building", "Academic Research Building", "The Wistar Institute"
    if re.search(r'\b(Building|Institute|Center|Hall|Library|Stadium|Tower|Plaza|Square|Station|Airport|Hospital|Hotel|Museum|Theater|Theatre|Church|Temple|Mosque|Synagogue|Cathedral)\b', filename, re.IGNORECASE):
        return True
    # Generic "New Recording N" pattern
    if re.match(r'^New Recording\s+\d+$', filename, re.IGNORECASE):
        return True
    return False


def is_zoom_generic_filename(filename: str) -> bool:
    """Check if filename is a Zoom generic video file (e.g., video1809307269)."""
    import re
    # Zoom saves recordings as videoNNNNNNNNNN.mp4 or audioNNNNNNNNNN.m4a
    return bool(re.match(r'^(video|audio)\d{8,}$', filename, re.IGNORECASE))


def extract_zoom_folder_title(recording_path: Path) -> Optional[str]:
    """Extract meeting title from Zoom's parent folder name.

    Zoom saves recordings in folders like:
    '2026-01-22 17.12.06 Claude Builder Club Introduction and Demo'

    Returns the title portion (after date/time), or None if not a Zoom folder.
    """
    import re
    parent_name = recording_path.parent.name

    # Pattern: YYYY-MM-DD HH.MM.SS Meeting Title
    match = re.match(r'^\d{4}-\d{2}-\d{2}\s+\d{2}\.\d{2}\.\d{2}\s+(.+)$', parent_name)
    if match:
        title = match.group(1).strip()
        # Skip generic titles like "Chris Callison-Burch's Personal Meeting Room"
        if "Personal Meeting Room" in title:
            return None
        return title
    return None


def clean_filename_for_folder(filename: str) -> str:
    """Remove dates, timestamps, and common suffixes from filename for folder naming."""
    import re

    name = filename

    # Detect generic recording filenames (Zoom, Voice Memos, etc.)
    if is_generic_recording_filename(name):
        return ''

    # Remove GMT timestamp pattern (GMT20240115-180000)
    name = re.sub(r'\bGMT\d{8}[-_]?\d{6}\b', '', name)

    # Remove common date patterns
    # YYYY-MM-DD, YYYY_MM_DD, YYYYMMDD (8 digits)
    name = re.sub(r'\b\d{4}[-_]?\d{2}[-_]?\d{2}\b', '', name)
    # MM-DD-YYYY, MM_DD_YYYY
    name = re.sub(r'\b\d{2}[-_]\d{2}[-_]\d{4}\b', '', name)

    # Remove time patterns
    # HH.MM.SS, HH-MM-SS, HH:MM:SS -- 1- or 2-digit hour, with an optional AM/PM
    # suffix, since macOS writes "Screen Recording ... at 7.48.08 PM". The AM/PM is
    # consumed here rather than globally, so a real title like "9:30 AM - 11AM"
    # is left alone.
    name = re.sub(r'\b\d{1,2}[.:_-]\d{2}[.:_-]\d{2}\s*(?:AM|PM)?\b', '', name,
                  flags=re.IGNORECASE)
    # HHMMSS (6 digits standalone)
    name = re.sub(r'(?<![a-zA-Z])\d{6}(?![a-zA-Z0-9])', '', name)
    # "at HH.MM" or "at HH:MM", optional AM/PM
    name = re.sub(r'\s+at\s+\d{1,2}[.:]\d{2}\s*(?:AM|PM)?\b', '', name, flags=re.IGNORECASE)

    # Remove common recording-app boilerplate (before trailing-preposition removal).
    # Order matters: longest alternatives first, otherwise a bare "Recording"
    # consumes only that word and leaves the app name stranded. Ecamm dropped
    # "Live" from its filename template ("Ecamm Recording on ..."), which silently
    # broke this and made every such file clean down to the token "Ecamm".
    name = re.sub(
        r'[-_\s]*('
        r'Ecamm Live Recording|Ecamm Recording|Screen Recording|QuickTime Player|'
        r'Recording|Ecamm|Zoom|default'
        r')[-_\s]*',
        ' ', name, flags=re.IGNORECASE)

    # Clean up whitespace and separators
    name = re.sub(r'[-_\s]+', ' ', name)  # normalize separators to spaces
    name = name.strip(' -_')

    # Remove trailing prepositions/articles left over (may need multiple passes)
    while True:
        new_name = re.sub(r'\s+(on|at|the|a|-)\s*$', '', name, flags=re.IGNORECASE)
        if new_name == name:
            break
        name = new_name

    name = name.strip()

    # If nothing but stopwords and app/device boilerplate survived, there is no
    # real title in the filename. Return '' so the caller falls through to the
    # calendar event title and then to the transcript-derived LLM title.
    if len(name) < 3:
        return ''
    meaningless = {'on', 'at', 'the', 'a', 'an', 'in', 'to', 'for', 'of', 'and', 'or', 'with',
                   'am', 'pm', 'ecamm', 'zoom', 'screen', 'recording', 'recordings',
                   'video', 'audio', 'movie', 'untitled', 'new', 'default', 'quicktime'}
    tokens = [t for t in re.split(r'[^A-Za-z0-9]+', name.lower()) if t]
    if tokens and all(t in meaningless for t in tokens):
        return ''

    return name


def create_meeting_folder(output_dir: Path, recording_path: Path,
                          timestamp: datetime, event_title: Optional[str] = None) -> Path:
    """Create a folder for this meeting's outputs.

    If a folder with the same name already exists and contains a transcript,
    looks for an adjacent calendar event to disambiguate, or appends a number.

    Args:
        output_dir: Base output directory
        recording_path: Path to the recording file
        timestamp: Recording timestamp
        event_title: Optional calendar event title to use instead of filename
    """
    # Format: YYYY-MM-DD_title
    date_str = timestamp.strftime('%Y-%m-%d')

    # Prefer event title, fall back to cleaned filename
    if event_title:
        clean_name = event_title.strip()
    else:
        # Clean the filename: remove redundant dates/times and common suffixes
        clean_name = clean_filename_for_folder(recording_path.stem)

    # Truncate if still too long
    if len(clean_name) > 200:
        clean_name = clean_name[:200].rstrip()

    # Combine date with cleaned name
    if clean_name:
        folder_name = f"{date_str}_{clean_name}"
    else:
        # Provisional name. process_recording() renames this folder once the
        # transcript yields an LLM title (needs_llm_title is `not folder_title`,
        # so an empty clean_name is what enables that path). Include the clock
        # time so two untitled recordings on the same day cannot contend for one
        # folder, and so a crashed run leaves an identifiable folder behind.
        # Midnight is excluded: voice memos legitimately carry date-only
        # timestamps, and the deferred-calendar-match path keys off exactly that.
        folder_name = date_str
        if (timestamp.hour, timestamp.minute, timestamp.second) != (0, 0, 0):
            folder_name = f"{date_str}_{timestamp:%H.%M}"

    # Make filesystem-safe (replace problematic chars)
    folder_name = re.sub(r'[<>:"/\\|?*]', '_', folder_name)

    meeting_dir = output_dir / folder_name

    # Anti-overwrite: if folder exists and has a transcript, don't reuse it
    if meeting_dir.exists() and (meeting_dir / 'transcript.json').exists():
        # Try to find an adjacent calendar event with a different title
        try:
            adjacent_events = query_calendar_events(
                timestamp - timedelta(minutes=30),
                timestamp + timedelta(hours=3)
            )
            for evt in adjacent_events:
                evt_title = evt.get('title', '').strip()
                evt_start = evt.get('start')
                if not evt_title or evt_title == event_title:
                    continue
                # Check if this event is adjacent (starts near our timestamp)
                if evt_start and abs((evt_start - timestamp).total_seconds()) < 1800:
                    safe_title = re.sub(r'[<>:"/\\|?*]', '_', evt_title)
                    alt_folder = f"{date_str}_{safe_title}"
                    alt_dir = output_dir / alt_folder
                    if not alt_dir.exists() or not (alt_dir / 'transcript.json').exists():
                        print(f"Folder '{folder_name}' already has a transcript, using adjacent event: {evt_title}")
                        meeting_dir = alt_dir
                        break
        except Exception:
            pass  # Calendar query failed, fall through to numeric suffix

        # If still conflicting, append a number
        if meeting_dir.exists() and (meeting_dir / 'transcript.json').exists():
            for i in range(2, 100):
                alt_dir = output_dir / f"{folder_name} - {i}"
                if not alt_dir.exists() or not (alt_dir / 'transcript.json').exists():
                    print(f"Folder '{folder_name}' already has a transcript, using: {alt_dir.name}")
                    meeting_dir = alt_dir
                    break

    meeting_dir.mkdir(parents=True, exist_ok=True)

    return meeting_dir


# ============================================================================
# Screenshot Capture
# ============================================================================

def find_meeting_screenshots(recording_timestamp: datetime, duration_seconds: float,
                              buffer_seconds: int = 60) -> list[tuple[Path, datetime]]:
    """Find macOS screenshots taken during the meeting time window.

    Uses Spotlight metadata to find screenshots regardless of save location,
    then filters by the meeting's time range (with a buffer).

    Args:
        recording_timestamp: When the recording started
        duration_seconds: Length of the recording in seconds
        buffer_seconds: Extra seconds before/after to include

    Returns:
        Sorted list of (path, capture_time) tuples
    """
    start = recording_timestamp - timedelta(seconds=buffer_seconds)
    end = recording_timestamp + timedelta(seconds=duration_seconds + buffer_seconds)

    # Use Spotlight to find screenshots by metadata
    query = (
        f'kMDItemIsScreenCapture == 1 && '
        f'kMDItemContentCreationDate >= $time.iso({start.strftime("%Y-%m-%dT%H:%M:%S")}) && '
        f'kMDItemContentCreationDate <= $time.iso({end.strftime("%Y-%m-%dT%H:%M:%S")})'
    )
    try:
        result = subprocess.run(
            ['mdfind', query],
            capture_output=True, text=True, timeout=10
        )
        paths = [Path(p) for p in result.stdout.strip().split('\n') if p.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        paths = []

    if not paths:
        # Fallback: glob screenshot directory for matching files
        screenshot_dir = _get_screenshot_directory()
        paths = list(screenshot_dir.glob('Screenshot *.png'))

    # Extract capture time and filter to time range
    screenshots = []
    for path in paths:
        if not path.exists():
            continue
        capture_time = _parse_screenshot_timestamp(path)
        if capture_time and start <= capture_time <= end:
            screenshots.append((path, capture_time))

    screenshots.sort(key=lambda x: x[1])
    return screenshots


def _get_screenshot_directory() -> Path:
    """Get the macOS screenshot save directory."""
    try:
        result = subprocess.run(
            ['defaults', 'read', 'com.apple.screencapture', 'location'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip()).expanduser()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return Path.home() / 'Desktop'


def _parse_screenshot_timestamp(path: Path) -> Optional[datetime]:
    """Parse capture time from a macOS screenshot filename or file metadata.

    macOS screenshots are named like: Screenshot YYYY-MM-DD at H.MM.SS AM.png
    """
    match = re.search(
        r'Screenshot (\d{4}-\d{2}-\d{2}) at (\d{1,2})\.(\d{2})\.(\d{2})\s*(AM|PM)',
        path.name
    )
    if match:
        date_str = match.group(1)
        hour = int(match.group(2))
        minute = int(match.group(3))
        second = int(match.group(4))
        ampm = match.group(5)

        if ampm == 'PM' and hour != 12:
            hour += 12
        elif ampm == 'AM' and hour == 12:
            hour = 0

        try:
            return datetime.strptime(date_str, '%Y-%m-%d').replace(
                hour=hour, minute=minute, second=second
            )
        except ValueError:
            pass

    # Fallback: use file modification time
    try:
        mtime = path.stat().st_mtime
        return datetime.fromtimestamp(mtime)
    except OSError:
        return None


def extract_transcript_context(segments: list[dict], offset_seconds: float,
                                window: int = 120) -> str:
    """Get formatted transcript text around a given time offset.

    Args:
        segments: List of transcript segments with 'start', 'end', 'speaker', 'text'
        offset_seconds: The time offset to center the context around
        window: Seconds before and after to include

    Returns:
        Formatted transcript text for the context window
    """
    start = max(0, offset_seconds - window)
    end = offset_seconds + window
    lines = []
    for seg in segments:
        if seg.get('end', 0) >= start and seg.get('start', 0) <= end:
            speaker = seg.get('speaker', 'UNKNOWN')
            text = seg.get('text', '').strip()
            if text:
                lines.append(f"{speaker}: {text}")
    return '\n'.join(lines) or '(no transcript context available)'


def describe_meeting_screenshots(screenshots: list[tuple[Path, datetime]],
                                  meeting_dir: Path,
                                  segments: list[dict],
                                  recording_timestamp: datetime) -> list[dict]:
    """Copy screenshots into the meeting directory and describe each with an LLM.

    Args:
        screenshots: List of (path, capture_time) tuples
        meeting_dir: Path to the meeting output directory
        segments: Transcript segments for context
        recording_timestamp: When the recording started

    Returns:
        List of manifest entries with filename, timestamp, offset, and description
    """
    import shutil
    import anthropic
    client = anthropic.Anthropic()

    screenshots_dir = meeting_dir / 'screenshots'
    screenshots_dir.mkdir(exist_ok=True)

    manifest = []
    for img_path, capture_time in screenshots:
        # Copy screenshot into meeting directory
        dest = screenshots_dir / img_path.name
        shutil.copy2(str(img_path), str(dest))

        offset = (capture_time - recording_timestamp).total_seconds()
        context = extract_transcript_context(segments, offset)

        # Read image bytes, resize if over 5MB API limit
        img_bytes = img_path.read_bytes()
        MAX_IMAGE_BYTES = 3_900_000  # base64 adds ~33%, so 3.9MB raw → ~5.2MB encoded (under 5MB API limit)
        suffix = img_path.suffix.lower()
        media_type = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
        }.get(suffix, 'image/png')

        if len(img_bytes) > MAX_IMAGE_BYTES:
            try:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(img_bytes))
                # Downscale until JPEG fits under limit
                for quality in [85, 70, 50]:
                    for scale in [1.0, 0.75, 0.5, 0.35]:
                        new_size = (int(img.width * scale), int(img.height * scale))
                        resized = img.resize(new_size, Image.LANCZOS)
                        buf = io.BytesIO()
                        resized.convert('RGB').save(buf, format='JPEG', quality=quality)
                        if buf.tell() <= MAX_IMAGE_BYTES:
                            img_bytes = buf.getvalue()
                            media_type = 'image/jpeg'
                            break
                    if len(img_bytes) <= MAX_IMAGE_BYTES:
                        break
            except ImportError:
                pass  # PIL not available, try sending anyway

        img_b64 = base64.b64encode(img_bytes).decode()

        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": img_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": (
                                "Describe this screenshot from a meeting. "
                                "What is shown and how does it relate to the discussion?\n\n"
                                f"Transcript context around this moment:\n{context}\n\n"
                                "Provide a concise 1-3 sentence description."
                            )
                        }
                    ]
                }]
            )
            description = response.content[0].text.strip()
        except Exception as e:
            description = f"(could not describe: {e})"

        manifest.append({
            'filename': img_path.name,
            'captured_at': capture_time.isoformat(),
            'offset_seconds': round(offset, 1),
            'description': description
        })

    # Save manifest
    with open(screenshots_dir / 'manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)

    return manifest


# ============================================================================
# Main Processing
# ============================================================================

def process_recording(recording_path: Path, args) -> dict:
    """Process a single recording: transcribe, diarize, identify speakers."""

    # Module-level diagnostics dict; reset per recording so batch runs don't
    # carry one recording's calendar/timestamp breadcrumbs into the next.
    PIPELINE_DEBUG.clear()

    # Get HuggingFace token
    hf_token = args.hf_token or os.environ.get('HF_TOKEN')

    # Check minimum duration
    min_duration = getattr(args, 'min_duration', 300)  # Default 5 minutes
    duration = get_media_duration(recording_path)
    if duration > 0 and duration < min_duration:
        print(f"Skipping: {recording_path.name} ({duration:.0f}s < {min_duration}s minimum)")
        if not args.dont_trash_recording:
            trash_file(recording_path)
        return None

    # Get recording timestamp
    timestamp = get_recording_timestamp(recording_path)
    print(f"Recording timestamp: {timestamp}")

    # Check if filename has a meaningful title
    clean_name = clean_filename_for_folder(recording_path.stem)
    has_meaningful_title = bool(clean_name)

    # For Zoom recordings, try to extract title from parent folder first
    zoom_folder_title = extract_zoom_folder_title(recording_path)
    if zoom_folder_title:
        print(f"Using Zoom folder title: {zoom_folder_title}")
        has_meaningful_title = True
        clean_name = zoom_folder_title

    # Always query calendar for events (for attendees and fallback title)
    event_title = None
    matched_event = None

    # Check if timestamp is date-only (time is midnight) - common for Voice Memos
    # Only a high-confidence clock time may drive time-proximity matching on its
    # own; a recovered or estimated one gets confirmed against transcript content.
    ts_confidence = PIPELINE_DEBUG.get('time_of_day_confidence', 'high')
    has_clock_time = (timestamp.hour, timestamp.minute, timestamp.second) != (0, 0, 0)
    is_date_only = not (has_clock_time and ts_confidence == 'high')

    # Track if we need to do deferred event matching after transcription
    deferred_event_matching = False
    day_events = []
    events = []  # Initialize for later use

    if is_date_only:
        # No trusted clock time - search the entire day
        day_start = timestamp.replace(hour=0, minute=0, second=0)
        day_end = timestamp.replace(hour=23, minute=59, second=59)
        day_events = query_calendar_events(day_start, day_end)
        print(f"No trusted clock time ({ts_confidence}) - searching full day "
              f"calendar ({len(day_events)} events found)")

        # A medium-confidence estimate cannot pick an event, but it can rule
        # events out: drop any that cannot overlap the recording at all.
        if day_events and ts_confidence == 'medium' and has_clock_time and duration > 0:
            win_start = timestamp - timedelta(minutes=90)
            win_end = timestamp + timedelta(seconds=duration) + timedelta(minutes=90)
            near = [e for e in day_events
                    if e.get('start') and e.get('end')
                    and e['start'] <= win_end and e['end'] >= win_start]
            if near and len(near) < len(day_events):
                print(f"  Narrowed to {len(near)} event(s) near estimated {timestamp:%H:%M}")
                day_events = near

        events = day_events  # Set events for later use
        if day_events:
            # A single event on the calendar is NOT evidence that this recording
            # IS that event. Many recordings (walking notes, ad-hoc chats, office
            # hours) are deliberately not on the calendar at all. Confirm against
            # transcript content, or match nothing and let a human decide.
            deferred_event_matching = True
            print(f"  Will confirm against transcript content after transcription")
            for i, evt in enumerate(day_events):
                start_str = evt.get('start', datetime.min).strftime('%H:%M') if evt.get('start') else '??:??'
                print(f"  {i+1}. [{start_str}] {evt.get('title', 'Untitled')}")
    else:
        # Normal timestamp - use narrow time window
        events = query_calendar_events(
            timestamp - timedelta(hours=1),
            timestamp + timedelta(hours=2)
        )
        if events:
            # Try keyword matching first if filename has a meaningful title
            if has_meaningful_title:
                keyword_match = match_event_by_title_keywords(
                    recording_path.stem, events,
                    recording_time=timestamp, duration_seconds=duration)
                if keyword_match:
                    matched_event = keyword_match
                    PIPELINE_DEBUG['calendar_match_basis'] = 'filename_keywords'
                    print(f"Matched by filename keywords: {matched_event.get('title')}")
            # Fall back to time-proximity matching
            if not matched_event:
                matched_event = match_recording_to_event(timestamp, events,
                                                         duration_seconds=duration)
                if matched_event:
                    PIPELINE_DEBUG['calendar_match_basis'] = 'time_proximity'

    if matched_event:
        # Use calendar title if we don't have a meaningful title yet
        if not has_meaningful_title and matched_event.get('title'):
            event_title = matched_event['title']
            print(f"Using calendar event title: {event_title}")

    # Determine best title for folder: calendar event > Zoom folder > filename
    folder_title = event_title or zoom_folder_title or (clean_name if has_meaningful_title else None)

    # Create output folder
    meeting_dir = create_meeting_folder(args.output_dir, recording_path, timestamp, folder_title)
    print(f"Output folder: {meeting_dir}")

    # Track if we need to generate a title later
    needs_llm_title = not folder_title

    # Extract audio from video if needed
    if is_video_file(recording_path):
        audio_path = meeting_dir / 'audio.wav'
        extract_audio_from_video(recording_path, audio_path)
    else:
        audio_path = recording_path

    # Load transcription model
    model = load_whisper_model(args.model, args.backend)

    # Transcribe
    condition_on_prev = getattr(args, 'condition_on_previous_text', False)
    transcription = transcribe_audio(audio_path, model,
                                     condition_on_previous_text=condition_on_prev)

    # Deferred event matching for Voice Memos (date-only timestamps)
    # Now that we have the transcript, use LLM to match to calendar events
    if deferred_event_matching and day_events and not matched_event:
        print("\nMatching transcript to calendar events using LLM...")
        transcript_text = transcription.get('text', '')
        matched_event = match_event_by_transcript_content(transcript_text, day_events)
        if matched_event:
            event_title = matched_event.get('title')
            print(f"LLM matched to event: {event_title}")
            # Rename the folder to use the matched event title
            if event_title and needs_llm_title:
                new_folder_title = event_title
                new_meeting_dir = create_meeting_folder(args.output_dir, recording_path, timestamp, new_folder_title)
                if new_meeting_dir != meeting_dir:
                    # Move contents to new folder
                    import shutil
                    for item in meeting_dir.iterdir():
                        shutil.move(str(item), str(new_meeting_dir / item.name))
                    meeting_dir.rmdir()
                    # Update audio_path if it was inside the old folder
                    if audio_path.parent == meeting_dir:
                        audio_path = new_meeting_dir / audio_path.name
                    meeting_dir = new_meeting_dir
                    print(f"Renamed folder to: {meeting_dir}")
                    needs_llm_title = False
        else:
            # No confident calendar match - generate a title from transcript content
            print("No confident calendar match - generating title from transcript...")
            generated_title = generate_meeting_title_from_transcript(transcript_text)
            if generated_title and needs_llm_title:
                print(f"Generated title: {generated_title}")
                new_meeting_dir = create_meeting_folder(args.output_dir, recording_path, timestamp, generated_title)
                if new_meeting_dir != meeting_dir:
                    # Move contents to new folder
                    import shutil
                    for item in meeting_dir.iterdir():
                        shutil.move(str(item), str(new_meeting_dir / item.name))
                    meeting_dir.rmdir()
                    # Update audio_path if it was inside the old folder
                    if audio_path.parent == meeting_dir:
                        audio_path = new_meeting_dir / audio_path.name
                    meeting_dir = new_meeting_dir
                    print(f"Renamed folder to: {meeting_dir}")
                    needs_llm_title = False

    # Diarize if HF token available
    embeddings = {}
    if hf_token:
        pipeline = load_diarization_pipeline(hf_token)
        diarization, embeddings = diarize_audio(
            audio_path, pipeline,
            min_speakers=args.min_speakers,
            max_speakers=args.max_speakers
        )
        transcription = align_transcription_with_diarization(transcription, diarization)
    else:
        print("Warning: No HF_TOKEN - skipping speaker diarization")

    # Load speaker profiles
    profiles = load_speaker_profiles()

    # Match to known profiles by voice embedding
    speaker_names = {}
    if embeddings:
        print("\nMatching speakers to known profiles...")
        speaker_names = match_speakers_to_profiles(embeddings, profiles)

    # Get suggestions from various sources
    suggestions = []
    attendee_details = []  # Store full attendee info for metadata
    email_matched_profiles = {}  # Track profiles matched by email

    # Always use calendar attendees if we have a matched event
    if matched_event:
        print(f"\nCalendar event: {format_event_for_display(matched_event)}")
        attendee_details = get_attendee_details(matched_event)

        # Match profiles to attendees by email
        if attendee_details:
            email_matched_profiles = match_profiles_to_attendees_by_email(profiles, attendee_details)

        # Get attendee names resolved through known_contacts
        attendees = get_attendee_names_from_email(attendee_details)
        if attendees:
            print(f"  Attendees: {', '.join(attendees)}")
            suggestions.extend(attendees)
    elif events:
        # No exact match, but show what was found
        print("\nNo exact calendar match. Nearby events:")
        for evt in events[:3]:
            print(f"  - {format_event_for_display(evt)}")
        # Still gather all attendees as suggestions
        for event in events:
            event_details = get_attendee_details(event)
            attendee_details.extend(event_details)
            suggestions.extend(get_attendee_names_from_email(event_details))

    # Heuristic name detection
    detected_names = detect_names_in_transcript(transcription.get('timestamped', []))
    if detected_names:
        print(f"\nDetected names in transcript: {', '.join(detected_names.keys())}")
    suggestions.extend(detected_names.keys())

    # Remove duplicates
    suggestions = list(dict.fromkeys(suggestions))

    # Process of elimination: if calendar attendees match unidentified speakers count
    if matched_event and embeddings:
        all_speakers = set()
        for seg in transcription.get('timestamped', []):
            speaker = seg.get('speaker', 'UNKNOWN')
            if speaker != 'UNKNOWN':
                all_speakers.add(speaker)

        unidentified = [s for s in all_speakers if s not in speaker_names]
        attendee_names = get_event_attendees(matched_event)
        # Remove already-identified attendees
        unmatched_attendees = [a for a in attendee_names if a not in speaker_names.values()]

        # If exactly one unidentified speaker and one unmatched attendee, match them
        if len(unidentified) == 1 and len(unmatched_attendees) == 1:
            speaker_id = unidentified[0]
            attendee_name = unmatched_attendees[0]
            speaker_names[speaker_id] = attendee_name
            print(f"  Matched {speaker_id} -> {attendee_name} (process of elimination)")

    # Parse --speakers argument if provided (non-interactive mode)
    manual_emails = {}
    if args.speakers:
        print(f"\nUsing provided speaker mapping: {args.speakers}")
        manual_mapping, manual_emails = parse_speaker_arg(args.speakers)
        for speaker_id, name in manual_mapping.items():
            speaker_names[speaker_id] = name
            print(f"  {speaker_id} -> {name}"
                  + (f" <{manual_emails[name]}>" if manual_emails.get(name) else ""))

    # Interactive identification for unmatched speakers (if --interactive or not auto mode)
    interactive_mode = args.interactive or not args.auto
    if interactive_mode and not args.speakers and embeddings:
        print("\nIdentifying speakers...")
        all_speakers = set()
        for seg in transcription.get('timestamped', []):
            all_speakers.add(seg.get('speaker', 'UNKNOWN'))

        unmatched = [s for s in all_speakers if s not in speaker_names and s != 'UNKNOWN']

        for speaker_id in sorted(unmatched):
            name = prompt_speaker_identification(
                transcription.get('timestamped', []),
                speaker_id,
                suggestions
            )
            if name == 'QUIT':
                break
            if name:
                speaker_names[speaker_id] = name

    # Apply speaker names to transcript
    for segment in transcription.get('timestamped', []):
        speaker_id = segment.get('speaker', 'UNKNOWN')
        if speaker_id in speaker_names:
            segment['speaker'] = speaker_names[speaker_id]

    # Update and save profiles (include attendee emails for new profiles)
    if speaker_names and embeddings:
        profiles = update_speaker_profiles(profiles, embeddings, speaker_names,
                                           attendee_details, manual_emails)
        save_speaker_profiles(profiles)

    # Save outputs
    metadata = {
        'source_file': str(recording_path),
        'timestamp': timestamp.isoformat(),
        'duration_seconds': transcription['timestamped'][-1]['end'] if transcription.get('timestamped') else 0,
        'language': transcription.get('language', 'unknown'),
        'speakers': list(set(s.get('speaker', 'UNKNOWN') for s in transcription.get('timestamped', []) if s.get('speaker'))),
        'processed_at': datetime.now().isoformat()
    }

    # Join what the system already knows: each identified speaker's email,
    # taken from the manual --speakers override first, otherwise from the
    # voice profile the speaker was matched to. (Calendar invitee emails
    # already live under calendar_event.attendees; we don't pull from there
    # here because that roster can be a low-confidence / wrong match.)
    _generic_names = ('Unknown', 'UNKNOWN', 'CROSS TALK', 'DEMO VOICE')
    speaker_emails = {}
    for name in set(speaker_names.values()):
        if not name or name in _generic_names or name.startswith('Student '):
            continue
        email = (manual_emails or {}).get(name) \
            or profiles.get('profiles', {}).get(name, {}).get('email')
        if email:
            speaker_emails[name] = email
    if speaker_emails:
        metadata['speaker_emails'] = speaker_emails

    # Diagnostic breadcrumbs: how the timestamp was derived and how the
    # calendar query went, so silent matching failures are inspectable later.
    if PIPELINE_DEBUG:
        metadata['calendar_debug'] = dict(PIPELINE_DEBUG)
        metadata['calendar_debug']['matched'] = bool(matched_event)
        # 'none' means the matcher declined rather than failed to find events -
        # these are the recordings worth asking a human to identify.
        metadata['calendar_debug'].setdefault('calendar_match_basis', 'none')

    # Add calendar event info if matched (attendee_details collected earlier)
    if matched_event:
        metadata['calendar_event'] = {
            'title': matched_event.get('title', ''),
            'start': matched_event['start'].isoformat() if matched_event.get('start') else None,
            'end': matched_event['end'].isoformat() if matched_event.get('end') else None,
            'attendees': attendee_details  # List of {'name': ..., 'email': ...}
        }

    # Save JSON transcript
    with open(meeting_dir / 'transcript.json', 'w') as f:
        json.dump({
            'metadata': metadata,
            'segments': transcription.get('timestamped', [])
        }, f, indent=2)

    # Save text transcript
    text_transcript = format_transcript_with_timestamps(transcription)
    if not getattr(args, 'no_clean_transcript', False):
        text_transcript = clean_transcript_with_llm(text_transcript)
    with open(meeting_dir / 'transcript.txt', 'w') as f:
        f.write(text_transcript)

    # Save metadata
    with open(meeting_dir / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    # Save unidentified speaker embeddings and audio samples to meeting directory
    if embeddings:
        unidentified = {sid: emb for sid, emb in embeddings.items() if sid not in speaker_names}
        if unidentified:
            # Save embeddings JSON (legacy format)
            meeting_profiles = {}
            for speaker_id, embedding in unidentified.items():
                meeting_profiles[speaker_id] = {
                    'embedding': embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding),
                    'created': datetime.now().isoformat()
                }
            with open(meeting_dir / 'unidentified_speakers.json', 'w') as f:
                json.dump(meeting_profiles, f, indent=2)

            # Save audio samples for manual identification
            if getattr(args, 'save_samples', True) and diarization is not None:
                samples_dir = meeting_dir / 'unidentified_speakers'
                samples_data = {}

                print(f"\n💡 Saving audio samples for {len(unidentified)} unidentified speaker(s)...")
                for speaker_id, embedding in unidentified.items():
                    clips = select_speaker_clips(diarization, speaker_id, num_clips=3)
                    if clips:
                        samples_data[speaker_id] = save_speaker_samples(
                            audio_path, samples_dir, speaker_id, clips,
                            transcription, embedding
                        )
                        print(f"   {speaker_id}: {len(clips)} clip(s) saved")

                if samples_data:
                    save_samples_metadata(samples_dir, samples_data)
                    print(f"   Listen in: {samples_dir}")

            print(f"  Saved {len(unidentified)} unidentified speaker embedding(s) to meeting folder")

    print(f"\nSaved transcript to: {meeting_dir}")

    # Collect and describe screenshots taken during the meeting
    duration_secs = metadata.get('duration_seconds', 0)
    is_date_only_ts = (timestamp.hour == 0 and timestamp.minute == 0 and timestamp.second == 0)
    if duration_secs > 0 and not is_date_only_ts:
        screenshots = find_meeting_screenshots(timestamp, duration_secs)
        if screenshots:
            print(f"\nFound {len(screenshots)} screenshot(s) taken during the meeting")
            manifest = describe_meeting_screenshots(
                screenshots, meeting_dir,
                transcription.get('timestamped', []), timestamp
            )
            metadata['screenshots'] = manifest
            # Re-save metadata with screenshots
            with open(meeting_dir / 'metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            for entry in manifest:
                print(f"  [{entry['offset_seconds']:.0f}s] {entry['filename']}: {entry['description'][:80]}")

    # If folder name is just the date, generate a title from transcript with LLM
    if needs_llm_title and text_transcript:
        try:
            generated_title = generate_meeting_title_with_llm(text_transcript)
            if generated_title:
                # Build new folder name
                date_str = timestamp.strftime('%Y-%m-%d')
                new_folder_name = f"{date_str}_{generated_title}"
                # Make filesystem-safe
                new_folder_name = re.sub(r'[<>:"/\\|?*]', '_', new_folder_name)
                if len(new_folder_name) > 200:
                    new_folder_name = new_folder_name[:200].rstrip()
                new_meeting_dir = meeting_dir.parent / new_folder_name
                # Rename if different
                if new_meeting_dir != meeting_dir and not new_meeting_dir.exists():
                    meeting_dir.rename(new_meeting_dir)
                    print(f"Renamed folder to: {new_meeting_dir.name}")
                    meeting_dir = new_meeting_dir
        except Exception as e:
            print(f"  Warning: Could not generate title: {e}")

    # Copy the Zoom chat in, if this meeting had one. Runs after any folder
    # rename so the chat lands in the final directory, and before the recording
    # is trashed. Zoom keeps the chat in its own folder even for calls it did
    # not record, so this works whether the call was captured by Zoom or Ecamm.
    try:
        chat_match = find_zoom_chat_for_recording(recording_path, timestamp, duration)
        chat_info = copy_zoom_chat_into_meeting(meeting_dir, chat_match)
        if chat_info:
            metadata['zoom_chat'] = chat_info
            with open(meeting_dir / 'metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
    except Exception as e:
        print(f"  Warning: Zoom chat lookup failed: {e}")

    # Clean up extracted audio
    if is_video_file(recording_path) and (meeting_dir / 'audio.wav').exists():
        (meeting_dir / 'audio.wav').unlink()

    # Trash original if requested
    if not args.dont_trash_recording:
        trash_file(recording_path)

    # Update meeting log
    update_meeting_log(meeting_dir, metadata, timestamp, recording_path)

    return {
        'meeting_dir': meeting_dir,
        'metadata': metadata,
        'transcription': transcription
    }


# =============================================================================
# Batch Processing
# =============================================================================

def is_recording_processed(recording_path: Path, output_dir: Path) -> bool:
    """Check if a recording has already been processed.

    Looks for an existing output folder matching the recording's date and title.

    Args:
        recording_path: Path to the recording file
        output_dir: Base output directory to check

    Returns:
        True if a matching output folder exists
    """
    if not output_dir.exists():
        return False

    # Get expected folder prefix based on recording date
    from source_handlers import EcammHandler, ZoomHandler, VoiceMemoHandler

    # Determine source type and get timestamp
    filename = recording_path.name.lower()
    parent = recording_path.parent.name.lower()

    if 'ecamm' in str(recording_path).lower():
        handler = EcammHandler()
    elif 'zoom' in parent or 'zoom' in filename:
        handler = ZoomHandler()
    else:
        handler = VoiceMemoHandler()

    try:
        timestamp = handler.get_recording_timestamp(recording_path)
        date_prefix = timestamp.strftime('%Y-%m-%d')
    except Exception:
        return False

    # Check for folders starting with this date
    for folder in output_dir.iterdir():
        if folder.is_dir() and folder.name.startswith(date_prefix):
            # Check if metadata points to this source file
            metadata_file = folder / 'metadata.json'
            if metadata_file.exists():
                try:
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                    source = metadata.get('source_file', '')
                    if recording_path.name in source or source == str(recording_path):
                        return True
                except (json.JSONDecodeError, KeyError):
                    pass

    return False


def discover_all_recordings(args) -> list:
    """Discover recordings from all configured sources.

    Args:
        args: Parsed command line arguments

    Returns:
        List of Recording objects from all sources
    """
    from source_handlers import EcammHandler, ZoomHandler, VoiceMemoHandler

    all_recordings = []

    # Determine which sources to scan
    scan_ecamm = args.process_all or args.process_ecamm
    scan_zoom = args.process_all or args.process_zoom
    scan_voicememos = args.process_all or args.process_voicememos

    if scan_ecamm:
        print("\n📹 Scanning Ecamm recordings...")
        handler = EcammHandler(min_duration=args.min_duration)
        recordings = handler.discover_recordings()
        print(f"  Found {len(recordings)} recordings")
        all_recordings.extend(recordings)

    if scan_zoom:
        print("\n🎥 Scanning Zoom recordings...")
        handler = ZoomHandler(min_duration=args.min_duration)
        recordings = handler.discover_recordings()
        print(f"  Found {len(recordings)} recordings")
        all_recordings.extend(recordings)

    if scan_voicememos:
        print("\n🎙️ Scanning Voice Memos...")
        handler = VoiceMemoHandler(min_duration=args.min_duration)
        recordings = handler.discover_recordings()
        print(f"  Found {len(recordings)} recordings")
        all_recordings.extend(recordings)

    # Sort by timestamp (oldest first)
    all_recordings.sort(key=lambda r: r.timestamp)

    return all_recordings


def process_batch(args) -> dict:
    """Process a batch of recordings from configured sources.

    Args:
        args: Parsed command line arguments

    Returns:
        Dict with 'processed', 'skipped', and 'errors' lists
    """
    results = {
        'processed': [],
        'skipped': [],
        'errors': []
    }

    # Discover recordings
    recordings = discover_all_recordings(args)

    if not recordings:
        print("\nNo recordings found to process.")
        return results

    print(f"\n{'=' * 60}")
    print(f"Found {len(recordings)} total recordings")
    print(f"{'=' * 60}")

    # Filter out already processed
    to_process = []
    for rec in recordings:
        if is_recording_processed(rec.path, args.output_dir):
            results['skipped'].append({
                'path': rec.path,
                'reason': 'already processed'
            })
            if not args.dry_run:
                print(f"  Skipping (already processed): {rec.path.name}")
        else:
            to_process.append(rec)

    if not to_process:
        print("\nAll recordings already processed.")
        return results

    print(f"\n{len(to_process)} recordings to process, {len(results['skipped'])} already done")

    if args.dry_run:
        print("\n[DRY RUN] Would process:")
        for rec in to_process:
            duration_min = int(rec.duration_seconds / 60) if rec.duration_seconds else 0
            print(f"  [{rec.source_type}] {rec.timestamp.strftime('%Y-%m-%d %H:%M')} - {rec.path.name} ({duration_min} min)")
        return results

    # Process each recording
    for i, rec in enumerate(to_process, 1):
        print(f"\n{'=' * 60}")
        print(f"Processing {i}/{len(to_process)}: {rec.path.name}")
        print(f"  Source: {rec.source_type}, Date: {rec.timestamp.strftime('%Y-%m-%d %H:%M')}")
        print(f"{'=' * 60}")

        try:
            result = process_recording(rec.path, args)
            results['processed'].append({
                'path': rec.path,
                'output': result['meeting_dir']
            })
            print(f"\n✓ Completed: {result['meeting_dir'].name}")

        except KeyboardInterrupt:
            print("\n\nCancelled by user.")
            break

        except Exception as e:
            error_msg = str(e)
            results['errors'].append({
                'path': rec.path,
                'error': error_msg
            })
            print(f"\n✗ Error: {error_msg}")

    # Print summary
    print(f"\n{'=' * 60}")
    print("BATCH PROCESSING SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Processed: {len(results['processed'])}")
    print(f"  Skipped:   {len(results['skipped'])}")
    print(f"  Errors:    {len(results['errors'])}")

    if results['errors']:
        print("\nErrors encountered:")
        for err in results['errors']:
            print(f"  - {err['path'].name}: {err['error'][:100]}")

    return results


def main():
    args = parse_args()

    # Handle --list-speakers
    if args.list_speakers:
        list_speaker_profiles()
        return

    # Handle --cleanup-expired-samples
    if getattr(args, 'cleanup_expired_samples', False):
        cleanup_expired_samples(args.output_dir)
        return

    # Handle --relabel
    if args.relabel:
        meeting_dir = Path(args.relabel)
        if not meeting_dir.exists():
            print(f"Error: Meeting directory not found: {meeting_dir}")
            sys.exit(1)

        if not args.speakers:
            print("Error: --relabel requires --speakers mapping")
            print('Example: --relabel "meetings/2026-02-06..." --speakers "SPEAKER_08=Kiril Volkov,SPEAKER_00=Student 1"')
            sys.exit(1)

        # Parse speaker mapping (supports optional "Name <email>" syntax)
        speaker_mapping, speaker_emails = parse_speaker_arg(args.speakers)

        # Get source recording path for enrollment
        source_recording = None
        if args.enroll_relabeled:
            metadata_path = meeting_dir / 'metadata.json'
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                source_recording = Path(metadata.get('source_file', ''))
                if not source_recording.exists():
                    print(f"Warning: Source recording not found: {source_recording}")
                    source_recording = None

        success = relabel_transcript(
            meeting_dir,
            speaker_mapping,
            enroll_speakers=args.enroll_relabeled,
            source_recording=source_recording,
            speaker_emails=speaker_emails
        )
        sys.exit(0 if success else 1)

    # Handle batch processing
    if args.process_all or args.process_ecamm or args.process_zoom or args.process_voicememos:
        try:
            results = process_batch(args)
            if results['errors']:
                sys.exit(1)
            sys.exit(0)
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(1)

    # Require recording for other operations
    if not args.recording:
        print("Error: Recording path required")
        print("Usage: python meeting_transcriber.py <recording.mp4>")
        sys.exit(1)

    recording_path = Path(args.recording)
    if not recording_path.exists():
        print(f"Error: Recording not found: {recording_path}")
        sys.exit(1)

    if not (is_video_file(recording_path) or is_audio_file(recording_path)):
        print(f"Error: Unsupported file format: {recording_path.suffix}")
        print(f"Supported: {VIDEO_EXTENSIONS | AUDIO_EXTENSIONS}")
        sys.exit(1)

    # Process the recording
    try:
        result = process_recording(recording_path, args)
        print("\nDone!")
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(1)
    except Exception as e:
        import traceback; traceback.print_exc(); print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
