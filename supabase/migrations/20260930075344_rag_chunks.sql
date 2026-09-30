-- Chat retrieval index (Tech Stack section 6). One row per searchable passage:
-- a window of transcript turns, a meeting summary, a decision, or a task.
-- No HNSW index: every search is filtered to one project, and HNSW would apply
-- that filter after the nearest-neighbor step. An exact scan per project is
-- fast at this size.

CREATE TABLE rag_chunks (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id        UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    meeting_id        UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    kind              VARCHAR(16) NOT NULL
        CHECK (kind IN ('transcript', 'summary', 'decision', 'task')),
    source_id         UUID,     -- meeting_decisions.id or tasks.id
    first_turn_order  INTEGER,  -- transcript windows only
    last_turn_order   INTEGER,
    start_time_ms     INTEGER,
    content           TEXT NOT NULL,
    embedding         vector(1536) NOT NULL, -- OpenAI text-embedding-3-small, unit length
    embedding_model   TEXT NOT NULL,
    tsv               TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_rag_chunks_turns CHECK (
        (kind = 'transcript')
        = (first_turn_order IS NOT NULL AND last_turn_order IS NOT NULL)
    ),
    CONSTRAINT chk_rag_chunks_source CHECK (
        (kind IN ('decision', 'task')) = (source_id IS NOT NULL)
    )
);

CREATE INDEX idx_rag_chunks_project_meeting ON rag_chunks(project_id, meeting_id);
CREATE INDEX idx_rag_chunks_meeting_id ON rag_chunks(meeting_id);
CREATE INDEX idx_rag_chunks_tsv_gin ON rag_chunks USING gin (tsv);

ALTER TABLE rag_chunks ENABLE ROW LEVEL SECURITY;