# Week 1

- Created repository document markdown files
  - README.md
  - LICENSE
  - CONTRIBUTING.md
  - CODE_OF_CONDUCT.md
  - CI integration via `.github/workflows/ci.yml` with a passing smoke test
- Created milestone_1 documents
  - pitch_deck.md
  - project_proposal.md
- Created a diagram workflow of the full scope of the project

# Week 2

## What needs to be done

- Create a train/val/test split of datasets
- Define how you judge candidate outputs, both quantitatively with automated scores and qualitatively with structured grading rubrics, using real input/output examples.
  - Create a LLM as a judge rubric (1 - 5) grading system to judge the Agent's output for assessing hallucination, completeness, reasoning coherence, or adherence to formatting constraints.
- Look for open source governance layers to benchmark against.

## What got done

- Refined the Milestone 1 proposal after the team meeting.
  - Narrowed the project to a visual context-governance workbench for coding agents.
  - Defined the governed, ungoverned, and prompt-only comparison conditions.
  - Clarified the MVP, stretch goals, out-of-scope work, risks, timeline, and requested faculty feedback.
  - Added preliminary choices for the React and TypeScript front end, FastAPI back end, SQLite storage, Pytest, and Playwright.
- Created a six-slide pitch deck draft aligned with the current proposal.
- Created and refined the project workflow diagram, including the decision ledger and the evidence path from candidate context to evaluated outcome.
- Expanded the evaluation planning.
  - Documented candidate benchmark scenarios such as deprecated API migration, cross-directory scope leakage, poisoned memory, context-budget saturation, and long-horizon drift.
  - Documented proposed reliability, rule-compliance, context-efficiency, conflict-resolution, and latency metrics.
  - Moved detailed formulas, statistical methods, and threshold calibration into the Milestone 2 evaluation plan so Milestone 1 stays focused on scope and direction.
- Added a Milestone 2 TODO list covering the prototype, model integration, governance contracts, pilot, and evaluation calibration.
- Added the weekly team journal and the repository code of conduct, and updated the README with the team name.

## Current blockers and decisions needed

- Select the first local or open-source coding model and runtime instead of leaving the model integration unspecified.
- Define the Phase 2 evaluation implementation in enough detail to connect each controlled fixture to automated policy checks, code tests, traces, and paired-run reports.
- Create the train, validation, and test split after the scenario fixture format and labeling rules are frozen.
- Agree on the LLM-as-judge rubric and determine which qualities require human review instead of automated scoring.
- Identify an appropriate open-source governance baseline for comparison.

# Week 3

## What got done

- Met with the professor and TA twice to discuss the revised project direction and received approval to proceed with a research meeting follow-through assistant.
- Updated the [Milestone 1 proposal](milestone_1/project_proposal.md) from the team's Word submission draft, covering the project charter, MVP, architecture, evaluation plan, responsible use, roles, timeline, and $75 planning budget.
- Clarified that proactive follow-through is a required MVP capability based on the professor discussion. Added scheduled reminders for outstanding commitments, user-configured delivery, cancellation and rescheduling after task changes, and corresponding evaluation and demo requirements.
- Revised the six-slide [pitch deck](milestone_1/pitch_deck.pptx) to emphasize follow-through between meetings, show reminder and completion examples, and align its scope with the proposal.
- Drafted the Milestone 2 evaluation-harness checkpoint with task owners: one synthetic three-meeting sequence, expected task states, an independent-meeting extraction baseline, and an offline scorer checked against correct and deliberately incorrect outputs.
- Set up the repository with an installable Python CLI scaffold, locked dependencies, setup and contribution documentation, and a GitHub Actions smoke-test workflow. The application remains a scaffold; meeting processing and reminder delivery are not implemented yet.
- Reviewed the professor's `agent-sandbox` as a reference for packaging, dependency management, and offline testing, and documented its provenance. It is a simulation framework, separate from the meeting-artifact pipeline.
- Checked the submission against the Milestone 1 assignment. Confirmed the six-slide limit, required proposal sections, repository files, GitHub issue labels, and successful hosted CI runs. All three local CLI tests, lint, and formatting checks passed.

## Planned next steps

- Replace the remaining project-name placeholders, assemble the proposal and pitch slides into the required single PDF, visually review the export, and confirm the Canvas deadline.
- Confirm the proposed next-milestone assignments: Will for transcript/task contracts and extraction, Bryan for CLI/import integration and the evaluation runner, and Guadalupe for fixtures, annotations, and evaluation design.
- Prepare and review the first synthetic three-meeting development sequence, including completion, a changed deadline, an unaccepted suggestion, an ambiguous reference, and a task not mentioned again.
- Implement the transcript/task contract, independent-meeting extraction baseline, and offline scorer. Record the model and prompt versions and keep live API calls separate from CI.
- Confirm access to reusable sponsor components and the meeting-artifact format; start with timestamped transcript imports while audio integration is clarified.
- Select the initial follow-up delivery channel, scheduling defaults, supported OS, and calendar integration, then run a small model quality/cost pilot.

