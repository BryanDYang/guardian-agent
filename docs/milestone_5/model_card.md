# LabSync Model Card

Final repository documentation, November 26, 2026. Track: AI Engineering.
This card describes an application using pretrained models, not a newly trained
foundation model. Historical measurements retain their original configurations.

## Intended use

Help consenting research teams review meeting summaries, decisions, tasks,
owners, dates, and cited answers. Users inspect source quotes and audio before
accepting important assignments or changes. Do not use this system for covert
recording, performance scoring, high-stakes decisions, or proof that work occurred.

## Models and parameters

- Speech: local Whisper via the separately supplied CCB acoustic bridge. The
  November 26 demo backend uses MLX Whisper base; weights are
  `mlx-community/whisper-base-mlx`. The AMI WER pilot used local OpenAI Whisper
  tiny/base, a different backend. No paid speech-recognition API is used.
- Diarization: `pyannote/speaker-diarization-3.1`, with its gated segmentation
  dependency. Labels are acoustic clusters, not guaranteed people.
- Identity matching: `pyannote/wespeaker-voxceleb-resnet34-LM`, 256 dimensions;
  minimum cluster speech 5 seconds, cosine threshold 0.60, margin 0.10. These
  provisional thresholds are not calibrated probabilities. Human review may
  map several clusters to one participant/account.
- Text extraction and chat: defaults `codex / gpt-5.6-sol`; alternative
  `claude / claude-sonnet-4-5`. Original team recordings were processed on a
  teammate's backend; the November 26 chat rehearsal used the local Codex backend.
  A runtime health response identifies the running configuration.
- Prompts: extraction `meeting-extraction-v5`, chat `project-chat-v2`.
  Extraction artifacts store requested model, prompt/input hashes, usage, and
  timing. Codex runs are text-only, schema-constrained, ephemeral, read-only,
  and reject reported tool use. The clients do not explicitly set temperature
  or reasoning effort; provider defaults apply. Claude's output limit is 8192
  tokens. A requested model name does not pin provider-side weights.
- Embeddings: OpenAI `text-embedding-3-small`, 1536 dimensions; task-title
  similarity uses the first 384 dimensions. Transcript windows target 150 words
  with whole-turn boundaries. Hybrid retrieval fuses dense and PostgreSQL text
  ranking using RRF k=60, depth 40 per leg; chat takes 8 search hits. Source
  expansion can produce more than 8 individual source entries.
- Deadlines: calendar-day precision anchored to the stored meeting date.
  Times remain in quoted evidence. Ambiguous phrases require review.

Authoritative code: [providers](../../src/labsync/providers.py),
[prompts/schema](../../src/labsync/extraction.py),
[chat](../../src/labsync/chat.py), [voice](../../src/labsync/voice.py),
[retrieval](../../src/labsync/db/rag.py), and
[dependency lock](../../uv.lock). See the
[transcriber dependency notice](../reference/ccb-transcriber.md) for its audited hash.

## Evaluation and evidence

The [evaluation reproduction guide](evaluation.md) maps each result to inputs,
commands, evidence, and limitations. The October 26 24-case development comparison
reported extraction F1 0.897 versus rules 0.710 using lexical proxy matching.
Bryan's separate 28-answer review recorded 25 Supported, 1 Partly Supported,
and 2 Unsupported outputs; Supported includes appropriate refusals. The eight
personal-case judgments and eight November 5 synthetic red-team checks are
separate sets. None establishes population accuracy or production safety.

The November 26 simulator rehearsal verified a reviewed task, actual inbox
arrival, and a cited answer opening meeting #3 audio. It did not score automatic
speaker accuracy, run a new extraction benchmark, or validate all cross-meeting
updates. See the [execution record](../evidence/demo_walkthrough.md#november-26-group-demo-simulator-rehearsal).

## Known limitations and review

ASR errors can corrupt names, actions, or dates. One three-person recording
produced four clusters and mixed-person turns. Human-confirmed labels corrected
that recording, but do not repair every word or establish diarization accuracy.
Task duplicates, omissions, and wrong assignments remain possible. Exact quote
validation does not establish semantic entailment. Small development sets,
AI-authored labels, one selected human reviewer, changing hosted models, and
cached hardware limit generalization and repeatability. No fine-tuning or
agentic autonomous tool selection is claimed. Review this card when models,
prompts, matching rules, or evaluation evidence change.
