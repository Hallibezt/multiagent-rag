# Product Roadmap — Multi-Agent RAG

> Lightweight phase tracker (Session Start reads this). Check items off `[x]` as they land.
> This will be expanded into proper work plans via `/plan` when we start each phase.
> Full rationale lives in `../../CLAUDE.md` and the `multiagent-rag-data-source` memory note.

**Decided:** data source = **GuestPad**. Three-agent supervisor pattern. Three cheap
multi-version seams baked in (CLAUDE.md Rule 4).

---

## Phase 0 — Ingestion
*Done when: a similarity query returns sensible chunks from real GuestPad content.*

- [x] Decide Python project tooling + pin verified versions (Rule 1) — uv + Python 3.13; versions verified against PyPI + locked in `uv.lock`; two-store docker-compose + injected config; smoke test
- [ ] Access to a GuestPad Postgres (pick the property with the richest seed content)
- [ ] Stand up the pgvector table(s)
- [ ] Chunk + embed the GuestPad document columns (see CLAUDE.md → GuestPad Data Map)
- [ ] Similarity query returns sensible chunks  ← **Phase 0 gate**
- [ ] `/learning/01-*` written

## Phase 1 — The graph (core)
*Done when: the example routing questions return correct answers via the correct agent(s).*

- [ ] Define the shared typed state (Rule 5: nested, per-agent ownership)
- [ ] RAG agent node (pgvector retrieval)
- [ ] SQL agent node (text-to-SQL over the scoped tables)
- [ ] Supervisor node (classify + route, incl. fan-out to both)
- [ ] Example routing questions pass  ← **Phase 1 gate**
- [ ] Learning docs written

## Phase 2 — Service / MLOps layer
*Done when: an interrupted run resumes from its checkpoint, and every run is traceable.*

- [ ] FastAPI wrapper around the graph
- [ ] Postgres checkpointing (NOT in-memory)
- [ ] Tracing wired in (Langfuse / LangSmith)
- [ ] Kill a run mid-flight → it resumes from checkpoint  ← **Phase 2 gate**
- [ ] Learning docs written

## Phase 3 — Operations
*Done when: it runs on the cluster, healthy, and the SQL agent provably cannot reach the doc store.*

- [ ] Containerise + health checks
- [ ] Deploy to **minikube** with an enforcing CNI (Calico/Cilium — default minikube does NOT enforce NetworkPolicy) — `--dry-run=server` every manifest first (Rule 1)
- [ ] NetworkPolicy scoping agent reach (stand doc store + SQL DB up as *separate* endpoints so it's enforceable — Rule 4 seam)
- [ ] Prove SQL agent cannot reach the document store  ← **Phase 3 gate**
- [ ] *Stretch:* redeploy the same manifests to GKE or AKS (managed-cloud demo) — verify current pricing first (Rule 1), use an ephemeral cluster + teardown
- [ ] Learning docs written

---

## Non-goals (Rule 3)
Polished UI · more than three agents · multi-tenant concerns · fine-tuning · more than one
data domain *at runtime* (seams kept for a later config-only Aurora instance).
