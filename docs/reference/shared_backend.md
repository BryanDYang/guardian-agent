# Shared backend rollout

Shared mode lets two backends use the same private audio bucket and database
jobs. Each worker processes one meeting at a time. New uploads can be processed,
polled, retried, and played through either backend. Local mode remains the default.
This implements shared state and job recovery, not automatic hostname failover.

## Set up a separate test environment first

1. Use a separate Supabase project for acceptance testing. Apply all migrations,
   including `supabase/migrations/20261010000000_shared_processing.sql`, with
   `supabase db push` against that project's explicit link. Do not apply migrations
   to the team project until the team coordinates the rollout.
2. Set `DATABASE_URL` and `SUPABASE_URL` to that same project on both machines.
   Use the same code version, model/provider settings, and required model keys.
3. Set `SUPABASE_SERVICE_ROLE_KEY` on each backend only. This privileged key is
   separate from the public anon key and must never go in the app or Git.
   The migration creates the private `meeting-audio` bucket; no direct client
   Storage policies are granted. Startup rejects a public bucket. Confirm the
   project-wide Storage upload limit accommodates your recordings as well as the
   bucket limit; upstream tunnel upload limits still apply.
4. Install the usual audio/server/diarization extras and transcriber source.
   Configure model logins on each machine. Use a unique worker ID per process.
5. Start each backend, using separate local scratch directories when testing two
   processes on one Mac:

   ```bash
   uv run --locked --env-file .env --extra audio --extra server --extra diarize \
     labsync serve --shared --worker-id bryan-mac --port 8000 \
     --storage artifacts/shared-bryan --whisper-backend mlx \
     --whisper-model medium --diarize
   ```

   On Will's Mac use `--worker-id will-mac` and his normal local port. For a second
   process on your Mac use a different ID, `--port 8001`, and another scratch path.
   Existing startup without `--shared` continues using local files and its local
   worker. Avoid mixing shared/local servers behind one load balancer.

## What changes in shared mode

- Audio uses stable keys `project_id/meeting_id/recording.ext` in private Storage.
  The DB stores the object reference, not another host's filesystem path.
- The upload is recorded durably before object publication. Only a successful
  upload queues processing. Interrupted uploads older than one hour are removed
  and their objects are scheduled for cleanup. They do not become completed jobs.
- PostgreSQL claims serialize processing within each project in upload order;
  separate projects may run concurrently. Claims use `FOR UPDATE SKIP LOCKED`,
  a fresh token, and a 120-second
  lease. Heartbeats renew every 40 seconds. A dead worker's job becomes claimable
  after expiry, and its processing attempt increments. A superseded worker cannot
  publish results. No connection is held during transcription/model inference.
- Results, retrieval indexing, meeting status, and job completion commit in one
  fenced transaction. Failed attempts can be retried through either backend.
- Polling on `/api/meetings/{id}` uses DB state and result snapshots. Temporary
  processing files are host-local scratch, not the source of truth.
- The audio endpoint checks project membership before redirecting to a 60-second
  signed Storage URL. That URL is a temporary bearer capability; do not share it.
- Purge/project/account deletion enqueue object cleanup in the DB transaction.
  Either worker can execute cleanup. Storage deletion is eventual; a previously
  issued signed URL may remain usable briefly. Cleanup waits when workers are
  processing; DB deletion does not mean Storage cleanup already finished.
- Health checks verify database access, a private reachable bucket, and that the
  worker thread is alive. They do not prove model-provider availability.
- Optional upload header `Idempotency-Key: <UUID>` makes repeated requests for the
  same user/project/content return the existing meeting. Reuse with changed
  content returns 409; an upload still in progress returns 409 with Retry-After.
  Clients must retain the key across retries. The current iOS client does not yet
  supply this header, so an interrupted upload may require checking the list
  before uploading again.

## Failure acceptance test

Use the same signed-in account and a dedicated development project on both URLs.

1. Upload on backend A; poll the returned meeting ID on backend B.
2. Stop A while it owns an active job. Keep B running. After lease expiry, verify
   B completes the job and the attempt count increases. There should be one set
   of results/tasks, not duplicate rows.
3. Relaunch A; verify it reads B's completed results and can play the recording.
4. Test retry of a failed job through the other backend.
5. Verify a non-member gets 404 and an unsigned request gets 401 for meeting/audio.
6. Purge after completion; verify DB records disappear and cleanup removes the
   Storage object. Stop Storage access temporarily and verify cleanup retries.
