# Milestone 2: Data, Evaluation, and Baselines

**Course:** CIS-5980 AI Capstone
**Track:** AI Engineering
**Project name:** Meeting Follow-Through Assistant (LabSync)
**Team:** Will Liu, Guadalupe Cantera, Bryan Yang
**Repository:** https://github.com/BryanDYang/guardian-agent
**Canvas deadline:** September 28, 2026 (recorded by the team; confirm submission time/timezone in Canvas)
**Last updated:** September 23, 2026
**Status:** Check-in draft. No Milestone 1 feedback received; TA meeting scheduled for September 23, 2026 (reported by Bryan). Evaluation results and team review remain outstanding.

## How to use this draft

Copy this document into Google Docs for team editing, then bring the revised text back into this file. Replace each `[TODO]` with an answer or an explicit limitation. Keep proposed plans separate from completed work and measured results. Owners below are proposed until the team confirms them.

The assignment's questions are guidance, not a requirement to answer every prompt individually. This draft organizes the required AI Engineering deliverables and adds project-specific questions to make the answers concrete. Remove drafting instructions before exporting the final report.

**Submission:** One PDF containing the report, with a repository URL. The repository must contain the milestone artifacts and README instructions for running the evaluation. A mandatory TA check-in is also required. The assignment does not separately request a new pitch deck, demo video, Google Doc submission, or a finished application.

**Grading:** Dataset readiness and Data Card: 40 points. Runnable evaluation, qualitative rubric, baselines, results, and error analysis: 60 points. Team contributions and next-milestone ownership must be included, although the team section is non-graded.

## 1. Project summary and changes since Milestone 1

**Draft summary:** We are building a research meeting follow-through assistant that extracts evidence-backed commitments, decisions, and suggestions and maintains task state across recurring meetings. Our central question is whether persistent meeting history improves task tracking over processing meetings independently, without introducing unsupported updates.

**What does this milestone actually implement and evaluate?**

The proposed Milestone 2 implementation imports timestamped transcripts, extracts owned commitments with source references, and compares saved predictions with human-reviewed labels. We plan to compare independent-meeting extraction with an applicable open-source reference on the same development inputs. The initial application feature and evaluation will share the extraction contract.

The repository implements timestamped AMI/CCB imports, independent-meeting structured extraction through Codex, local Whisper transcription, and an HTTP backend with a connected web Meetings UI. Uploads, processing state, predictions, and audio persist on the filesystem. A SwiftUI iOS prototype is present, but still uses seeded SwiftData records and placeholder playback; it is not connected to the backend. PostgreSQL has a proposed schema, not an integrated runtime. Human-reviewed evaluation labels, an offline scorer, open-source extraction comparison, and quantitative quality results are still missing. Calendar integration, reminders, and cross-meeting task reconciliation are not implemented.

The September 23 engineering check passed 36 offline Python tests, Ruff lint/format, TypeScript checking, and the web production build. These checks establish software behavior, not extraction accuracy. See [pre-merge verification](verification.md) for live-test evidence and remaining merge gates.

**What changed after Milestone 1, and why?**

Milestone 1 TA/professor feedback is pending. No feedback-driven scope change is confirmed. The immediate proposal is to implement and evaluate a transcript-first slice while retaining the broader follow-through objective.

**Architecture decision to reconcile:** The submitted proposal specifies an iOS client and PostgreSQL/pgvector; the Markdown proposal and pitch deck describe a CLI/local service with SQLite. The submitted proposal also mentions SQLite in its budget. Confirm the intended final architecture and distinguish it from the evaluation-only tooling needed now.

**Current direction:** Bryan prefers the iOS client, backed by the existing Python HTTP service. The web client provides a working integration test surface. Final storage/deployment decisions and team-wide agreement remain pending.
**Decision date and participants:** Direction stated by Bryan on September 23, 2026; confirmation by Will and Guadalupe is pending.

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

No human-reviewed commitment evaluation dataset has been established yet. The following inputs exist; generated predictions are not gold labels.

| Source/subset | Actual size | Format and coverage | Access |
| --- | --- | --- | --- |
| Synthetic extraction example | 1 meeting, 3 turns | Explicit agreement, Sam's commitment with raw deadline, unaccepted suggestion | `tests/fixtures/meeting.json` |
| AMI TS3005 manual transcripts | 1 series, 4 meetings; 287/693/619/1,194 nonempty turns | Timestamped corpus speakers A-D; no reviewed LabSync commitment/state labels | Local `artifacts/ami/TS3005{a,b,c,d}.json`; reproduction in `docs/codex-integration.md` |
| AMI audio excerpt | 1 clip, 45 seconds, TS3005a 90-135s | Mono 16 kHz PCM WAV; opening/agenda content, not a commitment benchmark | `tests/fixtures/ami/TS3005a-90s-135s.wav` |

