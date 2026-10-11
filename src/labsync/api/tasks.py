"""/api/v1/tasks: calendar list, human review, edits, lifecycle changes, and undo."""

from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field

from ..db import access, tasks
from .deps import User, get_conn, require_member, require_task

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])
Conn = Annotated[Connection, Depends(get_conn)]


Title = Annotated[str, Field(max_length=500)]
SpeakerLabel = Annotated[str, Field(max_length=64)]


class Review(BaseModel):
    """Fields left out keep their current value."""

    action: Literal["approve", "edit", "dismiss"]
    title: Title | None = None
    due_date: date | None = None
    assignee_user_id: UUID | None = None
    owner_label: SpeakerLabel | None = None


class TaskEdit(BaseModel):
    """Edits to an approved task. Fields left out keep their current value."""

    title: Title | None = None
    due_date: date | None = None
    assignee_user_id: UUID | None = None
    owner_label: SpeakerLabel | None = None


class Reconciliation(BaseModel):
    target_task_id: UUID
    action: Literal["duplicate", "deadline", "complete"]
    expected_updated_at: datetime
    due_date: date | None = None
    transcript_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)


class StateChange(BaseModel):
    state: Literal["open", "done", "dropped"]


def locked(conn: Connection, task_id: UUID) -> dict:
    task = tasks.lock_task(conn, task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    return task


def new_title(task: dict, title: str | None) -> str:
    title = task["title"] if title is None else title.strip()
    if not title:
        raise HTTPException(400, "Task title must not be blank")
    return title


def new_assignee(
    conn: Connection, task: dict, body: Review | TaskEdit
) -> tuple[UUID | None, str | None]:
    """(assignee_user_id, owner_label) after this request.

    A task belongs to a project member, to a speaker the diarizer found who
    isn't a member (SPEAKER_1), or to nobody. Sending either field replaces the
    assignment, so {"assignee_user_id": null, "owner_label": null} unassigns.
    Leaving both out keeps it."""
    if not {"assignee_user_id", "owner_label"} & body.model_fields_set:
        return task["assignee_user_id"], task["owner_label"]
    user_id = body.assignee_user_id
    label = (body.owner_label or "").strip() or None
    if user_id is not None and label is not None:
        raise HTTPException(400, "Assign the task to a member or a speaker, not both")
    if user_id is not None and not access.is_member(conn, user_id, task["project_id"]):
        raise HTTPException(400, "The assignee must be a member of this project")
    if label is not None and not tasks.is_speaker(conn, task["meeting_id"], label):
        raise HTTPException(400, "That speaker is not in this task's meeting")
    return user_id, label


@router.get("")
def list_tasks(
    project_id: UUID, start_date: date, end_date: date, user: User, conn: Conn
) -> list[dict]:
    if start_date > end_date:
        raise HTTPException(400, "start_date must not be after end_date")
    require_member(conn, user, project_id)
    return tasks.list_calendar_tasks(conn, project_id, start_date, end_date)


@router.get("/accepted")
def accepted_tasks(project_id: UUID, user: User, conn: Conn) -> list[dict]:
    require_member(conn, user, project_id)
    return tasks.list_accepted_tasks(conn, project_id)


@router.patch("/{task_id}/review")
def review_task(task_id: UUID, body: Review, user: User, conn: Conn) -> dict:
    require_task(conn, user, task_id)
    task = locked(conn, task_id)
    if task["review_status"] != "pending":
        raise HTTPException(409, f"Task was already {task['review_status']}")
    title = new_title(task, body.title)
    # JSON null clears a field. Leaving it out keeps the stored value.
    provided = body.model_fields_set
    due_date = body.due_date if "due_date" in provided else task["due_date"]
    assignee_user_id, owner_label = new_assignee(conn, task, body)
    status = {"approve": "approved", "edit": "pending", "dismiss": "dismissed"}
    task = tasks.update_review(
        conn,
        task_id,
        review_status=status[body.action],
        title=title,
        assignee_user_id=assignee_user_id,
        owner_label=owner_label,
        due_date=due_date,
        approved_by=user.id if body.action == "approve" else None,
    )
    if body.action != "approve" or due_date is None:
        return {"task": task}
    # The iOS app creates the reminder with EventKit from this payload.
    return {"task": task, "eventkit": {"title": title, "due_date": due_date}}


@router.patch("/{task_id}")
def edit_task(task_id: UUID, body: TaskEdit, user: User, conn: Conn) -> dict:
    """Change an approved task's title, due date, or assignee. Pending tasks
    are edited through /review; status changes go through /state."""
    require_task(conn, user, task_id)
    task = locked(conn, task_id)
    if task["review_status"] != "approved":
        raise HTTPException(409, "Only approved tasks can be edited here")
    assignee_user_id, owner_label = new_assignee(conn, task, body)
    task = tasks.update_details(
        conn,
        task_id,
        title=new_title(task, body.title),
        assignee_user_id=assignee_user_id,
        owner_label=owner_label,
        due_date=(
            body.due_date if "due_date" in body.model_fields_set else task["due_date"]
        ),
    )
    return {"task": task}


@router.post("/{task_id}/reconcile")
def reconcile(task_id: UUID, body: Reconciliation, user: User, conn: Conn) -> dict:
    """A reviewer confirms a later meeting's effect on one stable accepted task.

    Similarity only suggests a target; it never applies a mutation. A source
    quote is required, and stale reviews fail instead of replacing newer work.
    """
    require_task(conn, user, task_id)
    require_task(conn, user, body.target_task_id)
    rows = {id: locked(conn, id) for id in sorted({task_id, body.target_task_id})}
    source, target = rows[task_id], rows[body.target_task_id]
    if source["project_id"] != target["project_id"]:
        raise HTTPException(404, "Task not found")
    if source["review_status"] != "pending" or target["review_status"] != "approved":
        raise HTTPException(409, "Review a pending candidate against an accepted task")
    if source["meeting_id"] == target["meeting_id"] or target["meeting_id"] is None:
        raise HTTPException(400, "Choose a task from an earlier meeting")
    order = conn.execute(
        "SELECT id, meeting_date, created_at FROM meetings WHERE id = ANY(%s)",
        ([source["meeting_id"], target["meeting_id"]],),
    ).fetchall()
    dates = {r["id"]: (r["meeting_date"], r["created_at"]) for r in order}
    if dates[source["meeting_id"]] <= dates[target["meeting_id"]]:
        raise HTTPException(400, "The source meeting must follow the original meeting")
    if target["updated_at"] != body.expected_updated_at:
        raise HTTPException(409, "Task changed. Reload before confirming")
    evidence = conn.execute(
        "SELECT turn_key, content, start_time_ms FROM meeting_transcripts "
        "WHERE meeting_id = %s AND turn_key = %s",
        (source["meeting_id"], body.transcript_id),
    ).fetchone()
    if not evidence or body.quote not in evidence["content"]:
        raise HTTPException(400, "Evidence must quote this meeting exactly")
    if body.action == "deadline" and body.due_date is None:
        raise HTTPException(400, "Confirm the new deadline")
    if body.action != "duplicate" and target["lifecycle_status"] != "open":
        raise HTTPException(
            409, "A later meeting cannot reopen completed or dropped work"
        )
    old = {
        "due_date": str(target["due_date"]) if target["due_date"] else None,
        "lifecycle_status": target["lifecycle_status"],
    }
    due = body.due_date if body.action == "deadline" else target["due_date"]
    state = "done" if body.action == "complete" else target["lifecycle_status"]
    conn.execute(
        "UPDATE tasks SET due_date = %s, lifecycle_status = %s, updated_at = now() "
        "WHERE id = %s",
        (due, state, target["id"]),
    )
    conn.execute(
        "UPDATE tasks SET review_status = 'dismissed', updated_at = now() WHERE id = "
        "%s",
        (task_id,),
    )
    conn.execute(
        "INSERT INTO task_audit_log (task_id, action, old_value, new_value, actor_id) "
        "VALUES (%s, 'MEETING_RECONCILIATION', %s, %s, %s)",
        (
            target["id"],
            Jsonb(old),
            Jsonb(
                {
                    "due_date": str(due) if due else None,
                    "lifecycle_status": state,
                    "operation": body.action,
                    "source_task_id": str(task_id),
                    "meeting_id": str(source["meeting_id"]),
                    "transcript_id": body.transcript_id,
                    "quote": body.quote,
                    "timestamp_ms": evidence["start_time_ms"],
                    "policy": "human-confirmed-v1",
                }
            ),
            user.id,
        ),
    )
    return {"task": locked(conn, target["id"])}


@router.post("/{task_id}/state")
def change_state(task_id: UUID, body: StateChange, user: User, conn: Conn) -> dict:
    require_task(conn, user, task_id)
    task = locked(conn, task_id)
    if task["review_status"] != "approved":
        raise HTTPException(409, "Only approved tasks can change state")
    if task["lifecycle_status"] == body.state:
        raise HTTPException(409, f"Task is already {body.state}")
    task, token = tasks.set_lifecycle(
        conn, task_id, task["lifecycle_status"], body.state, "STATUS_CHANGE", user.id
    )
    return {"task": task, "revert_token": token}


@router.post("/revert/{revert_token}")
def revert(revert_token: UUID, user: User, conn: Conn) -> dict:
    audit = tasks.find_audit(conn, revert_token)
    # A token for another project's task looks exactly like an unknown one.
    if audit is None or not access.can_see_task(conn, user.id, audit["task_id"]):
        raise HTTPException(404, "Unknown revert token")
    if audit["action"] == "MEETING_RECONCILIATION":
        raise HTTPException(409, "Edit the task to correct a meeting reconciliation")
    task = locked(conn, audit["task_id"])
    if tasks.latest_audit_id(conn, task["id"]) != audit["id"]:
        raise HTTPException(409, "Only the most recent change can be undone")
    task, token = tasks.set_lifecycle(
        conn,
        task["id"],
        task["lifecycle_status"],
        audit["old_value"]["lifecycle_status"],
        "REVERT",
        user.id,
    )
    return {"task": task, "revert_token": token}
