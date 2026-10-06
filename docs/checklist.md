# End-to-End Completion Checklist

Source of truth: [Workflow.md](writeups/Workflow.md). User-facing behavior: [Story Writeup.md](writeups/Story%20Writeup.md).

This is the remaining work to make Meetings, Tasks, and Chat run against PostgreSQL from iOS, not local JSON files or seeded SwiftData.

**Current state:** Sign-in, profiles, project membership, invitations, voice enrollment, upload, speaker identification, review, tasks, and cited project chat are implemented. The signed-in app loads projects from `GET /api/v1/projects` and does not seed sample projects on launch. Enrollment records three clips and stores a voiceprint only after consent and quality checks; skipping is still allowed, and revoke deletes the voiceprint. When the worker is started with `--diarize`, enrolled project members can be named on the transcript and everyone else stays `SPEAKER_N`. Match thresholds are provisional and not calibrated. Playback, storylines, summary editing, redaction, and the JSON status file are still incomplete. This is an implementation inventory, not a claim that a user journey works end to end.

Legend: `[x]` implementation exists in the repo · `[ ]` implementation still required. A checked item is not acceptance evidence. Use the [UI demo walkthrough](demo_walkthrough.md) to record the build, backend, observed behavior, and remaining gaps before claiming a user journey works.

---

## Phase 1 — Contract & Interface Freeze

- [x] Author PostgreSQL DDL (`db/schema.sql`, 13 tables including `item_evidence`) and apply it on Supabase
- [x] Later migrations for accounts and membership, voice consent and voiceprints, and speaker-match columns (`20261001181443_accounts_and_membership.sql`, `20261003200000_voice_enrollment.sql`, `20261004120000_speaker_identification.sql`)
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

Postgres is used for projects, meeting rows, pipeline results, and hybrid search. The worker still reads and writes `meeting.json` for status. The pool is `psycopg` + `psycopg_pool`, not SQLAlchemy.

- [x] Hosted Postgres with `pgvector` on Supabase; local tests use `supabase start` and `TEST_DATABASE_URL`
- [x] Schema applied (`supabase db push` / `supabase/migrations/20260927033954_initial_schema.sql`)
- [x] `psycopg_pool.ConnectionPool` and FastAPI `get_conn` (`src/labsync/db/connection.py`, `src/labsync/api/deps.py`)
- [x] Repositories in use: `projects`, `meetings`, `meeting_transcripts`, `meeting_summaries`, `meeting_decisions`, `item_evidence`, `tasks`, `task_audit_log`, `chat_conversations`, `chat_messages`, `rag_chunks`, `profiles`, `invitations`, `voice_consents`, `voice_profiles`
- [x] A voice match writes the member's `attendees` row and a `meeting_attendees` row (`display_label`, `match_score`, `match_method`, `embedding_model_id`). Unmatched speakers get no attendee row
- [ ] `meeting_attendee_storylines` is still unused for writes (detail reads return an empty list)
- [x] Lifecycle changes (`open` / `done` / `dropped` and revert) append `task_audit_log` with a unique `revert_token`
- [ ] Review edits (title, assignee, due date, approve, dismiss) are not written to `task_audit_log`
- [x] Hybrid search CTE: pgvector cosine + `tsvector` RRF at `k=60`, scoped by `WHERE project_id = :project_id`
- [ ] Stop using `artifacts/server/*/meeting.json` as the pipeline source of truth (audio files may still live on disk)

**Owner hint:** Engineer 2.

---

## Phase 3 — Headless Audio & Extraction Pipeline (Systems 6 & 7)

Whisper, optional diarization, and Codex/Claude extraction run, and completed v1 uploads persist summary, decisions, transcript turns, and pending tasks. Passage embeddings, shortened task-title embeddings, and voiceprints are written. Storylines are not. Speaker naming runs only when diarization wrote `speakers.json`.

