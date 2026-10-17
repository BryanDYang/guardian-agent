"""Opt-in shared audio and recoverable workers. Local mode remains separate."""

import hashlib
import logging
import shutil
from datetime import date, datetime, timezone
from pathlib import Path
from threading import Event, Thread
from typing import Annotated
from uuid import UUID, uuid4, uuid5

from fastapi import Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from psycopg.types.json import Jsonb

from .api.deps import Conn, SignedIn, User, require_meeting, require_member
from .db import meetings, profiles, projects, rag
from .pipeline import run_pipeline
from .shared_jobs import LeaseLost, claim, clean_uploads, finish, guard, heartbeat
from .shared_storage import StorageError

logger = logging.getLogger(__name__)


class SharedBackend:
    def __init__(
        self,
        app,
        audio,
        storage,
        source,
        settings,
        worker_id,
        lease_seconds,
        identify,
        run,
    ):
        self.app, self.audio, self.storage, self.source = app, audio, storage, source
        self.settings, self.worker_id = settings, worker_id
        self.lease_seconds, self.identify, self.run = lease_seconds, identify, run
        self.shutdown = Event()
        self.thread = Thread(
            target=self.loop, name="shared-meeting-worker", daemon=True
        )

    @property
    def pool(self):
        return self.app.state.pool

    def start(self):
        self.audio.check()
        with self.pool.connection() as conn:
            conn.execute("SELECT 1 FROM meeting_jobs LIMIT 1")
        self.thread.start()

    def stop(self):
        self.shutdown.set()
        # Keep the pool alive until the in-flight attempt finishes. Forced process
        # termination instead leaves the lease to expire for another worker.
        if self.thread.is_alive():
            self.thread.join()

    def loop(self):
        while not self.shutdown.is_set():
            try:
                with self.pool.connection() as conn:
                    job = claim(conn, self.worker_id, self.lease_seconds)
                if job:
                    self.process(job)
                with self.pool.connection() as conn:
                    clean_uploads(conn)
                self.cleanup()
                if not job:
                    self.shutdown.wait(2)
            except Exception:
                logger.exception("Shared worker operation failed; retrying")
                self.shutdown.wait(2)

    def cleanup(self):
        with self.pool.connection() as conn:
            row = conn.execute(
                "SELECT object_key FROM audio_deletions ORDER BY created_at "
                "FOR UPDATE SKIP LOCKED LIMIT 1"
            ).fetchone()
            if row:
                self.audio.delete(row["object_key"])
                conn.execute(
                    "DELETE FROM audio_deletions WHERE object_key=%s",
                    (row["object_key"],),
                )

    def process(self, job):
        meeting_id, token = job["meeting_id"], job["claim_token"]
        directory = self.storage / str(meeting_id) / str(token)
        directory.mkdir(parents=True)
        record = job["record"]
        record["id"] = str(meeting_id)
        done, lost = Event(), Event()

        def renew():
            while not done.wait(self.lease_seconds / 3):
                try:
                    with self.pool.connection() as conn:
                        alive = heartbeat(conn, meeting_id, token, self.lease_seconds)
                    if not alive:
                        lost.set()
                        return
                except Exception:
                    # Fail closed. Never publish results without current ownership.
                    lost.set()
                    return

        timer = Thread(target=renew, daemon=True)
        timer.start()

        def stage(value):
            if lost.is_set():
                raise LeaseLost()
            with self.pool.connection() as conn:
                guard(conn, meeting_id, token)
                record["status"] = value
                conn.execute(
                    "UPDATE meeting_jobs SET record=%s WHERE meeting_id=%s",
                    (Jsonb(record), meeting_id),
                )
                meetings.update_status(conn, meeting_id, value, record["attempt"], None)

        try:
            self.audio.download(job["object_key"], directory / record["filename"])
            transcript, named, result, identity, metadata = run_pipeline(
                record,
                directory,
                directory / "pipeline",
                self.source,
                job["settings"],
                self.identify,
                stage,
                self.run,
            )
            if lost.is_set():
                raise LeaseLost()
            with self.pool.connection() as conn:
                guard(conn, meeting_id, token)
                meetings.save_results(
                    conn, meeting_id, transcript, result, metadata, identity
                )
                rag.index_meeting(conn, meeting_id, self.app.state.embedder)
                record.update(
                    status="completed",
                    error=None,
                    transcript=named.model_dump(mode="json"),
                    extraction=result["extraction"],
                )
                # Result rows, index, status, and job completion commit together.
                finish(conn, meeting_id, token, record, "completed")
                meetings.update_status(
                    conn, meeting_id, "completed", record["attempt"], None
                )
        except LeaseLost:
            logger.info("Discarding results from replaced claim for %s", meeting_id)
        except Exception:
            logger.exception("Shared meeting %s failed", meeting_id)
            if not lost.is_set():
                try:
                    with self.pool.connection() as conn:
                        error = "Processing failed. Check the backend log, then retry."
                        record.update(status="failed", error=error)
                        finish(conn, meeting_id, token, record, "failed")
                        meetings.update_status(
                            conn, meeting_id, "failed", record["attempt"], error
                        )
                except LeaseLost:
                    pass
        finally:
            done.set()
            timer.join()
            # Keep failure logs locally; audio/speaker/model artifacts are temporary.
            if (directory / "processing.log").exists():
                shutil.copyfile(
                    directory / "processing.log", directory.parent / f"{token}.log"
                )
            shutil.rmtree(directory, ignore_errors=True)


