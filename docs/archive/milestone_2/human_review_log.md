# Human review log

Index and results table for the [human review packet](human_review.md): 72 outputs, the 24 development inputs for each extraction baseline. Columns are facts from saved outputs. Judgments are in the [review sheet](human_review_reviewer_a.md) and [spot check](human_review_spot_check.md).

| ID | Input | Frozen expected tasks | Predicted commitments | Proxy flags | App validation |
| --- | --- | --- | --- | --- | --- |
| 01-rules | explicit | prepare transcript fixture [owner: Sam; deadline: Friday] | I will prepare the transcript fixture by Friday. [owner: Sam; deadline: Friday] | none | accepted |
| 01-codex | explicit | prepare transcript fixture [owner: Sam; deadline: Friday] | Prepare the transcript fixture [owner: Sam; deadline: by Friday] | deadline: g1 | accepted |
| 01-qwen | explicit | prepare transcript fixture [owner: Sam; deadline: Friday] | Prepare the transcript fixture [owner: Sam; deadline: Friday] | none | accepted |
| 02-rules | contraction | rerun baseline [owner: Will; deadline: tomorrow] | I'll rerun the baseline tomorrow. [owner: Will; deadline: tomorrow] | none | accepted |
| 02-codex | contraction | rerun baseline [owner: Will; deadline: tomorrow] | Rerun the baseline [owner: Will; deadline: tomorrow] | none | accepted |
| 02-qwen | contraction | rerun baseline [owner: Will; deadline: tomorrow] | Rerun the baseline [owner: Will; deadline: tomorrow] | none | accepted |
| 03-rules | volunteer | review labels [owner: Guadalupe; deadline: null] | (none) | missed gold: g1 | accepted |
| 03-codex | volunteer | review labels [owner: Guadalupe; deadline: null] | Review the labels [owner: Guadalupe; deadline: null] | none | accepted |
| 03-qwen | volunteer | review labels [owner: Guadalupe; deadline: null] | Review the labels [owner: Guadalupe; deadline: null] | none | accepted |
| 04-rules | accepted_request | upload slides [owner: Will; deadline: Monday] | Yes, I will do that by Monday. [owner: Will; deadline: Monday] | unmatched prediction: 0; missed gold: g1 | accepted |
| 04-codex | accepted_request | upload slides [owner: Will; deadline: Monday] | Upload the slides [owner: Will; deadline: by Monday] | deadline: g1 | accepted |
| 04-qwen | accepted_request | upload slides [owner: Will; deadline: Monday] | Upload slides by Monday [owner: Will; deadline: Monday] | incomplete evidence: g1 | accepted |
| 05-rules | unaccepted_request | (none) | (none) | none | accepted |
| 05-codex | unaccepted_request | (none) | (none) | none | accepted |
| 05-qwen | unaccepted_request | (none) | (none) | none | accepted |
| 06-rules | suggestion | (none) | (none) | none | accepted |
| 06-codex | suggestion | (none) | (none) | none | accepted |
| 06-qwen | suggestion | (none) | (none) | none | accepted |
| 07-rules | negated | (none) | I will not rerun the baseline this week. [owner: Will; deadline: null] | unmatched prediction: 0 | accepted |
| 07-codex | negated | (none) | (none) | none | accepted |
| 07-qwen | negated | (none) | (none) | none | accepted |
| 08-rules | conditional | (none) | (none) | none | accepted |
| 08-codex | conditional | (none) | (none) | none | accepted |
| 08-qwen | conditional | (none) | (none) | none | accepted |
| 09-rules | completed | (none) | (none) | none | accepted |
| 09-codex | completed | (none) | (none) | none | accepted |
| 09-qwen | completed | (none) | (none) | none | accepted |
| 10-rules | partial_progress | (none) | (none) | none | accepted |
| 10-codex | partial_progress | (none) | (none) | none | accepted |
| 10-qwen | partial_progress | (none) | (none) | none | accepted |
| 11-rules | unknown_owner | send slides [owner: null; deadline: Thursday] | I will send the slides by Thursday. [owner: null; deadline: Thursday] | none | accepted |
| 11-codex | unknown_owner | send slides [owner: null; deadline: Thursday] | (none) | missed gold: g1 | accepted |
| 11-qwen | unknown_owner | send slides [owner: null; deadline: Thursday] | Send the slides [owner: UNKNOWN; deadline: Thursday] | owner: g1 | rejected: Unknown commitment owner: UNKNOWN |
| 12-rules | no_deadline | update documentation [owner: Sam; deadline: null] | I will update the documentation. [owner: Sam; deadline: null] | none | accepted |
| 12-codex | no_deadline | update documentation [owner: Sam; deadline: null] | Update the documentation [owner: Sam; deadline: null] | none | accepted |
| 12-qwen | no_deadline | update documentation [owner: Sam; deadline: null] | Update the documentation [owner: Sam; deadline: null] | none | accepted |
| 13-rules | two_owners | review schema [owner: Sam; deadline: null]; test upload endpoint [owner: Will; deadline: null] | I will review the schema. [owner: Sam; deadline: null]; I will test the upload endpoint. [owner: Will; deadline: null] | none | accepted |
| 13-codex | two_owners | review schema [owner: Sam; deadline: null]; test upload endpoint [owner: Will; deadline: null] | Review the schema [owner: Sam; deadline: null]; Test the upload endpoint [owner: Will; deadline: null] | none | accepted |
| 13-qwen | two_owners | review schema [owner: Sam; deadline: null]; test upload endpoint [owner: Will; deadline: null] | Review the schema [owner: Sam; deadline: null]; Test the upload endpoint [owner: Will; deadline: null] | none | accepted |
| 14-rules | repeat | send report [owner: Sam; deadline: Friday] | I will send the report by Friday. [owner: Sam; deadline: Friday]; To repeat, I will send the report by Friday. [owner: Sam; deadline: Friday] | unmatched prediction: 1 | accepted |
| 14-codex | repeat | send report [owner: Sam; deadline: Friday] | Send the report [owner: Sam; deadline: by Friday] | deadline: g1 | accepted |
| 14-qwen | repeat | send report [owner: Sam; deadline: Friday] | Send the report by Friday [owner: Sam; deadline: Friday] | none | accepted |
| 15-rules | correction | send report [owner: Sam; deadline: Monday] | I will send the report by Friday. [owner: Sam; deadline: Friday]; Correction: I will send the report by Monday, not Friday. [owner: Sam; deadline: Monday] | deadline: g1; incomplete evidence: g1; unmatched prediction: 1 | accepted |
| 15-codex | correction | send report [owner: Sam; deadline: Monday] | Send the report [owner: Sam; deadline: by Monday, not Friday] | deadline: g1 | accepted |
| 15-qwen | correction | send report [owner: Sam; deadline: Monday] | Send the report [owner: Sam; deadline: Friday]; Send the report [owner: Sam; deadline: Monday] | deadline: g1; incomplete evidence: g1; unmatched prediction: 1 | accepted |
| 16-rules | declined | (none) | (none) | none | accepted |
| 16-codex | declined | (none) | (none) | none | accepted |
| 16-qwen | declined | (none) | (none) | none | accepted |
| 17-rules | decision_only | (none) | (none) | none | accepted |
| 17-codex | decision_only | (none) | (none) | none | accepted |
| 17-qwen | decision_only | (none) | (none) | none | accepted |
| 18-rules | quoted_promise | (none) | The example sentence in the documentation is "I will send the report by Friday." It is not an assignment. [owner: Sam; deadline: Friday] | unmatched prediction: 0 | accepted |
| 18-codex | quoted_promise | (none) | (none) | none | accepted |
| 18-qwen | quoted_promise | (none) | (none) | none | accepted |
| 19-rules | injection | (none) | (none) | none | accepted |
| 19-codex | injection | (none) | (none) | none | accepted |
| 19-qwen | injection | (none) | (none) | none | accepted |
| 20-rules | joint | review schema [owner: null; deadline: Tuesday] | Will and I will review the schema together by Tuesday. [owner: Sam; deadline: Tuesday] | owner: g1; incomplete evidence: g1 | accepted |
| 20-codex | joint | review schema [owner: null; deadline: Tuesday] | Review the schema together [owner: Sam; deadline: by Tuesday]; Review the schema together [owner: Will; deadline: by Tuesday] | owner: g1; deadline: g1; unmatched prediction: 1 | accepted |
| 20-qwen | joint | review schema [owner: null; deadline: Tuesday] | Review the schema together [owner: Sam; deadline: Tuesday] | owner: g1; incomplete evidence: g1 | accepted |
| 21-rules | assignment | prepare demo [owner: Will; deadline: Friday] | (none) | missed gold: g1 | accepted |
| 21-codex | assignment | prepare demo [owner: Will; deadline: Friday] | Prepare the demo [owner: Will; deadline: by Friday] | deadline: g1 | accepted |
| 21-qwen | assignment | prepare demo [owner: Will; deadline: Friday] | Prepare the demo [owner: Will; deadline: Friday] | incomplete evidence: g1 | rejected: Deadline text must occur in the cited evidence |
| 22-rules | reassignment | send report [owner: Will; deadline: Friday] | Yes, I will send the report by Friday instead of Sam. [owner: Will; deadline: Friday] | none | accepted |
| 22-codex | reassignment | send report [owner: Will; deadline: Friday] | Send the report [owner: Will; deadline: by Friday] | deadline: g1 | accepted |
| 22-qwen | reassignment | send report [owner: Will; deadline: Friday] | Send the report by Friday [owner: Will; deadline: Friday] | none | accepted |
| 23-rules | two_actions | review schema [owner: Sam; deadline: Friday]; send slides [owner: Sam; deadline: Friday] | I will review the schema and send the slides by Friday. [owner: Sam; deadline: Friday] | missed gold: g2 | accepted |
| 23-codex | two_actions | review schema [owner: Sam; deadline: Friday]; send slides [owner: Sam; deadline: Friday] | Review the schema and send the slides [owner: Sam; deadline: by Friday] | deadline: g1; missed gold: g2 | accepted |
| 23-qwen | two_actions | review schema [owner: Sam; deadline: Friday]; send slides [owner: Sam; deadline: Friday] | Review the schema and send the slides [owner: Sam; deadline: Friday] | missed gold: g2 | accepted |
| 24-rules | silence | (none) | (none) | none | accepted |
| 24-codex | silence | (none) | (none) | none | accepted |
| 24-qwen | silence | (none) | (none) | none | accepted |

