"""Evidence-gated approval and immediate task email, separate from reminders."""

import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from threading import Event, Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

from psycopg.types.json import Jsonb

from .db import tasks

logger = logging.getLogger(__name__)
POLICY = "explicit-self-commitment-v1"


def delivery_mode():
    mode = os.environ.get("LABSYNC_EMAIL_MODE", "capture")
    if mode not in {"capture", "resend"}:
        raise ValueError("LABSYNC_EMAIL_MODE must be capture or resend")
    return mode


def enqueue(conn, task, mode=None):
    """Queue once per task/recipient in the approval transaction."""
    if task["review_status"] != "approved" or not task["assignee_user_id"]:
        return
    conn.execute(
        "INSERT INTO task_followup_emails(task_id,recipient_id,mode) "
        "SELECT %s,pm.user_id,%s FROM project_members pm "
        "JOIN projects p ON p.id=pm.project_id "
        "WHERE p.id=%s AND pm.user_id=%s AND p.followup_email_enabled "
        "AND pm.followup_email_enabled ON CONFLICT DO NOTHING",
        (
            task["id"],
            mode or delivery_mode(),
            task["project_id"],
            task["assignee_user_id"],
        ),
    )


def auto_approve(conn, meeting_id):
    """A narrow, auditable rule, not a calibrated model-confidence score.

    Human speaker/account confirmation is required once per recording. Provisional
    voice matches never qualify. Unknown dates and possible duplicates stay pending.
    """
    meeting = conn.execute(
        "SELECT m.*,p.auto_approve_tasks FROM meetings m JOIN projects p "
        "ON p.id=m.project_id WHERE m.id=%s FOR UPDATE OF p",
        (meeting_id,),
    ).fetchone()
    if not meeting or not meeting["auto_approve_tasks"]:
        return 0
    reviews = (meeting["model_metadata"] or {}).get("speaker_name_reviews", {})
    candidates = conn.execute(
        "SELECT id FROM tasks WHERE meeting_id=%s AND review_status='pending' "
        "ORDER BY id FOR UPDATE",
        (meeting_id,),
    ).fetchall()
    approved = 0
    for row in candidates:
        task = tasks.lock_task(conn, row["id"])
        if (
            task["category"] != "commitment"
            or not task["assignee_user_id"]
            or task["due_date_text"]
            or task["due_date"]
        ):
            continue
        # Require an actual current account mapping, not a guessed name.
        labels = {
            label
            for label, review in reviews.items()
            if review.get("method") == "human_confirmation"
            and review.get("processing_attempt") == meeting["processing_attempt"]
            and review.get("assignee_user_id") == str(task["assignee_user_id"])
        }
        if (
            not labels
            or not conn.execute(
                "SELECT 1 FROM project_members WHERE project_id=%s AND user_id=%s",
                (task["project_id"], task["assignee_user_id"]),
            ).fetchone()
        ):
            continue
        evidence = conn.execute(
            "SELECT e.quote,e.turn_key,t.content,t.speaker_label "
            "FROM item_evidence e JOIN meeting_transcripts t "
            "ON t.meeting_id=%s AND t.turn_key=e.turn_key WHERE e.task_id=%s",
            (meeting_id, task["id"]),
        ).fetchall()
        if not evidence or any(
            e["speaker_label"] not in labels
            or e["quote"] not in e["content"]
            or not re.match(r"^\s*I(?: will|'ll)\s+\w", e["content"], re.I)
            or re.search(
                r"\b(if|maybe|might|could|try|unless|not|never|still|already)\b|\?",
                e["content"],
                re.I,
            )
            for e in evidence
        ):
            continue
        # Fail closed when the model's title is not grounded in quoted words.
        words = set(re.findall(r"[a-z]+", task["title"].lower())) - {
            "the",
            "a",
            "an",
            "to",
            "and",
            "in",
            "on",
            "of",
            "my",
            "our",
        }
        quoted = set(
            re.findall(r"[a-z]+", " ".join(e["quote"] for e in evidence).lower())
        )
        if not words or not words <= quoted:
            continue
        # Compare with all non-dismissed work, including completed tasks. A later
        # mention must not silently reopen work or create a second commitment.
        if conn.execute(
            "SELECT 1 FROM tasks other JOIN tasks candidate ON candidate.id=%s "
            "WHERE other.project_id=candidate.project_id AND other.id<>candidate.id "
            "AND other.review_status<>'dismissed' AND ("
            "lower(other.title)=lower(candidate.title) OR candidate.embedding IS NULL "
            "OR other.embedding IS NULL OR "
            "1-(other.embedding <=> candidate.embedding)>=0.80) LIMIT 1",
            (task["id"],),
        ).fetchone():
            continue
        # At least one embedding is needed to compare future mentions reliably.
        if not conn.execute(
            "SELECT 1 FROM tasks WHERE id=%s AND embedding IS NOT NULL", (task["id"],)
        ).fetchone():
            continue
        conn.execute(
            "UPDATE tasks SET review_status='approved',approved_at=now(),"
            "updated_at=now() WHERE id=%s",
            (task["id"],),
        )
        conn.execute(
            "INSERT INTO task_audit_log(task_id,action,old_value,new_value) "
            "VALUES(%s,'AUTO_APPROVE',%s,%s)",
            (
                task["id"],
                Jsonb({"review_status": "pending"}),
                Jsonb(
                    {
                        "review_status": "approved",
                        "policy": POLICY,
                        "evidence": [
                            {"turn_key": e["turn_key"], "quote": e["quote"]}
                            for e in evidence
                        ],
                        "assignee_user_id": str(task["assignee_user_id"]),
                    }
                ),
            ),
        )
        enqueue(conn, tasks.lock_task(conn, task["id"]))
        approved += 1
    return approved


