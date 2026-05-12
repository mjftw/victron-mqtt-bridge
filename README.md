# victron-mqtt-bridge

![Python](https://img.shields.io/badge/python-3.13-blue?logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

A lightweight bridge that reads live telemetry from a [Victron Cerbo GX](https://www.victronenergy.com/panel-systems-remote-monitoring/cerbo-gx) over its local MQTT broker and republishes selected topics to any downstream MQTT broker, such as a Home Assistant instance, InfluxDB ingestion pipeline, or Node-RED flow.

## Why this exists

I wanted a simple way to get data from the Victron Cerbo GX's MQTT broker into a central broker I already use to collect data from other sources, but a standard MQTT bridge doesn't work out of the box for two reasons.

First, the Cerbo GX requires a periodic keepalive publish to `R/<serial>/keepalive` or it stops streaming data after roughly one minute. A passive bridge silently starves.

Second, a transparent bridge would expose the raw Victron topic structure (serial-prefixed, deep paths like `N/a1b2c3d4e5f6/system/0/Dc/Battery/Soc`) to every downstream client. I wanted to hide that detail and remap only the topics I care about to clean, stable names of my choosing, so nothing downstream needs to know anything about the Victron topic tree.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [Topic mapping](#topic-mapping)
- [Running](#running)
- [Docker](#docker)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Topic remapping**: publish any Victron path to whatever downstream topic name you choose, keeping downstream clients completely decoupled from Victron internals.
- **Keep-alive managed for you**: the keepalive is sent automatically so the data stream never stalls.
- **Leaf and branch mappings**: map individual topics exactly, or forward an entire subtree with a single trailing `/`.
- **Pre-flight connectivity check**: verifies both brokers are reachable before starting, with a clear error if they are not.
- **Docker-ready**: ships a minimal multi-stage image with no build tools or dev dependencies.

---

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)

For Docker usage only Docker is required.

---

## Getting started

```sh
# 1. Clone the repo
git clone https://github.com/mjftw/victron-mqtt-bridge.git
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

All settings are read from environment variables or a `.env` file in the project root. Copy `.env.example` to get started; it includes inline documentation for every variable.

| Variable | Required | Default | Description |
|---|---|---|---|
| `VICTRON_MQTT_HOST` | Yes | n/a | IP or hostname of the Cerbo GX on your local network |
| `VICTRON_MQTT_USE_SSL` | No | `false` | Connect over SSL on port 8883 instead of plain 1883 |
| `KEEPALIVE_INTERVAL_SECONDS` | No | `60` | How often (in seconds) to send the keepalive signal |
| `TOPIC_MAPPING` | Yes | n/a | JSON object mapping Victron paths to downstream topics (see below) |
| `DOWNSTREAM_MQTT_HOST` | Yes | n/a | IP or hostname of the downstream broker |
| `DOWNSTREAM_MQTT_PORT` | No | `1883` | Port of the downstream broker |
| `DOWNSTREAM_MQTT_USE_SSL` | No | `false` | Connect to downstream broker over SSL |
| `DOWNSTREAM_MQTT_USERNAME` | No | n/a | Username for the downstream broker |
| `DOWNSTREAM_MQTT_PASSWORD` | No | n/a | Password for the downstream broker |

---

## Topic mapping

`TOPIC_MAPPING` is a JSON object. Keys are Victron **relative paths** (the segment of the topic after `N/<serial>/`). Values are the **full topic** to publish on the downstream broker.

### Leaf mapping (exact path)

Maps a single Victron topic to a single downstream topic.

```sh
TOPIC_MAPPING='{
  "system/0/Dc/Battery/Soc":    "victron/battery/soc",
  "system/0/Dc/Battery/Voltage": "victron/battery/voltage",
  "system/0/Ac/Grid/L1/Power":   "victron/grid/l1/power"
}'
```

### Branch mapping (trailing `/`)

A key ending with `/` subscribes to the **entire subtree** under that path using an MQTT `#` wildcard, and forwards every message by appending the remaining path segments to the downstream prefix.

```sh
TOPIC_MAPPING='{
  "system/0/Dc/Battery/": "victron/battery/",
  "system/0/Ac/Grid/":    "victron/grid/"
}'
```

Example with `"system/0/Dc/Battery/": "victron/battery/"`:

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

A multi-stage `Dockerfile` is included. The builder stage installs runtime dependencies with uv into an isolated virtualenv; the runtime stage copies only the virtualenv and source, with no uv, build tools, or dev dependencies.

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

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, the `just` command reference, commit style, testing approach, and the release process.

---

## License

[MIT](LICENSE)
