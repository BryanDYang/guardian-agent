-- Chat is always scoped to one project, optionally narrowed to one meeting.
-- Deleting either one deletes its conversations. With the original
-- ON DELETE SET NULL, a meeting-scoped chat would silently widen to the whole
-- project, and quotes from a purged meeting would outlive it.
-- Nothing has written these tables yet, so SET NOT NULL cannot fail.

ALTER TABLE chat_conversations
    ALTER COLUMN project_id SET NOT NULL,
    DROP CONSTRAINT chat_conversations_project_id_fkey,
    ADD CONSTRAINT chat_conversations_project_id_fkey
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    DROP CONSTRAINT chat_conversations_meeting_id_fkey,
    ADD CONSTRAINT chat_conversations_meeting_id_fkey
        FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE;