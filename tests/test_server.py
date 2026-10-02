"""HTTP workflow tests with real persistence and a stubbed model process.

Tests marked needs_db run against a local database only, e.g. after
`supabase start`:
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
Never point this at the Supabase project."""

import json
import os
import subprocess
import time
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import psycopg
import pytest
from conftest import JWT_SECRET, SUPABASE_URL, make_token
from fastapi.testclient import TestClient

from labsync.api.deps import CurrentUser, onboarded_user
from labsync.embeddings import OpenAIEmbedder
from labsync.providers import DEFAULT_MODELS
from labsync.server import create_app

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
needs_db = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")

TRANSCRIPT = {
    "project_id": "Capstone",
    "meeting_id": "test",
    "turns": [
        {
            "id": "turn-0",
            "speaker": "UNKNOWN",
            "start_time_ms": 0,
            "end_time_ms": 1000,
            "content": "We will review this later.",
        }
    ],
}
EXTRACTION = {
    "summary": "A review was discussed.",
    "decisions": [],
    "commitments": [],
    "suggestions": [],
}


@pytest.fixture
def fake_process(monkeypatch):
    def run(command, **kwargs):
        if "transcribe" in command:
            directory = Path(command[command.index("--output-dir") + 1])
            directory.mkdir()
            transcript = dict(TRANSCRIPT)
            transcript["meeting_id"] = command[command.index("--meeting-id") + 1]
            (directory / "transcript.json").write_text(json.dumps(transcript))
        else:
            Path(command[command.index("--output") + 1]).write_text(
                json.dumps({"extraction": EXTRACTION})
            )

    monkeypatch.setattr("labsync.server.subprocess.run", run)
    return run


@pytest.fixture
def member(make_user):
    """A project with one signed-in member: (project_id, headers)."""
    user_id, headers = make_user()
    with psycopg.connect(DATABASE_URL) as conn:
        project_id = conn.execute(
            "INSERT INTO projects (name) VALUES ('pytest server') RETURNING id"
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO project_members (project_id, user_id, role) "
            "VALUES (%s, %s, 'member')",
            (project_id, user_id),
        )
    yield str(project_id), headers
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("DELETE FROM projects WHERE id = %s", (project_id,))


def make_app(storage, embedder, **options):
    """A backend that uses the test database and trusts the test tokens."""
    return create_app(
        storage,
        database_url=DATABASE_URL,
        embedder=embedder,
        supabase_url=SUPABASE_URL,
        jwt_secret=JWT_SECRET,
        **options,
    )


def upload(client, project_id, **overrides):
    data = {
        "project_id": project_id,
        "title": "Weekly sync",
        "meeting_date": "2026-09-22",
        "consent_confirmed": "true",
    } | overrides
    return client.post(
        "/api/v1/meetings/upload",
        data=data,
        files={"file": ("../../meeting.wav", b"RIFF-test-audio", "audio/wav")},
    )


def signed_in_member(app, monkeypatch):
    """Skip token and membership checks for tests that fake the database."""
    app.dependency_overrides[onboarded_user] = lambda: CurrentUser(
        id=uuid4(), email="member@example.com", profile={}
    )
    monkeypatch.setattr("labsync.db.access.is_member", lambda *args: True)


def wait_for(client, meeting_id, status):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        result = client.get(f"/api/meetings/{meeting_id}").json()
        if result["status"] == status:
            return result
        time.sleep(0.01)
    pytest.fail(f"Meeting did not reach {status}: {result}")


def test_embedder_defaults_and_can_be_injected(tmp_path):
    app = create_app(tmp_path)
    assert isinstance(app.state.embedder, OpenAIEmbedder)
    sentinel = object()
    app = create_app(tmp_path, embedder=sentinel)
    assert app.state.embedder is sentinel


@needs_db
def test_upload_results_audio_and_restart(tmp_path, fake_process, embedder, member):
    project_id, headers = member
    with TestClient(make_app(tmp_path, embedder), headers=headers) as client:
        response = upload(client, project_id)
        assert response.status_code == 202
        meeting_id = response.json()["id"]
        result = wait_for(client, meeting_id, "completed")
        assert result["transcript"]["turns"][0]["speaker"] == "UNKNOWN"
        assert result["extraction"] == EXTRACTION
        assert "filename" not in result and "transcript_path" not in result
        audio = client.get(result["audio_url"], headers={"Range": "bytes=0-3"})
        assert audio.status_code == 206
        assert audio.content == b"RIFF"
        assert not (tmp_path.parent / "meeting.wav").exists()
        assert client.post(f"/api/meetings/{meeting_id}/retry").status_code == 409
    with TestClient(make_app(tmp_path, embedder), headers=headers) as client:
        assert client.get(f"/api/meetings/{meeting_id}").json()["status"] == "completed"


@needs_db
@pytest.mark.parametrize("fields", [{"consent_confirmed": "false"}, {"title": " "}])
def test_invalid_metadata_creates_no_job(
    tmp_path, fake_process, embedder, member, fields
):
    project_id, headers = member
    with TestClient(make_app(tmp_path, embedder), headers=headers) as client:
        assert upload(client, project_id, **fields).status_code == 400
    assert list(tmp_path.glob("*/meeting.json")) == []


@needs_db
def test_upload_limits_and_bad_format(
    tmp_path, fake_process, embedder, member, monkeypatch
):
    project_id, headers = member
    monkeypatch.setattr("labsync.server.MAX_UPLOAD_BYTES", 4)
    with TestClient(make_app(tmp_path, embedder), headers=headers) as client:
        assert upload(client, project_id).status_code == 413
        data = {
            "project_id": project_id,
            "title": "Test",
            "meeting_date": "2026-09-22",
            "consent_confirmed": "true",
        }
        for name, content, status in [
            ("bad.exe", b"123", 415),
            ("empty.wav", b"", 400),
        ]:
            result = client.post(
                "/api/v1/meetings/upload", data=data, files={"file": (name, content)}
            )
            assert result.status_code == status
        assert list(tmp_path.iterdir()) == []


@needs_db
def test_failure_and_retry(tmp_path, fake_process, embedder, member, monkeypatch):
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, ["transcriber"])

    project_id, headers = member
    monkeypatch.setattr("labsync.server.subprocess.run", fail)
    with TestClient(make_app(tmp_path, embedder), headers=headers) as client:
        meeting_id = upload(client, project_id).json()["id"]
        result = wait_for(client, meeting_id, "failed")
        assert "Transcribing failed" in result["error"]
        monkeypatch.setattr("labsync.server.subprocess.run", fake_process)
        assert client.post(f"/api/meetings/{meeting_id}/retry").status_code == 202
        assert wait_for(client, meeting_id, "completed")["attempt"] == 2


@needs_db
def test_selected_provider_reaches_extraction(
    tmp_path, fake_process, embedder, member, monkeypatch
):
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        fake_process(command, **kwargs)

    project_id, headers = member
    monkeypatch.setattr("labsync.server.subprocess.run", run)
    app = make_app(tmp_path, embedder, provider="claude")
    with TestClient(app, headers=headers) as client:
        health = client.get("/api/health").json()
        assert health["extraction_provider"] == "claude"
        assert health["extraction_model"] == DEFAULT_MODELS["claude"]
        wait_for(client, upload(client, project_id).json()["id"], "completed")
    extract = commands[-1]
    assert extract[extract.index("--provider") + 1] == "claude"
    assert extract[extract.index("--model") + 1] == DEFAULT_MODELS["claude"]
    with pytest.raises(ValueError, match="Unknown extraction provider"):
        create_app(tmp_path, provider="gemini")


@needs_db
@pytest.mark.parametrize("backend", ["mlx", "openai"])
def test_whisper_backend_reaches_transcription(
    tmp_path, fake_process, embedder, member, monkeypatch, backend
):
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        fake_process(command, **kwargs)

    project_id, headers = member
    monkeypatch.setattr("labsync.server.subprocess.run", run)
    app = make_app(tmp_path, embedder, whisper_backend=backend)
    with TestClient(app, headers=headers) as client:
        assert client.get("/api/health").json()["whisper_backend"] == backend
        wait_for(client, upload(client, project_id).json()["id"], "completed")
    transcribe = commands[0]
    assert transcribe[transcribe.index("--whisper-backend") + 1] == backend
    for invalid in ["auto", "cuda"]:
        with pytest.raises(ValueError, match="Unknown Whisper backend"):
            create_app(tmp_path, whisper_backend=invalid)


@needs_db
def test_interrupted_job_and_origin_check(tmp_path, fake_process, embedder, member):
    project_id, headers = member
    with TestClient(make_app(tmp_path, embedder), headers=headers) as client:
        meeting_id = upload(client, project_id).json()["id"]
        wait_for(client, meeting_id, "completed")
    path = tmp_path / meeting_id / "meeting.json"
    record = json.loads(path.read_text())
    record["status"] = "extracting"
    path.write_text(json.dumps(record))
    with TestClient(make_app(tmp_path, embedder), headers=headers) as client:
        result = client.get(f"/api/meetings/{meeting_id}").json()
        assert result["status"] == "failed"
        assert "interrupted" in result["error"]
        assert client.get("/api/meetings/not-an-id").status_code == 404
        untrusted = {"Origin": "https://untrusted.example"}
        assert client.get("/api/health", headers=untrusted).status_code == 403


def test_tasks_router_is_mounted(tmp_path):
    """The tasks router answers even before Postgres is configured."""
    with TestClient(create_app(tmp_path)) as client:
        response = client.get(
            "/api/v1/tasks",
            params={
                "project_id": "00000000-0000-0000-0000-000000000000",
                "start_date": "2026-10-01",
                "end_date": "2026-10-31",
            },
        )
    assert response.status_code == 503
    assert "DATABASE_URL" in response.json()["detail"]


