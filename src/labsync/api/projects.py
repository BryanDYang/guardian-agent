"""/api/v1/projects"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
from pydantic import BaseModel, Field

from ..db import projects
from .deps import get_conn

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])
Conn = Annotated[Connection, Depends(get_conn)]


class NewProject(BaseModel):
    name: Annotated[str, Field(max_length=255)]
    image_path: str | None = None


@router.get("")
def list_projects(conn: Conn) -> list[dict]:
    return projects.list_projects(conn)


@router.post("", status_code=201)
def create_project(body: NewProject, conn: Conn) -> dict:
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Project name must not be blank")
    return projects.create_project(conn, name, body.image_path)
