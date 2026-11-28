"""Conservative, quoted deadline revisions. No model or similarity-only writes."""

import re

from psycopg.types.json import Jsonb

from .deadlines import explicit_deadline

POLICY = "explicit-deadline-revision-v1"


def work_words(text):
    # Only regular noun plurals are normalized; do not conflate different verbs.
    stop = {
        "a",
        "an",
        "the",
        "all",
        "demo",
        "this",
        "that",
        "my",
        "our",
        "by",
        "to",
        "and",
        "have",
        "will",
        "i",
        "at",
        "tonight",
        "tomorrow",
    }
    return {
        w[:-1] if w.endswith("s") and not w.endswith("ss") else w
        for w in re.findall(r"[a-z]+", text.lower())
        if w not in stop
    }


def revision_dates(quote, due_text, day):
    quote = quote.replace("’", "'")
    # An explicit old-date reference is essential. Similar titles alone cannot
    # establish that a new commitment supersedes an existing one.
    match = re.search(
        r"\bI (?:originally|previously) said (.+?),? but "
        r"that(?:'s| is) too (?:late|early)(?: now)?[.!]\s+"
        r"(I(?:'ll| will) .+)",
        quote,
        re.I,
    )
    if not match or re.search(
        r"\b(if|maybe|might|could|unless|not|never|instead|someone|different|separate|"
        r"another|don't|won't|can't|cancel|nevermind)\b|\?",
        quote,
        re.I,
    ):
        return None
    if re.search(r"\b(but|actually|rather|or|correction)\b", match[2], re.I):
        return None
    old = explicit_deadline(match[1].rstrip(", "), day)
    new = explicit_deadline(due_text, day)
    promise = match[2]
    if (
        not old
        or not new
        or old == new
        or new < (day.date() if hasattr(day, "date") else day)
    ):
        return None
    if not due_text or due_text not in promise:
        return None
    return old, new, promise


def revision_context(content, quote):
    """Expand a short extracted promise only across its adjacent old-date clause."""
    if quote not in content:
        return quote
    prefix = re.search(
        r"\bI (?:originally|previously) said [^.!?]+?,? but "
        r"that(?:['’]s| is) too (?:late|early)(?: now)?[.!]\s+$",
        content[: content.index(quote)],
        re.I,
    )
    if prefix and re.match(r"I(?:['’]ll| will)\b", quote, re.I):
        return content[prefix.start() : content.index(quote) + len(quote)]
    return quote


def apply_revision(conn, task, meeting, labels):
    """Return True only after atomically updating one unambiguous accepted task.

    Called under the project's automation lock and source-task row lock. A busy
    target stays pending, avoiding inverted locks against manual reconciliation.
    """
    if task["archived_at"] or task["deleted_at"]:
        return False
    evidence = conn.execute(
        "SELECT e.quote,e.turn_key,t.content,t.speaker_label,t.start_time_ms "
        "FROM item_evidence e JOIN meeting_transcripts t "
        "ON t.meeting_id=%s AND t.turn_key=e.turn_key WHERE e.task_id=%s",
        (meeting["id"], task["id"]),
    ).fetchall()
    if len(evidence) != 1:
        return False
    e = evidence[0]
    if e["speaker_label"] not in labels or e["quote"] not in e["content"]:
        return False
    context = revision_context(e["content"], e["quote"])
    dates = revision_dates(context, task["due_date_text"], meeting["meeting_date"])
    if not dates or task["due_date"] != dates[1]:
        return False
    old, new, promise = dates
    candidates = conn.execute(
        "SELECT t.* "
        "FROM tasks t JOIN meetings m ON m.id=t.meeting_id "
        "WHERE t.project_id=%s AND t.assignee_user_id=%s AND t.id<>%s "
        "AND t.review_status='approved' AND t.lifecycle_status='open' "
        "AND t.category='commitment' "
        "AND t.archived_at IS NULL AND t.deleted_at IS NULL "
        "AND m.archived_at IS NULL AND m.deleted_at IS NULL "
        "AND t.due_date=%s AND m.meeting_date<%s",
        (
            task["project_id"],
            task["assignee_user_id"],
            task["id"],
            old,
            meeting["meeting_date"],
        ),
    ).fetchall()
    words = work_words(promise)
    matches = []
    for target in candidates:
        title = work_words(target["title"])
        verb = target["title"].lower().split()[0]
        shared = title & words
        if verb in words and len(shared) >= 2 and title <= words:
            matches.append(target)
    if len(matches) != 1:
        return False
    target = matches[0]
    locked = conn.execute(
        "SELECT id FROM tasks WHERE id=%s FOR UPDATE SKIP LOCKED", (target["id"],)
    ).fetchone()
    if not locked:
        return False
    # Re-read after acquiring the lock. Never replace a concurrent edit.
    current = conn.execute(
        "SELECT * FROM tasks WHERE id=%s", (target["id"],)
    ).fetchone()
    if current["updated_at"] != target["updated_at"]:
        return False
    source_created = conn.execute(
        "SELECT created_at FROM tasks WHERE id=%s", (task["id"],)
    ).fetchone()["created_at"]
    if conn.execute(
        "SELECT 1 FROM task_audit_log WHERE task_id=%s AND created_at>%s "
        "AND action IN ('DETAILS_EDIT','RETURN_FOR_REVIEW',"
        "'MEETING_RECONCILIATION','AUTO_DEADLINE') LIMIT 1",
        (target["id"], source_created),
    ).fetchone():
        return False
    conn.execute(
        "UPDATE tasks SET due_date=%s,updated_at=now() WHERE id=%s", (new, target["id"])
    )
    conn.execute(
        "UPDATE tasks SET review_status='dismissed',updated_at=now() WHERE id=%s",
        (task["id"],),
    )
    note = (
        f"Deadline automatically changed from {old} to {new} after "
        f"{meeting['name']}. Evidence: {context}"
    )
    audit = conn.execute(
        "INSERT INTO task_audit_log(task_id,action,old_value,new_value) "
        "VALUES (%s,'AUTO_DEADLINE',%s,%s) RETURNING id",
        (
            target["id"],
            Jsonb({"due_date": str(old)}),
            Jsonb(
                {
                    "due_date": str(new),
                    "note": note,
                    "policy": POLICY,
                    "source_task_id": str(task["id"]),
                    "meeting_id": str(meeting["id"]),
                    "transcript_id": e["turn_key"],
                    "quote": context,
                    "extracted_quote": e["quote"],
                    "timestamp_ms": e["start_time_ms"],
                }
            ),
        ),
    ).fetchone()
    from .followup import enqueue

    enqueue(conn, target, change_id=audit["id"])
    return True
