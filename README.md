# victron-mqtt-bridge

Connects to a Victron Cerbo GX local MQTT broker, discovers the device serial
number, subscribes to a configurable set of telemetry topics, and republishes
them to a downstream MQTT broker. A keep-alive signal is sent every 60 seconds
(configurable) to keep the Victron broker streaming data.

## How it works

1. Connects to the Victron broker and subscribes to `N/+/system/0/Serial` to
   discover the device serial automatically.
2. Subscribes to only the paths listed in `TOPIC_MAPPING` in `main.py`
   (e.g. `system/0/Dc/Battery/Soc`).
3. Sends an immediate keepalive to `R/<serial>/keepalive`, then repeats on a
   60-second interval. Without keepalives the Victron broker stops publishing
   after roughly one minute.
4. Forwards each received message to the downstream broker, preserving the
   MQTT retain flag from the source.

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)

## Setup

```sh
# Install dependencies
uv sync

# Copy the example env file and fill in your values
cp .env.example .env
```

## Configuration

All settings are read from environment variables (or a `.env` file).

| Variable | Required | Default | Description |
|---|---|---|---|
| `VICTRON_MQTT_HOST` | Yes | — | Hostname/IP of the Cerbo GX |
| `VICTRON_MQTT_USE_SSL` | No | `false` | Use SSL (port 8883) instead of plain (port 1883) |
| `KEEPALIVE_INTERVAL_SECONDS` | No | `60` | Seconds between keepalive publishes |
| `DOWNSTREAM_MQTT_HOST` | Yes | — | Hostname/IP of the downstream broker |
| `DOWNSTREAM_MQTT_PORT` | No | `1883` | Port of the downstream broker |
| `DOWNSTREAM_MQTT_USE_SSL` | No | `false` | Connect to downstream broker over SSL |
| `DOWNSTREAM_MQTT_USERNAME` | No | — | Username for the downstream broker |
| `DOWNSTREAM_MQTT_PASSWORD` | No | — | Password for the downstream broker |

## Adding topic mappings

Edit `TOPIC_MAPPING` in `src/victron_mqtt_bridge/main.py`. Keys are Victron
relative paths (the segment after `N/<serial>/`), values are the full topic to
publish on the downstream broker:

```python
TOPIC_MAPPING: dict[str, str] = {
    "system/0/Dc/Battery/Soc":        "victron/battery/soc",
    "system/0/Ac/Grid/L1/Power":      "victron/grid/l1/power",
    "system/0/Ac/Consumption/L1/Power": "victron/consumption/l1/power",
}
```

## Running

```sh
uv run victron-mqtt-bridge
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