### Provenance, licensing, and permissions

The AMI fixture manifest records source URL, CC BY 4.0 attribution, SHA-256, and transformations: cropping to 90-135 seconds and conversion to mono 16 kHz PCM. See [fixture provenance](../../tests/fixtures/ami/README.md) and `manifest.json`. The manual annotation import uses AMI v1.6.2, joins word tokens, excludes non-word markers/empty segments, and preserves source IDs and millisecond timestamps. Source links and acquisition commands are in the [integration guide](../codex-integration.md). Full corpus downloads and predictions are ignored local artifacts, not bundled teaching-staff deliverables.

The synthetic example is invented project data with fictitious speakers. Human authorship/review and AI-assistance attribution have not yet been confirmed by the team. It must not be represented as independently reviewed gold data.

No private participant recordings are needed for the current demonstration. Private recordings require permission before collection and external transcript processing. The backend requires explicit processing permission; local audio is transcribed with Whisper, and transcript text is sent through the Codex login. Retention/deletion policy for future participant data remains to be agreed.

CCB source is supplied separately in `contexts/meeting_transcriber-master`; its archive has no verified upstream commit or license file. We do not redistribute it. Its audited hash and the exact functions used are documented in [the audio integration guide](../ccb-transcriber.md). A fresh clone alone cannot reproduce audio processing until this source is supplied.

### Annotation design and quality

**What is labeled?** Proposed labels include commitment descriptions, owners, supported deadlines, source segment IDs, and suggestions kept separate from accepted commitments. Sequence annotations will also record links to earlier tasks and expected state after each meeting. Decisions and historical Q&A are outside the first extraction scorer unless explicitly added.

**Labeling rules (proposed):** A suggestion becomes a commitment only with evidence of acceptance. Unknown owners and missing deadlines remain unknown rather than inferred. Explicit supported completion can change a task to done; partial progress, negation, and silence cannot. Ambiguous references require review rather than an invented task link. Every accepted record or update must identify its supporting transcript segment.

**Review and disagreement resolution:** No independently reviewed gold labels or disagreement log exists yet. Assign a labeler and second reviewer at the team check-in before treating examples as scored evaluation data.

**Annotation guide and schema location:** `src/labsync/extraction.py` contains the provisional Pydantic contract and `meeting-extraction-v2` prompt. Inputs contain project/meeting IDs and turns with IDs, speakers, millisecond timestamps, and content. Outputs contain a summary, decisions, commitments, and suggestions. Commitments preserve nullable owners and verbatim deadline text plus one or more cited quotes. Team-reviewed annotation and matching rules are not yet finalized.

### Training/development, validation, and test splits

**How are the splits constructed, and why?**

We do not plan to train or fine-tune model parameters for this checkpoint. Development inputs will support prompt/rule iteration and initial baseline evaluation. Related meetings will stay together within a sequence/project split to avoid leakage. Separate validation and held-out test sequences are planned, with exact counts and IDs pending data assembly. Milestone 2 results will be labeled as development results; the first sequence will not later be presented as held-out evidence.

| Split                | Sequence/project IDs and counts | Purpose | Has it influenced prompts or rules? |
| -------------------- | ------------------------------- | ------- | ----------------------------------- |
| Development candidates | Synthetic example plus AMI TS3005a-d (5 transcripts; one AMI series) | Schema/integration and future label review | Inputs available locally; labels not assembled |
| Validation | 0 designated | Future tuning validation | Not assembled |
| Test | 0 designated | Held-out evaluation | Not assembled |

**Split manifest/version and any seed:** No finalized split manifest or randomized split exists. The AMI clip overlaps TS3005a and must remain in the same split; it is not an independent test meeting.
**Current split status:** Inputs, labels, and split manifests are not yet assembled. We cannot report sample counts, held-out performance, or generalization claims.

### Known limitations

