## Goal

The app turns one meeting recording into a project record the team can act on. A user creates a project, uploads a consented recording, and the backend transcribes it, then extracts a summary, decisions, commitments, and unaccepted suggestions. Decisions, commitments, and suggestions are kept only when they cite a verbatim quote from the transcript. Commitments and suggestions arrive as pending tasks. Nothing becomes a tracked task until the user approves it, and a task cannot be approved without a due date. Approved tasks show up on that project's calendar and can be copied into Apple Reminders. The user can also open a chat and ask questions about earlier meetings in a project. The model answers from the stored transcripts, summaries, decisions, and tasks in the database, and cites the meeting and timestamp the answer came from. If that history does not contain the answer, it says it does not know.

Success means opening a project and seeing, for a given meeting, what was summarized, what was decided, and which candidate tasks came from an explicit commitment versus an advisor suggestion, each tied back to a speaker, a quote, and a timestamp. On the calendar, the user can see which approved tasks are still open, done, or dropped, and can undo a status change. In chat, the user can ask something like what was decided in a previous sync and get an answer grounded in that project's stored history, with a reference back to the meeting, instead of searching old transcripts by hand. The record stays limited to what the meeting actually said: an absent task is not marked done or dropped, and a suggestion stays a suggestion until the user accepts it.

## [[PREBUILT_TRANSCRIBER]].md

- Has the features and technology of what has already been built (by professor) for us developers to build on top of
The backend transcrier



## Features



### In Scope

- Native iOS application: Serves as the primary mobile client for audio ingestion, transcript viewing, task management, and conversational queries.
- MP3 audio file ingestion: Allows users to import and process local or shared MP3 audio recordings directly into the pipeline.
- Audio-to-text transcription: Converts spoken audio into timestamped text transcripts using existing speech-recognition models.
- Speaker segregation/diarization: Identifies distinct speakers across the recording to attribute spoken statements to specific participants.
- LLM Summary creation: Synthesizes transcripts into structured, concise meeting overviews highlighting core discussions and key takeaways.
- Speaker Task extraction (Todo list): Automatically identifies action items assigned to specific speakers and routes them into a human-in-the-loop review workflow for approval, editing, or rejection.
- Task lifecycle management (Open, Done, Dropped): Tracks and transitions tasks across 3 explicit status states to reflect real project progress across meeting sequences.
- Duplication filtering: Compares newly extracted action items against previously tracked open tasks to prevent redundant entries.
- Calendar integration / updates: Pulls meeting metadata (attendees, dates, projects) from external calendar services and syncs task deadlines back to user schedules.
- Meeting Session Storage: Securely persists raw audio files, transcripts, generated summaries, and structured task data for long-term access.
- Safe file handling: Enforces secure local storage practices, validation checks, and cleanup routines to prevent file corruption or data leaks.
- Tunnel Gateway Auth Guard: Enforces zero-trust request verification using a static pre-shared bearer token (API_SECRET_KEY) shared between the Cloudflare Tunnel/iOS client and the FastAPI backend, bypassing multi-user session management.
- Evaluation measurement: Benchmarks system performance and model accuracy using reproducible evaluation datasets and metric scoring.
- RAG System / User LLM integration: Enables users to ask natural-language questions about past discussions and retrieve answers grounded in historical meeting context.
- Update meeting notes: Allows users to manually edit, append, and save revisions to generated meeting summaries.
- Update task todos: Enables manual editing of task attributes, including assignees, descriptions, due dates, and status values.
- Provide citations back to the source: Links extracted tasks, decisions, and RAG answers directly to exact transcript timestamps and audio segments for verification.
- Summary sharing: Formats and exports meeting notes and action items for external sharing across communication platforms or files.
- Todo list (task) Reminders: Triggers scheduled reminders and highlights approaching deadlines for outstanding action items.
- Audit Trail, Versioning, and Undo: Records a historical log of modifications to tasks and notes, allowing users to inspect changes and revert unwanted edits.
- Provide inspection by meeting, person, and project: Generates aggregated, filtered dashboard views organized by meeting session, attendee, or broader project workstreams.
- Demonstrate consent gating, selective exclusion, deletion, and project-scoped retrieval: Implements privacy mechanisms to verify participant recording consent, exclude sensitive transcript portions, purge deleted records, and isolate data retrieval strictly to the target project.
- need to be able to pick up meeting date if so



### Out of Scope

- Transcription encryption: Implementing cryptographic encryption at rest or in transit for stored transcripts and audio files will not be built.
- Notification system: Operating dedicated background push notifications, SMS alerts, or external notification dispatch infrastructure is omitted.
- Train a speech-recognition model from scratch
- Generate productivity or performance scores
- Rank students or researchers
- Monitor meetings without participant consent
- Deploy a production multi-tenant service
- Treat meeting statements as independently verified proof that real-world work occurred
- Claim broad performance across languages or meeting settings beyond those evaluated
- User Authentication



## Frontend User Experience Story

When the user loads into the app, they will have a navigation bar the navigates the user to 3 different views: Meetings, Tasks, and Chat. The default page the user will load into when opening the app will be meetings view.

#### Meetings View

