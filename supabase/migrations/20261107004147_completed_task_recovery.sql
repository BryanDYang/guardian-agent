ALTER TABLE public.tasks
    ADD COLUMN archived_at timestamptz,
    ADD COLUMN deleted_at timestamptz;
CREATE INDEX tasks_deleted_at_idx ON public.tasks(deleted_at)
    WHERE deleted_at IS NOT NULL;
