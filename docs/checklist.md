# End-to-End Completion Checklist

Source of truth: [Workflow.md](writeups/Workflow.md). User-facing behavior: [Story Writeup.md](writeups/Story%20Writeup.md).

This is the remaining work to make Meetings, Tasks, and Chat run against PostgreSQL from iOS, not local JSON files or seeded SwiftData.

**Current state:** Meetings upload/transcribe/extract works through FastAPI JSON-on-disk (`artifacts/server/`). iOS Meetings talks to that API and copies results into on-device SwiftData. PostgreSQL (`db/schema.sql`) is authored but unused. Tasks, Chat, real audio playback, EventKit, RAG, auth, and hybrid search are not end-to-end.

Legend: `[x]` done in the repo · `[ ]` still required for E2E.

---



## Phase 1 — Contract & Interface Freeze

- [x] Author PostgreSQL 16 DDL for all 12 tables (`db/schema.sql`)
- [x] Foreign keys with `ON DELETE CASCADE` / `SET NULL` as specified
- [x] HNSW vector indexes (`vector_cosine_ops`) on attendees, transcripts, tasks
- [x] GIN full-text index (`tsvector`) on transcripts
- [x] Pydantic models for transcript turns, summary, decisions, commitments, suggestions, evidence (`src/labsync/extraction.py`)
- [ ] Pydantic models for attendee storylines (`what_they_want`, `what_they_see`, `what_they_discuss`)
- [ ] Pydantic models for task review payloads (approve / edit / dismiss + lifecycle `open` / `done` / `dropped`)
- [ ] Pydantic models for RAG query/response (answer, citations, grounded refusal)
- [ ] Lock remaining contracts to the DDL (source IDs vs UUIDs, multi-citation evidence vs single `transcript_id` on tasks/decisions)
- [ ] Golden fixture pack in `tests/fixtures/`: ~60s `.wav`, human-verified transcript, mock attendee calendar records

**Owner hint:** Engineer 2 (schema) + Engineer 3 (extraction/RAG contracts). All three review before Phase 2.

---



## Phase 2 — Persistence & Search Layer (System 8)

Nothing in this phase is used at runtime yet. Backend still writes `meeting.json` files.

- [ ] Install/run local PostgreSQL 16 with `pgvector` (Homebrew or `docker-compose`)
- [ ] Execute `db/schema.sql` (or Alembic) against a fresh database and confirm extensions, FKs, and indexes
- [ ] SQLAlchemy 2.0 + `asyncpg` engine, connection pool, FastAPI session dependency
- [ ] Repositories for all 12 tables: `projects`, `meetings`, `attendees`, `meeting_attendees`, `transcripts`, `meeting_summaries`, `meeting_decisions`, `attendee_storylines`, `tasks`, `task_audit_log`, `chat_conversations`, `chat_messages`
- [ ] Every task mutation writes `task_audit_log` with a unique UUID `revert_token`
- [ ] Hybrid search CTE: pgvector cosine + `tsvector` RRF at `k=60`, scoped by `WHERE project_id = :project_id`
- [ ] Stop using `artifacts/server/*/meeting.json` as the source of truth (audio files may still live on disk; metadata must live in Postgres)

**Owner hint:** Engineer 2.

---



## Phase 3 — Headless Audio & Extraction Pipeline (Systems 6 & 7)

Partial: Whisper + optional pyannote via the CCB bridge, Codex extraction of summary/decisions/commitments. Results are not written to Postgres. Storylines and dedup are missing.

- [x] Audio ingest + Whisper transcription with timestamps (`labsync transcribe`)
- [x] Optional `pyannote.audio` diarization (`--diarize`)
- [x] LLM structured extraction for summary, decisions, commitments, suggestions with quote checks
- [ ] FFmpeg normalization to 16 kHz mono WAV as a first-class pipeline stage
- [ ] Token-level timestamps suitable for sub-second `AVPlayer` seek
- [ ] 512-d x-vector extraction and cosine match against `attendees.voice_embedding`
- [ ] Map diarized speakers to named attendees / profile initials (calendar + voice profile)
- [ ] Persist turns into `transcripts` (content, `start_time_ms`, `end_time_ms`, embedding, `tsv`)
- [ ] Extract and persist attendee storylines into `attendee_storylines`
- [ ] Persist summaries into `meeting_summaries` and decisions into `meeting_decisions`
- [ ] Insert extracted commitments as `tasks` with `review_status = pending`
- [ ] Task dedup: `sentence-transformers/all-MiniLM-L6-v2` embeddings, pgvector cosine vs open tasks, LLM arbitration above 0.80 similarity
- [ ] Parse `due_date_text` into `tasks.due_date` during review (do not silently invent dates)

**Owner hint:** Engineer 3 (pipeline) + Engineer 2 (writes into repositories).

