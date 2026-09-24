# Synthetic extraction development suite v1

`development.json` contains 24 independent English micro-meetings, 35 turns,
15 labeled obligations in 13 positive cases, and 11 negative cases. All cases,
labels, and action-term alternatives were AI-authored by Codex on September 24,
2026 before baseline inference. No private conversations or external corpus text
were used. The fixtures use the repository's MIT license. Human review is pending.
This is a development diagnostic, not a held-out test or a human-reviewed gold set.

## Annotation rules

- Label an explicit accepted future obligation. Suggestions, requests awaiting
  acceptance, hypothetical possibilities, negated promises, completed work, quoted
  examples, and transcript instructions to fabricate tasks are not new obligations.
- Resolve acceptance and reassignment using the complete current micro-meeting.
  Retain only the final stated deadline in a correction and one copy of a repeated
  obligation. Split distinct actions into separate tasks.
- Use the exact speaker label for a single supported owner. Use null for UNKNOWN
  and for joint ownership that cannot fit the current single-owner contract.
  The `joint` case deliberately exposes this contract limitation; representing
  joint work as two individually owned records may be reasonable but is penalized
  by this suite's one-obligation policy. Human review must resolve this policy.
- Keep deadline labels as the minimal explicit day expression (`Friday`,
  `tomorrow`), or null. Exact-text agreement intentionally counts `by Friday` as
  different from `Friday`; it is not semantic date accuracy. Do not normalize
  relative dates without meeting-date/timezone context.
- Required evidence IDs identify the action and acceptance where both are needed.
  For repeated statements, v1 designates the first occurrence; this can penalize
  another sufficient quote. Human semantic support review is separate.
- No cross-meeting task state, decisions, suggestions, or summary quality is scored.
  Negative cases check absence of commitments, not correct suggestion extraction.

## Frozen matching protocol

`action-terms-v1` matches a prediction's title to a label when at least one
case-insensitive word-prefix alternative from every `action_terms` group appears.
Maximum-cardinality one-to-one matching determines true positives. Owner, deadline,
and evidence do not affect action matching and are measured separately. Ties are
resolved by stable input order, not by the most favorable owner/deadline score.

This is a lexical proxy: unseen paraphrases can be false negatives; a negated or
hallucinated action containing all the terms can be a false positive match.
A title that merges two actions matches at most one label. No term alternatives
were adjusted after observing baseline outputs. Human semantic adjudication is
required before describing these scores as semantic task accuracy.

Precision = matches / predictions; recall = matches / labels; F1 = twice matches /
(predictions + labels), aggregated across cases. Duplicates are unmatched
predictions compatible with an already matched label, not a semantic duplicate
measure across unrelated hallucinations. Owner agreement uses only matched tasks
with known gold owners; null-owner cases have a separate denominator. Deadline
agreement includes nulls. Evidence completeness requires all gold source IDs with
valid quotes for a matched task. Citation validity covers all predicted commitment,
decision, and suggestion references and means exact quote/source agreement only.

Zero denominators produce null (`N/A` in Markdown). Missing, failed, or invalid
schema outputs retain their labels in recall and count as failures. They contribute
no valid predictions to precision. Report failure coverage alongside every score.
The Codex production client rejects invalid evidence before returning outputs;
Ollama raw structured outputs remain available for offline citation scoring. This
validation difference is part of the measured systems and can affect failure rates.

## Reproduction

From the repository root, use the installed development environment:

```bash
uv run --locked --extra dev pytest tests/benchmarks/
uv run --locked python -m labsync.evaluation run --method rules \
  --directory artifacts/evaluation/rules-new
uv run --locked python -m labsync.evaluation score \
  --directory artifacts/evaluation/rules-new

# Live inference, using the existing Codex login and model usage:
uv run --locked python -m labsync.evaluation run --method codex \
  --model gpt-5.6-sol --directory artifacts/evaluation/codex-new

# Local open-source reference; install/pull the model before running:
ollama serve
# In another terminal:
ollama pull granite-code:8b
uv run --locked python -m labsync.evaluation run --method ollama \
  --model granite-code:8b --directory artifacts/evaluation/granite-new
```

Run `score` against each resulting directory. Live commands require fresh output
directories and save each attempt separately, including failures. Inference sees
only transcripts, never labels or matching terms. Run metadata records suite and
source hashes, UTC time, platform, model settings and identity; Codex records CLI
version, prompt hash, token usage, and elapsed time. Ollama records model digest,
quantization, runtime version, prompt hash and generation counts. Model tags can
change; compare the recorded digest before claiming an exact replication.
Scoring makes no network calls and refuses a mismatched suite/input hash.

The milestone results summary presents measured scores and observed failures.
Saved predictions and generated reports remain in ignored `artifacts/evaluation/`
for local re-scoring; they are not included in the submission. The commands above
regenerate them from the versioned fixtures and scorer.
