# ── builder ────────────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Use /app so .venv script shebangs match the runtime stage path
WORKDIR /app

# Copy dependency manifests first so this layer is cached across code changes
COPY pyproject.toml uv.lock ./

# Install runtime dependencies only into an isolated prefix (no dev deps)
RUN uv sync --frozen --no-dev --no-install-project

# Copy source and install the package itself
# README.md is required by pyproject.toml and must be present for uv_build
COPY README.md ./
COPY src/ ./src/
RUN uv sync --frozen --no-dev

# ── runtime ────────────────────────────────────────────────────────────────
FROM python:3.13-slim

WORKDIR /app

# Copy the fully-resolved virtualenv from the builder
COPY --from=builder /app/.venv ./.venv

# Copy application source (no build tools, no uv, no cache)
COPY --from=builder /app/src ./src

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["victron-mqtt-bridge"]
