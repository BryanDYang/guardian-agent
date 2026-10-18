> **Historical design/reference:** Preserved for rationale and context. Use [current architecture](../../../architecture.md) for implementation and [the roadmap](../../../milestone_3/roadmap.md) for current work.

The Native Presentation System (SwiftUI) is the client-side interface of the app, organizing meeting artifacts into a 3-tab navigation hierarchy—Meetings, Tasks, and Chat—while coordinating audio playback, consent checks, and background pipeline states.

**1. Meetings View & Meeting Detail Hub** Serves as the app’s default landing screen, structured to handle multi-project tracking and meeting inspection:

- **Project & Session Management:** Displays visual project cards with customized images and titles, supports adding new projects, and lists each project's associated meetings annotated with meeting dates, audio durations, and source file metadata.
    
- **Consent Gating & Ingestion:** Prompts users with a mandatory consent gating modal that blocks upload execution until participant recording consent is explicitly verified, taking files shared via iOS Document Picker or System Share Sheets.
    
- **Summary & Decisions View:** Displays LLM-generated meeting takeaways alongside a structured consensus ledger detailing explicit decisions reached during the conversation.
    
- **Human-in-the-Loop Task Review:** Renders a card stack of AI-extracted action items attributed to specific speakers with their profile initials, suggested due dates, and verbatim transcript citations as proof. Users can individually **Approve**, **Edit**, or **Dismiss** each item.
    
- **Interactive Transcript Feed:** Presents a diarized conversational turn feed labeled by attendee names and initials, with timestamps linked directly to playback.
    
- **Attendee Storylines:** Lists all detected participants; tapping an attendee opens their subjective storyline detailing their point of view on _what they want_, _what they see_, and _what they discuss_.
    

**2. Tasks View (Calendar & State Machine)** Acts as an operational calendar dashboard that aggregates tasks approved from the Meetings view:

- **Multi-Scale Calendar Component:** Provides scrolling across years, months, and days to visualize deadlines and deliverables.
    
- **3-State Lifecycle Controls:** Tasks default to the **Open** state; tapping the check button marks the task as **Done**, while tapping the trash button transitions it to **Dropped**.
    
- **Workstream Filtering:** Includes project-level filters so users can isolate commitments tied to a single project or view all active tasks.
    
- **EventKit Synchronization:** Triggers updates directly to native Apple Reminders and Apple Calendar upon task approval.
    

**3. Chat View (Project-Scoped RAG Interface)** Provides conversational retrieval over historical meeting sessions:

- **Natural Language Meeting Q&A:** Allows users to query the local vector and full-text database across previous syncs.
    
- **Inline Citation Chips:** Renders verifiable reference tags (displaying meeting name and timestamp) that allow users to jump straight to the source audio.
    
- **Grounded Refusal Display:** Natively surfaces explicit refusal messages (displaying "I don't know") when queries fall outside the bounds of recorded context.
    
- **Chat History & Project Filtering:** Manages prior chat threads, allowing users to start new sessions or filter conversational histories between "All" and specific project boundaries.
    

**4. Performance & Concurrency Architecture**

- **Non-Blocking Concurrency:** Built with Swift 6 modern concurrency (`async/await`, `TaskGroup`, `Actors`) to parse large transcript arrays and render LLM streaming responses without freezing the main UI thread.
    
- **Real-Time Processing Progress:** Integrates with backend WebSockets via `URLSessionWebSocketTask` to render live pipeline status cards (_"Transcribing..."_, _"Diarizing..."_, _"Extracting Tasks..."_) while heavy sequential workloads process on the backend.




## API specification

### api/v1

