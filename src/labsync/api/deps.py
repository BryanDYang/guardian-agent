"""FastAPI dependencies shared by the /api/v1 routers."""

from collections.abc import Iterator

from fastapi import HTTPException, Request
from psycopg import Connection


def get_conn(request: Request) -> Iterator[Connection]:
    pool = request.app.state.pool
    if pool is None:
        raise HTTPException(503, "Database is not configured; set DATABASE_URL")
    with pool.connection() as conn:
        yield conn