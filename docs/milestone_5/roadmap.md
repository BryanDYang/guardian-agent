# Final submission scope and acceptance

Updated November 26, 2026 for CIS-5980 AI Engineering. This document owns the
remaining work for Milestone 5 or the final submission. The three course PDFs stored locally in `contexts/milestone_5/` establish the
final deliverables.
Canvas shows the presentation PDF due December 6 at 8:59 p.m. The other
assignment dates remain separate. The showcase session date and timezone
are still needed to calculate its advance deadlines.

## Confirmed course deliverables

The presentation/showcase is 150 points, the technical report is 40 points,
and repository/documentation is 10 points.

### Recorded presentation and public demo

The [presentation notes](presentation_notes.md) link the nine-slide presentation
PDF and separate one-slide showcase PDF, with speaking sections, a 9:45 rehearsal
target, EdDiscussion text, and alt text. Final recording/publication is still open.

Prepare the longer Final Capstone Presentation recording for submission three
days before the showcase session. The presentation rubric rewards a 9-10 minute
presentation. Include the problem, user capabilities, architecture, development
choices, evaluation/results, safety/limitations, and future work. Demonstrate an
end-to-end path with one strength and one known limitation. Slides are submitted
as PDF. Link a short, publicly accessible demo video from the README or project
page. The existing three-person 4-5 minute app demo can be a segment of this
presentation, with the remaining time covering the other required topics.

### Live showcase

The showcase guidelines specify a live Zoom talk with camera on and a hard stop
at 10 minutes per group. At least one team member attends live. Use one static
slide, with spoken delivery. The showcase rules prohibit video, audio, animations,
additional media, and props. Prepare a separate talk around the slide.

Three days before the session, post a title of at most 120 characters, a 50-word
plain-language summary, and a one-sentence headline result on EdDiscussion.
Forty-eight hours before the session, upload the single-slide PDF to Canvas,
named `Lastname_Firstname_ShortTitle`, and include image alt-text as a note.
Join 10 minutes early for the AV check. The slide guidance prefers 16:9,
recommends at most 20 words, and asks for readable text of at least 28 points.

The document contains both general live-demo wording and the specific single-slide
showcase rules, and explicitly distinguishes the longer presentation recording.
Follow the separate showcase restrictions and confirm any session-specific
instructions or recording-duration clarification with the instructor.

### Final technical report

Submit one PDF with accessible repository, demo, and evidence URLs. Required
sections are title information, abstract with one or two quantified headline
results, introduction/problem framing, system overview with a diagram, data and
inputs, methodology/configuration, development since Milestone 3 with a decision
log, evaluation setup and reproduction, results/baseline comparisons, robustness
and safety, latency/cost, error analysis/limitations, conclusion/future work, and
references. Include at least one targeted comparison supporting a design choice.

### Repository and documentation

Provide an accessible repository link. Public is encouraged, and private is
accepted with teaching-staff access. Include README capabilities/demo link,
end-to-end quick-start, commands reproducing the main evaluation results,
configuration/parameter documentation, readable code, and final supporting
artifacts for evaluation, red-teaming, latency, cost, and reproducibility.
Include final Model and System Cards if created in earlier milestones. For
withheld components, provide a clear stub explaining what is withheld and why,
plus runnable components where possible. Canvas requires a single PDF for this
assignment; use the repository submission PDF with clickable code, setup, cards,
evaluation, evidence, and demo links. One group upload covers all members.

Assignment sources are the presentation/showcase, repository/documentation, and
technical-report PDFs in `contexts/milestone_5/`. This Git-ignored directory holds
local course references. A fresh checkout requires obtaining those references
separately. The confirmed requirements above remain available in this roadmap.

Start with the [final report draft](submission_draft.md). Preserve the
[submitted Milestone 4 PDF](../archive/milestone_4/milestone4_submission.pdf) as
the historical submission. Record new run evidence in the
[walkthrough](../evidence/demo_walkthrough.md) and progress in the
[journal](../weekly_journal.md).

