# UI demo walkthrough

Start from the story we want to demonstrate, perform it in the iOS UI, and use failures to choose the next implementation work. Repository checkboxes track implementation only. A successful build, API health check, or scripted backend response does not establish that the corresponding UI journey works.


## Milestone 3 product demo: a research team remembers and follows through

Prepared October 21, 2026. **Planned story, not executed acceptance.** Aim for a
4-5 minute presentation after rehearsing the real app path. The audience should
understand the team's problem and outcome; A-F test cases remain evidence in the
background. Use the [test script](../archive/milestone_3/follow_through.md#clean-app-journey-screen-recording)
for detailed controls and [result.md](result.md) to record observations.

**Story:** A small research team discussed how to start a pilot. At its next
check-in, Bryan volunteers to prepare an interview guide. LabSync captures the
meeting, proposes supported work, connects that work to a confirmed account,
and retains the decision history so the team can ask why it chose this plan.
The organizer should not have to reconstruct every action item from memory.

**Opening narration:** “Meeting notes tell us what people said. We also need to
know what happens next, who owns it, and why we made the decision. Here is one
research project across two short meetings.”

### Prepare the story once

Use a fresh server project `Cedar Research Pilot - [RUN_DATE]`. Keep existing
AMI and October 20 test projects intact. Existing audio remains valid for those
checks and human review; these two optional short clips provide a coherent demo
scenario, not replacements for the test recordings. Label the clips as synthetic
and consented. Record only the quoted words, not the narration or headings.

- Clip 1 is the earlier meeting, processed before the presentation. Its real
  recording date must be used, even if both clips are recorded the same day.
  Names “Kickoff” and “Check-in” describe their intended sequence; do not invent
  historical recording dates. If titles cannot be edited, note timestamped titles
  in the run log and point to the right recording on screen.
- Clip 2 is the check-in: record/upload it in the app during the demo, or show
  the actual recorded upload sequence with a clearly labeled processing-time cut.
  A completed preprocessed result alone is not end-to-end upload evidence.
- Use capture delivery. Verify email automation, auto-approval, and the recipient
  preference are on before Clip 2. Confirm the correct speaker/account when
  reviewing results. Clear undated commitments are eligible for the bounded
  policy; dated commitments can remain pending and are not this story's main path.
- Verify both recordings and actual chat outputs in rehearsal. Save unexpected
  output and errors. Three model timeouts in the AMI diagnostic mean processing
  availability is a real risk; do not promise instant completion or invent results.

**Clip 1: Kickoff, about 20 seconds**

> This is a consented example meeting for the Cedar research pilot. We decided to start with three individual interviews before considering a larger survey. The reason is to learn which questions people find confusing before recruiting more participants. We have not approved a budget amount.

**Clip 2: Check-in, about 15 seconds**

> This is a consented Cedar research pilot check-in. I am Bryan Yang. I will prepare the interview guide. The guide will cover participants' current workflow and the problems they encounter. I might also prepare a survey if we need one, but I am not committing to that yet.

Do not assign an expected pass before processing. The conditional survey may
appear as a pending suggestion; it must not become an approved promise. Read
only the script; do not deliberately announce completion or a deadline that the
main demo does not exercise.

### Presentation sequence

| Beat | What to show in the app | Suggested narration and honest boundary |
| --- | --- | --- |
| 1. A real team context, 20 s | Meetings > Cedar project > existing Kickoff recording | “We agreed to start small. That decision is already part of this project's history.” This is a previously processed example, not a live result. |
| 2. Capture the next meeting, 30-45 s plus actual processing | Project + > record Clip 2 > preview > consent/upload; show processing, then completed result | “At the next check-in I volunteer for the guide. The app records and processes the meeting.” Preserve actual waiting/error evidence; disclose edits in the presentation copy. |
| 3. Show what the AI understood, 30 s | Summary and the relevant Transcript passage; open/play its timestamp | “Here is the commitment and its source. We can check what was actually said.” Confirm the guide is present and the tentative survey is not treated as a promise. |
| 4. Connect speech to a person, 30 s | Review speaker names and confirm/connect Bryan's cluster to the actual signed-in member | “A speaker label alone is not an email recipient. I confirm who this person is.” This is a human mapping, not proof of automatic recognition. |
| 5. Move from conversation to work, 30 s | Tasks > To-do: the interview-guide task, evidence, and owner; project Follow-through > refresh > one captured email preview | “A clear commitment can become assigned work after confirmation without the organizer approving every task. This preview is captured for testing; it has not been sent to a real inbox.” If it remains pending, show the actual gate and manual review; do not claim automatic approval passed. |
| 6. Recall the reason, 45-60 s | Chat scope: Cedar project, All meetings. Ask the two supported questions below; open the relevant citation | “We can recover both the next action and the earlier reason, with sources across this project's meetings.” Verify actual answers and citation destinations. |
| 7. Show a boundary, 20 s | Ask the budget question below in the same scope | “The app should admit when the meeting history doesn't establish an answer.” A made-up amount is a failure, not a line to skip. |
| 8. Close the loop, 20-30 s | Relaunch and show the task and saved chat; optionally mark the guide complete as a user action | “The work and its context survive the meeting. I can update the task as I finish it.” User-marked completion is not automatic completion inference. |

Type these questions verbatim, then preserve the actual responses:

1. `What did Bryan commit to prepare, and what should it cover?`
2. `Why did we decide to start with three interviews before a larger survey?`
3. `What exact budget amount was approved for Cedar?`

For question 2, a useful answer should locate Kickoff's reason rather than
invent a rationale from the later task. The expected budget boundary is that
no amount was approved; a grounded statement of that fact or refusal is
acceptable. Literal quote validation alone does not prove answer support.
These rehearsed questions are demo checks, not a new held-out evaluation set.

**Closing narration:** “The value is continuity from conversation to owned work
and back to the evidence behind it. The current alpha still needs stronger date
resolution, completion inference, and real inbox/reminder validation. We have
recorded those gaps alongside the working paths.”

### Optional detail, outside the main story

- **Calendar:** edit the accepted guide task to a chosen future date manually,
  then show its Calendar placement. Say explicitly that the date was entered
  manually. The already-captured email is a one-time original follow-up; date
  edits do not establish an updated email or reminder rescheduling.
- **Update/completion:** demonstrate reviewed repeat reconciliation or manual
  completion only if time permits. Automatic completion inference is a known gap.
- **Zoom:** briefly mention the implemented manual summary-import option if
  relevant to the professor's suggestion. Do not show or claim an unimplemented
  live Zoom connection/webhook path.
- Keep login/setup, repeated settings screens, negative-case permutations,
  abrupt worker recovery, and detailed metrics for an appendix or questions.
  They remain separate acceptance/evaluation work; a short story does not waive them.

### Rehearsal and evidence gate

This story has **not run**. Before presenting it as a working demo, use a fresh
run record, check the displayed outputs/citations, confirm one captured follow-up,
and verify relaunch persistence. Stop and document the earliest blocking failure.
Keep original audio/video locally or in the restricted team evidence location,
with sanitized observed outcomes in a new dated section of this walkthrough.
Do not reset or relabel an older accepted task to make a clean run appear to pass.

## Record each run

Record the commit, device/iOS version, backend URL (no keys), date, project and meeting names, screenshots, and observed results. Use **Passed**, **Failed**, **Blocked**, or **Not run** for each step. Mark Passed only after performing the action and observing its result. A local fixture run and a connected backend run are separate evidence.

## Demo story and acceptance criteria

This is the initial checklist, retained as historical context. Dated observations
below supersede its original Not run/Reported entries; it is not a current status
dashboard. Use the Milestone 3 roadmap for today's open gates.

Use a real server project with at least two completed recordings and a second project for the scope check. Choose a question whose answer and source timestamp you can verify in the transcript, plus an unsupported question. Obtain recording consent before uploading.

| Step | UI action | Expected result | Latest evidence |
| --- | --- | --- | --- |
| 1 | Launch and enter the app | Identify placeholder login honestly; it does not establish a real account or isolated user data | Not run |
| 2 | Open Meetings | Server projects appear; local sample projects are clearly identified | Reported failure: sample projects looked like real projects |
| 3 | Create a project and upload a recording with consent | Processing completes; the recording appears under the intended project | Not run |
| 4 | Open the completed meeting | Summary, transcript, decisions, and candidates match the uploaded recording | Not run |
| 5 | Open Chat before opening every project detail | Project picker distinguishes samples; selecting a server project loads its meetings directly | Reported gap: Chat relied on meetings previously cached by Meetings |
| 6 | Select a project and open the meeting selector | Completed meetings can be selected; unfinished meetings are visible but unavailable; All meetings is explicitly scoped to this project | Not run |
| 7 | Ask the supported question across the project's meetings | Answer includes a citation to the correct meeting and timestamp; verify its wording against the transcript | Not run |
| 8 | Select one meeting and ask again | New conversation uses only the selected meeting | Not run |
| 9 | Ask the unsupported question | Honest refusal without invented evidence | Not run |
| 10 | Switch to the second project and ask about the first | No evidence from the first project is returned | Not run |
| 11 | Open history, relaunch, and reopen the thread | Saved messages and their original project/meeting scope survive | Not run |
| 12 | Approve a candidate with a due date, then open Tasks | Approved task appears on the correct date; done and undo persist after refresh | Not run |
| 13 | Disconnect the backend and open Chat | Refresh failure is visible; retry recovers after reconnection | Not run |

## Work backward from failures

Fix the earliest failing step needed for the story, repeat that step in the UI, then continue the walkthrough. Keep unverified rows marked Not run. Do not fill missing behavior with sample content or silently treat another API request as UI evidence.

Playback/seek, per-attendee storylines, real login, voice identity, and cross-project search are outside this initial demo's verified claims. Add acceptance steps before presenting them as working.

## October 10, 2026 partial native run

Device: iPhone 18 Pro Max simulator, iOS 27.0. Backend: `http://127.0.0.1:8000`, shared mode, MLX Whisper base, without diarization. The repository checkpoint commit records this implementation; no complete walkthrough video was recorded.

- **Passed:** Signed-in Google account reached the main app; created real server projects; projects appeared after relaunch. This is not a clean-install or second-user authorization check.
- **Passed:** Native file selection and permission confirmation submitted all seven AMI recordings to their assigned projects. PostgreSQL contained all seven durable jobs. TS3005a/b completed at the checkpoint; remaining jobs were running/queued.
- **Observed failure and recovery:** The larger TS3005b WAV returned a Storage error. A smaller lossless FLAC retry succeeded. FLAC copies were checked sample-for-sample against originals.
- **Passed:** Reproduced Profile using a white canvas while other tabs were dark; rebuilt with adaptive colors and visually checked light/dark modes.
- **Not run:** Inspect complete outputs, approve/update tasks, verify continuity, supported/unsupported chat and citations, isolation, purge, and complete persistence journey.
- **Not run:** Two-device worker failover, automatic API routing, and external tester availability.

Corpus mapping and local operating commands are in [the shared backend guide](../reference/shared_backend.md). Current meeting dates are import dates, not verified corpus dates.

## Playback implementation follow-up

Reproduced the inert Play button and placeholder 14:32/30:40 times on TS3005a. Replaced the static dock with AVPlayer, authenticated audio download, real duration/position, pause, +/-15 seconds, scrubber, loading/error/retry states, and temporary-file cleanup on leaving the meeting. Transcript and decision timestamps seek and play; task/chat citation navigation seeks without automatically playing. Long transcript rows now load lazily.

Observed on the simulator: protected TS3005a WAV loaded with duration 21:58; tapping decision 03:59 moved playback there and displayed Pause; elapsed time advanced to 04:26; pause worked. This verifies player progression, not subjective speaker-volume or output-device audibility. TS3005b FLAC loaded with duration 40:39; tapping decision 20:05 started playback and advanced to 20:08. On the transcript tab, tapping 00:17 moved playback near that position and advanced to 00:22. Pause was verified and the recording was left paused. Slider dragging, retry failures, and physical-device audibility still require acceptance checks.

## Speaker processing checkpoint

Diarization is now the default for CLI transcription and server processing, with
`--no-diarize` as an explicit opt-out. The existing TS3005a-d development meetings
remain completed outputs from the earlier run without diarization. Reprocessing
was not queued: Bryan's environment has neither `HF_TOKEN` nor a cached Hugging
Face login. Dependencies are installed; model access must be configured and the
worker restarted before verifying TS3005a and then processing b-d. Name inference
from introductions is not implemented, and Storyline detail still contains
placeholder content. Neither is accepted end-to-end behavior.

The larger centered playback controls built successfully and were inspected in
the simulator; TS3005a loaded its real 21:58 duration.

## Live diarization reprocessing

Hugging Face access to both gated models was verified and the pipeline loaded
successfully. Restarted the idle shared worker and requeued TS3005a with its saved
job settings explicitly changed to enable diarization. The run completed with
six speaker clusters and nine unassigned turns. This is a successful processing
run, not verified speaker accuracy; compare against corpus annotations before
using the clusters as identities. No development tasks had been reviewed. Previous
job/result snapshots were preserved in the gitignored
`artifacts/dev-reprocess-backup-20261010.json`. TS3005b-d were then queued in order
with diarization enabled; their final acceptance is pending.

Reproduced a stale-cache issue in the native app: the completed reprocessed
meeting still showed one unknown speaker because stored turns only populated an
empty local transcript. Updated the refresh path to replace stored turns and
reuse existing speaker attendees. Simulator build passed. Reopening TS3005a
showed its new summary and six anonymous speaker cards plus the unknown group
on Storyline. Storyline detail still contains placeholders.

## Speaker naming and task-owner review implementation

The app now exposes speaker-name review from Tasks, Transcript, and Storyline.
The API proposes names only from conservative direct self-introductions in
English, with the source quote and timestamp. Suggestions remain unverified ASR
text until a project member confirms or corrects them. General name mentions do
not establish identity; conflicting introductions remain visible for review.
Names outside this parser's coverage can be entered manually. No account is
chosen from a name alone.

A reviewer can optionally connect the speaker to an existing project member.
Pending commitments already owned by that speaker then receive the confirmed
account assignment automatically. Existing account assignments and reviewed
tasks remain unchanged. This does not automatically approve a task, invent a
deadline, or recognize the participant in a later recording. Enrolled-member
voice matching continues assigning recognized owners through the existing
pipeline. Speaker reviews are audited in meeting model metadata; reprocessing
keeps review history but invalidates the old cluster mapping.

Task cards display the evidence quote, provide owner/account review actions, and
play their timestamp in place instead of switching to the transcript. Storyline's
hardcoded perspective text has been replaced with an explicit unavailable state.
A real speaker-specific storyline is still not implemented.

Simulator build, lint, formatting, and all 282 tests passed against disposable
local PostgreSQL. All seven shared development jobs completed. The idle backend
was restarted with the updated routes, and the new build installed without
resetting app data. Native confirmation and task persistence acceptance remain
open until explicitly recorded below.

### October 11 task-loop and continuity checkpoint

Authenticated API regression tests verify undated approval, absence from the
calendar, visibility in accepted tasks, completion/undo, adding/clearing a date,
and outsider denial. Reviewed reconciliation tests preserve a stable task through
a repeated mention, changed deadline, or completion; exact quote evidence and a
current task revision are mandatory. Repeated requests, stale reviews, and changes
to user-completed work are rejected. These tests use scripted disposable data,
not a human-reviewed AMI sequence or a measure of model accuracy.

The native app exposes To-do and Calendar views, optional deadlines in task edits,
and Review task update on candidate cards. The reconciliation screen requires a
selected existing task and explicit evidence confirmation. Completion-only
utterances are not yet extracted as update candidates. Reminder lifecycle and
automatic reconciliation remain unfinished.

AMI annotation inspection found gaps where several introduction names would
appear. Those annotations cannot validate the ASR name spellings. The app keeps
the suggestions unconfirmed; do not connect corpus participants to Bryan's
account merely because it is the only available account.

Native inspection on October 11 verified the installed speaker-review sheet
loads introduction suggestions, leaves account connections unset, and exposes
Listen/Pause controls. Playing Danny's suggested introduction moved the main
player to about 03:12; it was paused at 03:19. No guessed name was confirmed.
The Tasks tab displayed the new To-do/Calendar switch and an accurate empty
accepted-task state. Full approval/edit/complete/relaunch and reconciliation
acceptance are still open. Physical-device audibility remains unverified.

## October 11 scripted native task continuity inspection

Used a separate **M3 Scripted Acceptance - Oct 11** project with the versioned
`tests/fixtures/continuity/native_sequence.json`. Four completed text-only meetings
and their pending review candidates were seeded deliberately through existing
persistence functions. This is a native workflow fixture, not audio-to-app or
model extraction evidence. It includes a seeded completion candidate because
completion-only update extraction is still missing. AMI projects were unchanged.

Observed in the simulator, beginning on `e7399c8` and finishing on the local follow-up build:

- Assigned the initial fixture task explicitly to Bryan, with no deadline.
- Approved it; it appeared in To-do. Completed it, then used Undo to reopen it.
- Opened the second meeting's **Update an existing task** action, selected the
  original task, confirmed the quoted repeated mention, and applied the review.
- The database retained the original accepted task ID and dismissed the later
  candidate. The reconciliation audit retained quote, meeting/turn, timestamp,
  operation, policy, and actor. No second accepted task was created.
- In the third meeting, confirmed the quoted deadline as October 16. The same
  task appeared on October 16 in Calendar, with its owner preserved.
- In the fourth meeting, confirmed explicit completion. The task appeared under
  Completed and persisted after relaunch, without a second accepted task.
- PostgreSQL retained one approved task and three dismissed later candidates.
  The three reconciliation audits contain the exact quotes and reviewer.
- Undo after reviewed completion initially failed because the client retained an
  obsolete lifecycle token. The fix associates the token with the server revision,
  clearing it when a newer revision arrives. Native Undo then reopened the task.
  After a new manual completion and relaunch, Undo used the valid audit token
  successfully (verified as REVERT in PostgreSQL). The fixture was left done.
- The seeded text-only meetings have no recording; their audio-unavailable error
  is expected and not playback proof. Completion-only extraction remains open.

Inspection exposed a calendar-day shift west of UTC, completed cards labeled
Processing until opened, stale mandatory-deadline guidance, and an empty-state
message incorrectly claiming nothing was extracted after approval. Fixes are
implemented; the simulator build passed. The exact date helper preserved October
11 in America/Los_Angeles and Pacific/Kiritimati checks. The resumed native inspection verified correct meeting dates, Processed status,
updated approval guidance, and the No pending tasks state. A loading indicator now distinguishes
fetching tasks from an empty review queue, and continuity review has a Pause
control for evidence playback.

Review and detail edits now append actor/old/new snapshots to the task audit.
Only lifecycle audit entries support Undo, and a later detail edit prevents an
old undo token from discarding that edit. Targeted API regressions passed (23).

Final verification for this follow-up: all 283 backend tests, Ruff lint/format,
and the simulator build passed. The updated simulator build was installed and
relaunched with cached account/task data preserved. The idle backend was restarted
only after checking that no queued/running jobs remained; the continuity route
was reachable afterward. The resumed scripted native sequence passed through
deadline change, completion, and relaunch. The follow-up simulator build also
passed with the undo-token cache fix and preserved existing app data during
installation. Real audio-to-task acceptance, physical audibility, independent
labels, and model-quality evaluation remain open. This follow-up is documented
alongside its implementation and versioned fixture in the repository.
# October 17 simulator OAuth signing repair

Google sign-in displayed "invalid request: both auth code and code verifier
should be non-empty" after the unsigned simulator installation. Simulator
security logs showed `-34018`: the app lacked application-identifier/Keychain
entitlements. Rebuilt with simulator code signing enabled and ad-hoc identity;
verified the embedded simulated application identity and reinstalled/relaunched
without clearing app data. A disposable non-secret Keychain entry was written,
read, and deleted inside the running app; all three operations returned success.
The entry was removed and the debugger detached. No real credentials were read.
This verifies the storage repair; a fresh user Google sign-in still needs to
complete to establish end-to-end OAuth acceptance. Keep signing enabled for
future simulator acceptance builds; do not bypass PKCE or replace Keychain.

## October 18 user-reported AMI walkthrough

Historical October 10 inspection: all seven AMI jobs completed with 69 pending
candidates and zero approved tasks; the calendar was therefore empty. This is
the earlier baseline, not the October 18 task count.

Bryan supplied simulator screenshots of accepted AMI tasks in To-do, including
TS3005d's quoted minutes commitment, and the Follow-through sheet with email and
automatic-approval controls enabled. The Test inbox showed no follow-ups. These
are user-reported UI observations; no new database audit or scored a-d sequence
was performed in this documentation session. The screenshot files were supplied
through temporary conversation attachments and have not been added as permanent
repository artifacts.

The existing tasks still show anonymous corpus speakers. Those participants are
not the signed-in account, and speaker mapping does not retrospectively change
approved assignments. Enabling email does not bulk-send old work. A separate
personal recording will be used for truthful identity/account and follow-up
acceptance, using the [dated read-aloud scripts](../archive/milestone_3/follow_through.md#personal-recording-test-scripts).
The recording, captured-message result, and real inbox test remain pending.

## October 19 Zoom summary import verification

- Added manual **Add Meeting > Import Zoom Summary**, with a synthetic solo
  example and a separate summary-specific extraction prompt. This does not
  connect a Zoom account, join calls, or subscribe to summary webhooks.
- Signed simulator build succeeded and was installed/launched. The development
  shared backend was restarted with no active processing meetings; health
  returned `ok`, and OpenAPI exposes `/api/v1/meetings/zoom-summary`.
- 62 relevant tests passed against the isolated local PostgreSQL regression
  database, with offline model/embedding substitutes. They cover summary
  provenance, exact evidence without playback timestamps, access/consent,
  idempotent retries, changed-content conflicts, atomic failures, task approval
  to captured email, and existing chat/shared-backend behavior.
- A real Codex model run on synthetic text proposed both expected assignments
  with validated document quotes in 4.331 seconds. A subsequent prompt refinement
  asks for action-only titles. Live rechecks then failed with provider HTTP 429
  (`Too Many Requests`), despite an authenticated CLI. No repeated retries or
  fabricated success were used. Resume live processing checks after rate limits
  clear; this one sample is not an extraction-quality evaluation.
- Native form interaction/visual acceptance and an actual authorized Zoom
  summary are still unverified. Desktop UI control is unavailable in this
  session. No real email was sent, and recurring reminders remain unfinished.
- Final pre-commit verification: all 314 backend tests passed against the local
  regression database after adding the Zoom endpoint to mandatory route-isolation
  coverage. Ruff lint/format checks and the signed simulator build passed. Two
  existing dependency deprecation warnings remain.

Use the existing [Zoom summary test](../archive/milestone_3/follow_through.md#zoom-summary-test)
to record the human walkthrough and keep it separate from audio test results.

## October 20 Codex CLI failure and recording recovery

Reproduced the failed D recording through the simulator: the Tasks screen showed
`Processing failed`, with the original audio still playable. Backend logs showed
successful Whisper transcription and one detected speaker, followed by failed
Codex extraction. Both the five-hour and weekly subscription allowances had
remaining capacity. A tiny synthetic request with Homebrew CLI 0.157.1 returned
HTTP 429; the same account, requested `gpt-5.6-sol` model, and structured request
completed with the official desktop-bundled CLI 0.163.0-alpha.10.2. The exact
upstream reason for the older runtime's rejection is not established.

Added host-specific `LABSYNC_CODEX_CLI` selection for availability checks,
inference, and version reporting. Configured the private local `.env` to use the
working bundled executable and restarted the idle shared backend. No credentials,
provider, model, subscription, or API billing configuration were changed.
The normal LabSync synthetic extraction command then completed in 4.876 seconds
with one decision and one commitment; its local diagnostic artifact is
`artifacts/diagnostics/codex-cli-fix-2026-10-20.json`.

Retried D's original meeting `d9acf3f8-ff26-4294-b64f-8c92f5441406` in the native
app. It completed and visibly showed the pending task **Upload the presentation
slides**, owner **SPEAKER_1**, and evidence **I will upload the presentation slides
tomorrow.** The failure banner disappeared. Calendar date entry and identity
confirmation remain manual checks; this was processing recovery, not completed
follow-through acceptance. No task was approved or emailed during this check.

Retried E's original meeting `56c9dc40-5be3-4808-b62e-a973efb42d8c` as well. It
completed and visibly showed **Review the deployment instructions**, owner
**SPEAKER_1**, with the exact source quote. D and E retained their existing meeting
IDs and were left pending for identity/assignment and scenario-specific review.
E's recipient opt-out behavior has not been tested by this processing recovery.

All 316 backend tests passed against isolated local PostgreSQL, including two
new CLI-selection regressions. Ruff lint and formatting passed. No iOS source
changed in this fix, so the existing signed app was used for the native retry.

## October 20 new-project automation defaults

At Bryan's request, new projects now default both project automation switches
on: task-owner email after approval and bounded automatic approval. Migration
`20261020173744_enable_project_automation_defaults.sql` changes column defaults
only. It does not update existing projects, approve old tasks, enqueue messages,
or change individual recipient preferences or delivery mode.

All 317 backend tests passed on isolated local PostgreSQL. Coverage verifies
new-project API settings, automatic approval only after identity confirmation,
capture delivery, explicit disabling, and persistence of disabled choices when
another project is created. Lint/format checks passed. Applied the migration to
the configured backend and recorded migration history. Compared all existing
project settings before/after and verified no changes. A transactional test
insert confirmed both new-project defaults are true, then was rolled back.
No permanent verification project or follow-up email was created by this check.

The previously created personal test projects retain their saved settings. Check
and save scenario-specific settings before running each test; default changes
do not retrospectively establish that B-positive ran with automation enabled.

## October 20 Done saves follow-through settings

Removed the separate project/preference save buttons. **Done** saves only changed
values and closes after success. Recipient preference is saved before project
automation because enabling automation can immediately evaluate candidates.
Failed saves retain draft switches for retry, and refreshing history no longer
reloads/reset drafts. Unsaved edits cannot be dismissed by swiping; **Cancel**
allows deliberate dismissal without saving remaining edits.

Signed simulator build passed and was installed. Native acceptance used the
existing B-negative project: changed the receive-email preference from on to
off, refreshed history and observed the draft remained off, tapped Done, reopened
the sheet, and observed the saved value was off. Restored the original on value
with Done. Project automation switches were unchanged, no candidates were
approved, and no follow-up messages appeared. This verifies native preference
persistence and refresh behavior; joint-write failure handling was code-reviewed
but not exercised through a forced network outage.

## October 20 personal audio acceptance: 2026-10-20-run-1

Executed the uploaded personal recordings through the signed iPhone simulator
app against the shared backend, using capture delivery and the configured Codex
CLI. The tested implementation was committed as `1d09bc6`, based on `afeaded`. Mutations
were performed through the native app; database reads verified saved state,
audit actions, and outbox counts. These are scripted single-speaker checks, not
natural-meeting accuracy measurements or independent external acceptance.

| Case | Observed result | Qualification |
| --- | --- | --- |
| A | Checklist task approved, visible in To-do, one captured follow-up | Already auto-approved at baseline; audit says `AUTO_APPROVE`. This is not a clean manual-approval A run. |
| B-positive | Enabled both project switches with Done; recording-sharing task auto-approved with one `AUTO_APPROVE` audit and one captured follow-up | No manual approval click. Confirmed account mapping was already present. |
| B-negative | Tentative budget statement remained a pending `advisor_suggestion`, unassigned, with zero messages while automation was enabled | Correct abstention; left pending. |
| C | Manually set October 21, approved the summary task, verified October 21 Calendar entry and one captured follow-up | Spoken date was retained as raw text; structured date was initially empty. Manual date entry passed; automatic parsing did not. |
| D | Turned automatic approval off, manually resolved “tomorrow” from October 20 to October 21, approved slides task, verified Calendar entry and one captured follow-up | Date picker initially offered October 20. Automatic relative-date resolution remains missing. |
| E | Saved project email on and recipient preference off together with Done, then approved deployment task; zero outbox rows | Restored recipient preference on afterward; still zero messages. No retroactive delivery. |
| F1 | Reconciled “same project summary” as a repeated mention of C, dismissing the source candidate without a second accepted task/email | ASR said October 3; Bryan confirmed intended October 23. Extracted quote omitted the deadline. Revised C manually to October 23 using task Edit, rather than asserting the quote supported a deadline update. Calendar moved from October 21 to October 23. |
| F2 | Completion recording yielded no candidate. Manually completed C, used Undo, then completed it again | Native completed state and October 23 Calendar entry persisted after app termination/relaunch. Automatic completion extraction remains unsupported. |

Final read-only verification found four captured messages total across these
projects: A, B-positive, C, and D, each with one delivery attempt. E and B-negative
had zero. C retained its original task ID through repeat reconciliation, date
edit, completion, and Undo. F1's source candidate was dismissed. A/B-positive,
D/E, and completed C were visible in native Tasks after relaunch. The original
October 21 raw extraction text remains provenance; the confirmed due date is
October 23. The one-time captured C email is not a rescheduled reminder or an
updated-deadline email.

The versioned ledger below preserves the detailed states, audit sequence, and
counts for team review. Raw local snapshots and the working results copy are under
`artifacts/follow-through/2026-10-20-run-1/{before.json,after.json,results.md}`.
They are ignored by Git. Original recordings remain in the app/backend; they
were not exported into the empty `artifacts/audio/` directory. UI observations
are in this session; no standalone screen recording was saved by these checks.
Still needed: a clean manual A demo with recorded visual evidence, live inbox
acceptance after sender setup, automatic date/completion improvements, recurring
reminder lifecycle, and the independent AMI a-d review/evaluation.

### Who recorded, who checked, and what was reviewed

Bryan supplied the personal audio recordings and account/speaker mappings.
The assistant executed the native app checks and inspected stored transcripts,
extracted tasks, UI state, audit records, and captured email counts. Bryan
confirmed that F1's intended revised date was October 23, 2026. The assistant
made the documented manual corrections through the app.

This is **assistant-executed integration testing**, not a signed human review
of model quality. A systematic listen-through comparing every recording to its
transcript was not documented; audio/transcript accuracy remains **Not checked**
for that purpose. No independent human reviewer has completed the
[review worksheet](../archive/milestone_3/human_review.md). The worksheet's unfilled
judgments do not mean the app tests were unrun, and the app test passes do not
mean the human review is complete.

The existing audio can be reused for review. Do not re-record the October 20
cases merely to fill a worksheet. The separately planned clean demo is a
**screen recording of an app journey**; its new recording/project is only needed
to demonstrate an uncontaminated manual approval, since A was already approved.

### Versioned run ledger

This ledger is the repository copy of the observed results, derived from the
local before/after snapshots. The tested implementation is commit `1d09bc6`
(on top of `afeaded`); environment: October 20, 2026, America/Los_Angeles,
iPhone 18 Pro Max simulator on iOS 27.0, signed Debug build, shared backend,
Whisper MLX `base`, Codex `gpt-5.6-sol` via CLI `0.163.0-alpha.10.2`, delivery
`capture`. One consenting tester, Bryan, used his account for recipient mapping.
These recordings were already processed before the baseline snapshot, including
D/E's documented recovery. The ledger measures subsequent native review and
follow-through behavior; it does not measure processing latency for each clip.

**Saved state transitions.** Dates below are structured due dates, not raw ASR
text. Project names use `Follow-through Dev - 2026-10-20 - [case]`; C/F1/F2 share
`C-F`. Opaque meeting/task IDs allow the team to locate the same test records
without committing account identifiers, addresses, or message payloads.

| Case | Meeting ID | Task ID | Before | After |
| --- | --- | --- | --- | --- |
| A | `d1369fd6-e347-466b-8979-541cd3875c41` | `7d0b8c92-b1c6-4198-b475-2d8ffc1d7e51` | approved/open; undated | approved/open; undated |
| B-negative | `fd4f6ba2-0f8c-4c06-b831-fa98a759ee30` | `b3c36219-230e-4a74-80c9-16828ac032ce` | pending/open; undated | pending/open; undated |
| B-positive | `25d4d3e7-9b80-4300-aa84-b92d5ab653d0` | `8ed21ec0-d519-457d-8608-25d62d7caa06` | pending/open; undated | approved/open; undated |
| C | `d4e19983-74ff-48f6-aa49-b7501c47af4d` | `e68d6b72-4464-433b-8d6f-92eabb4d9cb2` | pending/open; undated | approved/done; 2026-10-23 |
| F1 | `981df1c6-eb96-4279-9742-329c7f959aa2` | `b928dca5-85ca-414a-9e07-c4eb5865c6a5` | pending/open; undated | dismissed/open; undated |
| F2 | `6762c1c2-fea6-4fa4-83ee-76a615d99ae3` | None | No task | No task |
| D | `d9acf3f8-ff26-4294-b64f-8c92f5441406` | `ca1ec16e-bbb3-4b00-8473-4e59ce47a1ea` | pending/open; undated | approved/open; 2026-10-21 |
| E | `56c9dc40-5be3-4808-b62e-a973efb42d8c` | `546a01c6-c100-42f8-843d-abd87db446e2` | pending/open; undated | approved/open; undated |

**Recorded audit sequence:** A's baseline approval was `AUTO_APPROVE`;
B-positive gained one `AUTO_APPROVE`. E recorded `REVIEW_APPROVE`. C recorded
`REVIEW_EDIT` to October 21, then `REVIEW_APPROVE`, `MEETING_RECONCILIATION`
with operation `duplicate`, `DETAILS_EDIT` to October 23, `STATUS_CHANGE` to
done, `REVERT` to open, and `STATUS_CHANGE` to done again. D recorded
`REVIEW_EDIT` to October 21 followed by `REVIEW_APPROVE`. F1's candidate became
dismissed. F2 had no task to reconcile. These are observed saved audit actions,
not assertions that the model inferred the manual edits.

**Final settings and delivery:**

| Project case | Project email | Auto-approve | Recipient preference | Captured messages | Attempts per message |
| --- | --- | --- | --- | --- | --- |
| A | On | On | On | 1 | 1 |
| B-negative | On | On | On | 0 | N/A |
| B-positive | On | On | On | 1 | 1 |
| C-F | On | On | On | 1 | 1 |
| D | On | Off | On | 1 | 1 |
| E | On | Off | On | 0 | N/A |

E's preference was **off at approval**, then restored on; the final On value
must not be read as the setting used for the opt-out test. The four delivery
rows were all `captured` in `capture` mode. Zero real-inbox deliveries were
tested. Refresh/relaunch and repeat reconciliation did not increase those
counts in the final snapshot; provider retry/failure recovery was not forced
in this native run.

**Acceptance disposition:** B-positive, B-negative abstention, E opt-out, and
the manual date/Calendar, duplicate, completion/Undo, and relaunch checks passed.
A manual approval was not run cleanly. C/D automatic date resolution and F1
automatic deadline revision did not pass. F2 automatic completion is unsupported.
Live inbox delivery, recurring reminders, multi-speaker identity accuracy, and
external testers were not tested here. No standalone screenshot/video files
were produced for this run; record the clean manual A demo separately.

## October 21 AMI retrieval comparison and partial live-answer run

Run: `m3-rag-2026-10-21`. Tester/executor: assistant on Bryan's behalf, with
explicit authorization for these AMI questions/excerpts and the configured
embedding/Codex destinations. No personal recordings or unrelated projects
were used. Baseline checkout: `4048fbb` plus the runner/fixture in this update.
No application database rows or production retrieval defaults were changed.
All 319 backend tests passed after adding scope/dismissal and interruption checks;
Ruff lint/format and diff checks passed.
No iOS source changed, so the October 20 signed build was not rerun.

**Versioned evidence:** [exact questions/proposed targets](../../tests/fixtures/rag/development.json),
[protocol and reproduction command](../../tests/fixtures/rag/README.md),
[machine outputs with retrieved sources, actual prompts, answers, usage, hashes,
and explicit statuses](rag_2026-10-21.json), and
[metrics/cost assumptions/source-loading timings](rag_2026-10-21_summary.json).
Raw corpus vectors, cached query vectors, the pre-interruption-fix runner, and
initial output remain ignored under `artifacts/evaluation/m3-rag-2026-10-21/`.
The measured runner hash is retained; the current runner additionally preserves
interruption status and stops after three failed calls. That control-flow fix
does not change the saved retrieval queries, prompts, rankings, or answers.
AMI source attribution and limits are in the fixture protocol.

### Design and retrieval results

The corpus is the existing 219-chunk TS3005a-d development index. Four positive
questions and two proposed unsupported questions are project-scoped; eight
positive questions are scoped to their specific meeting. Twelve designated
existing decision chunks were chosen before retrieving. These labels are
assistant-proposed from model-generated decisions plus inspected stored quotes,
not independent human gold or an exhaustive inventory of relevant chunks.

Both variants reuse identical 1,536-dimensional `text-embedding-3-small` query
vectors, K=8, corpus snapshot, project/meeting and dismissal filters, source
builder, `project-chat-v2` instructions, empty history, and requested
`gpt-5.6-sol`. Hybrid uses the production sparse/dense RRF implementation,
k=60 and leg depth=40; dense removes that sparse/fusion leg. A REPEATABLE READ,
READ ONLY transaction froze corpus/source state. Each variant/question had three
retrieval timings, alternating which variant ran first. CLI version was
`0.163.0-alpha.10.2`. Exact prompt/corpus/dataset/vector hashes are saved.

| Variant | Designated target Hit@1 | Hit@3 | Hit@8 | Target MRR@8 | Median retrieval round trip (42 samples) |
| --- | --- | --- | --- | --- | --- |
| Dense | 9/12 | 10/12 | 11/12 | 0.7944 | 87.30 ms |
| Hybrid | 4/12 | 7/12 | 11/12 | 0.5188 | 88.31 ms |

This is target recovery, not exhaustive Recall@K or answer accuracy. Both reach
11/12 at K=8 but miss different targets: hybrid recovers the price-decision chunk
missed by dense; dense recovers the rubber-housing decision lost by hybrid.
Dense's price answer still found alternative transcript evidence. Target MRR
alone cannot choose a semantic winner. The approximately 1 ms timing difference
is not evidence of a material speed advantage. Production hybrid stays unchanged
pending broader data and human answer/citation review.

### Answer-run disposition and failures

All 28 retrieval rankings completed. Answer generation is **partial**: 9 completed
answers, 3 calls that timed out at 180 seconds, 1 interrupted in-flight call, and
15 calls not run. All three timed-out calls were dense (`phases`, `style`, `power`).
After the third timeout, the operator interrupted `teletext-b/dense`; its final
provider completion and token consumption are unknown. Other uncompleted cases
are not passes or failures. Both unsupported-question answer pairs were **not
run**, so refusal accuracy is unmeasured. Human correctness/entailment is pending
for every completed output. A nonzero model-call completion count is not a
correct-answer count.

| Variant | Completed answers | Timeouts | Interrupted | Not run | Successful-call median / longest |
| --- | --- | --- | --- | --- | --- |
| Dense | 3 | 3 | 1 | 7 | 108.93 s / 110.83 s |
| Hybrid | 6 | 0 | 0 | 8 | 4.52 s / 7.52 s |

The successful subsets are unequal and exclude timed-out calls. These are
observations of this CLI/service run, not a causal latency claim for retrieval
strategy or an acceptable overall user latency. Upstream timeout causes remain
unknown. Do not average away the three 180-second timeouts or claim zero cost
for failed/interrupted requests with unavailable usage.

One concrete pipeline failure occurred on `lcd/hybrid`: the target decision was
retrieved at rank 4. The raw model response's sole quote prepended `Decision:`
to source text that lacks that prefix. Literal verification rejected the quote
and the application returned its fixed refusal. Across 9 completed calls, 1 of
12 raw citations failed literal validation (hybrid 1/7; dense 0/5). This is not
semantic citation-support scoring. Preserve raw output alongside final output;
review prompt/source-format changes as a later version, not a silent correction
to the frozen experiment.

### Latency, tokens, and estimated cost

These measurements are service components, not mobile end-to-end latency.
Query embedding took 1.825 seconds for one batch of 14 texts. Local
`cl100k_base` counting estimates 206 input tokens, not API-reported usage;
the vectors were reused by both variants. Additional source-loading checks
matched the frozen sources and measured about 0.72-0.88 seconds for price,
LCD, and unsupported-unicorn source sets (three repeats per variant). Source
loading is excluded from retrieval-only and model-only columns.

| Completed-call workload | N | Median model + validation | Mean input / output tokens | Mean observed cached-input tokens | Hypothetical standard API-equivalent per completed call |
| --- | --- | --- | --- | --- | --- |
| Project-scoped supported chat | 6 | 5.082 s | 17,432.17 / 117.17 | 0 | $0.072072 |
| Meeting-scoped supported chat | 3 | 4.955 s | 18,021.33 / 87.33 | 8,874.67 | $0.041883 |

Usage is reported by the CLI and includes its request overhead; do not substitute
these counts for the visible prompt's token count. Both workload cohorts are
selected completed calls; report the timeouts above alongside them. No P95,
concurrency/load benchmark, standalone single-query embedding latency, or native
end-to-end latency was established.

Rates checked October 21 against [official OpenAI pricing](https://developers.openai.com/api/docs/pricing):
standard short-context `gpt-5.6-sol` input $4/M, cached input $0.40/M, output
$20/M; `text-embedding-3-small` $0.02/M input. Estimate per completed answer =
`((input-cached)*4 + cached*0.40 + output*20)/1,000,000`.
For all nine completed answers the hypothetical total is $0.558082; the query
embedding estimate is $0.00000412. These are **not measured subscription-backed
CLI charges** or a total cost for the incomplete run. Failed/interrupted usage,
subscription allocation, index creation, database/storage, hosting, network,
regional/priority charges and other operational costs are excluded. No model,
provider, or billing setup was switched for the experiment.

### Next actions

- Human-review target labels and the actual completed answers/sources using the
  [RAG review section](../archive/milestone_3/human_review.md#retrieval-diagnostic-review-ami-rag-pilot-v1).
  Preserve original judgments and any adjudicated corrections.
- Investigate the repeated CLI timeouts before attempting full answer coverage;
  keep a rerun separate and retain this partial run.
- Test the citation-prefix failure as a later prompt/source-format version,
  without changing this run's labels or declaring a retrieval winner.
- Complete the supported/unsupported native demo and expanded scope/isolation
  evaluation. AMI development results are not a held-out quality claim or a
  substitute for the personal task-extraction worksheet.

## October 26 Milestone 4 release checkpoint

Baseline export: `a2b078e`; subsequent pipeline, citation and logging changes are
included in the commit containing this entry. Assistant executed these checks on
Bryan's behalf. Public AMI or explicitly synthetic data only was sent to models.
Raw run products remain under `artifacts/m4/2026-10-26/`.

- Fresh tracked-source export installed locked dev/server/audio extras into a new
  environment and ran MLX base on the 45-second public AMI fixture with the audited
  external transcriber hash. Cached model weights were reused. No diarization or
  speaker recognition was tested. Initial omission of `--no-diarize` failed for
  missing HF_TOKEN; instructions now pass the negative flag explicitly.
- Upload API regression exposed a second issue: disabled diarization was not
  forwarded to the transcription subprocess. The shared pipeline now passes an
  explicit positive or negative flag. Both settings pass HTTP workflow tests.
- Authenticated chat API regression reproduced an unsupported budget sentence
  surviving beside a legitimate citation after its fabricated ref was removed.
  Chat now refuses the entire reply for any invalid quote/ref or mismatched
  markers, including whitespace-only quotes. The persisted API answer is also
  checked. Literal verification still does not prove semantic entailment.
- Ruff lint/format passed; all **327 backend tests passed** against newly created
  isolated PostgreSQL `guardian_m4_20261026` (not the hosted application database).
  Existing Starlette/httpx and AnyIO deprecation warnings remain visible.
- Signed Debug simulator build succeeded for iPhone 18 Pro Max, iOS 27.0. Xcode
  required explicit `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer`;
  the shell default selects Command Line Tools. Code signing remained enabled.
  Xcode emitted the nonfatal no-AppIntents-dependency metadata warning.
- The separate [frozen-source answer pass](m4_2026-10-26/rag_answers.json)
  completed 28/28 calls with Codex CLI 0.163.0 and requested gpt-5.6-sol. No prior
  timeout was reproduced; no root cause has been established. Both variants
  refused both proposed unsupported questions. Power/hybrid and curve/dense
  also refused after literal quote rejection. Human answer/citation judgments
  remain pending in the [review packet](../milestone_4/human_review.md).
- [Five live synthetic safety probes](m4_2026-10-26/redteam.json) covered source
  injection, direct user injection, nonexistent secrets, supported control and
  extraction injection. No fabricated budget or exfiltration task was returned;
  the control cited Friday. This small pass complements existing auth/isolation,
  approval/opt-out and outbox regression tests; it does not establish safety.
- [Nine workload runs](m4_2026-10-26/workloads.json) completed. Median local
  45-second audio-to-extraction time was 8.33 s (range 7.25-11.28); supported
  frozen-source chat 4.43 s (3.76-4.54); unsupported chat 4.54 s (3.81-5.38).
  These exclude mobile upload, auth, live retrieval, indexing and DB publication.
  [Summary](m4_2026-10-26/summary.json) records usage and hypothetical standard
  API-equivalent estimates, not actual CLI charges or total system cost.

### Reproduce the direct evidence procedures

From the repository root after locked audio/dev/server setup and Codex login:

```sh
uv run --no-sync python docs/evidence/m4_2026-10-26/runners/rag_answers.py \
  --output artifacts/m4-reviewer/rag-new.json
uv run --no-sync python docs/evidence/m4_2026-10-26/runners/redteam.py \
  --output artifacts/m4-reviewer/redteam-new.json
uv run --no-sync python docs/evidence/m4_2026-10-26/runners/workloads.py \
  --output artifacts/m4-reviewer/workloads-new.json
```

These direct, dated procedures require new output files and send the frozen
public AMI or synthetic excerpts to Codex. They do not query the app database or
send personal meetings. The audio procedure additionally requires the supplied
transcriber and Apple Silicon MLX. Original procedures ran from temporary source;
committed copies add output-path arguments and formatting for reviewer reuse.
The answer pass preceded the stricter mixed-citation mitigation; preserve its raw
and final outputs. A rerun uses current validation and is a separate experiment.

### Milestone 4 demo edit plan

Target: 85 seconds, 1080p or higher, captions and clear voiceover. This is an edit
plan, not an assertion that a public video exists. Preserve the uncut acceptance
capture and identify any removed processing waits in the final narration/caption.

| Time | Visual and narration purpose |
| --- | --- |
| 0-10 s | Fresh Cedar project: meeting decisions and commitments should not disappear after the call |
| 10-25 s | Upload clearly labeled synthetic audio; show the completed transcript and exact task evidence; label waiting-time edits |
| 25-42 s | Human assigns the test task, enters October 30 manually, and approves it |
| 42-55 s | Show the same task/date in Tasks and Calendar; show captured follow-up with no real inbox delivery claim |
| 55-73 s | Ask supported checklist question and unsupported budget question; show citation and abstention |
| 73-85 s | Show persistence after relaunch and repository link; state human review, date/identity limits and capture mode |

Do not present synthetic Casey audio as Bryan's actual voice or infer identity.
The test assignee is explicitly selected by the tester. Publish only after
reviewing for account/contact information; use unlisted YouTube/Vimeo and link it
from the project page/README. Hosting/public URL remains a submission gate.


### October 26 native acceptance

Run project: `39a5351a-3b8f-4b90-8435-c13b0f8f50b2`; meeting:
`a25880e9-8d79-453e-8391-df6bd4c6522e`, title `cedar`. Synthetic audio was
generated with macOS Samantha voice, imported through Files from the app's shared
Documents folder, then uploaded through the app after confirming test consent.
It is not Bryan's voice or a natural meeting. The selected assignee is tester
supplied and does not establish that Casey is Bryan.

| Check | Observed result |
| --- | --- |
| Initial launch | Signed app launched; API unavailable until the local backend was started, then Try Again loaded projects |
| Fresh project/policy | Created `M4 RC - 2026-10-26 - manual`; automatic approval off, task email/recipient on, Test inbox; saved policy verified after approval |
| Upload/processing | Uploaded `cedar-synthetic.wav`; real MLX base and Codex processing completed; no diarization; first attempt completed |
| Transcript/evidence | Commitment preserved October 30th, 2026 at 00:03; checklist scope at 00:08; no budget amount at 00:15 |
| Manual review | Candidate stayed pending; tester selected Bryan and October 30, then clicked Approve once |
| Tasks/Calendar | Accepted checklist visible in To-do and Calendar on October 30; completion moved it to Completed; Undo restored open state |
| Follow-up | One Captured for testing entry; body contained correct task, cedar meeting, 2026-10-30 and exact commitment quote |
| Supported chat | “What will the evaluation checklist cover?” answered task ownership, due dates and supporting evidence with [1]; citation opened the transcript at 00:08 |
| Unsupported chat | “What is the project Wi-Fi password?” returned the fixed no-answer response |
| Relaunch | Terminated/launched same signed app without clearing data; accepted task remained and Chat History reopened both answers |

Raw video: `artifacts/m4/2026-10-26/native-acceptance.mov`, 12m35s,
1320x2868; persisted-chat screenshot beside it. Video starts at the audio form,
after project creation/policy setup; those earlier actions are evidenced by the
observed UI/server log, not by this video. The document picker took time to load;
no permanent picker failure was established. Native checks used the actual
configured backend and embeddings; the separate workload timing experiment uses
frozen chat sources and excludes the mobile path. No mobile latency percentile
is claimed. No microphone recording, real mail, identity calibration or automatic
date parsing was established.


### October 26 demo review draft

[85-second captioned video](https://raw.githubusercontent.com/BryanDYang/guardian-agent/main/docs/milestone_4/demo_draft.mp4)
is linked from the README. The committed copy is `docs/milestone_4/demo_draft.mp4`;
[subtitle sidecar](../milestone_4/demo_draft.srt) and
[edit manifest](m4_2026-10-26/demo_edit.json) preserve narration and source offsets.
The source is the uncut native acceptance recording. The portrait output is
1080x2600 with H.264 video/AAC audio, 85.00 seconds, burned-in captions and macOS
Samantha synthetic narration. Processing waits/navigation were edited out, and
the synthetic input, manual date/assignment, and capture-only delivery are labeled.
All eight sampled sections were visually inspected; a complete decode found no
errors. Human demo sign-off remains pending. Public raw-file access must be
verified after push; this is a review draft rather than a final showcase claim.


### October 26 extraction rerun

Current production extraction (`meeting-extraction-v2`, gpt-5.6-sol, CLI 0.163.0)
completed 24/24 frozen synthetic development cases, as did the rules baseline.
[Combined run/scoring/output packet](m4_2026-10-26/extraction.json) preserves
source/fixture hashes and per-case results. Codex task precision/recall/F1 proxies
were .929/.867/.897 (13 matched, 14 predicted, 15 labeled); rules were
.688/.733/.710 (11/16/15). No failures/missing cases. Codex literal citations
28/28; negative cases 11/11; exact deadline text 5/13; mean extraction wall time
4.402 s across all 24 attempts. These replicate earlier proxy scores, not a new
quality improvement or independent semantic evaluation. Unknown-owner omission,
merged actions, joint-owner duplication and deadline-span mismatches remain.

```sh
uv run --no-sync python -m labsync.evaluation run --method codex \
  --model gpt-5.6-sol --directory artifacts/m4-reviewer/extraction-codex-new
uv run --no-sync python -m labsync.evaluation score \
  --directory artifacts/m4-reviewer/extraction-codex-new
uv run --no-sync python -m labsync.evaluation run --method rules \
  --directory artifacts/m4-reviewer/extraction-rules-new
uv run --no-sync python -m labsync.evaluation score \
  --directory artifacts/m4-reviewer/extraction-rules-new
```

The suite is synthetic; no personal data or application database writes. Human
label adjudication and suggestion/state scoring remain outside these proxies.

**Public-access verification:** after pushing `60880fb`, an anonymous HEAD request
to the README's raw demo URL returned HTTP 200 with content length 7,624,214 bytes.
GitHub serves the MP4 as `application/octet-stream`, so it is a public downloadable
video rather than a dedicated streaming/player page. A YouTube/Vimeo showcase
link can replace it after human demo sign-off. Main revision and clean working
tree were verified. Runtime fixes are in `5634435`; the evidence/report/video
package is in `60880fb`.
