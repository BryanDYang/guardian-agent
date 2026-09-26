# Milestone 2 Prototype and Initial Model Integration

**Course:** CIS-5980
**Track:** AI Engineering
**Team:** Will Liu, Guadalupe Cantera, and Bryan Yang
**Repository:** https://github.com/BryanDYang/guardian-agent

**Report updated:** September 25, 2026

This report documents the datasets, evaluation methods, initial results, and next steps for LabSync. Measured results cover audio transcription and independent-meeting task extraction. Cross-meeting reconciliation, diarization, and RAG are not established by these evaluations.

## 1 Dataset and Data Card

### Data sourcing and access

Our system is designed to help researchers keep track of tasks, commitments, and decisions across recurring meetings. It takes meeting recordings (MP3 or MP4) or transcripts and uses them to identify action items, generate summaries, and track how tasks change from one meeting to the next.

For Milestone 2, our primary measured baseline is audio transcription through CCB's supplied meeting transcriber. We compare Whisper tiny and base against manual AMI references with separate development, validation and test series. A supplementary transcript-to-task evaluation measures extraction separately; task updates and RAG remain future work.

Our current evaluation uses AMI audio and synthetic transcripts. The following distinguishes those inputs from planned sequence evaluation:

**Synthetic meeting transcripts:** The current benchmark contains 24 independent micro-meetings. For future sequence evaluation, we will create a three-meeting sequence based on realistic research meetings. These transcripts will include scenarios such as completed tasks, changed deadlines, suggestions that were never accepted, unclear references to previous tasks, and commitments that are not mentioned again. This will help us test specific situations before moving on to real meeting conversations.

**AMI Meeting Corpus:** We have acquired manual transcripts for the TS3005a-d sequence from the AMI Meeting Corpus. This dataset contains four related meetings from a simulated product-design project, along with dialogue, summary, and decision-point annotations. We will use it to see how our system performs on more natural conversations rather than relying only on transcripts we wrote ourselves. The dataset can be accessed through the AMI corpus website and Hugging Face.

**ICSI Meeting Corpus (planned, not acquired):** We plan to use the Bmr001-Bmr003 sequence, or an equivalent recurring research-group sequence, from the ICSI Meeting Corpus. Since our intended users are researchers who meet regularly, this dataset is closer to the type of conversations we want our application to process. However, it does not include the specific commitment and decision labels we need, so our team will have to annotate those ourselves.

We would also like to eventually test our system using recordings from our own project meetings or research lab meetings. These would give us a better idea of how our system performs in the setting we are actually building it for. However, we will not record or use any meetings without obtaining written consent from everyone involved.

Transcription and task extraction are evaluated separately. The audio pilot uses real AMI recordings and manual word references; the extraction diagnostic uses synthetic timestamped transcripts. Neither currently evaluates speaker identification.

**Current inputs:** A scored synthetic development suite is now available: 24 independent micro-meetings, 35 turns, 15 labeled obligations, and 11 negative cases. Labels and matching rules were AI-authored before inference and still need human review. The following inputs exist; generated predictions are not gold labels.

| Source/subset                   | Actual size                                             | Format and coverage                                                                 | Access                                                                                     |
| ------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| CCB transcription pilot         | 4 meetings, 12 clips, 12 minutes, 1,738 reference words | Manual AMI references; 3 development / 3 validation / 6 test clips, series-disjoint | `tests/fixtures/asr/manifest.json`; raw data local                                       |
| Synthetic development benchmark | 24 micro-meetings, 35 turns, 15 obligations             | AI-authored labels; frozen lexical matching; 3 measured baselines                   | `tests/fixtures/evaluation/development.json`                                             |
| Synthetic extraction example    | 1 meeting, 3 turns                                      | Explicit agreement, Sam's commitment with raw deadline, unaccepted suggestion       | `tests/fixtures/meeting.json`                                                            |
| AMI TS3005 manual transcripts   | 1 series, 4 meetings; 287/693/619/1,194 nonempty turns  | Timestamped corpus speakers A-D; no reviewed LabSync commitment/state labels        | Local `artifacts/ami/TS3005{a,b,c,d}.json`; reproduction in `docs/codex-integration.md` |
| AMI audio excerpt               | 1 clip, 45 seconds, TS3005a 90-135s                     | Mono 16 kHz PCM WAV; opening/agenda content, not a commitment benchmark             | `tests/fixtures/ami/TS3005a-90s-135s.wav`                                                |

See the [integration guide](../codex-integration.md) for acquisition and conversion commands and the [AMI fixture documentation](../../tests/fixtures/ami/README.md) for attribution, checksums, and audio preparation. Full corpus downloads and their generated predictions remain local and ignored by Git. Complete synthetic runs remain local under `artifacts/evaluation/`. The [human review packet](human_review.md) and [evidence snapshot](human_review_cases.json) include all 72 extraction outputs (24 inputs for each of three methods); aggregate results and failure analysis are included in this report.

