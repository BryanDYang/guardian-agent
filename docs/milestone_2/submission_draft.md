# Milestone 2: Data, Evaluation, and Baselines

**Course:** CIS-5980 AI Capstone
**Track:** AI Engineering
**Project name:** [TODO]
**Team:** Will Liu, Guadalupe Cantera, Bryan Yang
**Repository:** https://github.com/BryanDYang/guardian-agent
**Canvas deadline:** September 28, 2026 (recorded by the team; confirm submission time/timezone in Canvas)
**Last updated:** September 16, 2026
**Status:** Collaborative draft; Milestone 1 TA/professor feedback pending.

## How to use this draft

Copy this document into Google Docs for team editing, then bring the revised text back into this file. Replace each `[TODO]` with an answer or an explicit limitation. Keep proposed plans separate from completed work and measured results. Owners below are proposed until the team confirms them.

The assignment's questions are guidance, not a requirement to answer every prompt individually. This draft organizes the required AI Engineering deliverables and adds project-specific questions to make the answers concrete. Remove drafting instructions before exporting the final report.

**Submission:** One PDF containing the report, with a repository URL. The repository must contain the milestone artifacts and README instructions for running the evaluation. A mandatory TA check-in is also required. The assignment does not separately request a new pitch deck, demo video, Google Doc submission, or a finished application.

**Grading:** Dataset readiness and Data Card: 40 points. Runnable evaluation, qualitative rubric, baselines, results, and error analysis: 60 points. Team contributions and next-milestone ownership must be included, although the team section is non-graded.

## 1. Project summary and changes since Milestone 1

**Draft summary:** We are building a research meeting follow-through assistant that extracts evidence-backed commitments, decisions, and suggestions and maintains task state across recurring meetings. Our central question is whether persistent meeting history improves task tracking over processing meetings independently, without introducing unsupported updates.

**What does this milestone actually implement and evaluate?**

The proposed Milestone 2 implementation imports timestamped transcripts, extracts owned commitments with source references, and compares saved predictions with human-reviewed labels. We plan to compare independent-meeting extraction with an applicable open-source reference on the same development inputs. The initial application feature and evaluation will share the extraction contract.

Currently, the repository contains an installable Python CLI scaffold and offline smoke tests. Extraction, fixtures, scoring, and baseline results are not implemented. The full mobile UI, audio pipeline, calendar integration, reminders, and complete cross-meeting reconciliation remain later application work; this checkpoint does not establish their quality.

**What changed after Milestone 1, and why?**

Milestone 1 TA/professor feedback is pending. No feedback-driven scope change is confirmed. The immediate proposal is to implement and evaluate a transcript-first slice while retaining the broader follow-through objective.

**Architecture decision to reconcile:** The submitted proposal specifies an iOS client and PostgreSQL/pgvector; the Markdown proposal and pitch deck describe a CLI/local service with SQLite. The submitted proposal also mentions SQLite in its budget. Confirm the intended final architecture and distinguish it from the evaluation-only tooling needed now.

**Agreed direction:** [TODO]
**Decision date and participants:** [TODO]

### Pending Milestone 1 feedback

We are awaiting TA and professor input on the Milestone 1 submission. The following decisions remain provisional until the team reviews that feedback.

| Feedback or question                                                               | Response received | Resulting decision or action | Owner  |
| ---------------------------------------------------------------------------------- | ----------------- | ---------------------------- | ------ |
| Is the proposed dataset size and coverage sufficient for our intended claims?      | Pending           | [TODO]                       | [TODO] |
| Is independent-meeting extraction an appropriate primary baseline?                 | Pending           | [TODO]                       | [TODO] |
| Can timestamped imports/sponsor transcription remain upstream for this checkpoint? | Pending           | [TODO]                       | [TODO] |
| What application scope and reminder behavior should we prioritize?                 | Pending           | [TODO]                       | [TODO] |
| Additional submission feedback                                                     | Pending           | [TODO]                       | [TODO] |

## 2. Dataset and Data Card

**Proposed lead:** Guadalupe; second label reviewer: [TODO]

### Data sourcing and access

