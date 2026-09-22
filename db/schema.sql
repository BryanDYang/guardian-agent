-- ============================================================================
-- PostgreSQL 16 schema
-- Source: docs/writeups/systems/Native Presentation System.md ("Database Setup"
--         and "Database Connection" ER diagrams) + docs/writeups/systems/
--         Unified Persistence & Hybrid Search Store.md
--
-- Requires PostgreSQL 16 with the pgvector extension installed.
-- Run against a fresh database, e.g.:
--   createdb labsync
--   psql -d labsync -f db/schema.sql
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- Extensions
-- ----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS vector;    -- pgvector: vector(n), <=> operator, HNSW

-- ============================================================================
-- 1. PROJECTS
-- Top-level scoping boundary. Deleting a project cascades to everything
-- scoped under it (meetings, tasks, chat conversations).
-- ============================================================================
CREATE TABLE projects (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    image_url   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 2. MEETINGS
-- Deleting a project removes its meetings. Meeting-level artifacts
-- (transcripts, summaries, decisions, storylines) cascade from here per the
-- ER diagram's explicit "[ON DELETE CASCADE]" annotations.
-- ============================================================================
CREATE TABLE meetings (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name                VARCHAR(255) NOT NULL,
    meeting_date        TIMESTAMPTZ NOT NULL,
    audio_file_path     TEXT,
    duration_seconds    INTEGER,
    calendar_event_id   TEXT,
    consent_given       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_meetings_project_id ON meetings(project_id);

-- ============================================================================
-- 3. ATTENDEES
-- Attendees are enrolled once and referenced across many meetings, so they
-- are not owned by a single meeting/project and are never cascade-deleted
-- by meeting/project removal (voice profiles and history should survive).
-- ============================================================================
CREATE TABLE attendees (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(255) NOT NULL,
    avatar_url          TEXT,
    contact_identifier  VARCHAR(255),
    voice_embedding     vector(512),  -- 512-d x-vector (pyannote/ResNet34)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- HNSW index for fast approximate cosine matching of returning speakers.
CREATE INDEX idx_attendees_voice_embedding_hnsw
    ON attendees USING hnsw (voice_embedding vector_cosine_ops);

-- ============================================================================
-- 4. MEETING_ATTENDEES (join table)
-- Composite PK; both legs cascade since the row has no meaning without
-- either parent.
-- ============================================================================
CREATE TABLE meeting_attendees (
    meeting_id      UUID NOT NULL REFERENCES meetings(id)   ON DELETE CASCADE,
    attendee_id     UUID NOT NULL REFERENCES attendees(id)  ON DELETE CASCADE,
    speaker_label   VARCHAR(64),  -- diarizer tag, e.g. SPEAKER_00
    PRIMARY KEY (meeting_id, attendee_id)
);

CREATE INDEX idx_meeting_attendees_attendee_id ON meeting_attendees(attendee_id);

-- ============================================================================
-- 5. TRANSCRIPTS
-- Cascades from meetings ("segments [ON DELETE CASCADE]"). attendee_id is
-- nullable ("speaks", optional leg) so an unresolved speaker doesn't block
-- transcript ingestion; if the attendee record is later removed the turn
-- is kept but unattributed (SET NULL).
-- ============================================================================
CREATE TABLE transcripts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id      UUID NOT NULL REFERENCES meetings(id)  ON DELETE CASCADE,
    attendee_id     UUID REFERENCES attendees(id)          ON DELETE SET NULL,
    speaker_name    VARCHAR(255),
    start_time_ms   INTEGER NOT NULL,
    end_time_ms     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    turn_order      INTEGER NOT NULL,
    embedding       vector(384),  -- dense chunk vector for RAG (all-MiniLM-L6-v2)
    tsv             TSVECTOR      -- lexical BM25/full-text vector, kept in sync by trigger below
);

CREATE INDEX idx_transcripts_meeting_id ON transcripts(meeting_id);
CREATE INDEX idx_transcripts_meeting_turn_order ON transcripts(meeting_id, turn_order);

-- Dense leg of hybrid search (ANN cosine).
CREATE INDEX idx_transcripts_embedding_hnsw
    ON transcripts USING hnsw (embedding vector_cosine_ops);

-- Sparse leg of hybrid search (BM25-style ranking via ts_rank).
CREATE INDEX idx_transcripts_tsv_gin
    ON transcripts USING gin (tsv);

-- to_tsvector(regconfig, text) is STABLE, not IMMUTABLE, so tsv can't be a
-- generated column; keep it in sync with a trigger instead.
CREATE OR REPLACE FUNCTION transcripts_tsv_trigger() RETURNS trigger AS $$
BEGIN
    NEW.tsv := to_tsvector('english', coalesce(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_transcripts_tsv_update
    BEFORE INSERT OR UPDATE OF content ON transcripts
    FOR EACH ROW EXECUTE FUNCTION transcripts_tsv_trigger();

-- ============================================================================
-- 6. MEETING_SUMMARIES
-- One-to-one with meetings ("synthesizes [ON DELETE CASCADE]"); meeting_id
-- is UNIQUE to enforce the 1:1 relationship.
-- ============================================================================
CREATE TABLE meeting_summaries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id      UUID NOT NULL UNIQUE REFERENCES meetings(id) ON DELETE CASCADE,
    overview        TEXT,
    bullet_points   JSONB,
    rubric_scores   JSONB,
    user_notes      TEXT,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 7. MEETING_DECISIONS
-- Cascades from meetings ("yields [ON DELETE CASCADE]"). transcript_id is
-- the optional evidence leg ("evidences") — kept but unlinked if that
-- specific transcript turn is ever removed independently.
-- ============================================================================
CREATE TABLE meeting_decisions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id          UUID NOT NULL REFERENCES meetings(id)    ON DELETE CASCADE,
    transcript_id       UUID REFERENCES transcripts(id)          ON DELETE SET NULL,
    decision_statement  TEXT NOT NULL,
    rationale           TEXT,
    timestamp_ms        INTEGER,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_meeting_decisions_meeting_id ON meeting_decisions(meeting_id);

-- ============================================================================
-- 8. ATTENDEE_STORYLINES
-- Cascades from meetings ("generates [ON DELETE CASCADE]"); the attendee
-- leg ("attributes") is mandatory since a storyline has no meaning without
-- knowing whose it is.
-- ============================================================================
CREATE TABLE attendee_storylines (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id          UUID NOT NULL REFERENCES meetings(id)   ON DELETE CASCADE,
    attendee_id         UUID NOT NULL REFERENCES attendees(id)  ON DELETE CASCADE,
    what_they_want      TEXT,
    what_they_see       TEXT,
    what_they_discuss   TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_attendee_storylines_meeting_id ON attendee_storylines(meeting_id);

-- ============================================================================
-- 9. TASKS
-- Scoped to a project (cascade — deleting the project retires its tasks).
-- meeting_id/attendee_id/evidence_transcript_id are the optional legs
-- ("originates" / "assigns" / "verifies") and use SET NULL: approved tasks
-- are synced out to Apple Reminders/Calendar and should survive the source
-- meeting, attendee record, or evidence transcript being deleted later.
-- ============================================================================
CREATE TABLE tasks (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id              UUID NOT NULL REFERENCES projects(id)     ON DELETE CASCADE,
    meeting_id              UUID REFERENCES meetings(id)              ON DELETE SET NULL,
    attendee_id             UUID REFERENCES attendees(id)             ON DELETE SET NULL,
    title                   TEXT NOT NULL,
    due_date                DATE,
    review_status           VARCHAR(32) NOT NULL DEFAULT 'pending'
        CHECK (review_status IN ('pending', 'approved', 'dismissed')),
    lifecycle_status        VARCHAR(32) NOT NULL DEFAULT 'open'
        CHECK (lifecycle_status IN ('open', 'done', 'dropped')),
    category                VARCHAR(32)
        CHECK (category IN ('commitment', 'advisor_suggestion')),
    evidence_transcript_id  UUID REFERENCES transcripts(id)           ON DELETE SET NULL,
    evidence_quote          TEXT,
    evidence_timestamp_ms   INTEGER,
    embedding               vector(384),  -- dense vector for dedup (all-MiniLM-L6-v2)
    eventkit_reminder_id    TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Composite index powering the SwiftUI calendar's date-range + status queries.
CREATE INDEX idx_tasks_project_due_lifecycle
    ON tasks (project_id, due_date, lifecycle_status);

CREATE INDEX idx_tasks_meeting_id ON tasks(meeting_id);

-- ANN index for the semantic-dedup similarity check (cosine > 0.80 threshold).
CREATE INDEX idx_tasks_embedding_hnsw
    ON tasks USING hnsw (embedding vector_cosine_ops);

-- ============================================================================
-- 10. TASK_AUDIT_LOG
-- Append-only ledger. Cascades from tasks — if a task record is ever
-- purged outright (not just "dropped"), its audit trail goes with it.
-- This is the "undo history" table.
-- ============================================================================
CREATE TABLE task_audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    action          VARCHAR(64) NOT NULL,       -- e.g. STATUS_CHANGE
    old_value       JSONB,
    new_value       JSONB,
    revert_token    UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_task_audit_log_task_id ON task_audit_log(task_id);

-- ============================================================================
-- 11. CHAT_CONVERSATIONS
-- project_id/meeting_id are both nullable scoping legs; a conversation can
-- be global, project-scoped, or meeting-scoped. SET NULL keeps the thread
-- around (demoted to a broader scope) if its project/meeting is removed.
-- ============================================================================
CREATE TABLE chat_conversations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID REFERENCES projects(id) ON DELETE SET NULL,
    meeting_id  UUID REFERENCES meetings(id) ON DELETE SET NULL,
    title       VARCHAR(255),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_chat_conversations_project_id ON chat_conversations(project_id);

-- ============================================================================
-- 12. CHAT_MESSAGES
-- Cascades from chat_conversations ("contains") — deleting a thread
-- deletes its messages.
-- ============================================================================
CREATE TABLE chat_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    role            VARCHAR(32) NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT NOT NULL,
    citations       JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_chat_messages_conversation_id ON chat_messages(conversation_id);

COMMIT;
