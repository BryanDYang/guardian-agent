# End-to-End Completion Checklist

Source of truth: [Workflow.md](writeups/Workflow.md). User-facing behavior: [Story Writeup.md](writeups/Story%20Writeup.md).

This is the remaining work to make Meetings, Tasks, and Chat run against PostgreSQL from iOS, not local JSON files or seeded SwiftData.

**Current state:** The repository contains backend and iOS implementations for upload, review, tasks, and cited project chat. This is an implementation inventory, not a claim that the connected UI works end to end. Seeded sample projects are local-only; auth and voice enrollment remain placeholders. Playback, storylines, account isolation, and other incomplete paths must not be presented as working features.

Legend: `[x]` implementation exists in the repo · `[ ]` implementation still required. A checked item is not acceptance evidence. Use the [UI demo walkthrough](demo_walkthrough.md) to record the build, backend, observed behavior, and remaining gaps before claiming a user journey works.

---

## Phase 1 — Contract & Interface Freeze

- [x] Author PostgreSQL DDL (`db/schema.sql`, 13 tables including `item_evidence`) and apply it on Supabase
- [x] Foreign keys with `ON DELETE CASCADE` / `SET NULL` as specified
- [x] HNSW vector indexes (`vector_cosine_ops`) on attendees, transcripts, tasks
- [x] GIN full-text index (`tsvector`) on transcripts
- [x] Pydantic models for transcript turns, summary, decisions, commitments, suggestions, evidence (`src/labsync/extraction.py`)
- [x] Multi-citation evidence in `item_evidence` (quote, `turn_key`, transcript UUID, timestamp), not a single `transcript_id` column on tasks or decisions
- [x] Pydantic models for task review and lifecycle (`Review`, `StateChange` in `src/labsync/api/tasks.py`)
- [ ] Pydantic models for attendee storylines (`what_they_want`, `what_they_see`, `what_they_discuss`)
- [x] Pydantic models for RAG query/response (answer, citations, grounded refusal)
- [ ] Golden fixture pack in `tests/fixtures/`: ~60s `.wav`, human-verified transcript, mock attendee calendar records

**Owner hint:** Engineer 2 (schema) + Engineer 3 (extraction/RAG contracts).

---

## Phase 2 — Persistence & Search Layer (System 8)

Postgres is used for projects, meeting rows, and pipeline results. The worker still reads and writes `meeting.json`. Search is not implemented. The pool is `psycopg` + `psycopg_pool`, not SQLAlchemy.

- [x] Hosted Postgres with `pgvector` on Supabase; local tests use `supabase start` and `TEST_DATABASE_URL`
- [x] Schema applied (`supabase db push` / `supabase/migrations/20260927033954_initial_schema.sql`)
- [x] `psycopg_pool.ConnectionPool` and FastAPI `get_conn` (`src/labsync/db/connection.py`, `src/labsync/api/deps.py`)
- [x] Repositories in use: `projects`, `meetings`, `transcripts`, `meeting_summaries`, `meeting_decisions`, `item_evidence`, `tasks`, `task_audit_log`, `chat_conversations`, `chat_messages`, `rag_chunks`
- [ ] Repositories still unused for writes: `attendees`, `meeting_attendees`, `attendee_storylines` (detail reads return an empty list)
- [x] Lifecycle changes (`open` / `done` / `dropped` and revert) append `task_audit_log` with a unique `revert_token`
- [ ] Review edits (title, assignee, due date, approve, dismiss) are not written to `task_audit_log`
- [x] Hybrid search CTE: pgvector cosine + `tsvector` RRF at `k=60`, scoped by `WHERE project_id = :project_id`
- [ ] Stop using `artifacts/server/*/meeting.json` as the pipeline source of truth (audio files may still live on disk)

**Owner hint:** Engineer 2.

---

## Phase 3 — Headless Audio & Extraction Pipeline (Systems 6 & 7)

Whisper, optional diarization, and Codex/Claude extraction run, and completed v1 uploads persist summary, decisions, transcript turns, and pending tasks. Storylines, embeddings, and dedup do not.

