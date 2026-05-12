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
3. **Subscribes** to the exact set of Victron paths listed in your `TOPIC_MAPPING`, and nothing else.
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

```sh
TOPIC_MAPPING='{
  "system/0/Dc/Battery/Soc":           "victron/battery/soc",
  "system/0/Dc/Battery/Voltage":        "victron/battery/voltage",
  "system/0/Ac/Grid/L1/Power":          "victron/grid/l1/power",
  "system/0/Ac/Grid/L2/Power":          "victron/grid/l2/power",
  "system/0/Ac/Grid/L3/Power":          "victron/grid/l3/power",
  "system/0/Ac/Consumption/L1/Power":   "victron/consumption/l1/power"
}'
```

The service subscribes **only** to the paths listed here. Messages on any other topic are ignored.

To find the full list of available paths for your system, browse the Victron MQTT API with any MQTT client (e.g. `mosquitto_sub -h <cerbo-ip> -t 'N/#' -v`) after sending a keepalive to start the stream:

```sh
mosquitto_pub -h <cerbo-ip> -t 'R/<serial>/keepalive' -m ''
```

## Running

```sh
uv run victron-mqtt-bridge
```

On startup you should see log lines like:

```
2026-05-12 21:00:00 INFO ... Connected to Victron broker
2026-05-12 21:00:00 INFO ... Discovered Victron serial {'serial': 'a1b2c3d4e5f6'}
2026-05-12 21:00:01 INFO ... Bridging message {'from': 'N/a1b2c3d4e5f6/system/0/Dc/Battery/Soc', 'to': 'victron/battery/soc', 'retain': True}
```

## Development

```sh
# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/

# Format
uv run ruff format src/ tests/

# Type check
uv run ty check src/
```

### Project structure

```
src/victron_mqtt_bridge/
├── config.py                      — all settings (pydantic-settings, env-driven)
├── topic_mapping.py               — TopicMapping type alias
├── main.py                        — entry point; wires components together
└── client/
    ├── publisher.py               — MqttPublisher Protocol
    ├── downstream_mqtt_client.py  — publishes to the downstream broker
    └── victron_mqtt_client.py     — connects to Victron, runs keepalive, bridges messages

tests/
├── fakes/fake_mqtt_publisher.py   — in-memory MqttPublisher for use in tests
└── client/test_victron_mqtt_client.py — behaviour-based tests (test_should_X_when_Y)
```

### Testing approach

No mocks. `FakeMqttPublisher` is a real implementation of the `MqttPublisher` Protocol that records every `publish()` call. The message-routing logic lives in the pure function `resolve_downstream_topic()`, which is tested directly by feeding it known inputs and asserting on the output — no broker or network needed.
