import math
import os
import re
import time
import uuid
from zlib import crc32

import jwt
import psycopg
import pytest
from psycopg.types.json import Jsonb

from labsync.embeddings import DIMENSIONS

# Every test app trusts tokens signed with this secret, as if issued by a local
# Supabase at this URL. Pass both to create_app(supabase_url=..., jwt_secret=...).
SUPABASE_URL = "http://127.0.0.1:54321"
JWT_SECRET = "pytest-jwt-secret-with-at-least-32-characters"


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


def make_token(sub, *, key=JWT_SECRET, algorithm="HS256", headers=None, **overrides):
    """An access token shaped like the ones Supabase Auth issues."""
    claims = {
        "sub": str(sub),
        "aud": "authenticated",
        "iss": SUPABASE_URL + "/auth/v1",
        "exp": int(time.time()) + 3600,
        "role": "authenticated",
    } | overrides
    return jwt.encode(claims, key, algorithm=algorithm, headers=headers)


@pytest.fixture
def make_user():
    """Create signed-in users: make_user(name) -> (user_id, request headers).

    Inserts into auth.users the way Supabase Auth does, so the trigger creates
    the profile. Users have finished onboarding unless onboarded=False. Needs
    TEST_DATABASE_URL. Users are deleted afterwards, which also removes their
    memberships."""
    database_url = os.environ["TEST_DATABASE_URL"]
    created = []

    def make(name="Pytest User", *, onboarded=True):
        user_id = uuid.uuid4()
        with psycopg.connect(database_url) as conn:
            conn.execute(
                "INSERT INTO auth.users (id, email, raw_user_meta_data, "
                "raw_app_meta_data) VALUES (%s, %s, %s, %s)",
                (
                    user_id,
                    f"pytest-{user_id}@example.com",
                    Jsonb({"full_name": name}),
                    Jsonb({}),
                ),
            )
            if onboarded:
                conn.execute(
                    "UPDATE profiles SET onboarding_completed_at = now() WHERE id = %s",
                    (user_id,),
                )
        created.append(user_id)
        return user_id, {"Authorization": f"Bearer {make_token(user_id)}"}

    yield make
    with psycopg.connect(database_url) as conn:
        conn.execute("DELETE FROM auth.users WHERE id = ANY(%s)", (created,))
