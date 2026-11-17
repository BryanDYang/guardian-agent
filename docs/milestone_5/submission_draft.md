# LabSync final report draft

Course CIS-5980. Track AI Engineering. Team Will Liu, Guadalupe Cantera, and
Bryan Yang. Prepared November 17, 2026. This is a working final-report draft.
Reviewed against the three final-deliverable assignment PDFs on November 17.
The exact Canvas deadlines and showcase session date await confirmation.
The [final roadmap](roadmap.md) owns outstanding work and acceptance gates.

## Abstract

LabSync is a meeting follow-through application for research teams. It combines
speaker-attributed transcription, structured summaries and task extraction,
human-confirmed ownership and task updates, immediate email follow-through,
and cited project chat. On a 24-case synthetic development suite, the recorded
extraction F1 was 0.897 compared with 0.710 for the rules baseline. A separate
28-answer frozen-source evaluation completed without timeouts, and Bryan's
review classified 25 answers as Supported, one as Partly Supported, and two as
Unsupported. These bounded development results motivate further testing on real
team recordings. The final group-audio acceptance run remains pending.

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

## Data and inputs

Inputs include public AMI Meeting Corpus audio, 24 synthetic extraction cases,
14 frozen-source RAG questions evaluated with two retrieval variants, eight
personal-case human judgments, and the team's staged meeting scripts. Describe
selection and any splits for each reported result in the final evaluation
section. Treat the synthetic suite as development data. The new team audio is
pending recording and consent. Document dataset licenses, recording access,
provider processing, and retention before finalizing this section. The external
transcriber has unresolved provenance/redistribution arrangements described in
the submitted Milestone 4 report.

## Methodology and development decisions

The pipeline uses configured pretrained speech and text models. The reported
work focuses on integration, prompting, retrieval, evidence validation, and
review workflows. Document exact model versions, prompt revision, parameters,
and frozen configuration alongside each final result.

The decision log includes adding quoted task evidence for review, requiring
human-confirmed speaker/account mappings before automatic approval, using scoped
retrieval with validated citations, and separating email delivery into an outbox
worker. The date parser and approval wording were revised after the November 17
script rehearsal exposed failed conversions and brittle language matching.
The architecture documents component responsibilities and failure handling.

The existing synthetic extraction comparison supports model extraction against
a rules baseline. For the required targeted design comparison, report the
existing dense-versus-hybrid retrieval comparison with its exact setup and
results from the review evidence. Populate its per-variant findings before
finalizing the report. Prefer this existing experiment to adding an unmotivated
new experiment solely for the final report.

## Development from Milestone 3 through the final release

Milestone 3 established the application and partial evaluation. Milestone 4
completed the frozen-source answer run and selected human review, added
extraction comparisons, red-team checks, and representative latency/cost work.
The following changes extend that baseline.

### Changes since the Milestone 4 submission

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

The final PDF needs a consolidated results table with metric definitions, sample
counts, baseline, and evidence URLs. The final report should add the actual group-audio acceptance results, correction
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
revision. The subsequent CI run at `2479b1e` passed all 415 tests with the disposable
database running, plus lint, formatting, and the extraction baseline. Its
[run record](https://github.com/BryanDYang/guardian-agent/actions/runs/44005877745)
is the current complete software checkpoint. Recheck the final frozen revision.

A teammate should reproduce setup and a representative recording from a fresh
checkout and record missing prerequisites. Transcriber provenance/delivery,
cold-download verification, and TA agreement on native-Mac packaging remain
open items carried from the submitted report.

## Final demonstration and access

The existing [Milestone 4 video](https://www.youtube.com/watch?v=xgaeo0GTi1Y)
is available. The new [three-presenter script](group_demo_script.md)
targets a 4-5 minute app-demo segment within the longer recorded presentation. Will presents
members and capture, Guadalupe presents task evidence and reviewed changes,
and Bryan presents email and cited retrieval. Final recording, captions,
public link, and signed-out playback verification are pending.

TestFlight is on hold. Confirm the final reviewer's access method and provide
backend/setup instructions appropriate to that method.

## Conclusion and future work

LabSync provides a reviewable path from meeting recordings to tasks, follow-up,
and cited project memory. The final report should summarize the completed
recording-based acceptance run once available and tie each headline result to
its evaluation scope. Practical next work includes stronger speaker evaluation,
completion-only update extraction, clearer ambiguous-date review, reproducible
external dependency delivery, and broader operational testing.

## References

Include complete citations for the AMI Meeting Corpus, Whisper/MLX Whisper,
pyannote.audio and any voice-identification component used, the configured text
and embedding providers/models, Supabase/pgvector, FastAPI, SwiftUI, and other
components relied on in the final release. Verify upstream versions and licenses.
The submitted Milestone 4 report contains source links to carry forward.

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

The exact Canvas deadlines, showcase date, final demo URL, release revision,
and completed acceptance evidence are pending finalization. Submit the technical
report as one PDF. Prepare the longer presentation recording, its PDF slides,
and the separate single-static-slide live showcase package with the advance
EdDiscussion and Canvas submissions specified in the assignment.
