"""The graph's nodes: supervisor, RAG + SQL workers, and a synthesizer.

Design: the **workers gather evidence** (the RAG agent retrieves chunks, the SQL
agent runs a query) and the single **synthesize** node composes the final answer.
That split makes the "both" route a clean parallel fan-out → fan-in.

Each node is a plain function ``(state) -> dict`` returning a partial state update
(LangGraph 1.x); each writes only its own section of the state (Rule 5).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from multiagent_rag import llm
from multiagent_rag.config import settings
from multiagent_rag.graph.state import GraphState
from multiagent_rag.ingest.search import search
from multiagent_rag.sql_agent.query import remote_query, run_query


# --- Supervisor: an LLM classifier that routes the question ---------------------
class _Route(BaseModel):
    route: Literal["rag", "sql", "both"]


_ROUTER_SYSTEM = (
    "You route a guest's question to the agent(s) that can answer it.\n"
    "- 'rag': from documents — house rules, how-to guides, amenities, local "
    "attractions, what's nearby, safety, check-in/out info.\n"
    "- 'sql': from structured records — bookings, availability, prices, menus, "
    "orders, counts, specific dates.\n"
    "- 'both': the question has two parts that need each source (a document part "
    "AND a records part).\n"
    "Choose 'both' only when the question genuinely needs both."
)


def supervise(state: GraphState) -> dict:
    result = llm.structured(
        _ROUTER_SYSTEM, state["question"], _Route, model=settings.router_model, max_tokens=64
    )
    return {"route": result.route}


def route_question(state: GraphState) -> str | list[str]:
    """Router for add_conditional_edges. Returning a LIST fans out in parallel."""
    return ["rag", "sql"] if state["route"] == "both" else state["route"]


# --- RAG worker: semantic retrieval (no answer — that's synthesize's job) -------
def rag_retrieve(state: GraphState) -> dict:
    hits = search(state["question"], k=4)
    chunks = [
        {"source": src, "title": title, "content": content, "distance": float(dist)}
        for (src, title, content, dist) in hits
    ]
    return {"retrieval": {"chunks": chunks}}


# --- SQL worker: safe read-only text-to-SQL (returns query + rows) --------------
# In-process by default; when SQL_AGENT_URL is set, delegate to the separately
# deployed SQL-agent pod so a NetworkPolicy can fence it off from the doc store.
def sql_query(state: GraphState) -> dict:
    if settings.sql_agent_url:
        sql, rows = remote_query(state["question"], settings.sql_agent_url)
    else:
        sql, rows = run_query(state["question"])
    return {"sql": {"query": sql, "rows": rows}}


# --- Synthesizer: compose the final answer from whatever evidence was gathered --
_SYNTH_SYSTEM = (
    "You are a helpful accommodation concierge. Answer the guest's question using "
    "ONLY the evidence provided below — retrieved documents and/or database query "
    "results. If part of the question isn't covered by the evidence, say so rather "
    "than guessing. Be concise and specific."
)


def synthesize(state: GraphState) -> dict:
    parts: list[str] = []

    chunks = (state.get("retrieval") or {}).get("chunks") or []
    if chunks:
        docs = "\n\n".join(f"[{c['title'] or c['source']}]\n{c['content']}" for c in chunks)
        parts.append(f"Retrieved documents:\n{docs}")

    sql = state.get("sql") or {}
    if sql.get("rows") is not None:
        parts.append(f"Database query:\n{sql.get('query')}\nResult rows: {sql['rows']}")

    evidence = "\n\n---\n\n".join(parts) or "(no evidence gathered)"
    answer = llm.text(
        _SYNTH_SYSTEM,
        f"Question: {state['question']}\n\nEvidence:\n{evidence}",
        max_tokens=500,
    )
    return {"answer": answer}
