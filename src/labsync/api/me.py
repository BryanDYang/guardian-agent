"""/api/v1/me: the signed-in user's own profile (spec Section 8.1)."""

import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .. import voice
from ..db import profiles
from .deps import Conn, SignedIn

router = APIRouter(prefix="/api/v1/me", tags=["me"])
log = logging.getLogger(__name__)


# An enrollment clip is about 20 seconds of AAC; this leaves plenty of room.
MAX_CLIP_BYTES = 10 * 1024 * 1024


class OnboardingDone(BaseModel):
    # A successful voice enrollment completes onboarding by itself.
    voice_step: Literal["skipped"]


class VoiceConsent(BaseModel):
    """The version of the consent text the user agreed to (FR-VOICE-1)."""

    consent_version: Annotated[str, Field(min_length=1, max_length=32)]


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
        "voice_enrolled_at": profiles.voice_status(conn, profile["id"])["enrolled_at"],
    }


def voice_payload(conn, user_id) -> dict:
    status = profiles.voice_status(conn, user_id)
    return {
        "consented": status["consented"],
        "enrolled": status["enrolled_at"] is not None,
        "enrolled_at": status["enrolled_at"],
        "embedding_model_id": status["embedding_model_id"],
        # FR-SPK-8: a voiceprint from another model can't be matched.
        "needs_rerecord": status["embedding_model_id"]
        not in (None, voice.EMBEDDING_MODEL_ID),
    }


@router.get("")
def get_me(user: SignedIn, conn: Conn) -> dict:
    return me_payload(conn, user.profile)


@router.patch("")
def update_me(body: ProfileUpdate, user: SignedIn, conn: Conn) -> dict:
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


@router.post("/onboarding/complete")
def complete_onboarding(body: OnboardingDone, user: SignedIn, conn: Conn) -> dict:
    """FR-ONB-2: only the backend marks onboarding complete, and only once."""
    profile = user.profile
    if not profile["display_name"]:
        raise HTTPException(409, "needs_profile")
    if profile["onboarding_completed_at"] is None:
        profile = profiles.update_profile(
            conn, user.id, onboarding_completed_at=datetime.now(timezone.utc)
        )
    return me_payload(conn, profile)


@router.get("/voice")
def get_voice(user: SignedIn, conn: Conn) -> dict:
    return voice_payload(conn, user.id)


@router.post("/voice-consent")
def grant_voice_consent(body: VoiceConsent, user: SignedIn, conn: Conn) -> dict:
    profiles.grant_voice_consent(conn, user.id, body.consent_version)
    return voice_payload(conn, user.id)


@router.delete("/voice-consent")
def revoke_voice_consent(user: SignedIn, conn: Conn) -> dict:
    """Deletes the voiceprint now. The account and onboarding are untouched."""
    profiles.revoke_voice_consent(conn, user.id)
    return voice_payload(conn, user.id)


@router.post("/voice-enrollments")
def enroll_voice(
    clip_a: UploadFile,
    clip_b: UploadFile,
    clip_c: UploadFile,
    user: SignedIn,
    conn: Conn,
) -> dict:
    """Three clips in, a voiceprint out (FR-VOICE-2 to FR-VOICE-6).

    Runs while the request waits (a few seconds), not behind meeting jobs.
    A clip that fails a quality check comes back as 422 with
    {"detail": "voice_quality", "failures": [{"clip": "A", "reason": ...}]}.
    The recordings are deleted before this returns, whatever the outcome."""
    if not profiles.voice_status(conn, user.id)["consented"]:
        raise HTTPException(403, "voice_consent_required")
    with TemporaryDirectory(prefix="labsync-voice-") as folder:
        paths = {}
        for name, upload in zip(voice.CLIPS, (clip_a, clip_b, clip_c), strict=True):
            path = Path(folder) / f"clip-{name}{Path(upload.filename or '').suffix}"
            with path.open("wb") as destination:
                shutil.copyfileobj(upload.file, destination)
            if path.stat().st_size > MAX_CLIP_BYTES:
                raise HTTPException(413, "Each clip must be under 10 MB")
            paths[name] = path
        try:
            result = voice.enroll(paths)
        except voice.VoiceUnavailable as exc:
            raise HTTPException(
                503, f"Voice enrollment isn't available on this server: {exc}"
            ) from exc
    if result.failures:
        log.warning("Voice enrollment rejected: %s %s", result.failures, result.quality)
        return JSONResponse(
            {"detail": "voice_quality", "failures": result.failures}, status_code=422
        )
    profiles.save_voice_profile(
        conn, user.id, result.embedding, voice.EMBEDDING_MODEL_ID, result.quality
    )
    # FR-ONB-2: a successful enrollment resolves the voice step of onboarding.
    profile = user.profile
    if profile["display_name"] and profile["onboarding_completed_at"] is None:
        profiles.update_profile(
            conn, user.id, onboarding_completed_at=datetime.now(timezone.utc)
        )
    return voice_payload(conn, user.id)


@router.get("/tasks/summary")
def task_summary(user: SignedIn, conn: Conn) -> dict:
    """FR-PROF-3: approved tasks assigned to me. All zero until speaker matching
    fills in assignees."""
    return profiles.task_summary(conn, user.id)
