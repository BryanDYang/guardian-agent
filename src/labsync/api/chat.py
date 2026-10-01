"""/api/v1 project chat: conversations, history, and grounded answers."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from psycopg import Connection
from pydantic import BaseModel, Field

from .. import chat
from ..db import chat as store
from ..db import rag
from .deps import User, get_conn, require_member

router = APIRouter(prefix="/api/v1/conversations", tags=["chat"])
Conn = Annotated[Connection, Depends(get_conn)]

# The phone reaches the Mac through Cloudflare, which drops a response that
# takes longer than 100 seconds.
ANSWER_TIMEOUT = 90


class NewConversation(BaseModel):
    project_id: UUID
    meeting_id: UUID | None = None  # set to search only this meeting


class Question(BaseModel):
    content: Annotated[str, Field(max_length=2000)]


@router.post("", status_code=201)
def create_conversation(body: NewConversation, user: User, conn: Conn) -> dict:
    require_member(conn, user, body.project_id)
    if body.meeting_id is not None and not store.meeting_in_project(
        conn, body.meeting_id, body.project_id
    ):
        raise HTTPException(404, "Meeting not found in this project")
    return store.create_conversation(conn, body.project_id, body.meeting_id, user.id)


@router.get("")
def list_conversations(
    user: User, conn: Conn, project_id: UUID | None = None
) -> list[dict]:
    return store.list_conversations(conn, user.id, project_id)


@router.get("/{conversation_id}")
def get_conversation(conversation_id: UUID, user: User, conn: Conn) -> dict:
    conversation = store.get_conversation(conn, conversation_id, user.id)
    if conversation is None:
        raise HTTPException(404, "Conversation not found")
    return conversation | {"messages": store.list_messages(conn, conversation_id)}


@router.post("/{conversation_id}/messages")
def ask(conversation_id: UUID, body: Question, user: User, request: Request) -> dict:
    """Answer from this conversation's project (or meeting) only. The database
    connection is released while the model runs, and nothing is stored unless
    an answer or a grounded refusal comes back."""
    question = body.content.strip()
    if not question:
        raise HTTPException(400, "Ask a question")
    pool = request.app.state.pool
    if pool is None:
        raise HTTPException(503, "Database is not configured; set DATABASE_URL")
    with pool.connection() as conn:
        conversation = store.get_conversation(conn, conversation_id, user.id)
        if conversation is None:
            raise HTTPException(404, "Conversation not found")
        history = store.list_messages(conn, conversation_id, chat.HISTORY_MESSAGES)
        query = chat.retrieval_text(question, history)
        try:
            [vector] = request.app.state.embedder.encode([query])
        except RuntimeError as exc:
            raise HTTPException(503, str(exc)) from exc
        hits = rag.search(
            conn,
            project_id=conversation["project_id"],
            meeting_id=conversation["meeting_id"],
            text=query,
            vector=vector,
            limit=chat.SEARCH_LIMIT,
        )
        sources = chat.build_sources(conn, hits)

    settings = request.app.state.chat
    try:
        answer, citations = chat.answer(
            question,
            history,
            sources,
            provider=settings["provider"],
            model=settings["model"],
            timeout=ANSWER_TIMEOUT,
        )
    except RuntimeError as exc:
        raise HTTPException(502, str(exc)) from exc

    with pool.connection() as conn:
        # Checked again: the conversation may have been deleted, or this user
        # removed from the project, while the model was answering.
        if store.get_conversation(conn, conversation_id, user.id) is None:
            raise HTTPException(404, "Conversation was deleted")
        asked, answered = store.add_exchange(
            conn, conversation_id, question, answer, citations
        )
    return {"user_message": asked, "assistant_message": answered}
