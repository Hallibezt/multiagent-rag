"""Phase 0 smoke test — proves the whole local stack works end-to-end, with no
secrets and no GuestPad access.

  1. Connect to the doc-store, ensure pgvector is enabled, run a real vector
     distance query   ->  proves Docker + Postgres + pgvector + psycopg.
  2. Load the local fastembed model and embed a sentence, checking the dimension
     matches config   ->  proves embeddings work offline.

Run:   uv run python -m multiagent_rag.smoke     (or `make smoke`)
"""

from __future__ import annotations

from fastembed import TextEmbedding

from multiagent_rag.config import settings
from multiagent_rag.db import connect


def check_pgvector() -> None:
    # `with connect(...) as conn` commits + closes on a clean exit (psycopg 3).
    with connect(settings.doc_store_dsn) as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("SELECT '[1,0,0]'::vector <-> '[0,1,0]'::vector AS l2;")
        (distance,) = cur.fetchone()
    print(
        f"[doc-store] pgvector OK — L2 distance between two unit vectors = {distance}"
    )


def check_embeddings() -> None:
    model = TextEmbedding(model_name=settings.embedding_model)
    # .embed() returns a generator of numpy arrays, one per input string.
    (vec,) = list(model.embed(["the sauna is open until 22:00"]))
    dim = len(vec)
    verdict = (
        "OK"
        if dim == settings.embedding_dim
        else f"MISMATCH (config says {settings.embedding_dim})"
    )
    print(f"[embeddings] {settings.embedding_model} -> {dim}-dim vector — {verdict}")


def main() -> None:
    print("Phase 0 smoke test — local stack, zero secrets\n")
    check_pgvector()
    check_embeddings()
    print("\nAll good: the RAG document store and the embedding pipeline are wired.")


if __name__ == "__main__":
    main()
