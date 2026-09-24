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

**Current inputs:** A scored synthetic development suite is now available: 24 independent micro-meetings, 35 turns, 15 labeled obligations, and 11 negative cases. Labels and matching rules were AI-authored before inference and still need human review. The following inputs exist; generated predictions are not gold labels.

| Source/subset | Actual size | Format and coverage | Access |
| --- | --- | --- | --- |
| Synthetic development benchmark | 24 micro-meetings, 35 turns, 15 obligations | AI-authored labels; frozen lexical matching; 3 measured baselines | `tests/fixtures/evaluation/development.json` |
| Synthetic extraction example | 1 meeting, 3 turns | Explicit agreement, Sam's commitment with raw deadline, unaccepted suggestion | `tests/fixtures/meeting.json` |
| AMI TS3005 manual transcripts | 1 series, 4 meetings; 287/693/619/1,194 nonempty turns | Timestamped corpus speakers A-D; no reviewed LabSync commitment/state labels | Local `artifacts/ami/TS3005{a,b,c,d}.json`; reproduction in `docs/codex-integration.md` |
| AMI audio excerpt | 1 clip, 45 seconds, TS3005a 90-135s | Mono 16 kHz PCM WAV; opening/agenda content, not a commitment benchmark | `tests/fixtures/ami/TS3005a-90s-135s.wav` |

See the [integration guide](../codex-integration.md) for acquisition and conversion commands and the [AMI fixture documentation](../../tests/fixtures/ami/README.md) for attribution, checksums, and audio preparation. Full corpus downloads and their generated predictions remain local and ignored by Git. Synthetic benchmark predictions also remain local under `artifacts/evaluation/`; the submission includes the measured results and failure analysis.

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

**Current split status:** The new 24-case suite is development-only and does not establish sequence tracking. The tables above describe planned corpus allocations. The three-meeting synthetic sequence, validation/test membership, human-reviewed labels, and corpus split manifest remain unfinished. The synthetic suite records its development split and input IDs. The existing synthetic example contains one meeting. The AMI audio clip overlaps TS3005a and must stay in the same split. Verify ICSI chronology and continuity before treating the proposed IDs as a related sequence.

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

This section serves as our Data Card. The synthetic benchmark now records its exact inputs, 15 obligation labels, development split, annotation/matching guide and reproducible predictions. Before submission, human reviewers and disagreements must be recorded; corpus labels and final validation/test membership remain unfinished. Real recordings and corpus outputs stay outside Git. Synthetic benchmark outputs remain local; summary measurements and observed failures are included in this report.

#### Annotation details still to finalize

**What is labeled?** Proposed labels include commitment descriptions, owners, supported deadlines, source segment IDs, and suggestions kept separate from accepted commitments. Sequence annotations will also record links to earlier tasks and expected state after each meeting. Decisions and historical Q&A are outside the first extraction scorer unless explicitly added.

**Labeling rules (proposed):** A suggestion becomes a commitment only with evidence of acceptance. Unknown owners and missing deadlines remain unknown rather than inferred. Explicit supported completion can change a task to done; partial progress, negation, and silence cannot. Ambiguous references require review rather than an invented task link. Every accepted record or update must identify its supporting transcript segment.

**Review and disagreement resolution:** No independently reviewed gold labels or disagreement log exists yet. Assign a labeler and second reviewer at the team check-in before treating examples as scored evaluation data.

**Implemented development guide:** [Fixture protocol](../../tests/fixtures/evaluation/README.md) specifies AI authorship, labels, task granularity, unknown/joint owners, minimal deadline text, one-to-one action-term matching, denominators, and known limitations. These rules were frozen before model runs; they have not been human-adjudicated.

**Annotation guide and schema location:** `src/labsync/extraction.py` contains the provisional Pydantic contract and `meeting-extraction-v2` prompt. Inputs contain project/meeting IDs and turns with IDs, speakers, millisecond timestamps, and content. Outputs contain a summary, decisions, commitments, and suggestions. Commitments preserve nullable owners and verbatim deadline text plus one or more cited quotes. Team-reviewed annotation and matching rules are not yet finalized.

## 2. Evaluation harness

### Metrics and scoring

**Why do the chosen metrics reflect success?** Users need commitments to be found without invented tasks, assigned to the right people, and linked to supporting evidence. Precision/recall measures extraction coverage and correctness; owner accuracy measures attribution; duplicate counts expose repeated tasks; citation checks measure traceability. Unsupported completion and state/link metrics will apply when update predictions are implemented. A model that produces no updates cannot be credited with successful reconciliation solely because it has no false completions.

The implemented extraction metrics are recorded with numerators and denominators in the [initial results summary](results/README.md).

