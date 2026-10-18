> **Design history:** This writeup includes proposed or earlier behavior. Use [Current architecture](../../architecture.md) for implemented connections and [the native walkthrough](../../evidence/demo_walkthrough.md) for acceptance evidence.

### 1. Native iOS Client Stack

- **Swift 6 & SwiftUI:** The core framework for the iOS client. Modern Swift Concurrency (`async`/`await`, `TaskGroup`, and Actors) prevents UI hangs when parsing large transcripts or receiving streaming LLM responses.
    
- **AVFoundation (`AVPlayer`, `CMTime`):** Powers audio playback and citation scrubbing via HTTP 206 Partial Content byte-range requests (`Range: bytes=...`). It allows the UI to bind transcript timestamps, task citations, and RAG badges directly to the audio buffer, streaming byte slices dynamically and seeking down to the millisecond (`player.seek(to: CMTime)`) without downloading the entire file upfront.
    
- **EventKit (`EKEventStore`):** Connects to the user’s native iOS Calendar and Reminders. It inspects calendar events matching recording timestamps to fetch attendee names, and writes approved action items directly into Apple Reminders to satisfy the reminder scope without maintaining an external notification server.
    
- **Background Tasks & Networking (`URLSessionConfiguration.background`):** Ensures that multi-megabyte MP3 uploads and long-running pipeline requests do not terminate when the user locks their phone or backgrounds the app.
    
- **SwiftData / SQLite.swift:** Lightweight local client caching for offline reading of approved tasks, previous meeting notes, and cached summaries.
    

### 2. Networking & Secure Remote Access

- **Cloudflare Tunnel (`cloudflared`) or Tailscale:** Exposes the FastAPI server running on your M4 Mac to your team's iPhones over HTTPS/WSS without opening router ports, managing dynamic DNS, or paying for cloud servers.
    
- **WebSockets (`starlette.websockets` / `URLSessionWebSocketTask`):** Streams real-time pipeline status updates (`Transcribing...`, `Diarizing...`, `Extracting Tasks...`) directly to the iOS progress card.
    

### 3. Backend Framework & Process Orchestration (M4 Mac)

- **Python 3.11+ & FastAPI:** High-performance, asynchronous web framework. Native support for Pydantic v2 schemas guarantees strict typing and input validation for all audio metadata, task payloads, and RAG queries. Implements an audio streaming router with HTTP 206 Partial Content byte-range slicing to serve local MP3 audio dynamically to the iOS `AVPlayer`.
    
- **Uvicorn:** Lightweight ASGI server running the FastAPI application on Apple Silicon.
    
- **`asyncio.Queue` / Sequential Worker:** An in-process async worker queue ensuring heavy ML workloads run sequentially. This guarantees that Whisper transcription, Pyannote diarization, and LLM extraction do not run concurrently, keeping peak unified memory consumption well under the M4’s 16 GB limit.
    
- **FFmpeg (`ffmpeg-python`):** Normalizes incoming MP3 files to standardized 16 kHz 16-bit mono WAV buffers before speech processing.
    
- **`send2trash`:** Safe file handling library that interfaces natively with macOS `~/.Trash`, ensuring deleted meeting audio can be recovered.
    

### 4. Audio, Diarization & Identity Stack

- **`mlx-whisper`:** Apple Silicon-native Whisper port utilizing the M4 GPU and 16-core Neural Engine. Pointed at `mlx-community/whisper-large-v3-turbo` for rapid, low-memory transcription with word-level timestamps.
    
- **`pyannote.audio` (3.1):** State-of-the-art speaker diarization pipeline (VAD, speaker embedding, and clustering) to segment dialogue turn-by-turn.
    
- **SpeechBrain / Pyannote Embedding (`x-vector` / ResNet34):** Generates 512-dimensional speaker voice embeddings to populate persistent voice profiles across meetings.
    
- **NumPy & SciPy:** Runs fast vector cosine similarity to match detected speaker embeddings against stored voice profiles and calendar attendee candidates.
    

### 5. Task Extraction, Evolution & Deduplication Engine

- **Anthropic Claude API (`claude-3-5-sonnet` / `claude-3-5-haiku`):** Handles transcript cleaning, structured meeting summarization, professor suggestion isolation, and task extraction.
    
- **Pydantic v2 (Instructor / Structured Tool Calling):** Enforces rigid JSON schemas on LLM outputs to guarantee that extracted tasks include:
    
    - Assignee identity
        
    - Verbatim transcript evidence and timestamp offsets
        
    - Categorization (binding commitment vs. advisor suggestion)
        
