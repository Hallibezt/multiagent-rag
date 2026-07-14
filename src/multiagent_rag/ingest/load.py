"""Load the seed documents into the pgvector doc store: chunk, embed, insert.

Reads ``data/seed/documents.jsonl`` (no GuestPad access needed), embeds each
chunk locally with fastembed, and (re)builds the ``documents`` table with an
HNSW cosine index.

Run:   make ingest    (or  uv run python -m multiagent_rag.ingest.load)
"""

from __future__ import annotations

import json
import pathlib

from fastembed import TextEmbedding
from psycopg.types.json import Jsonb

from multiagent_rag.config import settings
from multiagent_rag.db import connect

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
SEED_PATH = REPO_ROOT / "data" / "seed" / "documents.jsonl"


def chunk(text: str, size: int = 600, overlap: int = 100) -> list[str]:
    """Split long text into overlapping windows. Most GuestPad records are short
    and come back as a single chunk; only the longer markdown guides get split.
    (A sentence/markdown-aware splitter is a later refinement.)"""
    text = text.strip()
    if len(text) <= size:
        return [text]
    out: list[str] = []
    start = 0
    while start < len(text):
        end = start + size
        out.append(text[start:end].strip())
        if end >= len(text):
            break
        start = end - overlap
    return [c for c in out if c]


def main() -> None:
    dim = int(settings.embedding_dim)
    ddl = f"""
    CREATE TABLE IF NOT EXISTS documents (
        id           bigserial PRIMARY KEY,
        source_table text NOT NULL,
        source_id    text NOT NULL,
        property_id  text,
        lang         text NOT NULL DEFAULT 'en',
        title        text,
        content      text NOT NULL,
        chunk_index  int  NOT NULL DEFAULT 0,
        metadata     jsonb NOT NULL DEFAULT '{{}}',
        embedding    vector({dim}) NOT NULL,
        UNIQUE (source_table, source_id, chunk_index)
    );
    """
    index_sql = (
        "CREATE INDEX IF NOT EXISTS documents_embedding_idx "
        "ON documents USING hnsw (embedding vector_cosine_ops)"
    )

    with SEED_PATH.open(encoding="utf-8") as f:
        docs = [json.loads(line) for line in f]

    # Fan each document out into chunks. We embed "title + chunk" so the title's
    # context sharpens retrieval, but store only the chunk text as `content`.
    rows: list[dict] = []
    to_embed: list[str] = []
    for d in docs:
        for i, ch in enumerate(chunk(d["content"])):
            rows.append({**d, "chunk_index": i, "chunk_text": ch})
            to_embed.append(f"{d['title']}\n\n{ch}" if d.get("title") else ch)

    print(
        f"embedding {len(to_embed)} chunks from {len(docs)} documents ({settings.embedding_model})..."
    )
    model = TextEmbedding(model_name=settings.embedding_model)
    vectors = list(model.embed(to_embed))

    params = [
        (
            r["source_table"],
            r["source_id"],
            r.get("property_id"),
            r.get("lang", "en"),
            r.get("title"),
            r["chunk_text"],
            r["chunk_index"],
            Jsonb(r.get("metadata") or {}),
            vec,
        )
        for r, vec in zip(rows, vectors)
    ]

    with connect(settings.doc_store_dsn) as conn, conn.cursor() as cur:
        cur.execute(ddl)
        cur.execute("TRUNCATE documents RESTART IDENTITY")
        cur.executemany(
            "INSERT INTO documents "
            "(source_table, source_id, property_id, lang, title, content, chunk_index, metadata, embedding) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            params,
        )
        cur.execute(index_sql)
        cur.execute("SELECT count(*) FROM documents")
        total = cur.fetchone()[0]
    print(f"ingested {total} chunks into the doc store (HNSW cosine index built).")


if __name__ == "__main__":
    main()
