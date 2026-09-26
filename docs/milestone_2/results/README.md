# Initial extraction measurements - September 24-26, 2026

Supplementary task-extraction evaluation. The primary audio baseline and
split-data measurements are in the [CCB transcription report](../transcription_results.md).

These are actual runs on the same **24 synthetic development micro-meetings
(35 turns, 15 labeled obligations, 11 negative cases)**. Labels were AI-authored
before inference and have not been independently reviewed by humans. Matching
uses frozen lexical action rules, so task P/R/F1 and duplicates are **proxies**,
not adjudicated semantic accuracy or held-out performance.

| Method | Matched / predicted / gold | Task P / R / F1 proxy | Known-owner agreement | Null-owner agreement | Exact deadline text | Duplicate proxy | Valid citations | Correct negative cases |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| First-person promise rules v1 | 11 / 16 / 15 | .688 / .733 / .710 | 9/9 | 1/2 | 10/11 | 2/16 | 16/16 | 9/11 |
| Codex `gpt-5.6-sol`, prompt v2 | 13 / 14 / 15 | .929 / .867 / .897 | 12/12 | 0/1 | 5/13 | 1/14 | 31/31 | 11/11 |
| Qwen3 8B Q4_K_M, prompt v2 | 14 / 15 / 15 | .933 / .933 / .933 | 12/12 | 0/2 | 13/14 | 1/15 | 27/27 | 11/11 |

All three runs produced schema-valid outputs for 24/24 cases with no missing or
failed attempts. Owner/deadline denominators contain matched tasks only; they do
not compensate for missed tasks. Deadline agreement includes nulls. Every quote
being valid does not mean every commitment is supported. Rules emit a negated
promise as a task despite quoting the transcript exactly.

Mean extraction wall time over 24 attempts: Codex **5.280 s** (September 24),
Qwen **5.223 s** (September 26, run alone).
Times include first-call overhead/warmup, have 1 ms stored resolution, and exclude
audio and UI. The Codex run overlapped another run on the host; this is a smoke timing sample,
not a controlled speed comparison. Rule timings are below the stored resolution
for 23/24 cases, so do not use their rounded mean as a microbenchmark. No monetary
cost was measured. Token counts are retained where the runtime supplies them.

## Scenario results and human review

[Scenario slices](slices.md) report all 24 cases in six disjoint groups, with
pooled counts and explicit denominators. [Saved scoring evidence](slice_results.json)
contains the original per-case scoring snapshots and source hashes. The
[human review packet](../human_review.md), [review log](../human_review_log.md),
and one verified [review sheet](../human_review_reviewer_a.md) cover all 72 outputs
(24 inputs for each method). A 12-output independent spot check is pending.

## Systems and settings

- **Rules:** `rule_extract` in `src/labsync/evaluation.py`, matching `I will`,
  `I shall`, or `I'll`, with a small explicit-day detector. This is a simple
  baseline authored for this project, not the external reference.
- **Codex:** Existing production `codex_client.extract`, requested `gpt-5.6-sol`,
  CLI `0.149.1`, `meeting-extraction-v2`, schema-constrained output, no tools, no
  history, user configuration ignored. Generation settings use CLI/model defaults;
  no custom temperature was specified. Requested model identity is recorded; the
  client does not capture an immutable hosted model checkpoint.