### Provenance and licensing

Our measured inputs consist of AI-authored synthetic transcripts and publicly available AMI meeting data. Each source has different permissions and limitations that we need to consider before using it.

| Data source                 | Origin and licensing                                                                                                                                                                | Usage constraints                                                                                                                         |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Synthetic development suite | AI-authored by Codex on September 24, 2026; labels and matching rules frozen before inference. Human review is pending. Repository MIT license.                                     | No real or private meeting information will be included.                                                                                  |
| AMI Meeting Corpus          | Developed by the AMI Consortium and the University of Edinburgh. Signals, transcripts, and some annotations are released under CC BY 4.0.                                           | Attribution is required when using or sharing the data.                                                                                   |
| ICSI Meeting Corpus         | Collected by the International Computer Science Institute in Berkeley. Signals, transcripts, and some annotations are released under CC BY 4.0 through the University of Edinburgh. | We will confirm the dataset's distribution and usage terms before using it. Raw data will not be uploaded to our GitHub repository.       |
| Our own meetings (planned)  | Recordings collected by our team with written consent from participants.                                                                                                            | Recordings will remain private and will not be uploaded to GitHub. Participants can request that their recordings be excluded or deleted. |

Privacy is an important part of our project, especially since meeting recordings can contain personal information, unpublished research, or conversations that participants may not want shared outside their group.

Our current database schema includes a consent_given field for each meeting, which defaults to false. We also have a field for voice embeddings, which would allow the system to recognize returning speakers across meetings.

The schema fields do not by themselves implement speaker recognition or enforce participant-level consent. Since voice embeddings can be used to identify individuals, we will only create them for participants who have explicitly consented. We will also keep private recordings, transcripts, and identifying information out of our public repository.

Before using recordings from our own meetings, we will make sure participants understand how their data will be used, who will have access to it, and whether any external AI services will process their information.

### Splits

We are not training or fine-tuning our own model for this milestone. Instead, we will use our datasets to develop and evaluate the prompts and extraction rules used by our system.

Since our application is meant to track information across multiple meetings, we will split the data by meeting sequence rather than by individual transcript. This means that all meetings from the same sequence will stay together in one split.

For example, we would not want Meeting 1 from a research group in our development set and Meeting 2 from that same group in our test set. The system could already have information about the tasks and decisions from the first meeting, which would make our evaluation results less reliable.

The following allocations are planned for future sequence evaluation; they are not the inputs used in the results tables:

| Split       | Dataset                                                                                    | Purpose                                                                                                     |
| ----------- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| Development | Synthetic three-meeting sequence and AMI TS3005a-d                                         | Develop and improve our prompts and extraction rules, test specific scenarios, and identify initial errors. |
| Validation  | ICSI Bmr001-Bmr003                                                                         | Check how well our system performs on recurring research meetings and identify issues before final testing. |
| Test        | A separate ICSI meeting sequence and potentially our own meetings, if consent is obtained. | Evaluate the final version of our system on meeting sequences that were not used during development.        |

We will use the development set to make changes to our prompts and rules as we identify problems. The validation set will help us check whether those changes also work on conversations outside our initial examples.

The test set will remain separate from the development process so that our final results reflect how well the system performs on previously unseen meeting sequences.

Since we are starting with a relatively small amount of data, we will also document exactly which meetings are included in each split and avoid making broad claims about the system's performance based on only a few examples.

**Actual audio split:** TS3005a development (3 clips / 544 words), IS1008a validation (3 clips / 489 words), IS1009a and ES2004a test (6 clips / 705 words). Each clip is 60 seconds; time windows and model settings were frozen before inference. Series do not cross splits, and allocation follows AMI full-corpus-ASR membership. No model training was performed. See the [audio protocol](../../tests/fixtures/asr/README.md). These are pilot subsets, not the complete AMI partitions.

**Current extraction split status:** The new 24-case suite is development-only and does not establish sequence tracking. The tables above describe planned corpus allocations. The three-meeting synthetic sequence, validation/test membership, human-reviewed labels, and corpus split manifest remain unfinished. The synthetic suite records its development split and input IDs. The existing synthetic example contains one meeting. The AMI audio clip overlaps TS3005a and must stay in the same split. Verify ICSI chronology and continuity before treating the proposed IDs as a related sequence.

### Known limitations

There are a few limitations with our current datasets that we need to keep in mind when evaluating our system.

**Small dataset size:** We are starting with a limited number of meeting sequences. This should be enough to test specific scenarios, but it will not tell us how well our system performs across different research groups, meeting formats, or larger organizations.

