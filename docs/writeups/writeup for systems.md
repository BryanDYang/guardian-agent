**1. [[Native Presentation System]] (SwiftUI)** Drives the 3-axis tab layout: the Projects/Meetings dashboard (summaries, decisions, transcripts, attendee storylines), the date-based Tasks calendar with 3-state execution (Open, Done, Dropped), and the conversational Chat view.

**2. [[Audio Playback & Deep-Linking Engine ]](AVFoundation)** Enables sub-second playhead seeking (`AVPlayer.seek(to: CMTime)`) mapped directly to transcript offsets, decision evidence, task proof citations, and chat source references without streaming full raw audio over the network repeatedly.

**3. [[Mobile OS Integration Service]] (Apple EventKit)** Natively bridges device capabilities by extracting attendee metadata from calendar events and exporting approved tasks and deadlines directly to Apple Reminders and Calendar, eliminating the need for a dedicated push notification backend.

**4. [[Remote Gateway & Secure Tunneling Layer ]](Cloudflare Tunnel / Tailscale)** Exposes the local backend to the mobile app over secure, zero-trust HTTPS and WebSockets, bypassing complex port forwarding, router configuration, or expensive cloud infrastructure.

**5. [[Ingestion & Sequential Worker Service ]](FastAPI / Uvicorn)** Serves as the central API gateway enforcing project-level access guards. It orchestrates background processing via an asynchronous worker queue, handles FFmpeg audio normalization, and executes safe, recoverable file trashing via `send2trash`.

**6. [[Acoustic Ingestion & Diarization Pipeline]] (MLX-Whisper + pyannote.audio)** *Leverages the PREBUILT foundation.* Executes on Apple Silicon unified memory to generate word-level timestamped transcripts, separate speech turns, and resolve persistent x-vector voice embeddings against attendee records.

**7. [[Structured Extraction & Task Reconciliation Engine]] (Claude 3.5 + Pydantic + Sentence-Transformers)** Extracts typed takeaways, consensus decisions, and attendee storylines (what they want, see, discuss). It uses dense embedding cosine distance and an LLM arbiter to reconcile shorthand and deduplicate tasks against active records.

**8. [[Unified Persistence & Hybrid Search Store]] (PostgreSQL 16 + pgvector)** Replaces flat-file JSON storage to maintain relational project entities, the immutable `task_audit_log` with revert tokens, and hybrid dense/BM25 search indices for scoped RAG queries.

**9. [[Evaluation & Benchmarking Harness]] (Ragas + jiwer + pyannote.metrics)** An offline testing suite benchmarking Word Error Rate, Diarization Error Rate, task linkage F1, and citation faithfulness against ground-truth fixtures to ensure model reliability

## File Tree