## Current blockers and dependencies

- **Meeting-pipeline and data access:** Access and permitted reuse of the sponsor's recording/transcription pipeline and any pre-recorded research-meeting sequences still need confirmation. Synthetic transcripts allow initial development to proceed.
- **Evaluation ground truth:** The annotation guide, labeled sequence, and scorer are planned but not yet implemented. The pilot dataset will support limited claims; broader evaluation depends on additional independent sequences.
- **Integration choices:** The first reminder delivery channel, OS/calendar integration, and model remain open decisions. Follow-up must work from validated task state and user-enabled settings.
- **Submission packaging:** A final combined PDF and project name are still needed. The deck passed structural checks, but its visual verification remains incomplete because the preview export failed.

# Week 4

## What got done

- Compared the [submitted Milestone 1 proposal](milestone_1/milestone1_proposal.pdf), [pitch deck](milestone_1/pitch_deck.pdf), and current repository against the [Milestone 2 requirements](<milestone_2/Milestone 2.pdf>) for the AI Engineering track.
- Identified the remaining graded deliverables: assembled data and a Data Card (40 points), plus a runnable evaluation harness, qualitative rubric, baselines, measured results, and initial error analysis (60 points).
- Confirmed that the repository currently provides a CLI scaffold and smoke tests. Meeting extraction, labeled evaluation fixtures, scoring, and baseline results remain unimplemented.
- Identified inconsistencies between the Milestone 1 artifacts: the submitted proposal specifies a native iOS client and PostgreSQL/pgvector, while the Markdown proposal and pitch deck describe a CLI/local service with SQLite. The submitted proposal also mentions SQLite in its budget. These choices need to be reconciled in Milestone 2.
- Outlined an implementation order centered on timestamped transcripts, labeled outputs, baseline predictions, and reproducible scoring. The full application is not required to complete the Milestone 2 evaluation deliverables.
- Created a meeting-assistant UI mockup covering the meetings list, meeting details, transcript playback, tasks, review actions, and chat experience.
- Completed writeups for the project story, technical stack, end-to-end workflow, and system boundaries. The system writeups cover native presentation, audio playback and deep linking, mobile OS integration, remote access, sequential ingestion, acoustic diarization, structured extraction and task reconciliation, unified persistence and hybrid search, and evaluation.
- Added a staged implementation workflow that starts with data contracts and persistence, continues through the audio and extraction pipeline, queue and API services, evaluation, and client integration. Added role ownership to divide the implementation across the team.
- Clarified from the project recap that the ingestion pipeline accepts MP4 or MP3 audio regardless of whether it comes from Zoom, a screen recorder, or a phone voice memo. Our in-person lab meetings do not create a Zoom recording queue.
- Researched public meeting datasets on Hugging Face and Kaggle. The AMI Meeting Corpus is a strong first prototype dataset because it is well annotated and includes dialogue acts, summaries, and decision-point labels for the TS3005a-d series. The ICSI Meeting Corpus is a realistic follow-up option for recurring research meetings; its Bmr, Bed, and Bro series provide real meetings and transcripts, but commitments and decisions would need to be labeled manually.
- Identified AMI TS3005a-d as the preferred initial sanity-check sequence and ICSI Bmr001-Bmr003, or the equivalent Bed sequence, as a possible development sequence for recurring-meeting evaluation. The pre-processed AMI diarization dataset may also help validate the pipeline while the system's own diarization is being developed.
- Confirmed that recordings of our own project meetings would best represent the final target setting, but written consent is required from teammates and the professor before recording or using them.

## Planned next steps

- **Guadalupe (proposed):** Assemble and annotate the first three-meeting development sequence, with a second team member reviewing labels. Cover completion, changed deadlines, unaccepted suggestions, ambiguous references, and tasks that remain open when not mentioned again. Draft the Data Card with provenance, permissions/licensing, access, splits, and limitations.
- **Will (proposed):** Define the transcript/task output contract and implement independent-meeting extraction and an applicable off-the-shelf open-source reference baseline. Preserve source IDs and record model versions, prompts, and run settings.
- **Bryan (proposed):** Build an evaluation runner that loads fixtures and saved predictions and reports task precision/recall, owner accuracy, duplicates, unsupported completions, and citation validity. Test the scorer with correct and deliberately incorrect outputs, and document commands and example results in the README.
- **Team:** Define a qualitative rubric with concrete examples, run the baselines on shared inputs, and produce a results table and initial failure analysis. Separate deterministic offline scoring tests from live model runs.
- **Team:** Complete the mandatory Milestone 2 TA check-in with a Data Card summary, harness instructions, baseline results, and blockers. Prepare the single submission PDF with the track declaration, repository link, weekly progress, contributions, and an owner-assigned plan for the next milestone; confirm the Canvas deadline.

