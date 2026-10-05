"""/api/v1/projects, their members, and live updates to the project list"""

import asyncio
import threading
from collections import defaultdict
from collections.abc import Iterable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from psycopg import Connection
from pydantic import BaseModel, Field

from ..db import projects
from .deps import User, get_conn, require_member

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])
Conn = Annotated[Connection, Depends(get_conn)]

# A comment line this often keeps the stream open through the Cloudflare
# tunnel, which closes connections idle for 100 seconds.
HEARTBEAT_SECONDS = 25


class ProjectEvents:
    """Tells each open app that its project list changed: someone joined, left,
    or was removed, or a project was deleted. The app then re-fetches
    GET /api/v1/projects, so member counts update live and events carry no data.

    Kept in memory because the server runs as one process. Running several
    workers would need a shared channel such as Postgres LISTEN/NOTIFY."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._queues: dict[UUID, set[asyncio.Queue]] = defaultdict(set)
        self._loop: asyncio.AbstractEventLoop | None = None

    def subscribe(self, user_id: UUID) -> asyncio.Queue:
        """Call from the event loop that serves the stream."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=1)
        with self._lock:
            self._loop = asyncio.get_running_loop()
            self._queues[user_id].add(queue)
        return queue

    def unsubscribe(self, user_id: UUID, queue: asyncio.Queue) -> None:
        with self._lock:
            self._queues[user_id].discard(queue)
            if not self._queues[user_id]:
                del self._queues[user_id]

    def publish(self, user_ids: Iterable[UUID]) -> None:
        """Safe from any thread, including the sync route handlers."""
        with self._lock:
            loop = self._loop
            queues = [q for uid in set(user_ids) for q in self._queues.get(uid, ())]
        if loop is None or not queues:
            return
        for queue in queues:
            try:
                loop.call_soon_threadsafe(_nudge, queue)
            except RuntimeError:  # the loop has shut down
                return


def _nudge(queue: asyncio.Queue) -> None:
    # One waiting nudge is enough, since the app re-fetches everything anyway.
    if queue.empty():
        queue.put_nowait(None)


def announce(request: Request, conn: Connection, user_ids: Iterable[UUID]) -> None:
    """Commit first, so an app that re-fetches on the nudge sees the change."""
    conn.commit()
    request.app.state.project_events.publish(user_ids)


class NewProject(BaseModel):
    name: Annotated[str, Field(max_length=255)]
    image_path: str | None = None


@router.get("/events")
async def project_events(request: Request, user: User) -> StreamingResponse:
    """Server-sent events for the signed-in user's project list.

    Sends `data: projects` once right away (anything that changed before the
    stream opened) and again after every membership change in the user's
    projects. Comment lines keep the connection alive. The stream ends after
    app.state.event_stream_seconds so the app reconnects with a fresh token."""
    events: ProjectEvents = request.app.state.project_events
    lifetime: float = request.app.state.event_stream_seconds

    async def stream():
        queue = events.subscribe(user.id)
        try:
            yield "data: projects\n\n"
            loop = asyncio.get_running_loop()
            deadline = loop.time() + lifetime
            while (remaining := deadline - loop.time()) > 0:
                try:
                    await asyncio.wait_for(
                        queue.get(), min(HEARTBEAT_SECONDS, remaining)
                    )
                    yield "data: projects\n\n"
                except TimeoutError:
                    yield ": ping\n\n"
        finally:
            events.unsubscribe(user.id, queue)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


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
def remove_member(
    project_id: UUID, member_id: UUID, user: User, conn: Conn, request: Request
) -> dict:
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
    # Everyone before the removal, so the removed member's app drops the project.
    recipients = projects.member_ids(conn, project_id)
    unassigned = projects.remove_member(conn, project_id, member_id)
    announce(request, conn, recipients)
    return {"removed": 1, "unassigned_tasks": unassigned}
