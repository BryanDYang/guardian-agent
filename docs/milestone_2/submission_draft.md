# Milestone 2: Prototype and Initial Model Integration

**Course:** CIS-5980
**Track:** AI Engineering
**Team:** Will Liu, Guadalupe Cantera, and Bryan Yang
**Repository:** https://github.com/BryanDYang/guardian-agent

<!-- Aligned with project_drafts (1).docx. Existing implementation evidence fills its blank sections; TODO items still need team input. -->

## 1. Dataset and Data Card

### Data sourcing and access

Our system is designed to help researchers keep track of tasks, commitments, and decisions across recurring meetings. It takes meeting recordings (MP3 or MP4) or transcripts and uses them to identify action items, generate summaries, and track how tasks change from one meeting to the next.

For Milestone 2, we are focusing on the transcript-to-task extraction step. We will use timestamped transcripts with speaker labels to test whether our system can correctly identify commitments, decisions, and task updates while evaluating extraction separately from the audio-processing pipeline.

We plan to use three main data sources:

**Synthetic meeting transcripts:** We will create a three-meeting sequence based on realistic research meetings. These transcripts will include scenarios such as completed tasks, changed deadlines, suggestions that were never accepted, unclear references to previous tasks, and commitments that are not mentioned again. This will help us test specific situations before moving on to real meeting conversations.

**AMI Meeting Corpus:** We plan to use the TS3005a–d sequence from the AMI Meeting Corpus. This dataset contains four related meetings from a simulated product-design project, along with dialogue, summary, and decision-point annotations. We will use it to see how our system performs on more natural conversations rather than relying only on transcripts we wrote ourselves. The dataset can be accessed through the AMI corpus website and Hugging Face.

**ICSI Meeting Corpus:** We plan to use the Bmr001–Bmr003 sequence, or an equivalent recurring research-group sequence, from the ICSI Meeting Corpus. Since our intended users are researchers who meet regularly, this dataset is closer to the type of conversations we want our application to process. However, it does not include the specific commitment and decision labels we need, so our team will have to annotate those ourselves.

We would also like to eventually test our system using recordings from our own project meetings or research lab meetings. These would give us a better idea of how our system performs in the setting we are actually building it for. However, we will not record or use any meetings without obtaining written consent from everyone involved.

For this milestone, we are focusing on transcripts rather than raw audio so we can evaluate task extraction separately from transcription and speaker identification.

**Current inputs:** No human-reviewed commitment evaluation dataset has been established yet. The following inputs exist; generated predictions are not gold labels.

| Source/subset | Actual size | Format and coverage | Access |
| --- | --- | --- | --- |
| Synthetic extraction example | 1 meeting, 3 turns | Explicit agreement, Sam's commitment with raw deadline, unaccepted suggestion | `tests/fixtures/meeting.json` |
| AMI TS3005 manual transcripts | 1 series, 4 meetings; 287/693/619/1,194 nonempty turns | Timestamped corpus speakers A-D; no reviewed LabSync commitment/state labels | Local `artifacts/ami/TS3005{a,b,c,d}.json`; reproduction in `docs/codex-integration.md` |
| AMI audio excerpt | 1 clip, 45 seconds, TS3005a 90-135s | Mono 16 kHz PCM WAV; opening/agenda content, not a commitment benchmark | `tests/fixtures/ami/TS3005a-90s-135s.wav` |

See the [integration guide](../codex-integration.md) for acquisition and conversion commands and the [AMI fixture documentation](../../tests/fixtures/ami/README.md) for attribution, checksums, and audio preparation. Full corpus downloads and generated predictions remain local and ignored by Git.

### Provenance and licensing

Our data will come from a combination of transcripts created by our team and publicly available meeting datasets. Each source has different permissions and limitations that we need to consider before using it.

| Data source | Origin and licensing | Usage constraints |
| --- | --- | --- |
| Synthetic sequence | Created by our team, with any AI assistance documented and the content manually reviewed. | No real or private meeting information will be included. |
| AMI Meeting Corpus | Developed by the AMI Consortium and the University of Edinburgh. Signals, transcripts, and some annotations are released under CC BY 4.0. | Attribution is required when using or sharing the data. |
| ICSI Meeting Corpus | Collected by the International Computer Science Institute in Berkeley. Signals, transcripts, and some annotations are released under CC BY 4.0 through the University of Edinburgh. | We will confirm the dataset's distribution and usage terms before using it. Raw data will not be uploaded to our GitHub repository. |
| Our own meetings (planned) | Recordings collected by our team with written consent from participants. | Recordings will remain private and will not be uploaded to GitHub. Participants can request that their recordings be excluded or deleted. |

