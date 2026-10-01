"""Supabase access tokens and /api/v1/me (Accounts & Voice Identity spec, Phase 2a).

Token tests need nothing. The /me tests run against a local database only,
e.g. after `supabase start`:
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
Never point this at the Supabase project."""

import os
import time
import uuid
from types import SimpleNamespace

import jwt
import psycopg
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from psycopg.types.json import Jsonb

from labsync.auth import InvalidToken, TokenVerifier
from labsync.server import create_app

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
needs_db = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")

SUPABASE_URL = "http://127.0.0.1:54321"
ISSUER = SUPABASE_URL + "/auth/v1"
SECRET = "pytest-jwt-secret-with-at-least-32-characters"


def make_token(sub, *, key=SECRET, algorithm="HS256", headers=None, **overrides):
    claims = {
        "sub": str(sub),
        "aud": "authenticated",
        "iss": ISSUER,
        "exp": int(time.time()) + 3600,
        "role": "authenticated",
    } | overrides
    return jwt.encode(claims, key, algorithm=algorithm, headers=headers)


# ---------------------------------------------------------------- token checks


def test_hs256_token_is_accepted_with_the_secret():
    user_id = uuid.uuid4()
    claims = TokenVerifier(SUPABASE_URL, SECRET).verify(make_token(user_id))
    assert claims["sub"] == str(user_id)


def test_hs256_token_is_rejected_without_a_configured_secret():
    with pytest.raises(InvalidToken):
        TokenVerifier(SUPABASE_URL).verify(make_token(uuid.uuid4()))


@pytest.mark.parametrize(
    "token",
    [
        make_token(uuid.uuid4(), exp=int(time.time()) - 60),
        make_token(uuid.uuid4(), aud="anon"),
        make_token(uuid.uuid4(), iss="https://other.supabase.co/auth/v1"),
        make_token(uuid.uuid4(), key="a-different-secret-that-is-32-chars-long"),
        jwt.encode({"aud": "authenticated", "iss": ISSUER, "exp": 2**31}, SECRET),
        jwt.encode({"sub": "x", "aud": "authenticated", "iss": ISSUER}, SECRET),
        make_token(uuid.uuid4(), key="", algorithm="none"),
        "not-a-jwt",
    ],
    ids=[
        "expired",
        "wrong-audience",
        "wrong-issuer",
        "wrong-secret",
        "no-subject",
        "no-expiry",
        "unsigned",
        "garbage",
    ],
)
def test_bad_tokens_are_rejected(token):
    with pytest.raises(InvalidToken):
        TokenVerifier(SUPABASE_URL, SECRET).verify(token)


def test_es256_token_is_checked_against_the_published_key(monkeypatch):
    private_key = ec.generate_private_key(ec.SECP256R1())
    verifier = TokenVerifier(SUPABASE_URL)
    monkeypatch.setattr(
        verifier._jwks,
        "get_signing_key_from_jwt",
        lambda token: SimpleNamespace(key=private_key.public_key()),
    )
    user_id = uuid.uuid4()
    token = make_token(
        user_id, key=private_key, algorithm="ES256", headers={"kid": "k1"}
    )
    assert verifier.verify(token)["sub"] == str(user_id)

    other_key = ec.generate_private_key(ec.SECP256R1())
    forged = make_token(user_id, key=other_key, algorithm="ES256")
    with pytest.raises(InvalidToken):
        verifier.verify(forged)


# ---------------------------------------------------------------- /api/v1/me


@pytest.fixture
def client(tmp_path):
    app = create_app(
        tmp_path,
        tmp_path,
        token="test-token",
        database_url=DATABASE_URL,
        supabase_url=SUPABASE_URL,
        jwt_secret=SECRET,
    )
    with TestClient(app) as client:
        yield client


@pytest.fixture
def make_user():
    """Create auth users the way Supabase Auth does; the trigger adds profiles."""
    created = []

    def make(name="Pytest User"):
        user_id = uuid.uuid4()
        email = f"pytest-{user_id}@example.com"
        with psycopg.connect(DATABASE_URL) as conn:
            conn.execute(
                "INSERT INTO auth.users (id, email, raw_user_meta_data, "
                "raw_app_meta_data) VALUES (%s, %s, %s, %s)",
                (user_id, email, Jsonb({"full_name": name}), Jsonb({})),
            )
        created.append(user_id)
        return user_id, {"Authorization": f"Bearer {make_token(user_id)}"}

    yield make
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("DELETE FROM projects WHERE name = 'pytest auth'")
        conn.execute("DELETE FROM auth.users WHERE id = ANY(%s)", (created,))


@needs_db
def test_me_requires_a_supabase_token(client):
    assert client.get("/api/v1/me").status_code == 401
    # The old shared API token is not a user session.
    shared = {"Authorization": "Bearer test-token"}
    assert client.get("/api/v1/me", headers=shared).status_code == 401


@needs_db
def test_me_returns_profile_and_onboarding_step(client, make_user):
    user_id, auth = make_user("Test One")
    body = client.get("/api/v1/me", headers=auth).json()
    assert body["id"] == str(user_id)
    assert body["display_name"] == "Test One"
    assert body["email"] == f"pytest-{user_id}@example.com"
    assert body["onboarding_step"] == "needs_voice"
    assert body["pending_invitation_count"] == 0


@needs_db
def test_user_without_a_name_needs_profile(client, make_user):
    _, auth = make_user(name="   ")
    assert client.get("/api/v1/me", headers=auth).json()["onboarding_step"] == (
        "needs_profile"
    )


@needs_db
def test_update_me_sets_name_and_clears_title(client, make_user):
    _, auth = make_user(name="   ")
    body = client.patch(
        "/api/v1/me", json={"display_name": " New Name ", "title": "PhD"}, headers=auth
    ).json()
    assert (body["display_name"], body["title"]) == ("New Name", "PhD")
    assert body["onboarding_step"] == "needs_voice"
    body = client.patch("/api/v1/me", json={"title": "  "}, headers=auth).json()
    assert body["title"] is None and body["display_name"] == "New Name"


@needs_db
def test_blank_display_name_is_rejected(client, make_user):
    _, auth = make_user()
    response = client.patch("/api/v1/me", json={"display_name": " "}, headers=auth)
    assert response.status_code == 400


@needs_db
def test_token_for_a_deleted_account_is_rejected(client):
    auth = {"Authorization": f"Bearer {make_token(uuid.uuid4())}"}
    response = client.get("/api/v1/me", headers=auth)
    assert response.status_code == 401
    assert response.json()["detail"] == "profile_missing"


@needs_db
def test_pending_invitations_are_counted(client, make_user):
    user_id, auth = make_user()
    with psycopg.connect(DATABASE_URL) as conn:
        project_id = conn.execute(
            "INSERT INTO projects (name) VALUES ('pytest auth') RETURNING id"
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO project_invitations (project_id, email, token_hash, "
            "expires_at) VALUES (%s, %s, %s, now() + interval '7 days')",
            (project_id, f"pytest-{user_id}@example.com", os.urandom(32)),
        )
    assert client.get("/api/v1/me", headers=auth).json()[
        "pending_invitation_count"
    ] == (1)


@needs_db
def test_without_supabase_url_returns_503(tmp_path):
    app = create_app(tmp_path, tmp_path, database_url=DATABASE_URL)
    with TestClient(app) as client:
        response = client.get("/api/v1/me", headers={"Authorization": "Bearer x"})
    assert response.status_code == 503