**Synthetic data:** Our team-created transcripts will help us test situations such as completed tasks, changed deadlines, and unclear references. However, these conversations may be more structured than real meetings and might not capture things like interruptions, incomplete sentences, or situations we did not think to include.

**Domain mismatch:** The AMI Meeting Corpus focuses on a simulated product-design project rather than recurring academic research meetings. The ICSI corpus is closer to our intended setting, but its recordings are from the early 2000s and may not fully reflect how research teams communicate today.

**Manual annotation:** The ICSI corpus does not include all the labels we need, so our team will have to identify commitments, decisions, task owners, and updates ourselves. Some statements may be difficult to label, especially when deciding whether someone actually committed to a task or was just making a suggestion. To reduce inconsistencies, a second teammate will review the annotations, and we will document any disagreements.

**Transcript quality:** Transcription WER is now measured in the audio pilot. Speaker identification and diarization accuracy remain unevaluated. The separate extraction diagnostic assumes supplied transcripts and speaker labels, so it does not quantify propagation of ASR errors into task extraction.

**Limited coverage:** Our initial datasets will focus on English-language meetings with a relatively small number of speakers. Because of this, we cannot yet determine how well our system will perform with different languages, accents, larger meetings, or research groups from different fields.

These limitations are important to keep in mind because we do not want to assume that our system works well in every setting just because it performs well on a few selected examples. As we continue developing the application, we will use our evaluation results to identify where the system struggles and what additional data we may need.

### Data Card deliverable

This section serves as our Data Card. The synthetic benchmark now records its exact inputs, 15 obligation labels, development split, annotation/matching guide and reproducible predictions. Human review of the development labels and disagreements remains pending. Corpus labels and held-out extraction membership are future work; M2 extraction results are development-only. Real recordings and corpus outputs stay outside Git. Complete synthetic runs remain local; all 72 extraction outputs are included in the human review packet alongside summary measurements and observed failures.

#### Annotation details still to finalize

**What is labeled?** Proposed labels include commitment descriptions, owners, supported deadlines, source segment IDs, and suggestions kept separate from accepted commitments. Sequence annotations will also record links to earlier tasks and expected state after each meeting. Decisions and historical Q&A are outside the first extraction scorer unless explicitly added.

**Labeling rules (proposed):** A suggestion becomes a commitment only with evidence of acceptance. Unknown owners and missing deadlines remain unknown rather than inferred. Explicit supported completion can change a task to done; partial progress, negation, and silence cannot. Ambiguous references require review rather than an invented task link. Every accepted record or update must identify its supporting transcript segment.

**Review and disagreement resolution:** No independently reviewed gold labels exist yet. One reviewer judged every extraction output in the [human review packet](human_review.md) and noted label disagreements; a second reviewer's independent spot check covers 12 outputs. Current scores remain explicitly labeled development proxies.

**Implemented development guide:** [Fixture protocol](../../tests/fixtures/evaluation/README.md) specifies AI authorship, labels, task granularity, unknown/joint owners, minimal deadline text, one-to-one action-term matching, denominators, and known limitations. These rules were frozen before model runs; they have not been human-adjudicated.

**Annotation guide and schema location:** `src/labsync/extraction.py` contains the provisional Pydantic contract and `meeting-extraction-v2` prompt. Inputs contain project/meeting IDs and turns with IDs, speakers, millisecond timestamps, and content. Outputs contain a summary, decisions, commitments, and suggestions. Commitments preserve nullable owners and verbatim deadline text plus one or more cited quotes. Team-reviewed annotation and matching rules are not yet finalized.

## 2 Evaluation harness

### Primary audio evaluation

`src/labsync/asr_evaluation.py` prepares the frozen AMI clips/references, runs the actual CCB bridge, and scores saved predictions offline with JiWER 4.0.0. WER is total substitutions + deletions + insertions divided by total reference words within each split. Failed outputs count as deletions and are reported separately; input hashes guard against mixing runs. Real-time factor records processing time divided by audio duration.

Manual references use word-midpoint clipping and chronological ordering across speakers. Identical normalization lowercases, removes apostrophes, replaces other punctuation with spaces and collapses whitespace. Fillers remain. Overlapping speech, spelling/tokenization differences and crop boundaries can affect these pilot scores; this is not official AMI ASR scoring. See the [complete protocol](../../tests/fixtures/asr/README.md).

```bash
uv sync --locked --extra dev --extra audio --extra server
# After downloading the manifest inputs and obtaining the supplied CCB source:
uv run --no-sync python -m labsync.asr_evaluation prepare --output artifacts/asr/prepared
uv run --no-sync python -m labsync.asr_evaluation run --model tiny --output artifacts/asr/ccb-tiny-v1
uv run --no-sync python -m labsync.asr_evaluation run --model base --output artifacts/asr/ccb-base-v1
uv run --no-sync python -m labsync.asr_evaluation score --output artifacts/asr/ccb-tiny-v1
uv run --no-sync python -m labsync.asr_evaluation score --output artifacts/asr/ccb-base-v1
```