Privacy is an important part of our project, especially since meeting recordings can contain personal information, unpublished research, or conversations that participants may not want shared outside their group.

Our current database schema includes a consent_given field for each meeting, which defaults to false. We also have a field for voice embeddings, which would allow the system to recognize returning speakers across meetings.

The schema fields do not by themselves implement speaker recognition or enforce participant-level consent. Since voice embeddings can be used to identify individuals, we will only create them for participants who have explicitly consented. We will also keep private recordings, transcripts, and identifying information out of our public repository.

Before using recordings from our own meetings, we will make sure participants understand how their data will be used, who will have access to it, and whether any external AI services will process their information.

### Splits

We are not training or fine-tuning our own model for this milestone. Instead, we will use our datasets to develop and evaluate the prompts and extraction rules used by our system.

Since our application is meant to track information across multiple meetings, we will split the data by meeting sequence rather than by individual transcript. This means that all meetings from the same sequence will stay together in one split.

For example, we would not want Meeting 1 from a research group in our development set and Meeting 2 from that same group in our test set. The system could already have information about the tasks and decisions from the first meeting, which would make our evaluation results less reliable.

Our planned splits are:

| Split | Dataset | Purpose |
| --- | --- | --- |
| Development | Synthetic three-meeting sequence and AMI TS3005a–d | Develop and improve our prompts and extraction rules, test specific scenarios, and identify initial errors. |
| Validation | ICSI Bmr001–Bmr003 | Check how well our system performs on recurring research meetings and identify issues before final testing. |
| Test | A separate ICSI meeting sequence and potentially our own meetings, if consent is obtained. | Evaluate the final version of our system on meeting sequences that were not used during development. |

We will use the development set to make changes to our prompts and rules as we identify problems. The validation set will help us check whether those changes also work on conversations outside our initial examples.

The test set will remain separate from the development process so that our final results reflect how well the system performs on previously unseen meeting sequences.

Since we are starting with a relatively small amount of data, we will also document exactly which meetings are included in each split and avoid making broad claims about the system's performance based on only a few examples.

**Current split status:** The tables above describe planned allocations. The three-meeting synthetic sequence, validation/test membership, reviewed labels, and split manifest remain unfinished. The existing synthetic example contains one meeting. The AMI audio clip overlaps TS3005a and must stay in the same split. Verify ICSI chronology and continuity before treating the proposed IDs as a related sequence.

### Known limitations

There are a few limitations with our current datasets that we need to keep in mind when evaluating our system.

**Small dataset size:** We are starting with a limited number of meeting sequences. This should be enough to test specific scenarios, but it will not tell us how well our system performs across different research groups, meeting formats, or larger organizations.

**Synthetic data:** Our team-created transcripts will help us test situations such as completed tasks, changed deadlines, and unclear references. However, these conversations may be more structured than real meetings and might not capture things like interruptions, incomplete sentences, or situations we did not think to include.

**Domain mismatch:** The AMI Meeting Corpus focuses on a simulated product-design project rather than recurring academic research meetings. The ICSI corpus is closer to our intended setting, but its recordings are from the early 2000s and may not fully reflect how research teams communicate today.

**Manual annotation:** The ICSI corpus does not include all the labels we need, so our team will have to identify commitments, decisions, task owners, and updates ourselves. Some statements may be difficult to label, especially when deciding whether someone actually committed to a task or was just making a suggestion. To reduce inconsistencies, a second teammate will review the annotations, and we will document any disagreements.

**Transcript quality:** For this milestone, we are assuming that transcripts already have timestamps and speaker labels. This means we are not yet evaluating errors from transcription or speaker identification, which could affect how well the full application performs once we start processing audio recordings.

**Limited coverage:** Our initial datasets will focus on English-language meetings with a relatively small number of speakers. Because of this, we cannot yet determine how well our system will perform with different languages, accents, larger meetings, or research groups from different fields.

