"""/api/v1/me: the signed-in user's own profile (spec Section 8.1)."""

from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..db import profiles
from .deps import Conn, User

router = APIRouter(prefix="/api/v1/me", tags=["me"])


class ProfileUpdate(BaseModel):
    """Fields left out keep their current value."""

    display_name: Annotated[str, Field(max_length=255)] | None = None
    title: Annotated[str, Field(max_length=255)] | None = None


def onboarding_step(profile: dict) -> str:
    """FR-ONB-1: where the app sends this user after sign in."""
    if not profile["display_name"]:
        return "needs_profile"
    if profile["onboarding_completed_at"] is None:
        return "needs_voice"
    return "complete"


def me_payload(conn, profile: dict) -> dict:
    return profile | {
        "onboarding_step": onboarding_step(profile),
        "pending_invitation_count": profiles.pending_invitation_count(
            conn, profile["email"]
        ),
    }


@router.get("")
def get_me(user: User, conn: Conn) -> dict:
    return me_payload(conn, user.profile)


@router.patch("")
def update_me(body: ProfileUpdate, user: User, conn: Conn) -> dict:
    fields = {}
    if body.display_name is not None:
        fields["display_name"] = body.display_name.strip()
        if not fields["display_name"]:
            raise HTTPException(400, "Display name must not be blank")
    if body.title is not None:
        # An empty title clears it.
        fields["title"] = body.title.strip() or None
    if not fields:
        return me_payload(conn, user.profile)
    return me_payload(conn, profiles.update_profile(conn, user.id, **fields))
