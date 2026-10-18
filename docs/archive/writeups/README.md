> **Historical design/reference:** Preserved for rationale and context. Use [current architecture](../../architecture.md) for implementation and [the roadmap](../../milestone_3/roadmap.md) for current work.

# Design writeups and reference material

These documents explain proposed systems, earlier technology choices, and upstream
capabilities. They are useful design history, but some describe functionality that
is not implemented or differs from the current application.

For current behavior and code entry points, use [Current architecture](../../architecture.md).
For tested behavior and limitations, use the [native walkthrough](../../evidence/demo_walkthrough.md)
and [Milestone 3 roadmap](../../milestone_3/roadmap.md).

Examples of distinctions to preserve:

- Proposed WebSocket status updates versus current meeting polling and project SSE.
- Proposed streamed audio versus current authenticated temporary-file playback.
- Upstream calendar/attendee matching versus the application's explicit
  speaker/account review and provisional voice matching.
- One-time Apple Reminders export versus backend task email versus the unfinished
  recurring reminder lifecycle.
- Initial model/database proposals versus the versions and schema in current code.

`PREBUILT_TRANSCRIBER.md` describes the external transcriber, not a promise that
all its standalone features are integrated into LabSync.
