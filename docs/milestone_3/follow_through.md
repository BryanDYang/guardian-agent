# Immediate task follow-through

Implemented October 17, 2026. This is the first email slice: task owner confirmation,
manual or bounded automatic approval, a durable delivery queue, and delivery history.
Scheduled recurring reminders and cancellation/rescheduling of future reminders are
still separate unfinished work.

## Try it in the app

1. Open a project's actions menu > **Follow-through**, or a meeting's gear >
   **Task email & automatic approval**.
2. As project owner, enable **Email task owners after approval** and save.
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

The owner can optionally enable **Automatically approve clear commitments**.
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
