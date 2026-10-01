"""/api/v1 meeting reads. The upload route lives in server.py (see phase 2)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection

from ..db import meetings
from .deps import get_conn

router = APIRouter(prefix="/api/v1", tags=["meetings"])
Conn = Annotated[Connection, Depends(get_conn)]


@router.get("/projects/{project_id}/meetings")
def list_meetings(
    project_id: UUID,
    conn: Conn,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[dict]:
    if not meetings.project_exists(conn, project_id):
        raise HTTPException(404, "Project not found")
    return meetings.list_meetings(conn, project_id, limit, offset)


@router.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: UUID, conn: Conn) -> dict:
    detail = meetings.get_meeting_detail(conn, meeting_id)
    if detail is None:
        raise HTTPException(404, "Meeting not found")
    # Audio is still served by the existing local route.
    return detail | {"audio_url": f"/api/meetings/{meeting_id}/audio"}
