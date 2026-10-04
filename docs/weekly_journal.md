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

**Did:** We integrated project chat with hybrid retrieval and verified citations, and connected more of the iOS app to authenticated backend data. I worked on setup documentation and the Milestone 3 draft, separating implemented features from verified behavior.<br>
**Blocked on:** A reviewed RAG question set and live retrieval/model evaluation; component tests do not establish answer quality.<br>
**Next:** Run a controlled comparison of hybrid retrieval against vector-only retrieval on the same labeled questions.

One specific system change was grouping consecutive transcript turns into windows of up to 150 words instead of retrieving each turn separately. Short turns often lack context, while long turns can exceed the embedding model's input limit. The windows aim to preserve enough surrounding discussion to answer questions about decisions and ownership.

We have not measured this change's effect on answer quality. The implementation includes chunking and citation-validation tests, but those check mechanics, not whether real retrieval finds better evidence. Integration and setup received attention before we had a labeled question set ready. That leaves an uncomfortable gap: we can explain why the design seems reasonable, but cannot claim it improved evaluation results. Last week's extraction scores do not answer that question.

Prompt engineering currently feels partly like art: wording and context choices depend on intuition until we test them. To make it engineering, we need versioned prompts and retrieval settings, fixed questions with expected evidence, controlled comparisons, and saved outputs. We should measure evidence retrieval, answer correctness, unsupported answers, and latency, then inspect failures. Even a negative result would tell us more than a convincing demonstration.
