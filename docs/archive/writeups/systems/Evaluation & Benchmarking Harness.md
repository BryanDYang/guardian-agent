> **Historical design/reference:** Preserved for rationale and context. Use [current architecture](../../../architecture.md) for implementation and [the roadmap](../../milestone_3/roadmap.md) for current work.

The Evaluation & Benchmarking Harness is an offline, decoupled testing suite built with `pytest`, `jiwer`, `pyannote.metrics`, and `ragas`. It runs locally on the host Mac to quantify error propagation across each discrete stage of the pipeline—from raw acoustics to grounded RAG responses—without touching production database tables or the mobile client.

**1. Acoustic Transcription Benchmarking (`jiwer`)**

- **Word Error Rate ($WER$):** Computes substitution, deletion, and insertion rates ($WER = \frac{S + D + I}{N}$) against human-annotated baseline recordings to benchmark `mlx-whisper` performance.
    
- **Timestamp Alignment Precision:** Asserts that word-level token offsets remain within a $\pm200\text{ ms}$ tolerance window to prevent playhead drift during `AVPlayer.seek(to: CMTime)` scrubbing.
    

**2. Diarization & Biometric Identification (`pyannote.metrics`)**

- **Diarization Error Rate ($DER$):** Measures the fraction of total recording time that contains errors ($DER = \frac{T_{\text{miss}} + T_{\text{fa}} + T_{\text{conf}}}{T_{\text{total}}}$). It tracks speaker confusion ($T_{\text{conf}}$) to assess whether overlapping voices are correctly separated.
    
- **Voice Match Calibration:** Sweeps cosine distance thresholds ($0.65$ to $0.85$) on 512-dimensional x-vectors to calibrate identification accuracy for recurring attendees versus unknown guest speakers.
    

**3. Cognitive Extraction & Deduplication Accuracy**

- **Artifact Extraction F1:** Scores Claude 3.5 Pydantic extractions (tasks, consensus decisions, and attendee storylines) against ground-truth meeting fixtures, measuring precision and recall on deliverable text and assignee attribution.
    
- **Deduplication Arbitration Benchmarking:** Runs synthesized task pairs through the 384-dimensional `sentence-transformers` embedding check and Claude arbiter to ensure existing open tasks are updated rather than duplicated.
    

**4. RAG Grounding & Citation Faithfulness (`ragas`)**

- **Faithfulness:** Breaks assistant responses into claims and verifies that $100\%$ of assertions are directly supported by retrieved transcript context, flagging hallucinations.
    
- **Context Precision & Recall:** Benchmarks whether the hybrid pgvector and BM25 RRF search retrieves the relevant chunks within the top 3 positions.
    
- **Refusal Validation:** Feeds out-of-scope adversarial questions to verify that the RAG pipeline outputs the expected grounded refusal (_"I don't know"_) rather than guessing.
    

**Database & API Requirements**

- **API Specification:** Requires **zero** client-facing REST or WebSocket endpoints. It executes strictly as a local CLI tool (`pytest tests/benchmarks/`) during local development and CI runs.
    
- **Database Setup:** Operates statelessly against pre-recorded golden fixture files (`tests/fixtures/*.wav`, `*.json`) or targets an isolated, ephemeral PostgreSQL test database (`labsync_test`) that spins up, seeds fixtures, and tears down automatically per test run.