class ResendEmail:
    def __init__(self):
        self.key = os.environ["RESEND_API_KEY"]
        self.sender = os.environ["LABSYNC_EMAIL_FROM"]

    def send(self, key, payload):
        request = Request(
            "https://api.resend.com/emails",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
                "Idempotency-Key": key,
            },
        )
        with urlopen(request, timeout=10) as response:
            return json.load(response)["id"]


class EmailWorker:
    def __init__(self, pool, mode=None, sender=None):
        self.pool, self.mode = pool, mode or delivery_mode()
        self.sender = sender or (ResendEmail() if self.mode == "resend" else None)
        self.shutdown = Event()
        self.thread = Thread(target=self.loop, name="task-email-worker", daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.shutdown.set()
        if self.thread.is_alive():
            self.thread.join()

    def loop(self):
        while not self.shutdown.is_set():
            try:
                if self.process_one():
                    continue
            except Exception:
                logger.exception("Task email worker failed")
            self.shutdown.wait(2)

    def process_one(self):
        now = datetime.now(timezone.utc)
        token = uuid4()
        with self.pool.connection() as conn:
            row = conn.execute(
                "SELECT * FROM task_followup_emails WHERE mode=%s "
                "AND ((state='queued' AND next_attempt_at<=now()) OR "
                "(state='sending' AND lease_until<now())) ORDER BY created_at "
                "LIMIT 1 FOR UPDATE SKIP LOCKED",
                (self.mode,),
            ).fetchone()
            if not row:
                return False
            task = conn.execute(
                f"SELECT {tasks.COLUMNS} FROM tasks t WHERE t.id=%s "
                "FOR UPDATE SKIP LOCKED",
                (row["task_id"],),
            ).fetchone()
            if not task:
                return False
            recipient = conn.execute(
                "SELECT pr.email,pm.followup_email_enabled AS opted_in,"
                "p.followup_email_enabled AS enabled,m.name AS meeting_name "
                "FROM tasks t JOIN project_members pm ON pm.project_id=t.project_id "
                "AND pm.user_id=%s JOIN profiles pr ON pr.id=pm.user_id "
                "JOIN projects p ON p.id=t.project_id "
                "LEFT JOIN meetings m ON m.id=t.meeting_id WHERE t.id=%s",
                (row["recipient_id"], row["task_id"]),
            ).fetchone()
            valid = (
                recipient
                and recipient["opted_in"]
                and recipient["enabled"]
                and task["review_status"] == "approved"
                and task["lifecycle_status"] == "open"
                and task["assignee_user_id"] == row["recipient_id"]
            )
            # The provider retains idempotency keys for 24h. Never retry a
            # potentially accepted request outside that window.
            expired = row["first_attempt_at"] and now - row[
                "first_attempt_at"
            ] >= timedelta(hours=23)
            changed = row["payload"] and row["task_revision"] != task["updated_at"]
            if row["payload"] and recipient:
                changed = changed or row["payload"]["to"] != [recipient["email"]]
            if not valid or changed or expired:
                conn.execute(
                    "UPDATE task_followup_emails SET state=%s,last_error=%s,"
                    "updated_at=now() WHERE id=%s",
                    (
                        "failed" if expired else "cancelled",
                        "Retry window expired; check provider before resending"
                        if expired
                        else "Task, recipient, or email settings changed",
                        row["id"],
                    ),
                )
                return True
            payload = row["payload"] or {
                "from": getattr(
                    self.sender, "sender", "LabSync <capture@example.test>"
                ),
                "to": [recipient["email"]],
                "subject": "LabSync: "
                + task["title"].replace("\n", " ").replace("\r", " ")[:150],
                "text": (
                    f"Your task: {task['title']}\n"
                    f"Meeting: {recipient['meeting_name'] or 'Project task'}\n"
                    f"Due: {task['due_date'] or 'No deadline set'}\n\n"
                    f"Meeting evidence: {task['quote'] or 'No source quote'}\n\n"
                    "Review your tasks: meetingmemory://tasks\n\n"
                    "Open LabSync > Tasks > To-do to review, correct, or complete "
                    "this task. Manage follow-up email in the project's "
                    "Follow-through settings.\n"
                    "This is a task follow-up, not a recurring reminder."
                ),
            }
            conn.execute(
                "UPDATE task_followup_emails SET state='sending',payload=%s,"
                "task_revision=%s,claim_token=%s,"
                "lease_until=now()+interval '60 seconds',"
                "first_attempt_at=coalesce(first_attempt_at,now()),attempts=attempts+1,"
                "updated_at=now() WHERE id=%s",
                (Jsonb(payload), task["updated_at"], token, row["id"]),
            )
        # The approval and outbox claim are committed before the network call.
        try:
            provider_id = (
                self.sender.send(f"labsync-task/{row['id']}", payload)
                if self.mode == "resend"
                else None
            )
        except Exception as exc:
            permanent = (
                isinstance(exc, HTTPError)
                and 400 <= exc.code < 500
                and exc.code not in {408, 409, 429}
            )
            with self.pool.connection() as conn:
                conn.execute(
                    "UPDATE task_followup_emails SET state=%s,last_error=%s,"
                    "next_attempt_at=now()+make_interval(secs => %s),updated_at=now() "
                    "WHERE id=%s AND claim_token=%s",
                    (
                        "failed" if permanent else "queued",
                        f"Email request failed ({type(exc).__name__})",
                        min(3600, 60 * 2 ** min(row["attempts"], 6)),
                        row["id"],
                        token,
                    ),
                )
        else:
            with self.pool.connection() as conn:
                conn.execute(
                    "UPDATE task_followup_emails SET state=%s,provider_id=%s,"
                    "last_error=NULL,updated_at=now() WHERE id=%s AND claim_token=%s",
                    (
                        "sent" if self.mode == "resend" else "captured",
                        provider_id,
                        row["id"],
                        token,
                    ),
                )
        return True
