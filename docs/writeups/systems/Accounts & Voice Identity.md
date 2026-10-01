# Accounts, Projects & Voice Identity

Status: Spec, not yet implemented
Scope: iOS client (`ios/MeetingApp`), FastAPI backend (`src/labsync`), Supabase Postgres (`supabase/migrations`)

This system adds user accounts, project membership with invitations, a voice enrollment onboarding step, automatic speaker recognition for enrolled project members, and a fourth "Profile" tab.

---

## 0. Instructions for the agent building this

1. Read `AGENTS.md` first. Its rules apply to everything here (for example: no em dashes, fix lint and flaky tests you touch, prefer quality and simplicity over development speed).
2. This document is the source of truth for this feature. Section 3 lists **locked decisions**. Do not change them without asking the owner.
3. Section 17 lists **open questions**. Do not decide those silently. Ask, or implement the stated default and flag it.
4. Build in the phase order in Section 15. Each phase has a verification step. Do not start the next phase until the current one passes.
5. Requirement IDs (`FR-...`, `NFR-...`) are referenced by tests and acceptance criteria. Keep them in test names or docstrings so coverage is traceable.
6. Table names: the live schema (`backup_schema.sql`) has renamed some tables from the initial migration (for example `transcripts` is now `meeting_transcripts`, `attendee_storylines` is now `meeting_attendee_storylines`). Always check the live schema before writing a migration.
7. Keep changes surgical. Do not refactor unrelated code. Existing tests in `tests/` and `ios/MeetingApp/MeetingAppTests/` must keep passing.

---

## 1. Summary

Today the app has no concept of a user. Anyone with the shared API token sees every project, and diarized speakers are labeled `SPEAKER_00`, `SPEAKER_01`, and so on.

After this system ships:

- People sign up and sign in (email + password, or Google).
- A new user goes through onboarding: set a display name, give explicit consent for voice biometrics, and record a short script so the backend can compute their voice embedding. Then they land on the Meetings tab.
- A user only sees projects they own or were invited to. Owners invite collaborators by email.
- When a meeting recording is processed, each diarized speaker is compared against the voice embeddings of that project's enrolled members. Confident matches are labeled with the member's name. Everyone else is labeled `SPEAKER_1`, `SPEAKER_2`, ... in order of first appearance.
- A fourth tab, Profile, shows the user's identity, workspaces (projects and pending invites), voice profile, task summary, integrations, privacy controls, account security, and app info.

---

## 2. Goals and non-goals

### Goals

- G1. Every request and every row of project data is tied to an authenticated user and scoped by project membership.
- G2. A user can collaborate with others on a project through invitations.
- G3. Transcripts carry real names for enrolled project members, without ever guessing: a wrong name is worse than `SPEAKER_N`.
- G4. Voice biometrics are collected only with explicit, recorded, revocable consent, and the embedding never leaves the backend.
- G5. Existing features (meetings, extraction, tasks, calendar, chat RAG, Apple Reminders) keep working, now scoped per user and project.

### Non-goals (v1)

- Organizations, companies, or org-wide discovery of projects or coworkers (projects only).
- Sign in with Apple, magic links, SSO/SAML, 2FA.
- Re-identifying speakers in meetings that were processed before a member enrolled or joined.
- Manually relabeling a speaker cluster in the UI (see Section 16).
- Real-time / live meeting identification.
- Transactional email delivery for invites (see FR-INV-4).

---

## 3. Locked decisions

| # | Decision | Notes |
|---|----------|-------|
| D1 | **Projects only**, no organization layer | A user sees only projects they are a member of. |
| D2 | **Supabase Auth** owns identity | iOS uses `supabase-swift` for auth only. The FastAPI backend verifies the Supabase JWT on every request. |
| D3 | Sign-in methods: **email + password** and **Google** | Email must be verified before the account can be used. |
| D4 | **Voice enrollment is skippable** for now ("Skip for now" in onboarding); it may become required later | Enrollment always needs explicit consent. Skipping or revoking never locks the account (FR-VOICE-8). If enrollment becomes required, revisit Section 17 question 5 first. |
| D5 | All project data access goes **through FastAPI**, not through the Supabase client | RLS is enabled on every table with **no policies for `anon` or `authenticated`** (deny by default), so the Supabase REST API cannot leak data. FastAPI enforces membership in SQL. |
| D6 | Roles: **owner** and **member** | Permissions in Section 6.4. A project can have more than one owner. |
| D7 | Speaker matching candidates = **enrolled members of the meeting's project** at processing time | Never match against users outside the project. |
| D8 | Unknown speakers are labeled **`SPEAKER_1`, `SPEAKER_2`, ...** | 1-based, numbered by first speaking time within the meeting. Raw diarizer tags (`SPEAKER_00`) are kept separately. |
| D9 | Same embedding model for enrollment and meetings | pyannote `speaker-diarization-3.1` with its WeSpeaker ResNet34 embedding (256-d, matching `vector(256)` in the schema). `docs/writeups/Tech Stack.md` says 512-d; the schema is correct, update the doc. |
| D10 | Chat conversations are **private to the user who created them** | Retrieval is still scoped to the whole project's data. |
| D11 | Raw enrollment audio is **deleted after the embedding is computed** | Only the embedding and quality metrics are stored. |
| D12 | Profile tab is the **4th tab** in `RootTabView` | SF Symbol `person.crop.circle`. Meetings stays the default tab. |
| D13 | **Develop against a local Supabase stack** (`supabase start`) | Push migrations and auth settings to the hosted project only in the final phase, after all tests pass (Section 15, Phase 9). |
| D14 | **A database trigger creates the `profiles` row** when a Supabase auth user is created | Covers email and Google sign-ups the same way, and the row exists even before the first API call. FastAPI reads profiles; it does not create them. |
| D15 | **Project privacy comes first** | Membership scoping ships in the same phase as backend authentication, before the iOS app sends real logins. No phase may leave project data visible to non-members. |

