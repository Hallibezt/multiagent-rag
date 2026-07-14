.PHONY: install up down reset ps logs smoke psql-doc psql-sql fmt lint

install:        ## install deps into the uv-managed venv
	uv sync

up:             ## start both data stores, wait until healthy
	docker compose up -d --wait

down:           ## stop stores (keep data)
	docker compose down

reset:          ## stop stores AND wipe their data volumes
	docker compose down -v

ps:
	docker compose ps

logs:
	docker compose logs -f

smoke:          ## prove the local stack works end-to-end (no secrets)
	uv run python -m multiagent_rag.smoke

.PHONY: extract ingest search
extract:        ## (needs GuestPad) pull content into data/seed/documents.jsonl
	uv run python -m multiagent_rag.ingest.extract

ingest:         ## embed the seed into the doc store (no GuestPad needed)
	uv run python -m multiagent_rag.ingest.load

seed-sql:       ## seed synthetic transactional data into the sql-store
	uv run python -m multiagent_rag.sql_agent.seed

search:         ## similarity search, e.g. make search Q="how do I use the hot tub"
	uv run python -m multiagent_rag.ingest.search "$(Q)"

.PHONY: ask
ask:            ## ask the graph, e.g. make ask Q="how do I use the hot tub"
	uv run python -m multiagent_rag.graph.run "$(Q)"

checkpoint-demo: ## prove crash recovery: pause → checkpoint to Postgres → resume in a fresh process
	uv run python -m multiagent_rag.checkpointing.demo

psql-doc:       ## psql into the document / vector store
	docker compose exec doc-store psql -U rag -d docs

psql-sql:       ## psql into the structured store
	docker compose exec sql-store psql -U rag -d guestpad

fmt:
	uv run ruff format .

lint:
	uv run ruff check .