The planned synthetic sequence will test selected behaviors but cannot establish performance on natural research meetings. Small samples and author-designed scenarios may miss conversational variation and difficult negative examples. Label disagreements will require review. Transcript-only evaluation will not measure transcription or diarization quality. Public meeting corpora may differ from advisor/student conversations and may lack our required task-state labels. Language, speaker, and domain coverage must be documented once inputs are assembled; no broad demographic or deployment claims are supported at this stage.

## 3. Evaluation harness

**Proposed lead:** Bryan, with Will on prediction contracts and Guadalupe on labels.

### Test design

**What does the custom suite measure?**

The planned harness loads labeled timestamped transcripts, runs interchangeable extraction baselines, saves their predictions and run settings, scores predictions against labels, and writes aggregate plus per-example results. Scoring saved predictions will run offline. Live inference will be a separate step. Input import, prediction generation, schema validation, and exact-quote validation run now. Gold-label matching, aggregate scoring, and benchmark report generation remain unimplemented. The sequence scenarios below describe desired coverage, not completed functionality.

| Scenario                     | Expected behavior                                      | Fixture ID | Implemented/scored? |
| ---------------------------- | ------------------------------------------------------ | ---------- | ------------------- |
| Explicit completion          | Update the correct existing task to done with evidence | [TODO]     | Not implemented     |
| Deadline change              | Update the supported date on the correct task          | [TODO]     | Not implemented     |
| Unaccepted suggestion | Keep separate from an owned commitment | `synthetic-001`, turn `t3` | Fixture and live prediction exist; not independently scored |
| Ambiguous reference          | Flag uncertainty rather than invent a match            | [TODO]     | Not implemented     |
| Task not mentioned again     | Preserve the previous state                            | [TODO]     | Not implemented     |
| Partial progress or negation | Avoid unsupported completion                           | [TODO]     | Not implemented     |

### Metrics and scoring rules

**Why do the chosen metrics reflect success?** Users need commitments to be found without invented tasks, assigned to the right people, and linked to supporting evidence. Precision/recall measures extraction coverage and correctness; owner accuracy measures attribution; duplicate counts expose repeated tasks; citation checks measure traceability. Unsupported completion and state/link metrics will apply when update predictions are implemented. A model that produces no updates cannot be credited with successful reconciliation solely because it has no false completions.

The rows below are proposed metrics. Confirm which are implemented, define their denominators and matching rules, and explicitly mark deferred metrics.

| Metric | Proposed scoring definition | Status |
| --- | --- | --- |
| Task precision / recall / F1 | One-to-one semantically matched commitments / predicted commitments for precision; matches / gold commitments for recall; harmonic mean for F1 | Scorer not implemented; matching rules need approval |
| Owner accuracy | Exact owner-label agreement among matched commitments with known gold owners; report null-gold cases separately | Not implemented |
| Duplicate count/rate | Additional predictions expressing the same obligation beyond the first; count / all predicted commitments | Not implemented |
| Citation validity | Existing source ID and exact contiguous quote; valid references / all predicted references | Validation implemented, aggregate metric not implemented |
| Semantic evidence support | Human-supported items / reviewed items; inspect action, owner, and deadline separately | Human review not performed |
| Unsupported completion rate | Unsupported done transitions / predicted done transitions, with numerator/count reported | Deferred: no state-update implementation |
| Cross-meeting state/link accuracy | Requires reviewed task identity links and state snapshots | Deferred: no reconciliation implementation |

**Matching and adjudication (proposal for team approval):** Use one-to-one matching of predicted and labeled commitments based on action meaning, with owners scored separately. Review paraphrases manually and log disputed matches; unmatched repeated predictions count as false positives and duplicates. Do not use string equality alone as semantic correctness.

**Empty denominators and missing/invalid predictions (proposal):** Report undefined ratios as N/A with counts, and report failed/missing outputs separately. A failed output leaves all gold commitments missed for recall and must not be removed from coverage reporting. Both-empty cases are not evidence of successful task extraction.

### Reproducibility and README instructions

**Environment and dependencies:** Python 3.12, uv lockfile, Pytest, Ruff, and optional audio/server extras. The extraction client records requested model, CLI version, prompt version/hash, normalized transcript hash, usage, and elapsed time in current outputs. Historical v1 artifacts predate some metadata fields and must not be pooled with v2 results without rerunning.

**Code revision inspected:** `df3a5390451f6e48f6e9f6f868d509d91a3e53fc` on `feature/ccb-codex-integration`.
**Live prerequisites:** Installed Codex CLI with a usable login/network connection; local CCB source and Whisper weights for audio. No model credentials are needed for offline tests.

