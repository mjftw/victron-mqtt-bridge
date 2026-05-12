# victron-mqtt-bridge

A bridge service that reads telemetry from a [Victron Cerbo GX](https://www.victronenergy.com/panel-systems-remote-monitoring/cerbo-gx) over its local MQTT broker and republishes selected topics to a separate downstream MQTT broker of your choice.

## Background

The Cerbo GX exposes a local MQTT broker on port 1883 (or 8883 with SSL). All Victron telemetry — battery state of charge, grid power, inverter state, temperature sensors, and more — is published there in real time under topics of the form:

```
N/<serial>/<service>/<instance>/<path>
```

where `<serial>` is the device's unique identifier (e.g. `a1b2c3d4e5f6`).

**The broker requires a keep-alive.** Without a periodic publish to `R/<serial>/keepalive`, the Cerbo GX stops streaming data after roughly one minute. This service handles that automatically.

## What this service does

1. **Connects** to the Victron MQTT broker.
2. **Discovers the serial** by subscribing to `N/+/system/0/Serial` and reading the device identifier from the first message topic — no manual configuration of the serial needed.
3. **Subscribes** to the paths listed in your `TOPIC_MAPPING` — individual leaf topics or entire subtrees (branch mappings).
4. **Sends an immediate keepalive** to `R/<serial>/keepalive` so data starts flowing straight away, then repeats every `KEEPALIVE_INTERVAL_SECONDS` (default 60 s) for the lifetime of the connection.
5. **Bridges each message** to the downstream broker, preserving the MQTT retain flag from the source.

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)

## Setup

```sh
# Install dependencies
uv sync

# Create your .env from the example and fill in your values
cp .env.example .env
```

## Configuration

All settings are read from environment variables or a `.env` file in the project root.

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

## Topic mapping

`TOPIC_MAPPING` is a JSON object. Keys are Victron **relative paths** — the segment of the topic after `N/<serial>/`. Values are the **full topic** to publish on the downstream broker.

Two key forms are supported:

### Leaf mapping (exact path)

Maps a single Victron topic to a single downstream topic.

```sh
TOPIC_MAPPING='{
  "system/0/Dc/Battery/Soc":           "victron/battery/soc",
  "system/0/Dc/Battery/Voltage":        "victron/battery/voltage",
  "system/0/Ac/Grid/L1/Power":          "victron/grid/l1/power"
}'
```

### Branch mapping (trailing `/`)

A key ending with `/` subscribes to the entire subtree under that path (using an MQTT `#` wildcard) and forwards every message by appending the remaining path segments to the downstream prefix.

```sh
TOPIC_MAPPING='{
  "system/0/Dc/Battery/": "victron/battery/",
  "system/0/Ac/Grid/":    "victron/grid/"
}'
```

For example, with `"system/0/Dc/Battery/": "victron/battery/"`:

| Victron topic | Downstream topic |
|---|---|
| `N/<serial>/system/0/Dc/Battery/Soc` | `victron/battery/Soc` |
| `N/<serial>/system/0/Dc/Battery/Voltage` | `victron/battery/Voltage` |
| `N/<serial>/system/0/Dc/Battery/Current` | `victron/battery/Current` |

Leaf and branch mappings can be mixed freely. When both an exact key and a branch key match the same incoming topic, the exact key wins. When multiple branch keys match, the longest (most specific) one wins.

### Discovering available paths

To find the full list of available paths for your system, browse the Victron MQTT API with any MQTT client after sending a keepalive to start the stream:

```sh
mosquitto_pub -h <cerbo-ip> -t 'R/<serial>/keepalive' -m ''
mosquitto_sub -h <cerbo-ip> -t 'N/#' -v
```

## Running

```sh
uv run victron-mqtt-bridge
```

On startup you should see log lines like:

```
2026-05-12 21:00:00 INFO ... Connected to Victron broker at 192.168.1.83:1883
2026-05-12 21:00:00 INFO ... Discovered Victron serial: a1b2c3d4e5f6
2026-05-12 21:00:01 INFO ... Bridging N/a1b2c3d4e5f6/system/0/Dc/Battery/Soc -> victron/battery/Soc
```

## Docker

A multi-stage `Dockerfile` is included. The builder stage installs runtime
dependencies with uv into a virtualenv; the runtime stage copies only the
virtualenv and source — no uv, no build tools, no dev dependencies.

```sh
# Build
docker build -t victron-mqtt-bridge .

# Run (pass your environment variables in)
docker run --rm \
  -e VICTRON_MQTT_HOST=192.168.1.83 \
  -e DOWNSTREAM_MQTT_HOST=192.168.1.200 \
  -e TOPIC_MAPPING='{"system/0/Dc/Battery/Soc":"victron/battery/soc"}' \
  victron-mqtt-bridge

# Or using an env file
docker run --rm --env-file .env victron-mqtt-bridge
```

## Local development

A `docker-compose.yaml` is included under `local-dev/` that starts a local [Mosquitto](https://mosquitto.org/) broker to use as the downstream target during development.

```sh
docker compose -f local-dev/docker-compose.yaml up -d
```

This starts Mosquitto on `localhost:1883` with anonymous connections enabled (see `local-dev/mosquitto.conf`). Point the downstream settings at it:

```sh
DOWNSTREAM_MQTT_HOST=localhost
DOWNSTREAM_MQTT_PORT=1883
```

To watch all messages arriving on the local broker in real time:

```sh
mosquitto_sub -h localhost -t '#' -v
```

To stop the broker:

```sh
docker compose -f local-dev/docker-compose.yaml down
```

## Development

A `justfile` is included with all common commands. Install [just](https://just.systems) then:

```sh
just          # lint + typecheck + test (default)
just lint     # ruff check
just format   # ruff format
just typecheck # ty check
just test     # pytest
just run      # run the bridge locally (reads .env)
just build    # build Docker image
just dev-up   # start local Mosquitto broker
just dev-down # stop local Mosquitto broker
just dev-watch # subscribe to all topics on the local broker
```

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

No mocks. `FakeMqttPublisher` is a real implementation of the `MqttPublisher` Protocol that records every `publish()` call. The topic-resolution logic lives in the pure function `resolve_topic()` and is tested directly — no broker or network needed.
