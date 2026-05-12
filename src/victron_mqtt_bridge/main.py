import asyncio
import logging

from victron_mqtt_bridge.client.downstream_mqtt_client import (
    DownstreamConnectionConfig,
    DownstreamMqttClient,
)
from victron_mqtt_bridge.client.victron_mqtt_client import VictronMqttClient
from victron_mqtt_bridge.config import Settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# Map Victron relative paths (after N/<serial>/) to downstream MQTT topics.
# Extend this dict as more telemetry points are needed.
TOPIC_MAPPING: dict[str, str] = {
    "system/0/Dc/Battery/Soc": "victron/battery/soc",
}


async def run() -> None:
    settings = Settings()
    config = DownstreamConnectionConfig.from_settings(settings)
    downstream = DownstreamMqttClient(config)
    async with downstream.connected():
        client = VictronMqttClient(settings, downstream, TOPIC_MAPPING)
        await client.connect()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
