-- Project content stays intact during the recovery window. Existing RLS remains
-- deny-by-default; project access continues through the authenticated API.
ALTER TABLE public.projects ADD COLUMN deleted_at timestamptz;
CREATE INDEX projects_deleted_at_idx ON public.projects (deleted_at)
    WHERE deleted_at IS NOT NULL;
ALTER TABLE public.project_members ADD COLUMN archived_at timestamptz;

-- Record local files before cascades remove their database references. A backend
-- only consumes entries belonging to its own storage directory.
CREATE TABLE public.local_recording_deletions (
    meeting_id uuid PRIMARY KEY,
    audio_file_path text NOT NULL
);
ALTER TABLE public.local_recording_deletions ENABLE ROW LEVEL SECURITY;
CREATE FUNCTION public.queue_local_recording_deletion() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
BEGIN
    IF OLD.audio_file_path LIKE '/%' THEN
        INSERT INTO public.local_recording_deletions(meeting_id, audio_file_path)
        VALUES (OLD.id, OLD.audio_file_path) ON CONFLICT DO NOTHING;
    END IF;
    RETURN OLD;
END;
$$;
REVOKE EXECUTE ON FUNCTION public.queue_local_recording_deletion()
    FROM PUBLIC, anon, authenticated;
CREATE TRIGGER queue_local_recording_deletion
    BEFORE DELETE ON public.meetings
    FOR EACH ROW EXECUTE FUNCTION public.queue_local_recording_deletion();
