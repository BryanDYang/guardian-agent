# Run the backend with the iOS app

Using Will's backend? Skip this file and run `scripts/use_shared_backend.sh` ([details](README.md#use-wills-backend-easiest)).

Running your own backend? Complete [Setup](README.md#setup) first.

## Local (simulator)

```bash
uv run --locked --env-file .env --extra audio --extra server labsync serve --whisper-backend mlx
open ios/MeetingApp/MeetingApp.xcodeproj
```

Run the app in the simulator and upload `tests/fixtures/ami/TS3005a-90s-135s.wav`.

## Phone (Cloudflare Tunnel)

Only the Mac that runs the backend needs this.

```bash
brew install cloudflared
scripts/setup_tunnel.sh api-yourname.guardianagent.dev labsync-yourname
```

Terminal 1:

```bash
uv run --locked --env-file .env --extra audio --extra server labsync serve --whisper-backend mlx
```

Terminal 2:

```bash
cloudflared tunnel run labsync-yourname
```

Check:

```bash
scripts/check_tunnel.sh api-yourname.guardianagent.dev
```

Rebuild the iOS app in Xcode after running the setup script.

## Speaker labels (optional)

Accept the terms for `pyannote/speaker-diarization-3.1` and `pyannote/segmentation-3.0` on Hugging Face, then set `HF_TOKEN` in `.env`.

```bash
uv sync --locked --extra dev --extra audio --extra server --extra diarize
uv run --locked --env-file .env --extra audio --extra server --extra diarize labsync serve --whisper-backend mlx --diarize
```

## Troubleshooting

Logs: `artifacts/server/<meeting-id>/processing.log`

| Symptom | Fix |
| --- | --- |
| "Missing or invalid API token" | Using Will's backend: re-run `scripts/use_shared_backend.sh` with his current key. Own backend: make `.env` and `LabSyncConfig.plist` match, rebuild, start the server with `--env-file .env` |
| "Invalid host header" | Re-run `scripts/setup_tunnel.sh` |
| HTTP 502 | Start the backend |
| HTTP 530 | Start `cloudflared tunnel run` |
| "Transcribing failed" | Add `contexts/meeting_transcriber-master` |
| "Extracting failed" | Run `codex login` or fix `ANTHROPIC_API_KEY` |
| Upload over 100 MB fails | Cloudflare plan limit |
