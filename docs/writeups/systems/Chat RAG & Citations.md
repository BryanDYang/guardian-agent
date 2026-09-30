# Project chat: hybrid RAG with citations

Implements Tech Stack section 6 (RAG, Search & Citations) end to end:
Postgres index -> hybrid search -> grounded answer -> iOS chat with citation chips.
Everything is in `chat-rag.patch`, made against the current working tree
(including the uncommitted `meeting_transcripts` rename).

```
git apply --check chat-rag.patch && git apply chat-rag.patch
supabase migration up            # or: supabase db push (applies 20261001000000_rag_chunks.sql)
uv sync --extra server --extra dev
labsync index                    # backfill meetings that completed before this change
```

## How a question is answered

1. **Index (at ingest).** When the worker saves a meeting's results, the same transaction
   calls `rag.index_meeting`, which rebuilds that meeting's rows in `rag_chunks`:
   - transcript **windows**: consecutive whole speaker turns packed up to 150 words, each
     line prefixed with its speaker label. A turn longer than 150 words is cut into pieces
     that all point back at that turn.
   - the meeting summary, each decision, and each task (commitment or suggestion) as its own
     row.
   Each row gets a 384-d `all-MiniLM-L6-v2` vector and a generated `tsvector`.
2. **Retrieve.** `rag.search` runs one SQL statement scoped to `project_id` (and to
   `meeting_id` when the conversation has one):
   - dense leg: exact cosine distance over the project's rows
   - sparse leg: full-text search with the question's terms OR-ed together (`plainto_tsquery`
     alone ANDs every word, so natural-language questions would rarely match)
   - fused with RRF (k = 60), top 8. Dismissed tasks are excluded.
   The retrieval text is the new question plus the previous one, so follow-ups like
   "who owns that?" still find something.
3. **Build sources.** Each hit is loaded **live** from the database and given a handle:
   `[T3]` transcript turn, `[D1]` decision, `[K2]` task (with current review, lifecycle,
   owner, and due date), `[S1]` summary. The sources are grouped by meeting in the prompt.
4. **Answer.** The configured provider (`codex` or `claude`, same as extraction) returns
   `{answerable, answer, citations: [{ref, quote}]}` through the existing schema-constrained
   channel. If nothing was retrieved, it refuses without calling the model.
5. **Verify.** `chat.finalize` keeps a citation only when its ref was shown to the model and
   its quote appears in that source (ignoring whitespace differences). It drops markers
   that fail this check, renumbers the rest `[1]`, `[2]`, ..., and maps each one to
   `meeting_id`, `turn_key`, `speaker`, and `start_time_ms`. If no verified citation
   remains, the reply becomes the fixed refusal: *"I don't know. The meetings in this
   project don't cover that."*
6. **Store.** The question and the answer (with its `citations` JSONB) commit together.
   If the model fails, the route returns 502 and stores nothing.

## Decisions that differ from the writeup

| Writeup says | Implemented | Why |
|---|---|---|
| One chunk per speaker turn | Windows of whole turns, max 150 words | Stored turns range from 1 to 664 words (median 9-17). 1-word turns are noise, and MiniLM truncates at 256 tokens. |
| Embed `meeting_transcripts.embedding` | New `rag_chunks` table | A window spans several turns, and summaries, decisions, and tasks also need to be searchable. The old column is now unused; I left it in place. |
| HNSW index | Exact scan per project | HNSW filters after the ANN step, so project-scoped queries can come back short. Exact search over a few thousand rows is fast and has perfect recall. The migration explains how to add HNSW later. |
| Model writes `[Ref: meeting_id#timestamp]` | Model writes `[T3]`; the server maps it | The model can't invent an ID or a time, and every citation's quote is checked. |
| Transcripts only | Transcripts plus summaries, decisions, and tasks | Matches the project description ("what was decided" should find the decision record). |

## API (`/api/v1/conversations`)

| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/conversations` | `{project_id, meeting_id?}`. Returns 404 if the meeting isn't in that project. |
| GET | `/api/v1/conversations?project_id=` | Newest first. Leave out `project_id` for All. Threads with no messages are hidden. |
| GET | `/api/v1/conversations/{id}` | Conversation plus `messages[]` |
| POST | `/api/v1/conversations/{id}/messages` | `{content}` -> `{user_message, assistant_message}`. The model gets 90 s (under Cloudflare's 100 s limit). The DB connection is released while the model runs. |

Citation JSON: `number, kind, meeting_id, meeting_name, meeting_date, turn_key, speaker,
start_time_ms, quote`.

## Schema changes (`20261001000000_rag_chunks.sql`)

- `rag_chunks` table, as described above.
- `chat_conversations.project_id` is now NOT NULL, and both foreign keys are now
  ON DELETE CASCADE. With the old SET NULL, deleting a meeting would silently widen a
  meeting-scoped chat to the whole project.
- `DELETE /api/projects/{id}/meetings` (purge) now also deletes that project's
  conversations, because they quote the purged meetings.

## Files

Backend: new files `chunking.py`, `embeddings.py`, `chat.py`, `db/rag.py`, `db/chat.py`,
`api/chat.py`. Edited: `server.py` (router, embedder, index on save), `providers.py` +
`claude_client.py` + `codex_client.py` (the call code is shared so chat reuses it;
extraction behavior and error messages are unchanged), `cli.py` (`labsync index`),
`db/meetings.py` (purge), `pyproject.toml` (`sentence-transformers` added to the `server`
extra).

iOS: `ChatView` (sends to the API; one menu picks project and "All meetings" or a single
meeting; changing either starts a new chat), `MessageBubble` (`[n] Meeting @ mm:ss`
chips), `ChatHistoryDrawer` (server history with All/project filter; opening a thread
restores its scope), `ChatMessage` (+ `init(remote:)`), `MeetingAPIClient` (4 calls +
types), `MeetingNavigator` (`pendingSeekMilliseconds`).

## Verification

- Done: 116 tests pass (91 existing + 25 new) against Postgres 16 + pgvector with every
  migration applied to a fresh database. The patch applies cleanly to the current tree. The
  new code passes ruff; the 6 E501 errors that remain were already in the uncommitted
  `db/meetings.py` and `tests/test_api_meetings.py`.
- New tests cover: chunk packing and splitting, the citation verify/renumber/refuse rules,
  project isolation, meeting scope, live task status, exclusion of dismissed tasks, RRF
  (a keyword-only hit still ranks), history and titles, a model failure storing nothing,
  purge, and the pipeline building the index (including a retry replacing it).
- **Not verified here:**
  1. **Real MiniLM.** Hugging Face was blocked in my sandbox, so tests use a hashing
     embedder. On the Mac: `labsync index`, then ask a real question.
  2. **Real Codex or Claude replies.** The model was faked in tests. Try one "what did we
     decide about X" question and one question the meetings don't cover.
  3. **Swift.** I couldn't compile it (no Xcode here). Build before relying on it.
  4. **pgvector on Supabase.** Only the base `vector` type and `<=>` are used, so any
     version should work.

## Known limits / follow-ups

- **Tapping a citation** opens the meeting's Transcript tab and sets
  `navigator.pendingSeekMilliseconds`. Nothing seeks yet because `AudioDockView` is still
  a static mock (checklist Phase 6). The AVPlayer work should read and clear that value.
- **Citations need the meeting stored locally.** A citation opens a meeting from the local
  SwiftData store. If that server meeting hasn't synced to the phone yet, the detail view
  shows "Meeting not found".
- **Indexing failures fail the meeting.** Indexing shares the save transaction, so if the
  embedding model can't load, the meeting is marked failed. Retrying after fixing it works.
- **Edited task titles aren't re-embedded.** Chat always shows the live title, but search
  still matches the original one.
- **Codex latency.** Codex CLI starts a process per question. If chat feels slow, run the
  server with `--provider claude`.
- **No streaming.** Answers arrive whole. Server-sent events would remove the 100 s tunnel
  limit if it ever becomes a problem.