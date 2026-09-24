# CCB transcription baseline protocol

`manifest.json` freezes 12 one-minute windows (90-150, 210-270, 330-390 seconds)
from four AMI Mix-Headset recordings before running either system. Selection was
based on availability and fixed time windows, not recognition results. This is a
12-minute pilot, not the full AMI benchmark. No ASR model is trained or fine-tuned.

| Local split | Series / meeting | Clips | Audio | AMI full-corpus-ASR allocation |
| --- | --- | --- | --- | --- |
| Development | TS3005 / TS3005a | 3 | 3 min | Training portion, used here only for development |
| Validation | IS1008 / IS1008a | 3 | 3 min | Development portion |
| Test | IS1009 / IS1009a, ES2004 / ES2004a | 6 | 6 min | Test portion |

All meetings in each series must remain in its assigned split. TS3005 was already
used for integration, so it cannot be held-out evaluation. The other recordings
were newly acquired for this pilot. Both model configurations and scoring rules
were fixed before inference; no test-result-driven tuning or model selection was
performed. The test set is held out from our local development, not proven absent
from Whisper's pretraining data. Related clips are not independent samples, and
only two test meetings do not support significance or broad generalization claims.

Sources: [AMI partition definitions](https://groups.inf.ed.ac.uk/ami/corpus/datasets.shtml),
[annotations](https://groups.inf.ed.ac.uk/ami/corpus/annotation.shtml),
[license](https://groups.inf.ed.ac.uk/ami/corpus/license.shtml).
AMI Consortium / Edinburgh CSTR, CC BY 4.0. Download URLs are in the manifest.
The preparation crops recordings and derives reference text from manual
annotation archive v1.6.2; raw audio and derived references remain local.

## What is being compared

Both configurations run the actual `labsync.ccb.transcribe` bridge, which calls
CCB's supplied `load_whisper_model` and `transcribe_audio` functions unchanged.
The baseline is multilingual Whisper `tiny`, already used for our integration
smoke. The comparison changes only that model selection to multilingual `base`.
This is a model-size/configuration comparison within CCB, not CCB versus a new
independent transcription product. Whisper is the open-source transcription
component; JiWER 4.0.0 is the scorer, not a competing baseline.

Use the supplied `contexts/meeting_transcriber-master` source. `agent-sandbox` is
a separate simulation repository and is not the meeting audio runtime. The CCB
script has no verified upstream commit/license in the supplied archive; it stays
local. Its SHA-256 is captured per run, along with the bridge and runner hashes.

Settings: English, word timestamps enabled, no initial prompt, no conditioning
on previous text, no diarization or LLM cleanup. The bridge normalizes to mono
16 kHz WAV. The runner seeds Python/NumPy/PyTorch with 42 and sets four PyTorch
threads. Other decoding parameters use the installed Whisper defaults. Local
runs use CPU/FP32. Package versions, model weight URL including its expected
SHA-256, dataset hash, source hashes, timestamps and platform are retained.
Whisper verifies the weights against the URL's checksum when loading them.

## References and scoring

For each clip, read the four speaker word XML files, excluding punctuation-only
and non-word elements and words without timestamps. Keep a word when its temporal
midpoint falls in the half-open clip interval. Sort by word start time, breaking
ties by speaker and source index, and concatenate. This includes simultaneous
speakers in one chronological word stream. It can penalize different legitimate
orderings of overlapping speech, and a crop can cut a word at its boundary.
This is a transparent pilot protocol, not official AMI ASR scoring.

Apply the same normalization to reference and hypothesis: lowercase; canonicalize
and remove apostrophes; replace other punctuation with spaces; collapse whitespace.
Preserve fillers and lexical numbers. No spelling corrections, synonym matching,
number expansion or output-dependent reference edits are applied.

[JiWER](https://jitsi.github.io/jiwer/usage/) computes substitutions (S), deletions
(D), insertions (I), and hits. Per split, **WER = sum(S + D + I) / sum(reference
words)**. This is a word-weighted aggregate, not the average of clip percentages.
WER can exceed 100%. Failed or missing attempts use an empty hypothesis, count all
reference words as deletions, and are also reported as failures. Input mismatches
fail scoring instead of silently accepting unrelated predictions. No zero-word
references occur in the pilot; empty denominators are undefined.

Real-time factor (RTF) = total clip processing wall time / total audio duration.
Each clip time includes CCB import, normalization, model loading from cache,
inference and output writing. A separate initial model download/load is excluded
and recorded as setup time. Timings are one local pass, not repeated performance
statistics; system load and caching affect them. No WER threshold is asserted as
an acceptance gate yet.

Manual AMI references are not model-generated gold. We have not independently
listened to and re-annotated all selected clips. Diarization DER, timestamp
accuracy, task extraction, RAG, and calendar/task state are outside this test.

## Reproduction

Install the audio and development dependencies, obtain the supplied CCB source,
and download the manual annotation archive and each manifest recording to its
listed path. Existing acquisition examples are in `docs/codex-integration.md`.
For example:

```bash
uv sync --locked --extra dev --extra audio --extra server
mkdir -p artifacts/asr/data
curl --fail --location --retry 2 \
  https://groups.inf.ed.ac.uk/ami/AMICorpusMirror/amicorpus/IS1008a/audio/IS1008a.Mix-Headset.wav \
  -o artifacts/asr/data/IS1008a.Mix-Headset.wav
# Repeat for IS1009a and ES2004a using manifest URLs and paths.
# TS3005a and the manual annotation ZIP use the existing contexts/datasets/ami paths.

uv run --no-sync python -m labsync.asr_evaluation prepare \
  --output artifacts/asr/prepared
uv run --no-sync python -m labsync.asr_evaluation run --model tiny \
  --output artifacts/asr/ccb-tiny-v1
uv run --no-sync python -m labsync.asr_evaluation run --model base \
  --output artifacts/asr/ccb-base-v1
uv run --no-sync python -m labsync.asr_evaluation score \
  --output artifacts/asr/ccb-tiny-v1
uv run --no-sync python -m labsync.asr_evaluation score \
  --output artifacts/asr/ccb-base-v1
uv run --no-sync pytest tests/benchmarks/
```

Preparation and inference require fresh output directories. `--dataset` accepts
a different prepared `dataset.json` path. Scoring is offline and writes
`scores.json`, including split totals, per-clip counts, hypotheses, references and
word alignments. Unit tests use tiny synthetic XML/audio fixtures, never model
inference or private data. The submission contains the results summary; the
recordings, prepared references and raw run artifacts stay in ignored directories.