## Current blockers and decisions needed

- **Scope alignment:** Confirm the authoritative application architecture and reminder scope, then document changes from Milestone 1 consistently across artifacts.
- **Data readiness:** Actual evaluation inputs and labels still need to be assembled. Sponsor pipeline/data permissions remain unconfirmed; synthetic transcripts can support initial development. Split by whole sequence or project to avoid related meetings leaking across sets, and keep the first development sequence out of held-out evaluation.
- **Baseline selection:** Choose an applicable open-source reference model or system in addition to the simple baseline. A proprietary-model-only comparison does not cover the open-source reference requirement.
- **Evaluation evidence:** Proposed quality targets are not measured results. The harness, qualitative rubric, baseline runs, and error analysis must be completed before reporting performance.
- **Coordination:** Confirm proposed task ownership, dataset coverage and split strategy, and the Milestone 2 TA check-in schedule.
- **Recording consent:** Obtain written consent from all teammates and the professor before recording project meetings or using those recordings for development or evaluation.

# Week 5 (September 21-27, 2026)

## What got done

- Implemented the initial meeting-processing backend with CCB transcription and structured Codex extraction. Added a SwiftUI iOS client and connected meeting uploads and project deletion to backend endpoints. Added Claude as an extraction provider and documented shared-backend setup. Native build and Simulator end-to-end verification remain outstanding.
- Built the extraction evaluation harness with 24 synthetic development cases containing 15 labeled obligations. Compared a simple rule baseline, Codex, and an off-the-shelf Qwen3 8B baseline. Replaced the initial Granite Code comparison with Qwen3 because Granite Code is specialized for coding.
- Recorded reproducible commands, model and prompt settings, saved outputs, and [baseline results](archive/milestone_2/results/README.md). Task F1 proxies were 0.710 for rules, 0.897 for Codex, and 0.933 for Qwen3. These are development-set action-matching proxies, not held-out semantic accuracy or a general model ranking.
- Added [scenario-level results](archive/milestone_2/results/slices.md) with denominators for explicit promises, acceptance and assignment, negation and quotation, owner and multi-action cases, and repetition and correction. Separated model errors from exact-text scoring artifacts and unresolved annotation policies.
- Measured Whisper tiny and base through CCB on disjoint AMI development and test splits using manual transcript references. Both configurations completed all 12 clips. Base reduced test WER by 4.26 percentage points compared with tiny on the small two-meeting test sample; no statistical significance or broad generalization is claimed.
- Expanded the initial failure-only worksheet into a [human review packet](archive/milestone_2/human_review.md) covering all 72 extraction outputs, including successful cases, complete outputs, evidence, and application-validation results. Bryan Yang verified and signed the AI-drafted [full review sheet](archive/milestone_2/human_review_reviewer_a.md) on September 26. This is one human-verified review, not two independent reviews.
- Prepared a separate 12-output [independent spot check](archive/milestone_2/human_review_spot_check.md) for Will. Identified unsupported commitments from negated or quoted speech, missed or merged obligations, stale deadlines, ambiguous ownership, and evidence-validation failures as priorities for follow-up. Two Qwen outputs fail application validation despite being scored by the offline harness.
- Updated the [Milestone 2 submission draft](archive/milestone_2/submission_draft.md), dataset documentation, README examples, limitations, and next-milestone plan. Integrated the evaluation documentation into main alongside the team's backend and setup changes.

## Planned next steps

- **Bryan:** Summarize the independent spot-check results when available, report agreement and disagreements without replacing the original scores, and consolidate supported failure patterns into Milestone 3 changes. Version any scorer changes and apply application evidence validation consistently across methods.
- **Will (proposed):** Complete the independent spot check without consulting the full review sheet, then complete a full second independent review for Milestone 3. Verify the native client and backend together end to end.
- **Guadalupe, with Will reviewing (proposed):** Human-review the synthetic gold labels and resolve joint-owner, task-granularity, and deadline policies before creating a new label version. Expand coverage toward natural meeting transcripts and recurring-meeting sequences.
- **Team:** Expand the audio pilot and conduct listening-based error review. Record specific TA feedback, confirm task ownership, and finalize the Milestone 2 submission PDF. Continue toward cross-meeting task reconciliation and proactive follow-through, which are not established by the current extraction results.