Preparation and inference require fresh directories. The test suite had 58 passing tests at this checkpoint, including six additional audio-scoring tests; after the Claude provider and shared-backend changes it has 80 passing tests. Ruff passes. Live inference completed all 24 model/clip runs. Offline tests and live quality measurements are separate evidence.

### Supplementary extraction evaluation

### Metrics and scoring

**Why do the chosen metrics reflect success?** Users need commitments to be found without invented tasks, assigned to the right people, and linked to supporting evidence. Precision/recall measures extraction coverage and correctness; owner accuracy measures attribution; duplicate counts expose repeated tasks; citation checks measure traceability. Unsupported completion and state/link metrics will apply when update predictions are implemented. A model that produces no updates cannot be credited with successful reconciliation solely because it has no false completions.

The implemented extraction metrics are recorded with numerators and denominators in the [initial results summary](results/README.md).

| Metric                                         | Implemented definition                                                                                               | Status                                                                                 |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Task precision / recall / F1 proxy             | Maximum one-to-one matches using frozen action-term alternatives; matches/predictions, matches/labels, harmonic mean | Measured on 24 synthetic development cases per baseline; semantic adjudication pending |
| Owner agreement                                | Exact label agreement among matched tasks with known gold owners; null-owner cases separate                          | Measured                                                                               |
| Deadline text agreement                        | Exact raw text agreement among matched tasks, including nulls                                                        | Measured; not semantic date accuracy                                                   |
| Duplicate proxy                                | Additional predictions compatible with already matched obligations / predicted tasks                                 | Measured                                                                               |
| Citation validity                              | Exact contiguous quote and existing source ID / all predicted citations                                              | Measured; not semantic support                                                         |
| Evidence completeness                          | Matched tasks citing all designated gold source IDs with valid quotes / matched tasks                                | Measured; alternate sufficient evidence may be penalized                               |
| Semantic evidence support                      | Human-supported items / reviewed items                                                                               | Human review pending                                                                   |
| Unsupported completion and state/link accuracy | Requires state-update predictions and reviewed sequences                                                             | Deferred: reconciliation not implemented                                               |

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

**Earlier extraction checkpoint on September 24:** 52 offline tests passed, including 15 new extraction scorer/benchmark tests; the subsequent audio checkpoint above brings the total to 58. Ruff passed. These tests validate scoring against correct and deliberately incorrect predictions, including duplicates, missing outputs, invalid citations and changed input hashes. They are distinct from the 72 actual baseline extraction runs (48 live model calls and 24 rule-based extractions). Existing dependency deprecation warnings remain; they do not alter the benchmark results.

## 3 Qualitative evaluation rubric

### Qualitative rubric

**Review protocol:** For Milestone 2, one reviewer applies this rubric to every extraction baseline output in Section 4: the 24 development inputs for each of rules, Codex, and Qwen3 8B, 72 outputs in total. The [human review packet](human_review.md) groups the three outputs for each input, shows the full extraction (commitments, decisions, suggestions, evidence), and records whether the application's evidence validation accepts each output. For each output the reviewer records how many predicted commitments and expected obligations match (one-to-one against the frozen labels, judging the action only), the five rubric scores below, and any critical error. Match counts give a human precision/recall for each method beside the proxy. The rows were drafted by an AI assistant and verified row by row by Bryan Yang, who signed the [review sheet](human_review_reviewer_a.md). Will Liu independently scores a 12-output [spot check](human_review_spot_check.md) without AI drafting and without seeing the full sheet, as a rough reliability check. A full second independent review with agreement statistics is planned for Milestone 3.

The following rubric defines the review criteria. Score 2 falls between anchors 1 and 3; score 4 is usable with minor corrections between anchors 3 and 5. Record critical errors separately so an average cannot hide an unsupported completion.

| Dimension                                | 1: poor                                                                | 3: needs substantial correction                                       | 5: high quality                                                       |
| ---------------------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Faithfulness/evidence support            | Invents commitments or unsupported changes                             | Mixes supported content with unsupported details requiring correction | Every substantive field or change is supported by the cited evidence  |
| Owner and speaker attribution            | Assigns work to the wrong person without evidence                      | Some attributions require correction or uncertainty is unclear        | All owners are supported; genuinely unknown owners remain unresolved  |
| Coverage of relevant commitments/updates | Misses most relevant commitments or updates                            | Captures the main items but misses material details or items          | Captures all relevant labeled items without duplicates                |
| Ambiguity and suggestion handling        | Treats suggestions or ambiguous speech as definite commitments/updates | Handles clear cases but mishandles some uncertainty                   | Separates suggestions and routes genuinely ambiguous cases for review |
| Clarity and usefulness                   | Output is unusable or misleading                                       | Understandable but needs substantive editing                          | Tasks are concise, actionable, and easy to verify against evidence    |

