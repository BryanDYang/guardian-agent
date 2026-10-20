-- New projects start with follow-through enabled. Preserve every existing
-- project's saved settings and all member-level email preferences.
ALTER TABLE public.projects
    ALTER COLUMN followup_email_enabled SET DEFAULT true,
    ALTER COLUMN auto_approve_tasks SET DEFAULT true;
