> **Historical design/reference:** Preserved for rationale and context. Use [current architecture](../../../architecture.md) for implementation and [the roadmap](../../milestone_3/roadmap.md) for current work.

The Structured Extraction & Task Reconciliation Engine is the post-transcription cognitive service that transforms raw, multi-speaker transcripts into structured relational records and deduplicated action items. Powered by Claude 3.5, Pydantic, and `sentence-transformers`, it executes in the background on the host Mac once the acoustic pipeline outputs aligned transcript turns.

**1. Schema-Enforced Extraction (Claude 3.5 + Pydantic)** The engine parses diarized transcript turns through Claude 3.5 using structured outputs (via Instructor or native tool-use schemas) to generate typed models:

- **Meeting Summaries:** Generates a high-level overview, sequential takeaway bullets, and optional qualitative rubric scores, saving directly to `MEETING_SUMMARIES`.
    
- **Consensus Decisions Ledger:** Isolates formal agreements reached by the group. For every decision, it extracts the final assertion, the agreed-upon rationale, discarded or rejected alternatives, and the exact millisecond offset where consensus was reached (`MEETING_DECISIONS`).
    
- **Attendee Storylines:** Analyzes the meeting through the subjective lens of each participant, structuring their stance into three discrete vectors: _what they want_ (goals and requests), _what they see_ (current status and observations), and _what they discuss_ (arguments, blockers, and topics raised) (`ATTENDEE_STORYLINES`).
    
- **Action Items:** Identifies prospective deliverables, assigned owners (matched to participant IDs), and explicit or inferred deadlines.
    

**2. Verifiable Evidence Citation** Every extracted decision and task is tied directly to source evidence. The engine extracts the verbatim sentence quote and cross-references Whisper's word-level timestamps to record exact playhead offsets (`evidence_timestamp_ms` and `evidence_quote`). This enables the SwiftUI client to deep-link users directly to source audio proof before they approve tasks or review decisions.

**3. Semantic Task Reconciliation & Deduplication** To prevent redundant action items when ongoing projects span multiple meetings, the engine runs a hybrid deduplication pipeline:

- **Dense Vector Generation:** Converts candidate task descriptions into 384-dimensional embeddings using a lightweight local embedding model (`sentence-transformers/all-MiniLM-L6-v2`) on Apple Silicon.
    
- **Similarity Scoping via pgvector:** Queries active, open tasks within the same `project_id` using cosine distance (`<=>`).
    
- **LLM Arbitration:** If a candidate task scores above a similarity threshold (e.g., cosine similarity > 0.80) against an existing open task, both items are submitted to a lightweight Claude prompt arbiter. The arbiter decides whether the new mention is:
    
    1. _A duplicate:_ Silently linked or discarded.
        
    2. _An update/progression:_ Merges new due dates or evidence notes into the existing task.
        
    3. _A distinct task:_ Staged as an independent item.
        

**4. Human-in-the-Loop Review Staging** Reconciled tasks are written to the `TASKS` table with `review_status = 'pending'` and `lifecycle_status = 'open'`. Staging them in this state ensures that automated AI extractions never automatically pollute the user's operational calendar or Apple Reminders until explicitly approved in the SwiftUI review card stack.



## API Specifications
| **Endpoint**                         | **Method** | **Auth Required** | **Request Body / Query**                                                      | **Status Codes**                                                                   | **Description**                                                                                                                                                                                                                                        |
| ------------------------------------ | ---------- | ----------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `/meetings/ {meeting_id}/ reextract` | `POST`     | Yes               | **Body (JSON):**<br>`{ "target": "all"/ "tasks"/ "storylines"/ "decisions" }` | `202 Accepted`, `400 Bad Request`, `401 Unauthorized`, `404 Not Found`             | Re-runs the LLM extraction and reconciliation pipeline. Typically triggered after a user manually reassigns speaker labels (e.g., remapping `SPEAKER_00` to a specific attendee) so storylines and task attributions reflect the corrected identities. |
| `/meetings/ {meeting_id}/ summary`   | `PATCH`    | Yes               | **Body (JSON):**<br>`{ "user_notes": string?, "rubric_scores": object? }`     | `200 OK`<br><br>`400 Bad Request`<br><br>`401 Unauthorized`<br><br>`404 Not Found` | Updates user-authored notes and qualitative rubric evaluations stored in the `MEETING_SUMMARIES` record.                                                                                                                                               |