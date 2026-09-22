# AMI audio test fixture

`TS3005a-90s-135s.wav` is actual meeting audio, not a transcript: a 45-second
excerpt of the mixed-headset recording, approximately 1.4 MB. All microphones
are mixed into one channel; it is not a single-speaker recording.

Attribution: AMI Meeting Corpus, AMI Consortium / Edinburgh Centre for Speech
Technology Research. Released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
[Corpus license](https://groups.inf.ed.ac.uk/ami/corpus/license.shtml) and
[download page](https://groups.inf.ed.ac.uk/ami/download/).
The audio was cropped from 90 to 135 seconds and converted to mono 16 kHz PCM
WAV. `manifest.json` records the original download URL, transformation, and hash.

## Run the audio test

From the repository root, with CCB's source provided separately at
`contexts/meeting_transcriber-master`:

```bash
uv sync --locked --extra dev --extra audio
uv run labsync transcribe tests/fixtures/ami/TS3005a-90s-135s.wav \
  --project-id ami-TS3005 --meeting-id TS3005a-90s-135s \
  --whisper-model tiny --output-dir artifacts/ami-audio-test
uv run labsync extract artifacts/ami-audio-test/transcript.json \
  --model gpt-5.6-sol --output artifacts/ami-audio-test/extraction.json
```

Whisper runs locally and downloads weights on first use. Extraction uses the
Codex CLI login and sends the generated transcript to Codex. Use a new output
directory for another run. These commands do not run diarization by default.
See [the integration guide](../../../docs/ccb-transcriber.md) for prerequisites.

This opening/agenda excerpt checks the pipeline; it is not a commitment benchmark.
Generated transcripts and predictions are not human labels. They remain in the
ignored `artifacts/` directory. The complete AMI recordings and annotation archive
remain in ignored `contexts/datasets/ami/`; they are not bundled with the repo.
ICSI has not yet been downloaded or incorporated.
