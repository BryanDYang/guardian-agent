> **Historical design/reference:** Preserved for rationale and context. Use [current architecture](../../../architecture.md) for implementation and [the roadmap](../../../milestone_3/roadmap.md) for current work.

The Mobile OS Integration Service is the native device bridge built around Apple's **EventKit framework (`EKEventStore`)** and iOS system services that synchronizes meeting intelligence directly with the native iOS ecosystem. It translates AI-extracted deliverables into OS-level calendar events and reminders while extracting schedule context to improve transcription accuracy.

**1. Calendar Context & Attendee Candidate Matching**

- **Time-Window Inspection:** When a user selects a meeting recording, the service queries `EKEventStore` for calendar entries matching the audio recording's start timestamp and duration.
    
- **Attendee Extraction:** Pulls the invitee list, participant names, and email addresses directly from the matched calendar event.
    
- **Biometric Resolution Input:** Hands these attendee candidates to the backend pipeline, giving the x-vector diarization engine an initial candidate list to attribute speaker turns and resolve profile initials before falling back to generic speaker labels.
    

**2. Native Task Synchronization (Apple Reminders & Calendar)**

- **Approved Task Export:** When a user taps **Approve** on an extracted action item in the human-in-the-loop review stack, the service generates a native `EKReminder` in Apple Reminders under a project-specific list.
    
- **Milestone & Due Date Scheduling:** Assigns explicit due dates, priority tags, and work-block calendar alerts directly to Apple Calendar (`EKEvent`).
    
- **Bidirectional Identifier Tracking:** Persists the generated external reminder identifier directly into the database as `TASKS.eventkit_reminder_id`. This enables the app to update, reschedule, or delete the native reminder whenever the task is edited or transitioned to "Done" or "Dropped".
    

**3. Zero-Backend Notification Architecture**

- **Local Notification Offloading:** The MVP scope explicitly excludes building and maintaining an external cloud push notification server (such as an APNs gateway or webhooks).
    
- **Native System Alerts:** By writing approved tasks directly to Apple Reminders with scheduled alert times, the app delegates all deadline notifications, badges, and lock-screen alerts to iOS itself.
    

**4. System File & Media Ingestion**

- **Share Sheet & Document Picker Support:** Integrates with `UIDocumentPickerViewController` and the system Share Sheet extension, allowing users to route `.mp3` and `.m4a` recordings directly into the app from Voice Memos, Files, or Zoom exports.
    
- **Sandboxed Handoff:** Stages imported files into the app's local sandbox before initiating background uploads over `URLSessionConfiguration.background`.
    

**5. Privacy & Permission Management**

- **Access Authorization:** Negotiates native permission dialogs for calendar and reminder access (`EKEntityTypeEvent` and `EKEntityTypeReminder`), gracefully adapting the UI if access is restricted.
    
- **Consent Gating Coordination:** Pairs OS-level permissions with the app's mandatory consent gating modal, blocking ingest workflows until participant recording compliance is explicitly certified.