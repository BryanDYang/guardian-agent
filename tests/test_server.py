"""HTTP workflow tests with real persistence and a stubbed model process."""

import json
import subprocess
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from labsync.server import create_app

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


def upload(client, **overrides):
    data = {
        "title": "Weekly sync",
        "project": "Capstone",
        "meeting_date": "2026-09-22",
        "permission_confirmed": "true",
    }
    data.update(overrides)
    return client.post(
        "/api/meetings",
        data=data,
        files={"file": ("../../meeting.wav", b"RIFF-test-audio", "audio/wav")},
    )


def wait_for(client, meeting_id, status):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        result = client.get(f"/api/meetings/{meeting_id}").json()
        if result["status"] == status:
            return result
        time.sleep(0.01)
    pytest.fail(f"Meeting did not reach {status}: {result}")


def test_upload_results_audio_and_restart(tmp_path, fake_process):
    with TestClient(create_app(tmp_path)) as client:
        response = upload(client)
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
    with TestClient(create_app(tmp_path)) as client:
        assert client.get("/api/meetings").json()[0]["id"] == meeting_id
        assert client.get(f"/api/meetings/{meeting_id}").json()["status"] == "completed"


@pytest.mark.parametrize("fields", [{"permission_confirmed": "false"}, {"title": " "}])
def test_invalid_metadata_creates_no_job(tmp_path, fake_process, fields):
    with TestClient(create_app(tmp_path)) as client:
        assert upload(client, **fields).status_code == 400
        assert client.get("/api/meetings").json() == []


def test_upload_limits_and_bad_format(tmp_path, fake_process, monkeypatch):
    monkeypatch.setattr("labsync.server.MAX_UPLOAD_BYTES", 4)
    with TestClient(create_app(tmp_path)) as client:
        assert upload(client).status_code == 413
        data = {
            "title": "Test",
            "project": "p",
            "meeting_date": "2026-09-22",
            "permission_confirmed": "true",
        }
        for name, content, status in [
            ("bad.exe", b"123", 415),
            ("empty.wav", b"", 400),
        ]:
            result = client.post(
                "/api/meetings", data=data, files={"file": (name, content)}
            )
            assert result.status_code == status
        assert list(tmp_path.iterdir()) == []


def test_failure_and_retry(tmp_path, fake_process, monkeypatch):
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, ["transcriber"])

    monkeypatch.setattr("labsync.server.subprocess.run", fail)
    with TestClient(create_app(tmp_path)) as client:
        meeting_id = upload(client).json()["id"]
        result = wait_for(client, meeting_id, "failed")
        assert "Transcribing failed" in result["error"]
        monkeypatch.setattr("labsync.server.subprocess.run", fake_process)
        assert client.post(f"/api/meetings/{meeting_id}/retry").status_code == 202
        assert wait_for(client, meeting_id, "completed")["attempt"] == 2


def test_interrupted_job_and_origin_check(tmp_path, fake_process):
    with TestClient(create_app(tmp_path)) as client:
        meeting_id = upload(client).json()["id"]
        wait_for(client, meeting_id, "completed")
    path = tmp_path / meeting_id / "meeting.json"
    record = json.loads(path.read_text())
    record["status"] = "extracting"
    path.write_text(json.dumps(record))
    with TestClient(create_app(tmp_path)) as client:
        result = client.get(f"/api/meetings/{meeting_id}").json()
        assert result["status"] == "failed"
        assert "interrupted" in result["error"]
        assert client.get("/api/meetings/not-an-id").status_code == 404
        assert (
            client.get(
                "/api/meetings", headers={"Origin": "https://untrusted.example"}
            ).status_code
            == 403
        )


def test_purge_project_meetings(tmp_path, fake_process):
    with TestClient(create_app(tmp_path)) as client:
        meeting_id = upload(client).json()["id"]
        wait_for(client, meeting_id, "completed")

        response = client.delete("/api/projects/Capstone/meetings")

        assert response.status_code == 200
        assert response.json() == {"deleted": 1}
        assert client.get("/api/meetings").json() == []
        assert not (tmp_path / meeting_id).exists()