**Illustrative example, not an evaluated result:** At segment `s1`, Will says, "I will rerun the baseline by Friday." At `s2`, the advisor says, "You could try mixed precision." A good output records Will's rerun commitment with `s1` as evidence and keeps mixed precision as an unaccepted suggestion. Assigning mixed precision to Will as a confirmed task is an unsupported commitment. Converting Friday to a calendar date requires meeting-date/timezone context. Actual baseline outputs and observed failures are now linked in Section 4; this illustrative rubric example is not a completed human score.

**Review disagreements and any LLM-judge role:** No automated LLM judge produces scores. An AI assistant drafted the review rows; the human reviewer verified each one and is accountable for the result. With one full reviewer there is no adjudication step; spot-check disagreements are reported, not resolved.

## 4 Baselines and initial results

**Proposed lead:** Will; scoring: Bryan; review: Guadalupe.

### Primary baseline: CCB audio transcription

CCB's `meeting_transcriber` supplies the actual acoustic functions; `agent-sandbox` is a separate simulation framework. We use the existing Whisper tiny configuration as the baseline and preselect Whisper base as a model-size comparison through the same bridge. Both use English, word timestamps, no initial prompt, no conditioning on previous text, and no diarization or LLM cleanup. This is a configuration comparison within CCB, not an independently developed ASR system. Whisper is the open-source model; JiWER is the scoring library.

| Split                  | Clips / reference words | Tiny S/D/I    | Tiny WER | Base S/D/I   | Base WER |
| ---------------------- | ----------------------- | ------------- | -------- | ------------ | -------- |
| Development: TS3005a   | 3 / 544                 | 21 / 55 / 3   | 14.52%   | 16 / 57 / 2  | 13.79%   |
| Validation: IS1008a    | 3 / 489                 | 47 / 90 / 2   | 28.43%   | 40 / 81 / 4  | 25.56%   |
| Test: IS1009a, ES2004a | 6 / 705                 | 86 / 103 / 14 | 28.79%   | 62 / 102 / 9 | 24.54%   |

Each model completed 12/12 clips. The test result is 30 fewer word errors with base: a 4.26 percentage point absolute WER reduction, or 14.78% relative. Test real-time factors are 0.021 for tiny and 0.039 for base on this host. These are single-pass observations on only two test meetings, without a significance claim. We did not train or tune either model on these clips.

**Observed errors:** Substitutions fall from 86 to 62 on test, but deletions stay near 100. Tiny confuses `dogs` with `stocks` and `thief` with `three fanner` in ES2004a-330-390; base recovers those words but still omits other material. Both models incur spelling/tokenization penalties such as `white board` versus `whiteboard`. Fillers are often omitted. Base is not uniformly better: it worsens one development clip. Listening-based error adjudication and broader evaluation are next steps.

The [transcription results report](transcription_results.md) records per-clip results, versions, settings, timings, limitations and sources. References come from AMI manual annotations, not model-generated labels. Raw recordings, references and predictions stay local in ignored directories. This audio evaluation does not establish diarization, RAG, timestamp accuracy or downstream task accuracy.

### Supplementary baseline: task extraction

The simple baseline detects first-person promises with fixed rules. The existing Codex independent-meeting extractor uses `gpt-5.6-sol`, CLI 0.149.1 and `meeting-extraction-v2`. The external open-source reference is Qwen3 8B (Apache 2.0), a general-purpose instruction model served locally by Ollama 0.6.8 in Q4_K_M with temperature 0 and seed 42. It uses the same transcript contract and extraction instructions with JSON Schema output. An earlier run with IBM Granite Code 8B was replaced because that model is code-specialized; its saved outputs remain local and are not reported. Qwen3 8B is a single off-the-shelf reference, not a meeting-specialized or best-open-source claim. Exact model digest, sources, prompts/settings, platform and validation differences are documented in the [results summary](results/README.md).

All methods see only the current transcript and speaker labels, without stored task state or gold labels. The same 24 synthetic development cases contain 15 obligations. Labels were AI-authored and frozen before inference; human review is pending.

| Method                          | Matched / predicted / gold | Task P / R / F1 proxy | Known-owner agreement | Exact deadline text | Duplicate proxy | Citation validity | Failures |
| ------------------------------- | -------------------------- | --------------------- | --------------------- | ------------------- | --------------- | ----------------- | -------- |
| Promise rules v1                | 11 / 16 / 15               | .688 / .733 / .710    | 9/9                   | 10/11               | 2/16            | 16/16             | 0/24     |
| Codex independent extraction v2 | 13 / 14 / 15               | .929 / .867 / .897    | 12/12                 | 5/13                | 1/14            | 31/31             | 0/24     |
| Qwen3 8B                        | 14 / 15 / 15               | .933 / .933 / .933    | 12/12                 | 13/14               | 1/15            | 27/27             | 0/24     |