- [x] Audio ingest + Whisper transcription with timestamps (`labsync transcribe`)
- [x] Optional `pyannote.audio` diarization (`--diarize`)
- [x] FFmpeg normalization to 16 kHz mono WAV before Whisper (`src/labsync/ccb.py`)
- [x] LLM structured extraction for summary, decisions, commitments, suggestions with quote checks
- [x] Persist turns into `meeting_transcripts` (content, `speaker_label`, `speaker_name`, `turn_key`, `start_time_ms`, `end_time_ms`)
- [x] Persist summaries into `meeting_summaries` and decisions into `meeting_decisions`, with evidence rows
- [x] Insert extracted commitments and suggestions as `tasks` with `review_status = pending`
- [x] Approval requires an explicit due date from the reviewer; `due_date_text` is stored verbatim and is not parsed into a date
- [x] Passage embeddings (OpenAI text-embedding-3-small, 1536-d) and `tsv` stored in `rag_chunks`
- [ ] `meeting_transcripts.embedding` is not written. Search uses `rag_chunks`, not the 384-d transcript column
- [ ] Token-level timestamps suitable for sub-second `AVPlayer` seek
- [x] Voiceprints: three clips (A, B, C), quality gates, and one L2-normalized 256-d WeSpeaker embedding in `voice_profiles` (`pyannote/wespeaker-voxceleb-resnet34-LM`). Raw clips are deleted. The API returns enrollment status, not the embedding. `attendees.voice_embedding` is unused
- [x] Cosine match of diarized speaker centroids against enrolled members of that project (`voice.identify`). One-to-one assignment uses a provisional threshold of 0.60 and a margin of 0.10, which are not calibrated. A failure leaves everyone as `SPEAKER_N` and does not fail the meeting. Speaker embeddings are deleted after matching
- [x] A match snapshots `profiles.display_name` into `speaker_name` and `meeting_attendees.display_label`. Extraction runs on that labeled transcript. A commitment owned by a matched member sets `assignee_user_id`
- [ ] Diarization is still opt-in (`labsync serve --diarize`). Without `speakers.json`, every speaker stays unmatched
- [ ] Calendar attendees are not used for speaker identity
- [ ] Extract and persist attendee storylines into `meeting_attendee_storylines`
- [x] Task similarity flag: a pending task whose title embedding (first 384 dimensions of `text-embedding-3-small`, stored on `tasks.embedding`) has cosine similarity of at least 0.80 with an earlier approved open task in the same project returns `matches_task`. The candidate is still inserted. There is no LLM arbiter, and `sentence-transformers/all-MiniLM-L6-v2` is not used
- [ ] `meetings.duration_seconds` is never written

**Owner hint:** Engineer 3 (pipeline) + Engineer 2 (writes into repositories).

---

## Phase 4 — Sequential Queue & API Gateway (Systems 4 & 5)

v1 project, meeting, task, chat, profile, invitation, and voice routes talk to Postgres. Legacy `/api/meetings` routes still serve the JSON worker record, which is what the iOS status poll uses. No WebSocket or summary edit. Voice enrollment runs inside the request, not in the meeting queue.

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
- [x] Profile and voice API: `GET` / `PATCH /api/v1/me`, `POST /api/v1/me/onboarding/complete` with `voice_step: skipped`, grant and revoke voice consent, `GET /api/v1/me/voice`, and `POST /api/v1/me/voice-enrollments`. A quality failure is HTTP 422 with per-clip reasons. Revoke deletes the voiceprint and does not lock the account
- [ ] `WS /ws/pipeline/{job_id}` for live stage cards (queued → transcribing → diarizing → extracting → complete)
- [ ] Selective transcript exclusion/redaction (the Privacy sheet button is a no-op)

**Owner hint:** Engineer 2.

---

## Phase 5 — Offline Evaluation Harness (System 9)

Partial: [CCB transcription measurements](archive/milestone_2/transcription_results.md) cover 12 minutes of AMI audio with series-disjoint development/validation/test splits. [Extraction development results](archive/milestone_2/results/README.md) cover 24 synthetic cases with AI-authored labels pending human review. No DER/RAGAS gate or calibrated WER acceptance threshold.

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

### Milestone 3 demo pack and updated evaluation

The current 45-second AMI fixture checks upload/transcription, not project continuity. Swift seed data is for previews/tests. Neither is a complete demo corpus. Use the [submission draft](milestone_3/submission_draft.md) for reporting and the [demo walkthrough](demo_walkthrough.md) for observed native behavior. Owners below are proposed until the team confirms them.