## Current blockers and limitations

- **Review reliability:** The full review started from AI-drafted judgments and has one human verifier. The independent spot-check sheet is still blank, so agreement statistics are not yet available. Output review does not substitute for independent review of the gold labels.
- **Evaluation scope:** Extraction results cover 24 synthetic development inputs. Audio results cover a small AMI sample. Neither establishes diarization quality, cross-meeting state tracking, reminder delivery, or full application reliability.
- **Scoring and contracts:** Lexical task matching and exact deadline comparison can differ from semantic correctness. Joint ownership and task granularity remain unresolved; the offline harness does not enforce application evidence validation uniformly across methods.
- **Reproduction and integration:** Audio reproduction requires separately supplied CCB source. A completed native build and Simulator end-to-end verification are not established in the report. Saved baseline results should not be treated as measurements of every currently supported backend configuration.

# Week 6 (September 28-October 4, 2026)

**Did:** We integrated project chat with hybrid retrieval and verified citations, and connected more of the iOS app to authenticated backend data. I worked on setup documentation and the Milestone 3 draft, separating implemented features from verified behavior.
**Blocked on:** A reviewed RAG question set and live retrieval/model evaluation; component tests do not establish answer quality.
**Next:** Run a controlled comparison of hybrid retrieval against vector-only retrieval on the same labeled questions.

One specific system change was grouping consecutive transcript turns into windows of up to 150 words instead of retrieving each turn separately. Short turns often lack context, while long turns can exceed the embedding model's input limit. The windows aim to preserve enough surrounding discussion to answer questions about decisions and ownership.

We have not measured this change's effect on answer quality. The implementation includes chunking and citation-validation tests, but those check mechanics, not whether real retrieval finds better evidence. Integration and setup received attention before we had a labeled question set ready. That leaves an uncomfortable gap: we can explain why the design seems reasonable, but cannot claim it improved evaluation results. Last week's extraction scores do not answer that question.

Prompt engineering currently feels partly like art: wording and context choices depend on intuition until we test them. To make it engineering, we need versioned prompts and retrieval settings, fixed questions with expected evidence, controlled comparisons, and saved outputs. We should measure evidence retrieval, answer correctness, unsupported answers, and latency, then inspect failures. Even a negative result would tell us more than a convincing demonstration.

# Week 7 (October 5-11, 2026)

**Progress so far, based on Will's October 4 implementation and [checklist update](archive/checklist.md).**

**Did:** Will implemented voice enrollment and speaker identification across the iOS client and backend. Enrollment records three clips and stores a voiceprint only after consent and quality checks. Users can skip enrollment, re-record from Profile, or revoke consent to delete their voiceprint. With the worker running with `--diarize`, the pipeline uses cosine similarity to match diarized speakers to enrolled project members; unmatched speakers keep generic `SPEAKER_N` labels.
**Blocked on:** Speaker-match thresholds are provisional and have not been calibrated. We still need a documented native end-to-end run and a speaker-identification benchmark before claiming reliable recognition.
**Next:** Verify enrollment, upload, named transcript output, and consent revocation together on a consented recording. Measure correct matches, incorrect matches, and unknown-speaker handling, then calibrate thresholds. Continue the controlled RAG comparison planned last week.

Will also updated the implementation checklist to distinguish connected code paths from accepted user journeys. The current task-similarity flag can show an earlier open task's title on a new candidate, but the candidate is still created. This is progress toward cross-meeting reconciliation; it does not yet establish duplicate prevention or reliable task-state updates across meetings.

The main engineering question is whether a similarity score is strong enough evidence to attach a person's name to a transcript. A wrong name can also misattribute an extracted commitment. Keeping unmatched speakers anonymous is a useful fallback, but we need recordings with known speakers and unenrolled participants to measure how often the system names the right person or should abstain. Existing component tests establish mechanics, not recognition quality. Playback, storylines, summary editing, redaction, and replacing JSON status polling with Postgres-backed status remain open in Will's checklist.

## Team meeting follow-up

Attendees: Bryan Yang, Guadalupe Cantera, and Will Liu. Recorded here from the supplied automated meeting summary; the summary does not specify the meeting date or assign every action item to an owner.

