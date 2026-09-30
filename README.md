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
run scripts/check_tunnel.sh api.guardianagent.dev
open ios/MeetingApp/MeetingApp.xcodeproj
```
Every line should say PASS when you run scripts/check_tunnel.sh api.guardianagent.dev

The script saves the key to the gitignored `LabSyncConfig.plist` and checks that Will's backend is online. Build and run the app in Xcode.

## Option B: Run your own backend (end to end)

**You need:** an Apple Silicon Mac, [Homebrew](https://brew.sh), Xcode, and a Cloudflare login that can manage `guardianagent.dev` (ask Will).

### 1. Get the code and install

```bash
brew install uv cloudflared
git clone https://github.com/BryanDYang/guardian-agent.git
cd guardian-agent
uv sync --locked --extra dev --extra audio --extra server --extra diarize
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

Leave `API_SECRET_KEY` blank; step 5 fills it in. To use Claude instead of Codex, set `LABSYNC_PROVIDER=claude` and `ANTHROPIC_API_KEY=...` in `.env`.

Set `OPENAI_API_KEY` in `.env`.

Speaker labels need a Hugging Face token. Accept the terms for `pyannote/speaker-diarization-3.1` and `pyannote/segmentation-3.0`, then set `HF_TOKEN` in `.env`.

### 4. Connect the database

Projects, meetings, and tasks are stored in Postgres on Supabase. The schema lives in `supabase/migrations/`.

To use the team database, ask Will for the connection string privately and set `DATABASE_URL` in `.env`. Never commit it.

To use your own Supabase project instead, create one at [supabase.com](https://supabase.com), then apply the schema:

```bash
brew install supabase/tap/supabase
supabase login
supabase link --project-ref <your-project-ref>
supabase db push
```

In the Supabase dashboard, click **Connect**, copy the **Session pooler** connection string, fill in your database password, and set it as `DATABASE_URL` in `.env`.

Check the connection:

```bash
uv run --locked --env-file .env --extra server python scripts/check_supabase.py
```

It should end with `Supabase connection OK`. Without `DATABASE_URL`, the backend still transcribes, but the project, meeting, and task endpoints return `503`.

Index existing meetings for chat:

```bash
uv run --locked --env-file .env --extra server labsync index
```

### 5. Set up the Cloudflare tunnel (once per Mac)

Pick your own hostname and tunnel name:

```bash
scripts/setup_tunnel.sh api-yourname.guardianagent.dev labsync-yourname
```

This logs you in to Cloudflare, creates the tunnel, generates `API_SECRET_KEY` in `.env`, and points the iOS app at `https://api-yourname.guardianagent.dev` with the same key.

### 6. Start the backend (Terminal 1)

```bash
uv run --locked --env-file .env --extra audio --extra server --extra diarize labsync serve --whisper-backend mlx --whisper-model medium --diarize
```

The first upload downloads the medium Whisper weights (about 1.5 GB), so it is slow once.

### 7. Start the tunnel (Terminal 2)

```bash
cloudflared tunnel run labsync-yourname
```

### 8. Check everything (Terminal 3)

```bash
scripts/check_tunnel.sh api-yourname.guardianagent.dev
```

Every line should say `PASS`. Each `FAIL` line tells you what to fix.

### 9. Run the app

```bash
open ios/MeetingApp/MeetingApp.xcodeproj
```

Build and run on your iPhone or the simulator. Upload `tests/fixtures/ami/TS3005a-90s-135s.wav` and wait for the transcript and action items to appear.

### After every `git pull`

```bash
git pull
uv sync --locked --extra dev --extra audio --extra server --extra diarize
```

Then repeat steps 6 to 8. Rebuild the app in Xcode if iOS code changed. You do not need to redo steps 2 to 5. If the pull added files under `supabase/migrations/` and you use your own Supabase project, run `supabase db push` again.

More: [RUN_UI.md](RUN_UI.md) covers troubleshooting.

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

### Transcription

[CCB baseline results](docs/milestone_2/transcription_results.md) measure actual
Whisper tiny/base transcription against AMI manual references on 12 one-minute
clips with separate development, validation and test meeting series. Test WER
is 28.79% for tiny and 24.54% for base in this pilot. JiWER scores the outputs;
it is not a competing transcription model.

See the [audio evaluation protocol](tests/fixtures/asr/README.md) for data downloads
and `python -m labsync.asr_evaluation` preparation, inference and scoring commands.
The audio run requires the separately supplied CCB source at
`contexts/meeting_transcriber-master`; it is not bundled in a fresh checkout.
Obtain it from the project team or course sponsor before attempting audio inference.
The supplied archive has no verified upstream commit/license, so it has not been
redistributed. Download AMI inputs using the protocol manifest. Raw audio run
artifacts stay local. The rule-based extraction example below works without CCB,
model credentials, or audio downloads. Use a fresh output directory for each run. Offline benchmark tests use the dev extra.

### Task extraction

[Initial measured results](docs/milestone_2/results/README.md) compare rules,
Codex and local Granite Code 8B on 24 synthetic development cases. Run the
offline scorer tests and a fresh rule baseline:

```bash
uv run --locked --extra dev pytest tests/benchmarks/
uv run --locked python -m labsync.evaluation run --method rules \
  --directory artifacts/evaluation/rules-new
uv run --locked python -m labsync.evaluation score \
  --directory artifacts/evaluation/rules-new
```

Example score output from the saved `rules-v1` run (metric rows excerpted):

```text
Method: rules; model: None.
Scorer: action-terms-v1.

| Metric | Numerator / denominator | Value |
| --- | --- | --- |
| task_precision_proxy | 11/16 | 0.688 |
| task_recall_proxy | 11/15 | 0.733 |
| task_f1_proxy | 22/31 | 0.710 |
| negative | 9/11 | 0.818 |

Failed/missing cases: 0.
```

[Saved scoring evidence](docs/milestone_2/results/slice_results.json) includes
all three v1 scoring reports and per-case counts, so inspecting these results
does not require credentials or live inference. [Scenario slices](docs/milestone_2/results/slices.md)
include exact membership and denominators. The [human review packet](docs/milestone_2/failure_review.md)
and [compact log](docs/milestone_2/failure_review_log.md) are prepared; human ratings remain pending.

See the [fixture protocol](tests/fixtures/evaluation/README.md) for live inference,
annotation rules, matching and metric definitions. Labels are AI-authored pending
human review; the reported action-matching scores are development proxies.
This implements the extraction portion of [checklist Phase 5](docs/checklist.md).

## Development

```bash
uv run --locked --extra dev ruff check src tests
uv run --locked --extra dev ruff format --check src tests
uv run --locked --extra dev pytest
```

The database tests are skipped unless `TEST_DATABASE_URL` is set. Run them against a local Supabase database (needs Docker running), never the real project. `supabase start` applies the migrations:

```bash
supabase start
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres \
  uv run --locked --extra dev --extra server pytest
supabase stop
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [the CCB guide](docs/ccb-transcriber.md), [the integration guide](docs/codex-integration.md), and [the project proposal](docs/archive/milestone_1/project_proposal.md).

## License

[MIT](LICENSE). Third-party code keeps its own license.

**Team:** Bryan Yang, Will Liu, and Guadalupe Cantera · **Course:** CIS-5980, AI Engineering track