**What inputs have we actually assembled, and how can a reviewer access them?**

No labeled evaluation dataset has been established in the application repository yet. The proposed starting point is one synthetic three-meeting development sequence, followed by additional independent cases and sequences to cover ordinary and difficult examples. AMI and QMSum were identified in Milestone 1 as candidate supplementary sources; neither is claimed here as acquired, licensed for our use, or annotated for our task. Sponsor recordings and pipeline reuse remain subject to access and permission confirmation.

| Source/subset | Actual size: projects, sequences, meetings | Format and annotation coverage | Access method or repository path |
| ------------- | ------------------------------------------ | ------------------------------ | -------------------------------- |
| [TODO]        | [TODO]                                     | [TODO]                         | [TODO]                           |

### Provenance, licensing, and permissions

**Where did each source come from, and what usage constraints apply?**

| Source | Creator/version or collection method | License/permission and supporting reference | Access, processing, and redistribution restrictions |
| ------ | ------------------------------------ | ------------------------------------------- | --------------------------------------------------- |
| [TODO] | [TODO]                               | [TODO]                                      | [TODO]                                              |

**For self-created data:** [TODO: Describe authorship, whether AI assisted creation, human review, and whether any real/private meeting content was used.]

**For participant data:** [TODO: Describe consent, permitted external model processing, exclusion/deletion, retention, and who can access it. Mark not applicable if using only synthetic data.]

### Annotation design and quality

**What is labeled?** Proposed labels include commitment descriptions, owners, supported deadlines, source segment IDs, and suggestions kept separate from accepted commitments. Sequence annotations will also record links to earlier tasks and expected state after each meeting. Decisions and historical Q&A are outside the first extraction scorer unless explicitly added.

**Labeling rules (proposed):** A suggestion becomes a commitment only with evidence of acceptance. Unknown owners and missing deadlines remain unknown rather than inferred. Explicit supported completion can change a task to done; partial progress, negation, and silence cannot. Ambiguous references require review rather than an invented task link. Every accepted record or update must identify its supporting transcript segment.

**Review and disagreement resolution:** [TODO: Who labeled, who reviewed, how disagreements were resolved, and any unresolved cases.]

**Annotation guide and schema location:** [TODO]

### Training/development, validation, and test splits

**How are the splits constructed, and why?**

We do not plan to train or fine-tune model parameters for this checkpoint. Development inputs will support prompt/rule iteration and initial baseline evaluation. Related meetings will stay together within a sequence/project split to avoid leakage. Separate validation and held-out test sequences are planned, with exact counts and IDs pending data assembly. Milestone 2 results will be labeled as development results; the first sequence will not later be presented as held-out evidence.

| Split                | Sequence/project IDs and counts | Purpose | Has it influenced prompts or rules? |
| -------------------- | ------------------------------- | ------- | ----------------------------------- |
| Training/development | [TODO]                          | [TODO]  | [TODO]                              |
| Validation           | [TODO]                          | [TODO]  | [TODO]                              |
| Test                 | [TODO]                          | [TODO]  | [TODO]                              |

**Split manifest/version and any seed:** [TODO]
**Current split status:** Inputs, labels, and split manifests are not yet assembled. We cannot report sample counts, held-out performance, or generalization claims.

### Known limitations

The initial synthetic sequence will test selected behaviors but cannot establish performance on natural research meetings. Small samples and author-designed scenarios may miss conversational variation and difficult negative examples. Label disagreements will require review. Transcript-only evaluation will not measure transcription or diarization quality. Public meeting corpora may differ from advisor/student conversations and may lack our required task-state labels. Language, speaker, and domain coverage must be documented once inputs are assembled; no broad demographic or deployment claims are supported at this stage.

## 3. Evaluation harness

**Proposed lead:** Bryan, with Will on prediction contracts and Guadalupe on labels.

### Test design

**What does the custom suite measure?**

The planned harness loads labeled timestamped transcripts, runs interchangeable extraction baselines, saves their predictions and run settings, scores predictions against labels, and writes aggregate plus per-example results. Scoring saved predictions will run offline. Live inference will be a separate step. Only the repository scaffold currently runs; all evaluation stages remain to be implemented. The sequence scenarios below describe desired coverage, not completed functionality.

