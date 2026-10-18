> **Historical design/reference:** Preserved for rationale and context. Use [current architecture](../../architecture.md) for implementation and [the roadmap](../../milestone_3/roadmap.md) for current work.

# meeting_transcriber

A command-line tool for transcribing meeting recordings with speaker diarization and identification. Designed for personal use on macOS: feed it a Zoom recording, voice memo, or screen capture, and it produces a timestamped transcript with named speakers — using a combination of voice fingerprinting and the attendee list from your macOS Calendar.

```
[00:01:23] Chris: Hey everyone, thanks for coming.
[00:01:27] Jane: Good to be here.
[00:01:30] Chris: So the main thing I wanted to discuss today...
```

## Features

- **Whisper transcription** with MLX-Whisper acceleration on Apple Silicon (3–4× faster than CPU OpenAI Whisper)
- **Speaker diarization** via `pyannote.audio` — separates speakers turn-by-turn
- **Persistent voice profiles** — once you label a speaker, future meetings auto-identify them by voice (x-vector embeddings, cosine similarity)
- **Calendar integration** — pulls attendees from your macOS Calendar event matching the recording time, uses them as ID candidates
- **Email-based profile matching** — links calendar attendees to known voice profiles by email
- **Heuristic name detection** — picks up "hi Hana", "thanks Dana" from the transcript
- **LLM post-processing** (optional) — uses Claude to fix proper nouns, punctuation, and filler removal
- **Source handlers** for Zoom, Ecamm, and iOS Voice Memos — handles each app's quirks (filename parsing, date extraction, multi-part recordings)
- **Interactive prompts** for unknown speakers, or `--auto` mode for batch processing
- **Safe file handling** — recordings move to Trash by default (recoverable), never permanent-deleted

## Requirements

- **macOS** (Calendar integration uses the macOS EventKit bridge). Most of the pipeline works on Linux/Windows but without calendar support.
- **Python 3.10+**
- **ffmpeg** — `brew install ffmpeg`
- **HuggingFace account** with accepted `pyannote/speaker-diarization-3.1` license — set `HF_TOKEN` in your environment
- **(Optional) Anthropic API key** for LLM transcript cleanup — set `ANTHROPIC_API_KEY`


Create a `.env` file in the repo root:

```
HF_TOKEN=hf_...
ANTHROPIC_API_KEY=sk-ant-...
```

The first run will prompt for macOS Calendar access — grant it in System Settings → Privacy & Security.

## Quick start

```bash
# Transcribe a Zoom recording with calendar attendee matching
python meeting_transcriber.py recording.mp4 --match-calendar

# Voice memo from iOS
python meeting_transcriber.py "Meeting Notes.m4a" --match-calendar

# Batch-process new recordings from all configured sources (Zoom + Ecamm + Voice Memos)
python meeting_transcriber.py --process-all

# List known speakers in your voice profile database
python meeting_transcriber.py --list-speakers

# Manually enroll someone from a recording (when calendar match doesn't help)
python meeting_transcriber.py recording.mp4 --enroll "John Smith"
```

### Output structure

Each transcribed meeting becomes a folder under `meetings/`:

```
meetings/
├── speaker_profiles.json                # Global voice embedding database
└── 2026-05-18_PrairieLearn agentic skill/
    ├── metadata.json                    # Meeting info, attendees, source, calendar event
    ├── transcript.json                  # Full timestamped, diarized transcript
    └── transcript.txt                   # Human-readable: [00:01:23] John: Hello…
```

## Common workflows

### Interactive speaker identification (default)

```bash
python meeting_transcriber.py recording.mp4 --interactive --match-calendar
```

For each unknown speaker, the tool shows a short transcript excerpt and prompts you to name them (or skip with Enter). Once named, the voice profile is saved and used to auto-identify them in future meetings.

### Auto mode (batch / unattended)

```bash
python meeting_transcriber.py recording.mp4 --auto
```

Skips prompts; unknown speakers are saved as `SPEAKER_00`, `SPEAKER_01`, etc. You can relabel later (see below).

### Non-interactive with known mappings

```bash
python meeting_transcriber.py recording.mp4 \
    --speakers "SPEAKER_00=John Smith,SPEAKER_01=Jane Doe"
```

### Relabel an existing transcript

If a meeting was processed with `SPEAKER_XX` labels and you want to retroactively name people:

```bash
python meeting_transcriber.py \
    --relabel "meetings/2026-02-06_08-43_Meeting Name" \
    --speakers "SPEAKER_08=Kiril Volkov,SPEAKER_00=Student 1"
```

Add `--enroll-relabeled` to also save those voice embeddings to the speaker profile DB (skips generic names like "Student 1"):

