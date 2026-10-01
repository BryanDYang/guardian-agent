"""Text embeddings from the OpenAI API, shared by meeting indexing and chat queries."""

import json
import math
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_URL = "https://api.openai.com/v1/embeddings"
MODEL = "text-embedding-3-small"
DIMENSIONS = 1536  # must match vector(1536) in the rag_chunks migration
BATCH_SIZE = 256  # inputs per request; the API accepts up to 2048
TIMEOUT = 60


class OpenAIEmbedder:
    """Reads OPENAI_API_KEY on each call, so the server starts without it."""

    name = MODEL

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError(
                "Set OPENAI_API_KEY (for example in .env) to embed text."
            )
        vectors: list[list[float]] = []
        for start in range(0, len(texts), BATCH_SIZE):
            vectors += _request(texts[start : start + BATCH_SIZE], key)
        return vectors


def _request(texts: list[str], key: str) -> list[list[float]]:
    request = Request(
        API_URL,
        data=json.dumps(
            {"model": MODEL, "input": texts, "dimensions": DIMENSIONS}
        ).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "authorization": f"Bearer {key}",
        },
    )
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            body = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(_describe(exc)) from exc
    except (TimeoutError, URLError) as exc:
        raise RuntimeError(
            "Could not reach the OpenAI embeddings API. Check network access."
        ) from exc
    items = sorted(body["data"], key=lambda item: item["index"])
    if len(items) != len(texts):
        raise RuntimeError("OpenAI returned the wrong number of embeddings.")
    return [_normalize(item["embedding"]) for item in items]


def _normalize(vector: list[float]) -> list[float]:
    """OpenAI already returns unit-length vectors; this keeps that true if
    DIMENSIONS is ever lowered, and makes cosine distance a dot product."""
    norm = math.sqrt(sum(v * v for v in vector))
    return [v / norm for v in vector]


def _describe(error: HTTPError) -> str:
    try:
        detail = json.load(error)["error"]["message"]
    except (OSError, ValueError, KeyError, TypeError):
        detail = error.reason
    hint = " Check OPENAI_API_KEY." if error.code in {401, 403} else ""
    return f"OpenAI embeddings failed (HTTP {error.code}): {detail}{hint}"


def to_pgvector(values: list[float]) -> str:
    """Text form of a vector for a `%s::vector` parameter."""
    return "[" + ",".join(f"{value:.7g}" for value in values) + "]"
