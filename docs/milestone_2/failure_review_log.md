# Human failure review log

Prepared from saved v1 outputs. All reviewer and final-classification fields are intentionally blank. Suggested categories below are AI-prepared review prompts, not human findings. Read the [full transcripts and evidence](failure_review.md) before deciding. There are 28 model/case outputs from 14 unique inputs; do not report this as 28 independently observed meetings or completed human reviews.

| ID / method / case | Frozen expected tasks | Actual predicted tasks | Candidate issue to inspect | Reviewer / date | Human classification and evidence |
| --- | --- | --- | --- | --- | --- |
| FR01 / rules / volunteer | review labels [owner: Guadalupe; deadline: null] | (none) | Model/scorer candidate: acceptance or action resolution | | |
| FR02 / rules / accepted_request | upload slides [owner: Will; deadline: Monday] | Yes, I will do that by Monday. [owner: Will; deadline: Monday] | Model/scorer candidate: acceptance or action resolution | | |
| FR03 / rules / negated | (none) | I will not rerun the baseline this week. [owner: Will; deadline: null] | Model candidate: unsupported commitment | | |
| FR04 / rules / repeat | send report [owner: Sam; deadline: Friday] | I will send the report by Friday. [owner: Sam; deadline: Friday]; To repeat, I will send the report by Friday. [owner: Sam; deadline: Friday] | Model candidate: duplicates, correction, or missing evidence | | |
| FR05 / rules / correction | send report [owner: Sam; deadline: Monday] | I will send the report by Friday. [owner: Sam; deadline: Friday]; Correction: I will send the report by Monday, not Friday. [owner: Sam; deadline: Monday] | Model candidate: duplicates, correction, or missing evidence | | |
| FR06 / rules / quoted_promise | (none) | The example sentence in the documentation is "I will send the report by Friday." It is not an assignment. [owner: Sam; deadline: Friday] | Model candidate: unsupported commitment | | |
| FR07 / rules / joint | review schema [owner: null; deadline: Tuesday] | Will and I will review the schema together by Tuesday. [owner: Sam; deadline: Tuesday] | Label/contract ambiguity: joint ownership; inspect any duplicate and deadline flags | | |
| FR08 / rules / assignment | prepare demo [owner: Will; deadline: Friday] | (none) | Model/scorer candidate: acceptance or action resolution | | |
| FR09 / rules / two_actions | review schema [owner: Sam; deadline: Friday]; send slides [owner: Sam; deadline: Friday] | I will review the schema and send the slides by Friday. [owner: Sam; deadline: Friday] | Model/contract candidate: owner handling or missing/merged obligations | | |
| FR10 / codex / explicit | prepare transcript fixture [owner: Sam; deadline: Friday] | Prepare the transcript fixture [owner: Sam; deadline: by Friday] | Scorer/representation candidate: exact span versus semantic deadline | | |
| FR11 / codex / accepted_request | upload slides [owner: Will; deadline: Monday] | Upload the slides [owner: Will; deadline: by Monday] | Scorer/representation candidate: exact span versus semantic deadline | | |
| FR12 / codex / unknown_owner | send slides [owner: null; deadline: Thursday] | (none) | Model/contract candidate: owner handling or missing/merged obligations | | |
| FR13 / codex / repeat | send report [owner: Sam; deadline: Friday] | Send the report [owner: Sam; deadline: by Friday] | Scorer/representation candidate: exact span versus semantic deadline | | |
| FR14 / codex / correction | send report [owner: Sam; deadline: Monday] | Send the report [owner: Sam; deadline: by Monday, not Friday] | Scorer/representation candidate: exact span versus semantic deadline | | |
| FR15 / codex / joint | review schema [owner: null; deadline: Tuesday] | Review the schema together [owner: Sam; deadline: by Tuesday]; Review the schema together [owner: Will; deadline: by Tuesday] | Label/contract ambiguity: joint ownership; inspect any duplicate and deadline flags | | |
| FR16 / codex / assignment | prepare demo [owner: Will; deadline: Friday] | Prepare the demo [owner: Will; deadline: by Friday] | Scorer/representation candidate: exact span versus semantic deadline | | |
| FR17 / codex / reassignment | send report [owner: Will; deadline: Friday] | Send the report [owner: Will; deadline: by Friday] | Scorer/representation candidate: exact span versus semantic deadline | | |
| FR18 / codex / two_actions | review schema [owner: Sam; deadline: Friday]; send slides [owner: Sam; deadline: Friday] | Review the schema and send the slides [owner: Sam; deadline: by Friday] | Model/contract candidate: owner handling or missing/merged obligations | | |
| FR19 / granite / explicit | prepare transcript fixture [owner: Sam; deadline: Friday] | Prepare the transcript fixture [owner: Sam; deadline: by Friday] | Scorer/representation candidate: exact span versus semantic deadline | | |
| FR20 / granite / contraction | rerun baseline [owner: Will; deadline: tomorrow] | Rerun Baseline [owner: Will; deadline: Tomorrow] | Scorer/representation candidate: exact span versus semantic deadline | | |
| FR21 / granite / accepted_request | upload slides [owner: Will; deadline: Monday] | (none) | Model/scorer candidate: acceptance or action resolution | | |
| FR22 / granite / negated | (none) | Not Rerun Baseline [owner: Will; deadline: null] | Model candidate: unsupported commitment | | |
| FR23 / granite / unknown_owner | send slides [owner: null; deadline: Thursday] | Send slides [owner: UNKNOWN; deadline: Thursday] | Model/contract candidate: owner handling or missing/merged obligations | | |
| FR24 / granite / two_owners | review schema [owner: Sam; deadline: null]; test upload endpoint [owner: Will; deadline: null] | (none) | Model/contract candidate: owner handling or missing/merged obligations | | |
| FR25 / granite / joint | review schema [owner: null; deadline: Tuesday] | Review the schema together by Tuesday [owner: Sam; deadline: null] | Label/contract ambiguity: joint ownership; inspect any duplicate and deadline flags | | |
| FR26 / granite / assignment | prepare demo [owner: Will; deadline: Friday] | Preparing the demo [owner: Will; deadline: Friday] | Scorer candidate: lexical paraphrase mismatch | | |
| FR27 / granite / reassignment | send report [owner: Will; deadline: Friday] | (none) | Model/scorer candidate: acceptance or action resolution | | |
| FR28 / granite / two_actions | review schema [owner: Sam; deadline: Friday]; send slides [owner: Sam; deadline: Friday] | Review the schema [owner: Sam; deadline: Friday] | Model/contract candidate: owner handling or missing/merged obligations | | |