---

## 4. Current state (read before changing anything)

| Area | Today | File |
|------|-------|------|
| API auth | One shared bearer token checked by middleware `require_token`; `TrustedHostMiddleware` and an origin check | `src/labsync/server.py` |
| DB access | `psycopg` pool, raw SQL, connects as a privileged role (bypasses RLS) | `src/labsync/api/deps.py`, `src/labsync/db/*` |
| Routers | `projects`, `meetings`, `tasks`, `chat` under `/api/v1/...`; legacy unscoped routes under `/api/meetings...` | `src/labsync/api/*.py`, `src/labsync/server.py` |
| Projects | `projects(id, name, image_url, ...)`, no owner | `supabase/migrations/20260927033954_initial_schema.sql` |
| Speakers | `attendees` (global, with `voice_embedding vector(256)`), `meeting_attendees(meeting_id, attendee_id, speaker_label)`, transcript rows with `attendee_id`, `speaker_label`, `speaker_name` | same migration |
| Tasks | `attendee_id`, `owner_label`; no assignee user, no approver | same migration |
| Audit | `task_audit_log` has no actor | same migration |
| Chat | `chat_conversations` has no user | same migration |
| Diarization | Optional (`diarize=False` by default). `diarize_audio` already requests `return_embeddings=True`, but `ccb.transcribe` discards the embeddings (`annotation, _ = ...`) | `src/labsync/ccb.py`, `contexts/meeting_transcriber-master/meeting_transcriber.py` |
| iOS tabs | Meetings, Tasks, Chat | `ios/MeetingApp/MeetingApp/RootTabView.swift` |
| iOS API client | Reads `BaseURL` and static `APIToken` from config | `ios/MeetingApp/MeetingApp/Networking/MeetingAPIClient.swift` |
| iOS cache | SwiftData models, not scoped to a user | `ios/MeetingApp/MeetingApp/Models/*` |

---

## 5. User flows

### 5.1 Sign up with email

1. App launch, no session: **Welcome** screen with "Continue with Google", "Sign up with email", "Sign in".
2. Sign up: email, password (min 8 chars), confirm password. Supabase sends a verification email.
3. **Check your email** screen with "Resend" (rate limited) and "Back to sign in".
4. User taps the verification link. It opens the app through the auth redirect URL. Session is created.
5. Backend creates the `profiles` row on first authenticated request (FR-AUTH-5).
6. Onboarding starts (5.3).

### 5.2 Sign up / sign in with Google

1. "Continue with Google" runs Supabase OAuth in `ASWebAuthenticationSession`.
2. On return, session is created. Google emails count as verified.
3. If onboarding is not complete, go to onboarding. Otherwise go to Meetings.

### 5.3 Onboarding (new user, or a user who quit onboarding midway)

Steps are resumable: the app asks `GET /api/v1/me` which step is next.

1. **Profile**: display name (required, prefilled from Google name if available), optional title, optional avatar.
2. **Voice consent**: plain-language screen explaining what is collected (a mathematical voiceprint, not the recording), why (to label you in meetings of projects you belong to), who can use it (only the backend, only for your projects), how long it is kept, and how to delete it. Toggle "I agree" + "Continue". Consent version is recorded (FR-VOICE-1). "Skip for now" is always available (D4): it completes onboarding without consent or enrollment, and the user can enroll later from Profile > Speaker Identity.
3. **Microphone permission**: request it. If denied, show how to enable it in Settings with a button that opens Settings.
4. **Recording tips**: quiet room, normal speaking voice, phone on the table about an arm's length away (this matches meeting conditions better than holding the phone to the mouth).
5. **Record 3 clips** (Section 9.1): two read passages and one free-speech prompt. Each clip shows the script, a live level meter, a timer, and Re-record / Next.
6. **Processing**: upload clips, show progress while the enrollment job runs.
7. On success: "You're all set" and land on **Meetings** tab. If the user arrived through an invite link, show the invite acceptance sheet first (5.4).
8. On quality failure: show the specific reason (too quiet, too short, background noise, more than one voice detected) and return to the failing clip(s).

### 5.4 Invite and accept

1. Owner opens a project's settings, taps "Invite", enters an email and a role.
2. Backend creates a pending invitation and returns an invite link. The app opens the iOS share sheet so the owner can send it by any channel.
3. Invitee opens the link:
   - Not signed in: goes through sign up / sign in, then onboarding, then sees the invite sheet.
   - Signed in: sees the invite sheet immediately.
4. The invite sheet shows project name, inviter, role. Accept or Decline.
5. Accept succeeds only if the signed-in user's verified email equals the invitation email (FR-INV-6).
6. Invitations also appear in Profile > Workspaces > Pending invitations for any user whose verified email matches, even without the link.

### 5.5 Meeting processing with speaker recognition

1. A member uploads a consented recording to a project (existing flow, now authenticated).
2. Worker transcribes and diarizes (diarization is now always on in the server path).
3. Worker computes one centroid embedding per diarized speaker and matches against enrolled project members (Section 9.2).
4. Matched speakers get the member's display name and are linked to that member's attendee row. Unmatched speakers get `SPEAKER_1`, `SPEAKER_2`, ...
5. Extraction runs on the labeled transcript, so commitments are attributed to real names when known.

### 5.6 Profile actions

