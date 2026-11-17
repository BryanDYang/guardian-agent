# LabSync final report draft

Course CIS-5980. Track AI Engineering. Team Will Liu, Guadalupe Cantera, and
Bryan Yang. Prepared November 17, 2026. This is a working final-report draft.
The official Milestone 5 assignment and submission deadline await confirmation.
The [final roadmap](roadmap.md) owns outstanding work and acceptance gates.

## Project overview

LabSync helps research teams turn recorded discussions into reviewable work and
recover the evidence behind decisions across meetings. A user records or uploads
a meeting, receives a speaker-attributed transcript and summary, reviews extracted
tasks, and uses project-scoped chat to ask questions with source citations.
Accepted tasks can generate immediate follow-up email. Users can correct owners
and dates, complete tasks, and return work for review with change notes.

Our final scenario follows Will, Guadalupe, and Bryan through two staged project
meetings. The first assigns work and revises deadlines. The second reports
progress, moves a deadline, and hands work to another teammate. The planned
recording-based rehearsal will establish which outputs and review actions can
be shown in the final video.

## System and release configuration

The SwiftUI client communicates with an authenticated FastAPI backend. Supabase
provides identity and PostgreSQL persistence. Local Whisper/diarization handles
audio, a configured text model extracts structured meeting information, and
embeddings support project-scoped retrieval. Answers carry validated source
handles and quotes. A separate outbox worker handles task email.

The [architecture](../architecture.md) documents interfaces, data flow, and
operational boundaries. The [README](../../README.md) and
[shared-backend guide](../reference/shared_backend.md) own setup and deployment.
The current audio path uses Apple Silicon and MLX. The submitted Milestone 4
report describes native-Mac reproducibility and a separately supplied transcriber.
The final release needs an independently checked setup and confirmed packaging
arrangement. Final tested commit, configuration, and artifact links are pending.

## Changes since the Milestone 4 submission

The November 17 work adds a People view to the project menus, with member names,
account emails, and roles. Simulator verification showed Bryan as Member and
Will as Owner in the shared project. The team should verify all three accounts
before the recording session.

Deadline parsing now supports weekday expressions, weekday/date combinations,
short ordinal dates, and time-of-day qualifiers at calendar-day precision.
Next-week weekdays use the following calendar week. The approval wording gate
accepts typographic apostrophes and common introductory acknowledgments before
explicit self-commitments. Tentative language and ambiguous dates need review.
Other account, evidence, title-grounding, and duplicate gates also apply.

The shared meeting scripts now use November 24 and December 2, 2026. The team
presentation has separate sections for Will, Guadalupe, and Bryan. These changes
have software and text-level checks. The full team-audio rehearsal is pending.

## Evaluation methods and dated results

The submitted [Milestone 4 report](../archive/milestone_4/milestone4_submission.pdf)
records these baselines.

- Frozen-source RAG completed 28 calls across 14 questions and two retrieval
  variants, with zero timeouts. Bryan reviewed 25 answers as Supported, one as
  Partly Supported, and two as Unsupported. Supported includes appropriate
  refusals. Four designated unsupported-question refusals were appropriate,
  while two supported questions received inappropriate refusals.
- The 24-case synthetic extraction suite reported precision 0.929, recall 0.867,
  and F1 0.897. Its rules baseline reported 0.688, 0.733, and 0.710. Labels and
  lexical scoring support development comparisons. Held-out generalization
  remains unestablished.
- Eight November 5 chat red-team checks passed within their bounded test scope.
- Eight personal-case human judgments remain a separate evaluation set.

Before the latest fixes, the two team scripts produced 21 and 13 commitments.
Each output had one date phrase resolved by the old parser, and none passed the
old wording gate. Replaying those saved outputs after the fixes resolved 19 of
21 Script #1 deadline strings and all 12 stated Script #2 deadlines. Seven of
34 candidates passed the wording gate alone. This replay uses written speaker
turns and synthetic timestamps. It does not measure transcription, diarization,
full approval, or inbox delivery.

The final report should add the actual group-audio acceptance results, correction
counts, failures, and retests after recording. Preserve the scopes above when
comparing the new evidence.

## Latency and cost

The submitted October 26 study ran three trials per workload with cached model
weights. Median recording-through-extraction latency was 8.33 seconds, supported
chat 4.43 seconds, and unsupported chat 4.54 seconds. The reported API-equivalent
estimates were $0.0715, $0.0366, and $0.0150 per run respectively, using the
historical rate assumptions in the submitted report. These were modeled costs
for subscription-backed CLI runs. The study excludes several mobile/backend
stages and infrastructure costs.

Final group-audio duration, upload and processing timing, observed usage, and
failure counts are pending. Cite historical rates as historical assumptions.
Verify pricing before publishing any new current-cost estimate.

## Error analysis and limitations

Speaker separation and identity mapping can fail, especially with overlap,
noise, and multiple voices. Users confirm each recording's speaker accounts.
Missed tasks, merged actions, wrong owners, vague deadlines, and repeated
commitments require explicit failure analysis. Automatic approval has several
independent gates, so successful extraction can still leave a candidate pending.

Cross-meeting updates use a reviewer-confirmed workflow. Completion-only proposal
extraction remains unfinished in the documented architecture. A valid quoted
citation can still accompany an overreaching answer. The final evidence uses
small development samples and selected human judgments, with production load,
quotas, alerts, abuse controls, and broad speaker performance unverified.

Revise this section with the worst observed group-recording failures and the
justification for each unresolved issue before submission.

## Verification and reproducibility

November 17 validation reported 219 passing Python tests, 196 database-dependent
tests skipped, passing lint, and a successful signed simulator build. An earlier
Milestone 4 checkpoint reported 395 passing tests with its own environment and
revision. The final packet needs a fresh full-suite result with the disposable
database running and a fixed release revision.

A teammate should reproduce setup and a representative recording from a fresh
checkout and record missing prerequisites. Transcriber provenance/delivery,
cold-download verification, and TA agreement on native-Mac packaging remain
open items carried from the submitted report.

## Final demonstration and access

The existing [Milestone 4 video](https://www.youtube.com/watch?v=xgaeo0GTi1Y)
is available. The new [three-presenter script](../archive/milestone_4/group_demo_script.md)
targets 4-5 minutes, subject to the final assignment's duration. Will presents
members and capture, Guadalupe presents task evidence and reviewed changes,
and Bryan presents email and cited retrieval. Final recording, captions,
public link, and signed-out playback verification are pending.

TestFlight is on hold. Confirm the final reviewer's access method and provide
backend/setup instructions appropriate to that method.

## Contributions and submission information

The Milestone 4 report attributes application integration, follow-through,
selected evaluation, and release preparation to Bryan. It attributes frontend
backend integration, authentication, projects, voice matching, and RAG chat work
to Will, and evaluation, datasets, realistic-recording tests, and documentation
to Guadalupe. Each member should confirm and update this statement for the final
submission. Presentation roles describe the video speaking order.

The implementation [repository](https://github.com/BryanDYang/guardian-agent)
and the [course-team repository](https://github.com/BryanDYang/ai-capstone) both
appear in project materials. Confirm their final roles and the submitted release
revision before finalizing the repository section.

The final assignment, deadline, required file list, check-in status, final demo
URL, release revision, and completed acceptance evidence are pending finalization.
