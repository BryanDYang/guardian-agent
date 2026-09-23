# Milestone 2: Prototype and Initial Model Integration

**Course:** CIS-5980 AI Capstone
**Track:** AI Engineering
**Team:** Will Liu, Guadalupe Cantera, Bryan Yang
**Repository:** https://github.com/BryanDYang/guardian-agent
**Canvas deadline:** September 28, 2026 (recorded by the team; confirm submission time/timezone in Canvas)
**Last updated:** September 23, 2026
**Status:** Check-in draft. No Milestone 1 feedback received; TA meeting scheduled for September 23, 2026 (reported by Bryan). Evaluation results and team review remain outstanding.

## 1. Dataset and Data Card

### Data sourcing and access

**What inputs have we actually assembled, and how can a reviewer access them?**

Our system is intended to accept meeting recordings (MP3 or MP4) or transcripts and help researchers track commitments, decisions, and task changes across recurring meetings. For this milestone, we focus on timestamped transcripts with speaker labels so that extraction can be evaluated separately from transcription and speaker identification. The proposed initial scorer focuses on commitments and suggestion handling; decision extraction and cross-meeting updates need separate labels and scoring before we report their quality.

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

### Data Card deliverable

A Data Card is the dataset's documentation: what it contains, where it came from, how it was prepared and labeled, how it is split, and what uses or conclusions it can support. This section serves as the report's Data Card; it should link to the versioned dataset manifest and annotation guide so reviewers can reproduce the evaluation.

Before submission, record actual sequence/meeting counts, duration or segment counts, speaker and language coverage, commitment/suggestion/update label counts, source versions, preprocessing, reviewer names, disagreement resolution, split IDs, and access instructions. Planned sizes must remain labeled as planned until the inputs and labels are verified.

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
**Current split status:** Development inputs exist, but reviewed labels and split manifests are not yet assembled. No held-out performance or generalization claims are supported.


**Planned expansion:** Add a reviewed synthetic three-meeting development sequence, verify ICSI Bmr001-Bmr003 or an equivalent recurring sequence for validation, and reserve a separate ICSI sequence for held-out testing. These additional inputs are not yet assembled.

**Leakage controls:** Verify that candidate ICSI meeting IDs form a meaningful chronological sequence rather than assuming adjacent IDs share tasks. Keep linked tasks and related project history within one split. If validation and test selections share a research group, participants, or project, document the overlap and avoid claiming evaluation on unseen groups. If prior work already used the proposed validation inputs for prompt development, reclassify them as development and choose a fresh validation sequence. Public corpora may also have appeared in model pretraining, which we cannot rule out.

### Known limitations

The initial synthetic sequence will test selected behaviors but cannot establish performance on natural research meetings. Small samples and author-designed scenarios may miss conversational variation and difficult negative examples. Label disagreements will require review. Transcript-only evaluation will not measure transcription or diarization quality. AMI product-design conversations differ from advisor/student meetings; ICSI research conversations are closer to the target setting but reflect an older collection period. Both require verification of task-specific labels. The initial plan focuses on English and small groups; actual language, speaker, and domain coverage must be documented once inputs are assembled. It cannot establish performance across languages, accents, larger meetings, or research fields.

## 2. Evaluation harness

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

## 3. Qualitative evaluation rubric

**Proposed protocol:** Two team members independently review a shared sample of extracted commitments and, once available, proposed updates. Include ordinary cases and each error category, record individual scores, and reconcile disagreements with evidence. Reviewer names, sample size, and actual scores remain pending.

The following rubric is a proposed starting point for team review, not a completed grading exercise. Score 2 falls between anchors 1 and 3; score 4 is usable with minor corrections between anchors 3 and 5. Record critical errors separately so an average cannot hide an unsupported completion.

| Dimension                                | 1: poor                                                                | 3: needs substantial correction                                       | 5: high quality                                                       |
| ---------------------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Faithfulness/evidence support            | Invents commitments or unsupported changes                             | Mixes supported content with unsupported details requiring correction | Every substantive field or change is supported by the cited evidence  |
| Owner and speaker attribution            | Assigns work to the wrong person without evidence                      | Some attributions require correction or uncertainty is unclear        | All owners are supported; genuinely unknown owners remain unresolved  |
| Coverage of relevant commitments/updates | Misses most relevant commitments or updates                            | Captures the main items but misses material details or items          | Captures all relevant labeled items without duplicates                |
| Ambiguity and suggestion handling        | Treats suggestions or ambiguous speech as definite commitments/updates | Handles clear cases but mishandles some uncertainty                   | Separates suggestions and routes genuinely ambiguous cases for review |
| Clarity and usefulness                   | Output is unusable or misleading                                       | Understandable but needs substantive editing                          | Tasks are concise, actionable, and easy to verify against evidence    |