- Edit name, title, avatar.
- Re-record voice (same flow as onboarding steps 4 to 6; replaces the old embedding only if the new one passes quality checks).
- Revoke voice consent: deletes the voice profile immediately. User stays signed in and is labeled `SPEAKER_N` in future meetings. Profile shows "Enroll voice".
- Sign out: clears the session and the local SwiftData cache.
- Delete account (FR-ACCT).

---

## 6. Functional requirements

Priority: **MUST** for v1, **SHOULD** if time allows in v1.

### 6.1 Authentication (FR-AUTH)

- FR-AUTH-1 MUST: Sign up and sign in with email + password via Supabase Auth. Email confirmation is required before a session is issued.
- FR-AUTH-2 MUST: Sign in with Google via Supabase OAuth.
- FR-AUTH-3 MUST: Password reset by email.
- FR-AUTH-4 MUST: iOS stores the session in the Keychain (supabase-swift default), refreshes tokens automatically, and sends `Authorization: Bearer <access_token>` on every backend request. On a 401, refresh once and retry; if refresh fails, go to the Welcome screen.
- FR-AUTH-5 MUST: Backend dependency `current_user` verifies the JWT (signature, `exp`, `aud = authenticated`, issuer = the project's Supabase auth URL) and returns `user_id` and `email`. The `profiles` row is created by a database trigger on `auth.users` insert (D14), copying the display name from sign-up metadata (`full_name` or Google's `name`). If the row is somehow missing, `current_user` returns 401 `profile_missing` rather than creating it.
- FR-AUTH-6 MUST: Every `/api/v1/*` route requires `current_user`, except `/api/health`.
- FR-AUTH-7 MUST: Sign out clears the session, the Keychain entry, and all locally cached SwiftData records.

### 6.2 Onboarding (FR-ONB)

- FR-ONB-1 MUST: After sign in, the app routes by server state: `needs_profile` -> `needs_voice` -> `complete`. `needs_voice` shows consent and enrollment with "Skip for now" (D4).
- FR-ONB-2 MUST: `profiles.onboarding_completed_at` is set by the backend, never directly by the client. It is set when a display name exists and the voice step is resolved: either an enrollment succeeded, or the user chose skip via `POST /me/onboarding/complete` with `{"voice_step": "skipped"}`.
- FR-ONB-2a TEMPORARY: Until the voice enrollment backend exists, the placeholder recorder's "Continue" calls the same endpoint with `{"voice_step": "placeholder"}`, which is treated as skipped (no voice profile is stored). Remove the `placeholder` value when FR-VOICE-3 ships.
- FR-ONB-3 MUST: Until onboarding is complete, project/meeting/task/chat endpoints return `403 onboarding_incomplete`.
- FR-ONB-4 MUST: After completion, the app shows `RootTabView` with Meetings selected.
- FR-ONB-5 MUST: A pending deep link (invite) captured before or during onboarding is handled after onboarding completes.

### 6.3 Voice consent and enrollment (FR-VOICE)

- FR-VOICE-1 MUST: Consent is stored as a row with `consent_version`, `granted_at`, and `revoked_at`. The consent text lives in the app bundle and its version string is sent with the grant.
- FR-VOICE-2 MUST: Enrollment upload is rejected unless the user has active consent.
- FR-VOICE-3 MUST: Enrollment accepts exactly 3 clips (A, B, C) as one multipart request, runs as a job in the existing sequential worker, and is prioritized ahead of queued meeting jobs (it must not interrupt a running job).
- FR-VOICE-4 MUST: Quality gates per Section 9.1. A failed job returns machine-readable reasons per clip.
- FR-VOICE-5 MUST: On success, store one L2-normalized 256-d embedding plus model id, quality metrics, and `enrolled_at`. Replace any previous voice profile atomically.
- FR-VOICE-6 MUST: Delete raw enrollment audio (uploaded files and normalized WAVs) when the job finishes, success or failure.
- FR-VOICE-7 MUST: The embedding is never returned by any API. Clients only see `{enrolled, enrolled_at, model_id}`.
- FR-VOICE-8 MUST: Revoking consent deletes the voice profile in the same transaction and sets `revoked_at`. It does not lock the account or reset onboarding.
- FR-VOICE-9 MUST: Re-recording follows the same gates and replaces the old profile only on success.

### 6.4 Projects and membership (FR-PROJ)

- FR-PROJ-1 MUST: Creating a project makes the creator an `owner` in `project_members` in the same transaction.
- FR-PROJ-2 MUST: `GET /api/v1/projects` returns only projects where the user is a member, with `role`, `member_count`, `last_activity_at`.
- FR-PROJ-3 MUST: Every project-scoped read and write (projects, meetings, audio, transcripts, summaries, decisions, tasks, evidence, chat, RAG search) checks membership in SQL. Non-members receive **404**, not 403, so they cannot learn that a resource exists.
- FR-PROJ-4 MUST: Permission matrix:

| Action | Owner | Member |
|--------|:-----:|:------:|
| View project, meetings, transcripts, tasks, calendar | yes | yes |
| Upload meeting, retry processing | yes | yes |
| Approve / edit / change status of tasks, undo | yes | yes |
| Use project chat | yes | yes |
| Rename project, change image | yes | no |
| Invite, revoke invites | yes | no |
| Change member roles, remove members | yes | no |
| Delete meetings, delete project | yes | no |
| Leave project | yes, unless last owner | yes |

- FR-PROJ-5 MUST: The last owner cannot leave or be demoted. They must promote another member first or delete the project.
- FR-PROJ-6 MUST: Record who did what: `projects.created_by`, `meetings.uploaded_by`, `tasks.approved_by` and `approved_at`, `tasks.assignee_user_id`, `task_audit_log.actor_id`.
- FR-PROJ-7 SHOULD: When a task's owner speaker is matched to a member, prefill `tasks.assignee_user_id` with that member. Approval still requires a user action and a due date (existing rule).
- FR-PROJ-8 MUST: `chat_conversations.user_id` is set on create; listing and reading conversations is limited to the creator (D10).