| **Endpoint**                      | **Method** | **Auth Required** | **Request Body / Query**                                                                                                               | **Status Codes**                                                                                    | **Description**                                                                                                                                                                                               |
| --------------------------------- | ---------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/projects`                       | `GET`      | Yes               | _None_                                                                                                                                 | `200 OK`, `401 Unauthorized`                                                                        | Fetches all tracked projects with metadata, card images, and meeting counts for the primary landing screen.                                                                                                   |
| `/projects`                       | `POST`     | Yes               | **Body (JSON):**<br>`{ "name": string, "image_path": string? }`                                                                        | `201 Created`, `400 Bad Request`, `401 Unauthorized`                                                | Creates a new project scoping boundary for grouping meetings, tasks, and search retrieval.                                                                                                                    |
| `/projects/{project_id}/meetings` | `GET`      | Yes               | **Query:**<br>`limit: int?`, `offset: int?`                                                                                            | `200 OK`<br><br>`401 Unauthorized`<br><br>`404 Not Found`                                           | Lists meeting cards under a target project, annotated with meeting dates, audio durations, and source file metadata.                                                                                          |
| `/meetings/upload`                | `POST`     | Yes               | **Multipart Form:**<br>`file: audio/mp3`, `project_id: UUID`, `consent_confirmed: bool`                                                | `202 Accepted`<br><br>`400 Bad Request`<br><br>`401 Unauthorized`<br><br>`422 Unprocessable Entity` | Enforces consent gating verification; queues audio normalization and sequential processing in the async worker; returns `job_id` and initial meeting metadata.                                                |
| `/ws/pipeline/{job_id}`           | `WS`       | Yes               | **Query:**<br>`token: string`                                                                                                          | `101 Switching Protocols`<br><br>`4001 Unauthorized`                                                | Streams real-time pipeline progression events (_"Transcribing..."_, _"Diarizing..."_, _"Extracting Tasks..."_, _"Complete"_) over a persistent WebSocket.                                                     |
| `/meetings/{meeting_id}`          | `GET`      | Yes               | _None_                                                                                                                                 | `200 OK`<br><br>`401 Unauthorized`<br><br>`404 Not Found`                                           | Retrieves the meeting detail payload: structured summary bullets, consensus decisions ledger, diarized transcript turns, and attendee storylines (_what they want, see, discuss_).                            |
| `/meetings/{meeting_id}`          | `DELETE`   | Yes               | _None_                                                                                                                                 | `200 OK`<br><br>`401 Unauthorized`<br><br>`404 Not Found`                                           | Purges relational meeting records and safely moves the source audio file to macOS `~/.Trash` via `send2trash` for recoverable deletion.                                                                       |
| `/tasks`                          | `GET`      | Yes               | **Query:**<br>`project_id: UUID?`, `start_date: date?`, `end_date: date?`, `status: string?`                                           | `200 OK`<br><br>`401 Unauthorized`                                                                  | Fetches tasks filtered across year, month, and day ranges to render the operational calendar view and project-specific workstreams.                                                                           |
| `/tasks/{task_id}`                | `PATCH`    | Yes               | **Body (JSON):**<br>`{ "action": "approve"/ "edit"/ "dismiss", "assignee_id": UUID?, "task_description": string?, "due_date": date? }` | `200 OK`<br><br>`400 Bad Request`<br><br>`401 Unauthorized`<br><br>`404 Not Found`                  | Executes human-in-the-loop review actions on generated task cards; returns formatted payloads to sync approved tasks directly into Apple Reminders and Calendar via EventKit.                                 |
| `/tasks/{task_id}/state`          | `POST`     | Yes               | **Body (JSON):**<br>`{ "status": "open"/"done"/ "dropped" }`                                                                           | `200 OK`<br><br>`400 Bad Request`<br><br>`401 Unauthorized` <br><br>`404 Not Found`                 | Updates the task across its 3 explicit lifecycle states; appends the state diff to `task_audit_log` and returns a revert token.                                                                               |
| `/tasks/{task_id}/revert`         | `POST`     | Yes               | **Body (JSON):**<br>`{ "revert_token": string }`                                                                                       | `200 OK`<br><br>`400 Bad Request`<br><br>`401 Unauthorized`<br><br>`404 Not Found`                  | Undoes a task status mutation by verifying the cryptographic revert token against the immutable audit ledger.                                                                                                 |
| `/chat/sessions`                  | `GET`      | Yes               | **Query:**<br>`project_id: UUID?`                                                                                                      | `200 OK`<br><br>`401 Unauthorized`                                                                  | Retrieves conversational history threads, supporting both global "all" session listings and project-filtered views.                                                                                           |
| `/chat/sessions`                  | `POST`     | Yes               | **Body (JSON):**<br>`{ "project_id": UUID?, "title": string }`                                                                         | `201 Created` <br><br>`400 Bad Request`<br><br>`401 Unauthorized`                                   | Initializes a new RAG chat conversation thread.                                                                                                                                                               |
| `/rag/query`                      | `POST`     | Yes               | **Body (JSON):**<br>`{ "session_id": UUID, "project_id": UUID?, "meeting_id": UUID?, "query": string }`                                | `200 OK`<br><br>`400 Bad Request`<br><br>`401 Unauthorized`<br><br>`404 Not Found`                  | Runs hybrid dense/sparse search (pgvector + BM25) strictly scoped to the project or meeting boundary; returns LLM-grounded answers with audio seek timestamps or an explicit _"I don't know"_ refusal string. |
## Database Setup

```mermaid
erDiagram
    PROJECTS {
        uuid id PK "Primary Key"
        varchar_255 name "Project name"
        text image_url "Thumbnail image asset path"
        timestamptz created_at "Creation timestamp"
        timestamptz updated_at "Update timestamp"
    }
