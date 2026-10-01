"""Accounts and membership schema (Accounts & Voice Identity spec, Phase 1).

Runs against a local database only, e.g. after `supabase start`:
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
Never point this at the Supabase project. Every test rolls back."""

import os
import uuid

import psycopg
import pytest
from psycopg.types.json import Jsonb

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")


@pytest.fixture
def conn():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.transaction(force_rollback=True):
            yield conn


def add_auth_user(conn, email, user_meta=None, provider="email"):
    """Insert the way Supabase Auth does; the trigger should create the profile."""
    user_id = uuid.uuid4()
    conn.execute(
        "INSERT INTO auth.users (id, email, raw_user_meta_data, raw_app_meta_data) "
        "VALUES (%s, %s, %s, %s)",
        (user_id, email, Jsonb(user_meta or {}), Jsonb({"provider": provider})),
    )
    return user_id


def profile(conn, user_id):
    return conn.execute(
        "SELECT email, display_name, auth_provider, onboarding_completed_at "
        "FROM profiles WHERE id = %s",
        (user_id,),
    ).fetchone()


def add_project(conn, created_by=None):
    return conn.execute(
        "INSERT INTO projects (name, created_by) VALUES ('pytest accounts', %s) "
        "RETURNING id",
        (created_by,),
    ).fetchone()[0]


def add_invitation(conn, project_id, email, status="pending"):
    conn.execute(
        "INSERT INTO project_invitations "
        "(project_id, email, token_hash, status, expires_at, resolved_at) "
        "VALUES (%s, %s, %s, %s, now() + interval '7 days', "
        "CASE WHEN %s = 'pending' THEN NULL ELSE now() END)",
        (project_id, email, os.urandom(32), status, status),
    )


def test_email_signup_creates_profile(conn):
    user_id = add_auth_user(conn, "Test.One@Example.com", {"full_name": "  Test One "})
    assert profile(conn, user_id) == ("test.one@example.com", "Test One", "email", None)


def test_google_signup_uses_name_and_provider(conn):
    user_id = add_auth_user(conn, "gina@gmail.com", {"name": "Gina G"}, "google")
    assert profile(conn, user_id) == ("gina@gmail.com", "Gina G", "google", None)


def test_blank_name_is_stored_as_null(conn):
    user_id = add_auth_user(conn, "blank@example.com", {"full_name": "   "})
    assert profile(conn, user_id)[1] is None


def test_email_change_updates_profile(conn):
    user_id = add_auth_user(conn, "old@example.com")
    conn.execute(
        "UPDATE auth.users SET email = 'New@Example.com' WHERE id = %s", (user_id,)
    )
    assert profile(conn, user_id)[0] == "new@example.com"


def test_deleting_user_removes_private_rows_and_keeps_shared_content(conn):
    user_id = add_auth_user(conn, "leaver@example.com")
    project_id = add_project(conn, created_by=user_id)
    conn.execute(
        "INSERT INTO project_members (project_id, user_id, role) "
        "VALUES (%s, %s, 'owner')",
        (project_id, user_id),
    )
    conn.execute(
        "INSERT INTO chat_conversations (project_id, user_id) VALUES (%s, %s)",
        (project_id, user_id),
    )

    conn.execute("DELETE FROM auth.users WHERE id = %s", (user_id,))

    assert profile(conn, user_id) is None
    counts = conn.execute(
        "SELECT (SELECT count(*) FROM project_members WHERE project_id = %s), "
        "(SELECT count(*) FROM chat_conversations WHERE project_id = %s)",
        (project_id, project_id),
    ).fetchone()
    assert counts == (0, 0)
    created_by = conn.execute(
        "SELECT created_by FROM projects WHERE id = %s", (project_id,)
    ).fetchone()[0]
    assert created_by is None


def test_membership_role_is_checked(conn):
    user_id = add_auth_user(conn, "role@example.com")
    project_id = add_project(conn)
    with pytest.raises(psycopg.errors.CheckViolation), conn.transaction():
        conn.execute(
            "INSERT INTO project_members (project_id, user_id, role) "
            "VALUES (%s, %s, 'admin')",
            (project_id, user_id),
        )


def test_one_pending_invitation_per_email(conn):
    project_id = add_project(conn)
    add_invitation(conn, project_id, "invitee@example.com")
    with pytest.raises(psycopg.errors.UniqueViolation), conn.transaction():
        add_invitation(conn, project_id, "invitee@example.com")
    # A resolved invitation does not block a new one.
    conn.execute(
        "UPDATE project_invitations SET status = 'revoked', resolved_at = now() "
        "WHERE project_id = %s",
        (project_id,),
    )
    add_invitation(conn, project_id, "invitee@example.com")


def test_invitation_email_must_be_lowercase(conn):
    project_id = add_project(conn)
    with pytest.raises(psycopg.errors.CheckViolation), conn.transaction():
        add_invitation(conn, project_id, "Invitee@Example.com")


def test_every_public_table_has_rls_and_no_policies(conn):
    open_tables = conn.execute(
        "SELECT c.relname FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = 'public' AND c.relkind = 'r' AND NOT c.relrowsecurity"
    ).fetchall()
    assert open_tables == []
    policies = conn.execute(
        "SELECT count(*) FROM pg_policies WHERE schemaname = 'public'"
    ).fetchone()[0]
    assert policies == 0


def test_trigger_functions_are_not_callable_by_app_roles(conn):
    for function in ("handle_new_user()", "handle_user_email_change()"):
        for role in ("anon", "authenticated"):
            allowed = conn.execute(
                "SELECT has_function_privilege(%s, %s, 'EXECUTE')",
                (role, f"public.{function}"),
            ).fetchone()[0]
            assert not allowed, f"{role} can execute {function}"