| Metric | Implemented definition | Status |
| --- | --- | --- |
| Task precision / recall / F1 proxy | Maximum one-to-one matches using frozen action-term alternatives; matches/predictions, matches/labels, harmonic mean | Measured on 24 synthetic development cases per baseline; semantic adjudication pending |
| Owner agreement | Exact label agreement among matched tasks with known gold owners; null-owner cases separate | Measured |
| Deadline text agreement | Exact raw text agreement among matched tasks, including nulls | Measured; not semantic date accuracy |
| Duplicate proxy | Additional predictions compatible with already matched obligations / predicted tasks | Measured |
| Citation validity | Exact contiguous quote and existing source ID / all predicted citations | Measured; not semantic support |
| Evidence completeness | Matched tasks citing all designated gold source IDs with valid quotes / matched tasks | Measured; alternate sufficient evidence may be penalized |
| Semantic evidence support | Human-supported items / reviewed items | Human review pending |
| Unsupported completion and state/link accuracy | Requires state-update predictions and reviewed sequences | Deferred: reconciliation not implemented |

### Benchmark and matching protocol

The suite covers explicit promises, accepted/unaccepted requests, suggestions, negation, conditional speech, completed/partial work, UNKNOWN speakers, multiple owners/actions, repetition, deadline correction, quoted examples, and adversarial transcript text. These are independent current-meeting extraction cases, not evidence of cross-meeting state tracking. See the [annotation and matching protocol](../../tests/fixtures/evaluation/README.md).

The scorer uses lexical action matching as a transparent development proxy. Owners and dates are scored separately, and maximum-cardinality matching prevents greedy order effects. Unseen paraphrases can be false negatives; titles containing the expected terms can match despite unsupported additional content. Human semantic adjudication remains necessary. Undefined ratios are N/A; failed/missing outputs retain their gold labels in recall and are reported as failures. Both-empty cases are counted only in the separate negative-case metric.

### Reproducibility and instructions

The harness is `src/labsync/evaluation.py`; live generation and offline scoring are separate commands. It stores predictions, errors, source/suite/input hashes, model settings, UTC run time and latency. Existing Codex metadata includes prompt hash, CLI version and usage; Ollama metadata includes quantization, immutable model digest and runtime version. No gold labels or action terms are sent to either model.

```bash
uv run --locked --extra dev pytest tests/benchmarks/
uv run --locked python -m labsync.evaluation score \
  --directory artifacts/evaluation/codex-v1
uv run --locked python -m labsync.evaluation run --method rules \
  --directory artifacts/evaluation/rules-new
uv run --locked python -m labsync.evaluation score \
  --directory artifacts/evaluation/rules-new
```

Full live commands and prerequisites are in the fixture protocol. Offline re-scoring needs the saved local run artifacts but no credentials or network. A fresh checkout can regenerate results using the documented inference commands. Live output directories must be fresh; Codex inference consumes model usage.

**September 24 verification:** 52 offline tests passed, including 15 new scorer/benchmark tests. Ruff passed. These tests validate scoring against correct and deliberately incorrect predictions, including duplicates, missing outputs, invalid citations and changed input hashes. They are distinct from the 72 actual baseline extraction runs (48 live model calls and 24 rule-based extractions). Existing dependency deprecation warnings remain; they do not alter the benchmark results.

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

**Illustrative example, not an evaluated result:** At segment `s1`, Will says, "I will rerun the baseline by Friday." At `s2`, the advisor says, "You could try mixed precision." A good output records Will's rerun commitment with `s1` as evidence and keeps mixed precision as an unaccepted suggestion. Assigning mixed precision to Will as a confirmed task is an unsupported commitment. Converting Friday to a calendar date requires meeting-date/timezone context. Actual baseline outputs and observed failures are now linked in Section 4; this illustrative rubric example is not a completed human score.

**Review disagreements and any LLM-judge role:** Human review is proposed. No LLM judge or adjudication results are implemented; reviewers and disagreement handling must be confirmed.

## 4. Baselines and initial results

**Proposed lead:** Will; scoring: Bryan; review: Guadalupe.

### Baselines and actual measurements

The simple baseline detects first-person promises with fixed rules. The existing Codex independent-meeting extractor uses `gpt-5.6-sol`, CLI 0.149.1 and `meeting-extraction-v2`. The external open-source reference is IBM Granite Code 8B (Apache 2.0), served locally by Ollama 0.6.8 in Q4_0 with temperature 0 and seed 42. It uses the same transcript contract and extraction instructions with JSON Schema output. It was already installed and is code-specialized, so it is a first off-the-shelf reference, not a meeting-specialized or best-open-source claim. Exact model digest, sources, prompts/settings, platform and validation differences are documented in the [results summary](results/README.md).

All methods see only the current transcript and speaker labels, without stored task state or gold labels. The same 24 synthetic development cases contain 15 obligations. Labels were AI-authored and frozen before inference; human review is pending.

| Method | Matched / predicted / gold | Task P / R / F1 proxy | Known-owner agreement | Exact deadline text | Duplicate proxy | Citation validity | Failures |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Promise rules v1 | 11 / 16 / 15 | .688 / .733 / .710 | 9/9 | 10/11 | 2/16 | 16/16 | 0/24 |
| Codex independent extraction v2 | 13 / 14 / 15 | .929 / .867 / .897 | 12/12 | 5/13 | 1/14 | 31/31 | 0/24 |
| Granite Code 8B | 9 / 11 / 15 | .818 / .600 / .692 | 7/7 | 6/9 | 0/11 | 21/21 | 0/24 |

