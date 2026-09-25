# Meeting assistant UI

The React/Vite Meetings screen connects to the local LabSync backend for audio
upload, processing status, transcripts, summaries, commitments, and playback.

Start the backend from the repository root:

```bash
uv run --locked --extra audio --extra server labsync serve --whisper-model tiny
```

Then, in this directory:

```bash
npm install
npm run dev
```

Open http://localhost:3000. No Gemini API key is needed.
See [the full setup and test guide](../RUN_UI.md) for Codex login, CCB source,
fixture upload, persistence, and current limitations.

TypeScript check: `npm run lint`. Production bundle: `npm run build`.
The documented integration uses Vite's development proxy; production hosting is
not configured yet. Tasks and Chat are not connected.
