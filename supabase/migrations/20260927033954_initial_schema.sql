-- ============================================================================
-- LabSync initial schema (PostgreSQL 16 + pgvector)
--
-- Applied to Supabase as the first migration (supabase/migrations/).
-- RLS is enabled on every table with no policies: only the backend's direct
-- database connection can read or write. The iOS app never talks to Supabase.
--
-- Local testing without Supabase:
--   createdb labsync && psql -d labsync -f db/schema.sql
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- Extensions
-- ----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS vector;    -- pgvector: vector(n), <=> operator, HNSW

-- ============================================================================
-- 1. PROJECTS
-- Scoping boundary for meetings, tasks, and scoped conversational RAG.
-- ============================================================================
CREATE TABLE projects (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    image_url   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 2. MEETINGS
-- Includes sequential worker lifecycle states, retry counts, and ML metadata.
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
    status              VARCHAR(32) NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'transcribing', 'diarizing', 'extracting', 'completed', 'failed')),
    processing_attempt  INTEGER NOT NULL DEFAULT 1,
    error_message       TEXT,
    model_metadata      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_meetings_project_date ON meetings(project_id, meeting_date);
CREATE INDEX idx_meetings_status ON meetings(status);

ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 3. ATTENDEES
-- Speaker profiles. Uses vector(256) for pyannote.audio 3.1 embeddings.
-- ============================================================================
CREATE TABLE attendees (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(255) NOT NULL,
    avatar_url          TEXT,
    contact_identifier  VARCHAR(255),
    voice_embedding     vector(256),  -- 256-d embedding (pyannote 3.1 / Wespeaker-ResNet34)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_attendees_voice_embedding_hnsw
    ON attendees USING hnsw (voice_embedding vector_cosine_ops);

ALTER TABLE attendees ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 4. MEETING_ATTENDEES (join table)
-- Maps attendees to meetings and links raw diarization labels to real profiles.
-- ============================================================================
CREATE TABLE meeting_attendees (
    meeting_id      UUID NOT NULL REFERENCES meetings(id)   ON DELETE CASCADE,
    attendee_id     UUID NOT NULL REFERENCES attendees(id)  ON DELETE CASCADE,
    speaker_label   VARCHAR(64),  -- Diarizer tag, e.g. SPEAKER_00
    PRIMARY KEY (meeting_id, attendee_id)
);

CREATE INDEX idx_meeting_attendees_attendee_id ON meeting_attendees(attendee_id);
CREATE INDEX idx_meeting_attendees_speaker_label ON meeting_attendees(meeting_id, speaker_label);

ALTER TABLE meeting_attendees ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 5. TRANSCRIPTS
-- Stores word-aligned turns with mandatory pipeline turn keys and diarizer tags.
-- ============================================================================
CREATE TABLE transcripts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id      UUID NOT NULL REFERENCES meetings(id)  ON DELETE CASCADE,
    attendee_id     UUID REFERENCES attendees(id)          ON DELETE SET NULL,
    speaker_label   VARCHAR(64),  -- Raw diarizer tag (e.g. SPEAKER_01)
    speaker_name    VARCHAR(255), -- Resolved or manual display name
    turn_key        TEXT NOT NULL, -- Full pipeline citation key, e.g. '7db626a0-...:turn:12'
    start_time_ms   INTEGER NOT NULL,
    end_time_ms     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    turn_order      INTEGER NOT NULL,
    embedding       vector(384),  -- Dense passage vector for RAG (all-MiniLM-L6-v2)
    tsv             TSVECTOR,     -- Full-text BM25 vector, updated via trigger
    CONSTRAINT uq_transcripts_meeting_turn UNIQUE (meeting_id, turn_key)
);

CREATE INDEX idx_transcripts_meeting_id ON transcripts(meeting_id);
CREATE INDEX idx_transcripts_meeting_turn_order ON transcripts(meeting_id, turn_order);

-- Dense vector index (ANN Cosine)
CREATE INDEX idx_transcripts_embedding_hnsw
    ON transcripts USING hnsw (embedding vector_cosine_ops);

-- Sparse full-text index
CREATE INDEX idx_transcripts_tsv_gin
    ON transcripts USING gin (tsv);

-- Automatic tsvector synchronization trigger
CREATE OR REPLACE FUNCTION transcripts_tsv_trigger() RETURNS trigger AS $$ BEGIN     NEW.tsv := to_tsvector('english', coalesce(NEW.content, ''));     RETURN NEW; END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_transcripts_tsv_update
    BEFORE INSERT OR UPDATE OF content ON transcripts
    FOR EACH ROW EXECUTE FUNCTION transcripts_tsv_trigger();

ALTER TABLE transcripts ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 6. MEETING_SUMMARIES
-- 1:1 synthesis for narrative takeaways, bullet points, and rubric evaluations.
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

