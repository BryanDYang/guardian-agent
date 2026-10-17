-- Backend-only transactional outbox. Account emails stay on the server.
ALTER TABLE projects ADD COLUMN followup_email_enabled boolean NOT NULL DEFAULT false;
ALTER TABLE projects ADD COLUMN auto_approve_tasks boolean NOT NULL DEFAULT false;
ALTER TABLE project_members ADD COLUMN followup_email_enabled boolean NOT NULL DEFAULT true;

CREATE TABLE task_followup_emails (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id uuid NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    recipient_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    mode text NOT NULL CHECK (mode IN ('capture', 'resend')),
    payload jsonb,
    task_revision timestamptz,
    state text NOT NULL DEFAULT 'queued'
        CHECK (state IN ('queued','sending','captured','sent','cancelled','failed')),
    attempts integer NOT NULL DEFAULT 0,
    claim_token uuid,
    lease_until timestamptz,
    first_attempt_at timestamptz,
    next_attempt_at timestamptz NOT NULL DEFAULT now(),
    provider_id text,
    last_error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(task_id, recipient_id)
);
CREATE INDEX task_followup_emails_ready ON task_followup_emails(next_attempt_at, created_at)
    WHERE state IN ('queued','sending');
ALTER TABLE task_followup_emails ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON task_followup_emails FROM anon, authenticated;
