# Milestone 3: Alpha Application and Model Integration

**Course:** CIS-5980
**Track:** AI Engineering
**Team:** Will Liu, Guadalupe Cantera, and Bryan Yang
**Repository:** https://github.com/BryanDYang/guardian-agent
**Draft updated:** October 1, 2026
**Submission date:** October 26, 2026

> **Draft status:** This document records the alpha implementation currently present in the repository and separates implemented features from verified end-to-end behavior. Bracketed placeholders identify work or evidence that must be completed before submission. The team must reconcile this structure with the official Milestone 3 rubric when that rubric is available.

## 1. Project and Milestone Goal

LabSync is a meeting follow-through assistant for recurring research meetings. It accepts a consented meeting recording, produces a timestamped transcript, extracts summaries, decisions, commitments, and suggestions, and stores those records as project memory. The iOS application lets users review candidate tasks, track their lifecycle, and ask historical questions that return supporting meeting citations.

Our central engineering question remains:

> Can an assistant reliably maintain commitments across a sequence of meetings while reducing manual reconciliation and avoiding unsupported task updates?

Milestone 2 established the initial data, transcription, task-extraction, and evaluation foundations. For Milestone 3, our goal is an alpha application that integrates the main product path and measures the behavior of its AI components. The intended alpha path is:

1. Create or select a project in the iOS application.
2. Upload a consented meeting recording through the authenticated backend.
3. Transcribe and extract structured meeting results.
4. Persist the meeting, transcript, summary, decisions, evidence, and candidate tasks in PostgreSQL.
5. Review candidate tasks and manage approved tasks through their lifecycle.
6. Ask questions over project history and receive grounded answers with verified citations, or a refusal when the indexed meetings do not support an answer.

The repository implements most individual stages of this path. The complete journey still requires a recorded end-to-end verification before submission.

## 2. Progress Since Milestone 2

### 2.1 Persistent project and meeting data

The application now uses PostgreSQL with pgvector for core project data. The backend provides versioned endpoints for projects, meetings, transcripts, summaries, decisions, evidence, tasks, chat conversations, chat messages, and retrieval chunks. Database migrations define the shared schema, and repository modules isolate SQL access from the API layer.

Completed implementation includes:

- Creation and listing of projects.
- Upload of a meeting under a project UUID.
- Persistence of transcript turns, meeting summaries, decisions, evidence, and pending tasks after processing.
- Project-scoped meeting reads for the iOS client.
- Cascading deletion for project meeting data.
- Bearer-token authentication for backend routes.
- A PostgreSQL connection pool shared by API handlers and background processing.

The sequential worker still uses a local `meeting.json` record for part of its status and retry flow. PostgreSQL is therefore the application data store, but it is not yet the only source of truth for pipeline status.

### 2.2 Structured audio and extraction pipeline

The backend accepts meeting audio, normalizes it to 16 kHz mono WAV, transcribes it with Whisper, optionally applies pyannote diarization, and sends the resulting timestamped turns to a schema-constrained Codex or Claude extraction provider. Extraction produces a summary, decisions, commitments, suggestions, and cited evidence.

The persistence layer writes:

- Transcript text, speaker labels, turn keys, and millisecond start and end times.
- A meeting summary.
- Decisions with supporting evidence.
- Commitments and suggestions as candidate tasks with `pending` review status.
- Retrieval chunks for transcripts, summaries, decisions, and tasks.

Evidence quotes are checked against source turns before extracted records are accepted. Missing owners and deadlines remain nullable instead of being invented.

Remaining pipeline work includes named-speaker identification, attendee storylines, task deduplication and cross-meeting reconciliation, meeting duration persistence, and removal of the JSON status dependency.

### 2.3 Human review and task lifecycle

The iOS client and backend support the human review path for candidate tasks. A reviewer can approve, edit, or dismiss a pending item. Approval requires an explicit due date. Approved tasks appear in the Tasks calendar and can be copied to Apple Reminders.

Approved tasks support `open`, `done`, and `dropped` lifecycle states. Each lifecycle change appends an audit record with the previous state, new state, and a unique revert token. The user can undo a lifecycle change through that token.

Current limitations are:

- Edits made during candidate review are not yet included in the task audit log.
- Editing an already approved task is not implemented.
- Calendar-event creation and ingest-time calendar matching are not implemented.
- Task deduplication and reconciliation against previously open tasks are not implemented.
- Scheduled follow-up beyond the one-time Apple Reminder created at approval is not implemented.

### 2.4 Project chat with hybrid retrieval and verified citations

The newest alpha capability is project-scoped chat over stored meeting history. Completed implementation includes:

- Ingestion-time indexing of transcript windows, summaries, decisions, and tasks in `rag_chunks`.
- Dense semantic retrieval combined with PostgreSQL full-text search through reciprocal rank fusion.
- Required project scoping and optional meeting scoping for every query.
- A structured answer contract containing answerability, answer text, and citation candidates.
- Server-side citation verification against retrieved source text.
- A fixed `I don't know` response when no supported citation remains.
- Persistent conversations and messages.
- Conversation history filtered across all projects or within a selected project.
- iOS chat controls for creating, selecting, and reopening conversations.
- Citation badges containing meeting and timestamp information.

The current retrieval implementation uses exact cosine search within a project instead of an approximate HNSW query. This favors recall and predictable project filtering at the current alpha scale. Transcript chunks use windows of complete speaker turns up to 150 words, while summaries, decisions, and tasks receive their own chunks.

Citation badges can navigate toward a meeting transcript, but audio playback and timestamp seeking are not yet connected. Real embedding-model, live model-response, Supabase, and Swift build checks must be completed on the team environment before these features are claimed as end-to-end verified.

### 2.5 iOS alpha application

The SwiftUI client currently provides three main areas:

- **Meetings:** project creation, meeting upload with consent, processing status, retry, purge, and rendering of stored summaries, decisions, transcripts, and candidate tasks.
- **Tasks:** a year and month calendar, project filters, approved server tasks, lifecycle changes, undo, and Apple Reminders export.
- **Chat:** project and meeting scope selection, new conversations, saved history, grounded answers, refusal behavior, and citation badges.

The client uses a configurable base URL and API token and can connect to the backend through a Cloudflare Tunnel. The repository includes scripts that configure and check the remote connection.

The client still loads seed data, does not reload the full project list from the server after a clean reinstall, and uses a static audio dock. These gaps prevent us from claiming a clean, persistent, seed-free alpha journey until they are resolved and tested.

## 3. Alpha Architecture

The alpha consists of the following integrated systems:

| Layer              | Current implementation                                                    | Current limitation                                                  |
| ------------------ | ------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Native client      | SwiftUI and SwiftData iOS application                                     | Seed data and static playback UI remain                             |
| Remote gateway     | Cloudflare Tunnel with bearer-token authentication                        | Shared-secret authentication is appropriate only for the team alpha |
| API and worker     | FastAPI routes and one-at-a-time meeting worker                           | Legacy JSON status path remains                                     |
| Audio processing   | FFmpeg, Whisper, and optional pyannote diarization                        | Named speaker matching and DER evaluation remain                    |
| Model extraction   | Codex or Claude with Pydantic contracts and evidence checks               | Cross-meeting reconciliation is not implemented                     |
| Persistence        | Supabase PostgreSQL with pgvector and append-only lifecycle audit records | Some attendee and storyline tables are unused                       |
| Retrieval and chat | Hybrid dense/full-text retrieval, structured answers, verified citations  | Live model and embedding checks remain; no streaming                |
| Evaluation         | Offline ASR and extraction harnesses with saved predictions               | RAG and sequence evaluations are incomplete                         |

The architecture intentionally separates audio recognition, structured extraction, storage, retrieval, and presentation. This lets us measure failure sources independently instead of attributing every downstream error to one model call.

## 4. Current Verification Evidence

### 4.1 Automated tests

The chat implementation report records 116 passing tests against PostgreSQL 16 and pgvector, including 25 tests added for chat and retrieval. These tests cover chunk construction, citation verification, refusal rules, project isolation, meeting scoping, task-state freshness, dismissed-task exclusion, hybrid ranking, history, model failure behavior, purge behavior, and index replacement after retry.

The prior Milestone 2 evaluation also included deterministic tests for extraction scoring and ASR scoring. Those tests verify known edit counts, missing outputs, duplicates, invalid citations, input hashes, and split constraints.

**Before submission:**