These limitations are important to keep in mind because we do not want to assume that our system works well in every setting just because it performs well on a few selected examples. As we continue developing the application, we will use our evaluation results to identify where the system struggles and what additional data we may need.

### Data Card Deliverable

This section serves as our Data Card: it documents the data sources, permissions, preparation, splits, and limitations. Before submission, we still need to record the final meeting IDs and counts, annotation guide, label counts, reviewers, disagreements, and access instructions. Generated recordings, transcripts, and predictions will remain outside Git; reviewers can use documented reproduction commands or separately arranged access.

#### Annotation details still to finalize

**What is labeled?** Proposed labels include commitment descriptions, owners, supported deadlines, source segment IDs, and suggestions kept separate from accepted commitments. Sequence annotations will also record links to earlier tasks and expected state after each meeting. Decisions and historical Q&A are outside the first extraction scorer unless explicitly added.

**Labeling rules (proposed):** A suggestion becomes a commitment only with evidence of acceptance. Unknown owners and missing deadlines remain unknown rather than inferred. Explicit supported completion can change a task to done; partial progress, negation, and silence cannot. Ambiguous references require review rather than an invented task link. Every accepted record or update must identify its supporting transcript segment.

**Review and disagreement resolution:** No independently reviewed gold labels or disagreement log exists yet. Assign a labeler and second reviewer at the team check-in before treating examples as scored evaluation data.

**Annotation guide and schema location:** `src/labsync/extraction.py` contains the provisional Pydantic contract and `meeting-extraction-v2` prompt. Inputs contain project/meeting IDs and turns with IDs, speakers, millisecond timestamps, and content. Outputs contain a summary, decisions, commitments, and suggestions. Commitments preserve nullable owners and verbatim deadline text plus one or more cited quotes. Team-reviewed annotation and matching rules are not yet finalized.

## 2. Evaluation harness

### Metrics and scoring

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

### Benchmark or custom test suite

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

### Reproducibility and instructions

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

### Qualitative rubric

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

### Open-source reference baseline

**Model/system, source, version, and license:** [TODO]
**How it is run and adapted to the same evaluation contract:** [TODO]
**Why it is a relevant reference:** [TODO]

The assignment requires an open-source reference baseline when applicable. If claiming it is not applicable, explain why and raise that interpretation with the TA. A proprietary model alone does not supply this reference.

### Results table

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

These local artifacts were inspected on September 23; original run dates for the two v1 artifacts are not recorded in their JSON. Times are individual extraction calls, not averaged end-to-end latency or a comparison. No monetary cost was measured. Local files are ignored by Git; document reproduction commands and arrange reviewer access separately before final submission; generated artifacts do not need to be committed.
**Interpretation and limitations:** Integration works on the small supplied examples, but no task precision/recall, owner accuracy, semantic citation support, or held-out performance has been measured. Whisper is an open-source transcription component, not a substitute for the required comparable extraction baseline. No comparative conclusion is supported.

### Analyze baseline failures

Analyze observed baseline failures rather than only anticipated risks. Separate observations from hypotheses about causes.

| Example/source ID | Expected output | Actual output and baseline | Error category | Likely cause | Proposed change and verification |
| ----------------- | --------------- | -------------------------- | -------------- | ------------ | -------------------------------- |
| [TODO]            | [TODO]          | [TODO]                     | [TODO]         | [TODO]       | [TODO]                           |

**Most frequent or consequential failures:** [TODO]
**What we will change next and why:** [TODO]
**What these initial results do not establish:** Recognition accuracy, correct task ownership, extraction completeness, semantic evidence support, or cross-meeting state tracking. One observed concern in the saved TS3005a prediction is the deadline text "In the meantime"; preserving it is schema-valid but does not produce an actionable calendar date. Human adjudication is pending. This is one inspection example, not a measured failure distribution; the requested 20-30-example error analysis is not complete.

## 5. Weekly check-ins and blockers

**Progress made:** Implemented independent transcript extraction, AMI/CCB normalization, local audio transcription, and the web upload/results/playback flow. Added a SwiftUI prototype and PostgreSQL schema. Rechecked software tests and refreshed this report against the current branch. Bryan also reported a successful Swagger upload/results/playback smoke test on September 23.