```

```mermaid
erDiagram
    MEETINGS {
        uuid id PK "Primary Key"
        uuid project_id FK "References projects(id)"
        varchar_255 name "Meeting title"
        timestamptz meeting_date "Date and time of meeting"
        text audio_file_path "Sandboxed path to raw audio"
        integer duration_seconds "Playback length in seconds"
        text calendar_event_id "Apple EventKit event identifier"
        boolean consent_given "Consent gating verification flag"
        timestamptz created_at "Creation timestamp"
    }
```

```mermaid
erDiagram
    ATTENDEES {
        uuid id PK "Primary Key"
        varchar_255 name "Full attendee name"
        text avatar_url "Contact photo or avatar image path"
        varchar_255 contact_identifier "iOS Contacts.framework ID"
        vector_512 voice_embedding "512-d acoustic x-vector profile"
        timestamptz created_at "Enrollment timestamp"
    }
```

```mermaid
erDiagram
    MEETING_ATTENDEES {
        uuid meeting_id PK, FK "References meetings(id)"
        uuid attendee_id PK, FK "References attendees(id)"
        varchar_64 speaker_label "Diarizer tag (e.g., SPEAKER_00)"
    }
```

```mermaid
	erDiagram
	    TRANSCRIPTS {
	        uuid id PK "Primary Key"
	        uuid meeting_id FK "References meetings(id)"
	        uuid attendee_id FK "References attendees(id)"
	        varchar_255 speaker_name "Attributed speaker name"
	        integer start_time_ms "Start playhead offset (ms)"
	        integer end_time_ms "End playhead offset (ms)"
	        text content "Transcribed utterance"
	        integer turn_order "Sequential turn counter"
	        vector_384 embedding "Dense chunk vector for RAG"
	        tsvector tsv "Lexical BM25 search vector"
	    }
```

```mermaid
	erDiagram
	    MEETING_SUMMARIES {
	        uuid id PK "Primary Key"
	        uuid meeting_id FK "References meetings(id) (Unique)"
	        text overview "Narrative synthesis"
	        jsonb bullet_points "Structured takeaway bullets"
	        jsonb rubric_scores "Faithfulness and conciseness scores"
	        text user_notes "Editable manual user notes"
	        timestamptz updated_at "Last revised timestamp"
	    }
```

```mermaid
erDiagram
    MEETING_DECISIONS {
        uuid id PK "Primary Key"
        uuid meeting_id FK "References meetings(id)"
        uuid transcript_id FK "References transcripts(id)"
        text decision_statement "Settled consensus item"
        text rationale "Context or alternatives rejected"
        integer timestamp_ms "Audio seek playhead offset (ms)"
        timestamptz created_at "Creation timestamp"
    }
```

```mermaid
erDiagram
    ATTENDEE_STORYLINES {
        uuid id PK "Primary Key"
        uuid meeting_id FK "References meetings(id)"
        uuid attendee_id FK "References attendees(id)"
        text what_they_want "Participant goals and agenda"
        text what_they_see "Participant observations and concerns"
        text what_they_discuss "Key discussion points contributed"
        timestamptz created_at "Generation timestamp"
    }
```

```mermaid
erDiagram
    TASKS {
        uuid id PK "Primary Key"
        uuid project_id FK "References projects(id), (Index Col 1)"
        uuid meeting_id FK "References meetings(id), (Index Col 2)"
        uuid attendee_id FK "References attendees(id)"
        text title "Task description"
        date due_date "Scheduled deadline, (Index Col 3)"
        varchar_32 review_status "pending, approved, dismissed"
        varchar_32 lifecycle_status "open, done, dropped (Index Col 4)"
        varchar_32 category "commitment vs advisor_suggestion"
        uuid evidence_transcript_id FK "References transcripts(id)"
        text evidence_quote "Verbatim transcript quote"
        integer evidence_timestamp_ms "Proof audio offset (ms)"
        vector_384 embedding "Dense vector for deduplication"
        text eventkit_reminder_id "Apple Reminders item identifier"
        timestamptz created_at "Creation timestamp"
        timestamptz updated_at "Update timestamp"
    }
```

```mermaid
erDiagram
    TASK_AUDIT_LOG {
        uuid id PK "Primary Key"
        uuid task_id FK "References tasks(id)"
        varchar_64 action "Action name (e.g., STATUS_CHANGE)"
        jsonb old_value "Prior state snapshot"
        jsonb new_value "Updated state snapshot"
        uuid revert_token "Unique token for atomic undo"
        timestamptz created_at "Audit entry timestamp"
    }
```

```mermaid
erDiagram
    CHAT_CONVERSATIONS {
        uuid id PK "Primary Key"
        uuid project_id FK "References projects(id) (Nullable)"
        uuid meeting_id FK "References meetings(id) (Nullable)"
        varchar_255 title "Generated conversation title"
        timestamptz created_at "Session start timestamp"
        timestamptz updated_at "Session update timestamp"
    }