| Scenario                     | Expected behavior                                      | Fixture ID | Implemented/scored? |
| ---------------------------- | ------------------------------------------------------ | ---------- | ------------------- |
| Explicit completion          | Update the correct existing task to done with evidence | [TODO]     | Not implemented     |
| Deadline change              | Update the supported date on the correct task          | [TODO]     | Not implemented     |
| Unaccepted suggestion        | Keep separate from an owned commitment                 | [TODO]     | Not implemented     |
| Ambiguous reference          | Flag uncertainty rather than invent a match            | [TODO]     | Not implemented     |
| Task not mentioned again     | Preserve the previous state                            | [TODO]     | Not implemented     |
| Partial progress or negation | Avoid unsupported completion                           | [TODO]     | Not implemented     |

### Metrics and scoring rules

**Why do the chosen metrics reflect success?** Users need commitments to be found without invented tasks, assigned to the right people, and linked to supporting evidence. Precision/recall measures extraction coverage and correctness; owner accuracy measures attribution; duplicate counts expose repeated tasks; citation checks measure traceability. Unsupported completion and state/link metrics will apply when update predictions are implemented. A model that produces no updates cannot be credited with successful reconciliation solely because it has no false completions.

The rows below are proposed metrics. Confirm which are implemented, define their denominators and matching rules, and explicitly mark deferred metrics.

| Metric                                            | Exact scoring definition and denominator                                   | Why it matters                             | Implemented? |
| ------------------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------ | ------------ |
| Task precision/recall (and F1 if used)            | [TODO: Define a correct match, including owner and semantic equivalence]   | Measures correct and missed commitments    | [TODO]       |
| Owner accuracy                                    | [TODO: Define the scored population and unknown owners]                    | Detects attribution errors                 | [TODO]       |
| Duplicate task count/rate                         | [TODO: Define a duplicate and rate denominator if used]                    | Detects repeated creation of existing work | [TODO]       |
| Unsupported completion count/rate                 | [TODO: Define evidence support and denominator]                            | Detects false done transitions             | [TODO]       |
| Citation validity/support                         | [TODO: Separate existing source IDs from evidence that supports the claim] | Measures traceability and grounding        | [TODO]       |
| Cross-meeting state/link accuracy, if implemented | [TODO]                                                                     | Measures maintained task state             | [TODO]       |

**Matching and adjudication:** [TODO: Explain paraphrase matching, one-to-one assignment, partial matches, and human adjudication.]

**Empty denominators and missing/invalid predictions:** [TODO: Explain scoring behavior; do not silently count missing outputs as correct.]

### Reproducibility and README instructions

**Environment and dependencies:** The scaffold uses Python 3.12, uv with locked dependencies, Pytest, and Ruff. Model/runtime dependencies will be recorded after baseline selection. See the repository README for existing setup instructions.
**Dataset/prediction versions and code revision:** [TODO]
**Model versions, prompt versions, settings, and seeds where supported:** [TODO]
**Credentials or hardware needed for live runs:** [TODO]

Replace these placeholders with tested commands and also place the instructions in the repository README:

```text
uv sync --locked --extra dev
[TODO: command to generate baseline predictions]
[TODO: command to score saved predictions without API calls]
[TODO: command to run offline scorer tests]
```

**Example output from an actual run:**

```text
[TODO: paste output, report path, dataset size, and measured scores]
```

**Scorer validation:** [TODO: Show that correct predictions receive expected scores and wrong owners, duplicates, unsupported completions, and invalid citations are detected. Keep live model generation separate from deterministic CI checks.]

## 4. Qualitative evaluation rubric

**Proposed lead:** Guadalupe; reviewers: [TODO]

**Proposed protocol:** Two team members independently review a shared sample of extracted commitments and, once available, proposed updates. Include ordinary cases and each error category, record individual scores, and reconcile disagreements with evidence. Reviewer names, sample size, and actual scores remain pending.

