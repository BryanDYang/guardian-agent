"""/api/v1/tasks: calendar list, human review, lifecycle changes, and undo."""

from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation
from pydantic import BaseModel, Field

from ..db import meetings, tasks
from .deps import get_conn

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])
Conn = Annotated[Connection, Depends(get_conn)]


class Review(BaseModel):
    """Fields left out keep their current value."""

    action: Literal["approve", "edit", "dismiss"]
    title: Annotated[str, Field(max_length=500)] | None = None
    due_date: date | None = None
    assignee_id: UUID | None = None


class StateChange(BaseModel):
    state: Literal["open", "done", "dropped"]


def locked(conn: Connection, task_id: UUID) -> dict:
    task = tasks.lock_task(conn, task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    return task


@router.get("")
def list_tasks(
    project_id: UUID, start_date: date, end_date: date, conn: Conn
) -> list[dict]:
    if start_date > end_date:
        raise HTTPException(400, "start_date must not be after end_date")
    if not meetings.project_exists(conn, project_id):
        raise HTTPException(404, "Project not found")
    return tasks.list_calendar_tasks(conn, project_id, start_date, end_date)


@router.patch("/{task_id}/review")
def review_task(task_id: UUID, body: Review, conn: Conn) -> dict:
    task = locked(conn, task_id)
    if task["review_status"] != "pending":
        raise HTTPException(409, f"Task was already {task['review_status']}")
    title = task["title"] if body.title is None else body.title.strip()
    if not title:
        raise HTTPException(400, "Task title must not be blank")
    # JSON null clears a field. Leaving it out keeps the stored value.
    provided = body.model_fields_set
    due_date = body.due_date if "due_date" in provided else task["due_date"]
    attendee_id = body.assignee_id if "assignee_id" in provided else task["attendee_id"]
    if body.action == "approve" and due_date is None:
        raise HTTPException(422, "Add a due date before approving this task")
    status = {"approve": "approved", "edit": "pending", "dismiss": "dismissed"}
    try:
        task = tasks.update_review(
            conn,
            task_id,
            review_status=status[body.action],
            title=title,
            attendee_id=attendee_id,
            due_date=due_date,
        )
    except ForeignKeyViolation as exc:
        raise HTTPException(400, "Unknown assignee_id") from exc
    if body.action != "approve":
        return {"task": task}
    # The iOS app creates the reminder with EventKit from this payload.
    return {"task": task, "eventkit": {"title": title, "due_date": due_date}}


@router.post("/{task_id}/state")
def change_state(task_id: UUID, body: StateChange, conn: Conn) -> dict:
    task = locked(conn, task_id)
    if task["review_status"] != "approved":
        raise HTTPException(409, "Only approved tasks can change state")
    if task["lifecycle_status"] == body.state:
        raise HTTPException(409, f"Task is already {body.state}")
    task, token = tasks.set_lifecycle(
        conn, task_id, task["lifecycle_status"], body.state, "STATUS_CHANGE"
    )
    return {"task": task, "revert_token": token}


@router.post("/revert/{revert_token}")
def revert(revert_token: UUID, conn: Conn) -> dict:
    audit = tasks.find_audit(conn, revert_token)
    if audit is None:
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
    )
    return {"task": task, "revert_token": token}