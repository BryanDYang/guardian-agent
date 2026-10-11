-- Opt-in shared processing. Local-mode servers do not read this queue.
CREATE TABLE public.meeting_jobs (
    meeting_id uuid PRIMARY KEY REFERENCES public.meetings(id) ON DELETE CASCADE,
    object_key text NOT NULL UNIQUE,
    record jsonb NOT NULL,
    settings jsonb NOT NULL,
    state text NOT NULL CHECK (state IN ('uploading','queued','running','completed','failed')),
    claim_token uuid,
    worker_id text,
    lease_until timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX meeting_jobs_available ON public.meeting_jobs (state, lease_until, created_at);
ALTER TABLE public.meeting_jobs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.meeting_jobs FROM anon, authenticated;

-- Object deletion is retried after the corresponding DB transaction commits.
CREATE TABLE public.audio_deletions (
    object_key text PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.audio_deletions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.audio_deletions FROM anon, authenticated;
CREATE FUNCTION public.enqueue_audio_deletion() RETURNS trigger
LANGUAGE plpgsql SET search_path = public AS $$
BEGIN
    INSERT INTO audio_deletions(object_key) VALUES (OLD.object_key)
    ON CONFLICT DO NOTHING;
    RETURN OLD;
END;
$$;
CREATE TRIGGER meeting_job_audio_deletion BEFORE DELETE ON public.meeting_jobs
FOR EACH ROW EXECUTE FUNCTION public.enqueue_audio_deletion();

INSERT INTO storage.buckets(id, name, public, file_size_limit)
VALUES ('meeting-audio', 'meeting-audio', false, 536870912)
ON CONFLICT (id) DO NOTHING;
-- No client policies: backend checks membership before privileged storage access.
