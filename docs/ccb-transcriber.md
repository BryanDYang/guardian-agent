# CCB transcriber integration

The supplied source is `contexts/meeting_transcriber-master`. Its README names
`https://github.com/ccb/meeting_transcriber` as the upstream repository. The archive
has no Git metadata or license file, so its upstream commit is unverified. We
load it locally and do not copy or redistribute its code in the LabSync package.

Audited `meeting_transcriber.py` SHA-256:
`c1f1a342ecf5924d9d92ee9791790ab90d98beef5a0a61377b552235ba1c0fa3`.

## Working audio-to-Codex path

Run from the project root:

```bash
uv sync --locked --extra dev --extra audio
uv run --locked --extra audio labsync transcribe /path/to/meeting.mp3 \
  --source contexts/meeting_transcriber-master \
  --project-id demo --meeting-id meeting-001 \
  --whisper-model base --output-dir artifacts/meeting-001
uv run labsync extract artifacts/meeting-001/transcript.json \
  --model gpt-5.6-sol --output artifacts/meeting-001/extraction.json
```

The first command runs locally. Whisper downloads model weights on first use.
The second uses your Codex login and sends the transcript to Codex. MP4 and other
FFmpeg-readable inputs also work. Each transcription needs a new output directory.

LabSync calls CCB's `load_whisper_model` and `transcribe_audio` directly.
It normalizes the input to a temporary 16 kHz mono WAV and disables conditioning
on previous text, matching the source's normal processing configuration.
`openai` here means local open-source Whisper, not a paid OpenAI transcription API.
The `audio` extra includes an FFmpeg binary fallback if FFmpeg is not on PATH.

It bypasses `process_recording`, whose personal workflow queries calendars,
looks for screenshots/chat files, performs Anthropic calls, and may trash input
recordings. The source is unchanged. Raw transcript text is preserved for
citations; Codex performs downstream extraction instead of transcript cleanup.
No Anthropic or Gemini key is required for this path.

Artifacts:

- `ccb-transcript.json`: CCB-compatible segments in seconds plus run metadata,
  including input audio and CCB script hashes, model, and diarization status.
- `transcript.json`: validated LabSync turns with millisecond timestamps.
- `extraction.json`: validated Codex predictions, usage, and prompt metadata.

## Import an existing CCB result

```bash
uv run labsync import-ccb /path/to/ccb/meeting/transcript.json \
  --project-id demo --meeting-id meeting-001 \
  --output artifacts/meeting-001.json
```

The input must contain `segments` with numeric `start`/`end`, `text`, and
optional `speaker`. Additional upstream metadata is ignored by the importer.
Whitespace-only segments are skipped; other raw text is preserved. IDs use
`<meeting-id>:segment:<original-index>` so skipped segments do not renumber
evidence. Missing speaker labels become `UNKNOWN`; commitment owners cannot be
`UNKNOWN` and remain null unless identified. Milliseconds are rounded from seconds.
Changing the source segmentation changes these IDs, so retain the original artifact.

## Verified run and limits

A 45-second excerpt of AMI TS3005a's mixed-headset recording, from 90s to 135s,
was processed with the actual supplied CCB functions and Whisper `tiny`.
It produced 11 segments, then Codex `gpt-5.6-sol` produced an overview, no
commitments or decisions, and one cited agenda suggestion. Quote and schema
validation passed; that suggestion's usefulness still needs human evaluation.
The clip's source file was preserved. Timestamps are relative to the clip,
not the full AMI meeting.

The [audio fixture](../tests/fixtures/ami/README.md) is included in the repository.
Local results: `artifacts/audio-smoke/ccb-tiny/`. This proves the integration,
not recognition accuracy. The tiny model visibly misrecognized some words.
Use a larger model and human-reviewed references for evaluation.

Attribution: AMI Meeting Corpus, AMI Consortium / Edinburgh CSTR, CC BY 4.0.
[Corpus download and annotations](https://groups.inf.ed.ac.uk/ami/download/),
[license](https://groups.inf.ed.ac.uk/ami/corpus/license.shtml).
The excerpt is cropped, converted to mono/16 kHz, and automatically transcribed.

Speaker diarization was **not run**: no `HF_TOKEN` is configured and pyannote is
not included in the tested `audio` extra. `--diarize` explicitly requires both
the source-compatible pyannote dependencies and accepted Hugging Face model
access; it fails instead of silently falling back. That branch has not been
verified against live models. No speaker recognition, voice enrollment, database
persistence, or cross-meeting reconciliation is implemented by this bridge.
Do not treat the combined UNKNOWN label as evidence that only one person spoke.

## Tests

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest
```

Thirty offline tests pass, including the existing extraction tests and new CCB
format, timestamp, missing speaker, source preservation, and core-function
isolation checks. Offline audio tests use a test double; the public audio run
above separately exercises real CCB/Whisper.