```
labsync/
├── .github/
│   └── workflows/
│       ├── ci-backend.yml              # Linting, type checks (mypy), and unit tests
│       └── ci-ios.yml                  # Xcode build and SwiftLint checks
├── Makefile                            # Native Homebrew and local virtual environment & common commands.
├── pyproject.toml                      # Poetry/UV dependency configuration for Python 3.11+
│
├── src/labsync/                        # CORE BACKEND (Engineers 2 & 3)
│   ├── __init__.py
│   ├── config.py                       # Pydantic Settings (.env, tunnel host, model paths)
│   ├── main.py                         # FastAPI initialization, CORS, and route registration
│   │
│   ├── schemas/                        # CONTRACT LAYER (Shared Source of Truth)
│   │   ├── __init__.py
│   │   ├── meeting.py                  # Meeting metadata, upload payloads, audio status
│   │   ├── transcript.py               # Diarized turn tokens, word-level timestamps
│   │   ├── task.py                     # 3-state lifecycle, audit token, EventKit sync DTOs
│   │   ├── summary.py                  # Summaries, consensus decisions, attendee storylines
│   │   ├── chat.py                     # RAG query, response payload, JSON citation schema
│   │   └── pipeline.py                 # Job states (queued, running, failed, complete)
│   │
│   ├── db/                             # SYSTEM 8: PERSISTENCE (Engineer 2)
│   │   ├── __init__.py
│   │   ├── session.py                  # asyncpg engine, async_sessionmaker dependency
│   │   ├── models/                     # SQLAlchemy 2.0 Declarative Models (12 Tables)
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # DeclarativeBase with UUID and timestamp mixins
│   │   │   ├── projects.py             # PROJECTS table
│   │   │   ├── meetings.py             # MEETINGS, ATTENDEES, MEETING_ATTENDEES
│   │   │   ├── transcripts.py          # TRANSCRIPTS table (with vector(384) & tsvector)
│   │   │   ├── summaries.py            # MEETING_SUMMARIES, DECISIONS, STORYLINES
│   │   │   ├── tasks.py                # TASKS (with vector(384)) & TASK_AUDIT_LOG
│   │   │   └── chat.py                 # CHAT_CONVERSATIONS & CHAT_MESSAGES
│   │   ├── repositories/               # Encapsulated Data Access Layer
│   │   │   ├── __init__.py
│   │   │   ├── meeting_repo.py         # Meeting CRUD and cascade handling
│   │   │   ├── task_repo.py            # Atomic task state changes + TASK_AUDIT_LOG inserts
│   │   │   └── search_repo.py          # Hybrid search CTE: pgvector + tsvector RRF
│   │   └── migrations/                 # Alembic Database Migrations
│   │       ├── env.py
│   │       └── versions/
│   │           └── 0001_initial_12_tables.py
│   │
│   ├── api/                            # SYSTEM 4 & 5: GATEWAY & ROUTERS (Engineer 2)
│   │   ├── __init__.py
│   │   ├── deps.py                     # Bearer auth guard, DB session, project scope validation
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py               # Aggregates sub-routers into /api/v1
│   │       ├── health.py               # GET /health (heartbeat probe for tunnel client)
│   │       ├── meetings.py             # Upload, detail, audio byte-streaming (HTTP 206)
│   │       ├── tasks.py                # Task filtering, status patch, undo revert route
│   │       ├── chat.py                 # POST /rag/query with citations & conversation routes
│   │       ├── pipeline.py             # GET/DELETE /pipeline/jobs/{id} status polling
│   │       └── websockets.py           # WS /ws/pipeline/{job_id} live telemetry channel
│   │
│   ├── worker/                         # SYSTEM 5: SEQUENTIAL INGESTION (Engineer 2)
│   │   ├── __init__.py
│   │   ├── queue.py                    # In-process asyncio.Queue single-flight worker (<10GB cap)
│   │   ├── dispatcher.py               # Lifecycle transitions and error handler
│   │   └── broadcaster.py             # WebSocket active client connection registry
│   │
│   ├── ml/                             # SYSTEM 6: ACOUSTIC PIPELINE (Engineer 3)
│   │   ├── __init__.py
│   │   ├── audio.py                    # ffmpeg-python 16kHz mono normalization & send2trash
│   │   ├── asr.py                      # mlx-whisper large-v3-turbo runner on Apple Silicon
│   │   ├── diarization.py              # pyannote.audio 3.1 VAD, segmentation & clustering
│   │   └── biometrics.py               # 512-d x-vector embedding generation & cosine match
│   │
│   └── extraction/                     # SYSTEM 7: COGNITIVE EXTRACTION (Engineer 3)
│       ├── __init__.py
│       ├── llm.py                      # Claude 3.5 Anthropic client with structured output schemas
│       ├── extractors/
│       │   ├── summary.py              # Overview bullets and rubric score generation
│       │   ├── decisions.py            # Consensus assertion, rationale, rejected alternatives
│       │   └── storylines.py           # 3-axis participant POV (wants, sees, discusses)
│       └── deduplication.py            # 384-d sentence-transformers + Claude task arbiter
│
├── frontend/                           # SYSTEMS 1, 2, 3: NATIVE IOS APP (Engineer 1)
│   ├── LabSync.xcodeproj/
│   └── LabSync/
│       ├── App/
│       │   ├── LabSyncApp.swift        # App entry point and window lifecycle
│       │   └── AppState.swift          # Global navigation state and active project store
│       ├── Core/
│       │   ├── Network/                # URLSession, Bearer auth, background upload manager
│       │   ├── WebSocket/              # URLSessionWebSocketTask pipeline telemetry listener
│       │   ├── Audio/                  # AVPlayer HTTP 206 streaming and CMTime playhead seek
│       │   └── EventKit/               # EKEventStore calendar sync and Reminders export
│       ├── Models/                     # Swift Decodable structs mirroring Pydantic schemas
│       ├── ViewModels/
│       │   ├── MeetingsViewModel.swift # Upload coordinator and transcript state
│       │   ├── TasksViewModel.swift    # Calendar queries, 3-state check/trash transitions
│       │   └── ChatViewModel.swift     # RAG query dispatch and citation selection
│       └── Views/
│           ├── Meetings/               # Project card hub, transcript feed, HITL review stack
│           ├── Tasks/                  # Multi-scale operational calendar and action lists
│           ├── Chat/                   # Conversational interface with citation badges
│           └── Common/                 # Audio scrubber toolbar, consent gating modal
│
└── tests/                              # SYSTEM 9: BENCHMARK & TEST SUITE (Engineer 3)
    ├── fixtures/                       # CONTRACT C: Golden Test Assets
    │   ├── sample_meeting.wav          # 60-second reference 16kHz mono audio recording
    │   ├── ground_truth_transcript.json
    │   └── mock_calendar_event.json
    ├── unit/                           # Isolated Module Tests
    │   ├── test_schemas.py             # DTO validation assertions
    │   ├── test_audio_normalization.py # FFmpeg format verification
    │   └── test_task_reconciliation.py # Semantic deduplication unit tests
    ├── integration/                    # Multi-Service Integration Tests
    │   ├── test_api_routes.py          # FastAPI testclient endpoint tests
    │   └── test_hybrid_search.py       # pgvector + tsvector RRF query assertions
    └── benchmarks/                     # Offline Evaluation Suite
        ├── test_wer_jiwer.py           # Word Error Rate benchmark on MLX-Whisper
        ├── test_der_pyannote.py        # Diarization Error Rate on pyannote 3.1
        └── test_ragas_eval.py          # Ragas citation faithfulness and refusal metrics
```