Correct negative-case counts are 9/11, 11/11 and 11/11, respectively. Null-owner agreement among matched tasks is 1/2, 0/1 and 0/2, separate from known owners. Mean extraction times are 5.280 s for Codex (September 24, overlapping with another run) and 5.223 s for Qwen (September 26, run alone), across 24 attempts each, including warmup and excluding audio/UI. These are observed timings, not a controlled speed comparison. Rule timings are mostly below the stored 1 ms resolution. No monetary cost was measured.

**Interpretation:** Qwen3 8B has the highest action-matching proxy on these fixtures, followed closely by Codex. The proxy does not measure faithfulness, deadline correctness, or whether the application accepts an output: two Qwen outputs fail the application's evidence validation, and Qwen keeps a retracted deadline in `correction` (see below). This does not establish held-out performance, semantic accuracy, or a general model ranking. Exact deadline-span agreement penalizes Codex's verbatim `by Friday` against the labeled `Friday`.

### Extraction results by scenario

The following descriptive slices group the saved v1 runs (rules and Codex from September 24, Qwen from September 26) after aggregate results were available. Membership is disjoint and covers all 24 development cases. Values are lexical action-matching proxies, not human-adjudicated accuracy. Counts pool obligations within each slice; no new inference or label changes were made.

| Scenario                               | Cases / gold | Method | Matched / predicted | P / R / F1 proxy      | Correct negatives |
| -------------------------------------- | ------------ | ------ | ------------------- | --------------------- | ----------------- |
| Explicit promises                      | 3 / 3        | rules  | 3 / 3               | 1.000 / 1.000 / 1.000 | N/A               |
| Explicit promises                      | 3 / 3        | codex  | 3 / 3               | 1.000 / 1.000 / 1.000 | N/A               |
| Explicit promises                      | 3 / 3        | qwen   | 3 / 3               | 1.000 / 1.000 / 1.000 | N/A               |
| Acceptance and assignment              | 4 / 4        | rules  | 1 / 2               | 0.500 / 0.250 / 0.333 | N/A               |
| Acceptance and assignment              | 4 / 4        | codex  | 4 / 4               | 1.000 / 1.000 / 1.000 | N/A               |
| Acceptance and assignment              | 4 / 4        | qwen   | 4 / 4               | 1.000 / 1.000 / 1.000 | N/A               |
| Multiple or unknown owners and actions | 4 / 6        | rules  | 5 / 5               | 1.000 / 0.833 / 0.909 | N/A               |
| Multiple or unknown owners and actions | 4 / 6        | codex  | 4 / 5               | 0.800 / 0.667 / 0.727 | N/A               |
| Multiple or unknown owners and actions | 4 / 6        | qwen   | 5 / 5               | 1.000 / 0.833 / 0.909 | N/A               |
| Repetition and deadline correction     | 2 / 2        | rules  | 2 / 4               | 0.500 / 1.000 / 0.667 | N/A               |
| Repetition and deadline correction     | 2 / 2        | codex  | 2 / 2               | 1.000 / 1.000 / 1.000 | N/A               |
| Repetition and deadline correction     | 2 / 2        | qwen   | 2 / 3               | 0.667 / 1.000 / 0.800 | N/A               |
| Negation and quoted speech             | 2 / 0        | rules  | 0 / 2               | 0.000 / N/A / 0.000   | 0/2               |
| Negation and quoted speech             | 2 / 0        | codex  | 0 / 0               | N/A / N/A / N/A       | 2/2               |
| Negation and quoted speech             | 2 / 0        | qwen   | 0 / 0               | N/A / N/A / N/A       | 2/2               |
| Other noncommitments                   | 9 / 0        | rules  | 0 / 0               | N/A / N/A / N/A       | 9/9               |
| Other noncommitments                   | 9 / 0        | codex  | 0 / 0               | N/A / N/A / N/A       | 9/9               |
| Other noncommitments                   | 9 / 0        | qwen   | 0 / 0               | N/A / N/A / N/A       | 9/9               |

All slice counts reconcile to the original totals. Precision = matched/predicted; recall = matched/gold; F1 = 2 x matched/(predicted + gold). Undefined ratios are N/A. For all-negative slices, correct-negative counts show whether the model avoided inventing tasks.

