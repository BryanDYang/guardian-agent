# Milestone 3 execution roadmap

Updated October 11, 2026. Target submission: October 26, subject to confirming Canvas. Stage order is the execution plan; proposed owners and dates need team agreement. See [scope and acceptance](scope_and_acceptance.md) for product boundaries and [submission draft](submission_draft.md) for rubric requirements.

## October 11 checkpoint

Implemented speaker-name proposals with timestamped evidence and optional confirmed account mapping, accepted undated tasks with a native To-do/Calendar switch, and human-confirmed reconciliation against an earlier accepted task. Reconciliation keeps the original task ID, records the source meeting/quote/reviewer, rejects stale changes, and cannot reopen completed work. Similarity never applies an update automatically. A candidate must already exist; completion-only statements are not yet extracted as update proposals.

All 282 backend tests passed on disposable PostgreSQL; Ruff and the simulator build passed. All seven shared development jobs completed before the backend was restarted. Native acceptance results belong in the walkthrough. Implementation does not close the Stage 2 or Stage 3 gates on its own.

Still required: reviewed sequence ledger and independent adjudication, automatic update proposals, reminder lifecycle and deduplication, paired extraction/retrieval evaluations, real audio-to-task native acceptance, external testers, two-host recovery, and final submission evidence. No natural-data accuracy or completion percentage is claimed from these tests.

## Native inspection follow-up

A separate, versioned scripted fixture exercised account assignment, undated
approval, To-do visibility, completion/undo, reviewed repeated mentions, a
deadline change visible in Calendar, explicit completion, and persistence after
relaunch. PostgreSQL retained one accepted task ID and three evidence audits.
The native run exposed an obsolete Undo token after reviewed completion; the
client now clears that token on a newer server revision, and native Undo passed.
Date/list-status/loading/empty-state fixes and task review/edit auditing are
implemented. All 283 backend tests, Ruff, and the simulator build passed. This
text-only fixture uses seeded candidates, including completion. It closes the
scripted UI path, not real extraction, audio playback, or the full native gate.
See the walkthrough for evidence and limitations.

## Starting point

Shared-mode backend, authenticated native uploads, Google sign-in, project membership, extraction, task review/lifecycle, and cited chat are implemented. Seven AMI meetings completed processing and produced 69 pending candidates at the last inspection. No candidates were approved. The calendar therefore remained empty. Targeted backend tests passed (29), lint passed, and simulator builds passed. Full native acceptance, live two-host recovery, external tester access, sequence accuracy, and automatic follow-through remain unverified.

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

**Gate:** A real uploaded meeting produces an evidence-reviewed assigned task, visible in the appropriate user's to-do view and calendar when dated. State changes persist. Record screenshots, commit, backend settings, and actual results in the [walkthrough](../demo_walkthrough.md).

## Stage 3: implement bounded continuity and follow-through

**Aim: October 16-20. Proposed lead: Will; Bryan evaluates; Guadalupe reviews evidence.**

- [ ] Start with failing tests for a new commitment, duplicate mention, supported deadline update, explicit completion, ambiguous match, and unmentioned task remaining unchanged.
- [ ] Implement reviewed reconciliation with stable task identity and evidence/audit history. Similarity alone must not authorize an update.
- [ ] Test user-marked completion against later meetings; avoid accidental reopening or unsupported completion.
- [ ] Define the alpha's automation policy: what can proceed automatically and what requires confirmation. Record the policy alongside the evaluation settings.
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

- [ ] Will configures shared mode following [the guide](../shared_backend.md); match code/migrations/storage/settings and use distinct worker IDs.
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

## How to execute work

For each item: reproduce the current behavior, state the expected outcome, implement the smallest robust change, run relevant regression/integration checks, validate in the app when user-facing, and record the result. Do not mark acceptance complete from code existence alone. Keep test projects separate from evaluation inputs and do not overwrite baseline outputs.

**Start now:** inspect TS3005a's results, review one evidence-supported candidate through approval/calendar, and build the reviewed sequence ledger. Those steps reveal real defects and prevent implementing automation against guessed expectations.

Automatic API routing, broad unsupervised assignment/follow-up, direct Zoom/Teams ingestion, production hosting, and broader voice calibration remain next-phase work unless the team explicitly promotes them into scope. See [next-phase boundaries](scope_and_acceptance.md#next-phase-after-milestone-3).
