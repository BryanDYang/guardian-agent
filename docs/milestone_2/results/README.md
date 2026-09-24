# Initial extraction measurements - September 24, 2026

These are actual runs on the same **24 synthetic development micro-meetings
(35 turns, 15 labeled obligations, 11 negative cases)**. Labels were AI-authored
before inference and have not been independently reviewed by humans. Matching
uses frozen lexical action rules, so task P/R/F1 and duplicates are **proxies**,
not adjudicated semantic accuracy or held-out performance.

| Method | Matched / predicted / gold | Task P / R / F1 proxy | Known-owner agreement | Null-owner agreement | Exact deadline text | Duplicate proxy | Valid citations | Correct negative cases |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| First-person promise rules v1 | 11 / 16 / 15 | .688 / .733 / .710 | 9/9 | 1/2 | 10/11 | 2/16 | 16/16 | 9/11 |
| Codex `gpt-5.6-sol`, prompt v2 | 13 / 14 / 15 | .929 / .867 / .897 | 12/12 | 0/1 | 5/13 | 1/14 | 31/31 | 11/11 |
| Granite Code 8B Q4_0, prompt v2 | 9 / 11 / 15 | .818 / .600 / .692 | 7/7 | 0/2 | 6/9 | 0/11 | 21/21 | 10/11 |

All three runs produced schema-valid outputs for 24/24 cases with no missing or
failed attempts. Owner/deadline denominators contain matched tasks only; they do
not compensate for missed tasks. Deadline agreement includes nulls. Every quote
being valid does not mean every commitment is supported. Granite emits a negated
promise as a task despite quoting the transcript exactly.

Mean extraction wall time over 24 attempts: Codex **5.280 s**, Granite **5.061 s**.
Times include first-call overhead/warmup, have 1 ms stored resolution, and exclude
audio and UI. The model runs overlapped on the host; this is a smoke timing sample,
not a controlled speed comparison. Rule timings are below the stored resolution
for 23/24 cases, so do not use their rounded mean as a microbenchmark. No monetary
cost was measured. Token counts are retained where the runtime supplies them.

## Systems and settings

- **Rules:** `rule_extract` in `src/labsync/evaluation.py`, matching `I will`,
  `I shall`, or `I'll`, with a small explicit-day detector. This is a simple
  baseline authored for this project, not the external reference.
- **Codex:** Existing production `codex_client.extract`, requested `gpt-5.6-sol`,
  CLI `0.149.1`, `meeting-extraction-v2`, schema-constrained output, no tools, no
  history, user configuration ignored. Generation settings use CLI/model defaults;
  no custom temperature was specified. Requested model identity is recorded; the
  client does not capture an immutable hosted model checkpoint.
- **Open-source reference:** Installed Ollama `granite-code:8b`, 8.1B parameters,
  Q4_0, Ollama 0.6.8, model digest
  `36c3c3b9683b411ee20ba5c6c6858df83a1d7bf3b65f9fd76a073791e98a18dd`.
  IBM releases Granite Code under Apache 2.0. Its instruction-following model is
  adapted to the same transcript/output contract with JSON Schema formatting,
  temperature 0, seed 42, context 4096, and maximum generation 1536 tokens. It sees
  the same extraction instructions plus a serialized output schema. See the
  [official model card](https://huggingface.co/ibm-granite/granite-8b-code-instruct-4k)
  and [Ollama structured output documentation](https://github.com/ollama/ollama/blob/main/docs/capabilities/structured-outputs.mdx).
  It is a code-specialized model selected because it was already installed, not a
  meeting-specialized system or evidence of the best attainable open-source result.
  A general instruction model is an appropriate additional comparison next.

Codex validates evidence before returning; Ollama saves raw structured output for
scoring. These are system-level comparisons with different validation paths, not
an isolated model ablation. Granite's `UNKNOWN` owner and capitalized `Tomorrow`
would fail the production evidence/owner validator even though its JSON is valid.

## Observed errors and next verification

Local reports in `artifacts/evaluation/{rules,codex,granite}-v1/` cover all
24 examples per baseline, retaining predictions, matches and error categories.
The submission presents the measurements above and representative findings below;
raw test artifacts remain local. These findings come from inspection of saved
outputs, not a completed human rubric exercise.

| Case | Observed result | Interpretation and next verification |
| --- | --- | --- |
| `negated` | Rules and Granite extract a task from “I will not rerun the baseline this week.” Codex emits none. | Negation handling failure; add explicit negative examples in a future prompt version and verify on new cases. |
| `quoted_promise` | Rules treat a documentation example as a promise. Both models emit none. | Regex lacks discourse context; keep this baseline fixed and test quote handling in the model pipeline. |
| `accepted_request` | Rules return “Yes, I will do that”; Granite emits none; Codex resolves “Upload the slides” and cites both turns. | Multi-turn action resolution is important; expand request/acceptance cases. |
| `unknown_owner` | Codex omits the commitment; Granite assigns literal `UNKNOWN`; rules preserve null. | Prompt says unknown owners must be null, not that the obligation should disappear. Verify preservation of unknown-owner tasks after a separate prompt change. |
| `two_owners` | Granite emits no commitments, missing both labels. | Likely multi-item extraction weakness; test on more independent two-owner meetings before attributing a cause. |
| `two_actions` | Codex merges both actions into one record; Granite emits only review; rules merge both. | Define task granularity explicitly and retest atomic action splitting. |
| `repeat`, `correction` | Rules create duplicate records and retain the outdated Friday deadline; models use one record with Monday for the correction. | Single-turn detection cannot reconcile within-meeting revisions. |
| `joint` | Codex emits one task per owner; Granite and rules emit a Sam-owned task. Gold expects one null-owner obligation. | Contract/annotation ambiguity: multi-owner tasks do not fit a single nullable owner cleanly. Resolve with reviewers before counting this as a semantic model failure. |
| `explicit`, other deadlines | Codex commonly says `by Friday` versus gold `Friday`; correction says `by Monday, not Friday`. | Exact-span mismatches explain the low deadline agreement; do not interpret 5/13 as calendar-date accuracy. Define a semantic date measure separately. |
| `assignment` | Granite says “Preparing the demo”; frozen matcher expects prefix `prepare` or `create`, so the task is unmatched. | Known scorer false negative. Preserve v1 scores; human-adjudicate paraphrases or publish a separately versioned matcher before rerunning comparisons. |

The most common Codex error flag is exact deadline-span mismatch (8 matched
items), largely an annotation/representation issue. It also misses the
unknown-owner task and merges two actions. Granite has six unmatched labels under
the proxy, including the known lexical false negative. The rule baseline exposes
false positives from negation/quotation and repeated predictions. These small,
constructed cases support targeted debugging, not a general ranking of models.

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
  --directory artifacts/evaluation/granite-v1
```

Raw predictions and generated reports are retained locally under ignored
`artifacts/evaluation/` and are not part of the submission. A fresh checkout can
regenerate them using the fixture protocol.
Still required: human label/match review, two-reviewer qualitative scores, natural
meeting evaluation, held-out splits, and state/reconciliation metrics. WER, DER,
RAG faithfulness/refusal and Postgres-backed E2E journeys are separate checklist
work and are not established by this extraction benchmark.
