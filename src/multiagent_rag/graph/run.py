"""Invoke the graph from the command line.

    uv run python -m multiagent_rag.graph.run "how do I use the hot tub?"
    make ask Q="which tours can I book?"
"""

from __future__ import annotations

import sys

from multiagent_rag.graph.build import graph


def main() -> None:
    question = " ".join(sys.argv[1:]).strip() or "how do I use the hot tub?"
    result = graph.invoke({"question": question})

    print(f"Q: {question}")
    print(f"routed to: {result.get('route')}")
    print(f"answer: {' '.join(result.get('answer', '').split())[:280]}")

    chunks = result.get("retrieval", {}).get("chunks", [])
    if chunks:
        print("top sources:")
        for c in chunks[:3]:
            print(f"  [{c['distance']:.3f}] {c['source']} — {c['title'] or '(no title)'}")


if __name__ == "__main__":
    main()
