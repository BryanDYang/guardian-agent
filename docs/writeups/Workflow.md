> **Design history:** This writeup includes proposed or earlier behavior. Use [Current architecture](../architecture.md) for implemented connections and [the native walkthrough](../demo_walkthrough.md) for acceptance evidence.

## Sequential AI build with agent

To build this end-to-end system with an AI agent while preventing hallucinations, dependency loops, and schema drift, develop from the **data contracts upward**—locking core schemas and headless processing before writing API routers or client views.

**Phase 1: Contract & Interface Freeze**

*Lock the interfaces first so the AI agent always references an immutable source of truth instead of guessing types.*

- **Database Schema (DDL):** Author the exact PostgreSQL 16 migration (`alembic` or raw SQL) establishing the 12 tables, foreign keys with `ON DELETE CASCADE`, HNSW vector indexes (`vector_cosine_ops`), and full-text GIN indexes (`tsvector`).
- **Pydantic Contract Definitions:** Define typed data models for all pipeline stages: transcript turns, summary bullet schemas, structured decisions, attendee storylines, task review payloads, and RAG retrieval responses.
- **Golden Test Fixtures:** Create a static fixture directory (`tests/fixtures/`) containing a 60-second `.wav` audio clip, its human-verified transcript, and mock attendee calendar records.

**Phase 2: Persistence & Search Layer (System 8)**

*Implement data access before processing logic so downstream tasks have reliable storage targets.*

- **Async Database Engine:** Configure SQLAlchemy 2.0 / `asyncpg` connection pools and session dependency injectors for FastAPI.
- **Repository CRUD & Audit Logging:** Write repositories for the 12 tables, ensuring all task mutations write an entry to `TASK_AUDIT_LOG` with a unique UUID `revert_token`.
- **Hybrid Search CTE:** Implement the SQL query combining pgvector cosine distance and `tsvector` full-text search with Reciprocal Rank Fusion (RRF) at $k=60$, enforcing strict `WHERE project_id = :project_id` scoping.

**Phase 3: Headless Audio & Extraction Pipeline (Systems 6 & 7)**

*Build and verify compute-heavy engines as isolated Python modules before attaching HTTP or queue interfaces.*

- **Acoustic Processing:** Build the sequential audio pipeline: FFmpeg normalization (16 kHz mono WAV) $\rightarrow$ `mlx-whisper` transcription with token-level timestamps $\rightarrow$ `pyannote.audio` diarization $\rightarrow$ 512-d x-vector extraction and cosine matching.
- **Cognitive Extraction:** Implement Claude 3.5 structured output parsers using the Pydantic schemas defined in Phase 1 to generate summaries, consensus decisions, and attendee storylines.
- **Task Deduplication Engine:** Embed candidate tasks using `sentence-transformers/all-MiniLM-L6-v2`, run pgvector cosine checks against open tasks, and invoke the Claude arbitration prompt for items scoring above $0.80$ similarity.

**Phase 4: Sequential Queue & API Gateway (Systems 4 & 5)**
*Wrap the verified pipeline modules in FastAPI endpoints and queue controls.*

- **Queue Orchestration:** Implement the in-process `asyncio.Queue` worker to restrict execution to one meeting at a time, enforcing the 10 GB memory ceiling on Apple Silicon.
- **API Routers & Auth Guards:** Implement endpoints matching the API specification, applying bearer token and `project_id` security dependencies.
- **Telemetry & Streaming:** Set up `WS /ws/pipeline/{job_id}` for real-time stage progress cards and write the byte-range streaming handler (`GET /meetings/{id}/audio`) returning `HTTP 206 Partial Content`.
- **Tunnel Configuration:** Script the `cloudflared` or Tailscale daemon to expose `localhost:8000` via secure HTTPS.

**Phase 5: Offline Evaluation Harness (System 9)**

*Validate the backend end-to-end headlessly before touching Swift or Xcode.*

