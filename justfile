default: check

# ── code quality ────────────────────────────────────────────────────────────

# Run all checks (lint, typecheck, test)
check: lint typecheck test

# Lint with ruff
lint:
    uv run ruff check src/ tests/

# Format with ruff
format:
    uv run ruff format src/ tests/

# Type-check with ty
typecheck:
    uv run ty check src/

# Run tests
test:
    uv run pytest

# ── run locally ─────────────────────────────────────────────────────────────

# Start the bridge (reads from .env)
run:
    uv run victron-mqtt-bridge

# ── docker ──────────────────────────────────────────────────────────────────

# Build the Docker image
build tag="victron-mqtt-bridge":
    docker build -t {{tag}} .

# Run the Docker image using .env
docker-run tag="victron-mqtt-bridge":
    docker run --rm --env-file .env {{tag}}

# ── local dev broker ────────────────────────────────────────────────────────

# Start the local Mosquitto broker
dev-up:
    docker compose -f local-dev/docker-compose.yaml up -d

# Stop the local Mosquitto broker
dev-down:
    docker compose -f local-dev/docker-compose.yaml down

# Watch all messages arriving on the local broker
dev-watch: dev-up run
    mosquitto_sub -h localhost -t '#' -v