- **Sentence-Transformers (`all-MiniLM-L6-v2` or `text-embedding-3-small`):** Embeds task descriptions into dense vector representations for semantic deduplication.
    
- **Task Matching Logic (NumPy + LLM Arbiter):** Calculates cosine distance between a newly mentioned task and historical open/blocked tasks. If similarity passes a threshold (e.g., $>0.82$), an LLM verification prompt checks whether shorthand (e.g., _"the rerun"_) refers to the existing task or represents a new objective.
    

### 6. RAG, Search & Citations

- **Hybrid Search (`pgvector` + PostgreSQL Full-Text Search):** Combines dense vector similarity with sparse BM25/keyword matching (`tsvector`). This is essential for research meetings where queries often contain specific technical jargon, model names, or proper nouns.
    
- **Conversational Turn Chunking:** Custom Python chunking utility that splits transcripts strictly along diarized speaker turns rather than raw character counts, embedding speaker metadata, meeting date, and start/end timestamps directly into each chunk.
    
- **Citation Grounding Module:** Custom prompt layer that forces the LLM to output inline reference tags matching chunk IDs (e.g., `[Ref: meeting_id#timestamp]`), which the iOS client renders as interactive audio scrub links.
    

### 7. Database, State Machine & Audit Trail

- **PostgreSQL 16 with `pgvector`:** The unified database for both relational application state and vector embeddings across 12 normalized tables. Storing vectors as native columns (`embedding vector(384)` on `transcripts` and `tasks`, `voice_embedding vector(512)` on `attendees`) eliminates join overhead, supports HNSW cosine indexing (`vector_cosine_ops`), and accelerates hybrid Reciprocal Rank Fusion (RRF) search.
        
- **SQLAlchemy 2.0 (Async) + Alembic:** Async Python ORM and schema migration manager to track evolving database models cleanly.
    
- **Append-Only Audit Ledger:** An immutable PostgreSQL table (`task_audit_log`) capturing every status transition across the 3-state operational lifecycle (`open`, `done`, `dropped`), while preserving the 2-state human-in-the-loop review status (`pending`, `approved`). Stores `task_id`, `changed_by`, `old_value`, `new_value`, `timestamp`, and a UUID `revert_token` to guarantee deterministic state rollbacks.
    

### 8. Evaluation & Benchmarking Harness

- **`jiwer`:** Calculates Word Error Rate (WER) against ground-truth audio fixtures to evaluate ASR accuracy.
    
- **`pyannote.metrics`:** Evaluates Diarization Error Rate (DER) and speaker confusion on recorded test meetings.
    
- **Ragas / DeepEval:** Evaluates RAG retrieval precision, context recall, and answer faithfulness to detect hallucinations across meeting histories.
    
- **Pytest + Pytest-Asyncio:** Unit and integration test suite executing reproducible evaluation fixtures on sample research meeting data.
    

### Summary of Stack Architecture

| **Layer**                | **Primary Technology**               | **Key Responsibility**                                                      |
| ------------------------ | ------------------------------------ | --------------------------------------------------------------------------- |
| **Mobile Client**        | SwiftUI                              | UI, Dashboards, Task Card Review, State Machine Picker                      |
| **Audio Playback**       | AVFoundation                         | Sub-second audio seeking from transcript/task citations                     |
| **Local OS Sync**        | Apple EventKit                       | Native Calendar matching and Apple Reminders sync                           |
| **Tunneling**            | Cloudflare Tunnel / Tailscale        | Secure remote connection from iOS to Mac backend                            |
| **Backend API**          | FastAPI / Uvicorn                    | Routing, background queue, project access guards                            |
| **Speech & Diarization** | MLX-Whisper + pyannote.audio         | Local Apple Silicon ASR and speaker separation                              |
| **LLM & Extraction**     | Claude 3.5 Sonnet + Pydantic         | Structured summaries, task extraction, deduplication check                  |
| **Database & Search**    | PostgreSQL 16 + `pgvector`           | Relational state, 3-state task lifecycle + review status, vector RAG search |
| **Safe Deletion**        | `send2trash`                         | Recoverable local file removal via macOS Trash                              |
| **Evaluation**           | Ragas + `jiwer` + `pyannote.metrics` | WER, DER, and RAG faithfulness benchmarks                                   |