- [x] Audio ingest + Whisper transcription with timestamps (`labsync transcribe`)
- [x] Optional `pyannote.audio` diarization (`--diarize`)
- [x] FFmpeg normalization to 16 kHz mono WAV before Whisper (`src/labsync/ccb.py`)
- [x] LLM structured extraction for summary, decisions, commitments, suggestions with quote checks
- [x] Persist turns into `transcripts` (content, `speaker_label`, `turn_key`, `start_time_ms`, `end_time_ms`)
- [x] Persist summaries into `meeting_summaries` and decisions into `meeting_decisions`, with evidence rows
- [x] Insert extracted commitments and suggestions as `tasks` with `review_status = pending`
- [x] Approval requires an explicit due date from the reviewer; `due_date_text` is stored verbatim and is not parsed into a date
- [x] Passage embeddings (OpenAI text-embedding-3-small, 1536-d) and tsv stored in rag_chunks; 
- [ ] meeting_transcripts.embedding is used (check and confirm)
- [ ] Token-level timestamps suitable for sub-second `AVPlayer` seek
- [ ] Voice embedding extraction and cosine match against `attendees.voice_embedding`
- [ ] Map diarized speakers to named attendees (calendar + voice profile). The app currently invents a local attendee per speaker label
- [ ] Extract and persist attendee storylines into `attendee_storylines`
- [ ] Task dedup: `sentence-transformers/all-MiniLM-L6-v2` embeddings, pgvector cosine vs open tasks, LLM arbitration above 0.80 similarity
- [ ] `meetings.duration_seconds` is never written

**Owner hint:** Engineer 3 (pipeline) + Engineer 2 (writes into repositories).

---

## Phase 4 — Sequential Queue & API Gateway (Systems 4 & 5)

v1 project, meeting, and task routes talk to Postgres. Legacy `/api/meetings` routes still serve the JSON worker record, which is what the iOS poll uses. No WebSocket, summary edit, or chat/RAG routes.

- [x] Sequential worker so only one meeting processes at a time
- [x] `POST /api/v1/meetings/upload` with consent, title, `project_id` (UUID), and date. Legacy `POST /api/meetings` removed
- [x] `GET /api/v1/projects` and `POST /api/v1/projects`
- [x] `GET /api/v1/projects/{project_id}/meetings` and `GET /api/v1/meetings/{id}` (transcript, summary, decisions, tasks, storylines)
- [x] `GET /api/meetings/{id}` JSON poll, `POST /api/meetings/{id}/retry`
- [x] `GET /api/meetings/{id}/audio` supports `HTTP 206` Range requests (`FileResponse`) and that project's chat conversations
- [x] `DELETE /api/projects/{project}/meetings` removes JSON folders and, when the id is a UUID, Postgres meeting rows (tasks, transcripts, and decisions cascade)
- [x] Supabase sign-in on every route except `/api/health`; non-members get 404
- [x] v1 reads and writes are scoped by project UUID
- [x] Task review API: `PATCH /api/v1/tasks/{id}/review` approve / edit / dismiss, with an EventKit payload on approve
- [x] Task lifecycle API: `POST /api/v1/tasks/{id}/state` (`open` / `done` / `dropped`) and `POST /api/v1/tasks/revert/{revert_token}`
- [x] Cloudflare Tunnel scripts (`scripts/setup_tunnel.sh`, `scripts/check_tunnel.sh`) and the shared-backend hostname
- [ ] Point iOS status polling at the Postgres meeting detail (it still polls `/api/meetings/{id}`)
- [x] Drop the legacy free-text project name on `/api/meetings` (part 5 deleted that route)
- [ ] Summary edit/save API
- [x] Chat/RAG API: create conversation, list history (all vs project), query with citations or `"I don't know"`
- [ ] `WS /ws/pipeline/{job_id}` for live stage cards (queued → transcribing → diarizing → extracting → complete)
- [ ] Selective transcript exclusion/redaction (the Privacy sheet button is a no-op)

**Owner hint:** Engineer 2.

---

## Phase 5 — Offline Evaluation Harness (System 9)

Partial: [CCB transcription measurements](milestone_2/transcription_results.md) cover 12 minutes of AMI audio with series-disjoint development/validation/test splits. [Extraction development results](milestone_2/results/README.md) cover 24 synthetic cases with AI-authored labels pending human review. No DER/RAGAS gate or calibrated WER acceptance threshold.

