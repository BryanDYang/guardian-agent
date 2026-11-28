-- Preserve approval delivery deduplication while allowing one email per change.
ALTER TABLE task_followup_emails
  ADD COLUMN change_id uuid REFERENCES task_audit_log(id) ON DELETE CASCADE;
ALTER TABLE task_followup_emails
  DROP CONSTRAINT task_followup_emails_task_id_recipient_id_key;
CREATE UNIQUE INDEX task_followup_approval_once
  ON task_followup_emails(task_id, recipient_id) WHERE change_id IS NULL;
CREATE UNIQUE INDEX task_followup_change_once
  ON task_followup_emails(task_id, recipient_id, change_id)
  WHERE change_id IS NOT NULL;
CREATE INDEX task_followup_change_id ON task_followup_emails(change_id)
  WHERE change_id IS NOT NULL;
-- Existing RLS and revoked client grants remain in force.