```bash
uv sync --locked --extra dev --extra audio --extra server
uv run --locked --extra dev pytest
uv run --locked --extra dev ruff check src tests
uv run --locked --extra dev ruff format --check src tests
uv run --locked labsync extract tests/fixtures/meeting.json \
  --model gpt-5.6-sol --output artifacts/m2-synthetic.json
```

Use a fresh output path; extraction refuses to overwrite results and consumes model usage. See README and RUN_UI.md for audio/UI commands. There is no evaluation/scoring command yet. Do not describe `pytest` as a task-quality benchmark.

**Actual September 23 offline check:** 36 tests passed in 2.59 seconds; Ruff passed and 13 Python files were already formatted. Two dependency deprecation warnings were emitted by Starlette/httpx/AnyIO. Tests cover CLI failure handling, invalid citations/owners, imports, uploads, stored results, range requests, retry, interrupted-job recovery, and origin restrictions. Inference is stubbed in these tests. No gold-label scorer validation has been performed.

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

**Review disagreements and any LLM-judge role:** Human review is proposed. No LLM judge or adjudication results are implemented; reviewers and disagreement handling must be confirmed.

## 5. Baselines and initial results

**Proposed lead:** Will; scoring: Bryan; review: Guadalupe.

### Simple baseline

**Method and rationale (implemented, not quantitatively evaluated):** Extract commitments from each meeting independently using a fixed prompt and the agreed output schema. This tests what can be recovered without persistent cross-meeting memory and provides the primary comparison described in Milestone 1.
**Model/rules, version, prompts, settings, and code path:** Codex CLI `gpt-5.6-sol`, `src/labsync/codex_client.py`, and prompt/contract in `src/labsync/extraction.py`. Current prompt is `meeting-extraction-v2`. Earlier synthetic and AMI transcript artifacts use v1 and CLI 0.149.1. The client checks structured output and cited quotes; it does not establish semantic support.
**Information available to this baseline:** Current timestamped transcript and supplied speaker labels only, with no prior meeting transcripts, stored task state, or gold labels. Corpus A-D labels are not verified identities; audio without diarization uses UNKNOWN.

### Off-the-shelf open-source reference baseline

**Model/system, source, version, and license:** [TODO]
**How it is run and adapted to the same evaluation contract:** [TODO]
**Why it is a relevant reference:** [TODO]

The assignment requires an open-source reference baseline when applicable. If claiming it is not applicable, explain why and raise that interpretation with the TA. A proprietary model alone does not supply this reference.

### Measured results

Use the same evaluation inputs for comparable rows. Include actual sample counts and numerators/denominators where appropriate. Use `not measured` rather than zero for missing results. Add or remove columns to match the implemented metrics.

| Method/version                | Split and sample count | Task P/R/F1  | Owner accuracy | Duplicates   | Unsupported completions | Citation validity/support |
| ----------------------------- | ---------------------- | ------------ | -------------- | ------------ | ----------------------- | ------------------------- |
| Codex independent extraction | No reviewed split                 | Not measured | Not measured   | Not measured | Not measured            | Not measured              |
| Open-source reference: not selected | Not run                 | Not measured | Not measured   | Not measured | Not measured            | Not measured              |

**Qualitative scores and sample count:** Not measured; no two-reviewer rubric exercise has been completed.
**Observed integration artifacts, not quality scores:**

| Input | Prompt | Saved extraction time | Predicted decisions / commitments / suggestions | Local artifact |
| --- | --- | --- | --- | --- |
| Synthetic, 3 turns | v1 | 9.550 s | 1 / 1 / 1 | `artifacts/synthetic-codex.json` |
| AMI TS3005a, 287 turns | v1 | 48.241 s | 2 / 3 / 4 | `artifacts/ami/TS3005a-codex.json` |
| AMI 45-second audio, 11 generated turns; September 23 live run | v2 | 5.864 s | 0 / 0 / 0 | `artifacts/server/bfddad72-5e2a-446d-95b6-40b74fb73850/attempt-1/extraction.json` |

These local artifacts were inspected on September 23; original run dates for the two v1 artifacts are not recorded in their JSON. Times are individual extraction calls, not averaged end-to-end latency or a comparison. No monetary cost was measured. Local files are ignored by Git; publish selected permitted artifacts or reproduce them before final submission.
**Interpretation and limitations:** Integration works on the small supplied examples, but no task precision/recall, owner accuracy, semantic citation support, or held-out performance has been measured. Whisper is an open-source transcription component, not a substitute for the required comparable extraction baseline. No comparative conclusion is supported.

