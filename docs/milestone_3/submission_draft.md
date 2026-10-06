# Milestone 3: Alpha Application and Model Integration

**Course:** CIS-5980
**Track:** AI Engineering
**Team:** Will Liu, Guadalupe Cantera, and Bryan Yang
**Repository:** https://github.com/BryanDYang/guardian-agent
**Draft updated:** October 6, 2026
**Planned submission date:** October 26, 2026 (confirm in Canvas; assignment PDF defers to Canvas)

> **Draft status:** This document follows the AI Engineering requirements and 100-point rubric in `contexts/milestone_3/Milestone 3.pdf`. It records the alpha implementation currently present in the repository and separates implemented features from verified end-to-end behavior. Bracketed placeholders identify work or evidence that must be completed before submission. The final deliverable must be submitted as a single PDF unless the teaching staff directs otherwise.

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

### Milestone 3 development path

We selected prompt engineering, structured outputs, retrieval-augmented generation, and lightweight orchestration rather than model fine-tuning. This path fits the application because the central challenges are grounding extraction in transcript evidence, maintaining structured application state, retrieving private project history, and refusing unsupported answers. We are not training a new foundation model.

The main development changes beyond the Milestone 2 baselines are:

- Replacing independent transcript-only outputs with persistent PostgreSQL project state.
- Adding schema-constrained extraction and evidence validation at the application boundary.
- Connecting the iOS application to project, meeting, transcript, task, and chat APIs.
- Adding hybrid dense and full-text retrieval over transcripts, summaries, decisions, and tasks.
- Verifying model citations against retrieved sources and refusing unsupported answers.
- Adding task review, lifecycle transitions, audit records, undo, and Apple Reminders export.
- Adding Supabase sign-in, profiles, project membership and invitations, consent-based voice enrollment, and project-member speaker matching.
- Flagging candidate tasks similar to earlier approved open tasks without automatically merging or updating them.

### Decision log

| Design question | What we considered | Decision and rationale | Evidence still needed |
| --- | --- | --- | --- |
| Retrieval strategy | Dense-only, sparse-only, and hybrid retrieval | Use dense and PostgreSQL full-text retrieval fused with reciprocal rank fusion. Dense search handles paraphrases while sparse search preserves exact terminology. | Required retrieval ablation |
| Retrieval index | HNSW approximate search or exact project-scoped cosine search | Use exact cosine search at the current alpha scale to avoid filtered approximate-search recall loss. | Query latency and corpus-size measurement |
| Retrieval unit | Individual turns or bounded multi-turn windows | Pack complete turns into windows up to 150 words and index summaries, decisions, and tasks separately. | Chunking comparison if time permits |
| Citation format | Model-generated database IDs or temporary source handles | Give the model temporary handles, then map verified quotes to stored IDs and timestamps on the server. | Human faithfulness review and live-model test |
| Unsupported questions | Best-effort answer or evidence requirement | Return a fixed refusal when no verified citation remains. | Refusal-accuracy evaluation |
| Model adaptation | Fine-tuning or constrained provider models | Use provider models with Pydantic contracts because current data volume does not justify fine-tuning and the task depends on grounding and workflow integration. | Final prompts, versions, settings, and hashes |

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

With `--diarize`, the pipeline now matches speaker centroids against enrolled project members using WeSpeaker voiceprints and cosine similarity. A match supplies a display name to the transcript and extraction input; a matched commitment owner can receive `assignee_user_id`. Unmatched speakers remain anonymous. Match thresholds are provisional and recognition quality has not been measured.

Remaining pipeline work includes calibrated speaker identification, attendee storylines, task deduplication and cross-meeting reconciliation, meeting duration persistence, and removal of the JSON status dependency.

### 2.3 Human review and task lifecycle

The iOS client and backend support the human review path for candidate tasks. A reviewer can approve, edit, or dismiss a pending item. Approval requires an explicit due date. Approved tasks appear in the Tasks calendar and can be copied to Apple Reminders.

Approved tasks support `open`, `done`, and `dropped` lifecycle states. Each lifecycle change appends an audit record with the previous state, new state, and a unique revert token. The user can undo a lifecycle change through that token.

Current limitations are:

