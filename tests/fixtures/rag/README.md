# AMI retrieval development diagnostic v1

`development.json` freezes 14 assistant-authored questions before retrieval
execution: 12 with one designated existing decision chunk, two proposed
unsupported questions. Eight positive questions are meeting-scoped; four
positive and both negative questions search the whole TS3005a-d development
project. Targets were selected from existing generated decisions and inspected
stored evidence, not independent human gold. Human review remains pending.
The questions and source targets must not be tuned after observing rankings.

This pilot isolates removal of the sparse/full-text leg and RRF from the current
hybrid path. Both versions use the same question embeddings, eligible corpus,
project/meeting scope, top K=8, live source construction, chat instructions,
empty history, requested answer model, and citation validator. Only retrieved
content/order changes. Dense baseline SQL preserves project/meeting filtering
and excludes dismissed task chunks. This is an offline service-level diagnostic,
not native UI or authorization acceptance.

## Run

From the repository root, with private configuration already set:

```sh
uv run --no-sync --env-file .env python scripts/evaluate_rag.py \
  --output artifacts/evaluation/m3-rag-YYYY-MM-DD-run-N --answers
```

The script sends questions to the configured OpenAI embedding service and
retrieved source excerpts to the configured Codex answer model. Use only an
authorized dataset/destination. Removing `--answers` skips answer generation,
but still makes external embedding requests. There is no offline claim for
that option. Never include unrelated private projects or personal recordings.
Output folders must be new so completed evidence cannot be overwritten.

The database transaction is REPEATABLE READ, READ ONLY. The script saves a
local corpus snapshot, query vectors, their hashes, dataset, source excerpts,
rankings, three network-inclusive retrieval timings per variant/question,
and optional exact model outputs/usage/timings. It alternates which retrieval
variant runs first. Model calls are serial, one per question/variant, with a 180-second deadline.
The current runner stops after three failed calls and checkpoints interruption;
completed, failed, interrupted, and not-run states stay distinct. They do
not establish P95 service latency, throughput, or repeated-run variability.
No app records, tasks, messages, jobs, or embeddings are written to the database.
Snapshot source state ends before slow model calls. A rerun against a changed
index is a new experiment; compare corpus hashes, not only project names.

## Metrics and review

- Designated-target Hit@1/3/8: number of the 12 designated decision chunks
  present at or above each cutoff, divided by 12. This is not exhaustive
  Recall@K: other transcript/summary chunks may also support the answer.
- Target MRR@8: mean reciprocal target rank, assigning zero when missing.
- Refusal behavior: whether the final citation-validated output refuses each
  proposed unsupported question. The negative labels still require review.
- Quote validity: application string-containment check. It does not establish
  semantic entailment or answer correctness.
- Latency: separate embedding batch, database round trips, source loading
  (not included in retrieval-only timings), and model+validator timings.
  These are not mobile end-to-end latencies. Timing includes external service
  and CLI overhead; model nondeterminism/cache/network effects remain.
- Usage/cost: record usage returned by the CLI. Do not equate subscription
  token usage with a published API price or invent actual marginal charges.
  Any price-based estimate needs a dated rate and explicit assumptions.

Export sanitized results into the existing walkthrough/report, with machine
outputs linked from tracked evidence. Raw corpus vectors and private settings
remain in ignored artifacts. Independent human reviewers should judge answers
against source excerpts before seeing aggregate outcomes; preserve initial
judgments and disagreements. Pending labels mean preliminary diagnostic results,
not a completed human-validated ablation or a held-out accuracy claim.

AMI TS3005a-d is development data already used for app testing. Corpus dates
in the app are import dates. This run does not evaluate chronology resolution,
ASR WER, speaker recognition, task extraction quality, completion inference,
natural-meeting generalization, or live email delivery.

## Source attribution

The underlying meeting scenario is AMI TS3005a-d, AMI Consortium / Edinburgh
CSTR, distributed under [CC BY 4.0](https://groups.inf.ed.ac.uk/ami/corpus/license.shtml).
The indexed transcripts are this application's ASR outputs and the decisions
are model-generated derivatives, not official AMI gold annotations. Preserve
this attribution with exported source excerpts. No personal test audio is in
this diagnostic. Question/label authorship is the assistant's, pending human
review; this does not replace the original corpus attribution.
