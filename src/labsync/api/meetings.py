"""/api/v1 meeting reads. The upload route lives in server.py (see phase 2)."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection
from pydantic import BaseModel, Field

from ..db import meetings
from .deps import User, get_conn, require_meeting, require_member

router = APIRouter(prefix="/api/v1", tags=["meetings"])
Conn = Annotated[Connection, Depends(get_conn)]


@router.get("/projects/{project_id}/meetings")
def list_meetings(
    project_id: UUID,
    user: User,
    conn: Conn,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[dict]:
    require_member(conn, user, project_id)
    return meetings.list_meetings(conn, project_id, limit, offset)


@router.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: UUID, user: User, conn: Conn) -> dict:
    require_meeting(conn, user, meeting_id)
    detail = meetings.get_meeting_detail(conn, meeting_id)
    if detail is None:
        raise HTTPException(404, "Meeting not found")
    # Audio is still served by the existing local route.
    return detail | {"audio_url": f"/api/meetings/{meeting_id}/audio"}


@router.get("/meetings/{meeting_id}/speakers")
def speakers(meeting_id: UUID, user: User, conn: Conn) -> list[dict]:
    from ..speaker_names import suggestions

    require_meeting(conn, user, meeting_id)
    turns = conn.execute(
        "SELECT speaker_label, speaker_name, turn_key, start_time_ms, content "
        "FROM meeting_transcripts WHERE meeting_id=%s ORDER BY turn_order",
        (meeting_id,),
    ).fetchall()
    proposed = suggestions(turns)
    metadata = (
        conn.execute(
            "SELECT model_metadata FROM meetings WHERE id=%s", (meeting_id,)
        ).fetchone()["model_metadata"]
        or {}
    )
    confirmed = metadata.get("speaker_name_reviews", {})
    identified = metadata.get("speaker_identification", {}).get("speakers", {})
    result = {}
    for turn in turns:
        label = turn["speaker_label"]
        if label.upper() == "UNKNOWN":
            continue
        result.setdefault(
            label,
            {
                "label": label,
                "display": turn["speaker_name"] or label,
                "suggestions": proposed.get(label, []),
                "confirmed": label in confirmed
                or bool(identified.get(label, {}).get("user_id")),
                "assignee_user_id": confirmed.get(label, {}).get("assignee_user_id")
                or identified.get(label, {}).get("user_id"),
            },
        )
    return list(result.values())


class SpeakerReview(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=64)]
    assignee_user_id: UUID | None = None


@router.put("/meetings/{meeting_id}/speakers/{label}")
def confirm_speaker(
    meeting_id: UUID, label: str, body: SpeakerReview, user: User, conn: Conn
) -> dict:
    from psycopg.types.json import Jsonb

    require_meeting(conn, user, meeting_id)
    meeting = conn.execute(
        "SELECT project_id,status,model_metadata,processing_attempt FROM meetings "
        "WHERE id=%s FOR UPDATE",
        (meeting_id,),
    ).fetchone()
    if meeting["status"] != "completed":
        raise HTTPException(
            409, "Wait for processing to complete before naming speakers"
        )
    name = body.name.strip()
    if not name or name.upper() == "UNKNOWN" or name.upper().startswith("SPEAKER_"):
        raise HTTPException(400, "Enter a participant name")
    turns = conn.execute(
        "SELECT speaker_name,speaker_label,content,turn_key,start_time_ms "
        "FROM meeting_transcripts WHERE meeting_id=%s "
        "AND speaker_label=%s",
        (meeting_id, label),
    ).fetchall()
    if not turns or label.upper() == "UNKNOWN":
        raise HTTPException(404, "Speaker not found")
    if conn.execute(
        "SELECT 1 FROM meeting_transcripts WHERE meeting_id=%s AND speaker_label<>%s "
        "AND lower(speaker_name)=lower(%s)",
        (meeting_id, label, name),
    ).fetchone():
        raise HTTPException(
            409,
            "That name is used by another speaker. Review the speaker split first.",
        )
    if body.assignee_user_id:
        if not conn.execute(
            "SELECT 1 FROM project_members WHERE project_id=%s AND user_id=%s",
            (meeting["project_id"], body.assignee_user_id),
        ).fetchone():
            raise HTTPException(400, "Choose a member of this project")
    previous = {t["speaker_name"] or label for t in turns}
    conn.execute(
        "UPDATE meeting_transcripts SET speaker_name=%s "
        "WHERE meeting_id=%s AND speaker_label=%s",
        (name, meeting_id, label),
    )
    # Reviewed tasks retain their explicit assignment. Pending commitments follow
    # the participant mapping, without approving the task or inventing a deadline.
    for old in previous:
        conn.execute(
            "UPDATE tasks SET owner_label=%s,assignee_user_id=%s,updated_at=now() "
            "WHERE meeting_id=%s AND owner_label=%s AND review_status='pending' "
            "AND assignee_user_id IS NULL",
            (name, body.assignee_user_id, meeting_id, old),
        )
    metadata = meeting["model_metadata"] or {}
    from ..speaker_names import suggestions

    review = {
        "name": name,
        "method": "human_confirmation",
        "processing_attempt": meeting["processing_attempt"],
        "introductions": suggestions(turns).get(label, []),
        "assignee_user_id": str(body.assignee_user_id)
        if body.assignee_user_id
        else None,
        "confirmed_by": str(user.id),
        "confirmed_at": datetime.now(timezone.utc).isoformat(),
    }
    metadata.setdefault("speaker_name_reviews", {})[label] = review
    metadata.setdefault("speaker_name_review_history", []).append(
        {"label": label, **review}
    )
    conn.execute(
        "UPDATE meetings SET model_metadata=%s,updated_at=now() WHERE id=%s",
        (Jsonb(metadata), meeting_id),
    )
    # Keep shared polling snapshots consistent with the stored transcript.
    job = conn.execute(
        "SELECT record FROM meeting_jobs WHERE meeting_id=%s FOR UPDATE", (meeting_id,)
    ).fetchone()
    if job:
        record = job["record"]
        for turn in record.get("transcript", {}).get("turns", []):
            if turn.get("speaker") in previous:
                turn["speaker"] = name
        for task in record.get("extraction", {}).get("commitments", []):
            if task.get("owner") in previous:
                task["owner"] = name
        conn.execute(
            "UPDATE meeting_jobs SET record=%s,updated_at=now() WHERE meeting_id=%s",
            (Jsonb(record), meeting_id),
        )
    return {"label": label, **review}