7. Repeat with A/B reversed, recording settings, commit, timings, and failures.

Automated tests exercise real PostgreSQL with offline Storage/inference stand-ins,
including an actual terminated claimant process. They do not establish live
Supabase Storage, native playback redirects, or two-device acceptance. Test those
before presenting seamless failover.

## Minimal rollout for Will

After acceptance testing, coordinate the shared migration on the team project.
Will pulls the tested commit, sets the server-only Storage key, and restarts with
`--shared --worker-id will-mac`. Bryan starts the same version/configuration with
his own ID and tunnel. No device-management access or Terraform/Ansible is needed.

Existing local meetings are not automatically copied into Storage or queued.
Their local mode backend can still serve them. Shared legacy polling/audio/retry
returns a clear 409 for those meetings; v1 DB reads remain available. Shared-mode
purge/deletion of projects containing old local recordings must be performed on
their original backend so those files are removed too. Plan any migration of old
recordings explicitly; do not discard existing meetings to enable shared mode.

For one app hostname, configure health-monitored routing between two independent
Cloudflare tunnels after both backends pass acceptance. Provisioning/routing is a
separate operation requiring control of the Cloudflare account. In-flight uploads
can fail; routing alone cannot resume them. Both hosts offline, Supabase failure,
or a shared provider outage are outside this two-host recovery mechanism.

## Keeping Bryan's local backend running

A terminal running `labsync serve` must remain alive. Unplugging power is fine
while the Mac is awake and connected. Closing its lid, sleep, shutdown, or losing
network access makes this backend unavailable. Supabase preserves shared audio
and job state; another configured shared worker can recover expired processing
leases. API failover still requires routing or switching the app's backend URL.

Use the installed `tmux` for development. Stop the existing foreground server
with Ctrl-C before starting another on port 8000. From the repo root:

```bash
tmux new-session -s labsync -c "$PWD"
uv run --locked --env-file .env --extra audio --extra server --extra diarize \
  labsync serve --shared --worker-id bryan-mac --port 8000 \
  --storage artifacts/shared-bryan --whisper-backend mlx --whisper-model base
```

Speaker diarization is enabled by default for `serve` and `transcribe`.
`--extra diarize` installs dependencies. Configure the required Hugging Face
model access and `HF_TOKEN`; processing fails visibly if diarization cannot run.
Use `--no-diarize` only for an intentional transcription-only run. Existing
completed recordings are not reprocessed by restarting the worker.
For AMI fixtures, retain anonymous speaker labels until reviewed against corpus
annotations. Map corpus speakers to test accounts only for task-routing tests;
that mapping is not voice recognition and does not mean the account owner
attended the meeting.

Detach with Ctrl-B, then D. The backend keeps running after the terminal window
closes. Reattach with `tmux attach -t labsync`; inspect sessions with `tmux ls`.
To stop it, reattach and press Ctrl-C. To restart, run the same `uv` command.
After a reboot there is no surviving tmux session: repeat the commands above.
Keep the same `.env` and worker configuration. For sustained availability, run
a shared backend on an always-on host. tmux is not a service manager or an
automatic failover router.

## Local AMI development setup

The signed-in Bryan account created these real server projects through iOS:

| Project | Recordings | Role |
| --- | --- | --- |
| AMI Remote Control - Dev | TS3005a, TS3005b, TS3005c, TS3005d | Connected development sequence, uploaded in suffix order |
| AMI Isolation - Validation | IS1008a | Separate project for isolation checks |
| AMI Evaluation | IS1009a | Evaluation candidate with prior Milestone 2 ASR use |
| AMI ES2004 - Evaluation | ES2004a | Separate design trial, also used in the ASR pilot |

All seven recordings were accepted on October 10, 2026. Their current app dates
are import dates, not verified corpus meeting dates. Sequence order comes from
the TS3005 suffixes and upload order. Human-reviewed continuity labels remain
required. Other accounts must join these projects through invitations.

Original WAV files remain under `contexts/datasets/ami`. Smaller, lossless FLAC
copies are under the gitignored `artifacts/ami-upload`; all decoded PCM samples
were checked against their originals. TS3005a was uploaded as WAV; the other
six were uploaded as FLAC after the larger TS3005b WAV hit a Storage error.
Audio files were staged in the simulator's Files app to exercise the native
file picker and authenticated upload path. Upload success does not establish
extraction quality or task continuity.
