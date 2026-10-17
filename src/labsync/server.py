"""Single-user local HTTP API for the meeting UI and CLI pipeline."""

import json
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import voice
from .api.chat import router as chat_router
from .api.deps import Conn, SignedIn, User, require_meeting, require_member
from .api.followup import router as followup_router
from .api.invitations import router as invitations_router
from .api.me import router as me_router
from .api.meetings import router as meetings_router
from .api.projects import ProjectEvents
from .api.projects import router as projects_router
from .api.tasks import router as tasks_router
from .auth import InvalidToken, TokenVerifier
from .ccb import SPEAKERS_FILE
from .db import meetings as meeting_store
from .db import profiles, rag
from .db import projects as project_store
from .db.connection import create_pool
from .embeddings import OpenAIEmbedder
from .pipeline import run_pipeline
from .providers import DEFAULT_MODELS

MAX_UPLOAD_BYTES = 512 * 1024 * 1024
ACTIVE = {"queued", "transcribing", "extracting"}
EXTENSIONS = {".wav", ".mp3", ".mp4", ".m4a", ".flac", ".ogg", ".webm", ".mov"}


def create_app(
    storage: Path = Path("artifacts/server"),
    source: Path = Path("contexts/meeting_transcriber-master"),
    *,
    provider: str = "codex",
    model: str | None = None,
    whisper_model: str = "base",
    whisper_backend: str = "openai",
    diarize: bool = True,
    database_url: str | None = None,
    embedder: rag.Embedder | None = None,
    supabase_url: str | None = None,
    jwt_secret: str | None = None,
    shared_audio=None,
    worker_id: str | None = None,
    lease_seconds: int = 120,
) -> FastAPI:
    if provider not in DEFAULT_MODELS:
        raise ValueError(f"Unknown extraction provider: {provider}")
    if whisper_backend not in {"mlx", "openai"}:
        raise ValueError(f"Unknown Whisper backend: {whisper_backend}")
    if shared_audio is not None and (
        not database_url or not worker_id or lease_seconds < 15
    ):
        raise ValueError("Shared mode requires a database, worker ID, and lease >= 15s")
    model = model or DEFAULT_MODELS[provider]
    storage, source = storage.resolve(), source.resolve()
    lock = RLock()

    def folder(meeting_id):
        try:
            return storage / str(UUID(meeting_id))
        except ValueError as exc:
            raise HTTPException(404, "Meeting not found") from exc

    def read(meeting_id):
        path = folder(meeting_id) / "meeting.json"
        if not path.is_file():
            raise HTTPException(404, "Meeting not found")
        return json.loads(path.read_text())

    def save(record):
        directory = folder(record["id"])
        temporary = directory / "meeting.tmp"
        temporary.write_text(json.dumps(record, indent=2))
        temporary.replace(directory / "meeting.json")

    def update(meeting_id, **fields):
        with lock:
            record = read(meeting_id)
            record.update(fields)
            save(record)

    def sync_database(
        meeting_id,
        status,
        attempt,
        error,
        *,
        transcript=None,
        result=None,
        transcription=None,
        identification=None,
    ):
        """Mirror pipeline state into Postgres when this meeting has a row."""
        pool = app.state.pool
        if pool is None:
            return
        with pool.connection() as conn:
            if (
                conn.execute(
                    "SELECT 1 FROM meetings WHERE id = %s", (meeting_id,)
                ).fetchone()
                is None
            ):
                return
            if transcript is not None and result is not None:
                meeting_store.save_results(
                    conn,
                    meeting_id,
                    transcript,
                    result,
                    transcription or {},
                    identification,
                )
                rag.index_meeting(conn, meeting_id, app.state.embedder)
            meeting_store.update_status(conn, meeting_id, status, attempt, error)

    def identify_speakers(project_id, transcript, work: Path) -> dict:
        """Match the diarized speakers to the project's enrolled members. Any
        failure leaves everyone as SPEAKER_N, never fails the meeting (FR-SPK-7)."""
        path = work / SPEAKERS_FILE
        try:
            diarized = json.loads(path.read_text()) if path.is_file() else None
            candidates = []
            if diarized is not None and app.state.pool is not None:
                with app.state.pool.connection() as conn:
                    candidates = profiles.voice_candidates(
                        conn, project_id, voice.EMBEDDING_MODEL_ID
                    )
            return voice.identify(transcript, diarized, candidates)
        except Exception as exc:
            return voice.unidentified(transcript, f"error: {type(exc).__name__}")
        finally:
            # Speaker embeddings, guests' included, are not kept after matching.
            path.unlink(missing_ok=True)

    settings = dict(
        provider=provider,
        model=model,
        whisper_model=whisper_model,
        whisper_backend=whisper_backend,
        diarize=diarize,
    )

    def process(meeting_id):
        record = read(meeting_id)
        directory = folder(meeting_id)
        attempt = record["attempt"]
        work = directory / f"attempt-{attempt}"
        current_stage = "transcribing"

        def stage(value):
            nonlocal current_stage
            current_stage = value
            update(meeting_id, status=value)
            if value == "extracting":
                update(
                    meeting_id, transcript_path=str(work / "labeled-transcript.json")
                )
            sync_database(meeting_id, value, attempt, None)

        try:
            transcript, named, result, identification, metadata = run_pipeline(
                record,
                directory,
                work,
                source,
                settings,
                identify_speakers,
                stage,
                subprocess.run,
            )
            update(meeting_id, transcript_path=str(work / "labeled-transcript.json"))
            sync_database(
                meeting_id,
                "completed",
                attempt,
                None,
                transcript=transcript,
                result=result,
                transcription=metadata,
                identification=identification,
            )
            update(
                meeting_id,
                status="completed",
                extraction_path=str(work / "extraction.json"),
                error=None,
            )
        except Exception:
            error = (
                f"{current_stage.capitalize()} failed. Check the backend processing "
                "log, resolve the problem, then retry."
            )
            update(meeting_id, status="failed", error=error)
            sync_database(meeting_id, "failed", attempt, error)

    @asynccontextmanager
    async def lifespan(app):
        storage.mkdir(parents=True, exist_ok=True)
        app.state.executor = ThreadPoolExecutor(max_workers=1)
        app.state.process = process
        app.state.pool = None
        try:
            if database_url:
                app.state.pool = create_pool(database_url)
                from .followup import EmailWorker

                with app.state.pool.connection() as conn:
                    migrated = conn.execute(
                        "SELECT to_regclass('public.task_followup_emails') AS name"
                    ).fetchone()["name"]
                if migrated:
                    app.state.email_worker = EmailWorker(app.state.pool)
                    app.state.email_worker.start()
            if shared_audio is not None:
                from .shared_backend import SharedBackend

                app.state.shared = SharedBackend(
                    app,
                    shared_audio,
                    storage,
                    source,
                    settings,
                    worker_id,
                    lease_seconds,
                    identify_speakers,
                    subprocess.run,
                )
                app.state.shared.start()
            for path in (
                [] if shared_audio is not None else storage.glob("*/meeting.json")
            ):
                record = json.loads(path.read_text())
                if record["status"] in ACTIVE:
                    record.update(
                        status="failed",
                        error="Processing was interrupted. Retry this meeting.",
                    )
                    save(record)
                    sync_database(
                        record["id"],
                        "failed",
                        record["attempt"],
                        record["error"],
                    )
            yield
        finally:
            if hasattr(app.state, "email_worker"):
                app.state.email_worker.stop()
            if shared_audio is not None and hasattr(app.state, "shared"):
                app.state.shared.stop()
            app.state.executor.shutdown(wait=True)
            if app.state.pool is not None:
                app.state.pool.close()

    app = FastAPI(title="LabSync local backend", lifespan=lifespan)
    app.state.pool = None
    app.state.embedder = embedder or OpenAIEmbedder()
    app.state.auth = TokenVerifier(supabase_url, jwt_secret) if supabase_url else None
    app.state.project_events = ProjectEvents()
    # Live project-list streams end after this long; the app reconnects.
    app.state.event_stream_seconds = 600

    app.state.chat = {"provider": provider, "model": model}
    app.include_router(projects_router)
    app.include_router(meetings_router)
    app.include_router(tasks_router)
    app.include_router(chat_router)
    app.include_router(me_router)
    app.include_router(invitations_router)
    app.include_router(followup_router)

    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"]
    )

    @app.middleware("http")
    async def local_browser_only(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin and origin not in {
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        }:
            return JSONResponse({"detail": "Untrusted browser origin"}, status_code=403)
        return await call_next(request)

    @app.middleware("http")
    async def check_token_early(request: Request, call_next):
        """Turn away a missing or invalid Supabase token before FastAPI reads the
        request body, so strangers can't make the server store large uploads.
        Routes still load the user and check project membership themselves."""
        verifier, path = app.state.auth, request.url.path
        if verifier is not None and path.startswith("/api/") and path != "/api/health":
            header = request.headers.get("authorization", "")
            scheme, _, credentials = header.partition(" ")
            try:
                if scheme.lower() != "bearer" or not credentials:
                    raise InvalidToken("No bearer token")
                await run_in_threadpool(verifier.verify, credentials)
            except InvalidToken:
                return JSONResponse(
                    {"detail": "Sign in to continue"},
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                )
        return await call_next(request)

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "diarization": diarize,
            "whisper_model": whisper_model,
            "whisper_backend": whisper_backend,
            "extraction_provider": provider,
            "extraction_model": model,
        }

    def require_stored_meeting(conn, user, meeting_id: str) -> None:
        """Membership check for the /api/meetings/{id} routes, whose ids are plain
        strings. A malformed id is just another meeting that isn't found."""
        try:
            require_meeting(conn, user, UUID(meeting_id))
        except ValueError as exc:
            raise HTTPException(404, "Meeting not found") from exc

    def public(record):
        return {
            key: value
            for key, value in record.items()
            if key not in {"filename", "transcript_path", "extraction_path"}
        }

    @app.post("/api/v1/meetings/upload", status_code=202)
    def upload_to_project(
        file: UploadFile,
        title: Annotated[str, Form()],
        project_id: Annotated[UUID, Form()],
        meeting_date: Annotated[date, Form()],
        consent_confirmed: Annotated[bool, Form()],
        user: User,
        conn: Conn,
    ):
        if not consent_confirmed:
            raise HTTPException(400, "Confirm permission to process this recording")
        name = title.strip()
        if not name or len(name) > 255:
            raise HTTPException(400, "Provide a title within the length limits")
        require_member(conn, user, project_id)
        extension = Path(file.filename or "").suffix.lower()
        if extension not in EXTENSIONS:
            raise HTTPException(415, "Choose a supported audio or video file")
        meeting_id = str(uuid4())
        directory = folder(meeting_id)
        directory.mkdir()
        filename = "recording" + extension
        try:
            total = 0
            with (directory / filename).open("xb") as destination:
                while chunk := file.file.read(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_UPLOAD_BYTES:
                        raise HTTPException(413, "Recording exceeds the 512 MB limit")
                    destination.write(chunk)
            if not total:
                raise HTTPException(400, "Recording is empty")
            record = {
                "id": meeting_id,
                "title": name,
                "project": str(project_id),
                "date": meeting_date.isoformat(),
                "filename": filename,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "permission_confirmed": True,
                "status": "queued",
                "attempt": 1,
                "diarization": diarize,
                "error": None,
            }
            with lock:
                save(record)
            with app.state.pool.connection() as conn:
                meeting_store.create_meeting(
                    conn,
                    meeting_id=meeting_id,
                    project_id=project_id,
                    name=name,
                    meeting_date=meeting_date,
                    audio_file_path=str(directory / filename),
                    uploaded_by=user.id,
                )
            app.state.executor.submit(app.state.process, meeting_id)
            return public(record) | {"job_id": meeting_id}
        except Exception:
            shutil.rmtree(directory, ignore_errors=True)
            try:
                with app.state.pool.connection() as conn:
                    conn.execute("DELETE FROM meetings WHERE id = %s", (meeting_id,))
            except Exception:
                pass
            raise
        finally:
            file.file.close()

    @app.delete("/api/v1/projects/{project_id}")
    def delete_project(project_id: UUID, user: User, conn: Conn):
        require_member(conn, user, project_id)
        recipients = project_store.member_ids(conn, project_id)
        with lock:
            records = [
                json.loads(path.read_text()) for path in storage.glob("*/meeting.json")
            ]
            matching = [r for r in records if r["project"] == str(project_id)]
            if any(r["status"] in ACTIVE for r in matching):
                raise HTTPException(
                    409, "Wait for active meetings to finish before deleting"
                )
            with app.state.pool.connection() as conn:
                try:
                    deleted = project_store.delete_project(conn, project_id)
                except project_store.ProjectBusyError as exc:
                    raise HTTPException(
                        409, "Wait for active meetings to finish before deleting"
                    ) from exc
                if not deleted:
                    raise HTTPException(404, "Project not found")
            # Committed when the block above closed its connection.
            app.state.project_events.publish(recipients)
            for record in matching:
                shutil.rmtree(folder(record["id"]), ignore_errors=True)
        return {"deleted": 1}

    @app.delete("/api/v1/me")
    def delete_account(user: SignedIn, conn: Conn):
        """FR-ACCT: projects where this user is the only member go with the
        account, recordings included. Shared projects keep their content."""
        solo = {
            str(project_id) for project_id in project_store.solo_projects(conn, user.id)
        }
        # Their shared projects lose a member, so those members' counts change.
        recipients = project_store.co_member_ids(conn, user.id)
        busy = HTTPException(
            409, "Wait for your meetings to finish processing, then try again"
        )
        with lock:
            records = [
                json.loads(path.read_text()) for path in storage.glob("*/meeting.json")
            ]
            matching = [r for r in records if r["project"] in solo]
            if any(r["status"] in ACTIVE for r in matching):
                raise busy
            try:
                for project_id in solo:
                    project_store.delete_project(conn, UUID(project_id))
            except project_store.ProjectBusyError as exc:
                raise busy from exc
            profiles.delete_account(conn, user.id)
            # Commit before removing recordings, so a failed delete keeps them.
            conn.commit()
            app.state.project_events.publish(recipients)
            for record in matching:
                shutil.rmtree(folder(record["id"]), ignore_errors=True)
        return {"deleted_projects": len(solo)}

    @app.delete("/api/projects/{project_id}/meetings")
    def purge_project(project_id: UUID, user: User, conn: Conn):
        require_member(conn, user, project_id)
        project = str(project_id)
        with lock:
            records = [
                json.loads(path.read_text()) for path in storage.glob("*/meeting.json")
            ]
            matching = [record for record in records if record["project"] == project]
            if any(record["status"] in ACTIVE for record in matching):
                raise HTTPException(
                    409, "Wait for active project meetings to finish before purging"
                )
            for record in matching:
                shutil.rmtree(folder(record["id"]))
        with app.state.pool.connection() as writer:
            removed = meeting_store.delete_project_meetings(writer, project_id)
        return {"deleted": max(len(matching), removed)}

    @app.get("/api/meetings/{meeting_id}")
    def detail(meeting_id: str, user: User, conn: Conn):
        require_stored_meeting(conn, user, meeting_id)
        with lock:
            record = read(meeting_id)
        result = public(record)
        result["transcript"] = (
            json.loads(Path(record["transcript_path"]).read_text())
            if record.get("transcript_path")
            else None
        )
        result["extraction"] = (
            json.loads(Path(record["extraction_path"]).read_text())["extraction"]
            if record.get("extraction_path")
            else None
        )
        result["audio_url"] = f"/api/meetings/{meeting_id}/audio"
        return result

    @app.get("/api/meetings/{meeting_id}/audio")
    def audio(meeting_id: str, user: User, conn: Conn):
        require_stored_meeting(conn, user, meeting_id)
        record = read(meeting_id)
        return FileResponse(folder(meeting_id) / record["filename"])

    @app.post("/api/meetings/{meeting_id}/retry", status_code=202)
    def retry(meeting_id: str, user: User, conn: Conn):
        require_stored_meeting(conn, user, meeting_id)
        with lock:
            record = read(meeting_id)
            if record["status"] != "failed":
                raise HTTPException(409, "Only failed meetings can be retried")
            record.update(status="queued", error=None, attempt=record["attempt"] + 1)
            record.pop("transcript_path", None)
            record.pop("extraction_path", None)
            save(record)
        sync_database(meeting_id, "queued", record["attempt"], None)
        app.state.executor.submit(app.state.process, meeting_id)
        return public(record)

    if shared_audio is not None:
        from .shared_backend import install_routes

        install_routes(app)
    return app