- [PLACEHOLDER: run the complete current Python test suite and record the command, date, commit, pass count, skips, failures, and warnings.]
- [PLACEHOLDER: run Ruff and record its result.]
- [PLACEHOLDER: build the iOS application in Xcode and record the target, simulator/device, OS version, and result.]
- [PLACEHOLDER: record any Swift test results.]

### 4.2 End-to-end alpha verification

The repository contains the components needed for an alpha demonstration, but the complete user journeys in `docs/checklist.md` are not yet marked verified. The team should execute and record one clean run using the checked-in AMI audio fixture or another consented recording.

Required verification sequence:

1. Start from a clean app installation or a documented clean local state.
2. Connect to the configured backend and PostgreSQL database.
3. Create a project and confirm it is visible after relaunch.
4. Upload a consented MP3 or WAV recording.
5. Observe processing and open the completed meeting.
6. Confirm that the transcript, summary, decisions, evidence, and candidate tasks came from PostgreSQL.
7. Approve one candidate task, confirm it appears in Tasks and Apple Reminders, change its lifecycle state, and undo that change.
8. Ask one supported project question and verify every displayed citation.
9. Ask one unsupported question and verify the fixed refusal.
10. Relaunch the application and confirm that meeting, task, and chat history persist.
11. Purge the test project and verify removal of its meeting, task, retrieval, and chat data.

[PLACEHOLDER: add date, tester, commit SHA, device, backend configuration, input fixture, observed result, screenshots, and demo-video link.]

## 5. Evaluation and Results

### 5.1 Results carried forward from Milestone 2

The ASR pilot compared Whisper tiny and base through the supplied CCB transcription bridge on 12 one-minute AMI clips containing 1,738 reference words. The frozen test subset contained six clips and 705 reference words. Test WER was 28.79% for tiny and 24.54% for base, a 4.26 percentage-point absolute reduction. Test real-time factors were 0.021 and 0.039 respectively. The sample is too small for a general performance claim.

The task-extraction development diagnostic compared promise rules, Codex independent extraction, and Granite Code 8B on 24 synthetic micro-meetings containing 15 labeled obligations. The reported task F1 proxies were 0.710, 0.897, and 0.692 respectively. These labels were AI-authored and the matching protocol was primarily lexical, so the figures remain development diagnostics rather than held-out semantic accuracy.

The prior error review identified candidate issues involving negated promises, quoted examples, cross-turn acceptance, duplicate repetitions, corrections, unknown owners, joint ownership, and merged actions. Human adjudication remains incomplete.

### 5.2 Milestone 3 evaluation targets

Milestone 3 must evaluate the newly integrated behavior rather than repeat only the Milestone 2 component results.

#### A. Cross-meeting continuity

Create or finalize a reviewed three-meeting sequence containing at least:

- A new commitment with an owner and deadline.
- A later deadline change.
- Explicit completion of an earlier task.
- An unaccepted suggestion.
- An ambiguous reference that should require review.
- A task that is not mentioned again and must remain open.

Compare the expected task state after every meeting against the application output. Report task creation, update, duplicate, unsupported completion, and final-state accuracy with numerators and denominators.

[PLACEHOLDER: reconciliation implementation, reviewed sequence, baseline, measurements, and error examples.]

#### B. Retrieval and grounded-answer evaluation

Build a reviewed set of supported and unsupported questions spanning multiple projects and meetings. Evaluate retrieval separately from answer generation.

Recommended measurements are:

| Measurement         | Definition                                                                                   | Result                  |
| ------------------- | -------------------------------------------------------------------------------------------- | ----------------------- |
| Recall@K            | Fraction of supported questions whose labeled evidence appears in the top K retrieved chunks | [PLACEHOLDER]           |
| Reciprocal rank     | Rank of the first labeled supporting chunk                                                   | [PLACEHOLDER]           |
| Citation validity   | Displayed citations whose quoted text is present in the referenced stored source             | [PLACEHOLDER]           |
| Answer faithfulness | Reviewed answers supported by their cited evidence                                           | [PLACEHOLDER]           |
| Refusal accuracy    | Unsupported questions that receive the fixed refusal                                         | [PLACEHOLDER]           |
| Project isolation   | Cross-project leakage cases across adversarial scope tests                                   | [PLACEHOLDER: target 0] |

Include questions involving decisions, tasks, transcript statements, follow-up questions, dismissed tasks, and facts absent from the project. Preserve the question set, expected evidence, settings, raw outputs, and review decisions.

