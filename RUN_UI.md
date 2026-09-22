# Run the connected meeting UI

Use branch `feature/ccb-codex-integration` in
[guardian-agent](https://github.com/BryanDYang/guardian-agent).
The Meetings screen uses the Python backend. There is no Gemini key in the browser.

## Terminal 1: backend

From the repository root, with CCB's supplied source present at
`contexts/meeting_transcriber-master`:

```bash
uv sync --locked --extra dev --extra audio --extra server
codex login status
uv run --locked --extra audio --extra server labsync serve --whisper-model tiny
```

Run `codex login` if needed. The backend listens on `127.0.0.1:8000`.
`tiny` is useful for a fast smoke test; omit the option to use `base`.
Whisper downloads weights on first use. Audio runs locally; generated transcript
text is sent through your Codex CLI login for extraction.

The server uses the same Codex executable and login as your terminal. It processes
one recording at a time. Both servers are intended for local, single-user
development. There is no account authentication or production deployment setup.

## Terminal 2: UI

From the repository root:

```bash
cd meeting-assistant-ui
npm install
npm run dev
```

Open **http://localhost:3000**. Vite forwards `/api` to the Python backend.
Keep both terminals open. Ports 3000 and 8000 must be free; if they are already
running from an agent session, use the existing servers rather than starting
duplicates.

## Test the entire path

1. Select **Add meeting** (the plus button).
2. Enter a title, project, and date.
3. Choose `tests/fixtures/ami/TS3005a-90s-135s.wav`.
4. Confirm permission to process the public audio and submit.
5. Watch the state change from queued to transcribing, extracting, and ready.
6. Read Summary, Commitments, and Transcript. Click transcript turns or quoted
   evidence to seek and play the recording.

The included clip contains opening remarks, so no commitments is a valid result.
The tiny model can misrecognize words. Output is a model prediction, not a
verified meeting record. Speakers remain unidentified without diarization.
The existing `--diarize` option still needs pyannote and accepted model access
through `HF_TOKEN`; that live branch has not been verified.

The UI replaces the mock meetings with real API data. Tasks and Chat show clear
unavailable states. Commitment approval, task tracking, storyline extraction,
and project question answering are not connected in this checkpoint.

## Persistence and troubleshooting

Uploads, job state, raw transcripts, predictions, and logs live under
`artifacts/server/<meeting-id>/` (ignored by Git). They survive page refreshes and
backend restarts. This is filesystem persistence, not the preliminary PostgreSQL
schema. Use one backend process per storage directory.

Failed jobs show an error and a retry action. Read
`artifacts/server/<meeting-id>/processing.log` for details. Retry starts a new
attempt and may consume model usage again. Interrupted jobs are marked failed
on restart. Graceful shutdown waits for submitted jobs to finish.

A backend connection error means the Python server is unavailable or its port
does not match the Vite proxy. Recordings up to 512 MB are accepted. WAV and MP3
are recommended for browser playback; other supported uploads may transcribe
successfully even if the browser cannot play their codec.

After a repository folder rename, deactivate any environment pointing at the
old path. Use `uv run` without reactivating that old environment.

## Checks

```bash
uv run --locked --extra dev pytest
uv run --locked --extra dev ruff check src tests
uv run --locked --extra dev ruff format --check src tests
cd meeting-assistant-ui
npm run lint
npm run build
```

The API tests cover upload validation, stored results, byte-range audio serving,
failures, retries, restart recovery, and browser-origin restrictions. Model calls
are stubbed in offline tests. The real Chrome smoke test separately exercised
public audio upload, Whisper, Codex, playback, seeking, refresh, and mobile layout.

API endpoints: `GET /api/health`, `GET/POST /api/meetings`,
`GET /api/meetings/{id}`, `GET /api/meetings/{id}/audio`,
and `POST /api/meetings/{id}/retry`. Local API documentation: http://127.0.0.1:8000/docs.