- Edits made during candidate review are not yet included in the task audit log.
- Editing an already approved task is not implemented.
- Calendar-event creation and ingest-time calendar matching are not implemented.
- A candidate can return `matches_task` when its title embedding has cosine similarity of at least 0.80 with an earlier approved open task in the same project. The candidate is still inserted; duplicate prevention, deadline updates, completion inference, and ambiguous-match arbitration are not implemented.
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

The SwiftUI client currently provides four main areas:

- **Meetings:** project creation, meeting upload with consent, processing status, retry, purge, and rendering of stored summaries, decisions, transcripts, and candidate tasks.
- **Tasks:** a year and month calendar, project filters, approved server tasks, lifecycle changes, undo, and Apple Reminders export.
- **Chat:** project and meeting scope selection, new conversations, saved history, grounded answers, refusal behavior, and citation badges.
- **Profile:** account details, workspaces and invitations, sign-in methods, account deletion, and voice enrollment or consent revocation.

The client uses a configurable base URL and the signed-in user's Supabase access token and can connect to the backend through a Cloudflare Tunnel. The repository includes scripts that configure and check the remote connection.

The client no longer seeds sample projects on launch. It refreshes projects from `GET /api/v1/projects`, and cache preparation removes legacy seed project IDs. Seed data remains for previews and tests. Audio playback still uses a static dock. Clean-install persistence and the complete native journey still require recorded verification.

### 2.6 Accounts, membership, and voice consent

Supabase sign-in replaces shared-secret authentication. Profiles, project membership, invitations, and account deletion have connected client/API paths. Project access is restricted to members. Profile displays account and workspace data from the backend.

Voice enrollment records three clips after separate consent, applies speech/quality and cross-clip consistency checks, and stores an L2-normalized 256-dimensional voiceprint. Raw enrollment clips are deleted. Users can skip enrollment, re-record, or revoke consent; revocation deletes the voiceprint without locking the account. The client receives enrollment status rather than the embedding. Quality gates and speaker-match thresholds still need calibration on real phone recordings.

## 3. Alpha Architecture

The alpha consists of the following integrated systems:

| Layer              | Current implementation                                                    | Current limitation                                                  |
| ------------------ | ------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Native client      | SwiftUI and SwiftData iOS application                                     | Static playback UI remains; clean-install journey unverified                             |
| Remote gateway     | Cloudflare Tunnel with Supabase access-token authentication                        | Project membership is enforced; live authorization checks remain |
| API and worker     | FastAPI routes and one-at-a-time meeting worker                           | Legacy JSON status path remains                                     |
| Audio processing   | FFmpeg, Whisper, and optional pyannote diarization                        | Speaker matching exists; calibration and DER evaluation remain                    |
| Model extraction   | Codex or Claude with Pydantic contracts and evidence checks               | Cross-meeting reconciliation is not implemented                     |
| Persistence        | Supabase PostgreSQL with pgvector and append-only lifecycle audit records | Matched attendees are written; storyline tables remain unused                       |
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
3. Sign in, create a project, and confirm it is visible after relaunch without seed data. Verify that a non-member cannot access it.
4. For the voice demonstration, enroll three consented clips, run the worker with `--diarize`, inspect correct and unknown speaker labels, and verify revocation deletes the voiceprint.
5. Upload a consented MP3 or WAV recording.
6. Observe processing and open the completed meeting.
7. Confirm that the transcript, summary, decisions, evidence, and candidate tasks came from PostgreSQL.
8. Approve one candidate task, confirm it appears in Tasks and Apple Reminders, change its lifecycle state, and undo that change.
9. Ask one supported project question and verify every displayed citation.
10. Ask one unsupported question and verify the fixed refusal.
11. Relaunch the application and confirm that meeting, task, and chat history persist.
12. Purge the test project and verify removal of its meeting, task, retrieval, and chat data.

[PLACEHOLDER: add date, tester, commit SHA, device, backend configuration, input fixture, observed result, screenshots, and demo-video link.]

## 5. Evaluation and Results

### Evaluation scope for this milestone

Updated evaluation is required for the Milestone 3 changes. Milestone 2 ASR and extraction results remain useful baselines, but do not measure the new retrieval, answers, identity matching, or integrated workflow. We do not need to replace every dataset or repeat every old baseline unchanged.

