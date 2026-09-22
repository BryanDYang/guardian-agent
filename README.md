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

## Audio with CCB's transcriber

The supplied source in `contexts/meeting_transcriber-master` now connects to
Codex extraction. See [the audio integration guide](docs/ccb-transcriber.md)
for installation and commands. The verified path preserves recordings and raw
transcripts; speaker diarization remains an unverified optional step.

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