- [ ] **Data selection (Guadalupe, with team review):** Inspect TS3005a-d manual transcripts for meaningful decisions, commitments, deadline changes, and completion before selecting audio. Annotations are local; only TS3005a audio from this series is currently downloaded. Download the missing recordings if the sequence fits
- [ ] **Coverage fallback (Team):** If AMI lacks the required continuity cases, record a clearly labeled scripted sequence with consenting teammates. Keep scripted demonstration evidence separate from natural-meeting accuracy claims
- [ ] **Main project (Team):** Assemble three connected meetings with a new owner/deadline commitment, a later deadline change, explicit completion, an unaccepted suggestion, an ambiguous reference, and an unmentioned task that remains open
- [ ] **Second project (Team):** Add a distinct recording with different facts and commitments for project selection and isolation checks
- [ ] **Frozen inputs and labels (Guadalupe, second reviewer):** Record provenance, license/consent, meeting order, timestamps, file hashes, reviewed transcripts, expected task state after each meeting, supporting evidence, and review disagreements before comparison runs
- [ ] **Continuity implementation (Will):** Extend the existing similarity flag to reviewed matching and state updates; preserve ambiguous cases for review. A `matches_task` flag alone is not a merge, deadline update, or completion
- [ ] **Sequence comparison (Bryan):** Run independent-meeting extraction and the updated reconciliation workflow on the same frozen transcripts and model/extraction settings. Report task-state accuracy, duplicate creation, incorrect updates, unsupported completions, and failures with denominators
- [ ] **RAG question set (Bryan, team review):** Freeze supported questions with expected source IDs/timestamps, unsupported questions, meeting-scope cases, and cross-project isolation cases
- [ ] **Required ablation (Bryan):** Compare dense-only against hybrid retrieval on the same corpus, questions, answer model, prompt, and K. Sparse-only is optional. Save raw outputs, versions/settings, Recall@K, ranking, answer correctness, citation faithfulness, refusals, latency, tokens, and estimated cost
- [ ] **Human error review (Guadalupe, second reviewer):** Review ordinary successes and representative failures; document disagreements, adjudication, and changes. Valid quotation text alone does not prove answer support
- [ ] **Voice extension evidence (Will, team review):** If speaker identity is claimed, evaluate enrolled and unenrolled speakers, false matches, abstentions, and downstream owner attribution. Separate threshold-calibration recordings from evaluation recordings
- [ ] **Native end-to-end run (Will):** Create real server projects and upload the pack through the app. Verify results, task review/state changes, supported/unsupported chat, isolation, relaunch persistence, and purge. Record commit, configuration, device, screenshots/video, and observed failures
- [ ] **Follow-through acceptance (Will and Bryan):** Verify promised reminders and cancellation/rescheduling after task changes. The one-time reminder exported at approval does not establish this behavior
- [ ] **Submission evidence (Team):** Add measured results, error analysis, exact reproduction instructions, Model/System Cards, and each member's extension write-up and metrics; export and review the final PDF

Retain Milestone 2 results as historical baselines. Do not compare old synthetic-case scores directly with new audio/sequence scores to claim improvement. Both variants must use identical inputs within each comparison. Optional extraction regression runs can reuse the original 24 cases. Run the complete audio-to-app path separately to expose ASR, speaker, persistence, and UI failures. Keep demo/development sequences out of any held-out evaluation claims.

---

## Phase 6 — iOS Networking & Playback (Systems 2 & 3)

The client signs in, lists projects from the API, enrolls or skips a voiceprint, uploads, polls, retries, purges, and syncs tasks. Playback, WebSocket progress, and calendar ingest are still open. `SeedData` remains for previews and tests only.

- [x] Swift models for meetings, transcript turns, decisions, commitments, tasks, and chat (create conversation, ask, history)
- [x] Onboarding records three voice clips and uploads them, or skips. Profile can re-record or revoke consent. The client shows enrolled or not enrolled and never receives the embedding
- [x] `MeetingAPIClient` against the configured base URL: upload, poll, retry, purge, create project, list meetings, review tasks, change state, revert
- [x] `RemoteMeetingApplier` mapping remote JSON → SwiftData
- [x] Base URL from `LabSyncConfig.plist` (`BaseURL`); every request sends the signed-in user's Supabase access token
- [x] Refresh a UUID project's meetings from `GET /api/v1/projects/{id}/meetings`
- [x] Load approved tasks from `GET /api/v1/tasks` into the calendar
- [x] EventKit: export an approved task to Apple Reminders (`ReminderScheduler`). Failure does not undo the approval
- [x] `GET /api/v1/projects` when Meetings, Chat, or Profile opens, so a reinstall sees projects created on the server
- [ ] WebSocket listener for pipeline progress (2s polling of the JSON meeting route is still the status path)
- [ ] `AVPlayer` + `AVAudioSession` playing `GET /meetings/{id}/audio` (`AudioDockView` is still a static mock)
- [ ] Sub-second seek via `CMTime` from transcript, task, decision, and chat citation timestamps
- [ ] Periodic time observer for active playhead highlighting
- [ ] EventKit: read a calendar event for attendees, date, and project at ingest (Session Setup still labels this "EventKit Match")
- [ ] EventKit: also create a Calendar event when a due date exists
- [x] `SeedData` is not applied on launch. `ProjectSync.prepareCache` drops leftover `p1` / `p2` / `p3` rows. Previews and unit tests still call `SeedData.seed`