In the meetings view, It will see a list of projects that the user has uploaded previously. They can add more projects. The projects contain an image and name. Each project has a list of meetings that the user uploaded for that target project. The meeting contains the meeting name, audio file, timestamp of audio length, and the date of the meeting. The user can also create new meetings for the that target project. When the user clicks on a specific target meeting, it will direct them to a new page of different retrieved data from the AI agent. They can view the meeting's summary (audio transcribed & summarize), tasks (LLM extracts tasks for each diarized attendee), transcript (audio transcription), and storyline. When the user clicks on summary, it will show a list of different summarized bullet points from. It will also extract a list of decisions that were made in the meeting discussion. Then when the user opens up the tasks for that target meeting upload, it will show a list of generated tasks that were assigned to each speaker that were in the meeting attendance. The user can either approve, edit, or dismiss the task suggestion. Each task item will contain the approve, edit, or dismiss buttons, the speaker's name and profile initial, due date, and timestamp of the referenced transcript as proof. When the user clicks approve for the task item, it will sync to the iPhone's calendar and reminder app and also sync to the app's calendar in the tasks view. Now when the user clicks on the transcript section in the target meeting, it will show a list of the meeting attendees transcription conversation throughout the meeting length. It consist of the message, attendee name, and their profile initials. When the user selects the storyline section, it will show a list of the attendees who are a part of the meeting discussion. Each list item will have the attendee's name and profile initials. Then when the user clicks on a target attendee, it will open up that attendee's storyline, which tells the user that target attendee's point of view of what they want, what they see, and what they are talking about.

#### Tasks View

Now when the user clicks on the tasks view from the navigation bar, it will open up the Tasks view. In the tasks view, it will show a calendar component of the year, month, and dates. The user can scroll through the years, months, and days. Each day of the month will contain a list of tasks linked from the user's action of approved from the meetings view when the user selected a target meeting and through that tasks generation from the AI agent. In the list of tasks shown for that specific date, it will have a check or trash button where if the user clicks on the check, it will be marked as "done" and when they click on the trash button, it will be marked as "dropped". The task item stays marked as "open" if left otherwise, indicating the user has not completed and is due on that specific date. The user can also filter through the projects which will show the tasks needed to be completed for that specific project.

#### Chat View

When the user clicks on the Chat button via navigation bar, it will open a Chat view. In the chat view, the user can basically ask questions to an LLM that filters through the database about a specific meeting. For example, the user asks "What did we decide about the ML architecture in the last sync?" and the LLM will go through the transcriptions of the meetings to come up with an answer. When the AI responds with an answer, it will have a reference tab of the meeting name and the timestamp of where that answer was answered. If the LLM can't find the answer, then it will say "I don't know". The user can also see the chat history of different conversation with the AI. They can also filter the chat history based on target project selected. The default is "all", which shows all of the various chat conversations the user has had with the AI. The user can also open up a new chat conversation with the AI.

## Backend User Experience Story

**1. Acoustic Ingestion & Speaker Identity Resolution (Meetings View)**

When a meeting recording is uploaded under a target project, the backend must silently:

- Enforce project-scoped access guards on the incoming HTTP request and queue the file in an asynchronous sequential worker to constrain peak memory consumption below 10 GB on the host Apple Silicon hardware.
- Normalize the audio stream into standardized 16 kHz mono WAV buffers via FFmpeg.
- Execute `mlx-whisper` on the Neural Engine to generate word-level timestamped transcripts, followed sequentially by `pyannote.audio` diarization to segment turn boundaries.
- Extract 512-dimensional x-vector speaker embeddings and compute cosine similarities against persistent voice profiles and calendar metadata to attribute utterances to attendee names and profile initials before populating the transcript.

**2. Structured Extraction, Storyline Synthesis & Deduplication**

To populate the target meeting’s Summary, Tasks, and Storylines:

- Invoke Claude using strict Pydantic v2 schemas to parse the diarized transcript into structured meeting takeaway bullets, explicit consensus decisions, and each attendee's subjective storyline (`what_they_want`, `what_they_see`, `what_they_discuss`).
- Isolate concrete speaker commitments from advisor suggestions, binding each proposed task to exact verbatim quotes and millisecond timestamp offsets.
- Generate dense embeddings of candidate tasks with `sentence-transformers` and query PostgreSQL for existing open tasks; if semantic similarity exceeds 0.82, trigger an LLM verification prompt to reconcile shorthand (e.g., matching "the rerun" to an existing item) instead of generating duplicate entries.

**3. Task Lifecycle Persistence & Audit Synchronization (Tasks View)**

When actions are approved, edited, or marked as done or dropped in the calendar view:

- Transition the task entity across its lifecycle (`open`, `done`, `dropped`) in PostgreSQL and commit an entry to the append-only `task_audit_log` with state diffs and revert tokens for complete undo history.
- Format task metadata and deadline updates into structured responses consumed by the client for EventKit reminder and calendar sync.
- Filter tasks dynamically by `project_id` and calendar `due_date` across year, month, and day ranges.

**4. Scoped Hybrid Retrieval & Citation Grounding (Chat View)**

When natural-language queries are submitted in the Chat view:

- Query conversational sessions filtered by `project_id` or nullable `meeting_id`, supporting both global "all" history listings and project-isolated RAG retrieval.
- Execute hybrid retrieval combining dense vector similarity (`pgvector`) with sparse lexical matching (PostgreSQL Full-Text Search / BM25) across conversational chunks strictly partitioned by the target meeting or project boundary.
- Enforce strict refusal guardrails instructing the model to return "I don't know" whenever recorded context is absent, while formatting verifiable answers with exact meeting names and second-accurate playhead timestamps that power client AVPlayer audio scrubbing.

