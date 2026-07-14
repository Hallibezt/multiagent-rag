"""Assemble and compile the supervisor graph (LangGraph 1.x).

    START -> supervisor -> (route) --> rag ---\\
                              |               --> synthesize -> END
                              \\-------> sql --/

The supervisor routes to `rag`, `sql`, or (for a "both" question) BOTH in parallel;
`synthesize` fans them in and composes the final answer.
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


def build_graph():
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

    return builder.compile()


# Compiled once on import.
graph = build_graph()