- Agreed to prioritize polishing and evaluating existing base features before adding new ones. Cross-meeting reconciliation and complete end-to-end reliability remain gaps to test rather than completed claims.
- Discussed shared-backend availability problems associated with Will's computer/connectivity. Bryan will set up the backend on his own machine, investigate a practical backup/recovery approach, and report findings to the team. GPU hosting and backend synchronization were discussed as possibilities, not selected architecture decisions; seek Derrick/CCB feedback before committing to a larger solution.
- Proposed TS3005a-d as the connected development/demo sequence, IS1008 for validation, and IS1009 for held-out evaluation. Finalize coverage and labels before comparisons. IS1009a was already used in the Milestone 2 ASR pilot, so it is not wholly untouched; disclose that prior use or select a fresh series for a clean held-out claim.
- Will demonstrated consent-based voice matching using cosine similarity. The team will document both successful and failed approaches for voice recognition/diarization, and evaluate RAG, transcription, and diarization rather than treating implementation as proof of quality.
- Guadalupe will test user accounts. Team testing should also cover sign-up, voice enrollment, project invitations, and transcription while the backend is available. Overnight availability was discussed, but no successful availability test is recorded yet.
- Bryan will prepare the shared Milestone 3 Google Doc from the repository draft and coordinate evaluation work. The supplied action list also calls for a Project 2 Part 2 TA check-in and reporting back; that coursework is separate from the capstone milestone. Confirm the actual check-in date/time because the summary only says "the next day."

Bryan's immediate sequence is to bring up a reachable local backend, verify sign-up and a small upload through the app, then ingest the connected AMI sequence into a dedicated development project. Review expected tasks and source-grounded questions before scoring, preserve other projects, record failures in the demo walkthrough, and run baseline/updated comparisons on identical inputs. A working second backend is the first availability experiment; automatic failover or synchronization should follow only if this exposes a concrete need.

## October 10 checkpoint: shared backend and native dataset setup

**Did:** Bryan brought up a second backend on his Mac using the shared Supabase project. Added opt-in shared processing: private audio Storage, PostgreSQL job/status records, renewable worker leases, fenced publication, per-project processing order, and deferred object cleanup. Existing local mode remains available. The backend now runs in a detached `labsync` tmux session; its shared-mode health check passed after a graceful restart. This provides shared storage and recoverable work, not automatic API failover. Will has not yet been verified running the same shared configuration. See [deployment and restart instructions](reference/shared_backend.md).

Configured Google sign-in and reached the signed-in native app. Created real account-owned AMI projects through iOS and verified they remained after relaunch. Uploaded all seven local recordings through the native file picker and consent flow: TS3005a-d into the connected dev project, IS1008a into isolation/validation, IS1009a into evaluation, and ES2004a into a separate evaluation project because it is a different trial. All seven uploads were confirmed in PostgreSQL; TS3005a and b completed processing at the checkpoint, while the rest were processing or queued. App dates currently reflect import dates, not verified corpus dates. IS1009a and ES2004a have prior Milestone 2 ASR exposure.

The larger TS3005b WAV failed at Storage. Retrying with a smaller lossless FLAC succeeded; decoded PCM samples for all seven FLAC copies were verified against the originals. Original recordings remain local and gitignored. Enabled Files access for native imports. Replaced the open-ended third enrollment prompt with a fixed passage to reduce repeated attempts; enrollment acceptance and voice quality still need testing. Reproduced Profile's white appearance in dark mode, replaced fixed colors with adaptive iOS colors, and visually checked both appearances. Simulator builds and formatting checks passed.

**Still unverified:** The full journey from recording through transcript inspection, task review and state changes, supported/unsupported cited chat, project isolation, relaunch persistence, and purge. Upload acceptance and completed job states do not establish output quality. Also outstanding: live two-device worker recovery, membership sharing with teammates, endpoint failover routing, and an always-on host for external testers. The current backend command does not enable diarization, so this run is not speaker-identification evidence.

**Next:** Invite teammates to the real projects, align Will's code/migration/configuration with the shared backend guide, finish and inspect the AMI processing outputs, then record the native walkthrough and freeze reviewed task-state labels and questions before comparison runs. This checkpoint records setup and partial native evidence, not Milestone 3 completion.

Checkpoint validation: 29 targeted server/shared-backend/storage tests passed against disposable PostgreSQL with offline storage/inference stand-ins; targeted Ruff checks passed. Simulator builds passed. These checks do not establish live two-device failover or model-output quality.

## October 11 native continuity checkpoint

Bryan tested a separate scripted project with four consecutive text-only meetings: a new commitment, repeated mention, deadline change, and explicit completion. In the simulator, the initial task was assigned to Bryan for this fixture, approved without a deadline, and shown in To-do. Later candidates were linked to the original task through evidence-backed human review. The October 16 deadline appeared in Calendar, completion persisted after relaunch, and PostgreSQL retained one accepted task ID, three dismissed later candidates, and three reconciliation audits with source quotes and reviewer.