Correct negative-case counts are 9/11, 11/11 and 10/11, respectively. Null-owner agreement among matched tasks is 1/2, 0/1 and 0/2, separate from known owners. Codex and Granite mean extraction times are 5.280 s and 5.061 s across 24 attempts each, including warmup and excluding audio/UI. Runs overlapped, so these are observed timings rather than a controlled speed comparison. Rule timings are mostly below the stored 1 ms resolution. No monetary cost was measured.

**Interpretation:** Codex has the highest action-matching proxy on these fixtures. This does not establish held-out performance, semantic accuracy, or a general model ranking. Exact quotes can still support a negated statement incorrectly treated as a commitment. Exact deadline-span agreement can penalize semantically equivalent `Friday` and `by Friday`. The scorer also has a known false negative for Granite's `Preparing the demo` versus the frozen `prepare` term.

### Observed failures and next changes

Local reports in `artifacts/evaluation/{rules,codex,granite}-v1/` contain expected and actual outputs and error flags for all 24 examples per method. Raw artifacts are retained locally; the submission presents aggregate results and representative failures. The [failure analysis](results/README.md#observed-errors-and-next-verification) separates observations from likely causes and scoring/annotation limitations.

- Rules extract negated and quoted promises, duplicate repeated commitments, and miss cross-turn acceptance.
- Codex misses the UNKNOWN-owner commitment and merges two distinct actions. Its eight deadline mismatch flags are largely raw-span differences. Joint ownership exposes the single-owner contract's ambiguity.
- Granite extracts a negated promise, assigns literal UNKNOWN, misses both tasks in `two_owners`, and fails to resolve some accepted/reassigned work. One unmatched task is a lexical scorer false negative.

Next, reviewers should resolve joint-owner and task-granularity policies, adjudicate semantic matches and deadline equivalence, and then test a separately versioned prompt on new development examples. Do not silently tune v1 labels or matching terms to these predictions.

**Qualitative scores:** No two-human-reviewer rubric exercise has been completed. Automated case reports and AI inspection do not substitute for it. Audio recognition, diarization, RAG, unsupported completion and cross-meeting state tracking remain outside these measurements.

## 5. Weekly check-ins and blockers

**Progress made:** Implemented independent transcript extraction, AMI/CCB normalization, local audio transcription, and the web upload/results/playback flow. Added a SwiftUI prototype and PostgreSQL schema. Rechecked software tests and refreshed this report against the current branch. Bryan also reported a successful Swagger upload/results/playback smoke test on September 23.

**Top blockers or risks:** iOS backend upload integration is present in code, but a completed native build and Simulator end-to-end verification are not established in this report. Audio reproduction depends on separately supplied CCB source. Human-reviewed labels, semantic adjudication, natural-meeting evaluation and reviewed qualitative scores remain missing. The scorer, three baseline runs, saved predictions and measured development proxies are now available. Team confirmation of final architecture, ownership, data splits, and TA guidance is still needed.

**Planned next steps:** Human-review the 24-case labels and observed errors, resolve task granularity/joint-owner/deadline policies, and expand coverage to natural meetings. Complete qualitative review and TA follow-up before final submission. See the [verification checklist](verification.md) for application integration checks. Raw recordings, predictions and generated reports remain outside Git. The results summary includes measurements, observed failures and reproduction instructions.

Earlier progress is recorded in the [weekly journal](../weekly_journal.md).

### TA check-in

**Status:** Scheduled for today, September 23, 2026, as reported by Bryan. No feedback received yet; do not mark complete until the meeting occurs.
**Date and attendees:** September 23, 2026; time and actual attendees to be recorded after the meeting.

#### Preparation checklist

- [ ] Data Card summary with actual inputs, splits, and limitations.
- [x] Working evaluation command and README instructions.
- [x] Initial development baseline results table; human adjudication still pending.
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

Initial proxy scoring and baseline comparisons run now. Semantic claims depend on human-reviewed labels and matching; a broader general-purpose open-source reference and natural-meeting evaluation remain follow-up work. Audio reproduction requires separately supplied CCB source; native integration still needs end-to-end verification. Final owners, data access arrangements, and TA guidance need team confirmation.

## 7. Reference

- [AMI and ICSI official distribution and license overview](https://groups.inf.ed.ac.uk/ami/).
- [AMI Meeting Corpus](https://groups.inf.ed.ac.uk/ami/corpus/).
- [ICSI Meeting Corpus](https://groups.inf.ed.ac.uk/ami/icsi/) and [ICSI license](https://groups.inf.ed.ac.uk/ami/icsi/license.shtml).
- [Project database schema](../../db/schema.sql), including meeting consent and optional voice-embedding fields.
- [Weekly journal](../weekly_journal.md).

## 8. GitHub Repository Link

https://github.com/BryanDYang/guardian-agent
