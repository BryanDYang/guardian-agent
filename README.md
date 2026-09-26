# Meeting Follow-Through Assistant

Turns meeting recordings into summaries, cited decisions, and action items.

**Repository:** https://github.com/BryanDYang/guardian-agent

## Use Will's backend (easiest)

The backend runs on Will's M4 Mac. To use it from the iOS app, you only need **Will's API key**. Ask him for it privately and never commit it.

```bash
git clone https://github.com/BryanDYang/guardian-agent.git
cd guardian-agent
scripts/use_shared_backend.sh
open ios/MeetingApp/MeetingApp.xcodeproj
```

The script asks for the key, saves it to the gitignored `LabSyncConfig.plist`, and checks the connection. Rebuild the app in Xcode.

To run your own backend instead, follow Setup below.

## Setup

Requires macOS, Python 3.12, and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/BryanDYang/guardian-agent.git
cd guardian-agent
uv sync --locked --extra dev --extra audio --extra server
uv run --locked --extra dev pytest
```

Get the `contexts/meeting_transcriber-master` folder from a teammate and put it in the repo root; audio transcription needs it.

### `.env` and iOS config

```bash
cp .env.example .env
TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
sed -i '' "s|^API_SECRET_KEY=.*|API_SECRET_KEY=$TOKEN|" .env
PLIST=ios/MeetingApp/MeetingApp/LabSyncConfig.plist
cp ios/MeetingApp/LabSyncConfig.example.plist "$PLIST"
plutil -replace BaseURL -string "http://127.0.0.1:8000" "$PLIST"
plutil -replace APIToken -string "$TOKEN" "$PLIST"
```

### Extraction provider (pick one)

```bash
codex login                                   # Codex (default)
```

For Claude, set `LABSYNC_PROVIDER=claude` and `ANTHROPIC_API_KEY=...` in `.env`.

## Run the backend

```bash
uv run --locked --env-file .env --extra audio --extra server labsync serve --whisper-backend mlx
```

Use `--whisper-backend openai` if you are not on Apple Silicon.

- Health check: `curl http://127.0.0.1:8000/api/health`
- API docs: http://127.0.0.1:8000/docs
- iOS app: `open ios/MeetingApp/MeetingApp.xcodeproj`, then run it in the simulator.

See [RUN_UI.md](RUN_UI.md) for the phone/tunnel setup, speaker labels, and troubleshooting.

## CLI without the server

```bash
uv run --locked --extra audio labsync transcribe tests/fixtures/ami/TS3005a-90s-135s.wav \
  --project-id ami-TS3005 --meeting-id TS3005a-90s-135s \
  --whisper-model tiny --whisper-backend mlx --output-dir artifacts/backend-test
uv run --locked --env-file .env labsync extract artifacts/backend-test/transcript.json \
  --output artifacts/backend-test/extraction.json
```

Each `transcribe` run needs a new `--output-dir`.

## Evaluation

```bash
uv run --locked --extra dev pytest tests/benchmarks/
uv run --locked python -m labsync.evaluation run --method rules --directory artifacts/evaluation/rules-new
uv run --locked python -m labsync.evaluation score --directory artifacts/evaluation/rules-new
```

Results: [transcription](docs/milestone_2/transcription_results.md), [extraction](docs/milestone_2/results/README.md).

## Development

```bash
uv run --locked --extra dev ruff check src tests
uv run --locked --extra dev ruff format --check src tests
uv run --locked --extra dev pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [the CCB guide](docs/ccb-transcriber.md), [the integration guide](docs/codex-integration.md), and [the project proposal](docs/milestone_1/project_proposal.md).

## License

[MIT](LICENSE). Third-party code keeps its own license.

**Team:** Bryan Yang, Will Liu, and Guadalupe Cantera · **Course:** CIS-5980, AI Engineering track
