# victron-mqtt-bridge

![Python](https://img.shields.io/badge/python-3.13-blue?logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

A lightweight bridge that reads live telemetry from a [Victron Cerbo GX](https://www.victronenergy.com/panel-systems-remote-monitoring/cerbo-gx) over its local MQTT broker and republishes selected topics to any downstream MQTT broker — such as a Home Assistant instance, InfluxDB ingestion pipeline, or Node-RED flow.

## Why this exists

The Victron Cerbo GX exposes a rich local MQTT broker, but using it directly from external systems has two friction points:

1. **Serial-prefixed topics.** Every topic is prefixed with `N/<serial>/`, where `<serial>` is the device's unique identifier. Hard-coding this into dashboards or automations means they break when you replace hardware.

2. **Mandatory keep-alive.** Without a periodic publish to `R/<serial>/keepalive`, the broker stops streaming data after roughly one minute. Every consumer has to implement this independently.

This service handles both: it discovers the serial automatically on startup and maintains the keep-alive for the lifetime of the connection, so downstream consumers see clean, stable topic names with no knowledge of Victron internals.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [Topic mapping](#topic-mapping)
- [Running](#running)
- [Docker](#docker)
- [Local development](#local-development)
- [Contributing](#contributing)
- [Development reference](#development-reference)
- [License](#license)

---

## Features

- **Automatic serial discovery** — subscribes to `N/+/system/0/Serial` and reads the device identifier from the first message; no manual configuration of the serial needed.
- **Keep-alive managed for you** — sends an immediate keepalive on connect, then repeats every `KEEPALIVE_INTERVAL_SECONDS` (default 60 s).
- **Leaf and branch mappings** — map individual topics exactly, or map an entire subtree with a trailing `/` and a single MQTT `#` subscription.
- **Retain flag preserved** — the MQTT retain flag from each Victron message is forwarded unchanged to the downstream broker.
- **Pre-flight connectivity check** — verifies both brokers are reachable before starting, with clear error output if they are not.
- **Docker-ready** — multi-stage `Dockerfile` produces a minimal runtime image with no build tools or dev dependencies.

---

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)

For Docker usage only Docker is required.

---

## Getting started

```sh
# 1. Clone the repo
git clone https://github.com/your-username/victron-mqtt-bridge.git
cd victron-mqtt-bridge

# 2. Install dependencies
uv sync

# 3. Create your configuration
cp .env.example .env
$EDITOR .env  # fill in your Victron and downstream broker details

# 4. Run
uv run victron-mqtt-bridge
```

---

## Configuration

All settings are read from environment variables or a `.env` file in the project root. Copy `.env.example` to get started — it includes inline documentation for every variable.

| Variable | Required | Default | Description |
|---|---|---|---|
| `VICTRON_MQTT_HOST` | Yes | — | IP or hostname of the Cerbo GX on your local network |
| `VICTRON_MQTT_USE_SSL` | No | `false` | Connect over SSL on port 8883 instead of plain 1883 |
| `KEEPALIVE_INTERVAL_SECONDS` | No | `60` | How often (in seconds) to send the keepalive signal |
| `TOPIC_MAPPING` | Yes | — | JSON object mapping Victron paths to downstream topics (see below) |
| `DOWNSTREAM_MQTT_HOST` | Yes | — | IP or hostname of the downstream broker |
| `DOWNSTREAM_MQTT_PORT` | No | `1883` | Port of the downstream broker |
| `DOWNSTREAM_MQTT_USE_SSL` | No | `false` | Connect to downstream broker over SSL |
| `DOWNSTREAM_MQTT_USERNAME` | No | — | Username for the downstream broker |
| `DOWNSTREAM_MQTT_PASSWORD` | No | — | Password for the downstream broker |

---

## Topic mapping

`TOPIC_MAPPING` is a JSON object. Keys are Victron **relative paths** — the segment of the topic after `N/<serial>/`. Values are the **full topic** to publish on the downstream broker.

### Leaf mapping — exact path

Maps a single Victron topic to a single downstream topic.

```sh
TOPIC_MAPPING='{
  "system/0/Dc/Battery/Soc":    "victron/battery/soc",
  "system/0/Dc/Battery/Voltage": "victron/battery/voltage",
  "system/0/Ac/Grid/L1/Power":   "victron/grid/l1/power"
}'
```

### Branch mapping — trailing `/`

A key ending with `/` subscribes to the **entire subtree** under that path using an MQTT `#` wildcard, and forwards every message by appending the remaining path segments to the downstream prefix.

```sh
TOPIC_MAPPING='{
  "system/0/Dc/Battery/": "victron/battery/",
  "system/0/Ac/Grid/":    "victron/grid/"
}'
```

Example: with `"system/0/Dc/Battery/": "victron/battery/"`:

| Victron topic | Downstream topic |
|---|---|
| `N/<serial>/system/0/Dc/Battery/Soc` | `victron/battery/Soc` |
| `N/<serial>/system/0/Dc/Battery/Voltage` | `victron/battery/Voltage` |
| `N/<serial>/system/0/Dc/Battery/Current` | `victron/battery/Current` |

Leaf and branch mappings can be mixed freely. When both match the same incoming topic, the exact key wins. When multiple branch keys match, the longest (most specific) one wins.

### Finding available paths

See **[docs/victron-mqtt-topics.md](docs/victron-mqtt-topics.md)** for a curated reference of all services, paths, units, and enum values (derived from the [official Venus OS dbus wiki](https://github.com/victronenergy/venus/wiki/dbus)).

To discover paths live on your own device:

```sh
mosquitto_pub -h <cerbo-ip> -t 'R/<serial>/keepalive' -m ''
mosquitto_sub -h <cerbo-ip> -t 'N/#' -v
```

---

## Running

```sh
uv run victron-mqtt-bridge
```

On startup you should see:

```
2026-05-12 21:00:00 INFO ... Connected to downstream broker at localhost:1883
2026-05-12 21:00:00 INFO ... Connected to Victron broker at 192.168.1.83:1883
2026-05-12 21:00:00 INFO ... Discovered Victron serial: a1b2c3d4e5f6
2026-05-12 21:00:01 INFO ... Bridging N/a1b2c3d4e5f6/system/0/Dc/Battery/Soc -> victron/battery/Soc
```

Press `Ctrl+C` to stop cleanly.

---

## Docker

A multi-stage `Dockerfile` is included. The builder stage installs runtime dependencies with uv into an isolated virtualenv; the runtime stage copies only the virtualenv and source — no uv, no build tools, no dev dependencies.

```sh
# Build
docker build -t victron-mqtt-bridge .

# Run with inline environment variables
docker run --rm \
  -e VICTRON_MQTT_HOST=192.168.1.83 \
  -e DOWNSTREAM_MQTT_HOST=192.168.1.200 \
  -e TOPIC_MAPPING='{"system/0/Dc/Battery/":"victron/battery/"}' \
  victron-mqtt-bridge

# Or using an env file
docker run --rm --env-file .env victron-mqtt-bridge
```

---

## Local development

A `docker-compose.yaml` under `local-dev/` starts a [Mosquitto](https://mosquitto.org/) broker on `localhost:1883` to use as the downstream target while developing.

```sh
just dev-up    # start the broker
just run       # run the bridge (reads .env)
just dev-watch # tail all messages arriving on the local broker
just dev-down  # stop the broker
```

Or without `just`:

```sh
docker compose -f local-dev/docker-compose.yaml up -d
mosquitto_sub -h localhost -t '#' -v
```

---

## Contributing

Contributions are welcome. Please:

1. Fork the repository and create a branch from `main`.
2. Run `just` (lint + typecheck + test) before opening a pull request — all checks must pass.
3. Keep commits focused and write a clear commit message explaining *why*, not just *what*.
4. Open an issue first for non-trivial changes so we can discuss the approach.

There is no formal CLA. By submitting a pull request you agree that your contributions will be licensed under the MIT licence.

---

## Development reference

Install [just](https://just.systems) then run `just` with no arguments to lint, typecheck, and test in one step.

| Command | Description |
|---|---|
| `just` | lint + typecheck + test (default) |
| `just lint` | ruff check |
| `just format` | ruff format |
| `just typecheck` | ty check |
| `just test` | pytest |
| `just run` | run the bridge locally (reads `.env`) |
| `just build` | build Docker image |
| `just dev-up` | start local Mosquitto broker |
| `just dev-down` | stop local Mosquitto broker |
| `just dev-watch` | start broker + bridge and subscribe to all topics |

### Project structure

```
src/victron_mqtt_bridge/
├── config.py                      — all settings (pydantic-settings, env-driven)
├── topic_mapping.py               — TopicMapping type alias + resolve_topic()
├── main.py                        — entry point; wires components together
└── client/
    ├── publisher.py               — MqttPublisher Protocol
    ├── downstream_mqtt_client.py  — publishes to the downstream broker
    └── victron_mqtt_client.py     — connects to Victron, runs keepalive, bridges messages

tests/
├── fakes/fake_mqtt_publisher.py        — in-memory MqttPublisher for use in tests
├── test_topic_mapping.py               — unit tests for resolve_topic()
└── client/test_victron_mqtt_client.py  — behaviour-based tests (test_should_X_when_Y)
```

### Testing approach

No mocks. `FakeMqttPublisher` is a real implementation of the `MqttPublisher` Protocol that records every `publish()` call in memory. The topic-resolution logic lives in the pure function `resolve_topic()` and is tested directly with known inputs — no broker or network needed.

---

## License

[MIT](LICENSE)
