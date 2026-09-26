# Run the backend with the iOS app

Using Will's backend? Skip this file and run `scripts/use_shared_backend.sh` ([details](README.md#option-a-use-wills-backend)).

Running your own backend? Follow the [end-to-end steps in the README](README.md#option-b-run-your-own-backend-end-to-end). The short version, once setup is done:

Terminal 1:

```bash
uv run --locked --env-file .env --extra audio --extra server labsync serve --whisper-backend mlx --whisper-model medium
```

Terminal 2:

```bash
cloudflared tunnel run labsync-yourname
```

Check:

```bash
scripts/check_tunnel.sh api-yourname.guardianagent.dev
```

## Speaker labels (optional)

Accept the terms for `pyannote/speaker-diarization-3.1` and `pyannote/segmentation-3.0` on Hugging Face, then set `HF_TOKEN` in `.env`.

```bash
uv sync --locked --extra dev --extra audio --extra server --extra diarize
uv run --locked --env-file .env --extra audio --extra server --extra diarize labsync serve --whisper-backend mlx --whisper-model medium --diarize
```

## Troubleshooting

Logs: `artifacts/server/<meeting-id>/processing.log`

| Symptom | Fix |
| --- | --- |
| "Missing or invalid API token" | Using Will's backend: re-run `scripts/use_shared_backend.sh` with his current key. Own backend: make `.env` and `LabSyncConfig.plist` match, rebuild, start the server with `--env-file .env` |
| "Invalid host header" | Re-run `scripts/setup_tunnel.sh` |
| HTTP 502 | Start the backend |
| HTTP 530 | Start `cloudflared tunnel run` |
| "Transcribing failed" | Add `contexts/meeting_transcriber-master` (README step 2) |
| "Extracting failed" | Run `codex login` or fix `ANTHROPIC_API_KEY` |
| First upload is slow | The medium Whisper weights (about 1.5 GB) download on first use |
| Upload over 100 MB fails | Cloudflare plan limit |
