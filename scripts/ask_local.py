"""Ask the local test project a question end to end: search, model, verify."""

import sys

import psycopg
from psycopg.rows import dict_row

from labsync import chat
from labsync.db import rag
from labsync.embeddings import OpenAIEmbedder
from labsync.providers import default_provider

LOCAL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
question = " ".join(sys.argv[1:])

[vector] = OpenAIEmbedder().encode([question])
with psycopg.connect(LOCAL, row_factory=dict_row) as conn:
    project = conn.execute(
        "SELECT id FROM projects WHERE name = 'Local RAG test'"
    ).fetchone()
    hits = rag.search(
        conn,
        project_id=project["id"],
        meeting_id=None,
        text=question,
        vector=vector,
        limit=chat.SEARCH_LIMIT,
    )
    sources = chat.build_sources(conn, hits)

answer, citations = chat.answer(
    question, [], sources, provider=default_provider(), model=None, timeout=90
)
print(answer)
for c in citations:
    at = chat.clock(c["start_time_ms"]) if c["start_time_ms"] is not None else "-"
    print(f'  [{c["number"]}] {c["meeting_name"]} @ {at} ({c["kind"]}): "{c["quote"]}"')