The following rubric is a proposed starting point for team review, not a completed grading exercise. Score 2 falls between anchors 1 and 3; score 4 is usable with minor corrections between anchors 3 and 5. Record critical errors separately so an average cannot hide an unsupported completion.

| Dimension                                | 1: poor | 3: needs substantial correction | 5: high quality |
| ---------------------------------------- | ------- | ------------------------------- | --------------- |
| Faithfulness/evidence support | Invents commitments or unsupported changes | Mixes supported content with unsupported details requiring correction | Every substantive field or change is supported by the cited evidence |
| Owner and speaker attribution | Assigns work to the wrong person without evidence | Some attributions require correction or uncertainty is unclear | All owners are supported; genuinely unknown owners remain unresolved |
| Coverage of relevant commitments/updates | Misses most relevant commitments or updates | Captures the main items but misses material details or items | Captures all relevant labeled items without duplicates |
| Ambiguity and suggestion handling | Treats suggestions or ambiguous speech as definite commitments/updates | Handles clear cases but mishandles some uncertainty | Separates suggestions and routes genuinely ambiguous cases for review |
| Clarity and usefulness | Output is unusable or misleading | Understandable but needs substantive editing | Tasks are concise, actionable, and easy to verify against evidence |

**Illustrative example, not an evaluated result:** At segment `s1`, Will says, "I will rerun the baseline by Friday." At `s2`, the advisor says, "You could try mixed precision." A good output records Will's rerun commitment with `s1` as evidence and keeps mixed precision as an unaccepted suggestion. Assigning mixed precision to Will as a confirmed task is an unsupported commitment. Converting Friday to a calendar date requires meeting-date/timezone context. Actual baseline examples will be added after runs.

**Review disagreements and any LLM-judge role:** [TODO: State whether grading is human, automated, or assisted. An LLM judge is not explicitly required by the assignment.]

## 5. Baselines and initial results

**Proposed lead:** Will; scoring: Bryan; review: Guadalupe.

### Simple baseline

**Method and rationale (proposed, not implemented):** Extract commitments from each meeting independently using a fixed prompt and the agreed output schema. This tests what can be recovered without persistent cross-meeting memory and provides the primary comparison described in Milestone 1.
**Model/rules, version, prompts, settings, and code path:** [TODO]
**Information available to this baseline (proposed):** The current timestamped transcript and confirmed speaker mapping only, with no prior meeting transcripts, stored task state, or gold labels.

### Off-the-shelf open-source reference baseline

**Model/system, source, version, and license:** [TODO]
**How it is run and adapted to the same evaluation contract:** [TODO]
**Why it is a relevant reference:** [TODO]

The assignment requires an open-source reference baseline when applicable. If claiming it is not applicable, explain why and raise that interpretation with the TA. A proprietary model alone does not supply this reference.

### Measured results

Use the same evaluation inputs for comparable rows. Include actual sample counts and numerators/denominators where appropriate. Use `not measured` rather than zero for missing results. Add or remove columns to match the implemented metrics.

| Method/version                | Split and sample count | Task P/R/F1  | Owner accuracy | Duplicates   | Unsupported completions | Citation validity/support |
| ----------------------------- | ---------------------- | ------------ | -------------- | ------------ | ----------------------- | ------------------------- |
| Simple baseline: [TODO]       | [TODO]                 | Not measured | Not measured   | Not measured | Not measured            | Not measured              |
| Open-source reference: [TODO] | [TODO]                 | Not measured | Not measured   | Not measured | Not measured            | Not measured              |

**Qualitative scores and sample count:** [TODO]
**Run date, report/prediction paths, and any measured latency/cost:** [TODO]
**Interpretation and limitations:** [TODO: Distinguish initial development results from held-out evidence; targets are not results.]

## 6. Initial error analysis

Analyze observed baseline failures rather than only anticipated risks. Separate observations from hypotheses about causes.

| Example/source ID | Expected output | Actual output and baseline | Error category | Likely cause | Proposed change and verification |
| ----------------- | --------------- | -------------------------- | -------------- | ------------ | -------------------------------- |
| [TODO]            | [TODO]          | [TODO]                     | [TODO]         | [TODO]       | [TODO]                           |

