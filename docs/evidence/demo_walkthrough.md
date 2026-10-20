# UI demo walkthrough

Start from the story we want to demonstrate, perform it in the iOS UI, and use failures to choose the next implementation work. Repository checkboxes track implementation only. A successful build, API health check, or scripted backend response does not establish that the corresponding UI journey works.

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
acceptance, using the [dated read-aloud scripts](../milestone_3/follow_through.md#personal-recording-test-scripts).
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

Use the existing [Zoom summary test](../milestone_3/follow_through.md#zoom-summary-test)
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
CLI. The source checkout was `afeaded` plus the changes in this commit. Mutations
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

Local detailed snapshots and results are under
`artifacts/follow-through/2026-10-20-run-1/{before.json,after.json,results.md}`.
They are ignored by Git. Original recordings remain in the app/backend; they
were not exported into the empty `artifacts/audio/` directory. UI observations
are in this session; no standalone screen recording was saved by these checks.
Still needed: a clean manual A demo with recorded visual evidence, live inbox
acceptance after sender setup, automatic date/completion improvements, recurring
reminder lifecycle, and the independent AMI a-d review/evaluation.