- [x] Offline pytest for extraction contract, CLI, and stubbed server workflow
- [x] Transcript extraction development fixtures: 24 cases, 15 obligations, annotation and matching protocol (`tests/fixtures/evaluation/`)
- [x] Offline scorer tests in `tests/benchmarks/`: matching, wrong owners/deadlines, duplicates, invalid citations, failed/missing outputs, input hashes
- [x] Separate live baseline generation and offline scoring (`python -m labsync.evaluation`)
- [x] Run rules, Codex, and an external open-source model on identical inputs; save predictions, settings, P/R/F1 proxies, owner/deadline agreement, citations, latency and per-case errors
- [ ] Human-review development labels and semantic matches; complete two-reviewer rubric
- [ ] Expand to natural meetings and freeze held-out splits before making general accuracy claims
- [x] `pytest tests/benchmarks/` with `jiwer` (WER): known edit counts, normalization, missing outputs, input hashes and series split checks
- [x] Run actual CCB transcription with Whisper tiny/base on a frozen AMI pilot; report split-level WER, S/D/I counts, failures and real-time factor
- [ ] Expand ASR evaluation beyond two test meetings and set reviewed acceptance thresholds
- [ ] Diarization DER via `pyannote.metrics`
- [ ] RAGAS (or equivalent) citation faithfulness + grounded refusal (`"I don't know"`)
- [ ] Run the suite against golden fixtures; record pass/fail before claiming E2E
- [ ] Keep a small live smoke: upload fixture → Postgres rows exist → RAG refuses unknown questions

**Owner hint:** Engineer 3.

---

## Phase 6 — iOS Networking & Playback (Systems 2 & 3)

The client uploads, polls, retries, purges, creates projects, and syncs tasks. Playback, WebSocket progress, calendar ingest, and a seed-free launch are still open.

- [x] Swift models for meetings, transcript turns, decisions, commitments, tasks, , chat (create conversation, ask, history)
- [x] `MeetingAPIClient` against the configured base URL: upload, poll, retry, purge, create project, list meetings, review tasks, change state, revert
- [x] `RemoteMeetingApplier` mapping remote JSON → SwiftData
- [x] Base URL from `LabSyncConfig.plist` (`BaseURL`); every request sends the signed-in user's Supabase access token
- [x] Refresh a UUID project's meetings from `GET /api/v1/projects/{id}/meetings`
- [x] Load approved tasks from `GET /api/v1/tasks` into the calendar
- [x] EventKit: export an approved task to Apple Reminders (`ReminderScheduler`). Failure does not undo the approval
- [ ] `GET /api/v1/projects` on launch, so a reinstall sees projects created on the server
- [ ] WebSocket listener for pipeline progress (2s polling of the JSON meeting route is still the status path)
- [ ] `AVPlayer` + `AVAudioSession` playing `GET /meetings/{id}/audio` (`AudioDockView` is still a static mock)
- [ ] Sub-second seek via `CMTime` from transcript, task, decision, and chat citation timestamps
- [ ] Periodic time observer for active playhead highlighting
- [ ] EventKit: read a calendar event for attendees, date, and project at ingest (Session Setup still labels this "EventKit Match")
- [ ] EventKit: also create a Calendar event when a due date exists
- [ ] Remove or gate `SeedData` so production runs are not mixed with mock "AI Thesis" / "Robotics Lab" records

**Owner hint:** Engineer 1.

---

## Phase 7 — Native Presentation (System 1)

Meetings, task review, the calendar, and project chat have connected code paths that require UI acceptance testing. Storylines and audio playback remain placeholders. Seeded local projects use SwiftData and are unavailable to backend chat.

### Meetings

- [x] Tab bar: Meetings (default), Tasks, Chat
- [x] Add project writes `projects` and stores the returned UUID locally
- [x] Meeting list per project + add meeting with consent required on upload
- [x] Upload audio and show queued / transcribing / extracting / failed + retry
- [x] Render backend summary, decisions, transcript, and candidate tasks after completion
- [x] Transcript rows show the diarized speaker label and initials
- [x] Task review: Approve, Edit, Dismiss persist through `/api/v1/tasks/{id}/review` when the candidate id is a server UUID
- [x] Approve requires a due date, then the task is `approved` / `open` and shows on the Tasks calendar
- [x] Approve writes an EventKit reminder
- [x] Purge deletes Postgres meetings (cascade) and the local SwiftData cache for that project
- [ ] Project list reloads from Postgres after relaunch (it is whatever SwiftData already has, including seed rows)
- [ ] Project image stored on `projects.image_url` and shown on the row (the row uses initials)
- [ ] Meeting row duration comes from audio. After a completed poll it is the last transcript timestamp; rows inserted from the meeting list stay `"Processing"` until that poll, and the waveform is random
- [ ] Named attendees from calendar or voice profiles
- [ ] Playhead highlight on the active transcript turn
- [ ] Timestamp chip seeks audio (it only switches to the transcript tab)
- [ ] Storylines from `attendee_storylines` (the three perspective cards are hardcoded)
- [ ] Manual summary notes edit + save
- [ ] Share formatted notes + action items (ShareLink payload is title + summary only)
- [ ] Redaction tool (button is a no-op)

