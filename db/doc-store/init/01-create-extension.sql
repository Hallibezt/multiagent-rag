-- Runs once, on first boot of the doc-store (Postgres' docker-entrypoint-initdb.d).
-- pgvector ships inside the image, but the extension must be enabled per-database.
CREATE EXTENSION IF NOT EXISTS vector;