def public(record):
    return {k: v for k, v in record.items() if k != "filename"}


def install_routes(app):
    # Replace only the local file-dependent routes in shared mode.
    paths = {
        "/api/v1/meetings/upload",
        "/api/meetings/{meeting_id}",
        "/api/meetings/{meeting_id}/audio",
        "/api/meetings/{meeting_id}/retry",
        "/api/projects/{project_id}/meetings",
        "/api/v1/projects/{project_id}",
        "/api/v1/me",
        "/api/health",
    }
    app.router.routes[:] = [
        route
        for route in app.router.routes
        if not (
            getattr(route, "path", None) in paths
            and (
                "DELETE" in getattr(route, "methods", set())
                or getattr(route, "path", None)
                not in {"/api/v1/projects/{project_id}", "/api/v1/me"}
            )
        )
    ]

    def backend(request):
        return request.app.state.shared

    def job_row(conn, meeting_id):
        row = conn.execute(
            "SELECT * FROM meeting_jobs WHERE meeting_id=%s", (meeting_id,)
        ).fetchone()
        if not row:
            raise HTTPException(
                409, "This meeting uses local storage on its original backend"
            )
        return row

    @app.get("/api/health")
    def health(request: Request):
        try:
            with app.state.pool.connection() as conn:
                conn.execute("SELECT 1 FROM meeting_jobs LIMIT 1")
            backend(request).audio.check()
            if not backend(request).thread.is_alive():
                raise RuntimeError("Worker is not running")
        except Exception:
            raise HTTPException(
                503, "Shared backend dependencies unavailable"
            ) from None
        return {"status": "ok", "mode": "shared"}

    @app.post("/api/v1/meetings/upload", status_code=202)
    def upload(
        request: Request,
        file: UploadFile,
        title: Annotated[str, Form()],
        project_id: Annotated[UUID, Form()],
        meeting_date: Annotated[date, Form()],
        consent_confirmed: Annotated[bool, Form()],
        user: User,
        conn: Conn,
    ):
        from .server import EXTENSIONS, MAX_UPLOAD_BYTES

        require_member(conn, user, project_id)
        if not consent_confirmed:
            raise HTTPException(400, "Confirm permission to process this recording")
        if not title.strip() or len(title.strip()) > 255:
            raise HTTPException(400, "Provide a title within the length limits")
        extension = Path(file.filename or "").suffix.lower()
        if extension not in EXTENSIONS:
            raise HTTPException(415, "Choose a supported audio or video file")
        shared = backend(request)
        upload_key = request.headers.get("Idempotency-Key")
        if upload_key:
            try:
                UUID(upload_key)
            except ValueError:
                raise HTTPException(400, "Idempotency-Key must be a UUID") from None
        meeting_id = (
            uuid5(user.id, f"{project_id}:{upload_key}") if upload_key else uuid4()
        )
        directory = shared.storage / str(meeting_id) / ("upload-" + str(uuid4()))
        directory.mkdir(parents=True)
        filename = "recording" + extension
        key = f"{project_id}/{meeting_id}/{filename}"
        record = dict(
            id=str(meeting_id),
            title=title.strip(),
            project=str(project_id),
            date=meeting_date.isoformat(),
            filename=filename,
            created_at=datetime.now(timezone.utc).isoformat(),
            permission_confirmed=True,
            status="queued",
            attempt=1,
            diarization=shared.settings["diarize"],
            error=None,
        )
        inserted = False
        try:
            total = 0
            digest = hashlib.sha256()
            with (directory / filename).open("xb") as target:
                while chunk := file.file.read(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_UPLOAD_BYTES:
                        raise HTTPException(413, "Recording exceeds the 512 MB limit")
                    digest.update(chunk)
                    target.write(chunk)
            if not total:
                raise HTTPException(400, "Recording is empty")
            record["audio_sha256"] = digest.hexdigest()
            # Serialize publication/deletion for this project. The lock is released
            # before the network upload; its durable uploading row blocks deletion.
            conn.execute(
                "SELECT id FROM projects WHERE id=%s FOR UPDATE", (project_id,)
            )
            require_member(conn, user, project_id)
            existing = conn.execute(
                "SELECT * FROM meeting_jobs WHERE meeting_id=%s", (meeting_id,)
            ).fetchone()
            if existing:
                old = existing["record"]
                if any(
                    old.get(k) != record[k]
                    for k in ("title", "date", "filename", "audio_sha256")
                ):
                    raise HTTPException(
                        409, "Idempotency-Key belongs to another upload"
                    )
                if existing["state"] == "uploading":
                    raise HTTPException(
                        409,
                        "Upload is still being stored; retry later",
                        headers={"Retry-After": "5"},
                    )
                return public(old) | {"job_id": str(meeting_id)}
            # Durable uploading row precedes object creation, allowing crash cleanup.
            meetings.create_meeting(
                conn,
                meeting_id=str(meeting_id),
                project_id=project_id,
                name=title.strip(),
                meeting_date=meeting_date,
                audio_file_path="supabase://meeting-audio/" + key,
                uploaded_by=user.id,
            )
            conn.execute(
                "INSERT INTO meeting_jobs(meeting_id,object_key,record,settings,state) "
                "VALUES (%s,%s,%s,%s,'uploading')",
                (meeting_id, key, Jsonb(record), Jsonb(shared.settings)),
            )
            conn.commit()
            inserted = True
            shared.audio.upload(key, directory / filename)
            conn.execute(
                "UPDATE meeting_jobs SET state='queued',updated_at=now() "
                "WHERE meeting_id=%s AND state='uploading'",
                (meeting_id,),
            )
            conn.commit()
            return public(record) | {"job_id": str(meeting_id)}
        except Exception as exc:
            conn.rollback()
            if inserted:
                conn.execute("DELETE FROM meetings WHERE id=%s", (meeting_id,))
                # Trigger schedules cleanup even when upload timed out.
                conn.commit()
            if isinstance(exc, StorageError):
                raise HTTPException(
                    503, "Audio storage is unavailable; retry upload"
                ) from None
            raise
        finally:
            file.file.close()
            shutil.rmtree(directory, ignore_errors=True)

    @app.get("/api/meetings/{meeting_id}")
    def detail(meeting_id: UUID, user: User, conn: Conn):
        require_meeting(conn, user, meeting_id)
        record = public(job_row(conn, meeting_id)["record"])
        return (
            {"transcript": None, "extraction": None}
            | record
            | {"audio_url": f"/api/meetings/{meeting_id}/audio"}
        )

    @app.get("/api/meetings/{meeting_id}/audio")
    def audio(request: Request, meeting_id: UUID, user: User, conn: Conn):
        require_meeting(conn, user, meeting_id)
        row = job_row(conn, meeting_id)
        try:
            url = backend(request).audio.signed_url(row["object_key"])
        except StorageError:
            raise HTTPException(503, "Audio storage is unavailable") from None
        return RedirectResponse(
            url, status_code=307, headers={"Cache-Control": "no-store"}
        )

    @app.post("/api/meetings/{meeting_id}/retry", status_code=202)
    def retry(meeting_id: UUID, user: User, conn: Conn):
        require_meeting(conn, user, meeting_id)
        row = conn.execute(
            "SELECT * FROM meeting_jobs WHERE meeting_id=%s FOR UPDATE", (meeting_id,)
        ).fetchone()
        if not row:
            raise HTTPException(409, "Retry on the original local backend")
        if row["state"] != "failed":
            raise HTTPException(409, "Only failed meetings can be retried")
        record = row["record"]
        record.update(status="queued", error=None, attempt=record["attempt"] + 1)
        record.pop("transcript", None)
        record.pop("extraction", None)
        conn.execute(
            "UPDATE meeting_jobs SET state='queued',record=%s,claim_token=NULL,"
            "worker_id=NULL,lease_until=NULL,updated_at=now() WHERE meeting_id=%s",
            (Jsonb(record), meeting_id),
        )
        meetings.update_status(conn, meeting_id, "queued", record["attempt"], None)
        return public(record)

    def lock_project(conn, project_id):
        conn.execute("SELECT id FROM projects WHERE id=%s FOR UPDATE", (project_id,))
        # Text-only imports have no processing job or recording to clean up.
        # Keep local recordings protected so their files are not orphaned.
        if conn.execute(
            "SELECT 1 FROM meetings m WHERE m.project_id=%s "
            "AND NULLIF(m.audio_file_path, '') IS NOT NULL "
            "AND m.audio_file_path <> 'scripted-text-only:no-audio' AND NOT EXISTS "
            "(SELECT 1 FROM meeting_jobs j WHERE j.meeting_id=m.id) LIMIT 1",
            (project_id,),
        ).fetchone():
            raise HTTPException(
                409, "Delete local recordings on their original backend"
            )
        conn.execute("SELECT id FROM projects WHERE id=%s FOR UPDATE", (project_id,))
        if conn.execute(
            "SELECT 1 FROM meetings WHERE project_id=%s AND status IN "
            "('queued','transcribing','diarizing','extracting') LIMIT 1",
            (project_id,),
        ).fetchone():
            raise HTTPException(
                409, "Wait for active meetings to finish before deleting"
            )

    @app.delete("/api/projects/{project_id}/meetings")
    def purge(project_id: UUID, user: User, conn: Conn):
        require_member(conn, user, project_id)
        lock_project(conn, project_id)
        count = meetings.delete_project_meetings(conn, project_id)
        return {"deleted": count}

    @app.delete("/api/v1/projects/{project_id}")
    def delete_project(project_id: UUID, user: User, conn: Conn):
        require_member(conn, user, project_id)
        lock_project(conn, project_id)
        recipients = projects.member_ids(conn, project_id)
        projects.delete_project(conn, project_id)
        conn.commit()
        app.state.project_events.publish(recipients)
        return {"deleted": 1}

    @app.delete("/api/v1/me")
    def delete_account(user: SignedIn, conn: Conn):
        solo = sorted(projects.solo_projects(conn, user.id), key=str)
        recipients = projects.co_member_ids(conn, user.id)
        for project_id in solo:
            lock_project(conn, project_id)
            projects.delete_project(conn, project_id)
        profiles.delete_account(conn, user.id)
        conn.commit()
        app.state.project_events.publish(recipients)
        return {"deleted_projects": len(solo)}
