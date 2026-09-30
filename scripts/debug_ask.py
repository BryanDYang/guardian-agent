"""Show every stage of one question: hits, sources, raw model reply, checks."""

import json
import sys

import psycopg
from psycopg.rows import dict_row

from labsync import chat, providers
from labsync.db import rag
from labsync.embeddings import OpenAIEmbedder

LOCAL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
question = " ".join(sys.argv[1:])

[vector] = OpenAIEmbedder().encode([question])
with psycopg.connect(LOCAL, row_factory=dict_row) as conn:
    counts = conn.execute(
        "SELECT p.id, p.name, count(c.id) AS chunks FROM projects p "
        "LEFT JOIN rag_chunks c ON c.project_id = p.id GROUP BY p.id"
    ).fetchall()
    print("1. projects and chunk counts:")
    for row in counts:
        print(f"   {row['name']!r}: {row['chunks']} chunks")
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

print(f"\n2. {len(hits)} hits -> {len(sources)} sources")
for s in sources[:12]:
    print(f"   [{s.ref}] {s.line[:110]}")
if not sources:
    sys.exit("No sources: the model is never called, so the answer is NO_ANSWER.")

provider = providers.default_provider()
raw = providers.structured(
    chat.build_prompt(question, [], sources),
    chat.ChatAnswer.model_json_schema(),
    provider=provider,
    model=None,
    timeout=90,
)
print(f"\n3. raw reply from {provider}:")
print(json.dumps(raw, indent=2, ensure_ascii=False))

print("\n4. citation checks:")
by_ref = {s.ref: s for s in sources}
for c in raw.get("citations", []):
    source = by_ref.get(c["ref"])
    if source is None:
        print(f"   {c['ref']}: FAIL - that ref was never shown to the model")
    elif chat._squash(c["quote"]) in chat._squash(source.text):
        print(f"   {c['ref']}: ok")
    else:
        print(f"   {c['ref']}: FAIL - quote not found in the source")
        print(f"      quote:  {c['quote']!r}")
        print(f"      source: {source.text[:200]!r}")

print("\n5. final:", chat.finalize(chat.ChatAnswer.model_validate(raw), sources)[0])