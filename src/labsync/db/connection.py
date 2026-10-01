"""Postgres connection pool for the backend (Supabase via the session pooler)."""

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


def create_pool(database_url: str) -> ConnectionPool:
    """Rows come back as dicts. Each borrowed connection commits on success
    and rolls back if the request raises."""
    return ConnectionPool(
        database_url,
        min_size=1,
        max_size=5,
        kwargs={"row_factory": dict_row},
        open=True,
    )
