"""Assemble and compile the supervisor graph (LangGraph 1.x).

    START -> supervisor -> (route) --> rag ---\\
                              |               --> synthesize -> END
                              \\-------> sql --/

The supervisor routes to `rag`, `sql`, or (for a "both" question) BOTH in parallel;
`synthesize` fans them in and composes the final answer.

`build_graph` optionally takes a `checkpointer` (Phase 2 — persist state to Postgres
so a crashed run resumes) and `interrupt_before` (pause before given nodes).
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from multiagent_rag.graph.nodes import (
    rag_retrieve,
    route_question,
    sql_query,
    supervise,
    synthesize,
)
from multiagent_rag.graph.state import GraphState


def build_graph(checkpointer=None, interrupt_before=None):
    builder = StateGraph(GraphState)
    builder.add_node("supervisor", supervise)
    builder.add_node("rag", rag_retrieve)
    builder.add_node("sql", sql_query)
    builder.add_node("synthesize", synthesize)

    builder.add_edge(START, "supervisor")
    # A list path_map declares the possible destinations; the router returns one
    # of them, or a list of them (parallel fan-out).
    builder.add_conditional_edges("supervisor", route_question, ["rag", "sql"])
    builder.add_edge("rag", "synthesize")
    builder.add_edge("sql", "synthesize")
    builder.add_edge("synthesize", END)

    return builder.compile(checkpointer=checkpointer, interrupt_before=interrupt_before or [])


# Compiled once on import — the CLI (`make ask`) uses this in-memory (no persistence).
graph = build_graph()
