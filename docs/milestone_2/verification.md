# September 23 pre-merge verification

Branch: `feature/ccb-codex-integration`. Application revision: `df3a5390451f6e48f6e9f6f868d509d91a3e53fc`.

## Verified in this session

| Check | Result |
| --- | --- |
| Python offline tests | 36 passed in 2.59 seconds |
| Ruff lint and formatting | Passed; 13 files already formatted |
| Web TypeScript check and production build | Passed |
| Live API upload of public 45-second AMI fixture | HTTP 202, queued |
| Actual Whisper tiny and Codex processing | Completed, 11 transcript turns, summary present |
| Web processing/result display | Observed extracting state and then Ready; summary and transcript rendered |
| Web audio playback and transcript seek | 45-second duration; playback active; selecting 0:25 set currentTime to 25.301 seconds |
| Browser refresh | Completed meeting still listed |
| Native iOS build/Simulator | Blocked: full Xcode unavailable; selected developer directory is CommandLineTools, and simctl is absent |

Equivalent verification commands using the current `uv` workflow:

```bash
uv run --locked --extra dev pytest -q
uv run --locked --extra dev ruff check src tests
uv run --locked --extra dev ruff format --check src tests
cd meeting-assistant-ui
npm run lint
npm run build
```

Two dependency deprecation warnings remain: Starlette's httpx TestClient backend and AnyIO BlockingPortal alias. They did not fail the tests; dependency migration was not attempted as part of this documentation/test pass.

Live test title: `Milestone 2 pre-merge smoke`. ID: `bfddad72-5e2a-446d-95b6-40b74fb73850`. Local evidence is under `artifacts/server/<id>/`, ignored by Git. Current extraction prompt: `meeting-extraction-v2`; saved extraction duration: 5.864 seconds (excludes transcription/upload). This run returned zero decisions, commitments, and suggestions, which is valid for an agenda clip. It does not measure recall or semantic accuracy.

The upload was performed through curl with the same multipart contract used by the UI. Browser automation could not attach the file because Chrome extension file access was unavailable. The upload form was inspected, but a fresh form-submission test remains outstanding. Bryan separately reported a successful Swagger upload/results/playback test in this conversation. The web transcript view was visually inspected with no obvious overlap or clipping in its phone-shaped layout; other viewport sizes were not rechecked in this session.

Failure/retry, invalid upload, byte-range audio, and restart recovery passed automated API tests with stubbed inference. A real process restart and live failure/retry were not repeated, and the existing backend process was left running. Do not equate stubbed tests with live model runs.

## Before merging

- [ ] Have a teammate reproduce the documented setup from a clean checkout. CCB source must be supplied separately; check its access and redistribution status.
- [ ] Complete one browser upload through the form, including consent validation, then inspect results and audio.
- [ ] Build the iOS project and run its tests on a machine with full Xcode and a compatible Simulator. The project currently targets iOS 27.0; confirm this target is intentional and available to teammates.
- [ ] If claiming native integration, first implement the Swift API client, real file upload, polling, error/retry states, and AVPlayer. Then test upload through relaunch persistence in the Simulator. Current native code is still seeded and must be described as a prototype.
- [ ] For physical-device claims, add configurable backend binding and test LAN connectivity; currently the CLI binds only to 127.0.0.1.
- [ ] Check the PR's CI and obtain at least one teammate review under CONTRIBUTING.md. Review changed files for secrets/private recordings and excluded local artifacts.

The branch can be presented for review as a working web/backend checkpoint with an unconnected native prototype. It is not yet verified as a complete iOS application. No push, PR publication, or merge was performed in this session.

## Today's TA/team check-in

Demo the completed web meeting above and distinguish engineering progress from evaluation evidence. Bring the updated submission draft and ask:

1. Is independent-meeting extraction the right Milestone 2 scope while native integration and task reconciliation remain unfinished?
2. What minimum reviewed dataset size and scenario coverage should we deliver by September 28?
3. Which open-source extraction baseline is appropriate? Whisper alone addresses transcription, not comparable task extraction.
4. Can the team agree on commitment matching, owner scoring, and semantic evidence review today?
5. Confirm accountable owners and dates for labels, scorer, baseline runs, error analysis, native integration, and final PDF review.

Record actual feedback and attendees after the meeting. The report cannot be finalized until measured evaluation results and human review are available.