All methods match the three explicit-promise obligations. Acceptance/assignment yields 4/4 matches for Codex and Qwen and 1/4 for rules. Multiple/unknown-owner and multi-action cases expose omissions, merged work, and joint-owner annotation ambiguity. Rules produce commitments in both negation/quotation cases; Codex and Qwen in neither. In repetition/correction, rules and Qwen keep an extra, outdated Friday record. These small, post hoc slices support debugging, not a general model ranking. Task F1 does not measure deadline correctness or semantic evidence support.

Exact case membership, source hashes, and per-case counts are included in [scenario results](results/slices.md) and [saved scoring evidence](results/slice_results.json).

### Observed failures and next changes

Local reports in `artifacts/evaluation/{rules,codex,qwen}-v1/` contain expected and actual outputs and error flags for all 24 examples per method. Complete raw runs are retained locally; the [human review packet](human_review.md) preserves all 72 outputs with their transcripts. The [failure analysis](results/README.md#observed-errors-and-next-verification) separates observations from likely causes and scoring/annotation limitations.

- Rules extract negated and quoted promises, duplicate repeated commitments, keep the retracted Friday deadline after a correction, and miss cross-turn acceptance and assignment.
- Codex omits the UNKNOWN-owner commitment, merges two distinct actions, and leaves `not Friday` in a corrected deadline. Most of its eight deadline flags are the verbatim `by Friday` the prompt asks for against the annotation guide's minimal `Friday`, a mismatch between prompt and labels rather than a model error. For joint work it emits one record per owner.
- Qwen assigns the literal owner `UNKNOWN`, keeps the retracted Friday record beside the corrected Monday one, merges two actions, and often cites only one turn when acceptance spans two (four incomplete-evidence flags). Two Qwen outputs (`unknown_owner`, `assignment`) fail the application's evidence validation. The harness validates evidence only inside the Codex client, so these outputs were scored even though the product would reject them.
- Suggestions are not scored. Codex and Qwen sometimes file refusals, negations, or injected text as suggestions; Qwen records the `injection` instruction as a suggestion a user would see.

Next, reviewers should resolve joint-owner and task-granularity policies, adjudicate semantic matches and deadline equivalence, apply the application's evidence validation to every method in a separately versioned scorer, and then test a separately versioned prompt on new development examples. Do not silently tune v1 labels or matching terms to these predictions.

**Human review:** The [review log](human_review_log.md) indexes all 72 outputs with frozen labels, predicted commitments, proxy flags, and application validation. The [packet](human_review.md) supplies transcripts and complete outputs, and the [review sheet](human_review_reviewer_a.md) holds every judgment. Results from the single verified review:

| Method   | Matched / predicted / expected | Human P / R / F1      | Proxy P / R / F1      | Mean F / A / C / U / L                                              | Critical errors                  | App-rejected outputs |
| -------- | ------------------------------ | --------------------- | --------------------- | ------------------------------------------------------------------- | -------------------------------- | -------------------- |
| Rules    | 11 / 16 / 15                   | 0.688 / 0.733 / 0.710 | 0.688 / 0.733 / 0.710 | 4.42 (n=24) / 4.73 (n=11) / 4.23 (n=22) / 4.27 (n=11) / 3.08 (n=13) | 3 (07-rules, 15-rules, 18-rules) | 0                    |
| Codex    | 13 / 14 / 15                   | 0.929 / 0.867 / 0.897 | 0.929 / 0.867 / 0.897 | 4.88 (n=24) / 4.92 (n=12) / 4.71 (n=24) / 4.91 (n=11) / 4.65 (n=17) | 0                                | 0                    |
| Qwen3 8B | 14 / 15 / 15                   | 0.933 / 0.933 / 0.933 | 0.933 / 0.933 / 0.933 | 4.29 (n=24) / 4.54 (n=13) / 4.83 (n=24) / 4.09 (n=11) / 3.81 (n=21) | 1 (15-qwen)                      | 2                    |

Human action matching agrees with the proxy counts for every method. That is partly by construction, since reviewers use the same one-to-one rule, but it means the lexical proxy did not misjudge which task was found. The methods differ in quality instead: Codex has the highest rubric means and no critical errors; Qwen matches slightly more tasks but scores lower on faithfulness, ambiguity handling, and clarity, keeps one stale deadline, and has two outputs the application rejects; rules score lowest on clarity and invent commitments from negated and quoted speech. Rubric dimensions marked N/A (for example attribution when no commitment is predicted) are excluded from the means.

**Qualitative scores:** These scores come from one reviewer working from AI-drafted rows, so they carry single-reviewer bias and no agreement estimate yet. Spot-check agreement will be added to the [review log](human_review_log.md) when complete. Audio recognition is measured separately above. Diarization, RAG, unsupported completion and cross-meeting state tracking remain outside these measurements.

## 5 Weekly check-ins and blockers

**Progress made:** Implemented independent transcript extraction, AMI/CCB normalization, local audio transcription, and the web upload/results/playback flow. Added a SwiftUI prototype and PostgreSQL schema. Rechecked software tests and refreshed this report against the current branch. Bryan also reported a successful Swagger upload/results/playback smoke test on September 23.

**Top blockers or risks:** iOS backend upload integration is present in code, but a completed native build and Simulator end-to-end verification are not established in this report. Audio reproduction depends on separately supplied CCB source. Human-reviewed extraction labels remain missing, and qualitative scores come from a single AI-drafted, human-verified review; a second independent review is planned. Audio evaluation now uses manual AMI references, but needs more test meetings and listening-based error review. The scorer, three baseline runs, saved predictions and measured development proxies are now available. The specific architecture decisions from the TA check-in and final task ownership still need to be recorded.

**Planned next steps:** Expand the CCB audio pilot and review recognition errors; then human-review the 24-case extraction labels and observed errors, resolve task granularity/joint-owner/deadline policies, and expand coverage to natural meetings. Complete the prepared human-review worksheet and record the specific TA follow-up before final submission. See the [verification checklist](verification.md) for application integration checks. Raw recordings and complete inference runs remain outside Git; the submission includes synthetic scoring snapshots and flagged-output review evidence. The results summary includes measurements, observed failures and reproduction instructions.

Earlier progress is recorded in the [weekly journal](../weekly_journal.md).

### TA check-in

**Status:** Completed, as recorded in the team Word draft. Guidance covered architecture, the technology stack, and the solution approach.

**Date and attendees:** September 23, 2026 at 7 pm Eastern time; Derrick Mo, Will Liu, Guadalupe Cantera, and Bryan Yang.

**Follow-up:** The specific advice, decisions, and resulting scope changes have not yet been recorded. The team will add them before final submission; no approval of the current evaluation scope or dataset size is implied by attendance alone. The initial results in this report include runs completed after the check-in.

## 6 For group only (non-graded)

### Team members and roles

| Member            | Actual Milestone 2 contributions | Artifact or evidence                |
| ----------------- | -------------------------------- | ----------------------------------- |
| Guadalupe Cantera | Database and data research       | db                                  |
| Will Liu          | frontend + backend integration   | ios                                 |
| Bryan Yang        | backend + frontend integration   | labsync - agent-sandbox integration |

### Work plan for the next milestone with an owner for each task

The following assignments are proposed and need team confirmation.

| Next milestone task                                                                     | Proposed accountable owner           | Completion check                                                                                         |
| --------------------------------------------------------------------------------------- | ------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| Review synthetic labels and define joint-owner, task-granularity, and deadline policies | Guadalupe; independent reviewer Will | Review records and disagreements completed; any revised labels receive a new version                     |
| Extend extraction toward cross-meeting task reconciliation                              | Will                                 | A three-meeting sequence covers accepted updates, changed deadlines, negation, and tasks left open       |
| Automate scenario reporting in the harness and add semantic adjudication                | Bryan                                | Versioned results retain v1 proxies and report slice denominators and reviewed matches separately        |
| Expand natural-meeting data and freeze future held-out membership                       | Guadalupe                            | Meeting IDs, access constraints, labels, and sequence-disjoint split manifest recorded before evaluation |
| Verify native upload, results, and playback integration                                 | Will                                 | Completed native build and a documented end-to-end recording-to-results journey                          |
| Consolidate failure patterns and resulting Milestone 3 changes                          | Bryan, with team review              | Human review log, 3-5 supported failure patterns, and prioritized changes recorded                       |
| Complete a full second independent human review of extraction outputs                   | Will                                 | All outputs scored without AI drafting; per-dimension agreement and adjudicated disagreements recorded   |

Before submitting M2, the team will finish the spot check, record specific TA advice, confirm these proposed owners, and export the synchronized report as a single PDF.

### Blockers, dependencies, or risks

Initial proxy scoring and baseline comparisons run now. Semantic claims depend on human-reviewed labels and a second independent review; natural-meeting evaluation remains follow-up work. Audio reproduction requires separately supplied CCB source; native integration still needs end-to-end verification. Proposed owners and data access arrangements need team confirmation; specific TA advice still needs to be documented.

## 7 Reference

- [AMI and ICSI official distribution and license overview](https://groups.inf.ed.ac.uk/ami/).
- [AMI Meeting Corpus](https://groups.inf.ed.ac.uk/ami/corpus/).
- [ICSI Meeting Corpus](https://groups.inf.ed.ac.uk/ami/icsi/) and [ICSI license](https://groups.inf.ed.ac.uk/ami/icsi/license.shtml).
- [Project database schema](../../db/schema.sql), including meeting consent and optional voice-embedding fields.
- [Weekly journal](../weekly_journal.md).

## 8 GitHub Repository Link

https://github.com/BryanDYang/guardian-agent
