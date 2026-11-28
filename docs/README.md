# Start here

Use the [final submission roadmap](milestone_5/roadmap.md) to finish the release
and the [final report draft](milestone_5/submission_draft.md) to assemble the report.
Milestone 4 is archived with the [submitted PDF](archive/milestone_4/milestone4_submission.pdf).
The final assignment references are local files in `contexts/milestone_5/`.
That directory is Git-ignored. Canvas shows the presentation PDF due December 6 at 8:59 p.m.; other exact
assignment deadlines and the showcase session date await confirmation.

For the final presentation, use Bryan's human-review judgments only. His eight
personal-case judgments and 28 RAG judgments retain separate scopes and counts.
Historical teammate reviews remain in the archive. The group presenter guide
assigns separate speaking sections to Will, Guadalupe, and Bryan.
The [journal](weekly_journal.md) records progress and the
[walkthrough](evidence/demo_walkthrough.md) records observed execution.
Each document below has one responsibility.

For the group recording workflow, use the
[three-person meeting dialogue](archive/milestone_4/group_meeting_script.md), then the
[group tell-show-tell demo and dry run](milestone_5/group_demo_script.md).

| Question | Authoritative document |
| --- | --- |
| How do I run the app? | [Root README](../README.md) |
| How is everything connected, and where do I debug? | [Architecture, code-review tour, and source cleanup plan](architecture.md) |
| Where do we review model outputs? | [M4 answer review](archive/milestone_4/human_review.md); [M3 personal-case reviews](archive/milestone_3/human_review.md) |
| Which slides and notes do we submit/present? | [Three-slide presentation, speaker notes, faculty Q&A, and report review](milestone_5/presentation_notes.md); [output files](../output/README.md) |
| How do we divide and record the final team demo? | [Will, Guadalupe, and Bryan sections and dry run](milestone_5/group_demo_script.md) |
| Where are the final cards and reproduction steps? | [Model Card](milestone_5/model_card.md), [System Card](milestone_5/system_card.md), and [evaluation reproduction](milestone_5/evaluation.md) |
| What remains for the final submission? | [Final scope and acceptance](milestone_5/roadmap.md) |
| How do I test task email and automatic approval? | [Follow-through setup, dated recording scripts, and result log](archive/milestone_3/follow_through.md) |
| How do I record a new test result? | [Reusable result.md template](evidence/result.md), then add the completed run to the walkthrough |
| What actually happened or passed? | [Weekly journal](weekly_journal.md) for progress; [native walkthrough](evidence/demo_walkthrough.md) for observed steps/evidence |
| What do we upload for the repository assignment? | [Single linked submission PDF](../output/pdf/Guardian_Agent_Final_Repository_Submission.pdf) |
| What will we submit for the final milestone? | [Final report draft](milestone_5/submission_draft.md) |
| What did we submit for Milestone 4? | [Submitted report](archive/milestone_4/milestone4_submission.pdf) |
| What did we prepare for Milestone 3? | [Milestone 3 report draft](archive/milestone_3/submission_draft.md), including cards and results; its draft prose does not supersede acceptance evidence |
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
- Root `meeting_transcriber.py` is an explanatory dependency stub. The normal
  runtime source is `contexts/meeting_transcriber-master`; its supplied snapshot
  has unverified upstream revision/license. Historical Git contains a former copy.
  See the [dependency notice](reference/ccb-transcriber.md).

## Maintaining documentation

Update the existing owner document instead of creating another progress/status
file. Put new results in the journal/walkthrough and link them from the roadmap
or report. Keep dated historical evidence, configuration, provenance, unresolved
failures, and proposed-vs-implemented distinctions. Group-message drafts belong
with their weekly entry. Add a new guide only for a distinct audience or workflow.
