> **Historical design/reference:** Preserved for rationale and context. Use [current architecture](../../../architecture.md) for implementation and [the roadmap](../../../milestone_3/roadmap.md) for current work.

The Ingestion & Sequential Worker Service is the backend orchestration engine running on the host M4 Mac via FastAPI and Uvicorn. It bridges incoming network uploads to the local ML models, enforcing project-level security and coordinating resource-intensive pipelines one meeting at a time.

**1. Ingestion Gateway & Access Verification**

- **Consent & Boundary Enforcement:** Serves as the initial entry point for uploads (`POST /meetings/upload`), rejecting requests that fail the bearer authentication check, lack a valid `project_id`, or omit the mandatory participant consent confirmation flag.
- **Database Meeting Initialization:** Instantiates the initial `MEETINGS` relational row in PostgreSQL with basic metadata (project ID, meeting date, filename) before passing execution down to the asynchronous processing queue.
    
**2. Memory-Constrained Sequential Worker (`asyncio.Queue`)**

- **Unified Memory Protection:** Because transcription (MLX-Whisper) and diarization (pyannote.audio) share the M4 Mac's unified memory pool with macOS system processes, concurrent runs could cause out-of-memory crashes.
    
- **Sequential Dispatch:** Uses an in-process asynchronous FIFO worker queue (`asyncio.Queue`) to guarantee that only a single meeting executes at any given moment. This caps peak memory consumption strictly below 10 GB on a 16 GB Apple Silicon machine.
    

**3. Acoustic Pre-Processing & FFmpeg Normalization**

- **Audio Harmonization:** Accepts various incoming formats (such as MP3, M4A from iOS Voice Memos, or Zoom MP4 tracks) and validates their bitrates and headers.
    
- **WAV Transcoding:** Invokes `ffmpeg-python` to transcode the raw recording into a standardized 16 kHz 16-bit mono WAV buffer. This normalization prevents known tensor format issues in pyannote and prepares standardized audio inputs for Whisper.
    

**4. Real-Time WebSocket Telemetry**

- **Granular Status Streaming:** Emits state-machine transitions over a persistent WebSocket connection (`WS /ws/pipeline/{job_id}`).
- **Client Feedback:** Keeps the SwiftUI interface in sync by broadcasting real-time progress strings (_"Transcribing..."_, _"Diarizing..."_, _"Resolving Speakers..."_, _"Extracting Tasks..."_, _"Complete"_) as stages complete.
    

**5. Safe File Lifecycle & Recoverable Quarantining**

- **Controlled Storage:** Stages processed audio files into a dedicated sandbox folder on the local macOS filesystem for subsequent byte-range HTTP streaming.
    
- **Recoverable Deletion:** When a meeting is deleted via `DELETE /meetings/{id}`, the service invokes `send2trash` rather than permanent unlinking, safely moving the audio asset to macOS `~/.Trash` so accidental deletions can be restored.

## API Specification
| **Endpoint**                | **Method** | **Auth Required** | **Request Body / Query** | **Status Codes**                                                 | **Description**                                                                                                                                                                               |
| --------------------------- | ---------- | ----------------- | ------------------------ | ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/pipeline/ jobs/ {job_id}` | `GET`      | Yes               | None                     | `200 OK`, `401 Unauthorized`, `404 Not Found`                    | Returns the current queue position, processing status (`queued`, `transcribing`, `diarizing`, `extracting`, `completed`, `failed`), error logs, and the resulting `meeting_id` once finished. |
| `/pipeline/ jobs/ {job_id}` | `DELETE`   | Yes               | None                     | `200 OK`, `400 Bad Request`, `401 Unauthorized`, `404 Not Found` | Cancels a queued job from `asyncio.Queue` or aborts execution before audio normalization or ML models load into unified memory                                                                |