- **Benchmark Suite:** Implement `pytest tests/benchmarks/` utilizing `jiwer` to verify $WER$, `pyannote.metrics` to track $DER$, and `ragas` to assert 100% citation faithfulness and grounded refusal (*"I don't know"*).
- **Verification Gate:** Run the test suite against your golden fixtures; do not proceed to iOS development until the backend passes without memory leaks or missing citations.

**Phase 6: Client Networking & Playback Foundation (Systems 2 & 3)**

*Establish low-level iOS data access and hardware controllers before building SwiftUI views.*

- **Swift Models & API Client:** Generate Swift structs mirroring the Pydantic models; implement `URLSession` network services with bearer token injection and WebSocket listeners.
- **AVFoundation Audio Controller:** Build the playback service managing `AVPlayer`, `AVAudioSession`, and sub-second seek dispatching (`CMTime(value:timescale:)`) tied to periodic time observers.
- **EventKit Service:** Implement native bridges to `EKEventStore` to query meeting attendees from iOS Calendar and export approved tasks directly into Apple Reminders.

**Phase 7: Native Presentation Assembly (System 1)**

*Bind UI components to the tested client services.*

- **Meetings Hub & Review Stack:** Assemble the project card dashboard, consent modal, diarized transcript feed with active playhead highlighting, and human-in-the-loop task review card stack (Approve, Edit, Dismiss).
- **Operational Tasks Calendar:** Build the multi-scale date picker with 3-state execution toggles (`open`, `done`, `dropped`) and project workstream filters.
- **Chat View:** Build the conversational interface supporting project scope toggles, grounded refusal rendering, and tappable citation badges that route seek commands directly to the AVFoundation controller.

**Immediate Actionable Execution Checklist**

1. **Prompt 1 (AI Agent):** Generate the complete PostgreSQL DDL file with all 12 tables, constraints, foreign key cascades, HNSW vector indexes, and the GIN full-text index.
2. **Prompt 2 (AI Agent):** Generate the Pydantic models for meeting ingestion, transcript turns, summaries, decisions, storylines, and tasks matching that DDL.
3. **Prompt 3 (AI Agent):** Implement the SQLAlchemy/asyncpg repository layer and run an automated migration against local PostgreSQL.
4. **Verification Step:** Run `docker-compose up -d postgres` and execute migration scripts to verify that foreign key cascades and pgvector extensions initialize without errors before generating any pipeline or ML code.



## Team Role Allocation


| **Role**       | **Core Domain**                           | **Systems Owned**                                                                                                    | **Primary Tech Stack**                                                                   | **Codebase Footprint**                                                               |
| -------------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| **Engineer 1** | **Native iOS & Device Integrations**      | **System 1:** Native Presentation **System 2:** AVFoundation Deep-Linking **System 3:** Mobile OS EventKit           | Swift 6, SwiftUI, AVFoundation, EventKit, SwiftData                                      | `ios/` or `frontend/` (Xcode project)                                                |
| **Engineer 2** | **Platform, Persistence & API Gateway**   | **System 4:** Remote Tunneling **System 5:** Ingestion & Queue Worker **System 8:** Unified Persistence (PostgreSQL) | PostgreSQL 16, pgvector, FastAPI, Uvicorn, SQLAlchemy 2.0 / asyncpg, Cloudflare Tunnel   | `backend/app/api/`, `backend/app/db/`, `backend/app/worker/`, `docker/`              |
| **Engineer 3** | **Applied ML, Extraction & Benchmarking** | **System 6:** Acoustic Diarization **System 7:** Structured LLM & Dedup **System 9:** Evaluation Harness             | MLX-Whisper, pyannote.audio, Claude 3.5 (Pydantic), sentence-transformers, Ragas, pytest | `backend/app/ml/`, `backend/app/extraction/`, `tests/benchmarks/`, `tests/fixtures/` |