The smallest coherent evaluation plan is:

1. Freeze one human-reviewed RAG question set with supporting source IDs, supported and unsupported questions, and project-isolation cases. Run dense-only and hybrid retrieval on the same corpus, questions, answer model, prompt, and K. Sparse-only is an additional diagnostic. This supplies the targeted ablation and updated retrieval/answer results together.
2. Use those same runs to review answer correctness, citation faithfulness, refusals, failures, latency, tokens, and cost. Include ordinary successes and failures in the independent human review. Quote validity alone does not establish that an answer is supported.
3. Record one clean native end-to-end alpha journey, including sign-in, server project persistence, task review, chat, and deletion. This is integration evidence, separate from model-quality measurements.
4. Evaluate speaker matching on consented labeled recordings with enrolled and unenrolled speakers if it is presented as an advanced extension. Report correct/incorrect identification, abstentions, unknown-speaker false matches, and downstream owner attribution. Calibrate on development recordings and keep evaluation recordings separate.
5. Evaluate a reviewed recurring-meeting sequence if we claim cross-meeting reconciliation. Until state-update logic exists, measure only the similarity flag or state explicitly that full continuity remains incomplete.

The RAG set and controlled comparison are the immediate priority. Speaker and sequence evaluations support our feature claims; the assignment does not prescribe these particular datasets. No new Milestone 3 model-quality measurements are recorded in this draft yet.

### 5.1 Results carried forward from Milestone 2

The ASR pilot compared Whisper tiny and base through the supplied CCB transcription bridge on 12 one-minute AMI clips containing 1,738 reference words. The frozen test subset contained six clips and 705 reference words. Test WER was 28.79% for tiny and 24.54% for base, a 4.26 percentage-point absolute reduction. Test real-time factors were 0.021 and 0.039 respectively. The sample is too small for a general performance claim.

The task-extraction development diagnostic compared promise rules, Codex independent extraction, and Qwen3 8B Q4_K_M on 24 synthetic micro-meetings containing 15 labeled obligations. The reported task F1 proxies were 0.710, 0.897, and 0.933 respectively. Qwen3 replaced the earlier code-specialized Granite comparison; the archived results report is authoritative. These labels were AI-authored and the matching protocol was primarily lexical, so the figures remain development diagnostics rather than held-out semantic accuracy.

The prior error review identified candidate issues involving negated promises, quoted examples, cross-turn acceptance, duplicate repetitions, corrections, unknown owners, joint ownership, and merged actions. Bryan verified the AI-drafted full review of all 72 outputs on September 26. The independent 12-output spot check and full second independent review remain pending; gold-label review is also incomplete.

### 5.2 Required ablation

The rubric requires at least one targeted comparison that isolates a key design choice. Dense-only versus hybrid is our primary two-version ablation; sparse-only is an optional diagnostic. Our proposed comparison evaluates retrieval strategies on the same frozen question set, indexed corpus, answer model, prompt, and top-K setting.

| Variant | Dense retrieval | Full-text retrieval | RRF fusion | Recall@K | MRR | Faithful answers | Refusal accuracy | Median latency |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Dense only | Yes | No | No | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| Sparse only | No | Yes | No | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| Hybrid | Yes | Yes | Yes | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |

This comparison will show whether hybrid retrieval improves evidence recall or ranking enough to justify its added complexity and latency. If time permits, a secondary comparison will test individual transcript turns against 150-word complete-turn windows.

[PLACEHOLDER: freeze the question set, run each variant, add results, interpret the differences, and record the resulting design decision.]

### 5.3 Milestone 3 evaluation targets

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

#### C. Robustness, bias, and safety tests

Targeted robustness cases should include ASR errors, long transcript turns, paraphrased questions, exact technical terms, follow-up questions with pronouns, missing owners, missing deadlines, negated commitments, quoted examples, duplicate statements, and model-provider failure. Safety tests should include unsupported questions, attempts to retrieve another project's data, dismissed tasks, purged meetings, and fabricated citation handles.