**Owner hint:** Engineer 1.

---

## Phase 7 — Native Presentation (System 1)

Meetings, task review, the calendar, project chat, and voice enrollment have connected code paths that require UI acceptance testing. The signed-in project list comes from Postgres. A transcript speaker string can be a member's display name when the server matched a voiceprint. Storylines and audio playback remain placeholders.

### Meetings

- [x] Tab bar: Meetings (default), Tasks, Chat, Profile
- [x] Add project writes `projects` and stores the returned UUID locally
- [x] Meeting list per project + add meeting with consent required on upload
- [x] Upload audio and show queued / transcribing / extracting / failed + retry
- [x] Render backend summary, decisions, transcript, and candidate tasks after completion
- [x] Transcript rows show the server speaker string and initials: a member's display name when voice matching succeeded, otherwise `SPEAKER_N` or the diarizer label. The client still creates one local `Attendee` per displayed string
- [x] Task review: Approve, Edit, Dismiss persist through `/api/v1/tasks/{id}/review` when the candidate id is a server UUID
- [x] Approve requires a due date, then the task is `approved` / `open` and shows on the Tasks calendar
- [x] Approve writes an EventKit reminder
- [x] Purge deletes Postgres meetings (cascade) and the local SwiftData cache for that project
- [x] Project list reloads from Postgres when Meetings opens (`ProjectSync.refreshProjects`). Leftover seed ids are removed
- [ ] Project image stored on `projects.image_url` and shown on the row (the row uses initials)
- [ ] Meeting row duration comes from audio. After a completed poll it is the last transcript timestamp; rows inserted from the meeting list stay `"Processing"` until that poll, and the waveform is random
- [x] A pending candidate can show the title of an earlier open task when `matches_task` is set. The candidate is still created
- [ ] Named attendees from a calendar event. Voice names arrive as the transcript speaker string, not from EventKit
- [ ] Playhead highlight on the active transcript turn
- [ ] Timestamp chip seeks audio (it only switches to the transcript tab)
- [ ] Storylines from `meeting_attendee_storylines` (the three perspective cards are hardcoded)
- [ ] Manual summary notes edit + save
- [ ] Share formatted notes + action items (ShareLink payload is title + summary only)
- [ ] Redaction tool (button is a no-op)

### Tasks

- [x] Year/month calendar UI and project filter
- [x] Approved server tasks with a due date fill the calendar for UUID projects
- [x] Server tasks use `open` / `done` / `dropped`, and Undo calls the revert token
- [x] "Connection lost. Tap to reconnect." when the calendar or meeting task fetch fails
- [ ] Non-server tasks still use `isCompleted` and delete. `In-Progress` and `Blocked` are unused. Production no longer inserts seed tasks
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

**Owner hint:** Engineer 1. Chat/RAG is in the repo. Playback is still open.

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

1. Assemble and review the Milestone 3 demo pack and expected task states/questions; confirm owners and the scope promised in the submitted proposal
2. Complete the narrow cross-meeting reconciliation and follow-through path, then run identical-input sequence comparisons. Voiceprints and task-similarity flags already exist, but their presence does not establish reliable state tracking
3. Run the dense-only/hybrid RAG comparison and human error review; collect latency/cost and evaluate speaker identity if claimed as an extension
4. Perform the native walkthrough with real server projects. Fix the earliest blocking failure, add AVPlayer/citation seek for evidence inspection, and replace JSON status polling with Postgres-backed status. Start the worker with `--diarize` for the speaker demo
5. Complete promised remaining scope or identify deferrals explicitly; freeze the verified configuration and package results, cards, individual contributions, and the final PDF. Storylines, summary editing, redaction, calendar integration, and duration persistence remain tracked above

The transcript-only extraction subset in Phase 5 can keep running without Postgres.
