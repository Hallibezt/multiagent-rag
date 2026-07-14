"""The shared, typed state that flows through the graph.

CLAUDE.md Rule 5: nested, typed, with clear per-agent ownership — NOT one flat
dict. Rule 4 seam #2: the envelope is domain-neutral (it never mentions "hot tub"
or "aurora"), so a different data domain reuses it unchanged.

LangGraph 1.x model: each top-level key has its own reducer. We don't declare
custom reducers here, so every key uses the default (overwrite) — each node
writes its own section and nothing clobbers another agent's.
"""

from __future__ import annotations

from typing import Any, TypedDict


class Retrieval(TypedDict, total=False):
    """The RAG agent's workspace."""

    chunks: list[dict[str, Any]]


class Sql(TypedDict, total=False):
    """The SQL agent's workspace."""

    query: str
    rows: list[dict[str, Any]]
    note: str


class GraphState(TypedDict, total=False):
    question: str  # input
    route: str  # supervisor's decision: "rag" | "sql"
    retrieval: Retrieval  # owned by the RAG agent
    sql: Sql  # owned by the SQL agent
    answer: str  # the final answer
