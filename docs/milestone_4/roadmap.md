# Milestone 4 release scope and acceptance

Prepared October 26, 2026. Track: **AI Engineering**. This document owns current
milestone scope and acceptance. Record progress in the [journal](../weekly_journal.md)
and observed runs in the [walkthrough](../evidence/demo_walkthrough.md).
The [Milestone 3 roadmap](../archive/milestone_3/roadmap.md) is historical.

## Requirements and current evidence

Local assignment sources: `contexts/milestone_4/Milestone 4.pdf` and
`contexts/milestone_4/CIS-5980_Phase 4.pptx`. These ignored references are not
available in a fresh clone. The PDF requires a single submission PDF, repository
link, weekly updates, and a mandatory TA check-in. Canvas owns the deadline;
Bryan confirmed November 16, 2026 as the Canvas deadline on October 26. The rubric allocates 60 points
to release/evaluation readiness and 40 to documentation/demo readiness.

| Requirement | Existing foundation | Completion evidence still needed |
| --- | --- | --- |
| Runnable release candidate | Native recording/upload, transcription, extraction, task review, Calendar, cited chat, captured email | Define supported configuration and complete a fresh-project native acceptance run at a fixed revision |
| Packaging and reproducibility | src layout, pyproject.toml, uv.lock, setup commands, migrations, CI | Verify fresh-checkout setup; resolve separately supplied transcriber source/provenance; provide exact container steps or justify and verify equivalent reproducibility scripts |
| Basic observability | Processing logs, health endpoint, audit history, evaluation usage/timing | Audit runtime coverage; make request/meeting correlation, stage timing, model, status and available usage inspectable; document privacy, retention and unavailable fields |
| Full evaluation and error analysis | ASR/extraction baselines, RAG runner and retrieval comparison, eight personal-case reviews | Freeze reviewed labels, finish answer/citation and refusal evaluation, preserve failures, publish current results and error slices |
| Latency and cost | Partial chat timings and hypothetical API-equivalent estimates | Measure representative end-to-end workloads with environment, repetitions, failures, usage and cost assumptions |
| Red-teaming and mitigations | Isolation tests, citation validation and approval controls | Threat model; executed attacks, outcomes, fixes/retests and residual risks |
| Documentation draft | Architecture diagrams, run/deployment instructions, troubleshooting and evaluation protocols | Reviewer quick-start verification, reproducibility checklist, updated system/model cards and report assembly |
| Demo | Product narrative and detailed acceptance script | Recorded 90-second core flow, public video URL linked from project page/README |
| Coordination and submission | Weekly journal and repository URL | Confirm TA check-in, deadline, task owners and selected extension contributions; assemble and visually review submission PDF |

The PDF asks for container run steps; its rubric allows containerization or
equivalent scripts. The lecture emphasizes Docker, tracing and adversarial tests.
Do not assume Linux containers can run the current Apple MLX processing path.
Choose and validate the packaging boundary before claiming portability. iOS
continues to require Xcode; keep signing enabled for simulator acceptance.
No Kubernetes or additional orchestration is needed to establish this release.

The lecture specifies a demo at most 90 seconds, captions, voiceover and at least
1080p. Aim for 75-85 seconds and keep a video backup for the showcase. Public
application deployment is optional; a publicly accessible demo video is required.

## Baseline and known limits

- October 21 evidence records 319 passing backend tests and Ruff checks; the
  signed simulator build passed October 20. These are historical checks, not
  verification of a new release candidate.
- The RAG run completed all 28 retrieval rankings but only nine answers; three
  calls timed out, one was interrupted and 15 were not run. Both unsupported
  answer pairs were unrun. Target recovery is not semantic answer accuracy.
- Bryan and Guadalupe filled all eight personal-case review tables October
  22-23. Guadalupe reviewed transcripts only; prior exposure and adjudication
  remain unrecorded. Older archived status text may describe earlier checkpoints.
- Known product gaps include automatic structured dates, missing owner mappings,
  deadline-change evidence and completion-state proposals. Real inbox delivery,
  recurring reminders and two-host recovery lack completed acceptance evidence.
- Existing demo preparation does not establish a recorded clean journey.

