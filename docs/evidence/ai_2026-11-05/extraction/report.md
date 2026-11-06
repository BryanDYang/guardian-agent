# Extraction development results

AI-authored development labels; lexical action matching proxy; no human adjudication, held-out quality, semantic support or state scoring.

Method: codex; model: gpt-5.6-sol.
Scorer: action-terms-v1.

| Metric | Numerator / denominator | Value |
| --- | --- | --- |
| task_precision_proxy | 13/14 | 0.929 |
| task_recall_proxy | 13/15 | 0.867 |
| task_f1_proxy | 26/29 | 0.897 |
| duplicate_proxy | 1/14 | 0.071 |
| evidence_completeness | 13/13 | 1.000 |
| owner | 12/12 | 1.000 |
| unknown_owner | 0/1 | 0.000 |
| deadline | 5/13 | 0.385 |
| negative | 11/11 | 1.000 |
| citation_validity | 31/31 | 1.000 |

Failed/missing cases: 0.
Mean extraction wall time: 6.181958333333333 seconds (24 attempts, includes failures and warmup).

| Case | Expected tasks | Actual tasks | Observed errors |
| --- | --- | --- | --- |
| explicit | prepare transcript fixture | Prepare the transcript fixture | deadline: g1 |
| contraction | rerun baseline | Rerun the baseline | none under proxy |
| volunteer | review labels | Review the labels | none under proxy |
| accepted_request | upload slides | Upload the slides | deadline: g1 |
| unaccepted_request | none | none | none under proxy |
| suggestion | none | none | none under proxy |
| negated | none | none | none under proxy |
| conditional | none | none | none under proxy |
| completed | none | none | none under proxy |
| partial_progress | none | none | none under proxy |
| unknown_owner | send slides | none | missed gold: g1 |
| no_deadline | update documentation | Update the documentation | none under proxy |
| two_owners | review schema; test upload endpoint | Review the schema; Test the upload endpoint | none under proxy |
| repeat | send report | Send the report | deadline: g1 |
| correction | send report | Send the report | deadline: g1 |
| declined | none | none | none under proxy |
| decision_only | none | none | none under proxy |
| quoted_promise | none | none | none under proxy |
| injection | none | none | none under proxy |
| joint | review schema | Review the schema together with Will; Review the schema together with Sam | owner: g1; deadline: g1; unmatched prediction: 1 |
| assignment | prepare demo | Prepare the demo | deadline: g1 |
| reassignment | send report | Send the report instead of Sam | deadline: g1 |
| two_actions | review schema; send slides | Review the schema and send the slides | deadline: g1; missed gold: g2 |
| silence | none | none | none under proxy |
