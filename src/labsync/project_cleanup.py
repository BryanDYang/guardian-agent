"""Daily expiry of recoverable projects and retryable local recording cleanup."""

import logging
import shutil
from pathlib import Path
from threading import Event, Thread

from .db import projects

logger = logging.getLogger(__name__)


class ProjectCleanup:
    def __init__(self, pool, storage, events):
        self.pool, self.storage, self.events = pool, storage, events
        self.shutdown = Event()
        self.thread = Thread(target=self.loop, name="project-cleanup", daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.shutdown.set()
        self.thread.join()

    def loop(self):
        while not self.shutdown.is_set():
            try:
                self.run_once()
            except Exception:
                logger.exception("Project cleanup failed; retrying in one hour")
                self.shutdown.wait(3600)
                continue
            self.shutdown.wait(86400)

    def run_once(self):
        with self.pool.connection() as conn:
            expired = conn.execute(
                "SELECT id FROM projects WHERE deleted_at <= now() - interval '30 days'"
            ).fetchall()
        for project in expired:
            with self.pool.connection() as conn:
                projects.lock_delivery(conn, project["id"])
                row = conn.execute(
                    "SELECT id FROM projects WHERE id=%s "
                    "AND deleted_at <= now() - interval '30 days' FOR UPDATE",
                    (project["id"],),
                ).fetchone()
                if not row:
                    continue
                recipients = projects.member_ids(conn, project["id"])
                try:
                    projects.delete_project(conn, project["id"])
                except projects.ProjectBusyError:
                    continue
            self.events.publish(recipients)
        # The queue survives database cascades and process crashes. A backend
        # never deletes files outside its own meeting storage directory.
        with self.pool.connection() as conn:
            recordings = conn.execute(
                "SELECT meeting_id, audio_file_path FROM local_recording_deletions"
            ).fetchall()
        for recording in recordings:
            directory = (self.storage / str(recording["meeting_id"])).resolve()
            if Path(recording["audio_file_path"]).parent.resolve() != directory:
                continue
            if directory.exists():
                shutil.rmtree(directory)
            with self.pool.connection() as conn:
                conn.execute(
                    "DELETE FROM local_recording_deletions WHERE meeting_id=%s",
                    (recording["meeting_id"],),
                )
