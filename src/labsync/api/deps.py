"""FastAPI dependencies shared by the /api/v1 routers."""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from psycopg import Connection

from ..auth import InvalidToken
from ..db import access, profiles


def get_conn(request: Request) -> Iterator[Connection]:
    pool = request.app.state.pool
    if pool is None:
        raise HTTPException(503, "Database is not configured; set DATABASE_URL")
    with pool.connection() as conn:
        yield conn


Conn = Annotated[Connection, Depends(get_conn)]


@dataclass(frozen=True)
class CurrentUser:
    id: UUID
    email: str
    profile: dict


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(401, detail, headers={"WWW-Authenticate": "Bearer"})


def current_user(request: Request) -> CurrentUser:
    """The signed-in user, from a Supabase access token (FR-AUTH-5).

    Borrows a database connection only for the profile lookup, so routes that
    give their connection back during slow work (chat answers) stay cheap."""
    pool, verifier = request.app.state.pool, request.app.state.auth
    if pool is None:
        raise HTTPException(503, "Database is not configured; set DATABASE_URL")
    if verifier is None:
        raise HTTPException(503, "Authentication is not configured; set SUPABASE_URL")
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise unauthorized("Sign in to continue")
    try:
        claims = verifier.verify(token)
        user_id = UUID(claims["sub"])
    except (InvalidToken, ValueError) as exc:
        raise unauthorized(
            "Your session is invalid or expired. Sign in again."
        ) from exc
    with pool.connection() as conn:
        profile = profiles.get_profile(conn, user_id)
    if profile is None:
        # The auth.users trigger creates every profile, so this means the account
        # was deleted while the token was still valid.
        raise unauthorized("profile_missing")
    return CurrentUser(id=user_id, email=profile["email"], profile=profile)


# For /me routes, which a user needs while still onboarding.
SignedIn = Annotated[CurrentUser, Depends(current_user)]


def onboarded_user(user: SignedIn) -> CurrentUser:
    """FR-ONB-3: project data waits until onboarding is complete."""
    if user.profile["onboarding_completed_at"] is None:
        raise HTTPException(403, "onboarding_incomplete")
    return user


User = Annotated[CurrentUser, Depends(onboarded_user)]


def require_member(conn: Connection, user: CurrentUser, project_id: UUID) -> None:
    """404 rather than 403, so non-members can't tell the project exists."""
    if not access.is_member(conn, user.id, project_id):
        raise HTTPException(404, "Project not found")


def require_meeting(conn: Connection, user: CurrentUser, meeting_id: UUID) -> None:
    if not access.can_see_meeting(conn, user.id, meeting_id):
        raise HTTPException(404, "Meeting not found")


def require_task(conn: Connection, user: CurrentUser, task_id: UUID) -> None:
    if not access.can_see_task(conn, user.id, task_id):
        raise HTTPException(404, "Task not found")
