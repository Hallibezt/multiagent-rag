# Build on Astral's uv image (uv + Python 3.13 preinstalled), matching our
# requires-python and uv.lock. One image serves both the API and (later) the
# split-out SQL-agent service — the Kubernetes Deployment picks the command.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# 1) Dependencies as a cached layer: lockfile only, no project, no dev deps.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# 2) The source (+ README, which pyproject references), then install the project.
COPY README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

# Put the venv on PATH so `uvicorn` is found directly.
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "multiagent_rag.service.app:app", "--host", "0.0.0.0", "--port", "8000"]
