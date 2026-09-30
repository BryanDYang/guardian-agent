"""Search the local test project from the command line."""

import sys

import psycopg
from psycopg.rows import dict_row

from labsync.db import rag
from labsync.embeddings import OpenAIEmbedder

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
        limit=5,
    )
for hit in hits:
    where = hit["kind"]
    if where == "transcript":
        where = f"turns {hit['first_turn_order']}-{hit['last_turn_order']}"
    if hit["start_time_ms"] is not None:
        where += f" @ {hit['start_time_ms'] // 1000}s"
    print(f"\n{float(hit['score']):.4f}  {where}")
    print("   " + hit["content"][:240].replace("\n", "\n   "))