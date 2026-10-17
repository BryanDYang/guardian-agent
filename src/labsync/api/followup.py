"""Project email controls, recipient preferences, and delivery history."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import followup
from ..db import projects
from .deps import Conn, User, require_member

router = APIRouter(prefix="/api/v1/projects", tags=["follow-through"])


class Settings(BaseModel):
    email_enabled: bool
    auto_approve: bool


class Preference(BaseModel):
    receive_email: bool


def settings(conn, project_id, user_id):
    row = conn.execute(
        "SELECT p.followup_email_enabled AS email_enabled,"
        "p.auto_approve_tasks AS auto_approve,"
        "pm.followup_email_enabled AS receive_email,"
        "pm.role='owner' AS can_manage FROM projects p JOIN project_members pm "
        "ON pm.project_id=p.id WHERE p.id=%s AND pm.user_id=%s",
        (project_id, user_id),
    ).fetchone()
    return row | {"delivery_mode": followup.delivery_mode()}


@router.get("/{project_id}/followup")
def get_settings(project_id: UUID, user: User, conn: Conn):
    require_member(conn, user, project_id)
    return settings(conn, project_id, user.id)


@router.put("/{project_id}/followup")
def update_settings(project_id: UUID, body: Settings, user: User, conn: Conn):
    require_member(conn, user, project_id)
    if projects.member_role(conn, project_id, user.id) != "owner":
        raise HTTPException(
            403, "Only project owners can change automatic follow-through"
        )
    conn.execute(
        "UPDATE projects SET followup_email_enabled=%s,auto_approve_tasks=%s "
        "WHERE id=%s",
        (body.email_enabled, body.auto_approve, project_id),
    )
    # Turning on automation also evaluates existing candidates. No model calls.
    for row in conn.execute(
        "SELECT id FROM meetings WHERE project_id=%s AND status='completed' "
        "ORDER BY meeting_date,created_at",
        (project_id,),
    ).fetchall():
        followup.auto_approve(conn, row["id"])
    # Existing accepted work isn't bulk-emailed just by enabling this setting.
    return settings(conn, project_id, user.id)


@router.put("/{project_id}/followup/me")
def preference(project_id: UUID, body: Preference, user: User, conn: Conn):
    require_member(conn, user, project_id)
    conn.execute(
        "UPDATE project_members SET followup_email_enabled=%s "
        "WHERE project_id=%s AND user_id=%s",
        (body.receive_email, project_id, user.id),
    )
    return settings(conn, project_id, user.id)


@router.get("/{project_id}/followup/emails")
def emails(project_id: UUID, user: User, conn: Conn):
    require_member(conn, user, project_id)
    owner = projects.member_role(conn, project_id, user.id) == "owner"
    # Members see only their own messages; owners see the project delivery log.
    return conn.execute(
        "SELECT e.id,t.title,e.state,e.mode,e.attempts,e.provider_id,e.last_error,"
        "e.created_at,e.updated_at,pr.display_name AS recipient_name,"
        "CASE WHEN e.mode='capture' THEN e.payload->>'text' END AS preview "
        "FROM task_followup_emails e JOIN tasks t ON t.id=e.task_id "
        "JOIN profiles pr ON pr.id=e.recipient_id WHERE t.project_id=%s "
        "AND (%s OR e.recipient_id=%s) ORDER BY e.created_at DESC LIMIT 100",
        (project_id, owner, user.id),
    ).fetchall()