## First priority for the team

### Record the presentation using the completed rehearsal

Three staged recordings are in the shared project: November 23, December 2,
and December 3, 2026. The November 26 simulator rehearsal centered on meeting #3
and verified People, reviewed speaker accounts, task dates and evidence, manual
approval, To-do, actual inbox arrival, and chat citations opening transcript/audio.
The [walkthrough](../evidence/demo_walkthrough.md#november-26-group-demo-simulator-rehearsal)
records the completed path and corrections. This was not a fresh-project two-meeting
state-reconciliation run, a new scored benchmark, or a timed team presentation.

The revised [three-presenter script](group_demo_script.md) follows one recording-
processing task from meeting #2 to meeting #3: initial December 7 commitment,
automatic deadline revision to December 4, and an answer citing both meetings. The November
27 isolated API rehearsal and live retrieval/model check passed; the continuous
on-screen approval/update sequence still needs rehearsal/filming. Will presents
the original plan and initial email, Guadalupe the automatic update, and Bryan
the current task and citations. Record the 4:30 app segment within the longer
presentation, publish the final video, and update the README. Unsupported-question
behavior remains a separate check.

### Verify the release after the latest changes

Freeze a commit and record the app, backend, model, and configuration used.
November 17 checks reported a successful signed simulator build, lint passing,
219 Python tests passing, and 196 database-dependent tests skipped because the
local database was unavailable. The subsequent CI fix in `2479b1e` passed all 415 tests against disposable
Postgres, plus the frozen extraction baseline and smoke checks. Preserve the
[successful CI run](https://github.com/BryanDYang/guardian-agent/actions/runs/44005877745)
as a historical software acceptance checkpoint.
Rehearse the normal upload/review/email flow on that revision.

The date parser now supports spoken weekdays and calendar dates. The approval
wording gate accepts common acknowledgments and curly apostrophes. Other gates
still check accounts, evidence, grounding, dates, and duplicates. Pending tasks
must be reviewed before the demo claims successful approval.

## Documentation and release gaps

- The credential-free path passed a clean local checkout/new environment check
  with 435 database-backed tests on November 26. Have a teammate follow the full
  native setup from a fresh checkout. Record the exact
  prerequisites, failures, and resulting output. The external transcriber still
  requires a verified delivery/provenance arrangement. The submitted report
  describes a cached-model setup test, so cold downloads remain unverified.
- Confirm with the TA whether native Apple Silicon reproduction meets the course
  packaging expectation. Preserve the MLX/Mac dependency in deployment notes.
- Final [Model Card](model_card.md), [System Card](system_card.md), and
  [evaluation reproduction guide](evaluation.md) now exist. Keep their limits
  aligned with new evidence. They address
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

- Confirm Canvas deadlines and the showcase session date/timezone.
- Prepare the longer presentation recording, the one-slide live talk, and the
  EdDiscussion title, summary, and headline result with their advance deadlines.
- Record the rehearsed meeting #3 demo. A fresh-project two-meeting state-update
  run remains separate, unverified work if the team chooses to claim it.
- Verify full software checks at the final frozen revision. The historical
  `2479b1e` checkpoint had 415 passing database-backed tests; retain dated counts.
- Finish the independent setup check and packaging explanation.
- Finalize the required report sections and architecture diagram, deployment
  links, targeted comparison, limitations, references, and contributions.
- Review the final cards and tested reproduction commands after any model,
  evaluation, or scope changes.
- Export the team demo, verify audio/captions and readability, and test its public
  link while signed out.
- Link the final demo and fixed release revision from the repository.
- Produce the required submission files, inspect their rendered layout, and test
  every evidence link before upload.

TestFlight remains on hold. Agentic tool calling remains a proposed extension.
A decision to add either should be driven by a confirmed final requirement or a
specific team workflow. Neither has completion evidence in this release plan.