---



## Phase 4 — Sequential Queue & API Gateway (Systems 4 & 5)

Partial: FastAPI upload, poll, retry, audio file, project purge. Single-thread worker. No auth, no WebSocket, no 206, no tunnel, no task/chat/RAG routes.

- [x] Sequential worker so only one meeting processes at a time
- [x] `POST /api/meetings` upload with consent flag, title, project, date
- [x] `GET /api/meetings/{id}` with transcript + extraction
- [x] `POST /api/meetings/{id}/retry`
- [x] `GET /api/meetings/{id}/audio` (full file, not byte-range)
- [x] `DELETE /api/projects/{project}/meetings`
- [ ] Swap JSON persistence for Postgres in all of the above
- [ ] Bearer token guard (`Authorization: Bearer <API_SECRET_KEY>`) on every route
- [ ] `project_id` scoping on reads/writes (UUID, not a free-text project name)
- [ ] `GET /api/meetings` list (and project list) so clients can sync after relaunch
- [ ] Task review API: approve / edit / dismiss; return payload for EventKit sync
- [ ] Task lifecycle API: `open` / `done` / `dropped` with audit log + undo via `revert_token`
- [ ] Summary edit/save API
- [ ] Chat/RAG API: create conversation, list history (all vs project), query with citations or `"I don't know"`
- [ ] `WS /ws/pipeline/{job_id}` for live stage cards (queued → transcribing → diarizing → extracting → complete)
- [ ] `GET /meetings/{id}/audio` returns `HTTP 206 Partial Content` for Range requests
- [ ] Cloudflare Tunnel or Tailscale to expose `localhost:8000` over HTTPS
- [ ] Privacy: selective transcript exclusion/redaction, project-scoped purge that actually deletes Postgres rows + audio

**Owner hint:** Engineer 2.

---



## Phase 5 — Offline Evaluation Harness (System 9)

Partial: extraction development evaluation now runs independently of persistence.
[Measured baseline results](milestone_2/results/README.md) cover 24 synthetic cases
with AI-authored labels pending human review. No WER/DER/RAGAS gate.

- [x] Offline pytest for extraction contract, CLI, and stubbed server workflow
- [x] Transcript extraction development fixtures: 24 cases, 15 obligations, annotation and matching protocol (`tests/fixtures/evaluation/`)
- [x] Offline scorer tests in `tests/benchmarks/`: matching, wrong owners/deadlines, duplicates, invalid citations, failed/missing outputs, input hashes
- [x] Separate live baseline generation and offline scoring (`python -m labsync.evaluation`)
- [x] Run rules, Codex, and an external open-source model on identical inputs; save predictions, settings, P/R/F1 proxies, owner/deadline agreement, citations, latency and per-case errors
- [ ] Human-review development labels and semantic matches; complete two-reviewer rubric
- [ ] Expand to natural meetings and freeze held-out splits before making general accuracy claims
- [ ] `pytest tests/benchmarks/` with `jiwer` (WER)
- [ ] Diarization DER via `pyannote.metrics`
- [ ] RAGAS (or equivalent) citation faithfulness + grounded refusal (`"I don't know"`)
- [ ] Run the suite against golden fixtures; record pass/fail before claiming E2E
- [ ] Keep a small live smoke: upload fixture → Postgres rows exist → RAG refuses unknown questions

**Owner hint:** Engineer 3.

---



## Phase 6 — iOS Networking & Playback (Systems 2 & 3)

Partial: Swift models, URLSession client, upload/poll/retry/purge. No bearer token, WebSocket, AVPlayer, or EventKit.

- [x] Swift models for meetings, transcript turns, decisions, commitments
- [x] `MeetingAPIClient` upload / poll / retry / purge against `http://127.0.0.1:8000`
- [x] `RemoteMeetingApplier` mapping remote JSON → SwiftData
- [ ] Configurable base URL (Simulator localhost vs device LAN vs tunnel)
- [ ] Inject bearer token on every request
- [ ] WebSocket listener for pipeline progress (replace 2s polling, or keep poll as fallback)
- [ ] Sync projects/meetings/tasks from `GET` APIs on launch (do not rely on seed data)
- [ ] `AVPlayer` + `AVAudioSession` playing `GET /meetings/{id}/audio`
- [ ] Sub-second seek via `CMTime` from transcript, task, decision, and chat citation timestamps
- [ ] Periodic time observer for active playhead highlighting
- [ ] EventKit: read calendar event for attendees/date/project at ingest
- [ ] EventKit: export approved tasks to Apple Reminders (+ Calendar when a due date exists)
- [ ] Remove or gate `SeedData` so production runs are not mixed with mock "AI Thesis" / "Robotics Lab" records

**Owner hint:** Engineer 1.

---



## Phase 7 — Native Presentation (System 1)

