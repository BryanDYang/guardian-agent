# CCB transcription baseline and initial split-data results

Measured September 24, 2026 using the actual supplied CCB transcription functions
through `labsync.ccb.transcribe`. This is the primary audio baseline for Milestone 2.
The earlier [extraction results](results/README.md) measure a separate downstream
feature and remain supplementary.

Whisper `tiny` is the existing integration baseline; `base` is a preselected
model-size comparison on identical audio. Both are open-source Whisper models,
not newly trained models. JiWER is the measurement library, not a competitor.
The separate `agent-sandbox` simulation repository is not the audio transcriber.

## Frozen split and scope

| Split | Meetings | Clips / minutes | Reference words |
| --- | --- | --- | --- |
| Development | TS3005a | 3 / 3 | 544 |
| Validation | IS1008a | 3 / 3 | 489 |
| Test | IS1009a, ES2004a | 6 / 6 | 705 |

Every clip covers 90-150, 210-270, or 330-390 seconds of its meeting. All windows,
model configurations, and scoring rules were fixed before inference. Meeting
series do not cross splits. The allocation follows the published AMI
[full-corpus-ASR partition](https://groups.inf.ed.ac.uk/ami/corpus/datasets.shtml):
its training portion is used only for our development checks, its development
portion for validation, and its test portion for this initial test. No training
or fine-tuning was performed. Test data was held out from our local development;
we cannot establish whether it was absent from pretrained Whisper training data.

## Measured results

WER = (substitutions + deletions + insertions) / reference words, aggregated
by word count within each split. Lower is better. RTF is total processing wall
time divided by audio duration.

| Split | CCB model | S | D | I | Errors / reference words | WER | RTF | Failed clips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | Whisper tiny | 21 | 55 | 3 | 79/544 | 14.52% | 0.033 | 0/3 |
| development | Whisper base | 16 | 57 | 2 | 75/544 | 13.79% | 0.046 | 0/3 |
| validation | Whisper tiny | 47 | 90 | 2 | 139/489 | 28.43% | 0.024 | 0/3 |
| validation | Whisper base | 40 | 81 | 4 | 125/489 | 25.56% | 0.039 | 0/3 |
| test | Whisper tiny | 86 | 103 | 14 | 203/705 | 28.79% | 0.021 | 0/6 |
| test | Whisper base | 62 | 102 | 9 | 173/705 | 24.54% | 0.039 | 0/6 |

**Initial finding:** On the six test clips, `base` reduces WER from 28.79% to
24.54%, or 30 fewer errors out of 705 reference words. That is a 4.26 percentage
point absolute reduction and 14.78% relative error reduction. This is an observed
difference in a small pilot, not a statistically established general improvement.
The test set contains only two meetings; clips from a meeting are correlated.
We do not report a significance test or treat the 705 words as independent trials.

Both configurations complete all 12 clips. Test errors are dominated by deletions:
103 for `tiny`, 102 for `base`. The improvement mostly comes from fewer
substitutions (86 to 62), not recovery of omitted words. Audio recognition remains
imperfect and downstream task extraction should not assume the transcript is exact.

## Per-clip inspection

| Clip | Split | Reference words | Tiny WER | Base WER |
| --- | --- | --- | --- | --- |
| TS3005a-90-150 | development | 180 | 14.44% | 13.33% |
| TS3005a-210-270 | development | 172 | 11.05% | 13.37% |
| TS3005a-330-390 | development | 192 | 17.71% | 14.58% |
| IS1008a-90-150 | validation | 135 | 30.37% | 29.63% |
| IS1008a-210-270 | validation | 178 | 32.58% | 26.40% |
| IS1008a-330-390 | validation | 176 | 22.73% | 21.59% |
| IS1009a-90-150 | test | 146 | 19.86% | 19.18% |
| IS1009a-210-270 | test | 108 | 36.11% | 25.93% |
| IS1009a-330-390 | test | 106 | 33.96% | 30.19% |
| ES2004a-90-150 | test | 144 | 18.06% | 17.36% |
| ES2004a-210-270 | test | 41 | 29.27% | 24.39% |
| ES2004a-330-390 | test | 160 | 38.12% | 31.25% |

Representative observed errors from saved word alignments:

| Clip | Observation | Interpretation / next verification |
| --- | --- | --- |
| IS1009a-210-270 | Reference `three` becomes `through` with tiny; base recovers it. | A lexical substitution improves with the larger model. Verify across more meetings. |
| ES2004a-330-390 | Tiny renders `dogs` as `stocks` and `thief` as `three fanner`; base recovers both. | Some content-word recognition improves, but base still deletes 31 reference words in this clip. |
| IS1009a-210-270 | Both output `whiteboard` for reference `white board`, and `favorite` for `favourite`. | Tokenization/spelling policy contributes to WER. Preserve these frozen results; evaluate any alternative normalization under a separately versioned protocol. |
| Several clips | Fillers such as `mm hmm` are omitted. | Verbatim AMI references preserve disfluencies. Some deletions are readability choices, while others omit meaningful content. Listening and categorization are follow-up work. |
| TS3005a-210-270 | Base has 13.37% WER versus tiny at 11.05%. | Bigger is not uniformly better; this development clip has more deletions with base. |

Possible overlap, low-volume speech, and crop-boundary effects are hypotheses,
not confirmed causes. We inspected textual alignments; we did not independently
listen to and re-annotate all selected audio. Do not describe this as a completed
two-human-reviewer qualitative exercise.

## Protocol and reproducibility

- References: AMI manual word annotations v1.6.2; retain timed words whose midpoint
  is inside the clip, sort by start time across speakers, exclude punctuation and
  non-word elements. This chronological serialization can penalize different
  orders of overlapping speech; it is not official AMI ASR scoring.
- Normalization: lowercase, remove apostrophes, replace other punctuation with
  spaces, collapse whitespace. Keep fillers, lexical numbers, and spelling
  differences. Apply exactly the same transformation to references and hypotheses.
- CCB settings: local OpenAI Whisper, English, word timestamps, no initial prompt,
  `condition_on_previous_text=False`, no diarization, no LLM cleanup. Existing
  bridge converts audio to mono 16 kHz. Python/NumPy/PyTorch seed 42, four threads.
- Runtime: `openai-whisper==20250625`, `torch==2.14.0`, `jiwer==4.0.0`,
  macOS 27 arm64, CPU/FP32. Models ran sequentially. Timings include per-clip
  normalization, cached model loading, inference and writing, excluding the
  separately recorded first model download/load. These are single-pass timings,
  affected by caching and other host work, not a repeated speed benchmark.
- Provenance: manifests and annotation protocol are versioned in the repo.
  Local run records contain dataset/audio/source hashes and model weight URLs
  with checksums. The CCB script hash is
  `c1f1a342ecf5924d9d92ee9791790ab90d98beef5a0a61377b552235ba1c0fa3`.
- Raw recordings, references, predictions and scored alignments remain local in
  ignored `artifacts/asr/` and `contexts/datasets/ami/`. The submission presents
  this summary, not the raw test artifacts.

See the [frozen manifest and complete reproduction protocol](../../tests/fixtures/asr/README.md)
and `python -m labsync.asr_evaluation --help`. The scorer is offline; actual model
runs are separate. Scorer tests cover known edit counts, normalization, midpoint
selection, split leakage, missing predictions, changed inputs and audio cropping.

Remaining scope: more test meetings, listening-based error adjudication, and any
separately versioned normalization experiments. DER requires an actual diarization
run and speaker-time references; JiWER does not supply it. RAG, timestamp accuracy,
and full application E2E behavior are not measured by this transcription pilot.

Sources: [JiWER scoring documentation](https://jitsi.github.io/jiwer/usage/),
[Whisper model/source and MIT license](https://github.com/openai/whisper),
[AMI annotations](https://groups.inf.ed.ac.uk/ami/corpus/annotation.shtml),
[AMI license](https://groups.inf.ed.ac.uk/ami/corpus/license.shtml).
Audio and annotations: AMI Consortium / Edinburgh CSTR, CC BY 4.0; cropped audio
and normalized reference text are derived representations.
