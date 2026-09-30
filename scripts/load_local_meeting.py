"""Copy one processed meeting from artifacts/ into LOCAL Supabase and index it."""

import json
import sys
from datetime import date
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from labsync.db import meetings, rag
from labsync.embeddings import OpenAIEmbedder
from labsync.extraction import Transcript

LOCAL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"  # never hosted
PROJECT = "Local RAG test"

folder = Path(sys.argv[1])  # artifacts/server/<meeting id>
attempt = max(
    (path.parent for path in folder.glob("attempt-*/extraction.json")),
    key=lambda path: int(path.name.split("-")[1]),  # attempt-10 after attempt-9
)
record = json.loads((folder / "meeting.json").read_text())
transcript = Transcript.model_validate_json((attempt / "transcript.json").read_text())
result = json.loads((attempt / "extraction.json").read_text())

with psycopg.connect(LOCAL, row_factory=dict_row) as conn:
    conn.execute("DELETE FROM meetings WHERE id = %s", (transcript.meeting_id,))
    project = conn.execute(
        "SELECT id FROM projects WHERE name = %s", (PROJECT,)
    ).fetchone() or conn.execute(
        "INSERT INTO projects (name) VALUES (%s) RETURNING id", (PROJECT,)
    ).fetchone()
    meetings.create_meeting(
        conn,
        meeting_id=transcript.meeting_id,
        project_id=project["id"],
        name=record["title"],
        meeting_date=date.fromisoformat(record["date"]),
        audio_file_path=str(folder / record["filename"]),
    )
    meetings.save_results(conn, transcript.meeting_id, transcript, result, {})
    meetings.update_status(conn, transcript.meeting_id, "completed", 1, None)
    count = rag.index_meeting(conn, transcript.meeting_id, OpenAIEmbedder())
    print(f"Loaded {record['title']!r} into project {project['id']}: {count} chunks")