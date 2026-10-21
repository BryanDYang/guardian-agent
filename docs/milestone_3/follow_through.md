# Immediate task follow-through

Implemented October 17, 2026. This is the first email slice: task owner confirmation,
manual or bounded automatic approval, a durable delivery queue, and delivery history.
Scheduled recurring reminders and cancellation/rescheduling of future reminders are
still separate unfinished work.

Quick navigation: [app test](#try-it-in-the-app), [approval policy](#automatic-approval),
[live delivery setup](#live-email-setup), [dated recording scripts](#personal-recording-test-scripts),
and [result log](#result-log).

## Try it in the app

For repeatable personal audio, use the [read-aloud scripts below](#personal-recording-test-scripts).
AMI participants have no corresponding recipient accounts. Test email routing
with a separate consented recording of an actual app member. Previously accepted
AMI tasks are not automatically reassigned or emailed by enabling these settings.

1. Open a project's actions menu > **Follow-through**, or a meeting's gear >
   **Task email & automatic approval**.
2. New projects start with **Email task owners after approval** and
   **Automatically approve clear commitments** on. Existing projects retain their
   saved settings. As owner, check the switches and save any changes needed for
   your scenario. For a manual-approval test, turn automatic approval off first.
   **Done** saves changed project settings and your receive-email preference,
   then closes the sheet. There are no separate save buttons. **Cancel** discards
   unsaved edits, and saving failures keep the sheet open for retry. Refreshing
   delivery history does not reset your draft switches.
   In the default **Test inbox** mode, nothing leaves the backend.
3. Open a real meeting's speaker review. Confirm the speaker's name and connect
   their actual app account. An anonymous diarization label cannot receive mail.
4. Approve an evidence-supported task. It need not have a deadline.
5. Return to Follow-through and refresh delivery history. Within a few seconds,
   a queued item should become **Captured for testing**. Expand **Read captured
   email** to inspect the task, meeting, quote, deadline, and Tasks-tab link.
6. Repeating approval must not create another email. Complete the task before
   delivery, opt out, or remove the member to check that queued delivery cancels.

Each member can turn off **Receive emails for my tasks**. Project owners control
project automation and can inspect the project delivery history. Other members
see only their own delivery records. Existing accepted tasks are not bulk-emailed
when a project enables email; new approvals or assignment edits enqueue work.

## Automatic approval

**Automatically approve clear commitments** defaults on for new projects as of
October 20. Owners can turn it off; existing projects retain their saved choices.
Saving the setting evaluates existing completed-meeting candidates; confirming a
speaker also evaluates that meeting. The rule `explicit-self-commitment-v1` requires:

- A current, human-confirmed speaker-to-member mapping for this recording.
  Provisional voice recognition or a display name alone does not qualify.
- A commitment with an explicit first-person `I will` or `I'll` source turn,
  matching speaker evidence, and an exactly supported quote.
- Title content words supported by the quote; no recognized uncertainty,
  negation, conditional, or question in the source.
- No unresolved deadline. Date-bearing tasks remain in review in this version.
- Available task embeddings and no possible duplicate among non-dismissed tasks,
  including completed work. The similarity cutoff is provisional.

Eligible tasks are approved, audited with the policy/evidence, and queued for
email if enabled. Everything else remains pending. This is a deliberately narrow
experimental rule, **not calibrated high-confidence AI** and not proof of extraction
accuracy. A task's title can still misrepresent a quote despite lexical checks.
Measure incorrect approvals and missed opportunities against reviewed a-d labels
before widening the rule. Identity still needs confirmation once per speaker per
recording because diarization labels are not stable identities across recordings.

## Live email setup

Apply `supabase/migrations/20261017212319_task_followup_email.sql` before using the
new endpoints. Restart the backend after configuring:

```dotenv
LABSYNC_EMAIL_MODE=resend
RESEND_API_KEY=<server-side API key>
LABSYNC_EMAIL_FROM=LabSync <verified-sender@your-domain.example>
```

Use a verified sender and a consenting test account for the first live test.
Capture records stay capture records when changing modes; they are never promoted
into live sends. No credentials are bundled into the mobile app. Project settings
and recipient opt-out are checked again before delivery.

The backend's email worker runs separately from audio processing, polling every
two seconds. Approval and queue insertion commit together. A unique task/recipient
pair prevents repeat approval from creating multiple messages. Workers use claims
and leases; immutable payloads and a stable Resend idempotency key protect retries.
Retries stop before the provider's 24-hour deduplication window expires. Expired
uncertain sends require inspection rather than risking a duplicate.

A change to task details or recipient after an attempted send cancels the pending
retry; it does not automatically generate another message. Initial queued messages
use current task details. Task completion, project disablement, recipient opt-out,
and membership removal cancel eligible queued work. Already submitted mail cannot
be recalled; changes racing an in-flight network request may not stop that request.
Project/account deletion cascades through stored email content.

`sent` means the provider accepted the request. Inbox delivery, bounce tracking,
and read confirmation are not implemented. Captured previews are available only
in test mode. Email links open `meetingmemory://tasks` after sign-in; they open the
task list rather than selecting an individual task.

Provider reference: [Resend idempotency keys](https://resend.com/docs/dashboard/emails/idempotency-keys).

## Verification

`tests/test_followup.py` exercises authenticated manual approval and speaker
confirmation through to captured email, plus policy abstentions, audit evidence,
recipient preferences, project ownership, isolation, cancellation, and provider
retry keys. Use only a disposable database with migrations applied:

```sh
TEST_DATABASE_URL=<disposable-local-postgres> uv run --no-sync pytest tests/test_followup.py
```

These checks use stored transcript fixtures and fake provider calls. They do not
establish real inbox delivery, AMI extraction quality, or native visual acceptance.

October 17 checkpoint: all 311 backend tests passed on disposable PostgreSQL;
Ruff lint/format and the simulator build passed. Applied the migration to the
configured backend and recorded its migration history; verified outbox RLS and
denied direct client-role reads. Installed/relaunched the app with cached data
preserved and restarted the idle backend explicitly in capture mode. Backend
health passed, all project automation remained off, and zero real emails were
sent. Desktop UI automation was unavailable, so visual native acceptance remains
open. The suite reports two existing dependency deprecation warnings.

## Personal recording test scripts

Prepared October 18, 2026. These are scripted acceptance recordings you can read
aloud, not natural-meeting accuracy benchmarks. Replace bracketed fields before
recording. Record only yourself or participants who consent. Keep original AMI
projects and their anonymous speaker identities unchanged.

### Fill this in once per test session

| Placeholder | Your value | Example if testing October 18, 2026 |
| --- | --- | --- |
| `[YOUR_NAME]` | Name of your signed-in test account | Bryan |
| `[RUN_LABEL]` | Unique label for this session | 2026-10-18-run-1 |
| `[MEETING_DATE]` | Actual recording date, YYYY-MM-DD | 2026-10-18 |
| `[DUE_DATE]` | Chosen calendar deadline | 2026-10-20 |
| `[DUE_DATE_SPOKEN]` | Say the full date aloud | October twentieth, twenty twenty-six |
| `[TOMORROW_DATE]` | Calendar day after the meeting | 2026-10-19 |
| `[REVISED_DUE_DATE]` | New later deadline | 2026-10-22 |
| `[REVISED_DUE_DATE_SPOKEN]` | Full revised date aloud | October twenty-second, twenty twenty-six |
| `[TIME_ZONE]` | Time zone used for the run | America/Los_Angeles |

Choose dates relative to your actual test day. Use future dates to avoid confusion
with overdue tasks. The upload form must contain the actual `[MEETING_DATE]`;
file timestamps are not reliable meeting-date evidence. The app currently stores
calendar deadlines, not a selectable deadline time. Do not expect a spoken time
or relative phrase to produce a prefilled calendar deadline automatically.

### Setup and recording method

**Do not read all the sentences in one recording.** Each row below is a separate
clip. Finish its settings, upload, and checks before moving on. Start with **A**
only; B through F can wait until A works. Read the quoted sentence, not the
headings, settings, or expected results. Replace bracketed dates with actual
spoken dates before recording.

| Clip / suggested meeting title | Project | Before recording |
| --- | --- | --- |
| `A-manual` | New project A | Automatic approval off; email and your receive preference on |
| `B-auto` | New project B-positive | Automatic approval on; email and receive preference on |
| `B-negative` | New project B-negative | Same settings as B; do not approve manually |
| `C-explicit-date` | New project C | Read the full chosen deadline; enter the calendar date manually before approval |
| `D-tomorrow` | New project D | Automatic approval off; enter tomorrow's date manually |
| `E-opt-out` | New project E | Automatic approval off; your receive-email preference off |
| `F1-date-change` | Reuse project C | Run after C; automatic approval off; restore receive-email preference on |
| `F2-completion` | Reuse project C | Run after F1; completion extraction is a known gap |

The in-app recorder assigns its own timestamped filename. Use the suggested name
as the **meeting title**; copy the actual audio filename into your result log.

### Where recordings and results go

- **In the app:** recordings are saved under the app's **Documents/Recordings**
  directory. On a physical iPhone, look in **Files > Browse > On My iPhone >
  MeetingApp (or the app's displayed name) > Recordings**. Originals remain after
  upload. On the simulator, use its Files app; the simulator's app container is
  separate from your Mac's Documents folder. If the folder is not visible, use
  Xcode's app-container tools to copy out `Documents/Recordings`.
- **For test evidence on your Mac:** use
  `artifacts/follow-through/[RUN_LABEL]/audio/` for exported original clips and
  `artifacts/follow-through/[RUN_LABEL]/evidence/` for screenshots or screen
  recordings. Exporting is a manual backup; uploading does not create these Mac
  copies. Keep the original filename or record any renamed copy in the log.
- **For observed results in Git:** fill the run results and ledger in the
  existing [walkthrough](../evidence/demo_walkthrough.md#october-20-personal-audio-acceptance-2026-10-20-run-1).
  Record the tested commit/configuration, actual dates, before/after state,
  manual actions, audit actions, delivery counts, failures, and unrun checks.
  Keep this as the authoritative team-readable result rather than maintaining
  another status document.
- **For local working notes:** `artifacts/follow-through/[RUN_LABEL]/results.md`
  and raw snapshots are optional scratch evidence. The October 19 starter has
  example dates and **not run** outcomes; it is not acceptance evidence.
- `artifacts/` is ignored by Git. Recordings, raw backend snapshots, private
  configuration, and full email payloads stay there or in an agreed restricted
  team evidence location. Promote the sanitized observed results into the
  walkthrough before committing. Keep account emails, tokens, and unrelated
  meeting content out of shared evidence.

### Run each clip

1. Use the installed signed simulator build or a normally signed device build.
2. Sign in with your own account and create a separate project for each independent
   scenario, such as `Follow-through [RUN_LABEL] - A`. Do not reuse AMI projects.
3. Open project **... > Follow-through**. Save **Email task owners after approval**
   on. Save your own receive-email preference on. Keep delivery in **Test inbox**.
4. In **Add Meeting**, confirm recording consent and choose **Record Audio**.
   Speak the quoted text clearly, stop, play it back, then choose **Use Recording**.
   Record each block separately; a short silence before/after is fine. Keep the
   app open while recording. Leaving the app stops and saves the clip, and there
   is a 60-minute limit. Originals remain in the app's **Recordings** folder in
   Files. Importing a Voice Memos recording is also supported.
5. Check `[MEETING_DATE]` and choose **Upload & Process**. The recorder prefills
   the capture date; change it if your script uses a different date.
   Wait until processing completes and inspect
   the transcript, exact evidence, task title, and owner before proceeding.
6. Confirm the speaker's name as `[YOUR_NAME]` and connect your actual app member.
   You can enter your name manually; a spoken introduction is not required.

For automatic-approval case B, record only its commitment sentence. Do not prepend
an introduction to the same turn: the current rule expects a source turn starting
with `I will` or `I'll`. If ASR or extraction changes the wording, record the
abstention instead of changing the transcript or claiming a successful auto-pass.

### Zoom summary test

This is a separate input experiment from the audio scripts below. It imports a
summary after it is available; it does not join, record, or watch a Zoom call.

1. In a dedicated project, open **Add Meeting > Import Zoom Summary**.
2. For a solo test, choose **Fill Solo Test Example**. Keep **synthetic test data**
   on and replace Bryan with your name if needed. For a real call, paste an
   authorized summary and turn the synthetic-data switch off.
3. Set the actual meeting date, title, and a unique instance label. A recurring
   Zoom meeting ID alone is insufficient: use its UUID, or a label containing
   the meeting's date/time. Confirm permission and choose **Process**.
4. Open the imported meeting. **Source** contains the summary document. No audio
   player or playback timestamps should appear. Names remain suggestions.
5. With task email and your receive-email preference enabled, edit a proposed
   task to assign your own project member and set any due date, then approve it.
   Check **Follow-through > Recent follow-ups** for the captured message.
6. Import the same instance and unchanged content again: expect the same meeting
   and existing tasks, without new emails. Changed content under the same label
   returns a conflict, preserving reviewed work. Review changes manually rather
   than creating a different label just to bypass this check.

Summary imports require manual approval even if project automatic approval is
enabled. An exact quote proves what the summary says, not what a person actually
said. Capture mode does not send to a real inbox, and recurring reminders remain
outside this test. If processing times out, retry with the same instance and
unchanged form fields. Inputs are limited to 30,000 characters.

Automatic Zoom account connection is not implemented. Creating a developer app
does not itself unlock meeting artifacts. Zoom's [Meeting Summary requirements](https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0058013)
list a licensed Pro-or-higher host. Verify the personal account's permissions,
plan and actual API availability before choosing OAuth scopes or implementing
automatic imports. No Zoom secrets belong in the mobile app.

### A. Manual approval to captured follow-up

**Settings:** email on; automatic approval off. Use a fresh project.

Read:

> I will prepare the evaluation checklist.

After processing, confirm your speaker/account and approve the evidence-supported
candidate without a due date. Open Follow-through, refresh history, and read the
captured email.

Expected: one approved task in To-do and one captured message for your account.
The message should include the task, meeting, supporting quote, and no invented
deadline. Its Tasks link should open the app's Tasks tab. Refresh/relaunch should
preserve the task and history, without creating another message.

**Pass evidence:** task card, speaker/account connection, captured email, relaunch.
This verifies capture delivery, not arrival in a real inbox.

### B. Automatic approval after identity confirmation

**Settings:** email on; automatic approval on. Use a fresh project with no other tasks.

Read:

> I will share the recording.

After processing, confirm the speaker and connect your account. Do not manually
approve the candidate first.

Expected: if the transcript/title/evidence meet the narrow policy, the task is
approved and one email is captured without a task-level approval click. Identity
confirmation is still required once for this recording. If the task remains
pending, preserve the transcript/title/evidence and record why it did not qualify.
A safe abstention is not evidence that automatic approval succeeded.

**Pass evidence:** before/after candidate state, accepted task, captured email, and
policy audit if available. Do not report calibrated confidence from this test.

**Negative case, in another fresh project:**

> I might prepare the budget spreadsheet if I have time.

Keep automatic approval on and confirm the speaker/account. Expected: no automatic
approval and no follow-up email. The extractor may omit this tentative statement
or present it for review; neither result should turn it into an accepted promise.
Do not manually approve it during this negative test.

### C. Explicit date and manual deadline entry

**Settings:** email on; automatic approval may be on. Use a fresh project.

Read after replacing the date:

> I will send the project summary by [DUE_DATE_SPOKEN].

Expected: the deadline text is preserved if extracted correctly. A date-bearing
task stays pending under the current automatic-approval policy. Open **Edit**,
turn **Due date** on, select `[DUE_DATE]`, save, then approve.

Verify To-do, Calendar on `[DUE_DATE]`, and the captured email all agree. If the
picker initially shows today's date, replace it deliberately; that initial value
is not an inferred deadline. A missing/wrong extracted deadline is a finding.

**Pass evidence:** source quote, selected date, Calendar placement, message date.

### D. Relative deadline: reveal the current limitation

**Settings:** email on; automatic approval off. Use a fresh project.

Read:

> I will upload the presentation slides tomorrow.

Upload with `[MEETING_DATE]`. Expected raw deadline text: `tomorrow`. The desired
calendar deadline is `[TOMORROW_DATE]`, but automatic relative-date resolution is
not implemented. Enter that date manually through Edit, then approve and inspect
the captured email and Calendar.

Record manual entry separately from extraction. Do not mark automatic date
calculation as passed because the manually entered value is correct.

### E. Recipient opt-out

**Settings:** email on; automatic approval off. Before approval, turn your own
receive-email preference off and save. Use a fresh project.

Read:

> I will review the deployment instructions.

Connect the speaker to your account and approve. Expected: the accepted task
exists but no email is queued/captured for the opted-out recipient. Restore your
preference after recording the result. Opting back in does not retroactively
send this task; use a fresh task for another delivery run.

### F. Later meetings and completion: staged continuity check

Use the project from case C. Keep automatic approval off. Record F1 and F2 as
separate files and upload in order with their actual meeting dates.

**F1 - deadline change. Read:**

> I will send the same project summary. The deadline for the project summary is now [REVISED_DUE_DATE_SPOKEN].

Inspect whether a suitable update candidate is extracted. If present, choose
**Update an existing task**, select the original summary task, confirm the quote,
and set `[REVISED_DUE_DATE]`. Expected: the same accepted task changes deadline;
no second accepted task is created. If there is no suitable candidate, record that
extraction gap. Do not manufacture a candidate to claim audio acceptance.

**F2 - completion. Read:**

> I finished the project summary. The project summary is complete.

Completion-only update extraction remains unfinished. It may not generate a
reviewable update. Record the actual output, then separately mark the original
task complete in To-do and verify persistence after relaunch. That manual action
is not proof of completion inference from the recording.

Current immediate email is one follow-up per task/recipient. Do not expect a new
update email, a scheduled reminder, or automatic reminder rescheduling/cancellation
from these later recordings. Those are future acceptance cases, not implemented
passes. A duplicate candidate is also not the same as retrying the original
approval: approving a new duplicate task can create a separate email.

### G. Live inbox delivery, after sender setup

Only run after configuring a verified email sender and a consenting test inbox.
Use a fresh project/task and repeat A. Capture records are never promoted into
live messages after a mode switch. Verify both the provider's recorded acceptance
and the actual received email; note spam/delivery delay separately. No live sender
has been established by the current capture tests.

### Result log

Start with the [copy-and-fill `result.md` template](../evidence/result.md).
It explains what to fill before testing, what to observe afterward, and which
claims require separate evidence. Paste completed runs into the walkthrough;
keep the template blank. Existing recordings do not need to be recreated for
human review.

October 20 actual results are recorded in the [native walkthrough](../evidence/demo_walkthrough.md#october-20-personal-audio-acceptance-2026-10-20-run-1).
The F1 intended revised date was October 23, 2026; ASR reported October 3.
Keep the error and manual correction in the evidence.

Copy this table for every run. Leave unexecuted cases pending.

| Field | Recorded value |
| --- | --- |
| Run label / tester / test date / time zone | |
| Commit, app build, device/simulator, backend configuration | |
| Scenario and actual meeting date | |
| Audio filename and consent | |
| Project / meeting / task IDs | |
| Expected title, owner, evidence, due date | |
| Observed transcript and extracted output | |
| Mapping and manual actions taken | |
| Email mode, state, recipient, message count | |
| Screenshot/video references | |
| Result: pass / fail / abstained / unsupported / not run | |
| Failure and next action | |

For a short demo, record the screen while showing A, B, C and a relaunch. Keep the
original audio files and label this as personal scripted acceptance. Run negative
cases too; a successful-looking email alone does not establish safe automation.
See [implementation and delivery limits](#live-email-setup).

## Clean app journey screen recording

Prepared October 21, 2026. **Planned, not executed.** This is a separate clean
manual-approval demonstration. Keep the October 20 projects/results intact.
Read aloud only the quoted meeting paragraph below. The other instructions are
screen actions, not additional meeting audio. You can review this script before
recording; observed model behavior may differ from the checkpoints.

### Prepare before you start the screen recording

1. Use your signed-in app and reachable backend. Note the app commit/build,
   device/iOS, actual date, time zone, and delivery mode in the walkthrough.
   Never record credentials or account settings that expose tokens.
2. Create a fresh server project named `M3 Demo - [ACTUAL_DATE] - manual`.
   Open the project's **... > Follow-through**. Set **Email task owners after
   approval ON**, **Automatically approve clear commitments OFF**, and
   **Receive emails for my tasks ON**. Tap **Done**, reopen and verify saved
   values. New projects default automation on, so do this before processing.
3. Check Delivery says **Test inbox** for this capture-mode demo. This will
   show a captured message, not send mail to your actual inbox. If it says
   Live email, pause and choose the intended delivery setup before proceeding.
4. Choose `[DUE_DATE]` a few days ahead and say the full date. If recording on
   October 21, use October 23, 2026. Replace both values if recording later.
   The meeting date must be your actual recording date, not the due date.
5. Have a screen-recording tool ready. On Mac you can use Screenshot's
   **Record Selected Portion** around the simulator. On iPhone use Control
   Center's Screen Recording. The app's microphone records meeting audio;
   the screen recording is separate demo evidence. Keep notifications hidden.

### Meeting paragraph to record in the app

> This is a consented test recording. I am Bryan Yang. I will prepare the evaluation checklist by [DUE_DATE_SPOKEN]. The checklist will cover task ownership, due dates, and supporting evidence. Our test project is called Cedar. No budget amount has been decided.

This is synthetic test data. The spoken name does not establish the diarized
speaker's account; confirm that mapping yourself in the next steps.

### Screen actions and checkpoints

1. **Start screen recording.** Show the fresh project name and saved
   Follow-through switches, then return to the project.
2. **Record/upload.** Use the project's **+** menu and recording option; give
   microphone permission/consent if prompted. Read the paragraph once clearly,
   stop, preview it, and submit using the recorder's upload action. Set the
   actual meeting date if the upload form asks. Use meeting title
   `M3 manual task demo` if editable; otherwise retain the timestamped title
   and record that name. Do not upload the same audio twice if processing is slow.
3. **Wait for completion.** Show the completed meeting. If it fails, record the
   error and pause to troubleshoot. You may trim waiting time in a presentation
   copy, but preserve the original evidence and label any edits.
4. **Inspect Transcript and Summary.** Play the relevant audio and compare the
   checklist action and full date with the transcript. Note omissions/wrong
   words before any correction. Summary should not invent a budget amount.
5. **Confirm speaker.** Open **Review speaker names**, find your speaking
   cluster, name it Bryan Yang and connect it to your signed-in project member
   using the available account selector. Save/confirm. If already mapped,
   inspect it rather than claim automatic identification.
6. **Review the task.** Open meeting **Tasks**. Show the checklist candidate
   and source quote/timestamp. It should still await manual approval. If it
   already approved, record the settings problem; this run does not demonstrate
   clean manual approval. Do not reset history to hide it.
7. **Set the date manually.** Tap candidate **Edit**, confirm the assignee,
   turn Due date on, select `[DUE_DATE]`, and save. Show the saved date, then
   tap **Approve** once. Say in your narration that this date entry is manual.
   Missing/incorrect candidate content is a result to record, not silently fix.
8. **Verify follow-up.** Return to project **... > Follow-through**, refresh
   history, and expand **Read captured email**. Check one entry for this task,
   correct assignee, title, date, meeting, and evidence. Show its captured status.
   If absent or wrong, mark failed/pending and retain the observation.
9. **Verify Tasks/Calendar.** Open bottom **Tasks**. Find the checklist in To-do.
   Open **Calendar**, select `[DUE_DATE]`, and show the same task. Complete it,
   show Completed, tap **Undo**, and verify it reopens. Leave it open for the
   persistence check. System Reminders permission/export is a separate claim.
10. **Supported chat.** Open **Chat**. In the scope menu choose this fresh
    project and the completed demo meeting. Type exactly:
    `What did Bryan commit to prepare, and what should it cover?`
    Save the actual answer. Check against the transcript: checklist; ownership,
    due dates, supporting evidence. Open the citation and confirm it points to
    this meeting and the relevant words/timestamp. A plausible answer without
    supporting evidence is not a pass.
11. **Unsupported chat.** In the same selected scope, type exactly:
    `What exact dollar amount was approved for the Cedar budget?`
    Check that the answer says the amount is not established, rather than
    inventing a number. Preserve the response and citations as returned.
12. **Relaunch.** Close and reopen the app. Verify the task remains open with
    the chosen date; reopen Chat history and check the saved conversation's
    scope/answers. Refresh follow-up history and verify there is still one
    captured message. Stop screen recording.

If a label differs in your installed build, stop at that step and tell the
assistant which screen you see. Do not guess destructive actions. This short
journey does not test cross-project isolation, natural multi-speaker accuracy,
automatic date resolution, live inbox delivery, or recurring reminders.

### Save the observed run

Keep original video/audio in `artifacts/follow-through/[RUN_LABEL]/evidence/`
and `audio/` when exported. Record their actual filenames. Add a dated run under
[the walkthrough](../evidence/demo_walkthrough.md) with step numbers, observed
results, manual edits, exact chat answers/citations, commit/configuration, and
**Passed / Failed / Blocked / Not run**. A script is not evidence of execution.
Share the resulting questions/answers for human review; keep their gold labels
and any later retrieval comparison separate from this rehearsed demo.
