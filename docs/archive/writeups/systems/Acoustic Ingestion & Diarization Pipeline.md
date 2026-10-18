> **Historical design/reference:** Preserved for rationale and context. Use [current architecture](../../../architecture.md) for implementation and [the roadmap](../../../milestone_3/roadmap.md) for current work.

The Acoustic Ingestion & Diarization Pipeline converts raw multi-party audio recordings into timestamped, speaker-attributed transcript turns on Apple Silicon hardware. It executes sequentially on the M4 Mac to keep peak unified memory under 10 GB while isolating speakers using voice biometrics and calendar context.

- **Audio Ingestion & Format Standardization:** Accepts multi-megabyte audio files (.mp3, .m4a, .wav) or video tracks (.mp4, .mov) imported via iOS Voice Memos, Files, or Zoom. Invokes FFmpeg (`ffmpeg-python`) to validate bitrates and normalize the stream into a standardized 16 kHz 16-bit mono WAV buffer, preventing tensor compatibility issues in pyannote.
    
- **Neural Engine ASR (MLX-Whisper):** Loads `whisper-large-v3-turbo` via `mlx-whisper` directly on the M4 GPU and Apple Neural Engine. It runs 3–4× faster than CPU Whisper, producing high-fidelity text with word-level timestamped tokens.
    
- **Vocal Turn Segmentation (pyannote.audio):** Applies `pyannote/speaker-diarization-3.1` to perform voice activity detection (VAD) and clustering. It segments conversational audio turn-by-turn into discrete speaker intervals (e.g., `SPEAKER_00: 00:00 - 00:14`, `SPEAKER_01: 00:15 - 00:32`) optimized for 2–5 participants.
    
- **Biometric Fingerprinting & Identity Resolution:**
    
    - Generates 512-dimensional x-vector/ResNet34 speaker voice embeddings from each speaker turn.
        
    - Computes vector cosine similarity with NumPy and SciPy against stored voice profiles in PostgreSQL to identify returning participants.
        
    - Cross-references candidate identities against attendee names and emails retrieved from Apple EventKit calendar events matching the recording timestamp.
        
    - Parses transcript cues using heuristic regex (such as _"Hi Hana"_ or _"Thanks Dana"_) to detect participant names when calendar or voice profile matches are absent.
        
- **Turn Alignment & Persistence:** Aligns Whisper’s word-level tokens with pyannote’s turn boundaries to produce structured transcript utterances. It writes each record to the `TRANSCRIPTS` table with millisecond playhead boundaries (`start_time_ms`, `end_time_ms`), speaker names, and profile initials to drive AVPlayer scrubbing and structured LLM extraction.