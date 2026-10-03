"""Project invitations (spec Sections 5.4 and 8.3). Any member can invite or
revoke; roles are stored but not enforced yet."""

import re
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..db import invitations, projects
from .deps import Conn, CurrentUser, User, require_member
from .projects import announce

router = APIRouter(tags=["invitations"])

# The app opens this link (FR-INV-5). The token is URL-safe base64.
INVITE_URL = "meetingmemory://invite?token={token}"
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


class NewInvitation(BaseModel):
    email: Annotated[str, Field(max_length=320)]


class InviteToken(BaseModel):
    token: Annotated[str, Field(max_length=200)]


@router.post("/api/v1/projects/{project_id}/invitations", status_code=201)
def create_invitation(
    project_id: UUID, body: NewInvitation, user: User, conn: Conn
) -> dict:
    require_member(conn, user, project_id)
    email = body.email.strip().lower()
    if not EMAIL.fullmatch(email):
        raise HTTPException(400, "Enter a valid email address")
    if invitations.is_member(conn, project_id, email):
        raise HTTPException(409, "already_member")
    invitation, token = invitations.create(conn, project_id, email, user.id)
    return {"invitation": invitation, "invite_url": INVITE_URL.format(token=token)}


@router.get("/api/v1/projects/{project_id}/invitations")
def list_project_invitations(project_id: UUID, user: User, conn: Conn) -> list[dict]:
    require_member(conn, user, project_id)
    return invitations.list_for_project(conn, project_id)


@router.delete("/api/v1/projects/{project_id}/invitations/{invitation_id}")
def revoke_invitation(
    project_id: UUID, invitation_id: UUID, user: User, conn: Conn
) -> dict:
    require_member(conn, user, project_id)
    invitation = invitations.get(conn, invitation_id)
    if invitation is None or invitation["project_id"] != project_id:
        raise HTTPException(404, "Invitation not found")
    if not invitations.resolve(conn, invitation_id, "revoked"):
        raise HTTPException(409, "Invitation is no longer pending")
    return {"revoked": 1}


@router.get("/api/v1/invitations")
def my_invitations(user: User, conn: Conn) -> list[dict]:
    """FR-INV-8: invitations for my email show up even without the link."""
    return invitations.list_for_email(conn, user.email)


def mine(conn, user: CurrentUser, invitation_id: UUID) -> dict:
    """Someone else's invitation looks the same as one that doesn't exist."""
    invitation = invitations.get(conn, invitation_id)
    if invitation is None or invitation["email"] != user.email:
        raise HTTPException(404, "Invitation not found")
    return invitation


def accept(request: Request, conn, user: CurrentUser, invitation: dict) -> dict:
    """FR-INV-6: the checks, each with its own reason the app can show.
    On success every member's app hears about it, so member counts update."""
    if invitations.is_member(conn, invitation["project_id"], user.email):
        raise HTTPException(409, "already_member")
    if invitation["status"] == "revoked":
        raise HTTPException(410, "revoked")
    if invitation["status"] != "pending":
        raise HTTPException(410, "already_used")
    if invitation["expires_at"] <= datetime.now(timezone.utc):
        raise HTTPException(410, "expired")
    if not invitations.accept(conn, invitation, user.id):
        raise HTTPException(410, "already_used")
    announce(request, conn, projects.member_ids(conn, invitation["project_id"]))
    return {
        "project_id": invitation["project_id"],
        "project_name": invitation["project_name"],
    }


@router.post("/api/v1/invitations/accept-token")
def accept_by_token(
    body: InviteToken, user: User, conn: Conn, request: Request
) -> dict:
    """From the invite link. Whoever holds the link learns it was for another
    email, which is fine: they already have the link."""
    invitation = invitations.find_by_token(conn, body.token)
    if invitation is None:
        raise HTTPException(404, "Invitation not found")
    if invitation["email"] != user.email:
        raise HTTPException(403, "email_mismatch")
    return accept(request, conn, user, invitation)


@router.post("/api/v1/invitations/{invitation_id}/accept")
def accept_by_id(invitation_id: UUID, user: User, conn: Conn, request: Request) -> dict:
    return accept(request, conn, user, mine(conn, user, invitation_id))


@router.post("/api/v1/invitations/{invitation_id}/decline")
def decline(invitation_id: UUID, user: User, conn: Conn) -> dict:
    mine(conn, user, invitation_id)
    if not invitations.resolve(conn, invitation_id, "declined"):
        raise HTTPException(409, "Invitation is no longer pending")
    return {"declined": 1}
