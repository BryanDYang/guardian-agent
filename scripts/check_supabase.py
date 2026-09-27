"""Smoke test: the backend can write to and read from the Supabase database."""

import os

import psycopg

with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    tables = conn.execute(
        "SELECT count(*) FILTER (WHERE relrowsecurity), count(*) FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = 'public' AND c.relkind = 'r'"
    ).fetchone()
    print(f"RLS enabled on {tables[0]} of {tables[1]} tables")
    project_id = conn.execute(
        "INSERT INTO projects (name) VALUES ('connection test') RETURNING id"
    ).fetchone()[0]
    name = conn.execute("SELECT name FROM projects WHERE id = %s", (project_id,)).fetchone()[0]
    print(f"Wrote and read back project: {name}")
    conn.rollback()  # leave no test data behind
print("Supabase connection OK")