The intended alpha is English-only and the existing evaluation does not establish comparable performance across accents, speaking styles, genders, disciplines, group sizes, or languages. Where the available consented or public data permits, report results by relevant audio condition or speaker group. Otherwise, state that subgroup evidence is unavailable and avoid fairness claims.

[PLACEHOLDER: list the final targeted cases, sample counts, pass criteria, subgroup or condition coverage, observed failures, and resulting changes.]

#### D. Human qualitative review

As our chosen reliability protocol, rather than a prescribed reviewer count in the assignment, two team members should independently review a shared sample containing ordinary successes and representative failures. Use the existing dimensions of evidence support, owner attribution, coverage, ambiguity handling, and usefulness. Add Milestone 3 performance dimensions for response time and estimated cost.

[PLACEHOLDER: reviewer names, review date, sample size, scores, disagreements, adjudication, and 3-5 supported failure patterns.]

#### E. Speaker identification and task-similarity evaluation

Voice matching and candidate similarity introduce separate error risks. For speaker identification, use known identities and unenrolled speakers, report false matches and abstentions with denominators, record consent and revocation behavior, and inspect owner-attribution errors downstream. The current 0.60 threshold and 0.10 margin are implementation defaults, not measured acceptance criteria.

For `matches_task`, label repeated obligations and similar but distinct tasks across meetings. Report flag precision/recall and false matches at the current 0.80 threshold. A flag result must not be counted as a successful merge, deadline update, or completion.

[PLACEHOLDER: reviewed inputs, development/evaluation separation, settings, saved predictions, counts, failures, and calibration decisions.]

#### F. Latency, usage, and cost

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

## 6. Model Card Draft

### Intended use

The alpha is intended to help consenting research teams review meeting transcripts, summaries, decisions, commitments, suggestions, and supporting evidence across recurring meetings. It supports human-reviewed follow-through and historical question answering within a selected project.

### Uses outside the intended scope

The system is not intended to record people without consent, evaluate employee or student performance, infer productivity, replace official project records, treat transcripts as proof that work occurred, make high-stakes decisions, or provide unrestricted access across organizations. It is not a general factual assistant and should refuse questions unsupported by stored project evidence.

### Models and configuration

- Whisper performs English speech recognition through the supplied CCB bridge.
- Optional pyannote diarization assigns speaker labels. Consent-based matching uses `pyannote/wespeaker-voxceleb-resnet34-LM` voiceprints (256 dimensions), with provisional cosine threshold 0.60 and margin 0.10. Without a confident match, labels remain anonymous.
- Codex or Claude performs schema-constrained meeting extraction and grounded answer generation.
- OpenAI `text-embedding-3-small` produces 1,536-dimensional passage embeddings. Task-title similarity uses the first 384 dimensions; `all-MiniLM-L6-v2` is not used.
- PostgreSQL full-text search supplies the sparse retrieval leg.

[PLACEHOLDER: record exact final model identifiers, provider or CLI versions, prompts and hashes, temperatures or reasoning settings, embedding version, top K, RRF constant, chunk size, and run date.]

### Evaluation summary and limitations

Milestone 2 measured ASR and independent-meeting extraction. Milestone 3 will add retrieval, grounded-answer, refusal, isolation, latency, and cost measurements plus the required ablation. ASR errors can propagate into extraction, anonymous speaker labels do not establish identity, and candidate tasks may merge, omit, or misattribute work. Human review is required before approval. The evaluation data remains small and partly synthetic, so claims are limited to the measured inputs and configurations.

## 7. System Card Draft

### Components and data flow

The SwiftUI client uploads consented audio to an authenticated FastAPI service, directly or through Cloudflare Tunnel. A sequential worker normalizes and transcribes the recording, optionally diarizes speakers, obtains structured extraction output, validates source evidence, and writes results to PostgreSQL. The retrieval service chunks and embeds meeting records. Chat queries use project-scoped hybrid retrieval, a schema-constrained answer model, server-side citation verification, and persistent conversation storage. The client displays results and lets users review task candidates and lifecycle changes.

### Guardrails

