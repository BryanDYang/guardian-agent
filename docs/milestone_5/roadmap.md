# Final submission scope and acceptance

Prepared November 17, 2026 for CIS-5980 AI Engineering. This document owns the
remaining work for Milestone 5 or the final submission. The final assignment,
Canvas deadline, presentation length, required files, and any final check-in
requirements await confirmation from the course page. The work below is our
proposed release plan based on the submitted Milestone 4 report and current
implementation.

Start with the [final report draft](submission_draft.md). Preserve the
[submitted Milestone 4 PDF](../archive/milestone_4/milestone4_submission.pdf) as
the historical submission. Record new run evidence in the
[walkthrough](../evidence/demo_walkthrough.md) and progress in the
[journal](../weekly_journal.md).

## First priority for the team

### Record and verify the two meetings

The team plans to record on November 24. The shared Google Docs scripts use
November 24 and December 2, 2026 as staged meeting dates. Process two separate
files in one fresh shared project, in chronological order. Confirm all three
accounts in People, then confirm speaker mappings separately for each recording.
Review and accept the relevant first-meeting tasks before processing meeting 2.

The acceptance run should demonstrate three real voices, correct owner mappings,
quoted evidence, dates, a reviewed deadline change, a reviewed reassignment,
one actual Bryan inbox message, and a cited answer across meetings. Include a
question whose answer is absent and inspect the actual response. Record manual
corrections and failures. The November 17 text extraction runs do not establish
audio transcription or diarization quality.

Use the [three-presenter demo and dry run](../archive/milestone_4/group_demo_script.md).
Will presents the team and capture, Guadalupe presents task review and changes,
and Bryan presents email and cited answers. The proposed video is 4-5 minutes.
Confirm the final course duration before exporting. Keep the existing public
Milestone 4 video available while preparing the new team video.

### Verify the release after the latest changes

Freeze a commit and record the app, backend, model, and configuration used.
November 17 checks reported a successful signed simulator build, lint passing,
219 Python tests passing, and 196 database-dependent tests skipped because the
local database was unavailable. Run the database-backed suite against disposable
Postgres and preserve the result before describing the final suite as complete.
Rehearse the normal upload/review/email flow on that revision.

The date parser now supports spoken weekdays and calendar dates. The approval
wording gate accepts common acknowledgments and curly apostrophes. Other gates
still check accounts, evidence, grounding, dates, and duplicates. Pending tasks
must be reviewed before the demo claims successful approval.

## Documentation and release gaps

- Have a teammate follow the setup from a fresh checkout. Record the exact
  prerequisites, failures, and resulting output. The external transcriber still
  requires a verified delivery/provenance arrangement. The submitted report
  describes a cached-model setup test, so cold downloads remain unverified.
- Confirm with the TA whether native Apple Silicon reproduction meets the course
  packaging expectation. Preserve the MLX/Mac dependency in deployment notes.
- Update the final System Card limitations from the group rehearsal. Address
  overlap/noise, speaker confusion, missed commitments, tentative language,
  unresolved dates, duplicate checks, reviewed cross-meeting changes, unsupported
  answers, and the selected evaluation's small sample and reviewer scope.
- Reconcile final report claims with actual implementation and evidence. The
  submitted Milestone 4 report says next Friday remains unresolved. The November
  17 parser change defines next weekday as that day in the following calendar
  week. Dates have day precision. Bare next week remains a review case.
- Verify the final repository URL and its relationship to the course team's
  ai-capstone repository. The submitted report names ai-capstone, while this
  implementation is guardian-agent. Link both with their roles once confirmed.
- Confirm the final contribution statement with all members. The presenter
  sections specify speaking roles and do not establish code authorship.

## Evaluation and performance work

Keep the submitted results as dated baselines. The 24-case synthetic extraction
suite, 28 frozen-source answers, eight personal-case judgments, and eight-case
red-team suite have different scopes. Bryan's selected judgments remain the
presentation's human-review evidence. Any additional reviewers or group-audio
results need their own method and counts.

For the new recordings, record expected and observed tasks, owners, final dates,
misses, extra tasks, speaker errors, review actions, processing failures, and
available stage durations. This is a demo acceptance sample. A short-versus-long
comparison needs the same target commitments and controlled content to attribute
an observed difference to length. Otherwise report the recordings as distinct
cases. Preserve genuine failures and describe any fixes/retests.

The existing latency study has three runs per workload and excludes mobile
upload, authentication, database writes, indexing, and live retrieval. If final
claims cover end-to-end performance, collect those timings. Existing cost values
are October 26 API-equivalent estimates with stated assumptions. Refresh pricing
and usage before presenting a new current-price estimate.

## Proposed owners and handoffs

- Bryan assembles the final report and video, checks the end-to-end flow, and
  packages the release and evidence links.
- Will verifies a fresh setup, shared-project membership, speaker/account
  mapping, and frontend behavior, then records the opening presenter section.
- Guadalupe reviews the new recording outputs and failure cases, checks the
  evaluation discussion, and records task-review presentation footage.
- All three record their meeting parts, review their contribution statements,
  and approve the final report and presentation claims.

These assignments are proposed for team confirmation. Actual availability and
course deadlines determine the work schedule.

## Final submission checklist

- Confirm the official rubric, deadline/timezone, format, duration, and check-in.
- Complete and record the fresh-project two-meeting acceptance run.
- Run the full software checks with the disposable database available.
- Finish the independent setup check and packaging explanation.
- Finalize the report, architecture/deployment links, limitations, and contributions.
- Export the team demo, verify audio/captions and readability, and test its public
  link while signed out.
- Link the final demo and fixed release revision from the repository.
- Produce the required submission files, inspect their rendered layout, and test
  every evidence link before upload.

TestFlight remains on hold. Agentic tool calling remains a proposed extension.
A decision to add either should be driven by a confirmed final requirement or a
specific team workflow. Neither has completion evidence in this release plan.