**Most frequent or consequential failures:** [TODO]
**What we will change next and why:** [TODO]
**What these initial results do not establish:** [TODO]

## 7. Mandatory TA check-in

**Status:** [TODO: not scheduled / scheduled / completed]
**Date and attendees:** [TODO]

### Preparation checklist

- [ ] Data Card summary with actual inputs, splits, and limitations.
- [ ] Working evaluation command and README instructions.
- [ ] Baseline results table.
- [ ] Top risks and blockers.

### Questions for discussion

1. What Milestone 1 feedback should change our scope or evaluation priorities?
2. Is our actual dataset size, sequence coverage, and split strategy sufficient for this checkpoint?
3. Are the simple baseline and selected open-source reference appropriate?
4. Is a transcript-first evaluation appropriate while sponsor audio/data access is unresolved?
5. How should we reconcile the differing application architectures in the Milestone 1 artifacts?

**Additional questions:** [TODO]

### Notes and follow-up

| Advice or decision | Required action | Owner  | Target date |
| ------------------ | --------------- | ------ | ----------- |
| [TODO]             | [TODO]          | [TODO] | [TODO]      |

Do not mark the check-in complete until it occurs. These notes are a collaboration aid; the assignment explicitly requires the meeting but does not prescribe a separate meeting-notes submission.

## 8. Weekly progress, blockers, and next steps

**Progress made:** Reviewed the Milestone 2 assignment and Phase 2 teaching materials against the Milestone 1 artifacts and current code. Identified missing evaluation deliverables and architecture inconsistencies. Prepared this collaborative submission draft and a proposed task breakdown. The existing CLI scaffold and smoke tests provide a starting repository, not an implemented evaluation harness.

**Top blockers or risks:** Milestone 1 feedback is pending. Team ownership, final architecture, baseline selection, data size/splits, and sponsor permissions remain unconfirmed. Labeled data and a common output contract are the immediate dependencies. A single synthetic sequence will not support broad performance claims.

**Planned next steps:** Agree on one transcript and its expected output, finalize the shared schema, prepare reviewed development labels, implement baselines and scoring, and run the first comparison. Then expand coverage, inspect failures, complete the TA check-in, and replace pending report sections with evidence. See [Milestone 2 task plan](task_plan.md).

The [weekly journal](../weekly_journal.md) contains the ongoing record. Include the relevant progress in this report so the PDF is self-contained.

## 9. Team contributions and next-milestone work plan

Record actual contributions separately from proposed ownership. This section is required for teams and is non-graded.

| Member            | Actual Milestone 2 contributions | Artifact or evidence |
| ----------------- | -------------------------------- | -------------------- |
| Guadalupe Cantera | [TODO]                           | [TODO]               |
| Will Liu          | [TODO]                           | [TODO]               |
| Bryan Yang        | [TODO]                           | [TODO]               |

| Task for the next milestone | Confirmed owner | Completion check | Dependencies/blockers | Target date |
| --------------------------- | --------------- | ---------------- | --------------------- | ----------- |
| [TODO]                      | [TODO]          | [TODO]           | [TODO]                | [TODO]      |

## 10. Final submission checklist

- [x] AI Engineering track and team declared.
- [ ] Actual dataset/inputs assembled with a complete Data Card.
- [ ] Provenance, licensing/permissions, splits, and limitations documented.
- [ ] Evaluation harness runs using documented README commands and includes example output.
- [ ] Qualitative rubric defined with concrete anchors/examples.
- [ ] Simple baseline implemented and evaluated.
- [ ] Applicable open-source reference baseline implemented and evaluated, or non-applicability explained.
- [ ] Measured results table and initial error analysis included.
- [ ] Mandatory TA check-in completed.
- [ ] Weekly progress, blockers, team contributions, and next-milestone owners included.
- [ ] Repository URL included; milestone artifacts and instructions available to teaching staff.
- [ ] Pending feedback addressed or clearly identified; scope changes documented.
- [ ] Drafting instructions and unresolved placeholders replaced with answers or explicit limitations.
- [ ] Report exported as one PDF and checked for readable tables and working links.
- [ ] Submission completed by the Canvas deadline.