Screens exist. Only the Meetings upload/review path is live, and it is local-cache-backed. Tasks/Chat/storyline/audio are UI shells.

### Meetings

- [x] Tab bar: Meetings (default), Tasks, Chat
- [x] Project list + add project (local SwiftData only)
- [x] Meeting list per project + add meeting with consent toggle
- [x] Upload audio and show queued / transcribing / extracting / failed + retry
- [x] Render backend summary, decisions, transcript, candidate tasks after completion
- [ ] Projects and meetings listed from Postgres after relaunch (no seed-only dashboard)
- [ ] Project image + name stored on `projects`
- [ ] Meeting row shows real duration from audio, not `"Processing"` leftover or mock waveform
- [ ] Consent modal actually gates ingest (already required on upload; EventKit match still fake)
- [ ] Diarized transcript with speaker name, initials, and playhead highlight
- [ ] Timestamp chip seeks audio (today it only switches to the transcript tab)
- [ ] Task review: Approve, **Edit**, Dismiss — persist to server, not only SwiftData
- [ ] Approve creates an `open` task that appears on the Tasks calendar for that due date
- [ ] Approve writes EventKit reminder/calendar
- [ ] Storylines from `attendee_storylines` (today the three perspective cards are hardcoded)
- [ ] Manual summary notes edit + save
- [ ] Share formatted notes + action items (ShareLink exists; payload is title + summary only)
- [ ] Redaction tool (button is a no-op)
- [ ] Purge deletes Postgres + local cache (today: JSON folders + SwiftData)



### Tasks

- [x] Year/month calendar UI and project filter
- [x] Local check (complete) and trash (delete) on SwiftData rows
- [ ] Calendar populated from **approved** server tasks, not seed data
- [ ] 3-state lifecycle: leftover = `open`, check = `done`, trash = `dropped` (today: `isCompleted` / delete; extra states `In-Progress` / `Blocked` are unused)
- [ ] Filter by project from Postgres `project_id`
- [ ] Edit assignee, description, due date, status — persist + audit log
- [ ] Reminders / approaching-deadline highlighting (bell button is a no-op; push notifications are out of scope)



### Chat

- [x] Chat chrome: history drawer, project picker, new-chat button, input bar
- [ ] Send a query to the RAG API (send button is inert)
- [ ] Grounded answer with meeting name + timestamp citation badges
- [ ] Citation tap seeks `AVPlayer` to that offset
- [ ] Render `"I don't know"` when retrieval has no support
- [ ] Persist threads in `chat_conversations` / `chat_messages`
- [ ] History filter: All vs a target project; open a new conversation

**Owner hint:** Engineer 1, blocked on Phase 4 APIs.

---



## End-to-end user journeys (definition of done)

Check these only after the phases above land. Each must work on a real recording (or the golden fixture) with the backend running and Postgres populated.

- [ ] **Ingest:** Pick a project → confirm consent → upload MP3/WAV → see live pipeline status → meeting appears under that project after relaunch
- [ ] **Read:** Open the meeting → summary + decisions + diarized transcript + per-attendee storylines all come from the database, with citation timestamps
- [ ] **Play:** Play audio; tap a transcript/task/decision timestamp; playhead jumps and the active turn highlights
- [ ] **Review:** Approve / edit / dismiss candidates; approved items show on the Tasks calendar; duplicates of open tasks are flagged, not double-created
- [ ] **Operate:** Mark a task done or dropped; undo via audit `revert_token`; optional Reminders/Calendar copy exists on device
- [ ] **Ask:** Chat within a project (and All) returns cited answers or `"I don't know"`; history survives relaunch
- [ ] **Scope/privacy:** Queries never leak another project; purge removes that project's meetings, audio, tasks, and chat from Postgres and the phone
- [ ] **Remote:** Phone on cellular/Wi-Fi reaches the Mac backend through the tunnel with the bearer token

---



## Out of scope (do not put on the sprint board)

From the Story Writeup: transcript encryption, push/SMS notification infrastructure, training ASR from scratch, productivity scores, ranking people, recording without consent, multi-tenant production auth/accounts, treating transcripts as proof that work happened, broad language claims.

---



## Suggested build order

Do not jump to more SwiftUI until persistence exists. Workflow order still applies:

1. Finish Phase 1 missing contracts + golden fixture
2. Phase 2: Postgres up, migrate, repositories, hybrid search
3. Phase 3: write pipeline output into those tables (including storylines + dedup)
4. Phase 4: replace JSON API with Postgres + task/chat/RAG/auth/206/WS
5. Phase 5: run the full evaluation gate on fixtures. The transcript-only extraction subset can run now using the Phase 1 contract and Phase 3 extractor; it does not depend on Postgres.
6. Phase 6–7: point iOS at the real APIs; AVPlayer, EventKit, live Tasks/Chat

)