def test_tokens_are_checked_before_an_upload_is_read(tmp_path):
    """No database needed: bad tokens never get past the middleware."""
    app = create_app(tmp_path, supabase_url=SUPABASE_URL, jwt_secret=JWT_SECRET)
    files = {"file": ("meeting.wav", b"RIFF-test-audio", "audio/wav")}
    with TestClient(app) as client:
        for headers in [
            {},
            {"Authorization": "Bearer not-a-token"},
            {"Authorization": f"Bearer {make_token(uuid4(), key='x' * 32)}"},
        ]:
            response = client.post(
                "/api/v1/meetings/upload", files=files, headers=headers
            )
            assert response.status_code == 401
            assert response.headers["www-authenticate"] == "Bearer"
        assert list(tmp_path.iterdir()) == []
        assert client.get("/api/health").status_code == 200
        # A valid token gets through to the route, which then needs the database.
        valid = {"Authorization": f"Bearer {make_token(uuid4())}"}
        assert client.get("/api/v1/projects", headers=valid).status_code == 503


@needs_db
def test_older_routes_are_private(tmp_path, fake_process, embedder, member, make_user):
    project_id, headers = member
    _, outsider = make_user("Outsider")
    with TestClient(make_app(tmp_path, embedder), headers=headers) as client:
        meeting_id = upload(client, project_id).json()["id"]
        wait_for(client, meeting_id, "completed")
        for method, url in [
            ("GET", f"/api/meetings/{meeting_id}"),
            ("GET", f"/api/meetings/{meeting_id}/audio"),
            ("POST", f"/api/meetings/{meeting_id}/retry"),
            ("DELETE", f"/api/projects/{project_id}/meetings"),
        ]:
            assert client.request(method, url, headers=outsider).status_code == 404
        assert client.get(f"/api/meetings/{meeting_id}").status_code == 200


@needs_db
def test_purge_project_meetings(tmp_path, fake_process, embedder, member):
    project_id, headers = member
    with TestClient(make_app(tmp_path, embedder), headers=headers) as client:
        meeting_id = upload(client, project_id).json()["id"]
        wait_for(client, meeting_id, "completed")

        response = client.delete(f"/api/projects/{project_id}/meetings")

        assert response.status_code == 200
        assert response.json() == {"deleted": 1}
        assert client.get(f"/api/meetings/{meeting_id}").status_code == 404
        assert not (tmp_path / meeting_id).exists()


@pytest.mark.parametrize("status", ["completed", "queued"])
def test_delete_project_removes_recordings_only_after_database_success(
    tmp_path, monkeypatch, status
):
    project_id, meeting_id = uuid4(), uuid4()
    storage = tmp_path / "storage"
    directory = storage / str(meeting_id)
    app = create_app(storage, tmp_path)
    deleted = []

    def delete_project(conn, value):
        deleted.append(value)
        return True

    monkeypatch.setattr("labsync.server.project_store.delete_project", delete_project)
    signed_in_member(app, monkeypatch)
    with TestClient(app) as client:
        directory.mkdir()
        (directory / "recording.wav").write_bytes(b"audio")
        (directory / "meeting.json").write_text(
            json.dumps(
                {"id": str(meeting_id), "project": str(project_id), "status": status}
            )
        )
        app.state.pool = SimpleNamespace(connection=lambda: nullcontext(object()))
        response = client.delete(f"/api/v1/projects/{project_id}")
        app.state.pool = None
        if status == "queued":
            assert response.status_code == 409
            assert directory.exists()
            assert deleted == []
        else:
            assert response.status_code == 200
            assert response.json() == {"deleted": 1}
            assert not directory.exists()
            assert deleted == [project_id]


def test_delete_project_requires_database(tmp_path):
    with TestClient(create_app(tmp_path, tmp_path)) as client:
        assert client.delete(f"/api/v1/projects/{uuid4()}").status_code == 503


@pytest.mark.parametrize("busy", [False, True])
def test_delete_project_preserves_recordings_when_database_rejects(
    tmp_path, monkeypatch, busy
):
    from labsync.db.projects import ProjectBusyError

    project_id, meeting_id = uuid4(), uuid4()
    app = create_app(tmp_path, tmp_path)

    def reject(conn, value):
        if busy:
            raise ProjectBusyError
        return False

    monkeypatch.setattr("labsync.server.project_store.delete_project", reject)
    signed_in_member(app, monkeypatch)
    with TestClient(app) as client:
        directory = tmp_path / str(meeting_id)
        directory.mkdir()
        (directory / "meeting.json").write_text(
            json.dumps(
                {
                    "id": str(meeting_id),
                    "project": str(project_id),
                    "status": "completed",
                }
            )
        )
        app.state.pool = SimpleNamespace(connection=lambda: nullcontext(object()))
        response = client.delete(f"/api/v1/projects/{project_id}")
        app.state.pool = None
        assert response.status_code == (409 if busy else 404)
        assert directory.exists()