See the [dated RAG evidence](../evidence/demo_walkthrough.md#october-21-ami-retrieval-comparison-and-partial-live-answer-run)
and [review update](../weekly_journal.md#october-22-23-human-review-and-demo-preparation).

## Release candidate flow

A consented recording in a fresh project becomes a transcript, summary and
reviewable task with source evidence. A human confirms identity, owner and any
unresolved date, approves the task, sees it in Tasks/Calendar and inspects one
captured follow-up. Supported chat cites project evidence; unsupported chat
abstains. Relaunch preserves the result.

This is the selected manual-review acceptance scope, not a claim it has passed. Label capture
mode visibly; real inbox delivery requires observed receipt. Demonstrate
experimental automatic approval separately and disclose its gates. Do not imply
that manual date entry or task completion proves automatic continuity.

## Work order and acceptance gates

Proposed leads below require team confirmation; no assignment or meeting message
has been sent as part of this assessment.

| Order | Work | Gate | Proposed lead |
| --- | --- | --- | --- |
| 1 | Freeze release configuration, flow and claims; confirm Canvas and TA session | Recorded revision/configuration, explicit exclusions, confirmed dates and owners | Bryan with team |
| 2 | Follow setup from a fresh checkout; choose Mac/container boundary and transcriber delivery | Another reviewer reproduces representative output using documented prerequisites and exact commands | Team |
| 3 | Run fresh-project native acceptance; reproduce failures before fixes | Saved run ledger and recording covering the proposed flow, including refusal and relaunch | Bryan with assistant support |
| 4 | Diagnose CLI timeouts; adjudicate labels; complete current evaluation | Results table with denominators, model/prompt/data versions, timeout/error counts and reviewed correctness/citation/refusal judgments | Bryan and reviewers |
| 5 | Run bounded red-team exercise and mitigate findings | Evidence for transcript/retrieval injection, cross-project access, unsupported citations, unintended approval/delivery and expensive/repeated requests; failures retested or disclosed | Team |
| 6 | Measure recording-to-results, supported chat and unsupported chat | Workload/environment definitions, cold/warm distinction, timings including failures, usage and clearly labeled estimates | Bryan with assistant support |
| 7 | Rehearse, record and assemble | Captioned public demo link, reviewer checklist, updated cards, TA packet, contribution/extension updates and visually checked single PDF | Team |

Use existing architecture, quick-start, evaluation protocols and evidence owners
instead of adding parallel setup/status guides. Extend logging only where the
coverage audit exposes a concrete gap. Live mail, reminders, date/completion
improvements and two-host recovery enter the release only with their own
acceptance evidence; otherwise document them as limitations.

## TA check-in packet

Prepare release run instructions; evaluation results and representative failures;
latency/cost summary; red-team results and mitigations; documentation outline;
and demo plan. The journal records a request for the week of November 2, but no
accepted time. Do not treat that request as a confirmed Milestone 4 check-in.


## October 26 execution checkpoint

The [execution evidence](../evidence/demo_walkthrough.md#october-26-milestone-4-release-checkpoint)
records the fresh-install audio check, signed simulator build, full database tests,
frozen-source answer rerun, workload measurements and bounded red-team pass.
The backend now passes disabled diarization explicitly; citation verification
refuses mixed invalid/valid replies. The captioned public demo is available, and Bryan confirmed all 28 answer
reviews on October 30. TA check-in and final demo sign-off remain open. See the [report draft](submission_draft.md)
for the reviewer checklist and remaining submission fields.


## October 30 human review completion

Bryan reviewed and accepted all 28 correctness, citation-entailment and refusal
judgments in the [completed review](human_review.md). Final-output categories:
25 Supported, 1 Partly supported, 2 Unsupported. The two false refusals and the
style/dense qualifier remain recorded as failures, not changed to passes. This
was an informed review following AI-assisted preparation. Personal-case
adjudication, independent setup, team contribution updates, demo sign-off and
the mandatory TA check-in remain separate gates.


## October 30 submission readiness and team handoff

The [report readiness table](submission_draft.md#submission-readiness-as-of-october-30)
separates assembled technical sections from missing submission inputs. Bryan sent
Will and Guadalupe requests for setup/report feedback and contribution/extension
summaries, followed up with Derrick, and offered to record a non-synthetic final
demo. Replies, task owners and the TA time remain unconfirmed. The current public
video is a reference for that recording. TestFlight remains optional exploration.
See the [dated journal entry](../weekly_journal.md#october-30-team-update-and-submission-readiness)
for this user-reported coordination; no messages were sent by the assistant.
