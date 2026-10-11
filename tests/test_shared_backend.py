"""Two independent API/worker instances sharing a real isolated PostgreSQL DB.

Storage and inference are offline stand-ins; no team data or live keys are used.
"""

import json
import os
import time
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from conftest import JWT_SECRET, SUPABASE_URL
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from labsync.server import create_app
from labsync.shared_backend import SharedBackend
from labsync.shared_jobs import LeaseLost, claim, finish, heartbeat
from labsync.shared_storage import StorageError

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")


class MemoryAudio:
    def __init__(self):
        self.objects = {}
        self.fail_upload = False

    def check(self):
        pass

    def upload(self, key, path):
        self.objects[key] = path.read_bytes()
        if self.fail_upload:
            raise StorageError("Upload interrupted after storage write")

    def download(self, key, path):
        path.write_bytes(self.objects[key])

    def delete(self, key):
        self.objects.pop(key, None)

    def signed_url(self, key):
        assert key in self.objects
        return "https://storage.example.test/audio?signed=temporary"


@pytest.fixture
def member(make_user):
    user_id, headers = make_user()
    with psycopg.connect(DATABASE_URL) as conn:
        project = conn.execute(
            "INSERT INTO projects(name) VALUES('shared test') RETURNING id"
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO project_members(project_id,user_id,role) "
            "VALUES(%s,%s,'owner')",
            (project, user_id),
        )
    yield project, headers
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("DELETE FROM projects WHERE id=%s", (project,))
        conn.execute(
            "DELETE FROM audio_deletions WHERE object_key LIKE %s",
            (str(project) + "/%",),
        )


@pytest.fixture
def fake_inference(monkeypatch):
    def run(command, **kwargs):
        if "transcribe" in command:
            work = Path(command[command.index("--output-dir") + 1])
            work.mkdir()
            transcript = {
                "project_id": command[command.index("--project-id") + 1],
                "meeting_id": command[command.index("--meeting-id") + 1],
                "turns": [
                    {
                        "id": "t1",
                        "speaker": "A",
                        "start_time_ms": 0,
                        "end_time_ms": 1000,
                        "content": "I will review the schema by Friday.",
                    }
                ],
            }
            (work / "transcript.json").write_text(json.dumps(transcript))
        else:
            Path(command[command.index("--output") + 1]).write_text(
                json.dumps(
                    {
                        "extraction": {
                            "summary": "Schema review planned.",
                            "decisions": [],
                            "suggestions": [],
                            "commitments": [
                                {
                                    "title": "Review the schema",
                                    "owner": None,
                                    "due_date_text": "Friday",
                                    "evidence": [
                                        {
                                            "transcript_id": "t1",
                                            "quote": "review the schema by Friday",
                                        }
                                    ],
                                }
                            ],
                        }
                    }
                )
            )

    monkeypatch.setattr("labsync.server.subprocess.run", run)


@pytest.fixture
def pair(tmp_path, embedder, fake_inference, monkeypatch):
    # Deterministic claim/recovery tests explicitly drive each worker.
    monkeypatch.setattr(SharedBackend, "start", lambda self: self.audio.check())
    audio = MemoryAudio()
    apps = [
        create_app(
            tmp_path / name,
            database_url=DATABASE_URL,
            embedder=embedder,
            supabase_url=SUPABASE_URL,
            jwt_secret=JWT_SECRET,
            shared_audio=audio,
            worker_id=name,
            lease_seconds=15,
        )
        for name in ("one", "two")
    ]
    with TestClient(apps[0]) as first, TestClient(apps[1]) as second:
        yield apps, first, second, audio


def upload(client, member, key=None):
    project, auth = member
    return client.post(
        "/api/v1/meetings/upload",
        headers=auth | ({"Idempotency-Key": key} if key else {}),
        data={
            "project_id": str(project),
            "title": "Connected meeting",
            "meeting_date": "2026-10-10",
            "consent_confirmed": "true",
        },
        files={"file": ("meeting.wav", b"fake audio", "audio/wav")},
    )


def claim_for(app):
    with app.state.pool.connection() as conn:
        return claim(conn, app.state.shared.worker_id, 15)


def test_upload_on_one_recover_on_two_and_read_on_either(pair, member, make_user):
    apps, first, second, audio = pair
    response = upload(first, member)
    assert response.status_code == 202, response.text
    meeting_id = response.json()["id"]
    old = claim_for(apps[0])
    assert old is not None
    assert claim_for(apps[1]) is None
    with apps[0].state.pool.connection() as conn:
        conn.execute(
            "UPDATE meeting_jobs SET lease_until=now()-interval '1 second' "
            "WHERE meeting_id=%s",
            (meeting_id,),
        )
    recovered = claim_for(apps[1])
    assert recovered["record"]["attempt"] == 2
    with apps[0].state.pool.connection() as conn:
        assert not heartbeat(conn, meeting_id, old["claim_token"], 15)
        with pytest.raises(LeaseLost):
            finish(conn, meeting_id, old["claim_token"], old["record"], "completed")
    apps[1].state.shared.process(recovered)
    for client in (first, second):
        result = client.get(f"/api/meetings/{meeting_id}", headers=member[1])
        assert result.status_code == 200, result.text
        assert result.json()["status"] == "completed"
        assert result.json()["extraction"]["summary"] == "Schema review planned."
        assert result.json()["transcript"]["turns"][0]["id"] == "t1"
        redirect = client.get(
            f"/api/meetings/{meeting_id}/audio",
            headers=member[1],
            follow_redirects=False,
        )
        assert redirect.status_code == 307
        assert redirect.headers["cache-control"] == "no-store"
    _, outsider = make_user()
    assert (
        second.get(f"/api/meetings/{meeting_id}/audio", headers=outsider).status_code
        == 404
    )
    assert second.get(f"/api/meetings/{meeting_id}/audio").status_code == 401
    with apps[1].state.pool.connection() as conn:
        assert (
            conn.execute(
                "SELECT count(*) AS n FROM tasks WHERE meeting_id=%s", (meeting_id,)
            ).fetchone()["n"]
            == 1
        )
    # A stale worker finishing late cannot replace the recovered result.
    with apps[0].state.pool.connection() as conn:
        with pytest.raises(LeaseLost):
            finish(conn, meeting_id, old["claim_token"], old["record"], "failed")
    assert len(audio.objects) == 1


def test_upload_idempotency_across_backends(pair, member):
    _, first, second, audio = pair
    key = str(uuid4())
    one, two = upload(first, member, key), upload(second, member, key)
    assert one.status_code == two.status_code == 202
    assert one.json()["id"] == two.json()["id"]
    assert len(audio.objects) == 1
    conflict = second.post(
        "/api/v1/meetings/upload",
        headers=member[1] | {"Idempotency-Key": key},
        data={
            "project_id": str(member[0]),
            "title": "Different",
            "meeting_date": "2026-10-10",
            "consent_confirmed": "true",
        },
        files={"file": ("meeting.wav", b"different audio", "audio/wav")},
    )
    assert conflict.status_code == 409


def test_failed_upload_and_project_purge_cleanup_objects(pair, member):
    apps, first, second, audio = pair
    audio.fail_upload = True
    assert upload(first, member).status_code == 503
    apps[1].state.shared.cleanup()
    assert not audio.objects
    audio.fail_upload = False
    meeting_id = upload(first, member).json()["id"]
    assert (
        second.delete(
            f"/api/projects/{member[0]}/meetings", headers=member[1]
        ).status_code
        == 409
    )
    apps[1].state.shared.process(claim_for(apps[1]))
    assert (
        second.delete(
            f"/api/projects/{member[0]}/meetings", headers=member[1]
        ).status_code
        == 200
    )
    apps[0].state.shared.cleanup()
    assert not audio.objects
    assert (
        first.get(f"/api/meetings/{meeting_id}", headers=member[1]).status_code == 404
    )


