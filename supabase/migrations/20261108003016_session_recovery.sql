-- Session content remains intact until the recovery window expires.
ALTER TABLE public.meetings ADD COLUMN archived_at timestamptz;
ALTER TABLE public.meetings ADD COLUMN deleted_at timestamptz;
CREATE INDEX meetings_deleted_at_idx ON public.meetings (deleted_at)
    WHERE deleted_at IS NOT NULL;
