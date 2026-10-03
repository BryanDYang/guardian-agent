"""/api/v1/tasks: calendar list, human review, edits, lifecycle changes, and undo."""

from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
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
    if body.action == "approve" and due_date is None:
        raise HTTPException(422, "Add a due date before approving this task")
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
    if body.action != "approve":
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
    if "due_date" in body.model_fields_set and body.due_date is None:
        raise HTTPException(422, "An approved task needs a due date")
    assignee_user_id, owner_label = new_assignee(conn, task, body)
    task = tasks.update_details(
        conn,
        task_id,
        title=new_title(task, body.title),
        assignee_user_id=assignee_user_id,
        owner_label=owner_label,
        due_date=body.due_date or task["due_date"],
    )
    return {"task": task}


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
