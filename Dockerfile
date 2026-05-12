# ── builder ────────────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build

# Copy dependency manifests first so this layer is cached across code changes
COPY pyproject.toml uv.lock ./

# Install runtime dependencies only into an isolated prefix (no dev deps)
RUN uv sync --frozen --no-dev --no-install-project

# Copy source and install the package itself
COPY src/ ./src/
RUN uv sync --frozen --no-dev

# ── runtime ────────────────────────────────────────────────────────────────
FROM python:3.13-slim

WORKDIR /app

# Copy the fully-resolved virtualenv from the builder
COPY --from=builder /build/.venv ./.venv

# Copy application source (no build tools, no uv, no cache)
COPY --from=builder /build/src ./src

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["victron-mqtt-bridge"]
