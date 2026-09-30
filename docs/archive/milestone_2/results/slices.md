# Extraction results by scenario

These are descriptive slices of the September 24 v1 runs, grouped after aggregate results were available. They do not change the frozen labels, action-term matcher, predictions, or aggregate scores. All 24 synthetic development inputs appear in exactly one slice. Small slice sizes and AI-authored labels limit interpretation. No human adjudication has been performed.

## Slice membership

- **Explicit promises:** `explicit`, `contraction`, `no_deadline`.
- **Acceptance and assignment:** `volunteer`, `accepted_request`, `assignment`, `reassignment`.
- **Multiple or unknown owners and actions:** `unknown_owner`, `two_owners`, `joint`, `two_actions`.
- **Repetition and deadline correction:** `repeat`, `correction`.
- **Negation and quoted speech:** `negated`, `quoted_promise`.
- **Other noncommitments:** `unaccepted_request`, `suggestion`, `conditional`, `completed`, `partial_progress`, `declined`, `decision_only`, `injection`, `silence`.

## Counts and metrics

Counts pool obligations across inputs within each slice; percentages are not averages of per-case scores. Precision = matched/predicted; recall = matched/gold; F1 = 2 × matched/(predicted + gold). Undefined denominators are N/A. In all-negative slices, use correct-negative cases and false-positive predictions rather than recall. A zero F1 when there are false positives and no gold is an arithmetic proxy, not a useful coverage measure. “Correct negative” means the system returned no commitments for a negative input.

| Scenario | Cases / gold | Method | Matched / predicted | P / R / F1 proxy | Correct negatives |
| --- | --- | --- | --- | --- | --- |
| Explicit promises | 3 / 3 | rules | 3 / 3 | 1.000 / 1.000 / 1.000 | N/A |
| Explicit promises | 3 / 3 | codex | 3 / 3 | 1.000 / 1.000 / 1.000 | N/A |
| Explicit promises | 3 / 3 | granite | 3 / 3 | 1.000 / 1.000 / 1.000 | N/A |
| Acceptance and assignment | 4 / 4 | rules | 1 / 2 | 0.500 / 0.250 / 0.333 | N/A |
| Acceptance and assignment | 4 / 4 | codex | 4 / 4 | 1.000 / 1.000 / 1.000 | N/A |
| Acceptance and assignment | 4 / 4 | granite | 1 / 2 | 0.500 / 0.250 / 0.333 | N/A |
| Multiple or unknown owners and actions | 4 / 6 | rules | 5 / 5 | 1.000 / 0.833 / 0.909 | N/A |
| Multiple or unknown owners and actions | 4 / 6 | codex | 4 / 5 | 0.800 / 0.667 / 0.727 | N/A |
| Multiple or unknown owners and actions | 4 / 6 | granite | 3 / 3 | 1.000 / 0.500 / 0.667 | N/A |
| Repetition and deadline correction | 2 / 2 | rules | 2 / 4 | 0.500 / 1.000 / 0.667 | N/A |
| Repetition and deadline correction | 2 / 2 | codex | 2 / 2 | 1.000 / 1.000 / 1.000 | N/A |
| Repetition and deadline correction | 2 / 2 | granite | 2 / 2 | 1.000 / 1.000 / 1.000 | N/A |
| Negation and quoted speech | 2 / 0 | rules | 0 / 2 | 0.000 / N/A / 0.000 | 0/2 |
| Negation and quoted speech | 2 / 0 | codex | 0 / 0 | N/A / N/A / N/A | 2/2 |
| Negation and quoted speech | 2 / 0 | granite | 0 / 1 | 0.000 / N/A / 0.000 | 1/2 |
| Other noncommitments | 9 / 0 | rules | 0 / 0 | N/A / N/A / N/A | 9/9 |
| Other noncommitments | 9 / 0 | codex | 0 / 0 | N/A / N/A / N/A | 9/9 |
| Other noncommitments | 9 / 0 | granite | 0 / 0 | N/A / N/A / N/A | 9/9 |

## Interpretation and next changes

- Rules generate false positives for negated and quoted promises. Add discourse-sensitive examples to the next model prompt and test on new development inputs; retain rules as the fixed comparator.
- Acceptance and assignment exposes cross-turn resolution and the known Granite lexical mismatch for “Preparing the demo.” Review semantic matches before attributing all unmatched labels to the model.
- Multiple/unknown owners and actions exposes missed commitments, merged actions, and the joint-owner contract ambiguity. Resolve ownership and task granularity, then version the contract and labels.
- Repetition/correction task F1 does not establish correct deadlines. Codex has exact deadline-span mismatches; rules duplicate work and retain outdated text. Review semantic dates and source support separately.

## Audit and reproduction

[slice_results.json](slice_results.json) records memberships, every pooled count, source hashes, and the complete per-case scoring snapshots used to calculate the table. For each method, sum case counts over the listed IDs, then apply the formulas above. All slice counts reconcile exactly to the saved aggregate counts, including 15 gold obligations and 11 negative cases per method. No new inference was run.

[Human failure review](../failure_review.md) covers the 28 flagged model/case outputs. The prepared packet is not evidence of completed human inspection.
