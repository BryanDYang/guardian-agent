# Meeting Follow-Through Assistant

A proposed assistant that turns meeting recordings into summaries, cited decisions, and a living action-item list that updates across later meetings.

The Python CLI imports AMI transcripts and extracts summaries, cited decisions,
commitments, and suggestions using a local Codex login. The optional CCB bridge
transcribes audio locally with Whisper. Database persistence and the background
service are not implemented yet. See the
[Milestone 1 proposal](docs/milestone_1/project_proposal.md) for the planned scope.

**Repository:** https://github.com/BryanDYang/guardian-agent

## Quick start

Install Python 3.12 and uv, then run:

```bash
git clone https://github.com/BryanDYang/guardian-agent.git
cd guardian-agent
uv sync --locked --extra dev
uv run labsync --help
uv run labsync status
uv run labsync status --json
```

Status and offline tests need no API keys, meeting data, or `contexts` files.

## First extraction with Codex

Install the Codex CLI and run `codex login`, then:

```bash
uv run labsync extract tests/fixtures/meeting.json \
  --model gpt-5.6-sol --output artifacts/synthetic-codex.json
```

This sends the transcript to Codex using your saved login and consumes model
usage. Select a model your account can access. The command checks the output
schema, quoted evidence, and owner labels before saving JSON with run metadata.
It refuses to overwrite an existing output. This is an extraction prototype,
not an accuracy benchmark or an audio transcription service.

See [the integration guide](docs/codex-integration.md) for AMI download/import
commands, the CCB source audit, database mapping, and current limitations.

## Test the audio backend

The backend is currently a CLI pipeline; there is no HTTP server to start.
From the project root, with CCB's source at `contexts/meeting_transcriber-master`:

```bash
uv sync --locked --extra dev --extra audio
uv run --locked --extra dev pytest
uv run --locked --extra audio labsync transcribe \
  tests/fixtures/ami/TS3005a-90s-135s.wav \
  --project-id ami-TS3005 --meeting-id TS3005a-90s-135s \
  --whisper-model tiny --output-dir artifacts/backend-test
```

The tests run offline. Transcription processes the included 45-second audio clip
locally and downloads Whisper weights on first use. It writes raw CCB output to
`artifacts/backend-test/ccb-transcript.json` and normalized turns to
`artifacts/backend-test/transcript.json`. Speaker labels remain UNKNOWN unless
speaker diarization is configured. Use a fresh output directory for each run.

Then check your Codex login and extract meeting information:

```bash
codex login status
uv run --locked labsync extract artifacts/backend-test/transcript.json \
  --model gpt-5.6-sol --output artifacts/backend-test/extraction.json
cat artifacts/backend-test/extraction.json
```

Run `codex login` if needed. This step sends the generated transcript to Codex.
Success means a saved, validated extraction containing `summary`, `decisions`,
`commitments`, and `suggestions`. This opening/agenda clip may have no commitments;
empty lists are valid. Database writes and UI binding are not implemented yet.
See [the audio integration guide](docs/ccb-transcriber.md) for more details.

### Environment warning after the folder rename

If `VIRTUAL_ENV` still references `ai-capstone/.venv`, run `deactivate` in the
terminal where that environment is active, or open a fresh terminal. Use `uv run`
without activating `.venv`; the old activation script also contains the previous
path. Do not use `--active` to target the obsolete environment.

The dev-only quick start is sufficient for offline tests. `uv sync --extra dev`
omits the optional audio extra and removes its packages. For audio testing, use
`uv sync --locked --extra dev --extra audio` and include `--extra audio` on
transcription commands so they also work after a dev-only sync.

## Visible test data

- [AMI audio fixture](tests/fixtures/ami/README.md): a 45-second mixed-speaker WAV,
  with attribution, provenance, and commands for automatic transcription.
- [Synthetic transcript](tests/fixtures/meeting.json): a small text-only fixture
  for testing extraction without audio processing.

Full AMI downloads and generated outputs stay local. ICSI is not yet included.

## Development

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest
```

CI runs these checks and the installed CLI on every push and pull request.
Application code lives in `src/labsync`, tests in `tests`, and project documents
in `docs`. See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow
and [upstream provenance](docs/upstream.md) for how the professor's
`agent-sandbox` informed this setup.

## License

Project code uses the [MIT license](LICENSE). Third-party code and assets retain
their own licenses and notices.

**Team:** Bryan Yang, Will Liu, and Guadalupe Cantera

**Course:** CIS-5980, AI Engineering track

Previous project materials are retained in [the guardian-agent archive](docs/archive/guardian-agent/). They describe a superseded direction. The [weekly journal](docs/weekly_journal.md) preserves historical progress; its earlier entries refer to that direction.