#### C. Human qualitative review

Two team members should independently review a shared sample containing ordinary successes and representative failures. Use the existing dimensions of evidence support, owner attribution, coverage, ambiguity handling, and usefulness. Add Milestone 3 performance dimensions for response time and estimated cost.

[PLACEHOLDER: reviewer names, review date, sample size, scores, disagreements, adjudication, and 3-5 supported failure patterns.]

#### D. Latency, usage, and cost

The extraction providers already return elapsed time and token usage, and the evaluation harness summarizes observed latency. Milestone 3 should extend this instrumentation to the integrated alpha path and chat queries.

For each tested workload, report:

- Model and provider version.
- Input duration or transcript size.
- Retrieved chunk count and prompt size for chat.
- Input and output tokens when exposed by the provider.
- End-to-end and model-call latency.
- Estimated monetary cost using the price in effect on the measurement date.
- Cache behavior, if any. No cache benefit should be claimed without observed cache-hit data.

| Workload              |   Sample size | Median latency |   P95 latency | Mean input/output tokens | Estimated cost |
| --------------------- | ------------: | -------------: | ------------: | -----------------------: | -------------: |
| Meeting transcription | [PLACEHOLDER] |  [PLACEHOLDER] | [PLACEHOLDER] |                      N/A |  [PLACEHOLDER] |
| Structured extraction | [PLACEHOLDER] |  [PLACEHOLDER] | [PLACEHOLDER] |            [PLACEHOLDER] |  [PLACEHOLDER] |
| Project chat          | [PLACEHOLDER] |  [PLACEHOLDER] | [PLACEHOLDER] |            [PLACEHOLDER] |  [PLACEHOLDER] |

Latency and cost must be interpreted together with quality. A faster or cheaper configuration is useful only if it preserves the required extraction, retrieval, citation, and refusal behavior.

## 6. Privacy, Safety, and Responsible Use

Meeting recordings can contain personal information, unpublished research, or confidential discussion. The alpha therefore requires explicit meeting-level consent before upload, keeps private recordings and credentials out of Git, scopes retrieval by project, and protects routes with a bearer token.

The chat system verifies citations rather than displaying model-supplied identifiers directly. If no citation survives verification, it returns a fixed refusal instead of an unsupported answer. Dismissed tasks are excluded from retrieval, and deletion cascades remove related chat and retrieval records.

Current limits must be stated clearly:

- The team authentication model uses a shared secret and is not production multi-user authorization.
- Selective transcript redaction is not implemented.
- Participant-level consent and voice-profile controls are not implemented.
- Voice embeddings and named-speaker matching are not active.
- Audio deletion and database deletion must be verified together in the purge test.
- Project-scope unit tests exist, but an end-to-end isolation test must still be recorded.

[PLACEHOLDER: document the completed privacy/purge test and any TA guidance received.]

## 7. What Remains Before Submission

### Required for a credible Milestone 3 alpha

- [ ] Confirm the official rubric, submission format, page limit, deadline, and required TA check-in.
- [ ] Run and record the complete Python tests and lint checks on the submission commit.
- [ ] Build and test the current SwiftUI application.
- [ ] Complete one clean recording-to-results-to-task-to-chat user journey.
- [ ] Remove or gate seed data for the recorded alpha demonstration.
- [ ] Load projects from PostgreSQL after relaunch and verify persistence.
- [ ] Test real embeddings and one live Codex or Claude chat response.
- [ ] Create a supported-query and unsupported-query RAG evaluation set.
- [ ] Measure retrieval, citation, refusal, isolation, latency, token usage, and cost.
- [ ] Complete the two-reviewer human rubric and adjudication log.
- [ ] Add screenshots and a short demonstration video.
- [ ] Freeze the submission commit and record exact reproduction instructions.

### Central product claim that remains incomplete

Cross-meeting task reconciliation is the core distinction between LabSync and an independent meeting summarizer. The current application stores task state and lets users change it, but it does not yet automatically match a later statement to an existing open task, arbitrate ambiguous matches, update a deadline, or flag a duplicate. The team should either implement and evaluate a narrow three-meeting reconciliation path before submission or explicitly present it as the highest-priority limitation. It must not be described as completed without measured sequence evidence.

### Valuable alpha improvements if time permits

