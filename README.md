# Meeting Follow-Through Assistant

Turns meeting recordings into summaries, cited decisions, and action items.

**Repository:** https://github.com/BryanDYang/guardian-agent

**Pipeline:** iOS app uploads audio → Cloudflare Tunnel → backend on a Mac → Whisper (medium) transcribes → Codex or Claude extracts decisions and action items → results show up in the app.

Pick one:

- **Option A:** use Will's backend. You only need Xcode.
- **Option B:** run the whole pipeline on your own Mac.

## Option A: Use Will's backend

1. Send Will the email you will sign up with. He adds you to the Supabase team and the Google sign-in test users.
2. Accept the Supabase team invite in your email.
3. Ask Will for the Supabase URL and anon key.
4. Run:

```bash
git clone https://github.com/BryanDYang/guardian-agent.git
cd guardian-agent
scripts/use_shared_backend.sh
scripts/check_tunnel.sh --shared api.guardianagent.dev
open ios/MeetingApp/MeetingApp.xcodeproj
```

Every line should say `PASS`.

5. Build and run the app in Xcode.
6. Sign up with the email from step 1, or tap **Continue with Google**.
7. Click the link in the confirmation email, then log in.
8. Record your voice or tap **Skip for now**.
9. Ask Will to invite you to a project. Accept it in **Profile > Workspaces**.

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

To use Claude instead of Codex, set `LABSYNC_PROVIDER=claude` and `ANTHROPIC_API_KEY=...` in `.env`.

Set `OPENAI_API_KEY` in `.env`.

Speaker labels need a Hugging Face token. Accept the terms for `pyannote/speaker-diarization-3.1` and `pyannote/segmentation-3.0`, then set `HF_TOKEN` in `.env`.

### 4. Connect Supabase

**Team project:** ask Will for the values in the table below.

**Your own project:** create one at [supabase.com](https://supabase.com), then run:

```bash
brew install supabase/tap/supabase
supabase login
supabase link --project-ref <your-project-ref>
supabase db push
```

Then add `meetingmemory://auth-callback` under **Authentication > URL Configuration > Redirect URLs**.

Set these in `.env`. Never commit `.env`.

| Variable | Where to find it |
| --- | --- |
| `DATABASE_URL` | **Connect > Session pooler**, with your database password filled in |
| `SUPABASE_URL` | **Project Settings > Data API > Project URL** |
| `SUPABASE_ANON_KEY` | **Project Settings > API Keys > Legacy anon, service_role API keys > anon** |
| `SUPABASE_JWT_SECRET` | Only if the current key in **Project Settings > JWT Keys** is HS256 |

Check the connection:

```bash
uv run --locked --env-file .env --extra server python scripts/check_supabase.py
```

It should end with `Supabase connection OK`.

Index existing meetings for chat:

```bash
uv run --locked --env-file .env --extra server labsync index
```

### 5. Set up the Cloudflare tunnel (once per Mac)

Pick your own hostname and tunnel name:

```bash
scripts/setup_tunnel.sh api-yourname.guardianagent.dev labsync-yourname
```

This logs you in to Cloudflare, creates the tunnel, and points the iOS app at `https://api-yourname.guardianagent.dev` and at the Supabase project in `.env`.

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

Build and run on your iPhone or the simulator. Sign up, confirm your email, and create a project. Upload `tests/fixtures/ami/TS3005a-90s-135s.wav` and wait for the transcript and action items to appear.

### After every `git pull`

```bash
git pull
uv sync --locked --extra dev --extra audio --extra server --extra diarize
```

Then repeat steps 6 to 8. Rebuild the app in Xcode if iOS code changed. You do not need to redo steps 2 to 5. If the pull added files under `supabase/migrations/` and you use your own Supabase project, run `supabase db push` again.

### Run without speaker labels

To run without diarization, omit `--extra diarize` and `--diarize`:

```bash
uv run --locked --env-file .env --extra audio --extra server labsync serve --whisper-backend mlx --whisper-model medium
```

## Troubleshooting

Logs: `artifacts/server/<meeting-id>/processing.log`

| Symptom | Fix |
| --- | --- |
| "Sign in to continue", or sent back to Log In | Will's backend: re-run `scripts/use_shared_backend.sh` and rebuild. Own backend: make `SUPABASE_URL` in `.env` match `SupabaseURL` in `LabSyncConfig.plist`, then restart the server with `--env-file .env` |
| "Email not confirmed" | Click the link in the confirmation email. No email: ask Will to add you to the Supabase team |
| Google "Access blocked" | Ask Will to add your Google account as a test user |
| No projects after sign-in | Ask a project member to invite you, then accept in **Profile > Workspaces** |
| "Invalid host header" | Re-run `scripts/setup_tunnel.sh` |
| HTTP 502 | Start the backend |
| HTTP 530 | Start `cloudflared tunnel run` |
| "Transcribing failed" | Add `contexts/meeting_transcriber-master` (README step 2) |
| "Extracting failed" | Run `codex login` or fix `ANTHROPIC_API_KEY` |
| First upload is slow | The medium Whisper weights (about 1.5 GB) download on first use |
| Upload over 100 MB fails | Cloudflare plan limit |

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

[CCB baseline results](docs/archive/milestone_2/transcription_results.md) measure actual
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

### Action-item extraction evaluation

These commands reproduce the offline evaluation of action items extracted from transcripts. They are for comparing extraction methods, rather than running the app.

[Initial measured results](docs/archive/milestone_2/results/README.md) compare rules,
Codex and local Qwen3 8B on 24 synthetic development cases. Run the
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

[Saved scoring evidence](docs/archive/milestone_2/results/slice_results.json) includes
all three v1 scoring reports and per-case counts, so inspecting these results
does not require credentials or live inference. [Scenario slices](docs/archive/milestone_2/results/slices.md)
include exact membership and denominators. The [human review packet](docs/archive/milestone_2/human_review.md)
and [review log](docs/archive/milestone_2/human_review_log.md) cover all 72 outputs with one verified review; a 12-output spot check is pending.

See the [fixture protocol](tests/fixtures/evaluation/README.md) for live inference,
annotation rules, matching and metric definitions. Labels are AI-authored pending
human review; the reported action-matching scores are development proxies.
This implements the extraction portion of [checklist Phase 5](docs/checklist.md).

## Contributor checks

Run these checks after changing the backend code:

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