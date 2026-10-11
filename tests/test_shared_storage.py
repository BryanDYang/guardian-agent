import io
import json
from urllib.error import HTTPError

import pytest

from labsync.shared_storage import StorageError, SupabaseAudio


def test_storage_protocol_streams_upload_and_checks_private_bucket(
    monkeypatch, tmp_path
):
    calls = []

    def transport(request, timeout):
        body = request.data
        calls.append((request, body.read() if hasattr(body, "read") else body))
        if "/bucket/" in request.full_url:
            return io.BytesIO(b'{"public":false}')
        if request.method == "GET":
            return io.BytesIO(b"audio bytes")
        if "/sign/" in request.full_url:
            return io.BytesIO(
                b'{"signedURL":"/object/sign/meeting-audio/a?token=test"}'
            )
        return io.BytesIO(b"{}")

    monkeypatch.setattr("labsync.shared_storage.urlopen", transport)
    store = SupabaseAudio("https://example.supabase.co", "server-key")
    path = tmp_path / "audio.wav"
    path.write_bytes(b"audio bytes")
    store.check()
    store.upload("project/meeting/recording.wav", path)
    store.download("project/meeting/recording.wav", tmp_path / "download.wav")
    assert (tmp_path / "download.wav").read_bytes() == path.read_bytes()
    assert store.signed_url("project/meeting/recording.wav").startswith(
        "https://example.supabase.co/storage/v1/object/sign/"
    )
    store.delete("project/meeting/recording.wav")
    assert calls[1][1] == b"audio bytes"
    assert calls[1][0].get_header("Content-length") == "11"
    assert json.loads(calls[-1][1]) == {"prefixes": ["project/meeting/recording.wav"]}
    assert all(
        req.get_header("Authorization") == "Bearer server-key" for req, _ in calls
    )


def test_public_bucket_is_rejected(monkeypatch):
    monkeypatch.setattr(
        "labsync.shared_storage.urlopen",
        lambda *args, **kwargs: io.BytesIO(b'{"public":true}'),
    )
    with pytest.raises(StorageError, match="private"):
        SupabaseAudio("https://example.supabase.co", "server-key").check()


def test_storage_errors_do_not_expose_credentials(monkeypatch):
    def fail(*args, **kwargs):
        raise HTTPError("https://example/token=secret", 403, "private body", {}, None)

    monkeypatch.setattr("labsync.shared_storage.urlopen", fail)
    with pytest.raises(StorageError) as error:
        SupabaseAudio("https://example.supabase.co", "server-key").check()
    assert str(error.value) == "Audio storage returned HTTP 403"
