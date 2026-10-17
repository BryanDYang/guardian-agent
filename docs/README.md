# Documentation and repository map

Start with [the current architecture](architecture.md) to understand how the app,
backend, storage, models, and email worker connect. Use the root
[README](../README.md) to set up a working environment.

## Choose the right document

| Question | Read |
| --- | --- |
| How does the application actually work? | [Current architecture and troubleshooting](architecture.md) |
| How do I run it? | [Root setup guide](../README.md), [shared-backend operations](shared_backend.md) |
| What remains for this milestone? | [Milestone 3 roadmap](milestone_3/roadmap.md), [scope and acceptance](milestone_3/scope_and_acceptance.md) |
| How do I test task email or auto-approval? | [Immediate follow-through](milestone_3/follow_through.md) |
| What has actually been tested? | [Native walkthrough](demo_walkthrough.md), [weekly journal](weekly_journal.md), versioned tests and evaluation reports |
| How do I contribute and run checks? | [Contributing](../CONTRIBUTING.md), [CI workflow](../.github/workflows/ci.yml) |
| Why were some designs considered? | [Design writeups](writeups/README.md); these are not current implementation specifications |
| How should we simplify the repo? | The staged plan below |

## Repository ownership

```text
guardian-agent/
  README.md                 Setup and links to current architecture
  pyproject.toml, uv.lock    Python dependencies and CLI entry point
  src/labsync/              Python application and evaluation code
    api/                    HTTP routes and authorization boundary
    db/                     SQL access and persistence
    server.py               App wiring and legacy local processing/routes
    shared_backend.py       Shared audio processing and related routes
    shared_jobs.py          Durable job ownership/recovery
    pipeline.py             One audio-to-extraction attempt
    ccb.py, voice.py         Audio adapter and voice enrollment/matching
    extraction.py           Transcript/extraction contracts and evidence checks
    providers.py            Text-model provider selection
    chat.py, embeddings.py  Grounded answers and text vectors
    followup.py             Approval eligibility and immediate email delivery
  ios/MeetingApp/           Native Xcode project
    MeetingApp/
      Auth/                 Session and sign-in
      Models/, Data/        SwiftData models, cache, previews
      Networking/           API client, sync, OS reminders
      Navigation/, Views/   Presentation and navigation
    MeetingAppTests/        Native tests
  supabase/migrations/      Ordered database schema changes
  tests/                    Python tests and versioned fixtures
  scripts/                  Setup/check helpers and local debugging utilities
  docs/                     Current guides, milestone evidence, design history
  db/schema.sql             Historical initial schema, not current full schema
```

These local directories/files are a separate category:

- `contexts/`: gitignored external transcriber, datasets, reference repositories,
  course materials, and exploratory notes. Some are runtime prerequisites; most
  are references. A fresh clone does not contain them.
- `artifacts/`: gitignored recordings, processing logs, saved runs, and local test IDs.
- `.env`, `.venv/`, model caches: private configuration and generated dependencies.
- Root `meeting_transcriber.py`: currently an untracked local file. The normal
  CLI source path points to `contexts/meeting_transcriber-master`; the root copy
  is not automatically the runtime dependency. Do not delete or edit it assuming
  it is redundant without checking provenance and local use.

## Simplification plan

The aim is fewer competing explanations and clearer responsibility boundaries.
Avoid adding a framework, service layer, message broker, or generic plugin system
unless an actual requirement calls for one.

### 1. Make the existing repo understandable first

Done in this documentation pass:

- Add one current architecture guide with data flows, code entry points, storage
  ownership, security/provider boundaries, and symptom-to-code troubleshooting.
- Add this documentation index and distinguish current guides, acceptance
  evidence, design proposals, historical schema, and local-only material.
- Correct the root pipeline summary and link readers to implementation details.
- Mark older tech-stack/workflow descriptions as design history where they can
  otherwise be mistaken for implemented behavior.

Next: reconcile the milestone submission/checklist against recorded acceptance.
Keep remaining claims tied to evidence rather than mechanically marking boxes.

### 2. Make the external audio dependency reproducible

This is the biggest clean-install obstacle: a fresh clone requires an ignored
folder copied from a teammate. First document its exact upstream revision,
license, required functions, and dependency versions. Then choose a pinned package
or a deliberately maintained vendored subset. Preserve provenance and verify the
same audio fixture before changing the import path. Do not copy the entire local
reference directory into application source.

Finished when a teammate can build the audio path from documented, versioned
inputs without receiving an unexplained folder privately.

### 3. Separate HTTP wiring from background work

`server.py` and `shared_backend.py` each mix app setup, routes, and processing.
First move shared upload/audio/delete routes into explicit API modules while
keeping endpoint contracts unchanged. Keep lease logic in `shared_jobs.py` and
one-attempt processing in `pipeline.py`. Move worker startup/configuration to a
small app assembly module only when needed by that extraction.

Decide whether local filesystem processing is still a supported product mode.
If yes, document and test it as such. If no, retire it in a separate change after
inventorying local recordings and migration/recovery needs. Shared mode should
be the main onboarding path; deleting the legacy path prematurely could orphan data.

Finished when someone can find an endpoint without searching two competing
server implementations and can test worker processing independently of routes.

### 4. Split the large iOS network file by responsibility

`MeetingAPIClient.swift` currently contains transport, many feature methods,
response models, and date helpers. Preserve one authenticated transport and the
existing public behavior; move feature methods into extensions/files for meetings,
tasks, projects/accounts, chat, and follow-through. Group response models by the
same features. Avoid introducing one separate networking framework per screen.

Then clarify the boundary between server DTOs, SwiftData cache models, and the
code that applies DTOs. Review `ProjectSync`, `TaskSync`, and
`RemoteMeetingApplier` together before consolidating their overlapping paths.

Finished when a task API change has a predictable home and every server record
has an explicit cache-update path. Verify sign-in, refresh, reprocessing, and relaunch.

### 5. Keep approval policy, outbox storage, and email transport distinct

`followup.py` currently holds all three. As the reminder lifecycle is added,
extract policy eligibility, outbox SQL, and provider transport into named modules
rather than adding scheduling branches to the current worker loop. Do this around
actual reminder requirements, preserving atomic approval/queue insertion and
stable provider retry keys. Do not build a general workflow engine.

Finished when a policy test does not require email transport and a transport
change does not alter task approval semantics.

### 6. Organize evidence without losing its meaning

Group tests by subsystem when navigation becomes difficult, keeping fixture and
cross-project isolation checks easy to find. Document which tests require a real
local PostgreSQL database, which replace inference, and which call real providers.
The current CI's plain `pytest` skips database-dependent tests unless
`TEST_DATABASE_URL` is configured; a green smoke run is not full integration proof.

Consider adding a disposable PostgreSQL/pgvector CI job with the minimum Auth and
Storage test schemas and all migrations. This would make new persistence and
outbox failures visible on every PR instead of relying on a developer's local run.

Version the small fixtures/configuration/expectations that make results
reproducible. Keep private audio and bulky outputs out of Git. Link representative
results into the walkthrough rather than copying progress claims into many documents.

## Change order and verification

Do these as small, behavior-preserving changes, one boundary at a time:

1. Documentation and reproducible dependency setup.
2. Backend route/worker separation.
3. iOS transport/DTO organization and explicit cache application.
4. Reminder-driven policy/outbox separation and stronger integration CI.

Before each code move, establish the relevant integration tests and one native
acceptance path. Afterward, compare behavior using the same inputs and API
contracts. Do not mix repo reorganization with model tuning, new automation, or
large schema changes in one PR.
