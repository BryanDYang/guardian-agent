# Milestone 3 scope and acceptance

Updated October 10, 2026. Proposed targets and owners require team confirmation. Course requirements remain authoritative; see the rubric referenced by the [submission draft](submission_draft.md).

## Product vision and current gap

The intended product turns a consented meeting recording into assigned work, follow-through, and source-grounded project memory. Later meetings and user actions update existing tasks and their reminders. Users can ask questions across that history.

Currently, recordings produce pending candidates. The calendar shows approved tasks with due dates. All seven AMI uploads completed processing and produced 69 candidates, with zero approved at the October 10 inspection. An empty calendar therefore does not mean extraction failed. It also exposes a product gap: undated accepted work needs a to-do view, even when calendar placement is unavailable.

Shared storage/jobs, Google sign-in, project creation, uploads, partial processing checks, and dark-mode appearance have been exercised. They do not establish the complete product loop, external tester access, output quality, speaker identification, or automatic failover.

## Milestone 3 targets

| Target | Acceptance evidence | Proposed lead |
| --- | --- | --- |
| Repeatable native alpha | Fresh-account sign-in, project creation/invitation, authenticated upload, completed results, relaunch persistence, access denial for non-members, and purge verified in the app | Will, with team testers |
| Useful task workflow | Review evidence, confirm owner, accept an undated task into a to-do list; dated tasks also appear in the calendar; completion/edit/undo persist | Will |
| Narrow cross-meeting continuity | On a frozen sequence, create one commitment, update its deadline, explicitly complete it, leave unmentioned tasks unchanged, and send ambiguous matches to review; retain evidence/audit history | Will, Bryan evaluates |
| Grounded project chat | Supported answers cite the correct meeting/time; unsupported questions refuse; meeting/project scopes remain isolated | Bryan and Will |
| Follow-through proof | Demonstrate the current reminder export plus a bounded reminder lifecycle test: schedule, reschedule, complete/cancel, and retry without duplicate delivery | Will, Bryan checks |
| Measured AI behavior | Reuse Milestone 2 regressions; compare independent extraction and reconciliation on identical sequence inputs; dense-only versus hybrid retrieval on identical questions/settings | Bryan |
| Reviewed dataset | Freeze inputs, speaker/account mapping, task-state labels, questions, timestamps, provenance, and second-reviewer disagreements/adjudication | Guadalupe, second team reviewer |
| External alpha feedback | Verify tester sign-in/access, provide a repeatable walkthrough, record observed failures and feedback; confirm course-required participant count from rubric | Team |
| Submission evidence | Exact commit/configuration, tests, metrics with denominators, error analysis, demo, Model/System Cards, and member extension write-ups | Team |

These targets define what to shoot for, not completed commitments. If a target is not implemented and accepted, report the limitation explicitly. Cross-meeting continuity and follow-through are central product gaps, not optional polish that can silently disappear from the report. The existing similarity flag is not reconciliation; one-time Reminders export is not automatic follow-up.

Use human confirmation for ambiguous owners, dates, or task matches. Clear automatic assignment needs an explicit acceptance policy and evaluation of incorrect assignments before enabling it. A missing deadline must not cause the system to invent one.

## Dataset and Milestone 2 reuse

- **TS3005a-d:** one connected development project, processed in suffix order. Inspect transcripts and label supported commitments/state transitions before tuning or scoring. App dates currently represent import dates. Verify corpus dates before resolving relative deadlines.
- **IS1008a:** separate isolation/validation project. One meeting cannot establish sequence tracking.
- **IS1009a and ES2004a:** separate evaluation projects because they are different trials. Both have prior Milestone 2 ASR exposure. Do not call them untouched held-out inputs. Choose a fresh sequence if a clean held-out claim is required.
- **Milestone 2:** inventory the 24 extraction cases, ASR fixtures, prompts/settings, labels, and saved outputs. Preserve historical scores. Rerun baseline and updated variants on identical new frozen inputs; do not compare old synthetic scores directly with new AMI scores as an improvement claim.
- **Coverage gaps:** AMI is a remote-control design scenario. Do not presume it contains explicit completion or deadline changes. Add a clearly labeled scripted, consented sequence for missing acceptance cases and keep its results separate from natural-meeting accuracy.
- **Speaker identity:** corpus speakers are not signed-in users. Use an explicit mapping to consenting test accounts for assignment demonstrations. This is a fixture mapping, not proof of voice recognition. The current Bryan backend runs without diarization.