```bash
python meeting_transcriber.py \
    --relabel "meetings/2026-02-06_08-43_Meeting Name" \
    --speakers "SPEAKER_08=Kiril Volkov" --enroll-relabeled
```

### Batch processing

Process all new recordings from configured sources:

```bash
python meeting_transcriber.py --process-all          # all sources
python meeting_transcriber.py --process-ecamm        # Ecamm Live only
python meeting_transcriber.py --process-zoom         # Zoom only
python meeting_transcriber.py --process-voicememos   # iOS Voice Memos only
python meeting_transcriber.py --process-all --dry-run # show what would be processed
```

A meeting log (`meetings/meeting_log.json`) tracks what's been processed to avoid duplicates.

## Selected CLI flags

| Flag | Effect |
|------|--------|
| `--model {turbo,large,...}` | Whisper model (default `turbo`) |
| `--backend {auto,mlx,openai}` | Force a specific backend |
| `--auto` / `--interactive` | Skip prompts vs. ask for unknown speakers |
| `--match-calendar` | Pull attendee names from macOS Calendar |
| `--speakers "SPEAKER_00=Alice,..."` | Pre-specify speaker mappings |
| `--enroll NAME` | Add a single speaker to the voice DB from this recording |
| `--relabel DIR` | Relabel speakers in an existing transcript |
| `--enroll-relabeled` | Also enroll voice profiles when relabeling |
| `--list-speakers` | Show known speakers in the voice DB |
| `--no-clean-transcript` | Skip LLM cleanup (faster, lower-quality) |
| `--clean-transcript` | Force LLM cleanup |
| `--condition-on-previous-text` | Revert to old Whisper behavior |
| `--output-dir DIR` | Where to save transcripts (default `meetings/`) |
| `--dont-trash-recording` | Keep the original recording (default: move to Trash) |
| `--min-duration SECS` | Skip recordings shorter than this (default 300s) |

Full flag list: `python meeting_transcriber.py --help`.

## Architecture overview

Single-file CLI (`meeting_transcriber.py`) plus a few support modules:

| Module | Purpose |
|--------|---------|
| `meeting_transcriber.py` | Main CLI, transcription, diarization, speaker ID |
| `source_handlers/` | Per-source quirks (Ecamm, Zoom, Voice Memos) — filename parsing, date extraction, multi-part handling |
| `contacts.py` | Email ↔ speaker profile resolution |
| `meeting_log.py` | Tracks processed meetings to avoid duplicates |
| `backfill_meeting_log.py` | One-off: populate the log from existing `meetings/` folders |

**Pipeline:**

1. Detect source type (Zoom / Ecamm / Voice Memo / generic)
2. Extract audio if input is video (ffmpeg)
3. Convert to WAV for pyannote (works around a pyannote tensor bug with some formats)
4. Transcribe with Whisper / MLX-Whisper
5. Diarize with pyannote (produces SPEAKER_00, SPEAKER_01, …)
6. Align transcript segments with diarization turns
7. Speaker identification:
   - Match each speaker's embedding against `speaker_profiles.json` (cosine similarity)
   - Query macOS Calendar for the meeting → get attendee names
   - Parse transcript for heuristic names ("hi Hana", "thanks Dana")
   - For unmatched speakers: prompt user (or fall back to SPEAKER_XX in `--auto`)
8. Auto-enroll confirmed speakers into the voice profile database
9. LLM post-processing for proper nouns, punctuation, filler (optional)
10. Save `transcript.json` + `transcript.txt` + `metadata.json`
11. Move source recording to Trash (default) or keep it (`--dont-trash-recording`)

## Known constraints

- `pyannote` requires a HuggingFace token *and* you must accept the model license at `huggingface.co/pyannote/speaker-diarization-3.1`
- `pyannote` has tensor bugs with some formats — the pipeline always converts to WAV first
- macOS Calendar access requires user permission grant on first run
- Optimized for 2–5 speakers; larger meetings may have reduced diarization accuracy
- Calendar integration is macOS-only; everything else is cross-platform

## Privacy

- Voice embeddings and transcripts are stored locally under `meetings/`
- `meetings/` is in `.gitignore` — your data is never pushed to git
- The Anthropic API is only called if you have `ANTHROPIC_API_KEY` set; transcripts sent to it are processed per [Anthropic's data policy](https://www.anthropic.com/legal/privacy)
- pyannote runs entirely locally (no audio sent to any service)

## License

No license file is included. If you'd like to use this beyond personal experimentation, please contact the author.

## Acknowledgements

Built on:
- [OpenAI Whisper](https://github.com/openai/whisper) and [MLX-Whisper](https://github.com/ml-explore/mlx-examples) for transcription
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) for speaker diarization
- [Anthropic Claude](https://www.anthropic.com) for transcript post-processing
