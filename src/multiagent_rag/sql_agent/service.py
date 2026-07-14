"""Standalone SQL-agent service (Phase 3 isolation).

Runs text-to-SQL against the sql-store as its OWN process/pod, so a Kubernetes
NetworkPolicy can fence it to the sql-store and DENY the doc-store — making
"the SQL agent cannot reach the document store" a provable network fact.

The graph's SQL node calls `POST /query` here when `SQL_AGENT_URL` is set; with
it unset the node runs `run_query` in-process (so local `make ask` needs nothing
extra). Same container image as the API — the k8s command selects this module.

Run:  make serve-sql-agent    (listens on :8081)
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from multiagent_rag.sql_agent.query import run_query

app = FastAPI(title="multiagent-rag-sql-agent")


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    sql: str
    rows: list[dict]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(body: QueryRequest) -> QueryResponse:
    sql, rows = run_query(body.question)
    return QueryResponse(sql=sql, rows=rows)