## Engineering sequence

1. **Freeze expected behavior.** Create a reviewed ledger containing meeting ID, evidence/time, task, owner, deadline, match to prior task, expected state after each meeting, and ambiguity. Freeze supported/unsupported/isolation questions.
2. **Record the baseline.** Run reproducible Milestone 2 extraction and current independent-meeting behavior on those inputs. Save raw outputs and configuration.
3. **Implement against failing acceptance cases.** Add the undated to-do path and bounded reconciliation/reminder behavior. Verify user-marked completion and silence in later meetings do not accidentally reopen or close tasks.
4. **Test follow-through with a controlled clock and notification sink.** Check recipient, timing, cancellation, rescheduling, and deduplication before sending to consenting test accounts. Keep external messaging disabled during offline tests.
5. **Run paired evaluations.** Report task-state correctness, duplicates, incorrect owner/deadline updates, unsupported completions, retrieval Recall@K, answer/citation correctness, refusals, isolation, latency, tokens, and cost with denominators. Report failures and uncertainty.
6. **Run the native walkthrough.** Upload, inspect, review/assign, open to-do/calendar, follow reminder changes, complete a task, ask cited questions, switch project, relaunch, and purge. Record exact commit and observed outcomes.
7. **Freeze the submission.** Link evidence into the walkthrough and submission draft. Do not convert implementation boxes into acceptance claims automatically.

## Shared-backend coordination

Before the next joint meeting, Will pulls the checkpoint and follows [shared-mode setup](../shared_backend.md), using `will-mac`; Bryan uses `bryan-mac`. Match database/storage, migrations, code, and compatible processing settings. Existing local mode remains available, but must not be mixed with shared mode behind a shared endpoint.

At the joint meeting, both hosts stay awake/online. Bryan supplies a disposable recording and checks job/output state. Will starts/stops his server and checks logs. Identify the claiming worker, stop it abruptly during processing, verify the other reclaims the expired lease and publishes one result, restart the stopped host, and repeat in the opposite direction. Normal Ctrl-C waits for in-flight processing, so it does not demonstrate abrupt recovery. Manually switch the app URL to test the surviving API. Live two-host recovery and automatic routing remain unverified.

## Next phase after Milestone 3

| Work | Boundary and reason |
| --- | --- |
| Broad automatic task assignment and follow-up | Expand beyond the bounded evaluated path only after measuring harmful assignments/updates and defining user controls |
| Direct Zoom/Teams/calendar ingestion | Current alpha imports recordings manually; provider ingestion needs separate permissions, consent, retries, and provenance |
| Production availability | Always-on hosting, health-based API routing, automatic restarts, monitoring, and operational ownership; tmux cannot keep a sleeping laptop available |
| Wider continuity and personalization | More projects, speakers, ambiguous references, multilingual recordings, and longer histories require broader labeled evaluation |
| Speaker recognition calibration | Separate calibration/evaluation audio and measure false matches/abstention before relying on names for automatic ownership |
| Playback and product polish | Audio seeking, waveform/duration, storylines, summary editing/sharing, and accessibility acceptance |
| Privacy and release readiness | Selective redaction, participant-level controls, verified deletion, public privacy/support pages, and App Store readiness |

Deferral is a scope proposal, not permission to omit an explicit rubric requirement. Revisit it with the team when the reviewed corpus and acceptance results expose what is achievable.
