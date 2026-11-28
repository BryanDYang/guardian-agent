# Guardian Agent System Card

Final repository documentation, November 26, 2026. Track: AI Engineering.

## System boundary and data flow

SwiftUI uploads consented recordings to authenticated FastAPI, directly or through
Cloudflare Tunnel. A worker normalizes audio, runs local transcription and optional
diarization, obtains structured text-model output, validates evidence, and stores
meeting/task state in PostgreSQL. Supabase supplies identity. Project-scoped
retrieval and hosted embeddings support cited chat. A separate outbox worker
sends immediate task emails through Resend; capture mode is available for tests.
See the [architecture and troubleshooting guide](../architecture.md).

This is an AI-assisted workflow with deterministic review/delivery rules. The
model does not autonomously select tools, send emails, or modify task state.

## Access, consent, and user control

- Authenticated routes check project membership. The backend's privileged
  database connection makes those checks essential; RLS alone is not the app's
  authorization boundary. Isolation tests run against disposable PostgreSQL.
- Upload requires a consent declaration. Voice enrollment is optional and
  consent-based; enrollment and meeting participants still need real-world consent.
- Speaker suggestions can be reviewed and linked to actual project accounts.
  Multiple acoustic clusters may be confirmed as the same person. Reviewed task
  assignments remain distinct from unreviewed speaker suggestions.
- Users can approve, edit, dismiss, complete, or return tasks for review with
  change notes. With project automation enabled and human-confirmed speaker
  identity, a narrow rule can revise one open task's deadline from a later
  commitment that explicitly names the previous date and its replacement.
  It requires the same owner, matching work words, a uniquely matching task,
  and no newer conflicting edit. A short extracted promise may use its immediately
  adjacent old-date clause in the same transcript turn; unrelated context is
  not borrowed. Ambiguous changes, completions, and
  reassignments require review. This is not general semantic consolidation.
  Automatic deadline changes retain the old/new dates and exact quote in
  task history. A separate, deduplicated deadline-change email can notify the
  current task owner, subject to project delivery and recipient preferences.
  Superseded queued changes are cancelled before delivery.
- Experimental automatic approval checks confirmed identity, explicit
  self-commitment, title/evidence grounding, date resolution, and duplicate
  conditions. It may leave clear-looking work pending. The November 26 demo
  exercised manual approval, not successful automatic approval.
- Project email and recipient preference must both allow delivery. Enabling
  email does not bulk-send previously accepted work. Immediate task follow-up
  is implemented; recurring deadline reminders are not.

## Data processing and retention

Speech inference runs locally. Transcripts/retrieved passages go to the configured
Codex/OpenAI or Anthropic text provider; embedding inputs go to OpenAI. Approved
task details and recipient address go to Resend when live email is enabled.
Provider account policies govern their processing; this project does not promise
zero retention. Do not upload confidential research without appropriate consent
and provider approval.

Local-mode audio remains on the backend that received it. A shared database does
not make those files portable: meeting #3 returned HTTP 404 on Bryan's backend
until its exact original recording was restored locally. Optional shared storage
and recoverable workers are documented in the [shared-backend guide](../reference/shared_backend.md).
Credentials, private audio, and private run artifacts are excluded from Git.
Projects, tasks, and sessions have archive/recovery controls; soft-deleted items
are recoverable for 30 days before cleanup. Backups and provider-held copies
have separate retention. Do not equate an app deletion with universal erasure.

## Failure handling and evidence

Structured output and quote checks reject invalid evidence. Chat cites verified
source handles and exact quotes, and refuses when no valid supporting citation
remains. Project-scoped retrieval and tests reduce cross-project disclosure risk.
A valid quote can still accompany an incorrect interpretation. Source prompt
injection checks are bounded tests, not proof that attacks cannot succeed.

The email outbox records delivery attempts and provider results. A `sent` state
means provider acceptance, not inbox arrival; the November 26 rehearsal separately
opened the matching message in Bryan's inbox. Backend loss, local file loss,
provider errors, authentication expiry, and transcription failures can interrupt
use. Keep the selected backend available during a demo.

## Observed limits and unresolved risks

The group recording exposed split/mixed speakers, missing deadline conversions,
and ambiguous ASR text such as “tomorrow morning at night.” Fixes and manual
corrections are recorded in the [walkthrough](../evidence/demo_walkthrough.md).
They do not establish reliable performance for natural overlapping meetings.
Duplicate tasks and missed updates remain limitations. Production load,
end-to-end latency, operational alerts, quotas, abuse controls, cold-model setup,
and independent full audio setup have not been comprehensively validated.
The external transcriber's upstream revision and licensing remain unresolved.

## Evidence and release scope

Use the [Model Card](model_card.md) for model settings and the
[evaluation guide](evaluation.md) for measured scopes, commands, safety evidence,
and reproducibility boundaries. The native simulator rehearsal passed People,
reviewed identities, task dates, manual approval, To-do, actual email arrival,
and chat citation-to-audio navigation. It was not a timed team presentation.
The public video remains the labeled Milestone 4 demonstration until the final
team video is recorded. TestFlight is on hold. The project is a research-team
prototype, not a production-ready or clinically validated system.
