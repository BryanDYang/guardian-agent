# Start here

**Your next step:** run [Clip A: manual approval to captured follow-up](milestone_3/follow_through.md#a-manual-approval-to-captured-follow-up).
Record one clear commitment, upload it to a separate test project, connect your
speaker/account, and record the observed result. You do not need to read the
technical references first.

After that, use the [Milestone 3 roadmap](milestone_3/roadmap.md) to choose the
next task. The [weekly journal](weekly_journal.md) records progress and contains
the Week 8 group-message draft. Each document below has one responsibility.

| Question | Authoritative document |
| --- | --- |
| How do I run the app? | [Root README](../README.md) |
| How is everything connected, and where do I debug? | [Architecture, code-review tour, and source cleanup plan](architecture.md) |
| What remains for Milestone 3? | [Roadmap, scope, and acceptance](milestone_3/roadmap.md) |
| How do I test task email and automatic approval? | [Follow-through setup, dated recording scripts, and result log](milestone_3/follow_through.md) |
| What actually happened or passed? | [Weekly journal](weekly_journal.md) for progress; [native walkthrough](evidence/demo_walkthrough.md) for observed steps/evidence |
| What will we submit? | [Milestone 3 report draft](milestone_3/submission_draft.md), including cards and results; its draft prose does not supersede acceptance evidence |
| How do I operate/recover the backend? | [Shared-backend guide](reference/shared_backend.md) |
| How do I contribute/run checks? | [Contributing](../CONTRIBUTING.md) and [CI](../.github/workflows/ci.yml) |

## Supporting references

[Transcriber integration](reference/ccb-transcriber.md), [model integration](reference/codex-integration.md),
and [upstream provenance](reference/upstream.md) explain specific dependencies. The
[implementation checklist](archive/checklist.md) is a code inventory, not a second current
roadmap or proof of acceptance. Use the roadmap to decide what to do next.

[Design writeups](archive/writeups/README.md) and `archive/` preserve earlier rationale,
proposals, and milestone artifacts. They are historical references, not current
implementation specifications. Read them only when tracing a decision or its origin.
Historical migration comments may still use the original `docs/writeups/` paths;
those documents are preserved under `docs/archive/writeups/`. Migration history
has not been rewritten to change comments.

## Repository boundaries

- `src/labsync/`: Python API, SQL access, pipeline/workers, models, and evaluation.
- `ios/MeetingApp/`: native app and client-side cache/networking.
- `supabase/migrations/`: current schema changes. `db/schema.sql` is historical.
- `tests/`: versioned tests/fixtures; `scripts/`: setup/check/debug commands.
- `contexts/`: ignored local references, course materials, datasets, and the
  external transcriber dependency. A fresh clone does not contain them.
- `artifacts/`: ignored recordings, processing logs, and run outputs.
- `.env`, `.venv/`, model caches: private configuration/generated dependencies.
- Root `meeting_transcriber.py` is currently an untracked local copy; the normal
  runtime source is `contexts/meeting_transcriber-master`. Preserve provenance
  and check local use before deleting either.

## Maintaining documentation

Update the existing owner document instead of creating another progress/status
file. Put new results in the journal/walkthrough and link them from the roadmap
or report. Keep dated historical evidence, configuration, provenance, unresolved
failures, and proposed-vs-implemented distinctions. Group-message drafts belong
with their weekly entry. Add a new guide only for a distinct audience or workflow.
