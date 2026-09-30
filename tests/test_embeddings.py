import io
import json
from urllib.error import HTTPError

import pytest

from labsync import embeddings
from labsync.embeddings import DIMENSIONS, OpenAIEmbedder, to_pgvector


def test_pgvector_text_form():
    assert to_pgvector([0.5, -0.25, 1e-8]) == "[0.5,-0.25,1e-08]"


def test_empty_input_needs_no_key_or_network(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert OpenAIEmbedder().encode([]) == []


def test_missing_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        OpenAIEmbedder().encode(["hello"])


@pytest.fixture
def fake_api(monkeypatch):
    """Stands in for urlopen and records every request body."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    requests = []

    def urlopen(request, timeout):
        body = json.loads(request.data)
        requests.append(body)
        # Return items out of order, as the API is allowed to; values are not
        # unit length, to check that the client normalizes.
        data = [
            {"index": i, "embedding": [float(i + 1)] + [0.0] * (DIMENSIONS - 1)}
            for i in range(len(body["input"]))
        ]
        return io.BytesIO(json.dumps({"data": data[::-1]}).encode())

    monkeypatch.setattr(embeddings, "urlopen", urlopen)
    monkeypatch.setattr(embeddings, "BATCH_SIZE", 2)
    return requests


def test_batches_keeps_order_and_normalizes(fake_api):
    vectors = OpenAIEmbedder().encode(["a", "b", "c"])
    assert [len(v) for v in vectors] == [DIMENSIONS] * 3
    assert [v[0] for v in vectors] == [1.0, 1.0, 1.0]  # unit length
    assert [body["input"] for body in fake_api] == [["a", "b"], ["c"]]
    assert fake_api[0]["model"] == "text-embedding-3-small"
    assert fake_api[0]["dimensions"] == DIMENSIONS


def test_api_errors_are_readable(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "bad-key")

    def fail(request, timeout):
        raise HTTPError(
            embeddings.API_URL,
            401,
            "Unauthorized",
            {},
            io.BytesIO(b'{"error": {"message": "Incorrect API key provided."}}'),
        )

    monkeypatch.setattr(embeddings, "urlopen", fail)
    with pytest.raises(RuntimeError, match=r"HTTP 401\).*Check OPENAI_API_KEY"):
        OpenAIEmbedder().encode(["hello"])