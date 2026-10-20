# Milestone 3 roadmap, scope, and acceptance

Updated October 20, 2026. Target submission: October 26, subject to confirming
Canvas. Proposed owners and schedule need team agreement; the course rubric
remains authoritative. This is the single current planning document. Use the
[weekly journal](../weekly_journal.md#week-8-october-12-18-2026) for progress history,
[native walkthrough](../evidence/demo_walkthrough.md) for observed evidence,
[follow-through guide](follow_through.md) for setup and recording scripts, and
[submission draft](submission_draft.md) for the course deliverable.

## Current status and next action

- Implemented: shared audio/jobs and recoverable worker leases, authenticated
  native uploads, project membership, extraction/cited chat, speaker/account
  review, undated To-do and dated Calendar tasks, reviewed reconciliation with
  stable identity/audits, and completion/Undo. A seeded four-meeting native test
  passed October 11; it did not test audio extraction or model accuracy.
- October 17 added immediate task email, recipient preferences, durable delivery
  history/capture previews, and optional evidence-gated automatic approval.
  All 311 backend tests, Ruff lint/format, and the simulator build passed. The
  policy is experimental, not calibrated confidence. Capture mode sends nothing
  externally; recurring reminders remain unfinished.
- The simulator OAuth signing failure was repaired and temporary Keychain
  write/read/delete verified. A fresh Google flow still needs recorded acceptance.
- October 18 screenshots show accepted AMI tasks, including TS3005d evidence,
  and enabled follow-through settings with an empty Test inbox. Bryan reports
  the dev path is working for these checks. The full a-d ledger/score and
  personal audio-to-email acceptance remain open. AMI speakers are not real app
  recipients; approved assignments are not changed by later speaker mapping,
  and enabling email does not bulk-send old tasks.

- October 20 personal scripted native acceptance verified bounded automatic
  approval, tentative-statement abstention, manual dates/Calendar, opt-out,
  duplicate reconciliation, and manual completion/Undo with relaunch persistence.
  Four messages were captured; none were sent to real inboxes. Done now saves
  settings; new-project automation defaults are on. All 317 backend tests and
  the signed simulator build passed. See the
  [case-by-case evidence](../evidence/demo_walkthrough.md#october-20-personal-audio-acceptance-2026-10-20-run-1).
  A was already auto-approved, F1 required a corrected date, and F2 yielded no
  completion candidate. Do not count those as clean manual A or automatic
  date/completion passes.

**Next:** record a clean manual A demo with visual evidence and validate actual
inbox delivery after sender setup. Automatic date resolution and completion
extraction remain gaps. Then finish the independently reviewed a-d ledger,
bounded reminder lifecycle, paired evaluations, external alpha acceptance, and
submission evidence below. Keep manual actions, captured email, real inbox
receipt, and recurring reminders as separate claims.

## Product scope

Turn a consented meeting recording into assigned work, follow-through, and grounded
project memory. Later meetings and user actions should update existing tasks and
their reminders. Current implementation and partial checks do not establish the
complete product loop, natural-data quality, speaker recognition, external tester
access, or automatic failover. Historical upload counts and checkpoints belong
in the walkthrough and journal, not as current totals here.

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
- **Speaker identity:** corpus speakers are not signed-in users. Use an explicit mapping to consenting test accounts for assignment demonstrations. This is a fixture mapping, not proof of voice recognition. The Bryan backend now runs with diarization; TS3005a-d reprocessing completed. Cluster accuracy and name spellings remain unverified.

## Stage 1: establish a trustworthy baseline

**Aim: October 10-13. Proposed leads: Guadalupe for labels, Bryan for baseline, Will for native inspection.**

- [ ] Inspect TS3005a in the app: transcript, summary, evidence, candidates, owner labels, and date handling. Record failures before making fixes.
- [ ] Inventory reproducible Milestone 2 fixtures, expected outputs, extraction prompts/settings, and saved results. Preserve historical results.
- [ ] Review TS3005a-d in order and freeze a task-state ledger with source timestamps, owner, deadline, prior-task relationship, ambiguity, and expected state after each meeting.
- [ ] Have a second reviewer check the ledger and record adjudication. Verify corpus dates before interpreting relative deadlines; current app dates are import dates.
- [ ] Map corpus speakers explicitly to consenting test accounts. Do not describe this fixture mapping as voice recognition.
- [ ] Freeze supported, unsupported, meeting-scope, and cross-project RAG questions with expected sources.
- [ ] Record corpus gaps. Add a clearly labeled scripted sequence for deadline changes/completion if AMI does not contain them.
- [ ] Run the independent-meeting baseline on frozen inputs and save raw outputs/configuration.

**Gate:** Inputs and reviewed expectations are versioned and reproducible. Every intended acceptance case has evidence or is explicitly assigned to a scripted fixture. No new comparison is based on incompatible historical scores.

## Stage 2: complete the first native task loop

**Aim: October 13-16. Proposed lead: Will; Bryan verifies.**

- [ ] Reproduce review/assignment/calendar behavior with one supported candidate in the app.
- [x] Implement an accepted-task to-do view that includes undated work; retain dated calendar placement. Native acceptance gate remains open.
- [x] Define owner mapping and confirmation behavior. Names remain suggestions until confirmed; account mapping is explicit and deadlines optional. Native acceptance remains open.
- [ ] Verify approval, owner selection, date editing, completion, undo, and refresh/relaunch persistence.
- [ ] Verify project invitations and a non-member's access denial using separate accounts.
- [ ] Fix the earliest blocking UI/API failure, add a meaningful regression check, and repeat the same native action.

**Gate:** A real uploaded meeting produces an evidence-reviewed assigned task, visible in the appropriate user's to-do view and calendar when dated. State changes persist. Record screenshots, commit, backend settings, and actual results in the [walkthrough](../evidence/demo_walkthrough.md).

## Stage 3: implement bounded continuity and follow-through

**Aim: October 16-20. Proposed lead: Will; Bryan evaluates; Guadalupe reviews evidence.**

- [ ] Start with failing tests for a new commitment, duplicate mention, supported deadline update, explicit completion, ambiguous match, and unmentioned task remaining unchanged.
- [x] Implement reviewed reconciliation with stable identity and evidence/audit history. Scripted native evidence exists; real-sequence acceptance remains open.
- [ ] Test user-marked completion against later meetings; avoid accidental reopening or unsupported completion.
- [x] Define the narrow experimental approval policy; see [follow-through](follow_through.md#automatic-approval). Calibration and natural-data acceptance remain open.
- [ ] Implement the bounded reminder lifecycle: schedule, reschedule, completion/cancellation, and retry deduplication.
- [ ] Use a controlled clock and notification sink first; verify recipient/content/timing before live delivery to consenting test accounts.
- [ ] Process the frozen sequence from a fresh disposable project and compare state after each meeting to the ledger.

**Gate:** The bounded sequence maintains one task through supported changes, preserves ambiguous cases for review, and cancels/replaces reminders correctly. Report missing behavior as a central limitation if this gate cannot be achieved; do not substitute a similarity flag or one-time reminder export.

## Stage 4: evaluate model and retrieval behavior

**Aim: October 20-22. Proposed lead: Bryan; second reviewer: Guadalupe/Will.**

- [ ] Run Milestone 2 extraction regressions.
- [ ] Compare baseline independent extraction and updated reconciliation on identical frozen transcripts/settings.
- [ ] Measure state accuracy, duplicate creation, incorrect assignments/updates, unsupported completions, and unresolved cases with denominators.
- [ ] Compare dense-only and hybrid retrieval on identical questions, corpus, K, prompt, and answer model.
- [ ] Measure retrieval Recall@K, answer correctness, citation support, refusal/isolation errors, latency, tokens, and estimated cost.
- [ ] Review representative successes/failures and disagreements. Do not treat a valid quotation as sufficient answer support.
- [ ] Run audio-to-app tests separately from transcript-only comparisons to expose ASR/persistence/UI errors.
- [ ] Disclose prior IS1009a/ES2004a ASR exposure; select fresh data before claiming untouched held-out evaluation.

**Gate:** Saved inputs/outputs and exact configuration reproduce the reported comparisons. Findings include failures and limits, not only favorable examples.

## Stage 5: validate availability and external alpha

**Aim: next joint meeting for worker recovery; October 22-24 for alpha acceptance. Proposed lead: team.**

- [ ] Will configures shared mode following [the guide](../reference/shared_backend.md); match code/migrations/storage/settings and use distinct worker IDs.
- [ ] Run abrupt worker-loss recovery in both directions on disposable data. Check one published result, expired-lease reclaim, and surviving API access through a manual URL switch.
- [ ] Verify Google sign-in for an external tester account; identify any Google audience/test-user restrictions before inviting testers.
- [ ] Provide a reachable backend during the agreed test window. A laptop tmux session is not always-on hosting or automatic API failover.
- [ ] Run the native walkthrough: upload, inspect, assign/review, to-do/calendar, reminders, later update/completion, cited answer, refusal, isolation, relaunch, and purge.
- [ ] Record tester feedback, task success/failure, and fixes. Confirm required tester count from the course rubric.
- [ ] Verify clean installation and deletion of both private audio and associated database records.

**Gate:** Documented native evidence and external feedback support the alpha claims. Worker recovery, manual endpoint switching, and automatic routing are reported separately.

## Stage 6: freeze and submit

**Aim: October 24-26. Proposed lead: team.**

- [ ] Reconcile implementation checkboxes with acceptance evidence; leave unverified claims open.
- [ ] Complete each member's extension write-up and measured contribution, human-review log, Model Card, and System Card.
- [ ] Run required Python checks and Swift build on the final submission commit; record warnings/limitations.
- [ ] Record reproduction commands, model/provider versions, settings, dataset provenance, and demo evidence.
- [ ] Update the submission draft around final behavior and remaining gaps.
- [ ] Export and visually review the final PDF; confirm deadline, submission requirements, and separate reflection survey.

**Gate:** Every result is traceable to evidence and the submission commit. Unfinished central functionality is explicitly disclosed.

## Shared-backend coordination

Before the next joint meeting, Will pulls the checkpoint and follows [shared-mode setup](../reference/shared_backend.md), using `will-mac`; Bryan uses `bryan-mac`. Match database/storage, migrations, code, and compatible processing settings. Existing local mode remains available, but must not be mixed with shared mode behind a shared endpoint.

At the joint meeting, both hosts stay awake/online. Bryan supplies a disposable recording and checks job/output state. Will starts/stops his server and checks logs. Identify the claiming worker, stop it abruptly during processing, verify the other reclaims the expired lease and publishes one result, restart the stopped host, and repeat in the opposite direction. Normal Ctrl-C waits for in-flight processing, so it does not demonstrate abrupt recovery. Manually switch the app URL to test the surviving API. Live two-host recovery and automatic routing remain unverified.

## Next phase after Milestone 3

The [archived implementation checklist](../archive/checklist.md) preserves the
old inventory. Its unchecked items are not automatically new milestone gates:

- **Keep in current acceptance:** a short, human-verified audio/transcript fixture,
  a separate-project isolation case, and reproducible run evidence. If claiming
  diarization/voice quality, measure DER, false matches, unknown-speaker abstention,
  and downstream ownership on reviewed audio; implementation alone is insufficient.
- **Retain as later product/data-quality work:** persisted audio duration,
  playhead highlighting, storylines, summary editing/formatted sharing, project
  images, deadline highlighting, calendar attendee/event integration, and redaction.
  These details remain in the historical inventory; the table below sets boundaries.
- **Design options, not required rewrites:** WebSocket progress instead of current
  polling, populating the unused legacy transcript-vector column instead of
  `rag_chunks`, and unifying preview-only task statuses. Decide separately whether
  to retire local JSON processing and migrate its recordings safely.

| Work | Boundary and reason |
| --- | --- |
| Broad automatic task assignment and follow-up | Expand beyond the bounded evaluated path only after measuring harmful assignments/updates and defining user controls |
| Direct Zoom/Teams/calendar ingestion | Current alpha imports recordings manually; provider ingestion needs separate permissions, consent, retries, and provenance |
| Production availability | Always-on hosting, health-based API routing, automatic restarts, monitoring, and operational ownership; tmux cannot keep a sleeping laptop available |
| Wider continuity and personalization | More projects, speakers, ambiguous references, multilingual recordings, and longer histories require broader labeled evaluation |
| Speaker recognition calibration | Separate calibration/evaluation audio and measure false matches/abstention before relying on names for automatic ownership |
| Playback and product polish | Full playback/physical-device acceptance, storylines, summary editing/sharing, and accessibility acceptance |
| Privacy and release readiness | Selective redaction, participant-level controls, verified deletion, public privacy/support pages, and App Store readiness |

Deferral is a scope proposal, not permission to omit an explicit rubric requirement. Revisit it with the team when the reviewed corpus and acceptance results expose what is achievable.

## Zoom proposal

Following the professor's Zoom/CCB discussion, explore authorized summary/transcript
ingestion into the existing project/task backend while retaining the standalone
mobile app. A background account integration could precede an interface inside
Zoom. As of October 19, the app implements a manual **Import Zoom Summary** path
with a solo-test example, document provenance, review-only task proposals, and
idempotent imports by project/meeting instance. This is not an account connection,
webhook subscription, or live-call integration. Account access and a real Zoom
artifact still need validation. Confirm CCB/host permission and available
account/artifact access before automated ingestion. Evaluate
Zoom-summary inputs separately from the audio pipeline. The original exploratory
note remains local-only in `contexts/zoom_integration_direction.md`.

For the test procedure and limits, see [Zoom summary test](follow_through.md#zoom-summary-test).

## Execution rule

For each change, reproduce user-visible behavior, state the expected result,
implement the smallest robust fix, run relevant regression checks, repeat the
native action, and record evidence. Preserve baseline outputs and keep seeded
workflow tests separate from natural-meeting quality. Implementation checkboxes
never close an acceptance gate by themselves.
