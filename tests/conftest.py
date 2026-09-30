import math
import re
from zlib import crc32

import pytest

from labsync.embeddings import DIMENSIONS


class HashEmbedder:
    """Offline stand-in for the real embedder: a normalized bag of hashed words.
    Texts that share words are close, which is enough to exercise the dense leg."""

    name = "test-hash-embedder"

    def encode(self, texts):
        vectors = []
        for text in texts:
            vector = [0.0] * DIMENSIONS
            for word in re.findall(r"[a-z0-9]+", text.lower()):
                vector[crc32(word.encode()) % DIMENSIONS] += 1.0
            vector[0] += 1e-3  # never the zero vector
            norm = math.sqrt(sum(v * v for v in vector))
            vectors.append([v / norm for v in vector])
        return vectors


@pytest.fixture
def embedder():
    return HashEmbedder()