## Human-judged results

From the [verified review sheet](human_review_reviewer_a.md) (one reviewer). Proxy values come from Section 4 and are unchanged. Rubric means use numeric scores only; n is the number of numeric rows.

| Method | Matched / predicted / expected | Human P / R / F1 | Proxy P / R / F1 | Mean F / A / C / U / L | Critical errors | App-rejected outputs |
| --- | --- | --- | --- | --- | --- | --- |
| rules | 11 / 16 / 15 | 0.688 / 0.733 / 0.710 | 0.688 / 0.733 / 0.710 | 4.42 (n=24) / 4.73 (n=11) / 4.23 (n=22) / 4.27 (n=11) / 3.08 (n=13) | 3 (07-rules, 15-rules, 18-rules) | 0 |
| Codex | 13 / 14 / 15 | 0.929 / 0.867 / 0.897 | 0.929 / 0.867 / 0.897 | 4.88 (n=24) / 4.92 (n=12) / 4.71 (n=24) / 4.91 (n=11) / 4.65 (n=17) | 0 | 0 |
| Qwen | 14 / 15 / 15 | 0.933 / 0.933 / 0.933 | 0.933 / 0.933 / 0.933 | 4.29 (n=24) / 4.54 (n=13) / 4.83 (n=24) / 4.09 (n=11) / 3.81 (n=21) | 1 (15-qwen) | 2 |

## Spot-check agreement

Fill after the [spot check](human_review_spot_check.md) is complete, comparing its 12 rows with the same rows of the full review. Exact agreement = identical pairs / numeric pairs; within one = pairs differing by at most 1. Report N/A or missing pairs as exclusions. Twelve pairs give only a rough reliability check.

| Measure | Pairs compared | Exact agreement | Within one | Exclusions and reason |
| --- | --- | --- | --- | --- |
| Matched / predicted | | | N/A | |
| Matched / expected | | | N/A | |
| Faithfulness | | | | |
| Attribution | | | | |
| Coverage | | | | |
| Ambiguity handling | | | | |
| Clarity/usefulness | | | | |
| Critical error | | | N/A | |

Disagreements (rows and values): __________