- **Open-source reference:** Ollama `qwen3:8b`, 8.2B parameters, Q4_K_M,
  Ollama 0.6.8, model digest
  `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`. Qwen3 is a
  general-purpose instruction model released under Apache 2.0. It uses the same
  transcript/output contract with JSON Schema formatting, temperature 0, seed 42,
  context 4096, and maximum generation 1536 tokens, and sees the same extraction
  instructions plus a serialized output schema. Schema-constrained output means no
  separate thinking trace is produced. See the
  [official model card](https://huggingface.co/Qwen/Qwen3-8B) and
  [Ollama structured output documentation](https://github.com/ollama/ollama/blob/main/docs/capabilities/structured-outputs.mdx).
  It replaces an earlier IBM Granite Code 8B run, which was code-specialized and
  chosen only because it was already installed; those outputs remain local and are
  not reported. Qwen3 8B is not evidence of the best attainable open-source result.

Codex validates evidence before returning; Ollama saves raw structured output for
scoring. These are system-level comparisons with different validation paths, not
an isolated model ablation. Qwen's `UNKNOWN` owner (`unknown_owner`) and a deadline
missing from its cited turn (`assignment`) would fail the production evidence/owner
validator even though the JSON is valid.

## Observed errors and next verification

Local reports in `artifacts/evaluation/{rules,codex,qwen}-v1/` cover all
24 examples per baseline, retaining predictions, matches and error categories.
The submission presents the measurements above and representative findings below;
raw test artifacts remain local. These findings come from inspection of saved
outputs, not a completed human rubric exercise.

| Case | Observed result | Interpretation and next verification |
| --- | --- | --- |
| `negated` | Rules extract a task from “I will not rerun the baseline this week.” Codex emits nothing; Qwen files the sentence as a suggestion. | Regex lacks negation handling. Suggestions are unscored, so Qwen's misfiled suggestion is invisible to the proxy. |
| `quoted_promise` | Rules treat a documentation example as a promise. Both models emit none. | Regex lacks discourse context; keep this baseline fixed and test quote handling in the model pipeline. |
| `accepted_request` | Rules return “Yes, I will do that”; Codex resolves “Upload the slides” and cites both turns; Qwen resolves the task but cites only the acceptance. | Multi-turn action resolution is important; expand request/acceptance cases and check evidence completeness. |
| `unknown_owner` | Codex omits the commitment; Qwen assigns literal `UNKNOWN`, which the production validator rejects; rules preserve null. | Prompt says unknown owners must be null, not that the obligation should disappear. Verify preservation of unknown-owner tasks after a separate prompt change. |
| `two_actions` | All three methods keep both actions in one record (Codex and Qwen as a merged title, rules as the raw sentence). | Define task granularity explicitly and retest atomic action splitting. |
| `repeat`, `correction` | Rules duplicate the repeated task. Rules and Qwen keep the retracted Friday record beside Monday; Codex keeps one record but writes `by Monday, not Friday`. | Within-meeting revisions need explicit handling; add correction tests that check for stale records. |
| `joint` | Codex emits one task per owner; Qwen and rules emit a Sam-owned task. Gold expects one null-owner obligation. | Contract/annotation ambiguity: multi-owner tasks do not fit a single nullable owner cleanly. Resolve with reviewers before counting this as a semantic model failure. |
| `assignment` | Qwen's deadline `Friday` comes from the assignment turn, but its commitment cites only the acceptance turn; the production validator rejects it. | Evidence must cover every field; apply the production validator in a versioned scorer. |
| `explicit`, other deadlines | Codex commonly says `by Friday` versus gold `Friday`; correction says `by Monday, not Friday`. | Exact-span mismatches explain Codex's low deadline agreement; do not interpret 5/13 as calendar-date accuracy. Define a semantic date measure separately. |
| `injection`, `declined`, `partial_progress` | No method creates a commitment, but Qwen records the injected instruction, a refusal, and an unrequested follow-up as suggestions. | Suggestions reach users but are not scored; add suggestion checks to a later scorer version. |

The most common Codex error flag is exact deadline-span mismatch (8 matched
items), largely an annotation/representation issue. It also misses the
unknown-owner task and merges two actions. Qwen has the highest proxy F1 but two
outputs the product would reject, one stale correction record, and four
incomplete-evidence flags. The rule baseline exposes false positives from
negation/quotation and repeated predictions. These small, constructed cases
support targeted debugging, not a general ranking of models.

## Reproduce and review

See the [fixture and scoring protocol](../../../tests/fixtures/evaluation/README.md)
for inference commands, labels, matching rules and limitations. No baseline used
gold labels during inference. Run/source/suite/prompt hashes and platform/runtime
metadata are in each `run.json` and prediction record. The run revision is the
base commit; the new harness was in the working tree, identified by its source
hash. No prompt, label or matching-rule tuning was done after seeing predictions.

Offline re-scoring on the machine holding the local run artifacts:

```bash
uv run --locked --extra dev pytest tests/benchmarks/
uv run --locked python -m labsync.evaluation score \
  --directory artifacts/evaluation/rules-v1
uv run --locked python -m labsync.evaluation score \
  --directory artifacts/evaluation/codex-v1
uv run --locked python -m labsync.evaluation score \
  --directory artifacts/evaluation/qwen-v1
```

Complete inference runs remain local under ignored `artifacts/evaluation/`.
The saved scoring evidence now includes all per-case commitment predictions,
labels, flags, and counts used for this report. The human review packet also
includes every output with its source transcript. A fresh checkout can
regenerate complete inference runs using the fixture protocol.
Still required: human label/match review, two-reviewer qualitative scores, natural
meeting evaluation, held-out splits, and state/reconciliation metrics. WER, DER,
RAG faithfulness/refusal and Postgres-backed E2E journeys are separate checklist
work and are not established by this extraction benchmark.