### 6.5 Invitations (FR-INV)

- FR-INV-1 MUST: Owners create invitations with `email` and `role`. Email is normalized (trimmed, lowercased).
- FR-INV-2 MUST: Creating an invitation for an email that is already a member returns 409. Re-inviting a pending email returns the existing invitation with a fresh token and expiry.
- FR-INV-3 MUST: Token is 32 random bytes, URL-safe base64. Only its SHA-256 hash is stored. Expiry is 7 days. Single use.
- FR-INV-4 MUST: Backend returns the invite URL; iOS shares it via the share sheet. No email service in v1.
- FR-INV-5 MUST: Invite URL opens the app (custom URL scheme `meetingapp://invite?token=...`, or a universal link if an associated domain is configured; see Section 17).
- FR-INV-6 MUST: Accept requires: authenticated, email verified, onboarding complete, invitation `pending` and not expired, and `lower(user.email) = invitation.email`. Otherwise return a specific error (`expired`, `revoked`, `email_mismatch`, `already_member`).
- FR-INV-7 MUST: Accepting inserts into `project_members` and marks the invitation `accepted` in one transaction.
- FR-INV-8 MUST: `GET /api/v1/invitations` returns pending invitations for the user's verified email, so invites appear in Profile even without the link.
- FR-INV-9 MUST: Owners can list and revoke pending invitations for their project.
- FR-INV-10 SHOULD: Rate limit invitation creation to 20 per user per hour.

### 6.6 Speaker identification (FR-SPK)

- FR-SPK-1 MUST: Diarization runs for every meeting processed by the server worker.
- FR-SPK-2 MUST: The worker keeps the per-speaker centroid embeddings returned by diarization (currently discarded in `ccb.transcribe`).
- FR-SPK-3 MUST: Matching follows Section 9.2 exactly: candidates limited to enrolled members of the meeting's project, one-to-one assignment, threshold and margin.
- FR-SPK-4 MUST: Each enrolled user has exactly one `attendees` row linked by `attendees.user_id`. A match links the transcript turns and `meeting_attendees` row to that attendee.
- FR-SPK-5 MUST: Display names: matched speaker -> `profiles.display_name` at processing time (snapshotted into `speaker_name`). Unmatched -> `SPEAKER_1..K` by first speaking time. Raw diarizer tag stays in `speaker_label`.
- FR-SPK-6 MUST: Store per cluster: `match_score`, `match_method` (`voice` or `none`), `embedding_model_id`.
- FR-SPK-7 MUST: If identification fails for any reason (no enrolled members, model error), the meeting still completes with all speakers as `SPEAKER_N`, and `meetings.model_metadata.speaker_identification` records the reason.
- FR-SPK-8 MUST: Never compare embeddings produced by different model ids. A voice profile with a stale model id is skipped and the user is prompted to re-record.
- FR-SPK-9 MUST: The extraction prompt receives the labeled transcript (names or `SPEAKER_N`), so evidence quotes and owner labels use those labels.

### 6.7 Profile tab (FR-PROF)

Sections, top to bottom:

1. FR-PROF-1 MUST **Identity header**: avatar (or initials), display name, title, email. Tap opens Edit Profile.
2. FR-PROF-2 MUST **Workspaces**:
   - Pending invitations at the top with Accept / Decline.
   - List of projects with role badge, member count, last activity. Tap opens the project in the Meetings tab.
3. FR-PROF-3 SHOULD **My tasks**: counts of approved tasks assigned to me that are open and overdue, across all my projects. Tap opens the Tasks tab filtered to me.
4. FR-PROF-4 MUST **Voice profile**: status (Enrolled on date / Not enrolled / Needs re-record because the model changed), "Re-record voice", "Revoke consent and delete voiceprint" (destructive, confirmation required).
5. FR-PROF-5 MUST **Integrations and notifications**: Apple Reminders and Calendar permission status with a button to open Settings when denied. (Push notifications are out of scope; show only permission status that exists today.)
6. FR-PROF-6 MUST **Privacy and data**: link to consent text and privacy policy, "Delete account".
7. FR-PROF-7 MUST **Account and security**: sign-in method (Email or Google), "Change password" (email users only), "Sign out".
8. FR-PROF-8 MUST **About**: app version and build, terms, privacy policy, support contact.

Project member management (invite, roles, remove) lives in **project settings** reached from the Meetings tab project header, not in Profile.

### 6.8 Account deletion (FR-ACCT)