- Upload requires affirmative consent in the application flow.
- API routes except health require Supabase sign-in; project access requires membership, with non-member requests returning 404.
- Voice enrollment requires separate consent and three quality-checked clips; raw clips are deleted and revocation deletes the stored voiceprint.
- Database reads and retrieval searches are scoped by project UUID.
- Structured extraction uses typed contracts and evidence checks.
- Candidate tasks require human approval.
- Chat citations require a valid source handle and a quote matching stored source text.
- Answers without verified citations are replaced by a fixed refusal.
- Task lifecycle changes append audit records and return revert tokens.
- Project purge cascades through related meeting, retrieval, task, and chat records.

### Operational constraints and mitigations

The backend currently runs on an Apple Silicon Mac, depends on separately supplied transcription code, stores audio locally, and uses Supabase authentication with project membership checks. The first model download is large, chat is not streamed, and some pipeline status still depends on a local JSON record. Before submission, we will verify clean installation, database migrations, real embeddings, live inference, project persistence, refusal behavior, isolation, and deletion. Longer-term mitigations include database-backed status, selective redaction, broader participant-level recording consent controls, audio seeking, and reviewed reconciliation logic.

## 8. Privacy, Safety, and Responsible Use

Meeting recordings can contain personal information, unpublished research, or confidential discussion. The alpha therefore requires explicit meeting-level consent before upload, keeps private recordings and credentials out of Git, scopes retrieval by project, and protects routes with a bearer token.

The chat system verifies citations rather than displaying model-supplied identifiers directly. If no citation survives verification, it returns a fixed refusal instead of an unsupported answer. Dismissed tasks are excluded from retrieval, and deletion cascades remove related chat and retrieval records.

Current limits must be stated clearly:

- Supabase sign-in, project membership, and invitations are implemented; production security and live end-to-end authorization have not been established.
- Selective transcript redaction is not implemented.
- Voice enrollment consent, skip, re-record, and revocation are implemented. Broader participant-level recording consent controls remain incomplete.
- Voice embeddings and named-speaker matching are implemented when diarization is enabled, but thresholds and recognition accuracy remain uncalibrated.
- Audio deletion and database deletion must be verified together in the purge test.
- Project-scope unit tests exist, but an end-to-end isolation test must still be recorded.

[PLACEHOLDER: document the completed privacy/purge test and any TA guidance received.]

## 9. What Remains Before Submission

### Required for a credible Milestone 3 alpha

- [x] Identify the official Milestone 3 rubric and required components.
- [ ] Confirm the Canvas deadline, page limit if any, and any TA check-in expectations.
- [ ] Run and record the complete Python tests and lint checks on the submission commit.
- [ ] Build and test the current SwiftUI application.
- [ ] Complete one clean recording-to-results-to-task-to-chat user journey.
- [x] Remove seed data from real app launches; keep preview/test fixtures.
- [ ] Verify the recorded clean-install demonstration contains no seed data.
- [x] Implement server project refresh through `GET /api/v1/projects`.
- [ ] Verify project persistence after relaunch and reinstall.
- [ ] Test real embeddings and one live Codex or Claude chat response.
- [ ] Create a supported-query and unsupported-query RAG evaluation set.
- [ ] Run and interpret at least one targeted ablation.
- [ ] Measure retrieval, citation, refusal, isolation, latency, token usage, and cost.
- [ ] Complete the two-reviewer human rubric and adjudication log.
- [ ] Finalize the Model Card and System Card with exact settings and results.
- [ ] Add a substantive advanced-extension write-up and metrics for each team member.
- [ ] Add screenshots and a short demonstration video.
- [ ] Freeze the submission commit and record exact reproduction instructions.
- [ ] Export and visually inspect the required single submission PDF.

### Central product claim that remains incomplete

Cross-meeting task reconciliation is the core distinction between LabSync and an independent meeting summarizer. The current application stores task state and lets users change it, and flags title-similar candidates against earlier approved open tasks. It does not yet merge duplicates, arbitrate ambiguous matches, update a deadline, or infer completion from later meetings. The team should either implement and evaluate a narrow three-meeting reconciliation path before submission or explicitly present it as the highest-priority limitation. It must not be described as completed without measured sequence evidence.

### Valuable alpha improvements if time permits

