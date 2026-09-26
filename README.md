# Meeting Follow-Through Assistant

Turns meeting recordings into summaries, cited decisions, and action items.

**Repository:** https://github.com/BryanDYang/guardian-agent

**Pipeline:** iOS app uploads audio → Cloudflare Tunnel → backend on a Mac → Whisper (medium) transcribes → Codex or Claude extracts decisions and action items → results show up in the app.

Pick one:

- **Option A:** use Will's backend. You only need the iOS app and his API key.
- **Option B:** run the whole pipeline on your own Mac.

## Option A: Use Will's backend

Ask Will for the API key privately. Never commit it.

```bash
git clone https://github.com/BryanDYang/guardian-agent.git
cd guardian-agent
scripts/use_shared_backend.sh
open ios/MeetingApp/MeetingApp.xcodeproj
```

The script saves the key to the gitignored `LabSyncConfig.plist` and checks that Will's backend is online. Build and run the app in Xcode.

## Option B: Run your own backend (end to end)

**You need:** an Apple Silicon Mac, [Homebrew](https://brew.sh), Xcode, and a Cloudflare login that can manage `guardianagent.dev` (ask Will).

### 1. Get the code and install

```bash
brew install uv cloudflared
git clone https://github.com/BryanDYang/guardian-agent.git
cd guardian-agent
uv sync --locked --extra dev --extra audio --extra server
```

### 2. Add the transcriber

Get the `contexts/meeting_transcriber-master` folder from a teammate and put it in the repo root. It is gitignored, so `git pull` will not bring it. Check it is in place:

```bash
ls contexts/meeting_transcriber-master/meeting_transcriber.py
```

### 3. Create `.env` and log in to the extraction model

```bash
cp .env.example .env
codex login        # if codex is missing: npm install -g @openai/codex
```

Leave `API_SECRET_KEY` blank; step 4 fills it in. To use Claude instead of Codex, set `LABSYNC_PROVIDER=claude` and `ANTHROPIC_API_KEY=...` in `.env`.

### 4. Set up the Cloudflare tunnel (once per Mac)

Pick your own hostname and tunnel name:

```bash
scripts/setup_tunnel.sh api-yourname.guardianagent.dev labsync-yourname
```

This logs you in to Cloudflare, creates the tunnel, generates `API_SECRET_KEY` in `.env`, and points the iOS app at `https://api-yourname.guardianagent.dev` with the same key.

### 5. Start the backend (Terminal 1)

```bash
uv run --locked --env-file .env --extra audio --extra server labsync serve --whisper-backend mlx --whisper-model medium
```

The first upload downloads the medium Whisper weights (about 1.5 GB), so it is slow once.

### 6. Start the tunnel (Terminal 2)

```bash
cloudflared tunnel run labsync-yourname
```

### 7. Check everything (Terminal 3)

```bash
scripts/check_tunnel.sh api-yourname.guardianagent.dev
```

Every line should say `PASS`. Each `FAIL` line tells you what to fix.

### 8. Run the app

```bash
open ios/MeetingApp/MeetingApp.xcodeproj
```

Build and run on your iPhone or the simulator. Upload `tests/fixtures/ami/TS3005a-90s-135s.wav` and wait for the transcript and action items to appear.

### After every `git pull`

```bash
git pull
uv sync --locked --extra dev --extra audio --extra server
```

Then repeat steps 5 to 7. Rebuild the app in Xcode if iOS code changed. You do not need to redo steps 2 to 4.

More: [RUN_UI.md](RUN_UI.md) covers speaker labels and troubleshooting.

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

See [CONTRIBUTING.md](CONTRIBUTING.md), [the CCB guide](docs/ccb-transcriber.md), [the integration guide](docs/codex-integration.md), and [the project proposal](docs/archive/milestone_1/project_proposal.md).

## License

[MIT](LICENSE). Third-party code keeps its own license.

**Team:** Bryan Yang, Will Liu, and Guadalupe Cantera · **Course:** CIS-5980, AI Engineering track