- Connect `AVPlayer` to stored audio and seek from transcript and chat citations.
- Replace the JSON status route with PostgreSQL-backed status throughout.
- Add approved-task editing with audit records.
- Save meeting duration and display a real waveform or deterministic progress UI.
- Add summary editing and formatted sharing.
- Add transcript redaction.
- Add attendee storylines and named-speaker matching only after consent and evaluation rules are settled.

## 8. Team Contributions

The following table is a draft based on repository history and the previous milestone plan. Every team member should review and correct it before submission.

| Team member       | Current contribution summary                                                                                                        | Evidence to add                                                                             |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Will Liu          | PostgreSQL/API integration, iOS and backend data flow, setup documentation, and project chat with hybrid RAG and verified citations | [PLACEHOLDER: PRs/commits, testing performed, and Milestone 3 write-up contribution]        |
| Guadalupe Cantera | Database/schema work and data research from earlier milestones                                                                      | [PLACEHOLDER: Milestone 3 work, reviewed labels, Data Card or privacy updates, PRs/commits] |
| Bryan Yang        | Audio/extraction integration, evaluation harness and reports, backend/client integration, and submission synthesis                  | [PLACEHOLDER: Milestone 3 PRs/commits, end-to-end verification, and evaluation results]     |

[PLACEHOLDER: replace contribution summaries with team-confirmed descriptions and include the required individual/group reporting format from the rubric.]

## 9. Work Plan to Complete Milestone 3

| Task                                                                | Proposed owner                   | Completion evidence                                                                               |
| ------------------------------------------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------- |
| Confirm rubric and submission requirements                          | Team                             | Requirements copied into this draft and every section mapped to a rubric item                     |
| Verify current backend, database, tunnel, and iOS build             | Will                             | Dated clean-run log, screenshots, device/configuration details, and demo clip                     |
| Implement and evaluate the narrow three-meeting reconciliation path | Will and Bryan                   | Reviewed sequence, saved outputs, baseline comparison, state metrics, and failures                |
| Complete human label and error review                               | Guadalupe with a second reviewer | Filled review records, adjudication notes, and 3-5 supported failure patterns                     |
| Build RAG question set and score retrieval/answers                  | Bryan with team review           | Versioned inputs, expected sources, saved outputs, metrics, and examples                          |
| Collect latency, token, and cost measurements                       | Bryan and Will                   | Reproducible measurement table with versions and workload descriptions                            |
| Finalize privacy and deletion verification                          | Team                             | Recorded isolation, refusal, purge, and credential-handling checks                                |
| Assemble and review final submission                                | Team                             | PDF or required artifact, repository link, demo link, contribution statement, and final proofread |

Assignments remain proposed until confirmed by the team.

## 10. Known Limitations and Claims Boundary

At this checkpoint, the repository supports a substantial alpha: consented upload, transcription, structured extraction, PostgreSQL persistence, task review and lifecycle changes, Apple Reminders export, and project chat with verified citations. Automated tests cover the individual backend behaviors extensively.

The current evidence does not yet establish reliable cross-meeting reconciliation, general accuracy on natural research meetings, diarization accuracy, named-speaker recognition, complete audio citation seeking, selective redaction, or production security. The existing extraction numbers are development proxies on synthetic examples, and the ASR test covers only two meeting series. Milestone 3 claims will be limited to the exact configurations, inputs, and user journeys measured before submission.

## 11. Reproduction and References

Primary repository documentation:

- `README.md` for installation, backend, tunnel, iOS, and evaluation commands.
- `docs/checklist.md` for the current end-to-end completion checklist.
- `docs/writeups/systems/Chat RAG & Citations.md` for the retrieval, answer, citation, and persistence design.
- `docs/archive/milestone_2/submission_draft.md` for the prior dataset, baseline, and evaluation record.
- `docs/archive/milestone_2/results/README.md` for task-extraction measurements.
- `docs/archive/milestone_2/transcription_results.md` for ASR measurements.
- `docs/archive/milestone_2/failure_review.md` and `failure_review_log.md` for the prepared human-review materials.
- `tests/fixtures/evaluation/README.md` and `tests/fixtures/asr/README.md` for evaluation protocols.

[PLACEHOLDER: add the official Milestone 3 assignment citation, TA feedback, final commit SHA, demo link, and any external sources used in the final report.]