- Connect `AVPlayer` to stored audio and seek from transcript and chat citations.
- Replace the JSON status route with PostgreSQL-backed status throughout.
- Add approved-task editing with audit records.
- Save meeting duration and display a real waveform or deterministic progress UI.
- Add summary editing and formatted sharing.
- Add transcript redaction.
- Add attendee storylines; calibrate and evaluate the implemented consent-based speaker matching.

## 10. Team Contributions and Advanced Extensions

The rubric requires a substantive advanced-extension write-up and metrics for each team member. The following table is a draft based on repository history and the previous milestone plan. Every team member should review and correct it before submission.

| Team member | Current contribution summary | Proposed advanced extension and required evidence |
| --- | --- | --- |
| Will Liu | PostgreSQL/API integration, iOS and backend data flow, Supabase accounts and membership, voice enrollment and speaker matching, task-similarity flags, setup documentation, and project chat with hybrid RAG and verified citations | **Integrated RAG/native chat and consent-based speaker identity.** Add speaker correct/false-match and abstention counts if claimed as an extension, plus retrieval comparison results, live-query success count, latency, citation validity, Swift build result, PRs/commits, and a substantive explanation of design choices and failures. |
| Guadalupe Cantera | Database/schema work and data research from earlier milestones | **Reviewed data and human evaluation.** Add number of labels reviewed, agreement and disagreement results, finalized policies, error categories, privacy checks, PRs/commits, and a substantive explanation of how review changed the system. |
| Bryan Yang | Audio/extraction integration, evaluation harness and reports, backend/client integration, and submission synthesis | **Evaluation and cross-meeting continuity.** Add sequence and RAG results, latency/cost instrumentation, end-to-end checks, PRs/commits, and a substantive explanation of the comparison design and resulting changes. |

[PLACEHOLDER: replace contribution summaries with team-confirmed descriptions and include the required individual/group reporting format from the rubric.]

### Individual reflection survey

Each team member must separately submit the non-graded reflection survey covering work completed and lessons learned, whether every member contributed materially, and any other feedback for the teaching staff. This survey is separate from the single group PDF.

## 11. Work Plan for the Next Milestone

| Task                                                                | Proposed owner                   | Completion evidence                                                                               |
| ------------------------------------------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------- |
| Confirm remaining submission logistics                              | Team                             | Canvas deadline, any page limit, and check-in expectations recorded                               |
| Verify current backend, database, tunnel, and iOS build             | Will                             | Dated clean-run log, screenshots, device/configuration details, and demo clip                     |
| Implement and evaluate the narrow three-meeting reconciliation path | Will and Bryan                   | Reviewed sequence, saved outputs, baseline comparison, state metrics, and failures                |
| Calibrate and evaluate speaker identity and task-similarity flags | Will with independent team review | Reviewed identities/task pairs, held-out recordings, false matches, abstentions, and threshold decisions |
| Complete human label and error review                               | Guadalupe with a second reviewer | Filled review records, adjudication notes, and 3-5 supported failure patterns                     |
| Build RAG question set and score retrieval/answers                  | Bryan with team review           | Versioned inputs, expected sources, saved outputs, metrics, and examples                          |
| Collect latency, token, and cost measurements                       | Bryan and Will                   | Reproducible measurement table with versions and workload descriptions                            |
| Finalize privacy and deletion verification                          | Team                             | Recorded isolation, refusal, purge, and credential-handling checks                                |
| Assemble and review final submission                                | Team                             | PDF or required artifact, repository link, demo link, contribution statement, and final proofread |

Assignments remain proposed until confirmed by the team.

## 12. Weekly Check-In, Blockers, and Next Steps

### Progress made

- Integrated PostgreSQL-backed projects, meetings, transcripts, summaries, decisions, tasks, and chat.
- Connected the iOS client to server project and meeting reads, task review and lifecycle APIs, and chat history and messages.
- Added hybrid project-scoped retrieval, structured answers, verified citations, grounded refusal, and persistent conversations.
- Added setup instructions for the team backend, local backend, Supabase, Cloudflare Tunnel, and iOS app.
- Added automated coverage for chat, retrieval, citation validation, scope isolation, failure behavior, purge, and indexing.
- Added accounts, membership and invitations, seed-free launch, server project refresh, consent-based voice enrollment, speaker identification, and task-similarity flags. These are implementation changes with acceptance and quality measurements still pending.

