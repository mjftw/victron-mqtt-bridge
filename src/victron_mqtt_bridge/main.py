import asyncio
import logging
import sys

from victron_mqtt_bridge.banner import BANNER
from victron_mqtt_bridge.client.downstream_mqtt_client import (
    DownstreamConnectionConfig,
    DownstreamMqttClient,
)
from victron_mqtt_bridge.client.victron_mqtt_client import VictronMqttClient
from victron_mqtt_bridge.config import Settings
from victron_mqtt_bridge.connectivity import check_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


async def run(settings: Settings) -> None:
    config = DownstreamConnectionConfig.from_settings(settings)
    downstream = DownstreamMqttClient(config)
    async with downstream.connected():
        client = VictronMqttClient(settings, downstream, settings.topic_mapping)
        await client.connect()


async def check_connectivity(settings: Settings) -> bool:
    print("Checking connectivity...")
    results = await check_all(
        victron_host=settings.victron_mqtt_host,
        victron_port=settings.victron_mqtt_port,
        downstream_host=settings.downstream_mqtt_host,
        downstream_port=settings.downstream_mqtt_port,
    )
    for result in results:
        print(result.display_line())

    failed = [r for r in results if not r.reachable]
    if failed:
        print()
        print("Cannot start: one or more brokers are not reachable.")
        print("Check that the hosts and ports in your configuration are correct")
        print("and that the brokers are running and accessible from this machine.")
        return False

    print()
    return True


def main() -> None:
    print(BANNER)
    settings = Settings()  # ty: ignore[missing-argument]
    for line in settings.display_lines():
        print(line)
    print()

    if not asyncio.run(check_connectivity(settings)):
        sys.exit(1)

    asyncio.run(run(settings))


if __name__ == "__main__":
    main()
