"""Single-user local HTTP API for the meeting UI and CLI pipeline."""

import json
import re
import secrets
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .api.chat import router as chat_router
from .api.deps import Conn, User, require_member
from .api.me import router as me_router
from .api.meetings import router as meetings_router
from .api.projects import router as projects_router
from .api.tasks import router as tasks_router
from .auth import TokenVerifier
from .db import meetings as meeting_store
from .db import projects as project_store
from .db import rag
from .db.connection import create_pool
from .embeddings import OpenAIEmbedder
from .extraction import Extraction, Transcript
from .providers import DEFAULT_MODELS

MAX_UPLOAD_BYTES = 512 * 1024 * 1024
ACTIVE = {"queued", "transcribing", "extracting"}
EXTENSIONS = {".wav", ".mp3", ".mp4", ".m4a", ".flac", ".ogg", ".webm", ".mov"}

# Routes that check Supabase access tokens themselves, so the shared-token
# middleware skips them. Phase 2b widens this one route group at a time.
SUPABASE_ROUTES = re.compile(
    r"/api/v1/(me|projects(/[^/]+(/meetings)?)?|meetings/[^/]+)"
)


def create_app(
    storage: Path = Path("artifacts/server"),
    source: Path = Path("contexts/meeting_transcriber-master"),
    *,
    provider: str = "codex",
    model: str | None = None,
    whisper_model: str = "base",
    whisper_backend: str = "openai",
    diarize: bool = False,
    token: str | None = None,
    database_url: str | None = None,
    embedder: rag.Embedder | None = None,
    supabase_url: str | None = None,
    jwt_secret: str | None = None,
) -> FastAPI:
    if provider not in DEFAULT_MODELS:
        raise ValueError(f"Unknown extraction provider: {provider}")
    if whisper_backend not in {"mlx", "openai"}:
        raise ValueError(f"Unknown Whisper backend: {whisper_backend}")
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

    def transcription_metadata(work: Path) -> dict:
        path = work / "ccb-transcript.json"
        if not path.is_file():
            return {}
        metadata = json.loads(path.read_text()).get("metadata")
        return metadata if isinstance(metadata, dict) else {}

    def sync_database(
        meeting_id,
        status,
        attempt,
        error,
        *,
        transcript=None,
        result=None,
        transcription=None,
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
                    conn, meeting_id, transcript, result, transcription or {}
                )
                rag.index_meeting(conn, meeting_id, app.state.embedder)
            meeting_store.update_status(conn, meeting_id, status, attempt, error)

    def process(meeting_id):
        record = read(meeting_id)
        directory = folder(meeting_id)
        attempt = record["attempt"]
        work = directory / f"attempt-{attempt}"
        stage = "transcribing"
        try:
            update(meeting_id, status=stage)
            sync_database(meeting_id, stage, attempt, None)
            with (directory / "processing.log").open("a") as log:
                command = [
                    sys.executable,
                    "-m",
                    "labsync",
                    "transcribe",
                    str(directory / record["filename"]),
                    "--source",
                    str(source),
                    "--project-id",
                    record["project"],
                    "--meeting-id",
                    meeting_id,
                    "--whisper-model",
                    whisper_model,
                    "--whisper-backend",
                    whisper_backend,
                    "--output-dir",
                    str(work),
                ]
                if diarize:
                    command.append("--diarize")
                subprocess.run(
                    command, check=True, stdout=log, stderr=log, timeout=7200
                )
                transcript = Transcript.model_validate_json(
                    (work / "transcript.json").read_text()
                )
                update(meeting_id, transcript_path=str(work / "transcript.json"))
                stage = "extracting"
                update(meeting_id, status=stage)
                sync_database(meeting_id, stage, attempt, None)
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "labsync",
                        "extract",
                        str(work / "transcript.json"),
                        "--provider",
                        provider,
                        "--model",
                        model,
                        "--output",
                        str(work / "extraction.json"),
                        "--timeout",
                        "300",
                    ],
                    check=True,
                    stdout=log,
                    stderr=log,
                    timeout=330,
                )
                result = json.loads((work / "extraction.json").read_text())
                Extraction.model_validate(result["extraction"]).check_evidence(
                    transcript
                )
                sync_database(
                    meeting_id,
                    "completed",
                    attempt,
                    None,
                    transcript=transcript,
                    result=result,
                    transcription=transcription_metadata(work),
                )
                update(
                    meeting_id,
                    status="completed",
                    extraction_path=str(work / "extraction.json"),
                    error=None,
                )
        except Exception:
            error = (
                f"{stage.capitalize()} failed. Check the backend processing log, "
                "resolve the problem, then retry."
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
            for path in storage.glob("*/meeting.json"):
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
            app.state.executor.shutdown(wait=True)
            if app.state.pool is not None:
                app.state.pool.close()

    app = FastAPI(title="LabSync local backend", lifespan=lifespan)
    app.state.pool = None
    app.state.embedder = embedder or OpenAIEmbedder()
    app.state.auth = TokenVerifier(supabase_url, jwt_secret) if supabase_url else None

    app.state.chat = {"provider": provider, "model": model}
    app.include_router(projects_router)
    app.include_router(meetings_router)
    app.include_router(tasks_router)
    app.include_router(chat_router)
    app.include_router(me_router)

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
    async def require_token(request: Request, call_next):
        if token and not SUPABASE_ROUTES.fullmatch(request.url.path):
            supplied = request.headers.get("authorization", "")
            if not secrets.compare_digest(
                supplied.encode(), f"Bearer {token}".encode()
            ):
                return JSONResponse(
                    {"detail": "Missing or invalid API token"},
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

    def public(record):
        return {
            key: value
            for key, value in record.items()
            if key not in {"filename", "transcript_path", "extraction_path"}
        }

    @app.get("/api/meetings")
    def meetings():
        with lock:
            records = [
                json.loads(path.read_text()) for path in storage.glob("*/meeting.json")
            ]
        return sorted(
            [public(record) for record in records],
            key=lambda record: record["created_at"],
            reverse=True,
        )

    @app.post("/api/meetings", status_code=202)
    def upload(
        file: UploadFile,
        title: Annotated[str, Form()],
        project: Annotated[str, Form()],
        meeting_date: Annotated[date, Form()],
        permission_confirmed: Annotated[bool, Form()],
    ):
        if not permission_confirmed:
            raise HTTPException(400, "Confirm permission to process this recording")
        if (
            not title.strip()
            or not project.strip()
            or len(title) > 200
            or len(project) > 100
        ):
            raise HTTPException(
                400, "Provide a title and project within the length limits"
            )
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
                "title": title.strip(),
                "project": project.strip(),
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
            app.state.executor.submit(app.state.process, meeting_id)
            return public(record)
        except Exception:
            shutil.rmtree(directory)
            raise
        finally:
            file.file.close()

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
            for record in matching:
                shutil.rmtree(folder(record["id"]), ignore_errors=True)
        return {"deleted": 1}

    @app.delete("/api/projects/{project}/meetings")
    def purge_project(project: str):
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
        removed = len(matching)
        try:
            project_id = UUID(project)
        except ValueError:
            project_id = None
        if project_id is not None and app.state.pool is not None:
            with app.state.pool.connection() as conn:
                removed = max(
                    removed, meeting_store.delete_project_meetings(conn, project_id)
                )
        return {"deleted": removed}

    @app.get("/api/meetings/{meeting_id}")
    def detail(meeting_id: str):
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
    def audio(meeting_id: str):
        record = read(meeting_id)
        return FileResponse(folder(meeting_id) / record["filename"])

    @app.post("/api/meetings/{meeting_id}/retry", status_code=202)
    def retry(meeting_id: str):
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

    return app
