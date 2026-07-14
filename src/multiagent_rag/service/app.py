"""FastAPI service in front of the checkpointed graph.

A web server handles requests on worker threads, and psycopg connections are not
thread-safe — so the checkpointer is backed by a **connection pool** (each thread
borrows its own connection). The pool is opened once in the app lifespan and the
persistent graph is built from it.

Run:  make serve      then POST to http://localhost:8000/ask
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from pydantic import BaseModel

from multiagent_rag.config import settings
from multiagent_rag.graph.build import build_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    # autocommit=True is required by the Postgres saver; prepare_threshold=0 keeps
    # it compatible with poolers.
    pool = ConnectionPool(
        conninfo=settings.checkpoint_dsn,
        max_size=10,
        kwargs={"autocommit": True, "prepare_threshold": 0},
        open=False,
    )
    pool.open()
    checkpointer = PostgresSaver(pool)
    checkpointer.setup()
    app.state.graph = build_graph(checkpointer=checkpointer)
    app.state.pool = pool
    try:
        yield
    finally:
        pool.close()


app = FastAPI(title="multiagent-rag", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str
    thread_id: str | None = None


class AskResponse(BaseModel):
    thread_id: str
    route: str | None
    answer: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest, request: Request) -> AskResponse:
    # A sync endpoint runs in FastAPI's worker threadpool; the pooled checkpointer
    # makes that safe. Pass/receive a thread_id so a run is resumable and remembers.
    thread_id = body.thread_id or f"api-{uuid.uuid4().hex[:8]}"
    result = request.app.state.graph.invoke(
        {"question": body.question},
        {"configurable": {"thread_id": thread_id}},
    )
    return AskResponse(
        thread_id=thread_id,
        route=result.get("route"),
        answer=result.get("answer", ""),
    )
