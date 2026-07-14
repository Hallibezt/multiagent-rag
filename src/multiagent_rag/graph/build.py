"""Assemble and compile the supervisor graph (LangGraph 1.x).

    START -> supervisor -> (route) -> rag -> END
                              \\----> sql -> END
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from multiagent_rag.graph.nodes import rag_retrieve, route_question, sql_query, supervise
from multiagent_rag.graph.state import GraphState


def build_graph():
    builder = StateGraph(GraphState)
    builder.add_node("supervisor", supervise)
    builder.add_node("rag", rag_retrieve)
    builder.add_node("sql", sql_query)

    builder.add_edge(START, "supervisor")
    builder.add_conditional_edges("supervisor", route_question, {"rag": "rag", "sql": "sql"})
    builder.add_edge("rag", END)
    builder.add_edge("sql", END)

    return builder.compile()


# Compiled once on import.
graph = build_graph()