### Tasks

- [x] Year/month calendar UI and project filter
- [x] Approved server tasks with a due date fill the calendar for UUID projects
- [x] Server tasks use `open` / `done` / `dropped`, and Undo calls the revert token
- [x] "Connection lost. Tap to reconnect." when the calendar or meeting task fetch fails
- [ ] Seeded local tasks still use `isCompleted` and delete. `In-Progress` and `Blocked` are unused
- [ ] Edit an already-approved task (assignee, description, due date) with an audit row. Edit today applies only while `review_status` is `pending`
- [ ] Reminders / approaching-deadline highlighting (the bell button is a no-op; a reminder is created only at approval)

### Chat

- [x] Chat chrome: history drawer, project picker, new-chat button, input bar
- [x] Send a query to the RAG API via `MeetingAPIClient`; verify answers and scope using the demo walkthrough
- [x] Grounded answer with meeting name + timestamp citation badges
- [ ] Citation tap seeks `AVPlayer` to that offset
- [x] Render `"I don't know"` when retrieval has no support
- [x] Persist threads in `chat_conversations` / `chat_messages`
- [x] History filter: All vs a target project; open a saved conversation

**Owner hint:** Engineer 1, blocked on the chat/RAG API and on playback.

---

## End-to-end user journeys (definition of done)

Check these only when the whole journey works on a real recording (or the golden fixture) with the backend running and Postgres populated. Pieces of ingest, review, and remote access work today; none of these boxes are complete.

- [ ] **Ingest:** Pick a project → confirm consent → upload MP3/WAV → see live pipeline status → meeting appears under that project after relaunch, including on a second device
- [ ] **Read:** Open the meeting → summary + decisions + diarized transcript + per-attendee storylines all come from the database, with citation timestamps
- [ ] **Play:** Play audio; tap a transcript/task/decision timestamp; playhead jumps and the active turn highlights
- [ ] **Review:** Approve / edit / dismiss candidates; approved items show on the Tasks calendar; duplicates of open tasks are flagged, not double-created
- [ ] **Operate:** Mark a task done or dropped; undo via audit `revert_token`; Reminders copy exists on device; Calendar copy exists when there is a due date
- [ ] **Ask:** Chat within a selected project, across its completed meetings or one selected meeting, returns cited answers or `"I don't know"`; history survives relaunch
- [ ] **Scope/privacy:** Queries never leak another project; purge removes that project's meetings, audio, tasks, and chat from Postgres and the phone; redaction removes selected turns
- [ ] **Remote:** Phone on cellular/Wi-Fi reaches the Mac backend through the tunnel while signed in, and status does not depend on the JSON file

---

## Out of scope (do not put on the sprint board)

From the Story Writeup: transcript encryption, push/SMS notification infrastructure, training ASR from scratch, productivity scores, ranking people, recording without consent, multi-tenant production auth/accounts, treating transcripts as proof that work happened, broad language claims.

---

## Suggested build order

1. Finish the Phase 1 storyline and RAG contracts, plus the golden fixture
2. Phase 2–3 leftovers: write `duration_seconds`, transcript `tsv`/embeddings, storylines, speaker identity, and task dedup; make Postgres the worker's source of truth
3. Phase 4 leftovers: poll the v1 meeting route, summary edit, chat/RAG, WebSocket or keep poll as the documented fallback, redaction
4. Phase 5: human review, then DER and RAGAS once those pipelines exist
5. Phase 6–7: drop `SeedData` on real launches, list projects from the API, AVPlayer seek, EventKit calendar read, live Chat

The transcript-only extraction subset in Phase 5 can keep running without Postgres.
