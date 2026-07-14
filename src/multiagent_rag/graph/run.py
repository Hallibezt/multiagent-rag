"""Invoke the graph from the command line.

    uv run python -m multiagent_rag.graph.run "how do I use the hot tub?"
    make ask Q="what are the sauna rules, and how many confirmed bookings do we have?"
"""

from __future__ import annotations

import sys

from multiagent_rag.graph.build import graph
from multiagent_rag.tracing import callbacks, flush


def main() -> None:
    question = " ".join(sys.argv[1:]).strip() or "how do I use the hot tub?"
    result = graph.invoke({"question": question}, config={"callbacks": callbacks()})
    flush()  # a one-shot CLI run: make sure the trace is sent before we exit

    print(f"Q: {question}")
    print(f"routed to: {result.get('route')}")
    print(f"answer: {' '.join(result.get('answer', '').split())[:500]}")

    chunks = (result.get("retrieval") or {}).get("chunks") or []
    if chunks:
        print("doc sources: " + ", ".join(c["source"] for c in chunks[:3]))
    sql = result.get("sql") or {}
    if sql.get("query"):
        print("sql: " + " ".join(sql["query"].split()))


if __name__ == "__main__":
    main()