```

```mermaid
erDiagram
    CHAT_MESSAGES {
        uuid id PK "Primary Key"
        uuid conversation_id FK "References chat_conversations(id)"
        varchar_32 role "user or assistant"
        text content "Message body or refusal"
        jsonb citations "Citation chips with timestamp offsets"
        timestamptz created_at "Message timestamp"
    }
```



## Database Connection

```mermaid
erDiagram
    PROJECTS ||--o{ MEETINGS : "contains"
    PROJECTS ||--o{ TASKS : "scopes"
    PROJECTS |o--o{ CHAT_CONVERSATIONS : "scopes"
    MEETINGS ||--o{ MEETING_ATTENDEES : "records"
    ATTENDEES ||--o{ MEETING_ATTENDEES : "participates_in"
    MEETINGS ||--o{ TRANSCRIPTS : "segments [ON DELETE CASCADE]"
    ATTENDEES |o--o{ TRANSCRIPTS : "speaks"
    MEETINGS ||--|| MEETING_SUMMARIES : "synthesizes [ON DELETE CASCADE]"
    MEETINGS ||--o{ MEETING_DECISIONS : "yields [ON DELETE CASCADE]"
    TRANSCRIPTS |o--o{ MEETING_DECISIONS : "evidences"
    MEETINGS ||--o{ ATTENDEE_STORYLINES : "generates [ON DELETE CASCADE]"
    ATTENDEES ||--o{ ATTENDEE_STORYLINES : "attributes"
    MEETINGS ||--o{ TASKS : "originates"
    ATTENDEES |o--o{ TASKS : "assigns"
    TRANSCRIPTS |o--o{ TASKS : "verifies"
    TASKS ||--o{ TASK_AUDIT_LOG : "audits"
    MEETINGS |o--o{ CHAT_CONVERSATIONS : "contextualizes"
    CHAT_CONVERSATIONS ||--o{ CHAT_MESSAGES : "contains"

    PROJECTS {
        uuid id PK
        varchar_255 name
        text image_url
        timestamptz created_at
        timestamptz updated_at
    }

    MEETINGS {
        uuid id PK
        uuid project_id FK
        varchar_255 name
        timestamptz meeting_date
        text audio_file_path
        integer duration_seconds
        text calendar_event_id
        boolean consent_given
        timestamptz created_at
    }

    ATTENDEES {
        uuid id PK
        varchar_255 name
        text avatar_url
        varchar_255 contact_identifier
        vector_512 voice_embedding
        timestamptz created_at
    }

    MEETING_ATTENDEES {
        uuid meeting_id PK, FK
        uuid attendee_id PK, FK
        varchar_64 speaker_label
    }

    TRANSCRIPTS {
        uuid id PK
        uuid meeting_id FK
        uuid attendee_id FK
        varchar_255 speaker_name
        integer start_time_ms
        integer end_time_ms
        text content
        integer turn_order
        vector_384 embedding
        tsvector tsv
    }

    MEETING_SUMMARIES {
        uuid id PK
        uuid meeting_id FK "UNIQUE"
        text overview
        jsonb bullet_points
        jsonb rubric_scores
        text user_notes
        timestamptz updated_at
    }

    MEETING_DECISIONS {
        uuid id PK
        uuid meeting_id FK
        uuid transcript_id FK
        text decision_statement
        text rationale
        integer timestamp_ms
        timestamptz created_at
    }

    ATTENDEE_STORYLINES {
        uuid id PK
        uuid meeting_id FK
        uuid attendee_id FK
        text what_they_want
        text what_they_see
        text what_they_discuss
        timestamptz created_at
    }

    TASKS {
        uuid id PK
        uuid project_id FK
        uuid meeting_id FK
        uuid attendee_id FK
        text title
        date due_date
        varchar_32 review_status
        varchar_32 lifecycle_status
        varchar_32 category
        uuid evidence_transcript_id FK
        text evidence_quote
        integer evidence_timestamp_ms
        vector_384 embedding
        text eventkit_reminder_id
        timestamptz created_at
        timestamptz updated_at
    }

    TASK_AUDIT_LOG {
        uuid id PK
        uuid task_id FK
        varchar_64 action
        jsonb old_value
        jsonb new_value
        uuid revert_token "UNIQUE"
        timestamptz created_at
    }

    CHAT_CONVERSATIONS {
        uuid id PK
        uuid project_id FK "NULLABLE"
        uuid meeting_id FK "NULLABLE"
        varchar_255 title
        timestamptz created_at
        timestamptz updated_at
    }

    CHAT_MESSAGES {
        uuid id PK
        uuid conversation_id FK
        varchar_32 role
        text content
        jsonb citations
        timestamptz created_at
    }
```


