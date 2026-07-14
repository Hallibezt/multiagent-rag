"""The graph's nodes: supervisor, RAG agent, SQL agent.

Each node is a plain function ``(state) -> dict`` returning a partial state update
(LangGraph 1.x). Nodes only write their own section of the state (Rule 5).
"""

from __future__ import annotations

from multiagent_rag.graph.state import GraphState
from multiagent_rag.ingest.search import search

# --- Supervisor -----------------------------------------------------------------
# PLACEHOLDER heuristic router. This is deliberately dumb for now; it gets replaced
# by an LLM classifier once the Claude API is grounded (Rule 1). It exists so the
# graph structure + routing are provable today with zero secrets.
_SQL_HINTS = (
    "booking", "book a", "available", "availability", "reserve", "reservation",
    "how much", "how many", "price", "cost", "cheapest", "menu", "order",
    "revenue", "total", "count",
)


def supervise(state: GraphState) -> dict:
    q = state["question"].lower()
    route = "sql" if any(h in q for h in _SQL_HINTS) else "rag"
    return {"route": route}


def route_question(state: GraphState) -> str:
    """Router for add_conditional_edges — returns the name of the next node."""
    return state["route"]


# --- RAG agent ------------------------------------------------------------------
def rag_retrieve(state: GraphState) -> dict:
    """Semantic retrieval over the pgvector doc store (wraps the Phase 0 search).
    For now the 'answer' is the top chunk (extractive); LLM synthesis is added
    once the Claude API is grounded."""
    hits = search(state["question"], k=4)
    chunks = [
        {"source": src, "title": title, "content": content, "distance": float(dist)}
        for (src, title, content, dist) in hits
    ]
    answer = chunks[0]["content"] if chunks else "No relevant document found."
    return {"retrieval": {"chunks": chunks}, "answer": answer}


# --- SQL agent ------------------------------------------------------------------
def sql_query(state: GraphState) -> dict:
    """STUB. GuestPad's transactional tables are empty, so real text-to-SQL and a
    synthetic dataset land in the next increment."""
    return {
        "sql": {
            "note": "SQL agent stub — GuestPad transactional tables are empty; "
            "synthetic data + text-to-SQL come next."
        },
        "answer": "(SQL agent not wired yet — needs synthetic transactional data.)",
    }