- FR-ACCT-1 MUST: Available in-app from Profile, with a confirmation that requires typing `DELETE`.
- FR-ACCT-2 MUST: If the user is the last owner of a project that has other members, block deletion and list those projects ("transfer ownership first").
- FR-ACCT-3 MUST: Projects where the user is the only member are deleted with the account (cascade, including audio files via the existing purge path).
- FR-ACCT-4 MUST: Delete voice profile, consents, memberships, invitations created by them that are still pending, chat conversations, and the `profiles` row; then delete the Supabase auth user via the admin API.
- FR-ACCT-5 MUST: In shared projects, content remains (it is the project's meeting record). Attribution columns (`created_by`, `uploaded_by`, `approved_by`, `actor_id`, `assignee_user_id`) become NULL and the UI shows "Former member". The user's `attendees.user_id` is set NULL; existing `speaker_name` snapshots are left as is.

---

## 7. Data model changes

New migration(s) under `supabase/migrations/`. Use the live table names. Enable RLS on every new table with no `anon`/`authenticated` policies (D5).

```sql
-- citext for case-insensitive email
CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE profiles (
    id                       UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email                    CITEXT NOT NULL,
    display_name             VARCHAR(255),
    title                    VARCHAR(255),
    avatar_url               TEXT,
    auth_provider            VARCHAR(32) NOT NULL,          -- 'email' | 'google'
    onboarding_completed_at  TIMESTAMPTZ,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE voice_consents (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    consent_version  VARCHAR(32) NOT NULL,
    granted_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at       TIMESTAMPTZ
);
-- at most one active consent per user
CREATE UNIQUE INDEX voice_consents_one_active ON voice_consents(user_id) WHERE revoked_at IS NULL;

CREATE TABLE voice_profiles (
    user_id             UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
    embedding           vector(256) NOT NULL,     -- L2-normalized
    embedding_model_id  VARCHAR(128) NOT NULL,    -- e.g. 'pyannote/wespeaker-voxceleb-resnet34-LM@<rev>'
    quality             JSONB NOT NULL,           -- per-clip speech seconds, rms, clipping, pairwise cosine
    enrolled_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE voice_enrollment_jobs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    status        VARCHAR(16) NOT NULL DEFAULT 'queued'
                  CHECK (status IN ('queued','processing','succeeded','failed')),
    failure       JSONB,                          -- [{clip:'A', reason:'too_quiet'}, ...]
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at   TIMESTAMPTZ
);

CREATE TYPE project_role AS ENUM ('owner', 'member');

CREATE TABLE project_members (
    project_id  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    role        project_role NOT NULL,
    joined_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (project_id, user_id)
);
CREATE INDEX project_members_user ON project_members(user_id);

CREATE TABLE project_invitations (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id   UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    email        CITEXT NOT NULL,
    role         project_role NOT NULL DEFAULT 'member',
    token_hash   BYTEA NOT NULL UNIQUE,
    invited_by   UUID REFERENCES profiles(id) ON DELETE SET NULL,
    status       VARCHAR(16) NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending','accepted','declined','revoked')),
    expires_at   TIMESTAMPTZ NOT NULL,
    accepted_by  UUID REFERENCES profiles(id) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    responded_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX project_invitations_one_pending
    ON project_invitations(project_id, email) WHERE status = 'pending';
```

Changes to existing tables:

```sql
ALTER TABLE projects          ADD COLUMN created_by UUID REFERENCES profiles(id) ON DELETE SET NULL;
ALTER TABLE meetings          ADD COLUMN uploaded_by UUID REFERENCES profiles(id) ON DELETE SET NULL;
ALTER TABLE attendees         ADD COLUMN user_id UUID UNIQUE REFERENCES profiles(id) ON DELETE SET NULL;
ALTER TABLE meeting_attendees ADD COLUMN display_label VARCHAR(64),      -- 'Will' or 'SPEAKER_2'
                              ADD COLUMN match_score REAL,
                              ADD COLUMN match_method VARCHAR(16) NOT NULL DEFAULT 'none',
                              ADD COLUMN embedding_model_id VARCHAR(128);
ALTER TABLE tasks             ADD COLUMN assignee_user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
                              ADD COLUMN approved_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
                              ADD COLUMN approved_at TIMESTAMPTZ;
ALTER TABLE task_audit_log    ADD COLUMN actor_id UUID REFERENCES profiles(id) ON DELETE SET NULL;
ALTER TABLE chat_conversations ADD COLUMN user_id UUID REFERENCES profiles(id) ON DELETE CASCADE;
```

Notes:

- `attendees.voice_embedding` stays in place but is **not** used for user matching. User voiceprints live only in `voice_profiles` so biometric data has one, tightly controlled home.
- Unmatched speakers do not get an `attendees` row unless the existing pipeline already creates one; follow current behavior.
- Add indexes for every new FK used in membership joins.

---

## 8. API

All routes are under `/api/v1`, require `current_user` (FR-AUTH-6), and return JSON. Errors use `{"detail": "<code>", "message": "<human text>"}`.

### 8.1 Me

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/me` | Profile, `onboarding_step`, voice status, pending invite count |
| PATCH | `/me` | Update `display_name`, `title`, `avatar_url` |
| DELETE | `/me` | Delete account (FR-ACCT) |
| POST | `/me/onboarding/complete` | Body `{voice_step: "skipped" \| "placeholder"}`; sets `onboarding_completed_at` (FR-ONB-2, FR-ONB-2a) |
| POST | `/me/voice-consent` | Body `{consent_version}`; grant |
| DELETE | `/me/voice-consent` | Revoke + delete voice profile |
| GET | `/me/voice` | `{enrolled, enrolled_at, embedding_model_id, needs_rerecord}` |
| POST | `/me/voice-enrollments` | Multipart `clip_a`, `clip_b`, `clip_c`; returns `202 {job_id}` |
| GET | `/me/voice-enrollments/{job_id}` | `{status, failure}` |
| GET | `/me/tasks/summary` | `{open, overdue}` for tasks where `assignee_user_id = me` |

### 8.2 Projects and members

| Method | Path | Who |
|--------|------|-----|
| GET | `/projects` | member (only own projects) |
| POST | `/projects` | any onboarded user (becomes owner) |
| PATCH | `/projects/{id}` | owner |
| DELETE | `/projects/{id}` | owner |
| GET | `/projects/{id}/members` | member |
| PATCH | `/projects/{id}/members/{user_id}` | owner; body `{role}` |
| DELETE | `/projects/{id}/members/{user_id}` | owner, or the user themself (leave) |

### 8.3 Invitations

| Method | Path | Who |
|--------|------|-----|
| POST | `/projects/{id}/invitations` | owner; body `{email, role}`; returns `{invitation, invite_url}` |
| GET | `/projects/{id}/invitations` | owner; pending only |
| DELETE | `/projects/{id}/invitations/{inv_id}` | owner; revoke |
| GET | `/invitations` | me; pending invites for my verified email |
| POST | `/invitations/{inv_id}/accept` | me |
| POST | `/invitations/{inv_id}/decline` | me |
| POST | `/invitations/accept-token` | me; body `{token}` (from deep link) |

### 8.4 Existing routes

- Every existing `/api/v1/...` route in `src/labsync/api/` gains `current_user` plus a membership check in its SQL.
- `POST /api/v1/meetings/upload` sets `uploaded_by`.
- Task review/state/revert routes set `approved_by`, `approved_at`, `actor_id`.
- `GET /api/meetings/{id}/audio` must check membership (audio is the most sensitive artifact).
- Legacy unscoped routes in `server.py` (`/api/meetings`, `/api/meetings/{id}`, retry): see Section 17.
- The static shared token middleware is removed in Phase 7 once the iOS app sends JWTs.

---

## 9. Voice enrollment and speaker identification spec

### 9.1 Enrollment recording and quality gates

Recording on iOS: `AVAudioRecorder`, mono, AAC `.m4a`, 48 kHz. The backend normalizes to 16 kHz mono WAV with the existing ffmpeg path.

Script (shown on screen, original text, safe to ship):

- **Clip A (read, about 15 s):** "Thanks for joining today. Before we start, here is a quick update on the project. We finished the first round of testing on Tuesday, and most of the results look good. There are still two open issues with the upload screen, and I would like both of them fixed by the end of next week."
- **Clip B (read, about 15 s):** "Let's go over the action items. Maya will send the budget draft by Thursday, and Jordan will check the numbers for March, April, and May. If anything changes, please post it in the shared channel so everyone sees it before our next meeting."
- **Clip C (free speech, at least 15 s):** "In your own words, describe what you worked on last week or what you plan to do this week."

Clip C matters: spontaneous speech is closer to meeting speech than reading aloud.

Quality gates (run per clip after VAD; all thresholds are config values in one module):

| Gate | Default | Failure reason |
|------|---------|----------------|
| Net speech duration (A, B) | >= 8 s | `too_short` |
| Net speech duration (C) | >= 10 s | `too_short` |
| Total net speech | >= 30 s | `too_short` |
| Clipping (samples at full scale) | < 1% | `too_loud` |
| Speech RMS level | within configured range | `too_quiet` / `too_loud` |
| Single speaker: diarization finds one speaker per clip | exactly 1 | `multiple_voices` |
| Consistency: pairwise cosine between the 3 clip embeddings | >= `ENROLL_CONSISTENCY_MIN` (provisional 0.65) | `inconsistent` |

Embedding: compute one embedding per clip with the same WeSpeaker model the diarization pipeline uses (D9), L2-normalize each, average, L2-normalize the average. Store with `embedding_model_id`.

### 9.2 Matching algorithm (per meeting)

Inputs: diarization clusters `c_1..c_n` with centroid embeddings and speech durations; candidates `u_1..u_m` = members of the meeting's project with an active voice profile whose `embedding_model_id` equals the current model.

1. If `m = 0` or diarization produced no embeddings: all clusters unmatched; record reason.
2. Drop clusters with total speech < `MIN_CLUSTER_SPEECH_S` (provisional 5 s) from matching; they stay unmatched.
3. L2-normalize centroids. Build cosine similarity matrix `S[n x m]`.
4. One-to-one assignment maximizing total similarity (`scipy.optimize.linear_sum_assignment` on `-S`).
5. Accept an assigned pair `(c_i, u_j)` only if:
   - `S[i, j] >= SPEAKER_MATCH_THRESHOLD` (provisional 0.60), and
   - `S[i, j] - second_best_i >= SPEAKER_MATCH_MARGIN` (provisional 0.10), where `second_best_i` is the highest similarity of `c_i` to any other candidate.
6. Unaccepted clusters are unmatched.
7. Order unmatched clusters by their first turn's `start_time_ms` and label them `SPEAKER_1`, `SPEAKER_2`, ...
8. Persist in one transaction with the transcript rows (FR-SPK-4 to FR-SPK-6).

The provisional thresholds must be calibrated in Phase 5 (Section 14.3) and then written into config with the calibration date and dataset in a comment. Bias toward precision: when in doubt, leave the speaker unmatched.

---

## 10. iOS client spec

### 10.1 App state machine

`AppSession` (an `@Observable` object injected at the root) drives the root view:

```
launching
  -> signedOut                    -> WelcomeView / SignUpView / SignInView / CheckEmailView
  -> signedIn(onboarding: step)   -> OnboardingFlow (profile, consent, mic, tips, record, processing)
  -> signedIn(complete)           -> RootTabView (Meetings selected)
```

The step comes from `GET /me`, never from local flags. A pending invite token is stored in `AppSession` and handled once the state is `complete`.

### 10.2 New and changed files (suggested layout, match existing style)

- `Auth/AppSession.swift`, `Auth/SupabaseAuthService.swift`
- `Views/Auth/WelcomeView.swift`, `SignUpView.swift`, `SignInView.swift`, `CheckEmailView.swift`, `ResetPasswordView.swift`
- `Views/Onboarding/OnboardingFlow.swift`, `ProfileStepView.swift`, `VoiceConsentView.swift`, `MicPermissionView.swift`, `RecordingTipsView.swift`, `VoiceRecordingView.swift`, `EnrollmentProcessingView.swift`
- `Views/Profile/ProfileTab.swift` plus one view per section in 6.7, `EditProfileSheet.swift`, `DeleteAccountView.swift`
- `Views/Projects/ProjectSettingsView.swift`, `MembersListView.swift`, `InviteSheet.swift`, `InvitationAcceptSheet.swift`
- `Resources/VoiceConsent.md` (consent text with a version string)
- `RootTabView.swift`: add the Profile tab (D12), add `Tab.profile`.
- `MeetingAPIClient.swift`: replace static `APIToken` with the session access token; refresh on 401.
- Deep link handling in `MeetingAppApp.swift` (`onOpenURL`) for auth redirects and invites.

### 10.3 Local cache

- SwiftData store is wiped on sign out and when a different user signs in (compare stored `user_id`).
- `SeedData` must not load into a signed-in user's store.

### 10.4 UI quality

- Follow the existing visual style (`Views/Shared`, `AvatarView`, `Color+Hex`).
- Recording screen: large script text that supports Dynamic Type, visible level meter, clear Re-record. VoiceOver labels on every control.
- Every error state has a specific message and an action.

---

## 11. Non-functional requirements

### Security

- NFR-SEC-1: JWT verification uses the Supabase project's JWKS (asymmetric signing keys) with caching; reject tokens with wrong `aud`, wrong `iss`, or expired `exp`. If the project still uses the legacy HS256 secret, read it from server env only.
- NFR-SEC-2: Membership is enforced in SQL on every project-scoped query (join on `project_members` with `user_id = $current_user`). No endpoint loads a row by id and checks membership afterward in Python.
- NFR-SEC-3: Non-member access returns 404 (FR-PROJ-3).
- NFR-SEC-4: The iOS bundle contains only the Supabase URL and anon key (public by design). No service-role key, DB URL, or shared API token ships in the app after Phase 7.
- NFR-SEC-5: Invite tokens: 256-bit random, stored hashed, single use, 7-day expiry, email-bound.
- NFR-SEC-6: Logs never contain access tokens, invite tokens, or embeddings.
- NFR-SEC-7: RLS enabled with no `anon`/`authenticated` policies on all tables (D5). Add a test that queries each table through the Supabase REST API with an authenticated user token and expects zero rows or a permission error.

### Privacy and biometrics

- NFR-PRIV-1: Voice embedding is biometric data. Collect only after recorded consent; keep a consent history.
- NFR-PRIV-2: Raw enrollment audio is deleted after processing (D11). Embeddings are deleted on consent revocation and account deletion, immediately.
- NFR-PRIV-3: Embeddings are used only for matching within projects the user belongs to (D7) and never exposed by the API (FR-VOICE-7).
- NFR-PRIV-4: A written retention period for voiceprints is shown in the consent text (see Section 17).

### Accuracy

- NFR-ACC-1: On the evaluation set (Section 14.3), named-speaker precision >= 0.95 (at most 1 in 20 named clusters is wrong). Recall is reported, not gated.
- NFR-ACC-2: Results are written to the evaluation harness output with the thresholds used.

### Performance

- NFR-PERF-1: Enrollment job finishes in <= 15 s p95 on the M4 Mac when no meeting job is running.
- NFR-PERF-2: Matching adds <= 2 s to meeting processing beyond diarization.
- NFR-PERF-3: `/me`, `/projects`, `/invitations` respond in <= 300 ms p95 on the server, excluding network.
- NFR-PERF-4: Peak memory stays inside the existing sequential worker budget (models are not loaded concurrently).

### Reliability

- NFR-REL-1: Speaker identification failure never fails a meeting (FR-SPK-7).
- NFR-REL-2: All multi-row changes (accept invite, account deletion, enrollment replace, meeting persistence) are single transactions.
- NFR-REL-3: Enrollment and meeting jobs survive a server restart the same way meeting jobs do today (follow the existing worker's recovery behavior).

### Maintainability

- NFR-MAIN-1: All thresholds live in one config module with comments.
- NFR-MAIN-2: Update `docs/writeups/Tech Stack.md` (embedding dim) and `docs/writeups/systems/Acoustic Ingestion & Diarization Pipeline.md` to match what ships.
- NFR-MAIN-3: Lint and type checks pass for Python; Swift builds with no new warnings.

### Platform

- NFR-PLAT-1: In-app account deletion is required for App Store apps that support account creation (FR-ACCT).
- NFR-PLAT-2: Apps that offer a third-party login such as Google are generally required by App Store Review Guideline 4.8 to also offer an equivalent privacy-focused login (Sign in with Apple qualifies). Confirm against the current guideline before App Store submission (Section 17).

---

## 12. Security and privacy model (summary)

```
iOS app --(Supabase Auth: sign up/in, OAuth, refresh)--> Supabase Auth
iOS app --(Bearer JWT)--> Cloudflare Tunnel --> FastAPI (verifies JWT, enforces membership)
FastAPI --(privileged psycopg role)--> Postgres (RLS deny-all for anon/authenticated)
FastAPI worker --> diarization + embeddings on M4 --> voice_profiles / meeting_attendees
```

Trust boundaries: the client is untrusted; FastAPI is the only path to project data; voiceprints never cross back to any client.

---

## 13. Migration of existing data

1. Create an owner account for the current operator (Will) through normal sign up.
2. A one-off script (or SQL in the migration guarded by an env-provided user id) sets `projects.created_by` and inserts `project_members(owner)` for all existing projects.
3. Existing `chat_conversations` get `user_id` = that owner.
4. Existing meetings keep their current speaker labels. No retroactive identification (non-goal).
5. Keep the static token middleware until the iOS build with JWT support is installed on all test devices, then remove it (Phase 7).

---

## 14. Testing and acceptance

### 14.1 Backend tests (pytest, `tests/`)

- `current_user`: valid token, expired, wrong audience, wrong issuer, missing header. Use locally generated keys and a test JWKS.
- Isolation: user B gets 404 on every project-scoped endpoint for user A's project (parametrize over the route list so new routes are covered).
- Onboarding gate: data endpoints return `403 onboarding_incomplete` before completion.
- Roles: each row of the permission matrix in FR-PROJ-4.
- Last-owner rules (FR-PROJ-5).
- Invitations: create, duplicate, re-invite, accept, email mismatch, expired, revoked, already member, accept-token, token stored hashed.
- Voice: consent required, revoke deletes profile, embedding never in responses, raw audio files removed after job.
- Matching (pure function, synthetic vectors): one-to-one assignment, threshold reject, margin reject, short cluster skipped, `SPEAKER_N` numbering by first appearance, no candidates, model id mismatch skipped.
- Account deletion: blocked when last owner with members, cascade otherwise, attribution set NULL.
- RLS deny test (NFR-SEC-7).

### 14.2 iOS tests

- Unit: `AppSession` routing for each server state; token refresh on 401; cache wipe on sign out and on user switch.
- UI / end-to-end on simulator: sign up -> verify -> onboarding -> Meetings is selected; Profile tab shows all sections; invite link while signed out -> sign up -> onboarding -> invite sheet -> project visible.

### 14.3 Speaker identification evaluation

Extend the existing harness (`src/labsync/evaluation.py`, `tests/benchmarks/`) with an identification benchmark:

- Use AMI speakers who appear in multiple meetings. Build each speaker's "enrollment" from about 45 s of their speech in other meetings, then run diarization + matching on a held-out meeting.
- Include impostor trials: enrolled members who are not in the meeting, and speakers in the meeting who are not enrolled.
- Report named-speaker precision, recall, and the unmatched rate at a grid of thresholds and margins. Pick defaults that meet NFR-ACC-1 with the best recall.
- Add at least one real app recording (phone on a table) to check the close-talk vs far-field gap.

### 14.4 Acceptance criteria

1. A new email user signs up, verifies, completes onboarding with a voice recording, and lands on Meetings.
2. A returning user with onboarding complete goes straight to Meetings on a new device.
3. A user sees only projects they belong to; direct API calls to another project return 404.
4. An owner invites a coworker by email; the coworker accepts via the link and sees the project and its meetings.
5. In a meeting with two enrolled members and one guest, the members are labeled by name and the guest is `SPEAKER_1`.
6. A member who revokes voice consent appears as `SPEAKER_N` in the next processed meeting.
7. The Profile tab shows every section in FR-PROF-1 to FR-PROF-8.
8. Account deletion works and follows FR-ACCT rules.
9. All existing tests still pass.

---

## 15. Implementation plan

Each phase ends with its verification passing.

1. **Schema + backend auth**: migrations (Section 7), `current_user` dependency, profile upsert, membership-scoped queries for all existing routes, data backfill (Section 13). Keep the static token middleware for now.
   Verify: existing tests pass; JWT and isolation tests pass.
2. **Projects, members, invitations API** (8.2, 8.3).
   Verify: role matrix, last-owner, and invitation tests pass.
3. **iOS auth + session + routing**: Supabase sign up/in, Google OAuth, check-email, reset password, `AppSession`, JWT in `MeetingAPIClient`, cache wipe, Profile tab placeholder in `RootTabView`.
   Verify: simulator E2E sign up -> Meetings; unit tests for routing.
4. **Voice consent + enrollment**: backend job, quality gates, `voice_profiles`; iOS onboarding flow with recording UI.
   Verify: enrollment tests; manual run on device in a quiet and a noisy room (noisy should fail with a clear reason).
5. **Speaker identification in the pipeline**: diarization always on in the server path, keep centroid embeddings, matching, persistence, extraction uses labels, task assignee prefill. Run the evaluation and set thresholds.
   Verify: matching unit tests; benchmark meets NFR-ACC-1; acceptance criterion 5 on a real recording.
6. **Profile tab and project settings UI**: all sections in 6.7, members list, invite sheet with share link, invite acceptance sheet, deep links, account deletion.
   Verify: acceptance criteria 1 to 8.
7. **Hardening**: remove static token middleware and `APIToken` config, rate limits, update docs listed in NFR-MAIN-2.
   Verify: full test suite, lint, Swift build with no new warnings, acceptance criterion 9.

---

## 16. Out of scope / future

- Manual speaker relabel: let a member assign a `SPEAKER_N` cluster in one meeting to a project member or a free-text name (never updates embeddings).
- Re-identify speakers in past meetings when a member enrolls or joins.
- Transactional invite emails.
- Organizations and org-wide directory.
- Sign in with Apple (but see NFR-PLAT-2), 2FA.
- Push notifications for invites and processed meetings.

---

## 17. Open questions (ask the owner, do not decide silently)

1. **Legacy routes**: should `/api/meetings`, `/api/meetings/{id}`, and `/api/meetings/{id}/retry` in `server.py` be removed or moved behind auth and membership? Default if unanswered: put them behind auth and membership, and flag it.
2. **Invite links**: custom URL scheme only, or set up a universal link on a domain served through the Cloudflare tunnel? Default: custom URL scheme.
3. **Voiceprint retention period** shown in the consent text (for example: until revoked, account deleted, or N years of inactivity). Biometric privacy laws such as Illinois BIPA set specific rules here; the owner should confirm the policy.
4. **Sign in with Apple**: confirm whether App Store Guideline 4.8 requires adding it alongside Google before submission.
5. **Mandatory enrollment vs. consent**: requiring biometric consent to use the app may conflict with some privacy regimes (for example GDPR treats consent as not freely given when a service is conditioned on it). Confirm the target users and regions.