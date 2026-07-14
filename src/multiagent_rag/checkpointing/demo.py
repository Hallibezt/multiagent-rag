"""Demonstrate crash recovery: a run interrupted mid-flight resumes from its
Postgres checkpoint — WITHOUT re-running the agents that already finished.

We compile with ``interrupt_before=["synthesize"]`` so the run pauses after the
workers. Their results are checkpointed to Postgres. We then open a SEPARATE saver
(a fresh "process"), confirm the state survived, and resume — only `synthesize`
runs; the workers do not.

Run:  make checkpoint-demo
"""

from __future__ import annotations

import uuid

from langgraph.checkpoint.postgres import PostgresSaver

from multiagent_rag.config import settings
from multiagent_rag.graph.build import build_graph

QUESTION = "what are the sauna rules, and how many confirmed bookings do we have?"


def main() -> None:
    thread_id = f"demo-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}
    print(f"thread_id = {thread_id}\nquestion  = {QUESTION}\n")

    # --- Process 1: run the workers, pause before synthesize, then 'crash' ---
    with PostgresSaver.from_conn_string(settings.checkpoint_dsn) as cp:
        cp.setup()  # creates the checkpoint tables on first use
        graph = build_graph(checkpointer=cp, interrupt_before=["synthesize"])
        graph.invoke({"question": QUESTION}, config)
        snap = graph.get_state(config)
        print("[process 1] ran the workers, paused before:", snap.next)
        print("  checkpointed state keys:", sorted(snap.values.keys()))
        print("  answer produced yet? ", "answer" in snap.values)
    print("  -- process 1 exits; its connection is closed --\n")

    # --- Process 2: a fresh saver + fresh graph. State must come back from Postgres. ---
    with PostgresSaver.from_conn_string(settings.checkpoint_dsn) as cp2:
        graph2 = build_graph(checkpointer=cp2, interrupt_before=["synthesize"])
        restored = graph2.get_state(config)
        print("[process 2] fresh process — state restored from Postgres:")
        print("  pending next node:", restored.next)
        print(
            "  workers' results survived? retrieval:",
            "retrieval" in restored.values,
            "| sql:",
            "sql" in restored.values,
        )
        # Resume: `None` input continues from the interrupt point.
        result = graph2.invoke(None, config)
        print("\n[process 2] resumed — synthesize ran, final answer:")
        print(" ", " ".join(result.get("answer", "").split())[:400])


if __name__ == "__main__":
    main()
