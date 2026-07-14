"""Similarity search over the doc store — the Phase 0 gate.

Embeds the query with the same local model, then finds the nearest chunks by
cosine distance (pgvector's ``<=>``).

Usage:
    uv run python -m multiagent_rag.ingest.search "how do I use the hot tub?"
    make search Q="which waterfall can I walk behind?"
"""

from __future__ import annotations

import sys

from fastembed import TextEmbedding

from multiagent_rag.config import settings
from multiagent_rag.db import connect


def search(query: str, k: int = 5) -> list[tuple]:
    model = TextEmbedding(model_name=settings.embedding_model)
    (qvec,) = list(model.embed([query]))
    with connect(settings.doc_store_dsn) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT source_table, title, content, embedding <=> %s AS distance
            FROM documents
            ORDER BY embedding <=> %s
            LIMIT %s
            """,
            (qvec, qvec, k),
        )
        return cur.fetchall()


def main() -> None:
    query = " ".join(sys.argv[1:]).strip() or "how do I use the hot tub?"
    print(f"query: {query!r}\n")
    for source_table, title, content, distance in search(query):
        snippet = " ".join(content.split())[:150]
        print(f"  [{distance:.3f}] {source_table} — {title or '(no title)'}")
        print(f"          {snippet}")


if __name__ == "__main__":
    main()
