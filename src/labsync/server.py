"""Single-user local HTTP API for the meeting UI and CLI pipeline."""

import json
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

from .extraction import Extraction, Transcript

MAX_UPLOAD_BYTES = 512 * 1024 * 1024
ACTIVE = {"queued", "transcribing", "extracting"}
EXTENSIONS = {".wav", ".mp3", ".mp4", ".m4a", ".flac", ".ogg", ".webm", ".mov"}


def create_app(
    storage: Path = Path("artifacts/server"),
    source: Path = Path("contexts/meeting_transcriber-master"),
    model: str = "gpt-5.6-sol",
    whisper_model: str = "base",
    diarize: bool = False,
) -> FastAPI:
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

    def process(meeting_id):
        record = read(meeting_id)
        directory = folder(meeting_id)
        work = directory / f"attempt-{record['attempt']}"
        stage = "transcribing"
        try:
            update(meeting_id, status=stage)
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
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "labsync",
                        "extract",
                        str(work / "transcript.json"),
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
                update(
                    meeting_id,
                    status="completed",
                    extraction_path=str(work / "extraction.json"),
                    error=None,
                )
        except Exception:
            update(
                meeting_id,
                status="failed",
                error=(
                    f"{stage.capitalize()} failed. Check the backend processing log, "
                    "resolve the problem, then retry."
                ),
            )

    @asynccontextmanager
    async def lifespan(app):
        storage.mkdir(parents=True, exist_ok=True)
        for path in storage.glob("*/meeting.json"):
            record = json.loads(path.read_text())
            if record["status"] in ACTIVE:
                record.update(
                    status="failed",
                    error="Processing was interrupted. Retry this meeting.",
                )
                save(record)
        app.state.executor = ThreadPoolExecutor(max_workers=1)
        app.state.process = process
        yield
        app.state.executor.shutdown(wait=True)

    app = FastAPI(title="LabSync local backend", lifespan=lifespan)
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

    @app.get("/api/health")
    def health():
        return {"status": "ok", "diarization": diarize, "whisper_model": whisper_model}

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
        return {"deleted": len(matching)}

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
        app.state.executor.submit(app.state.process, meeting_id)
        return public(record)

    return app
