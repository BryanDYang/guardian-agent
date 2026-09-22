# Initial Codex integration

## Source audit and scope

On September 22, 2026, the local `contexts/agent-sandbox` checkout and GitHub's
non-truncated recursive main tree both resolved to
`d7b872e396df2ef05ff8391de53e0563ca698cf3`. They contain a multi-agent simulation
framework, not the meeting transcriber. Its `text_adventure_games/llm_client.py`
already supports OpenAI, Anthropic, and mock providers. It has no Gemini provider.
The existing OpenAI adapter uses Chat Completions and an API key; it does not
reuse a Codex login.

The separate audio source is now supplied in `contexts/meeting_transcriber-master`.
The [CCB audio integration guide](ccb-transcriber.md) describes the audited source,
working local Whisper-to-Codex commands, and verified audio smoke test. The
simulation code is still not part of the meeting-processing runtime.

## Runnable path

LabSync uses the supported `codex exec` interface, not an unofficial REST endpoint
or copied login tokens. It reuses the installed CLI's authentication. This initial
local prototype needs no Gemini key or separately configured OpenAI key.
It sends transcript text to Codex and consumes your account's usage.

```bash
uv sync --locked --extra dev
codex login
codex login status
uv run labsync extract tests/fixtures/meeting.json \
  --model gpt-5.6-sol --output artifacts/synthetic-codex.json
```

The first live synthetic run used Codex CLI 0.149.1 with `gpt-5.6-sol` and produced
one decision, one commitment owned by Sam with the deadline text "by Friday",
and one unaccepted calendar suggestion. The fixture is invented project data.
Subsequent runs may phrase outputs differently; this is not a deterministic
quality score. Use a fresh output path for each run.

The command invokes a fresh, ephemeral Codex session in a temporary directory,
with read-only sandboxing, user config excluded, a JSON output schema, and a
timeout. It requests text-only processing and rejects runs reporting tool use.
Read-only sandboxing is not a guarantee that tools are unavailable; this is a
local prototype, not a hardened untrusted-input service. Normal project execution
does not require weakening Codex's sandbox. A containing automation sandbox may
need to allow the CLI's local runtime and model network access.

Output contains IDs, requested model, CLI version, prompt version and hash,
normalized transcript hash, elapsed time, usage, and validated extraction.
The CLI does not report a resolved model revision in this artifact. Hashes refer
to normalized JSON/prompt strings, not original input file bytes. Codex harness
tokens are included in usage. Failed, incomplete, invalid, or uncitable outputs
are rejected; existing result files are never overwritten.

## AMI test data

Download the official manual annotation archive, which includes transcripts:

```bash
mkdir -p contexts/datasets/ami
curl --fail --location \
  https://groups.inf.ed.ac.uk/ami/AMICorpusAnnotations/ami_public_manual_1.6.2.zip \
  -o contexts/datasets/ami/ami_public_manual_1.6.2.zip
uv run labsync import-ami \
  contexts/datasets/ami/ami_public_manual_1.6.2.zip \
  --meeting TS3005a --output artifacts/ami/TS3005a.json
uv run labsync extract artifacts/ami/TS3005a.json \
  --model gpt-5.6-sol --output artifacts/ami/TS3005a-codex.json --timeout 240
```

Repeat import with `TS3005b`, `TS3005c`, and `TS3005d` for the full series.
The importer reads only `segments/` and `words/`, preserving source segment IDs
and timestamps in milliseconds. It joins word tokens with spaces, excludes
non-word markers, skips empty segments, and sorts turns chronologically. Speaker
labels A-D remain corpus labels; no real-person identity is inferred. Evaluation
summaries, decisions, and dialogue acts are never included in inference inputs.

The initial TS3005a live run processed 287 segments in 48.241 seconds and returned
2 decisions, 3 commitments, and 4 suggestions. All cited quotes and speaker labels
passed validation. These are model predictions, not gold labels. The model used
"In the meantime" as raw deadline text; this must not become a calendar date
without review. The remaining imported meetings have 693 (b), 619 (c), and 1,194
(d) nonempty transcript segments and have not yet been sent for extraction.

Archive inspection confirmed abstractive summaries, extractive summaries,
dialogue acts, and manual decision files for all four TS3005 meetings. ES2002 has
manual decision files for a/d only. A missing annotation file is not a negative
decision label and must not be scored as evidence that no decision occurred.
AMI decisions still need mapping/review against our commitment schema before
they can serve as evaluation labels. Split data by series, not random turns.

Attribution: AMI Meeting Corpus, AMI Consortium / Edinburgh CSTR, manual
annotations v1.6.2. Source and [download documentation](https://groups.inf.ed.ac.uk/ami/download/);
[CC BY 4.0 license](https://groups.inf.ed.ac.uk/ami/corpus/license.shtml).
The imported JSON is an adapted representation using the transformations above.
Downloaded corpora and outputs are ignored by Git.

ICSI remains a follow-up source, not an imported or labeled dataset in this
change. Its [download page](https://groups.inf.ed.ac.uk/ami/icsi/download/)
distinguishes core transcripts/dialogue acts from contributed annotations that
also include summarization and other layers. Review those before assuming all
useful labels are absent. It is also released under
[CC BY 4.0](https://groups.inf.ed.ac.uk/ami/icsi/license.shtml).
Verify meeting dates, participants, and annotation coverage before choosing a
three-meeting longitudinal sequence. Our own recordings still require the
written consent described in the team notes before recording.

## Database handoff

`db/schema.sql` is present; database connectivity and migration execution were
not verified by this work. `src/labsync/extraction.py` defines the provisional
input/output contract. It preserves `start_time_ms`, `end_time_ms`, and `content`
for mapping to `transcripts`, and source IDs for mapping citations to database
UUIDs. AMI IDs are external IDs, not database UUIDs.

Before adding persistence, agree with Guadalupe on the source-ID to UUID map,
meeting/project ownership, and speaker-to-attendee mapping. Commitments should
enter the existing task review flow as pending proposals. Preserve raw deadline
text for review before converting it to `tasks.due_date`. Generic suggestions
cannot automatically become `advisor_suggestion` without a verified advisor role.
The current schema holds one task/decision evidence reference while extraction
can cite several turns; agree how to preserve all supporting citations.

The validator checks schema, unique input IDs, time bounds, speaker membership,
and exact quote existence. It does not prove semantic support, correct ownership,
or extraction completeness. The uncited summary needs separate review. There
is no cross-meeting reconciliation, scored audio evaluation, database write, or
UI/API binding. Audio transcription is available through the CCB bridge.

## Verification

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest
```

Tests exercise installed CLI subprocesses with a fake Codex executable, invalid
citations/owners/input, timeouts, incomplete output, and AMI segment import.
They run offline. Live synthetic and public AMI runs are integration checks,
not benchmark metrics.

References: [CCB repository](https://github.com/ccb/agent-sandbox),
[Codex non-interactive mode and authentication](https://learn.chatgpt.com/docs/non-interactive-mode).
