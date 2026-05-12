import asyncio
import logging

from victron_mqtt_bridge.banner import BANNER
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


async def run() -> None:
    settings = Settings()
    config = DownstreamConnectionConfig.from_settings(settings)
    downstream = DownstreamMqttClient(config)
    async with downstream.connected():
        client = VictronMqttClient(settings, downstream, settings.topic_mapping)
        await client.connect()


def main() -> None:
    print(BANNER)
    asyncio.run(run())


if __name__ == "__main__":
    main()
