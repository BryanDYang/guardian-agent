# Guardian Agent final report draft

Course CIS-5980. Track AI Engineering. Team Will Liu, Guadalupe Cantera, and
Bryan Yang. Updated November 26, 2026. This is a working final-report draft.
Reviewed against the three final-deliverable assignment PDFs on November 17.
The exact Canvas deadlines and showcase session date await confirmation.
The [final roadmap](roadmap.md) owns outstanding work and acceptance gates.

## Abstract

Guardian Agent is a meeting follow-through application for research teams. It combines
speaker-attributed transcription, structured summaries and task extraction,
human-confirmed ownership and task updates, immediate email follow-through,
and cited project chat. On a 24-case synthetic development suite, the recorded
extraction F1 was 0.897 compared with 0.710 for the rules baseline. A separate
28-answer frozen-source evaluation completed without timeouts, and Bryan's
review classified 25 answers as Supported, one as Partly Supported, and two as
Unsupported. These bounded development results motivate further testing on real
team recordings. A November 26 functional simulator rehearsal passed task
approval, actual inbox delivery, and chat citation-to-audio navigation; it is
not a new accuracy benchmark or a complete cross-meeting reconciliation test.

## Project overview

Guardian Agent helps research teams turn recorded discussions into reviewable work and
recover the evidence behind decisions across meetings. A user records or uploads
a meeting, receives a speaker-attributed transcript and summary, reviews extracted
tasks, and uses project-scoped chat to ask questions with source citations.
Accepted tasks can generate immediate follow-up email. Users can correct owners
and dates, complete tasks, and return work for review with change notes.

Our final scenario uses three staged team recordings stored as November 23,
December 2, and December 3, 2026. The rehearsed demo centers on meeting #3,
showing reviewed identities, extracted tasks and dates, manual task approval,
email arrival, and a decision recovered through cited chat. The recorded
three-presenter video remains to be produced.

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
arrangement. The [Model Card](model_card.md), [System Card](system_card.md),
and [evaluation reproduction guide](evaluation.md) document configuration and
measured scope; the [walkthrough](../evidence/demo_walkthrough.md) records
revision-specific checks. The repository submission PDF pins its reviewed revision.

## Data and inputs

Inputs include public AMI Meeting Corpus audio, 24 synthetic extraction cases,
14 frozen-source RAG questions evaluated with two retrieval variants, eight
personal-case human judgments, and the team's staged meeting scripts. Describe
selection and any splits for each reported result in the final evaluation
section. Treat the synthetic suite as development data. The team audio was supplied locally and processed in the shared project; it is
not included in the public repository. The System Card documents provider
processing and retention boundaries. Original consent and any further sharing
permissions remain the team's responsibility. The external
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
Will as Owner in the shared project. The November 26 rehearsal also verified
Guadalupe as Member and all three account names in People.

Deadline parsing now supports weekday expressions, weekday/date combinations,
short ordinal dates, and time-of-day qualifiers at calendar-day precision.
Next-week weekdays use the following calendar week. The approval wording gate
accepts typographic apostrophes and common introductory acknowledgments before
explicit self-commitments. Tentative language and ambiguous dates need review.
Other account, evidence, title-grounding, and duplicate gates also apply.

The November 24 recording inspection exposed missing spoken/qualified dates.
The parser was extended and 34 existing pending task dates were repaired with
audit entries. Meeting #3 also split Will into two acoustic labels; human
confirmation mapped both to Will while retaining raw labels and history.
Its local playback was restored from the hash-matching original audio.
The November 26 simulator rehearsal verified task approval, To-do visibility,
actual email arrival, and chat citations at 04:39 and 05:05 opening the source
transcript and audio. These are bounded functional checks, not fresh extraction
or automatic diarization accuracy measurements.

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

The [evaluation guide](evaluation.md) maps these baselines to metric definitions,
sample counts, saved predictions, and tested reproduction commands. Its historical
aggregates were recomputed during final repository preparation. The final report
PDF should retain these scopes and include the bounded simulator rehearsal
separately from the scored model evaluations.

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

Meeting #3 produced four acoustic clusters for three people and some mixed-voice
turns. Human naming corrected the split, not every segment. Ambiguous ASR text
such as “tomorrow morning at night” remains for review. Broader diarization and
duplicate-task improvements were deferred to avoid unverified changes before the
demo; these failures remain visible limitations.

## Verification and reproducibility

November 17 validation reported 219 passing Python tests, 196 database-dependent
tests skipped, passing lint, and a successful signed simulator build. An earlier
Milestone 4 checkpoint reported 395 passing tests with its own environment and
revision. The subsequent CI run at `2479b1e` passed all 415 tests with the disposable
database running, plus lint, formatting, and the extraction baseline. Its
[run record](https://github.com/BryanDYang/guardian-agent/actions/runs/44005877745)
is a historical complete software checkpoint, not the latest release result.
Final repository preparation verified a clean local checkout with a new locked
environment, the 24-output credential-free rule run, and 435 passing tests against
disposable PostgreSQL. Two upstream deprecation warnings remained. Ruff and local
documentation link checks passed. The walkthrough records the setup correction
and boundaries; this did not test cold model downloads or full native setup.

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

Guardian Agent provides a reviewable path from meeting recordings to tasks, follow-up,
and cited project memory. The final report should summarize the completed
functional rehearsal and tie each headline result to
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

The exact Canvas deadlines, showcase date, and final demo URL
remain pending finalization; completed rehearsal evidence is in the walkthrough.
Submit the technical
report as one PDF. Prepare the longer presentation recording, its PDF slides,
and the separate single-static-slide live showcase package with the advance
EdDiscussion and Canvas submissions specified in the assignment.
