# multiagent-rag

A deployable **multi-agent RAG service** on the supervisor / orchestrator-worker pattern: an
LLM supervisor routes each question to the agent that should answer it — **semantic retrieval**
over documents, **text-to-SQL** over structured tables, or **both in parallel** — then merges a
single grounded answer.

The interesting part isn't the agents (a three-node graph is a weekend). It's **operating** one:
persistent checkpointed state that survives a crash, tracing on every run, a real HTTP API,
containerisation, and network-scoped isolation between agents. That production layer is the point.

> **Status:** Phases 0–2 complete and verified. Phase 3 (Kubernetes) in progress — the service is
> containerised and the SQL agent is split into its own pod; the minikube + NetworkPolicy deploy is
> the remaining step. See the [roadmap](docs/plans/product-roadmap.md).

## What it does

- **LLM supervisor** classifies each question into `rag | sql | both` with *validated* structured
  output (it can't emit an invalid route).
- **RAG agent** — semantic search over a pgvector store, answers grounded strictly in retrieved
  context ("say you don't know" rather than hallucinate).
- **SQL agent** — text-to-SQL over structured tables, run **read-only** with SELECT-only validation
  (an LLM writing SQL is a real risk surface).
- **Parallel fan-out** — a compound question runs both agents at once and a synthesizer merges them.
- **Crash recovery** — graph state is checkpointed to Postgres after every step; a run killed
  mid-flight resumes in a fresh process without re-doing completed work.
- **Observability** — every run is traced (self-hosted Langfuse) — route, retrieval, SQL, timings.
- **Isolation-ready** — document store and SQL store are separate endpoints, and the SQL agent can
  run as its own service, so a Kubernetes NetworkPolicy can *prove* it cannot reach the doc store.

## Architecture

```
                    ┌──────────────── FastAPI  (POST /ask) ─────────────────┐
   question ───────►│                                                        │
                    │   LangGraph supervisor graph                           │
                    │     supervisor  ─ LLM classifies the route             │
                    │        │                                               │
                    │        ├──► RAG agent  ──►  doc-store   (Postgres + pgvector)
                    │        ├──► SQL agent  ──►  sql-store   (Postgres, read-only text-to-SQL)
                    │        └──► synthesize ──►  one grounded answer         │
                    └───────────────┬───────────────────────────────────────┘
                     state checkpointed ─► checkpoint-store   (resume after a crash)
                     every run traced   ─► Langfuse
```

Three separate Postgres endpoints on purpose — the two agents' data and the orchestration state
are distinct concerns (and distinct network identities, for Phase 3).

## Quickstart

**Prerequisites:** [Docker](https://www.docker.com/), [uv](https://docs.astral.sh/uv/), and an
**Anthropic (Claude) API key**. The only secret needed is that key — embeddings run locally
(keyless) via [fastembed](https://github.com/qdrant/fastembed), so nothing else phones home.

```bash
git clone https://github.com/Hallibezt/multiagent-rag && cd multiagent-rag
uv sync                          # create the venv, install pinned deps
cp .env.example .env             # then edit .env and set your ANTHROPIC_API_KEY

make up                          # start the 3 Postgres+pgvector stores (waits until healthy)
make ingest                      # embed the committed document corpus into the doc-store
make seed-sql                    # load synthetic transactional data into the sql-store

make ask Q="what are the sauna rules, and how many confirmed bookings do we have?"
```

That last command routes to **both** agents, runs them in parallel, and prints one merged answer
plus the sources and the generated SQL. A run is a couple of Claude calls (a few cents).

## Using it

```bash
# route to the right agent(s)
make ask Q="how do I use the hot tub"            # → rag
make ask Q="how many confirmed bookings"         # → sql
make ask Q="sauna rules, and a free table tonight?"   # → both (parallel, merged)

# semantic retrieval on its own (no LLM)
make search Q="which waterfall can I walk behind"

# crash recovery: pause → checkpoint to Postgres → resume in a fresh process
make checkpoint-demo

# run it as an HTTP service
make serve                                       # then: curl -X POST localhost:8000/ask \
                                                 #   -H 'content-type: application/json' \
                                                 #   -d '{"question":"which vegan mains are on the menu"}'
                                                 # docs at http://localhost:8000/docs

# observability: self-hosted Langfuse (uncomment the LANGFUSE_* keys in .env first)
make langfuse-up                                 # UI at http://localhost:3000

# run the SQL agent as its own isolated service
make serve-sql-agent
SQL_AGENT_URL=http://localhost:8081 make ask Q="total confirmed revenue"
```

`make help`-style command list lives in the `Makefile` (each target has a `##` description).

## Data

The document corpus (house rules, how-to guides, local attractions, ~160 points of interest) is a
**committed, redacted** export from a real accommodation product, so ingestion needs no external
access. The transactional tables (bookings, menus, orders) are **synthetic** demo data — no real
guest information. Everything is reproducible from `make up && make ingest && make seed-sql`.

## Stack

Python 3.13 · [uv](https://docs.astral.sh/uv/) · [LangGraph](https://docs.langchain.com/oss/python/langgraph/) ·
[Claude](https://docs.claude.com/) (Anthropic SDK) · Postgres 17 + [pgvector](https://github.com/pgvector/pgvector) ·
[fastembed](https://github.com/qdrant/fastembed) (local embeddings) · [FastAPI](https://fastapi.tiangolo.com/) ·
psycopg 3 · pydantic-settings · [Langfuse](https://langfuse.com/) (self-hosted) · Docker · Kubernetes.

## Layout

```
docker-compose.yml            three Postgres+pgvector stores (doc / sql / checkpoint)
langfuse/                     self-hosted Langfuse stack (observability)
Dockerfile                    container image (uv build)
src/multiagent_rag/
  config.py                   injected settings (data sources, models, tracing)
  ingest/                     extract → seed → embed → search (Phase 0)
  graph/                      typed state, supervisor + workers + synthesize (Phase 1)
  sql_agent/                  text-to-SQL, synthetic seed, standalone service (Phase 1 / 3)
  checkpointing/              Postgres checkpointer + crash-recovery demo (Phase 2)
  service/                    FastAPI app (Phase 2)
  tracing.py                  Langfuse callback wiring (Phase 2)
docs/plans/                   roadmap
Makefile                      up / ingest / seed-sql / ask / serve / checkpoint-demo / ...
```

## Roadmap

0. **Ingestion** — pgvector store, real corpus chunked + embedded, similarity search ✅
1. **The graph** — LLM supervisor + RAG + SQL agents, parallel fan-out, grounded synthesis ✅
2. **Service / MLOps** — FastAPI, Postgres-checkpointed state (resumes after a crash), tracing ✅
3. **Operations** — containerise ✅, split the SQL agent ✅, deploy to Kubernetes + a NetworkPolicy
   that proves the SQL agent cannot reach the document store *(in progress)*