## Five candidate patterns for human review

These are hypotheses from saved outputs, not completed human adjudication.

| Candidate pattern | Example review IDs | Separate model behavior from scoring | Proposed Milestone 3 change |
| --- | --- | --- | --- |
| Unsupported commitments from negation or quotations | FR03, FR06, FR22 | An exact quote can still contradict the predicted commitment | Add discourse-sensitive negative examples and retest on new development cases |
| Missed or unresolved acceptance and assignment | FR01, FR02, FR21, FR27 | Check cross-turn acceptance; do not include the known Granite paraphrase mismatch as a confirmed miss | Improve action resolution and preserve supporting turns |
| Unknown/joint owners and multiple actions | FR07, FR09, FR12, FR15, FR18, FR23-FR25, FR28 | Separate omitted obligations from the unresolved one-owner/one-task label policy | Version ownership and task-granularity contracts and labels before rerunning |
| Duplicate work and deadline corrections | FR04, FR05 | Check obsolete deadline text and evidence; a matched action alone does not prove correct reconciliation | Add within-meeting deduplication and correction tests |
| Exact-span and lexical-matching artifacts | FR10, FR13, FR14, FR19, FR20, FR26 | Compare supported equivalent deadlines and paraphrases; preserve original v1 proxy results | Add separately versioned semantic date/match adjudication with audit examples |

## Pattern summary after adjudication

| Confirmed pattern | Review IDs and count | Evidence and likely cause | Milestone 3 change | Proposed owner |
| --- | --- | --- | --- | --- |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |

## Agreement after independent scoring

Use the unchanged [reviewer A](failure_review_reviewer_a.md) and [reviewer B](failure_review_reviewer_b.md) scores. For each dimension, exact agreement = identical numeric pairs / numeric pairs; within-one agreement = pairs differing by at most one / numeric pairs. Record N/A or missing pairs as exclusions; do not silently discard them. Consensus scores must not replace independent scores.

| Dimension | Paired numeric ratings | Exact matches | Exact agreement | Within one point | Within-one agreement | Excluded pairs and reason |
| --- | --- | --- | --- | --- | --- | --- |
| Faithfulness | | | | | | |
| Attribution | | | | | | |
| Coverage | | | | | | |
| Ambiguity | | | | | | |
| Clarity/usefulness | | | | | | |

## Disagreement resolution

| Review ID | Original A / B score or classification | Supporting turns | Final decision | Adjudicator / date |
| --- | --- | --- | --- | --- |
| | | | | |