ALTER TABLE meeting_summaries ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 7. MEETING_DECISIONS
-- Group consensus items. Detailed citations are linked via `item_evidence`.
-- ============================================================================
CREATE TABLE meeting_decisions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id          UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    decision_statement  TEXT NOT NULL,
    rationale           TEXT,
    timestamp_ms        INTEGER,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_meeting_decisions_meeting_id ON meeting_decisions(meeting_id);

ALTER TABLE meeting_decisions ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 8. ATTENDEE_STORYLINES
-- Participant subjective POV vectors (what they want, see, discuss).
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

ALTER TABLE attendee_storylines ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 9. TASKS
-- Supports verbatim text deadlines and diarizer owners pending attendee mapping.
-- ============================================================================
CREATE TABLE tasks (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id              UUID NOT NULL REFERENCES projects(id)     ON DELETE CASCADE,
    meeting_id              UUID REFERENCES meetings(id)              ON DELETE SET NULL,
    attendee_id             UUID REFERENCES attendees(id)             ON DELETE SET NULL,
    owner_label             VARCHAR(64),  -- Raw diarizer owner (e.g. SPEAKER_03)
    title                   TEXT NOT NULL,
    due_date                DATE,         -- Populated when confirmed/parsed
    due_date_text           TEXT,         -- Raw extracted string (e.g. "next Tuesday")
    review_status           VARCHAR(32) NOT NULL DEFAULT 'pending'
        CHECK (review_status IN ('pending', 'approved', 'dismissed')),
    lifecycle_status        VARCHAR(32) NOT NULL DEFAULT 'open'
        CHECK (lifecycle_status IN ('open', 'done', 'dropped')),
    category                VARCHAR(32)
        CHECK (category IN ('commitment', 'advisor_suggestion')),
    embedding               vector(384),  -- Deduplication vector (all-MiniLM-L6-v2)
    eventkit_reminder_id    TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Operational index for the SwiftUI Calendar View
CREATE INDEX idx_tasks_project_due_lifecycle
    ON tasks (project_id, due_date, lifecycle_status);

CREATE INDEX idx_tasks_meeting_id ON tasks(meeting_id);
CREATE INDEX idx_tasks_owner_label ON tasks(owner_label);

-- Deduplication index (cosine similarity threshold checks)
CREATE INDEX idx_tasks_embedding_hnsw
    ON tasks USING hnsw (embedding vector_cosine_ops);

ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 10. ITEM_EVIDENCE
-- Normalizes multi-quote citations for decisions and tasks.
-- Stores full turn citation strings (e.g. '7db626a0-...:turn:12') to enable direct matching.
-- ============================================================================
CREATE TABLE item_evidence (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         UUID REFERENCES tasks(id)              ON DELETE CASCADE,
    decision_id     UUID REFERENCES meeting_decisions(id)  ON DELETE CASCADE,
    transcript_id   UUID REFERENCES transcripts(id)        ON DELETE SET NULL,
    turn_key        TEXT NOT NULL,  -- Matches full pipeline identifier (e.g. '7db626a0-...:turn:12')
    position        INTEGER NOT NULL,
    quote           TEXT NOT NULL,
    timestamp_ms    INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_evidence_parent CHECK (
        (task_id IS NOT NULL AND decision_id IS NULL) OR
        (task_id IS NULL AND decision_id IS NOT NULL)
    )
);

CREATE INDEX idx_item_evidence_task_id ON item_evidence(task_id);
CREATE INDEX idx_item_evidence_decision_id ON item_evidence(decision_id);
CREATE INDEX idx_item_evidence_transcript_id ON item_evidence(transcript_id);
CREATE INDEX idx_item_evidence_turn_key ON item_evidence(turn_key);

ALTER TABLE item_evidence ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 11. TASK_AUDIT_LOG
-- Append-only undo ledger for state reversals and tracking modifications.
-- ============================================================================
CREATE TABLE task_audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    action          VARCHAR(64) NOT NULL,  -- e.g. STATUS_CHANGE, DUE_DATE_CONFIRMED
    old_value       JSONB,
    new_value       JSONB,
    revert_token    UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_task_audit_log_task_id ON task_audit_log(task_id);

ALTER TABLE task_audit_log ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 12. CHAT_CONVERSATIONS
-- Conversation thread container supporting global, project-, or meeting-scope.
-- ============================================================================
CREATE TABLE chat_conversations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID REFERENCES projects(id)  ON DELETE SET NULL,
    meeting_id  UUID REFERENCES meetings(id)  ON DELETE SET NULL,
    title       VARCHAR(255),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_chat_conversations_project_id ON chat_conversations(project_id);

ALTER TABLE chat_conversations ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 13. CHAT_MESSAGES
-- Conversational exchanges with serialized citation chips for AVPlayer scrubbing.
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

ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

COMMIT;