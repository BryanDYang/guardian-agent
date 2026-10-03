"""/api/v1/projects and their members"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
from pydantic import BaseModel, Field

from ..db import projects
from .deps import User, get_conn, require_member

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])
Conn = Annotated[Connection, Depends(get_conn)]


class NewProject(BaseModel):
    name: Annotated[str, Field(max_length=255)]
    image_path: str | None = None


@router.get("")
def list_projects(user: User, conn: Conn) -> list[dict]:
    return projects.list_projects(conn, user.id)


@router.post("", status_code=201)
def create_project(body: NewProject, user: User, conn: Conn) -> dict:
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Project name must not be blank")
    return projects.create_project(conn, name, body.image_path, user.id)


@router.get("/{project_id}/members")
def list_members(project_id: UUID, user: User, conn: Conn) -> list[dict]:
    """Everyone who can be assigned a task in this project. is_me marks the
    caller, so the app can show "(Me)" next to their name."""
    require_member(conn, user, project_id)
    return [
        member | {"is_me": member["user_id"] == user.id}
        for member in projects.list_members(conn, project_id)
    ]


@router.delete("/{project_id}/members/{member_id}")
def remove_member(project_id: UUID, member_id: UUID, user: User, conn: Conn) -> dict:
    """Owners remove anyone; members can only remove themselves (leave).
    The removed member's tasks in this project become unassigned."""
    require_member(conn, user, project_id)
    owners = projects.lock_owners(conn, project_id)
    if member_id != user.id and user.id not in owners:
        raise HTTPException(403, "Only project owners can remove members")
    if projects.member_role(conn, project_id, member_id) is None:
        raise HTTPException(404, "Member not found")
    if owners == [member_id]:
        raise HTTPException(
            409, "Make another member an owner before the last owner leaves"
        )
    unassigned = projects.remove_member(conn, project_id, member_id)
    return {"removed": 1, "unassigned_tasks": unassigned}
