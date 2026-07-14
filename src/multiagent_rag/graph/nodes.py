"""The graph's nodes: supervisor, RAG agent, SQL agent.

Each node is a plain function ``(state) -> dict`` returning a partial state update
(LangGraph 1.x). Nodes only write their own section of the state (Rule 5).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from multiagent_rag import llm
from multiagent_rag.config import settings
from multiagent_rag.graph.state import GraphState
from multiagent_rag.ingest.search import search
from multiagent_rag.sql_agent.query import answer_question


# --- Supervisor: an LLM classifier that routes the question ---------------------
class _Route(BaseModel):
    route: Literal["rag", "sql"]


_ROUTER_SYSTEM = (
    "You route a guest's question to exactly one agent at an accommodation.\n"
    "- 'rag': answered from documents — house rules, how-to guides, amenities, "
    "local attractions, what's nearby, safety, check-in/out info.\n"
    "- 'sql': answered from structured records — bookings, availability, prices, "
    "menus, orders, counts, specific dates.\n"
    "Choose the single best route."
)


def supervise(state: GraphState) -> dict:
    result = llm.structured(
        _ROUTER_SYSTEM, state["question"], _Route, model=settings.router_model, max_tokens=64
    )
    return {"route": result.route}


def route_question(state: GraphState) -> str:
    """Router for add_conditional_edges — returns the name of the next node."""
    return state["route"]


# --- RAG agent: retrieve, then synthesize a grounded answer ---------------------
_RAG_SYSTEM = (
    "You are a helpful accommodation concierge. Answer the guest's question using "
    "ONLY the provided context. If the context does not contain the answer, say you "
    "don't have that information rather than guessing. Be concise and specific."
)


def rag_retrieve(state: GraphState) -> dict:
    hits = search(state["question"], k=4)
    chunks = [
        {"source": src, "title": title, "content": content, "distance": float(dist)}
        for (src, title, content, dist) in hits
    ]
    context = (
        "\n\n".join(f"[{c['title'] or c['source']}]\n{c['content']}" for c in chunks)
        or "(no documents found)"
    )
    answer = llm.text(
        _RAG_SYSTEM,
        f"Question: {state['question']}\n\nContext:\n{context}",
        max_tokens=400,
    )
    return {"retrieval": {"chunks": chunks}, "answer": answer}


# --- SQL agent: safe, read-only text-to-SQL over the structured store -----------
def sql_query(state: GraphState) -> dict:
    sql, rows, answer = answer_question(state["question"])
    return {"sql": {"query": sql, "rows": rows}, "answer": answer}