### Top blockers and risks

- No recorded clean end-to-end alpha verification exists yet.
- Task-similarity flags are implemented, but automatic cross-meeting state reconciliation and its sequence evaluation remain incomplete.
- Human review of labels and semantic matches is incomplete.
- The required ablation, updated RAG results, and latency/cost table are not complete.
- The iOS build and real model/embedding behavior must be verified on the team environment.
- The remaining JSON status dependency and static playback limit the alpha path; seed-free launch and server project refresh are implemented but need clean-run evidence.

### Planned next steps

The owner-assigned work plan in Section 11 prioritizes end-to-end verification, the retrieval ablation, RAG evaluation, human review, cross-meeting continuity, performance measurements, Model Card and System Card completion, and final single-PDF assembly.

## 13. Known Limitations and Claims Boundary

At this checkpoint, the repository supports a substantial alpha: consented upload, transcription, structured extraction, PostgreSQL persistence, task review and lifecycle changes, Apple Reminders export, and project chat with verified citations. Automated tests cover the individual backend behaviors extensively.

The current evidence does not yet establish reliable cross-meeting reconciliation, general accuracy on natural research meetings, diarization accuracy, named-speaker recognition, complete audio citation seeking, selective redaction, or production security. The existing extraction numbers are development proxies on synthetic examples, and the ASR test covers only two meeting series. Milestone 3 claims will be limited to the exact configurations, inputs, and user journeys measured before submission.

## 14. Rubric Coverage

| Official requirement | Draft section | Status |
| --- | --- | --- |
| Track declaration | Front matter and Section 1 | Complete |
| Development path, M2 changes, and decision log | Sections 1 and 2 | Draft complete; evidence pending |
| Configuration and reproducibility | Sections 3-7 and 15 | Partial; exact final settings pending |
| At least one ablation | Section 5.2 | Planned; results required |
| Targeted tests, robustness, bias, safety, and hallucination | Sections 4, 5.3, and 8 | Partial; updated results required |
| Latency and cost | Section 5.3 | Planned; measurements required |
| Updated results and error analysis | Section 5 | Partial; M3 results and human adjudication required |
| Alpha flow and inference service | Sections 1-4 | Implemented in parts; recorded end-to-end evidence required |
| README run instructions and examples | Section 15 references | Present; clean-run verification required |
| Model Card and System Card drafts | Sections 6 and 7 | Drafted; exact settings and results pending |
| Weekly check-in, team roles, and work plan | Sections 10-12 | Team confirmation required |
| Per-member extension write-up and metrics | Section 10 | Placeholders require completion |
| GitHub link | Front matter | Complete |
| Single PDF | Submission packaging | Not yet exported |

The rubric allocates 60 points to core progress and evidence quality and 40 points to the alpha deliverable and documentation artifacts. Missing the ablation, updated results, Model Card, System Card, or per-member extension evidence would directly leave graded requirements incomplete.

## 15. Reproduction and References

Primary repository documentation:

- `README.md` for installation, backend, tunnel, iOS, and evaluation commands.
- `docs/checklist.md` for the current end-to-end completion checklist.
- `docs/demo_walkthrough.md` for recording native acceptance evidence.
- `docs/weekly_journal.md` for the Week 6 and Week 7 progress/reflections.
- `src/labsync/voice.py`, `src/labsync/embeddings.py`, and `src/labsync/db/meetings.py` for current speaker and task-similarity settings.
- `docs/writeups/systems/Chat RAG & Citations.md` for the retrieval, answer, citation, and persistence design.
- `docs/archive/milestone_2/submission_draft.md` for the prior dataset, baseline, and evaluation record.
- `docs/archive/milestone_2/results/README.md` for task-extraction measurements.
- `docs/archive/milestone_2/transcription_results.md` for ASR measurements.
- `docs/archive/milestone_2/failure_review.md` and `failure_review_log.md` for the prepared human-review materials.
- `tests/fixtures/evaluation/README.md` and `tests/fixtures/asr/README.md` for evaluation protocols.
- `contexts/milestone_3/Milestone 3.pdf` for the official assignment and grading rubric.

[PLACEHOLDER: add TA feedback, final commit SHA, demo link, and any external sources used in the final report.]