## 6. Initial error analysis

Analyze observed baseline failures rather than only anticipated risks. Separate observations from hypotheses about causes.

| Example/source ID | Expected output | Actual output and baseline | Error category | Likely cause | Proposed change and verification |
| ----------------- | --------------- | -------------------------- | -------------- | ------------ | -------------------------------- |
| [TODO]            | [TODO]          | [TODO]                     | [TODO]         | [TODO]       | [TODO]                           |

**Most frequent or consequential failures:** [TODO]
**What we will change next and why:** [TODO]
**What these initial results do not establish:** Recognition accuracy, correct task ownership, extraction completeness, semantic evidence support, or cross-meeting state tracking. One observed concern in the saved TS3005a prediction is the deadline text "In the meantime"; preserving it is schema-valid but does not produce an actionable calendar date. Human adjudication is pending. This is one inspection example, not a measured failure distribution; the requested 20-30-example error analysis is not complete.

## 7. Mandatory TA check-in

**Status:** Scheduled for today, September 23, 2026, as reported by Bryan. No feedback received yet; do not mark complete until the meeting occurs.
**Date and attendees:** September 23, 2026; time and actual attendees to be recorded after the meeting.

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

**Additional questions:** Confirm minimum viable reviewed dataset/scoring coverage before the deadline, and whether the native client can remain a prototype while evaluation artifacts are completed.

### Notes and follow-up

| Advice or decision | Required action | Owner  | Target date |
| ------------------ | --------------- | ------ | ----------- |
| [TODO]             | [TODO]          | [TODO] | [TODO]      |

Do not mark the check-in complete until it occurs. These notes are a collaboration aid; the assignment explicitly requires the meeting but does not prescribe a separate meeting-notes submission.

## 8. Weekly progress, blockers, and next steps

**Progress made:** Implemented independent transcript extraction, AMI/CCB normalization, local audio transcription, and the web upload/results/playback flow. Added a SwiftUI prototype and PostgreSQL schema. Rechecked software tests and refreshed this report against the current branch. Bryan also reported a successful Swagger upload/results/playback smoke test on September 23.

**Top blockers or risks:** iOS is not connected and has not been built/tested in this environment; full Xcode/Simulator is unavailable here. Audio reproduction depends on separately supplied CCB source. Reviewed labels, a scorer, open-source extraction baseline, comparable metrics, and reviewed error analysis remain missing. Team confirmation of final architecture, ownership, data splits, and TA guidance is still needed.

**Planned next steps:** At today's check-in, agree on a small reviewed extraction dataset and matching rules, select an open-source reference, and confirm acceptable checkpoint scope. Implement offline scoring, preserve comparable prediction artifacts, and conduct rubric/error review before final export. Complete the native connection and Simulator tests as a separately tracked application gate. See [task plan](task_plan.md) and [verification checklist](verification.md).

The [weekly journal](../weekly_journal.md) contains the ongoing record. Include the relevant progress in this report so the PDF is self-contained.

## 9. Team contributions and next-milestone work plan

Record actual contributions separately from proposed ownership. This section is required for teams and is non-graded.

| Member            | Actual Milestone 2 contributions | Artifact or evidence |
| ----------------- | -------------------------------- | -------------------- |
| Guadalupe Cantera | Added PostgreSQL schema (Git author `gcantera5`; attribution to confirm) | `db/schema.sql` and Git history |
| Will Liu | Added SwiftUI iOS prototype and local model tests | Commit `2f85320`, `ios/MeetingApp/` |
| Bryan Yang | Integrated CCB/Codex and web backend, added public audio fixture and reproduction docs; performed Swagger smoke test | Commits `533a3c4`, `d499ab4`, integration guides; September 23 user-reported check |

| Task for the next milestone | Confirmed owner | Completion check | Dependencies/blockers | Target date |
| --------------------------- | --------------- | ---------------- | --------------------- | ----------- |
| Native backend integration and Simulator run | Unconfirmed | Upload, results, playback, relaunch pass | Full Xcode and API client | Agree at check-in |
| Reviewed data and offline scorer | Unconfirmed | Labels, matching rules, deterministic reports | Two-reviewer agreement | Before milestone submission |
| Comparable baselines and error review | Unconfirmed | Saved predictions, metrics, rubric results | Data and scorer | Before milestone submission |

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