def test_failed_processing_retry_on_other_backend(pair, member):
    apps, first, second, audio = pair
    meeting_id = upload(first, member).json()["id"]
    job = claim_for(apps[0])

    def fail(*args, **kwargs):
        raise RuntimeError("inference unavailable")

    original = apps[0].state.shared.run
    apps[0].state.shared.run = fail
    apps[0].state.shared.process(job)
    assert (
        first.get(f"/api/meetings/{meeting_id}", headers=member[1]).json()["status"]
        == "failed"
    )
    retry = second.post(f"/api/meetings/{meeting_id}/retry", headers=member[1])
    assert retry.status_code == 202
    assert retry.json()["attempt"] == 2
    apps[0].state.shared.run = original
    apps[1].state.shared.process(claim_for(apps[1]))
    assert (
        first.get(f"/api/meetings/{meeting_id}", headers=member[1]).json()["status"]
        == "completed"
    )


def test_actual_two_worker_loops(tmp_path, embedder, fake_inference, member):
    audio = MemoryAudio()
    apps = [
        create_app(
            tmp_path / name,
            database_url=DATABASE_URL,
            embedder=embedder,
            supabase_url=SUPABASE_URL,
            jwt_secret=JWT_SECRET,
            shared_audio=audio,
            worker_id=name,
            lease_seconds=15,
        )
        for name in ("live-one", "live-two")
    ]
    with TestClient(apps[0]) as first, TestClient(apps[1]) as second:
        response = upload(first, member)
        assert response.status_code == 202
        meeting_id = response.json()["id"]
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            state = second.get(f"/api/meetings/{meeting_id}", headers=member[1]).json()
            if state["status"] in {"completed", "failed"}:
                break
            time.sleep(0.05)
        assert state["status"] == "completed", state
        assert first.get("/api/health").status_code == 200
        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
            assert (
                conn.execute(
                    "SELECT count(*) AS n FROM tasks WHERE meeting_id=%s", (meeting_id,)
                ).fetchone()["n"]
                == 1
            )


def test_killed_claimant_recovers_without_manual_lease_edit(pair, member):
    import subprocess
    import sys

    apps, first, second, _ = pair
    meeting_id = upload(first, member).json()["id"]
    script = """
import os, time, psycopg
from psycopg.rows import dict_row
from labsync.shared_jobs import claim
with psycopg.connect(os.environ['TEST_DATABASE_URL'], row_factory=dict_row) as c:
    job = claim(c, 'terminated-worker', 1)
print(str(job['meeting_id']), flush=True)
time.sleep(60)
"""
    child = subprocess.Popen(
        [sys.executable, "-c", script], stdout=subprocess.PIPE, text=True
    )
    try:
        assert child.stdout.readline().strip() == meeting_id
    finally:
        child.terminate()
        child.wait(timeout=5)
    # The worker is gone; real lease time, not a test SQL edit, permits recovery.
    time.sleep(1.1)
    recovered = claim_for(apps[1])
    assert str(recovered["meeting_id"]) == meeting_id
    assert recovered["record"]["attempt"] == 2
    apps[1].state.shared.process(recovered)
    assert (
        second.get(f"/api/meetings/{meeting_id}", headers=member[1]).json()["status"]
        == "completed"
    )


def test_connected_meetings_wait_for_previous_job(pair, member):
    apps, first, second, _ = pair
    first_id = upload(first, member).json()["id"]
    second_id = upload(second, member).json()["id"]
    job = claim_for(apps[0])
    assert str(job["meeting_id"]) == first_id
    assert claim_for(apps[1]) is None
    apps[0].state.shared.process(job)
    next_job = claim_for(apps[1])
    assert str(next_job["meeting_id"]) == second_id
    apps[1].state.shared.process(next_job)