The native run exposed a one-day meeting-date shift, completed meetings labeled Processing, outdated deadline guidance, an inaccurate empty review state, and a stale Undo token after reviewed completion. These were fixed and checked in the simulator. Undo after meeting review passed; a valid lifecycle Undo also survived relaunch and was verified in the database. Review and accepted-task detail edits now record actor and old/new values, and Undo cannot discard a later detail edit.

Validation: 283 backend tests passed against disposable PostgreSQL, Ruff lint/format passed, and the simulator build passed. The existing account/cache survived installation. See the [native walkthrough](evidence/demo_walkthrough.md), [scripted fixture](../tests/fixtures/continuity/README.md), and [Milestone 3 roadmap](milestone_3/roadmap.md).

**Limits and next:** Candidates, including completion, were seeded deliberately; this establishes UI and persistence behavior, not extraction accuracy or audio-to-task acceptance. AMI projects were unchanged. Completion-only update extraction, independently reviewed sequence labels, paired evaluations, reminder lifecycle, external alpha feedback, physical audio playback, and two-host recovery remain outstanding.

# Week 8 (October 12-18, 2026)

## What got done

- **October 17:** Reproduced and fixed deletion of the text-only scripted test project. The shared backend now distinguishes meetings without recordings from real local recordings that still require cleanup on their original backend.
- Implemented immediate task follow-up email: project-owner controls, recipient opt-out, a durable outbox, captured-email previews/history, and retry/duplicate protection. Added optional evidence-gated automatic approval after a current human-confirmed speaker/account connection. The rule abstains on uncertainty, unresolved deadlines, and possible duplicates; it is experimental, not calibrated confidence. See [implementation and limitations](milestone_3/follow_through.md).
- Applied the additive database migration with project automation off by default and installed the updated simulator app. The final backend suite passed **311 tests** on disposable PostgreSQL; Ruff lint/format and the simulator build passed. These checks use inference/provider stand-ins and do not establish real inbox delivery or natural-meeting accuracy.
- Diagnosed Google OAuth's missing PKCE verifier as a simulator signing problem. The unsigned build could not access Keychain (`-34018`). Rebuilt/reinstalled with signing enabled and verified a disposable Keychain write/read/delete inside the running app. A fresh user Google sign-in remains needed to document complete OAuth acceptance.
- Added the [current architecture/troubleshooting guide](architecture.md) and [repository map/simplification plan](README.md). Distinguished old design proposals from implementation, corrected onboarding guidance and broken links, and documented code paths, cache/backend ownership, worker recovery, and external data boundaries. The source reorganization itself has not been performed.
- **Bryan, October 18:** Continued the AMI development-set walkthrough. Supplied screenshots show extracted/accepted tasks in To-do, including a TS3005d evidence quote, and enabled follow-through controls with an empty Test inbox. Bryan reports the dev path is working for these checks. This is partial UI evidence, not a reviewed/scored TS3005a-d sequence or completed email acceptance.
- Confirmed the test-data limitation: AMI speakers are corpus participants, not app members with recipient inboxes. Existing approved tasks retain their assignments, and enabling email does not bulk-send old work. A separate personal recording is needed to test a truthful speaker-to-account-to-email path without relabeling AMI participants as Bryan.
- Prepared [read-aloud follow-through scripts](milestone_3/follow_through.md#personal-recording-test-scripts) with replaceable meeting/deadline dates, expected results, negative cases, and an evidence log. The personal-recording tests have not been executed yet.

## Engineering reflection

The development data is useful for reviewing extraction and continuity, but cannot by itself prove email routing to real participants. Keep natural-data quality evaluation separate from personal scripted acceptance. Diarization separates voices; account mapping establishes a recipient. Date-bearing tasks currently require manual calendar entry/review, and completion-only extraction and recurring reminders remain gaps. Capture mode lets us inspect messages without contacting anyone; it does not demonstrate real inbox delivery.

## Week 8 prompt response: runtime, cost, and tradeoffs

Our runtime includes local audio normalization, Whisper transcription and
speaker diarization, followed by text-model extraction and embedding/indexing.
We have not measured every stage of the current pipeline, so we cannot yet name
its slowest step. One concrete existing measurement is **48.241 seconds for the
text-extraction call on TS3005a**, with **28,106 input tokens and 1,355 output
tokens**. This comes from the earlier saved local artifact
`artifacts/ami/TS3005a-codex.json`, using `meeting-extraction-v1` and requested
model `gpt-5.6-sol`. It is an earlier baseline inspected during Week 8, not a new
Week 8 timing, an end-to-end upload latency, or a current-v2 benchmark.

Token/API usage comes from extraction and chat generation plus OpenAI embedding
requests. Audio inference runs on our Mac, consuming local compute rather than
hosted transcription requests. Storage and live email are additional deployment
costs. We have not verified the applicable billing or measured a per-meeting dollar
cost, so token counts should not be presented as an actual charge. The next
personal-recording run should log upload-to-result time, individual processing
stages, model/embedding usage, and approval-to-capture latency separately.

This week we traded broader hands-off automation and live-email scope for
controlled, inspectable behavior. Automatic approval requires a confirmed
speaker/account connection and a narrow evidence rule; uncertain commitments,
possible duplicates, and date-bearing tasks stay in review. Capture mode lets us
inspect follow-up messages without contacting recipients. This leaves some manual
work and delays proof of real inbox delivery, but AMI speakers are not actual app
account holders, and we do not yet have reviewed evidence that broader automatic
assignment is reliable. We chose to validate that boundary before expanding it.

We are not fine-tuning, and we have no evidence that prompting has reached its
ceiling. The immediate gaps include identity mapping, date handling, follow-through
integration, and independently reviewed sequence labels. We need categorized
errors and controlled prompt/retrieval comparisons before deciding whether any
remaining failure is a model limitation that fine-tuning would address.

## Zoom direction discussed

Following the professor's discussion of Zoom for CCB meetings, Bryan documented a proposed Zoom connection in the local, gitignored `contexts/zoom_integration_direction.md`. The idea is to import authorized meeting summaries/transcripts into the same project/task backend, retain the standalone mobile app, and eventually maintain commitments and follow-through across meetings. A full interface inside Zoom is a separate later decision. The [tracked Milestone 3 checkpoint](milestone_3/roadmap.md#zoom-proposal) records the proposal for teammates who do not have the local context folder.

No Zoom integration has been implemented or tested. CCB/host permission, available account features/API access, provenance, and summary-versus-transcript evidence need confirmation. First validate one authorized artifact after the core task loop works; keep any Zoom-input evaluation separate from the current audio pipeline.

## Next priorities and dependencies

1. Record Bryan's consented test audio and run manual approval-to-captured-email, then automatic approval after speaker/account confirmation. Record actual outcomes using the new script; verify relaunch, dates, and recipient opt-out. Configure a verified sender before claiming real inbox delivery.
2. Complete the human-reviewed TS3005a-d ledger and obtain a second review. Keep original AMI identities, baseline inputs/results, and prior evaluation exposure documented. The full sequence-quality evaluation remains open.
3. Finish completion-only update proposals and the bounded reminder lifecycle: schedule, reschedule, completion/cancellation, and retry deduplication. Use a controlled clock and test sink before live delivery.
4. Coordinate separate-account invitations/isolation, two-worker recovery with Will, external alpha access/feedback, and physical-device audio acceptance. Proposed owners and timing need team agreement.
5. Discuss Zoom with the team as a scoped next ingestion experiment, rather than substituting it for unfinished Milestone 3 acceptance and evaluation.

Evidence for the October 17 implementation is committed in `88f517a`, `ff58d1c`, and `0d01cf4`. October 18 screenshots are user-supplied observations; original screenshot/video artifacts and a completed personal-recording result log still need to be attached to the walkthrough. The [roadmap](milestone_3/roadmap.md) and [submission draft](milestone_3/submission_draft.md) retain the unfinished milestone gates.

# Week 9 (October 19-25, 2026)

## What got done so far

- **October 19:** Committed and pushed the preliminary implementation to `main`
  in [`afeaded`](https://github.com/BryanDYang/guardian-agent/commit/afeaded).
  This is an implementation checkpoint, not completed Milestone 3 acceptance.
- Added in-app meeting audio recording: consent and microphone permission,
  timer/input level, stop, playback, and upload through the existing processing
  pipeline. Original M4A recordings remain in the app's `Documents/Recordings`
  folder. Recording stops and saves when the app leaves the foreground, with a
  60-minute limit. The signed simulator build was installed; personal microphone
  recording and the complete native processing journey still need testing.
- Implemented the first Zoom experiment discussed with the professor: manual
  summary import into the existing project/task flow, with a synthetic solo-test
  example. Summary text retains its provenance, proposed owners require review,
  and unchanged meeting-instance retries do not duplicate work. Summary evidence
  is distinguished from recorded speech in the app, retrieval citations, and
  follow-up emails. This does not connect a Zoom account or automatically import
  post-call summaries; OAuth, API access, webhooks, and account eligibility remain
  unresolved. It advances the Week 8 proposal without replacing audio evaluation.
- Simplified the app logo to a flat speech bubble with a checkmark, with matching
  light/dark icons and sign-in branding.
- Clarified the [personal recording scripts and storage instructions](milestone_3/follow_through.md#personal-recording-test-scripts):
  eight separate clips, independent projects except the C/F continuity sequence,
  settings and expected outcomes per case, and local audio/evidence/result-log
  locations. Prepared a local run log under
  `artifacts/follow-through/2026-10-19-run-1/results.md`; all outcomes remain
  **not run**. Recordings and detailed local logs are ignored by Git.

## Verification and limits

All **314 backend tests** passed against isolated local PostgreSQL, including
Zoom import-to-captured-email acceptance and mandatory route-isolation coverage.
Ruff lint/format and the signed iOS simulator build passed. Two existing
dependency deprecation warnings remain. These automated checks use offline
inference/embedding substitutes and do not establish real inbox delivery, native
visual acceptance, or natural-meeting quality.

A real synthetic-summary model call proposed both expected assignments with
validated document quotes in **4.331 seconds**. This measures one text-extraction
call, not the full pipeline or a quality benchmark. Later rechecks hit provider
**HTTP 429 (Too Many Requests)** despite a signed-in CLI; live processing needs
rechecking after the rate limit clears. No real follow-up email was sent.

## Planned work this week

**October 20 processing update:** Diagnosed the failed personal D/E recordings
as Codex extraction failures after successful transcription/diarization. An
otherwise identical synthetic request failed with the older Homebrew CLI and
succeeded with the official desktop-bundled CLI, despite available subscription
allowance. Added configurable `LABSYNC_CODEX_CLI`, pinned the working executable
in local private configuration, and restarted the backend. The existing D and E
recordings then processed successfully in the native app, with
their tasks left pending for human review. All 316 backend tests and lint/format
checks passed. See the
[recovery evidence](evidence/demo_walkthrough.md#october-20-codex-cli-failure-and-recording-recovery).
The observed earlier HTTP 429 is not evidence that the account exhausted credits.

**October 20 automation-default update:** New projects now start with task-owner
email and bounded automatic approval enabled. Applied the default-only migration
and verified that every existing project's saved choices remained unchanged.
Recipient opt-out and evidence/identity checks still apply; delivery remains in
the configured mode. All 317 backend tests passed, including opt-out/explicit-off
coverage. Existing personal test projects still need their scenario settings
checked before approval; their outcomes are not inferred from the new defaults.

**October 20 native acceptance:** Simplified follow-through settings so Done saves
changed project/recipient values and closes after success. Draft switches survive
history refresh and failed saves. Native tests verified preference persistence,
joint project/preference saving, and restoration of recipient opt-in.

Ran the personal recordings: B-positive auto-approved with one captured email;
B-negative abstained; C/D manual approval and Calendar dates passed; E opt-out
produced zero messages. F1 repeated-mention reconciliation avoided a duplicate,
but ASR heard October 3 instead of the confirmed October 23, requiring a manual
date edit. F2 produced no completion candidate; manual completion/Undo and
relaunch persistence passed. Four captured messages total, zero actual inbox
sends. A had already auto-approved and cannot count as a clean manual A test.
The [dated evidence table](evidence/demo_walkthrough.md#october-20-personal-audio-acceptance-2026-10-20-run-1)
records interventions and limits; local before/after snapshots stay in ignored
artifacts. All 317 backend tests, Ruff checks, and the signed simulator build
passed for these changes.

Next: record a clean manual A demo, configure/verify a consenting live inbox,
resolve automatic dates and completion extraction, and finish the AMI a-d human
review, reminder lifecycle, external testers, and paired evaluations. Zoom
remains manual summary import; automatic account integration has not been
validated.

## Team coordination

Bryan may miss the Tuesday, October 20 check-in with Derrick because of an urgent
work meeting. Ask teammates to share Derrick's feedback and action items so the
recording tests and Milestone 3 priorities can be adjusted accordingly.

### Short Slack draft

Draft only; not sent. Share after this journal update is pushed or otherwise
available to the team.

> Hi team! I may miss tomorrow's check-in with Derrick because of an urgent work meeting. I've pushed the preliminary in-app recording, manual Zoom summary import, and updated logo. The Week 9 journal is updated, and I plan to record the follow-through tests this week and document the results for Milestone 3. Please share Derrick's feedback and any action items afterward. Thanks!

### October 21 independent-review request draft

Draft only; not sent.

> Hi Will and Guadalupe! The M3 follow-through results are documented. Could one of you independently review the eight short cases in `docs/milestone_3/human_review.md`? Copy the blank worksheet and review the source/output pairs before reading my judgments or the walkthrough conclusions. Please flag unsupported or missing information and return your notes before we compare. I’ll record the clean app demo next. Let me know who can take this. Thanks!