**Top blockers or risks:** iOS backend upload integration is present in code, but a completed native build and Simulator end-to-end verification are not established in this report. Audio reproduction depends on separately supplied CCB source. Reviewed labels, a scorer, open-source extraction baseline, comparable metrics, and reviewed error analysis remain missing. Team confirmation of final architecture, ownership, data splits, and TA guidance is still needed.

**Planned next steps:** Agree on one transcript and its expected output, finalize the shared schema, prepare reviewed development labels, implement baselines and scoring, and run the first comparison. Then expand coverage, inspect failures, complete the TA check-in, and replace pending report sections with evidence. See the [verification checklist](verification.md) for application integration checks. Generated recordings, transcripts, and predictions remain outside Git; document reproduction commands and reviewer access separately.

Earlier progress is recorded in the [weekly journal](../weekly_journal.md).

### TA check-in

**Status:** Scheduled for today, September 23, 2026, as reported by Bryan. No feedback received yet; do not mark complete until the meeting occurs.
**Date and attendees:** September 23, 2026; time and actual attendees to be recorded after the meeting.

#### Preparation checklist

- [ ] Data Card summary with actual inputs, splits, and limitations.
- [ ] Working evaluation command and README instructions.
- [ ] Baseline results table.
- [ ] Top risks and blockers.

#### Questions for discussion

1. What Milestone 1 feedback should change our scope or evaluation priorities?
2. Is our actual dataset size, sequence coverage, and split strategy sufficient for this checkpoint?
3. Are the simple baseline and selected open-source reference appropriate?
4. Is a transcript-first evaluation appropriate while sponsor audio/data access is unresolved?
5. How should we reconcile the differing application architectures in the Milestone 1 artifacts?

**Additional questions:** Confirm minimum viable reviewed dataset/scoring coverage before the deadline, and whether the native client can remain a prototype while evaluation artifacts are completed.

#### Notes and follow-up

| Advice or decision | Required action | Owner  | Target date |
| ------------------ | --------------- | ------ | ----------- |
| [TODO]             | [TODO]          | [TODO] | [TODO]      |

Do not mark the check-in complete until it occurs. These notes are a collaboration aid; the assignment explicitly requires the meeting but does not prescribe a separate meeting-notes submission.

## 6. For group only (non-graded)

### Team members and roles

| Member            | Actual Milestone 2 contributions | Artifact or evidence                |
| ----------------- | -------------------------------- | ----------------------------------- |
| Guadalupe Cantera | Database and data research       | db                                  |
| Will Liu          | frontend + backend integration   | ios                                 |
| Bryan Yang        | backend + frontend integration   | labsync - agent-sandbox integration |

### Work plan for the next milestone with an owner for each task

The following assignments are proposed and need team confirmation.

| Task | Proposed owner | Completion check |
| --- | --- | --- |
| Assemble data, annotation guide, and reviewed labels | Guadalupe; second reviewer TODO | Meeting IDs, provenance, split manifest, and reviewed labels recorded |
| Finalize extraction contract and comparable baselines | Will | Both baselines produce saved predictions on the same reviewed inputs |
| Implement offline scoring and reproducibility instructions | Bryan | Scorer detects deliberately incorrect predictions and produces a results table |
| Review errors and complete submission | All members | Rubric scores, error examples, TA follow-up, and reviewed PDF completed |

### Blockers, dependencies, or risks

Scoring depends on reviewed labels and agreed matching rules. Baseline comparison depends on selecting an applicable open-source extraction system. Audio reproduction requires separately supplied CCB source; native integration still needs end-to-end verification. Final owners, data access arrangements, and TA guidance need team confirmation.

## 7. Reference

- [AMI and ICSI official distribution and license overview](https://groups.inf.ed.ac.uk/ami/).
- [AMI Meeting Corpus](https://groups.inf.ed.ac.uk/ami/corpus/).
- [ICSI Meeting Corpus](https://groups.inf.ed.ac.uk/ami/icsi/) and [ICSI license](https://groups.inf.ed.ac.uk/ami/icsi/license.shtml).
- [Project database schema](../../db/schema.sql), including meeting consent and optional voice-embedding fields.
- [Weekly journal](../weekly_journal.md).

## 8. GitHub Repository Link

https://github.com/BryanDYang/guardian-agent
