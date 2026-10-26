# Milestone 3: Alpha Application and Model Integration

**Course:** CIS-5980
**Track:** AI Engineering
**Team:** Will Liu, Guadalupe Cantera, and Bryan Yang
**Repository:** https://github.com/BryanDYang/guardian-agent
**Draft updated:** October 21, 2026
**Planned submission date:** October 26, 2026

> **Draft status:** This document follows the AI Engineering requirements and 100-point rubric in `contexts/milestone_3/Milestone 3.pdf`. It records the alpha implementation currently present in the repository and separates implemented features from verified end-to-end behavior. Bracketed placeholders identify work or evidence that must be completed before submission. The final deliverable must be submitted as a single PDF unless the teaching staff directs otherwise.

## October 21 status checkpoint

Personal audio acceptance was executed October 20. Bryan supplied eight short
scripted recordings and account mappings; assistant-run native checks verified
bounded automatic approval, tentative-statement abstention, manual date/Calendar
handling, recipient opt-out, repeated-task reconciliation, manual completion/Undo,
and relaunch persistence. Four messages were captured; zero real-inbox deliveries
were tested. C/D dates were entered manually. F1's ASR date was October 3 rather
than the speaker-confirmed October 23, and its candidate omitted the deadline.
F2 yielded no completion candidate. A was already auto-approved at baseline,
so it does not count as a clean manual-approval demo. See the
[run ledger and provenance](../../evidence/demo_walkthrough.md#versioned-run-ledger).

The October 20 implementation passed 317 backend tests, Ruff, and a signed
simulator build. New-project automation defaults are on; recipient opt-out and
evidence/identity gates remain. Settings save through Done. The failed D/E
recordings recovered with a configured working Codex CLI; the cause of the
older CLI's upstream HTTP 429 remains unresolved.

The eight-case [human-review worksheet](human_review.md) is prepared but its
human judgments are blank. Assistant integration checks are not independent
human review or a systematic audio/transcript fidelity evaluation. A clean
screen-recorded journey with actual supported/unsupported chat outputs remains
pending. Automatic dates/completion, recurring reminders, live inbox delivery,
reviewed AMI sequence scores, and live two-host recovery remain open.

Manual in-app recording and **Import Zoom Summary** are implemented. Automatic
Zoom account connection/webhooks/live-call ingestion and a real authorized Zoom
artifact have not been validated. These are separate from the audio acceptance.
The current priority is a frozen retrieval comparison, human-reviewed output
quality, representative latency/usage measurements, and complete report artifacts.

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

| Design question       | What we considered                                            | Decision and rationale                                                                                                                                            | Evidence still needed                         |
| --------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| Retrieval strategy    | Dense-only, sparse-only, and hybrid retrieval                 | Use dense and PostgreSQL full-text retrieval fused with reciprocal rank fusion. Dense search handles paraphrases while sparse search preserves exact terminology. | Required retrieval ablation                   |
| Retrieval index       | HNSW approximate search or exact project-scoped cosine search | Use exact cosine search at the current alpha scale to avoid filtered approximate-search recall loss.                                                              | Query latency and corpus-size measurement     |
| Retrieval unit        | Individual turns or bounded multi-turn windows                | Pack complete turns into windows up to 150 words and index summaries, decisions, and tasks separately.                                                            | Chunking comparison if time permits           |
| Citation format       | Model-generated database IDs or temporary source handles      | Give the model temporary handles, then map verified quotes to stored IDs and timestamps on the server.                                                            | Human faithfulness review and live-model test |
| Unsupported questions | Best-effort answer or evidence requirement                    | Return a fixed refusal when no verified citation remains.                                                                                                         | Refusal-accuracy evaluation                   |
| Model adaptation      | Fine-tuning or constrained provider models                    | Use provider models with Pydantic contracts because current data volume does not justify fine-tuning and the task depends on grounding and workflow integration.  | Final prompts, versions, settings, and hashes |

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

Shared mode uses PostgreSQL jobs/status, private audio storage, and recoverable worker leases. Legacy local mode retains `meeting.json` records. Do not treat the two modes as interchangeable recording owners.

### October 11 native continuity validation

A separate scripted project exercised undated approval, repeated mentions, a reviewed deadline change, and reviewed completion across four meetings. The simulator and PostgreSQL retained one accepted task ID, three evidence-backed reconciliation audits, and the completed state after relaunch. The run exposed date display, review guidance, empty-state, and stale Undo-token issues; the follow-up fixes were validated natively. All 283 backend tests, Ruff checks, and the simulator build passed.

These are deliberately seeded text-only candidates, including the completion candidate. This is workflow and persistence evidence, not audio processing or model accuracy evidence. Completion-only update extraction, independent sequence labels, paired evaluations, reminders, external alpha testing, and two-host recovery remain unfinished. See `docs/evidence/demo_walkthrough.md` for the observed steps.

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

Remaining pipeline work includes calibrated speaker identification, attendee storylines, task deduplication and cross-meeting reconciliation, meeting duration persistence, and verification of PostgreSQL-backed status in shared mode; legacy local mode retains JSON status.

### 2.3 Task review, lifecycle, and immediate follow-through

A reviewer can approve, edit, or dismiss a pending task. Deadlines are optional:
accepted undated work appears in To-do; dated tasks also appear in Calendar.
Review and accepted-task edits are audited. Approved tasks support `open`, `done`,
and `dropped`, with lifecycle Undo protected against stale tokens and later edits.
Dated approvals can also produce a phone-side Apple Reminders export.

Reviewed reconciliation can attach a later candidate to one existing accepted
task as a repeated mention, deadline change, or completion, preserving task ID
and evidence history. Similarity alone does not authorize an update. A seeded
four-meeting native fixture verified this workflow on October 11; natural-data
sequence accuracy and completion-only proposal extraction remain open.

Project owners can enable a narrow experimental automatic-approval rule after
human-confirmed speaker/account mapping. It requires explicit self-commitment,
supported evidence/title, available embeddings, and no unresolved deadline or
possible duplicate. This is not calibrated AI confidence. Other tasks stay pending.

Immediate email queues transactionally for an approved assigned task when project
email and recipient preferences permit. A separate worker records capture or
provider acceptance, with retry/idempotency protection and pre-send state/access
checks. Default capture mode sends nothing externally. The current AMI walkthrough
has no real recipient mapping or captured email; personal-recording acceptance
and configured live inbox delivery are still pending.

Recurring reminders, automatic relative-date calculation, automatic later-task
updates, calendar-event creation, and calendar-based attendee matching remain
unimplemented. One-time export and immediate email do not establish a complete
reminder lifecycle. See [follow-through details](follow_through.md).

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

Citation navigation and authenticated audio playback/seeking are implemented, with selected simulator observations recorded in the walkthrough. Full native citation journeys, physical audibility, and measured answer/citation quality remain open.

### 2.5 iOS alpha application

The SwiftUI client currently provides four main areas:

- **Meetings:** project creation, meeting upload with consent, processing status, retry, purge, and rendering of stored summaries, decisions, transcripts, and candidate tasks.
- **Tasks:** a year and month calendar, project filters, approved server tasks, lifecycle changes, undo, and Apple Reminders export.
- **Chat:** project and meeting scope selection, new conversations, saved history, grounded answers, refusal behavior, and citation badges.
- **Profile:** account details, workspaces and invitations, sign-in methods, account deletion, and voice enrollment or consent revocation.

The client uses a configurable base URL and the signed-in user's Supabase access token and can connect to the backend through a Cloudflare Tunnel. The repository includes scripts that configure and check the remote connection.

The client no longer seeds sample projects on launch. It refreshes projects from `GET /api/v1/projects`, and cache preparation removes legacy seed project IDs. Seed data remains for previews and tests. The audio dock uses AVPlayer with authenticated temporary-file download and seeking. Clean-install persistence and the complete native journey still require recorded verification.

### 2.6 Accounts, membership, and voice consent

Supabase sign-in replaces shared-secret authentication. Profiles, project membership, invitations, and account deletion have connected client/API paths. Project access is restricted to members. Profile displays account and workspace data from the backend.

Voice enrollment records three clips after separate consent, applies speech/quality and cross-clip consistency checks, and stores an L2-normalized 256-dimensional voiceprint. Raw enrollment clips are deleted. Users can skip enrollment, re-record, or revoke consent; revocation deletes the voiceprint without locking the account. The client receives enrollment status rather than the embedding. Quality gates and speaker-match thresholds still need calibration on real phone recordings.

## 3. Alpha Architecture

The alpha consists of the following integrated systems:

| Layer              | Current implementation                                                    | Current limitation                                                                           |
| ------------------ | ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Native client      | SwiftUI and SwiftData iOS application                                     | Full native/physical-device acceptance remains open                                          |
| Remote gateway     | Cloudflare Tunnel with Supabase access-token authentication               | Project membership is enforced; live authorization checks remain                             |
| API and worker     | FastAPI with optional PostgreSQL jobs and recoverable shared workers      | Two-device recovery and API failover routing remain unverified                               |
| Audio processing   | FFmpeg, Whisper, and optional pyannote diarization                        | Speaker matching exists; calibration and DER evaluation remain                               |
| Model extraction   | Codex or Claude with Pydantic contracts and evidence checks               | Reviewed reconciliation exists; automatic update proposals and sequence accuracy remain open |
| Persistence        | Supabase PostgreSQL with pgvector and append-only lifecycle audit records | Matched attendees are written; storyline tables remain unused                                |
| Retrieval and chat | Hybrid dense/full-text retrieval, structured answers, verified citations  | Live model and embedding checks remain; no streaming                                         |
| Evaluation         | Offline ASR and extraction harnesses with saved predictions               | RAG and sequence evaluations are incomplete                                                  |

The architecture intentionally separates audio recognition, structured extraction, storage, retrieval, and presentation. This lets us measure failure sources independently instead of attributing every downstream error to one model call.

## 4. Current Verification Evidence

### 4.1 Automated tests

Latest recorded run, October 21: all **319 backend tests** passed against
isolated PostgreSQL; Ruff lint/format and diff checks passed. Added coverage
checks the evaluation baseline's project/meeting/dismissal filters and retention
of interrupted/not-run statuses. Two existing dependency deprecation warnings
remain. The implementation and results are committed as `af3a4b8`.

The signed simulator build last passed October 20. No iOS code changed in the
October 21 evaluation update, so no new build was run. These engineering checks
are separate from the partial live-model experiment and pending human quality
review. See the [dated evaluation evidence](../../evidence/demo_walkthrough.md#october-21-ami-retrieval-comparison-and-partial-live-answer-run).
Repeat required checks on the final submission commit.

The chat implementation report records 116 passing tests against PostgreSQL 16 and pgvector, including 25 tests added for chat and retrieval. These tests cover chunk construction, citation verification, refusal rules, project isolation, meeting scoping, task-state freshness, dismissed-task exclusion, hybrid ranking, history, model failure behavior, purge behavior, and index replacement after retry.

The prior Milestone 2 evaluation also included deterministic tests for extraction scoring and ASR scoring. Those tests verify known edit counts, missing outputs, duplicates, invalid citations, input hashes, and split constraints.

**Before submission:**

- [PLACEHOLDER: run the complete current Python test suite and record the command, date, commit, pass count, skips, failures, and warnings.]
- [PLACEHOLDER: run Ruff and record its result.]
- [PLACEHOLDER: build the iOS application in Xcode and record the target, simulator/device, OS version, and result.]
- [PLACEHOLDER: record any Swift test results.]

### 4.2 End-to-end alpha verification

The repository contains the components needed for an alpha demonstration, but the complete user journeys in `docs/archive/checklist.md` are not yet marked verified. The team should execute and record one clean run using the checked-in AMI audio fixture or another consented recording.

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
5. Evaluate a reviewed recurring-meeting sequence if we claim cross-meeting reconciliation. Measure reviewed reconciliation separately from autonomous proposals and retain the remaining continuity limitations.

The RAG set and controlled comparison are the immediate priority. A 14-question assistant-proposed AMI development diagnostic and read-only runner are prepared in `tests/fixtures/rag/` and `scripts/evaluate_rag.py`. Retrieval results are in Section 5.2; human validation and answer-quality scoring remain pending. The live answer run is partial due to repeated 180-second timeouts. Speaker and sequence evaluations support our feature claims; the assignment does not prescribe these particular datasets.

### 5.1 Results carried forward from Milestone 2

The ASR pilot compared Whisper tiny and base through the supplied CCB transcription bridge on 12 one-minute AMI clips containing 1,738 reference words. The frozen test subset contained six clips and 705 reference words. Test WER was 28.79% for tiny and 24.54% for base, a 4.26 percentage-point absolute reduction. Test real-time factors were 0.021 and 0.039 respectively. The sample is too small for a general performance claim.

The task-extraction development diagnostic compared promise rules, Codex independent extraction, and Qwen3 8B Q4_K_M on 24 synthetic micro-meetings containing 15 labeled obligations. The reported task F1 proxies were 0.710, 0.897, and 0.933 respectively. Qwen3 replaced the earlier code-specialized Granite comparison; the archived results report is authoritative. These labels were AI-authored and the matching protocol was primarily lexical, so the figures remain development diagnostics rather than held-out semantic accuracy.

The prior error review identified candidate issues involving negated promises, quoted examples, cross-turn acceptance, duplicate repetitions, corrections, unknown owners, joint ownership, and merged actions. Bryan verified the AI-drafted full review of all 72 outputs on September 26. The independent 12-output spot check and full second independent review remain pending; gold-label review is also incomplete.

### 5.2 Required ablation

The October 21 development diagnostic compares dense-only retrieval with the
production hybrid/full-text/RRF path. The frozen set contains 12 designated
source-target questions and two proposed unsupported questions over the existing
219-chunk TS3005a-d index. Questions and targets were assistant-authored before
retrieval execution from generated decisions and inspected stored evidence;
human validation remains pending. This is not held-out natural-meeting accuracy.

Both variants use the same query embeddings (`text-embedding-3-small`, 1,536
dimensions), eligible corpus and dismissal filters, scope, K=8, source builder,
empty history, chat instructions, and requested `gpt-5.6-sol` answer model. Hybrid
adds full-text ranking and RRF (k=60, leg depth=40). Eight positive questions
are meeting-scoped; four positive and both negative questions are project-scoped.
Production retrieval defaults were not changed by this experiment.

The live answer run also exposed a citation-format failure in the hybrid LCD
case. The target was retrieved at rank 4, but the model's quotation added a
`Decision:` prefix absent from the source's quotable text. The validator dropped
that sole citation, so the final output refused despite the available evidence.
The raw response, sources, and final output must remain together for review.
This is an observed pipeline failure, not evidence that retrieval alone missed
the answer. Prompt/source-format changes should be a subsequent version, not
silently applied during this frozen run.

| Variant | Target Hit@1 | Target Hit@3 | Target Hit@8 | Target MRR@8 | Median retrieval round trip |
| --- | --- | --- | --- | --- | --- |
| Dense only | 9/12 | 10/12 | 11/12 | 0.7944 | 87.30 ms |
| Hybrid | 4/12 | 7/12 | 11/12 | 0.5188 | 88.31 ms |

Each positive question designates one decision chunk. These metrics measure
recovery/rank of that target, not exhaustive Recall@K or answer correctness:
alternative transcript chunks may support the answer. Three retrieval timings
per question/variant include client/database network time; variant-first order
alternates. The roughly 1 ms median difference on this tiny sample is not a
reliable service-speed advantage. No significance test or load test was run.

**Interpretation:** both retrieve 11/12 designated targets at K=8. Dense ranks
more designated targets first; hybrid recovers the price-decision target that
dense misses, but loses the rubber-housing target from the top eight. Equal
Hit@8 hides these different misses. In the returned price answers, dense still
used another source to answer the values. Therefore target rank alone cannot
establish a quality winner. Keep production hybrid unchanged pending source-level
human answer review and a broader frozen set. Sparse-only and chunking ablations
were not run. The dataset/protocol is in
[`tests/fixtures/rag/`](../../../tests/fixtures/rag/README.md); machine outputs and
human review status are in the [walkthrough](../../evidence/demo_walkthrough.md#october-21-ami-retrieval-comparison-and-partial-live-answer-run).

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

October 21 measurements separate retrieval, source loading, and model response
from the native UI. Query embedding was 1.825 s for a batch of 14 questions.
Retrieval round-trip medians were 87.30 ms dense and 88.31 ms hybrid (42 samples
each). Verified source loading for three representative questions took about
0.72-0.88 s. These components were measured separately; do not sum their medians
and call the result mobile end-to-end latency.

| Completed-call workload | N | Median model + validation | Mean input/output tokens | Mean cached-input tokens | Hypothetical API-equivalent per completed call |
| --- | --- | --- | --- | --- | --- |
| Project-scoped supported chat | 6 | 5.082 s | 17,432.17 / 117.17 | 0 | $0.072072 |
| Meeting-scoped supported chat | 3 | 4.955 s | 18,021.33 / 87.33 | 8,874.67 | $0.041883 |

**Failure boundary:** the answer run stopped after 3 dense calls timed out at
180 s. There were 9 completed calls, 3 timeouts, 1 interrupted request, and 15
not run; unsupported-answer refusal accuracy is not measured. Successful-call
medians omit failed calls and do not establish typical reliability or a causal
speed advantage. Dense completed-call median was 108.93 s (N=3), hybrid 4.52 s
(N=6); these unequal selected samples and observed caching prevent a fair model
latency conclusion. Human answer/citation judgments remain pending. The precise
[outputs, timing and failure ledger](../../evidence/demo_walkthrough.md#october-21-ami-retrieval-comparison-and-partial-live-answer-run)
are in the repository.

Pricing assumptions checked October 21: [official OpenAI standard rates](https://developers.openai.com/api/docs/pricing)
for short-context `gpt-5.6-sol` are $4/M input, $0.40/M cached input, $20/M output;
embedding input is $0.02/M for `text-embedding-3-small`. Applying those rates to
CLI-reported completed-call usage gives a hypothetical $0.558082 for nine
answers, not the observed subscription charge. Locally counted embedding input
is 206 tokens, estimated $0.00000412; API embedding usage was not captured.
The formula and actual usage are in the versioned summary. Failed/interrupted
request usage, infrastructure, indexing, subscription allocation, and any
regional/priority surcharges are excluded. Cost for those requests is unknown,
not zero. No P95, load/concurrency result, or mobile end-to-end latency is claimed.

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

Milestone 2 measured ASR and independent-meeting extraction. Milestone 3 now includes a source-recovery ablation and partial answer/latency/cost evidence; human semantic review, refusal-answer coverage, and expanded isolation evaluation remain pending. ASR errors can propagate into extraction, anonymous speaker labels do not establish identity, and candidate tasks may merge, omit, or misattribute work. Automatic approval is experimental and limited to confirmed accounts and explicit evidence-gated self-commitments; ambiguous candidates remain in review. The evaluation data remains small and partly synthetic, so claims are limited to the measured inputs and configurations.

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

The backend currently runs on Apple Silicon Macs and depends on separately supplied transcription code. Optional shared mode stores audio in private Supabase Storage and jobs/status in PostgreSQL, with recoverable worker leases and project membership checks. Bryan has verified a shared-mode backend locally; live two-device recovery and automatic API routing remain unverified. The first model download is large, chat is not streamed, and legacy local-mode status still depends on a local JSON record. Before submission, we will verify clean installation, database migrations, real embeddings, live inference, project persistence, refusal behavior, isolation, and deletion. Shared-mode database status, audio seeking, and reviewed reconciliation are now implemented. Remaining work includes full native acceptance, live recovery, selective redaction, broader participant controls, and evaluated automatic continuity.

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

The [roadmap, scope, and acceptance plan](roadmap.md) defines current targets, execution order, validation gates, and next-phase boundaries. The [implementation checklist](../checklist.md) tracks code; the [native walkthrough](../../evidence/demo_walkthrough.md) tracks observed acceptance. Targets are not completed claims.

### Required for a credible Milestone 3 alpha

- [X] Identify the official Milestone 3 rubric and required components.
- [X] Confirm the Canvas deadline, page limit if any, and any TA check-in expectations.
- [ ] Run and record the complete Python tests and lint checks on the submission commit.
- [ ] Build and test the current SwiftUI application.
- [ ] Complete one clean recording-to-results-to-task-to-chat user journey.
- [X] Remove seed data from real app launches; keep preview/test fixtures.
- [ ] Verify the recorded clean-install demonstration contains no seed data.
- [X] Implement server project refresh through `GET /api/v1/projects`.
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

Cross-meeting continuity remains the central product claim to evaluate. Human-confirmed reconciliation with stable task identity is implemented and passed a seeded native workflow. Completion-only update proposals, autonomous state changes, reviewed natural-sequence expectations, and measured sequence accuracy remain unfinished. Immediate email is implemented in capture mode; recurring follow-through is not. Neither the seeded fixture nor the current AMI screenshots establish the complete product claim.

### Valuable alpha improvements if time permits

- Complete physical-device audio and full citation-navigation acceptance for the implemented player.
- Verify shared-mode PostgreSQL status and live worker recovery; decide how to migrate remaining local-mode records.
- Complete real-recording acceptance of the implemented approved-task editing/audit path.
- Save meeting duration and display a real waveform or deterministic progress UI.
- Add summary editing and formatted sharing.
- Add transcript redaction.
- Add attendee storylines; calibrate and evaluate the implemented consent-based speaker matching.

## 10. Team Contributions and Advanced Extensions

The rubric requires a substantive advanced-extension write-up and metrics for each team member. The following table is a draft based on repository history and the previous milestone plan. Every team member should review and correct it before submission.

| Team member       | Current contribution summary                                                                                                                                                                                                        | Proposed advanced extension and required evidence                                                                                                                                                                                                                                                                                                  |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Will Liu          | PostgreSQL/API integration, iOS and backend data flow, Supabase accounts and membership, voice enrollment and speaker matching, task-similarity flags, setup documentation, and project chat with hybrid RAG and verified citations | **Integrated RAG/native chat and consent-based speaker identity.** Add speaker correct/false-match and abstention counts if claimed as an extension, plus retrieval comparison results, live-query success count, latency, citation validity, Swift build result, PRs/commits, and a substantive explanation of design choices and failures. |
| Guadalupe Cantera | Database/schema work and data research from earlier milestones                                                                                                                                                                      | **Reviewed data and human evaluation.** Add number of labels reviewed, agreement and disagreement results, finalized policies, error categories, privacy checks, PRs/commits, and a substantive explanation of how review changed the system.                                                                                                |
| Bryan Yang        | Audio/extraction integration, evaluation harness and reports, backend/client integration, and submission synthesis                                                                                                                  | **Evaluation and cross-meeting continuity.** Add sequence and RAG results, latency/cost instrumentation, end-to-end checks, PRs/commits, and a substantive explanation of the comparison design and resulting changes.                                                                                                                       |

[PLACEHOLDER: replace contribution summaries with team-confirmed descriptions and include the required individual/group reporting format from the rubric.]

### Bryan: evaluation and auditable follow-through extension (draft)

Bryan's extension combines reproducible evaluation with the application's
meeting-to-task evidence trail. The implementation separates transcript/model
outputs from reviewed application state: a named voice is not automatically a
verified account, a candidate is not an approved task, and a quoted passage is
not sufficient proof of semantic correctness. Reviewed reconciliation preserves
the original task identity and records the source meeting and lifecycle audit.
Immediate follow-up uses a transactional outbox and a task/recipient uniqueness
constraint; it is separate from recurring reminder scheduling.

The October 20 personal sequence exposed these boundaries in use. Eight scripted
clips exercised clear/tentative promises, dates, opt-out, a repeated obligation,
and completion. Four follow-ups were captured. Manual approval, date edits,
reconciliation, completion/Undo, and relaunch persistence were verified. The
same run exposed a date transcription error and absent completion proposals;
those were preserved as failures instead of being counted as automatic successes.
The implemented auto-approval policy remains narrow and uncalibrated on natural
meetings. The assistant executed the native checks and bookkeeping from Bryan's
recordings; independent human quality judgments remain pending.

For retrieval, Bryan's evaluation work now includes a frozen 14-question
assistant-proposed development diagnostic, read-only dense/hybrid runner, saved
source targets and rankings, and measured timing. Both variants recover 11/12
designated targets at K=8, while dense has higher target MRR in this sample
(0.7944 versus 0.5188). Alternative transcript evidence can still support an
answer when the designated decision is missing. This motivates separating
source-target ranking from human answer/citation evaluation; it does not justify
a blanket production retrieval change. One new local regression verifies that
the dense baseline retains project/meeting filters and dismissal behavior; all
319 backend tests passed. Live model-call failures and completed-call usage
must be reported alongside successful latency, not discarded.

Evidence is versioned in the walkthrough, question fixture, and run artifacts.
Bryan must review this contribution description; teammates must confirm shared
ownership. Remaining extension evidence includes human adjudication, broader
scope/isolation questions, semantic answer scores, and the clean native demo.
This draft does not attribute independent human review to the assistant or claim
that every cross-meeting update is inferred automatically.

### Individual reflection survey

Each team member must separately submit the non-graded reflection survey covering work completed and lessons learned, whether every member contributed materially, and any other feedback for the teaching staff. This survey is separate from the single group PDF.

## 11. Work Plan for the Next Milestone

| Task                                                                | Proposed owner                    | Completion evidence                                                                                      |
| ------------------------------------------------------------------- | --------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Confirm remaining submission logistics                              | Team                              | Canvas deadline, any page limit, and check-in expectations recorded                                      |
| Verify current backend, database, tunnel, and iOS build             | Will                              | Dated clean-run log, screenshots, device/configuration details, and demo clip                            |
| Implement and evaluate the narrow three-meeting reconciliation path | Will and Bryan                    | Reviewed sequence, saved outputs, baseline comparison, state metrics, and failures                       |
| Calibrate and evaluate speaker identity and task-similarity flags   | Will with independent team review | Reviewed identities/task pairs, held-out recordings, false matches, abstentions, and threshold decisions |
| Complete human label and error review                               | Guadalupe with a second reviewer  | Filled review records, adjudication notes, and 3-5 supported failure patterns                            |
| Build RAG question set and score retrieval/answers                  | Bryan with team review            | Versioned inputs, expected sources, saved outputs, metrics, and examples                                 |
| Collect latency, token, and cost measurements                       | Bryan and Will                    | Reproducible measurement table with versions and workload descriptions                                   |
| Finalize privacy and deletion verification                          | Team                              | Recorded isolation, refusal, purge, and credential-handling checks                                       |
| Assemble and review final submission                                | Team                              | PDF or required artifact, repository link, demo link, contribution statement, and final proofread        |

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
- Source-recovery ablation and partial latency/cost results are recorded; human labels, semantic answer scores, and full live answer coverage remain incomplete after repeated timeouts.
- The iOS build and real model/embedding behavior must be verified on the team environment.
- Legacy local-mode JSON status remains; shared-mode status and real playback are implemented. Seed-free launch, server refresh, and the full native flow still need clean-run evidence.

### Planned next steps

The owner-assigned work plan in Section 11 prioritizes end-to-end verification, the retrieval ablation, RAG evaluation, human review, cross-meeting continuity, performance measurements, Model Card and System Card completion, and final single-PDF assembly.

## 13. Known Limitations and Claims Boundary

At this checkpoint, the repository supports a substantial alpha: consented upload, transcription, structured extraction, PostgreSQL persistence, task review and lifecycle changes, Apple Reminders export, and project chat with verified citations. Automated tests cover the individual backend behaviors extensively.

The current evidence does not yet establish reliable cross-meeting reconciliation, general accuracy on natural research meetings, diarization accuracy, named-speaker recognition, complete audio citation seeking, selective redaction, or production security. The existing extraction numbers are development proxies on synthetic examples, and the ASR test covers only two meeting series. Milestone 3 claims will be limited to the exact configurations, inputs, and user journeys measured before submission.

## 14. Rubric Coverage

| Official requirement                                        | Draft section              | Status                                                      |
| ----------------------------------------------------------- | -------------------------- | ----------------------------------------------------------- |
| Track declaration                                           | Front matter and Section 1 | Complete                                                    |
| Development path, M2 changes, and decision log              | Sections 1 and 2           | Draft complete; evidence pending                            |
| Configuration and reproducibility                           | Sections 3-7 and 15        | Partial; exact final settings pending                       |
| At least one ablation                                       | Section 5.2                | Source-recovery pilot executed; human labels/answer scoring pending |
| Targeted tests, robustness, bias, safety, and hallucination | Sections 4, 5.3, and 8     | Partial; updated results required                           |
| Latency and cost                                            | Section 5.3                | Component/partial completed-call measurements; failures disclosed |
| Updated results and error analysis                          | Section 5                  | Partial; M3 results and human adjudication required         |
| Alpha flow and inference service                            | Sections 1-4               | Implemented in parts; recorded end-to-end evidence required |
| README run instructions and examples                        | Section 15 references      | Present; clean-run verification required                    |
| Model Card and System Card drafts                           | Sections 6 and 7           | Drafted; exact settings and results pending                 |
| Weekly check-in, team roles, and work plan                  | Sections 10-12             | Team confirmation required                                  |
| Per-member extension write-up and metrics                   | Section 10                 | Placeholders require completion                             |
| GitHub link                                                 | Front matter               | Complete                                                    |
| Single PDF                                                  | Submission packaging       | Not yet exported                                            |

The rubric allocates 60 points to core progress and evidence quality and 40 points to the alpha deliverable and documentation artifacts. Missing the ablation, updated results, Model Card, System Card, or per-member extension evidence would directly leave graded requirements incomplete.

## 15. Reproduction and References

Primary repository documentation:

- `README.md` for installation, backend, tunnel, iOS, and evaluation commands.
- `docs/archive/checklist.md` for the current end-to-end completion checklist.
- `docs/evidence/demo_walkthrough.md` for recording native acceptance evidence.
- `docs/weekly_journal.md` for the Week 6 and Week 7 progress/reflections.
- `src/labsync/voice.py`, `src/labsync/embeddings.py`, and `src/labsync/db/meetings.py` for current speaker and task-similarity settings.
- `docs/archive/writeups/systems/Chat RAG & Citations.md` for the retrieval, answer, citation, and persistence design.
- `docs/archive/milestone_2/submission_draft.md` for the prior dataset, baseline, and evaluation record.
- `docs/archive/milestone_2/results/README.md` for task-extraction measurements.
- `docs/archive/milestone_2/transcription_results.md` for ASR measurements.
- `docs/archive/milestone_2/failure_review.md` and `failure_review_log.md` for the prepared human-review materials.
- `tests/fixtures/evaluation/README.md` and `tests/fixtures/asr/README.md` for evaluation protocols.
- `contexts/milestone_3/Milestone 3.pdf` for the official assignment and grading rubric.

[PLACEHOLDER: add TA feedback, final commit SHA, demo link, and any external sources used in the final report.]

### October 10 setup checkpoint

The signed-in iOS app created four real AMI projects and uploaded seven recordings: TS3005a-d (one connected dev project), IS1008a (isolation/validation), IS1009a (evaluation candidate), and ES2004a (separate evaluation trial). All uploads were confirmed in shared PostgreSQL job records. At the checkpoint, TS3005a and b had completed processing and other jobs were running or queued. Project-list persistence across app relaunch was observed. The simulator build passed, and Profile was visually verified in light and dark appearances. The third voice-enrollment prompt is now scripted; its effect on retries remains unmeasured.

This is partial native integration evidence. Transcript correctness, task review and continuity, cited answers/refusals, cross-project isolation, purge, clean-install behavior, external tester availability, and live two-host failover still require recorded acceptance runs. IS1009a and ES2004a were used in the Milestone 2 ASR pilot and cannot be presented as untouched evaluation inputs. See [shared backend setup](../../reference/shared_backend.md) and [native walkthrough](../../evidence/demo_walkthrough.md).

## October 11 implementation checkpoint (not final acceptance)

Speaker-name review now proposes direct introductions with source timestamps;
confirmed account links propagate to matching pending commitments. Accepted
undated work is supported in a native to-do view, with optional calendar dates.
A reviewer can reconcile a later candidate against an earlier accepted task as a
repeated mention, deadline update, or completion. Task identity and audited source
evidence are retained; similarity alone never changes a task. Stale reviews and
reopening completed work are rejected.

Validation: 282 backend tests against disposable PostgreSQL, Ruff, and simulator
build passed. This establishes implementation regressions, not AMI model quality.
Completion-only update extraction, automatic update proposals, reminder lifecycle,
reviewed sequence/RAG evaluations, full native acceptance, independent review,
external testers, and live two-host recovery remain open. Earlier limitations
and historical Milestone 2 results must not be presented as new improvements.
