# multiagent-rag

A deployable **multi-agent RAG service** built on the supervisor / orchestrator-worker
pattern: a supervisor routes each question to the agent that should answer it — semantic
retrieval over documents, or text-to-SQL over structured tables — and merges the result.

The emphasis is on **operating** such a system in production: persistent checkpointed state,
observability, containerisation, and network-scoped deployment — not on agent cleverness.

> **Status:** Phase 0 (ingestion) in progress. See [Roadmap](docs/plans/product-roadmap.md).

## Architecture

```
  question ──► FastAPI ──► LangGraph
                            ├─ supervisor        (classify + route)
                            ├─ RAG agent   ──► doc-store   (Postgres + pgvector)
                            └─ SQL agent   ──► sql-store   (Postgres, structured)
                            state checkpointed to Postgres  (resume after a crash)
                            every step traced (Langfuse / LangSmith)
```

The document store and the structured store are **separate Postgres endpoints** by design,
so agent reach can be network-scoped (a Kubernetes NetworkPolicy proves the SQL agent
cannot reach the document store).

## Stack

Python 3.13 · [uv](https://docs.astral.sh/uv/) · Postgres 17 + [pgvector](https://github.com/pgvector/pgvector) ·
[fastembed](https://github.com/qdrant/fastembed) (local, keyless embeddings) · psycopg 3 ·
pydantic-settings · Docker Compose. LangGraph + FastAPI arrive in Phases 1–2.

## Quickstart

Prerequisites: **Docker** and **uv**.

```bash
uv sync                     # create the venv, install pinned deps
cp .env.example .env        # local-dev defaults (no secrets required)
make up                     # start Postgres + pgvector, wait until healthy
make smoke                  # prove the stack end-to-end (DB + pgvector + embeddings)
```

`make smoke` needs no API keys — embeddings run locally via fastembed.

## Layout

```
docker-compose.yml          two Postgres stores (doc + sql)
db/doc-store/init/          pgvector extension bootstrap
src/multiagent_rag/
  config.py                 injected settings (data sources, embedding model)
  db.py                     psycopg + pgvector connection helper
  smoke.py                  end-to-end Phase 0 check
docs/plans/                 roadmap
Makefile                    up / down / smoke / psql / lint
```

## Phases

0. **Ingestion** — pgvector store; a real corpus chunked + embedded; similarity queries work.
1. **The graph** — supervisor + RAG + SQL agents over shared typed state.
2. **Service / MLOps** — FastAPI; Postgres-checkpointed state (resumes after a crash); tracing.
3. **Operations** — containerise; deploy to Kubernetes; health checks; NetworkPolicy scoping.
