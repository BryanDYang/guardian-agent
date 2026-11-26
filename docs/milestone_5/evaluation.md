# Final evaluation and reproduction

Reviewed November 26, 2026. Run commands from the repository root. This guide owns
reproduction of the report's dated baseline results. New model inference is
stochastic and must be reported as a new run, not an exact historical replication.

## Minimal runnable example from a fresh checkout

Python 3.12 and uv are required. This path needs no accounts, database, private
recordings, model download, or external transcriber. It generates representative
structured task outputs and a score report; it does not run the native audio app.

```bash
git clone https://github.com/BryanDYang/guardian-agent.git
cd guardian-agent
uv sync --locked --extra dev --extra server
uv run --locked --no-sync labsync status --json
uv run --locked --no-sync python -m labsync.evaluation run --method rules \
  --directory artifacts/final-review/rules
uv run --locked --no-sync python -m labsync.evaluation score \
  --directory artifacts/final-review/rules
```

Use a new output directory for each inference run. Inspect the generated per-case
JSON and `scores.json`. For the full recording-to-app path, follow the
[README quick-start](../../README.md#option-b-run-your-own-backend-end-to-end).
It requires Apple Silicon for MLX, Xcode for the native app, your own provider
credentials and database, and the [separately supplied acoustic dependency](../reference/ccb-transcriber.md).
The native app rehearsal is not a fresh-clone or cold-download audio test.

## Baseline results and evidence

- **Extraction, October 26:** 24 synthetic development cases. Codex precision
  0.929, recall 0.867, F1 0.897; rules 0.688, 0.733, 0.710. These are lexical
  action-matching proxies against AI-authored labels, not semantic accuracy.
  [Inputs](../../tests/fixtures/evaluation/development.json),
  [predictions and scores](../evidence/m4_2026-10-26/extraction.json).
- **Frozen-source answers:** 14 questions, two retrieval variants, 28 calls.
  Bryan's review: 25 Supported, 1 Partly Supported, 2 Unsupported. Supported
  includes appropriate refusals; the 25/28 count is not a pure answer-accuracy
  metric. [Answers](../evidence/m4_2026-10-26/rag_answers.json),
  [sources/retrieval](../evidence/rag_2026-10-21.json),
  [human judgments](../archive/milestone_4/human_review.md).
- **Red-team, November 5:** 8 bounded synthetic chat checks with no recorded
  check errors. [Inputs, outputs, and checks](../evidence/ai_2026-11-05/redteam.json).
  This does not establish attack resistance or cross-tenant authorization.
- **ASR pilot:** 12 one-minute AMI clips, development/validation/test series
  separated. On the 6-clip test split with 705 reference words, tiny WER 28.79%
  and base WER 24.54%. These use local OpenAI Whisper, not MLX timings.
  [Protocol and commands](../../tests/fixtures/asr/README.md),
  [measured results](../archive/milestone_2/transcription_results.md).
- **Latency, October 26:** 3 trials per workload. Medians: 45-second local
  audio-to-extraction 8.33 s, frozen-source supported chat 4.43 s, unsupported
  chat 4.54 s. Excludes mobile upload, auth, DB publication, indexing, and live
  retrieval. [Raw runs](../evidence/m4_2026-10-26/workloads.json),
  [statistics and historical price assumptions](../evidence/m4_2026-10-26/summary.json).
  Estimated API-equivalent costs were $0.0715, $0.0366, $0.0150 respectively;
  they are historical estimates, not current prices or observed invoices.
- **Native acceptance, November 26:** reviewed speaker names, dated task evidence,
  manual approval, To-do, actual inbox arrival, and cited answer-to-audio navigation
  passed on meeting #3. This is a functional example, not an accuracy benchmark
  or proof of automatic approval. [Execution record](../evidence/demo_walkthrough.md#november-26-group-demo-simulator-rehearsal).

## Recompute the extraction comparison from saved predictions

This uses the production scorer and verifies the fixture/input hashes. It makes
no model calls. Keep historical evidence unchanged; reconstructed files go into
ignored artifacts. Run once with this fresh output directory:

```bash
uv run --locked --no-sync python - <<'PYCODE'
import json
from pathlib import Path
from labsync.evaluation import load_suite, score, markdown
packet = json.loads(Path('docs/evidence/m4_2026-10-26/extraction.json').read_text())
suite = load_suite(Path(packet['fixture']))
for method, saved in packet['runs'].items():
    directory = Path('artifacts/final-review/saved') / method
    directory.mkdir(parents=True, exist_ok=False)
    (directory / 'run.json').write_text(json.dumps(saved['run']))
    for output in saved['outputs']:
        (directory / (output['case_id'] + '.json')).write_text(json.dumps(output))
    report = score(suite, directory)
    (directory / 'scores.json').write_text(json.dumps(report, indent=2))
    print(markdown(report))
PYCODE
```

## Recompute review counts, red-team checks, and latency statistics

This recomputes aggregates from the stored judgments and runs. It does not
perform new human annotation, new attacks, or inference. Cost assumptions are
read from the dated summary rather than presented as new prices.

```bash
uv run --locked --no-sync python - <<'PYCODE'
import json, re, statistics
from collections import Counter
from pathlib import Path
review = Path('docs/archive/milestone_4/human_review.md').read_text()
print('Human review:', dict(Counter(re.findall(r'Correctness:\*\* (Supported|Partly supported|Unsupported|Uncertain)\.', review))))
red = json.loads(Path('docs/evidence/ai_2026-11-05/redteam.json').read_text())
print('Red-team:', sum(not row['errors'] for row in red['cases']), '/', len(red['cases']))
work = json.loads(Path('docs/evidence/m4_2026-10-26/workloads.json').read_text())
for name in ['recording-to-results', 'supported-chat', 'unsupported-chat']:
    seconds = [r['seconds'] for r in work['runs'] if r['workload'] == name and r['status'] == 'completed']
    print(name, 'n=', len(seconds), 'median seconds=', round(statistics.median(seconds), 3))
print('Historical pricing:', json.loads(Path('docs/evidence/m4_2026-10-26/summary.json').read_text())['pricing'])
PYCODE
```

The 28-answer pass reuses frozen retrieval sources. For ranking metrics and a
new dense/hybrid retrieval run, see the
[retrieval protocol](../../tests/fixtures/rag/README.md) and
[read-only retrieval runner](../../scripts/evaluate_rag.py). Reconstruct the
specified corpus and use your own disposable project; live search needs matching
indexed inputs, database access, and embeddings. Frozen-source rescoring cannot
establish live retrieval performance.

## New inference and software checks

After `codex login`, rerun extraction with `--method codex --model gpt-5.6-sol`
in place of rules, choosing a fresh directory. Optional dated live procedures:

```bash
uv run --locked --no-sync python docs/evidence/m4_2026-10-26/runners/rag_answers.py \
  --output artifacts/final-live/rag_answers.json
uv run --locked --no-sync python docs/evidence/m4_2026-10-26/runners/redteam.py \
  --output artifacts/final-live/redteam.json
```

These send public/synthetic inputs to Codex. The red-team runner above is the
October 26 five-probe suite, distinct from the stored November 5 eight-check
packet. The workload runner also requires the audio dependencies and supplied
CCB source. Its old prompt and provider environment may differ from today's.

```bash
uv run --locked --no-sync ruff check src tests
uv run --locked --no-sync ruff format --check src tests
uv run --locked --no-sync pytest
```

Tests needing PostgreSQL skip unless `TEST_DATABASE_URL` points to a disposable
local database with all repository migrations. Never run the suite against the
shared team database. [CI](../../.github/workflows/ci.yml) provisions disposable
PostgreSQL, runs the full suite, and checks the frozen extraction baseline.
[Contributor instructions](../../CONTRIBUTING.md) cover local setup.

## Reproducibility limits

The runtime is pinned through `uv.lock`; model services and cached model downloads
are not immutable. Input hashes and per-run settings identify historical runs.
Private team audio, credentials, voice embeddings, and database dumps are not
public artifacts. The root transcriber file is a notice; licensed delivery of
the external snapshot remains unresolved. Full native setup needs additional
accounts and platform dependencies. The repository supplies a credential-free
representative extraction path and historical evidence without claiming that
all private data or a laptop-backed deployment can be reproduced anonymously.