**Illustrative example, not an evaluated result:** At segment `s1`, Will says, "I will rerun the baseline by Friday." At `s2`, the advisor says, "You could try mixed precision." A good output records Will's rerun commitment with `s1` as evidence and keeps mixed precision as an unaccepted suggestion. Assigning mixed precision to Will as a confirmed task is an unsupported commitment. Converting Friday to a calendar date requires meeting-date/timezone context. Actual baseline examples will be added after runs.

**Review disagreements and any LLM-judge role:** Human review is proposed. No LLM judge or adjudication results are implemented; reviewers and disagreement handling must be confirmed.

## 4. Baselines and initial results

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

## 5. Initial error analysis

Analyze observed baseline failures rather than only anticipated risks. Separate observations from hypotheses about causes.

| Example/source ID | Expected output | Actual output and baseline | Error category | Likely cause | Proposed change and verification |
| ----------------- | --------------- | -------------------------- | -------------- | ------------ | -------------------------------- |
| [TODO]            | [TODO]          | [TODO]                     | [TODO]         | [TODO]       | [TODO]                           |

**Most frequent or consequential failures:** [TODO]
**What we will change next and why:** [TODO]
**What these initial results do not establish:** Recognition accuracy, correct task ownership, extraction completeness, semantic evidence support, or cross-meeting state tracking. One observed concern in the saved TS3005a prediction is the deadline text "In the meantime"; preserving it is schema-valid but does not produce an actionable calendar date. Human adjudication is pending. This is one inspection example, not a measured failure distribution; the requested 20-30-example error analysis is not complete.

## 6. Mandatory TA check-in

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

## 7. Weekly progress, blockers, and next steps

**Progress made:** Implemented independent transcript extraction, AMI/CCB normalization, local audio transcription, and the web upload/results/playback flow. Added a SwiftUI prototype and PostgreSQL schema. Rechecked software tests and refreshed this report against the current branch. Bryan also reported a successful Swagger upload/results/playback smoke test on September 23.

**Top blockers or risks:** iOS backend upload integration is present in code, but a completed native build and Simulator end-to-end verification are not established in this report. Audio reproduction depends on separately supplied CCB source. Reviewed labels, a scorer, open-source extraction baseline, comparable metrics, and reviewed error analysis remain missing. Team confirmation of final architecture, ownership, data splits, and TA guidance is still needed.

**Planned next steps:** Agree on one transcript and its expected output, finalize the shared schema, prepare reviewed development labels, implement baselines and scoring, and run the first comparison. Then expand coverage, inspect failures, complete the TA check-in, and replace pending report sections with evidence. See the [verification checklist](verification.md) for application integration checks. Generated recordings, transcripts, and predictions remain outside Git; document reproduction commands and reviewer access separately.

The [weekly journal](../weekly_journal.md) contains the ongoing record. Include the relevant progress in this report so the PDF is self-contained.

## 8. Team contributions and next-milestone work plan

Record actual contributions separately from proposed ownership. This section is required for teams and is non-graded.

| Member            | Actual Milestone 2 contributions | Artifact or evidence                |
| ----------------- | -------------------------------- | ----------------------------------- |
| Guadalupe Cantera | Database and data research       | db                                  |
| Will Liu          | frontend + backend integration   | ios                                 |
| Bryan Yang        | backend + frontend integration   | labsync - agent-sandbox integration |

## 10. Final submission checklist

- [X] AI Engineering track and team declared.
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

## 11. References

- [AMI and ICSI official distribution and license overview](https://groups.inf.ed.ac.uk/ami/).
- [AMI Meeting Corpus](https://groups.inf.ed.ac.uk/ami/corpus/).
- [ICSI Meeting Corpus](https://groups.inf.ed.ac.uk/ami/icsi/) and [ICSI license](https://groups.inf.ed.ac.uk/ami/icsi/license.shtml).
- [Project database schema](../../db/schema.sql), including meeting consent and optional voice-embedding fields.
- [Weekly journal](../weekly_journal.md).
