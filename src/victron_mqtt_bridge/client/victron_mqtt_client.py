import asyncio
import logging

import aiomqtt

from victron_mqtt_bridge.client.publisher import MqttPublisher
from victron_mqtt_bridge.config import Settings
from victron_mqtt_bridge.topic_mapping import TopicMapping
from victron_mqtt_bridge.topic_tree import build_topic_tree, render_topic_tree

logger = logging.getLogger(__name__)

_SERIAL_DISCOVERY_TOPIC = "N/+/system/0/Serial"
_KEEPALIVE_TOPIC_TEMPLATE = "R/{serial}/keepalive"
_VICTRON_DATA_PREFIX_TEMPLATE = "N/{serial}/"
_TOPIC_DISCOVERY_WINDOW_SECONDS = 5.0


# ---------------------------------------------------------------------------
# Topic discovery
# ---------------------------------------------------------------------------


async def _collect_topic_paths(
    client: aiomqtt.Client,
    serial: str,
    window_seconds: float,
) -> frozenset[str]:
    """Subscribe to N/<serial>/#, send a keepalive, collect relative topic
    paths for window_seconds, then unsubscribe.
    """
    wildcard = f"N/{serial}/#"
    prefix = _VICTRON_DATA_PREFIX_TEMPLATE.format(serial=serial)
    await client.subscribe(wildcard)
    await _send_keepalive(client, serial)

    paths: set[str] = set()
    try:
        async with asyncio.timeout(window_seconds):
            async for message in client.messages:
                topic = str(message.topic)
                if topic.startswith(prefix):
                    paths.add(topic[len(prefix):])
    except TimeoutError:
        pass

    await client.unsubscribe(wildcard)
    return frozenset(paths)


# ---------------------------------------------------------------------------
# Keep-alive
# ---------------------------------------------------------------------------


async def _send_keepalive(client: aiomqtt.Client, serial: str) -> None:
    topic = _KEEPALIVE_TOPIC_TEMPLATE.format(serial=serial)
    await client.publish(topic, payload="")
    logger.debug("Sent keepalive for serial %s", serial)


async def _keepalive_loop(
    client: aiomqtt.Client,
    serial: str,
    interval_seconds: int,
) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        await _send_keepalive(client, serial)


# ---------------------------------------------------------------------------
# Serial discovery
# ---------------------------------------------------------------------------


async def _discover_serial(client: aiomqtt.Client) -> str:
    """Subscribe to the serial discovery topic and return the first serial seen."""
    await client.subscribe(_SERIAL_DISCOVERY_TOPIC)
    async for message in client.messages:
        # Topic format: N/<serial>/system/0/Serial
        parts = str(message.topic).split("/")
        if len(parts) >= 2:
            serial = parts[1]
            logger.info("Discovered Victron serial: %s", serial)
            return serial
    raise RuntimeError("MQTT message stream ended before serial was discovered")


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def resolve_downstream_topic(
    incoming_topic: str,
    serial: str,
    topic_mapping: TopicMapping,
) -> str | None:
    """Return the downstream topic for an incoming Victron message, or None if unmapped.

    Strips the N/<serial>/ prefix from the incoming topic, then looks the
    relative path up in topic_mapping.
    """
    prefix = _VICTRON_DATA_PREFIX_TEMPLATE.format(serial=serial)
    if not incoming_topic.startswith(prefix):
        return None
    relative_path = incoming_topic[len(prefix):]
    return topic_mapping.get(relative_path)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class VictronMqttClient:
    """Connects to a Victron Cerbo GX MQTT broker, discovers the device serial,
    logs the full topic tree on startup, maintains a keep-alive, and bridges
    mapped telemetry topics to a downstream MQTT publisher.
    """

    def __init__(
        self,
        settings: Settings,
        downstream: MqttPublisher,
        topic_mapping: TopicMapping,
    ) -> None:
        self._settings = settings
        self._downstream = downstream
        self._topic_mapping = topic_mapping

    async def connect(self) -> None:
        tls_params = (
            aiomqtt.TLSParameters() if self._settings.victron_mqtt_use_ssl else None
        )
        async with aiomqtt.Client(
            hostname=self._settings.victron_mqtt_host,
            port=self._settings.victron_mqtt_port,
            tls_params=tls_params,
        ) as client:
            logger.info(
                "Connected to Victron broker at %s:%s",
                self._settings.victron_mqtt_host,
                self._settings.victron_mqtt_port,
            )
            serial = await _discover_serial(client)

            logger.info(
                "Discovering available topics (collecting for %.0f s)...",
                _TOPIC_DISCOVERY_WINDOW_SECONDS,
            )
            paths = await _collect_topic_paths(
                client, serial, _TOPIC_DISCOVERY_WINDOW_SECONDS
            )
            tree = build_topic_tree(paths)
            logger.info("Available Victron topics under N/%s/", serial)
            for line in render_topic_tree(tree):
                logger.info(line)

            for relative_path in self._topic_mapping:
                prefix = _VICTRON_DATA_PREFIX_TEMPLATE.format(serial=serial)
                topic = f"{prefix}{relative_path}"
                await client.subscribe(topic)
                logger.debug("Subscribed to Victron topic %s", topic)

            await _send_keepalive(client, serial)

            keepalive_task = asyncio.create_task(
                _keepalive_loop(
                    client,
                    serial,
                    self._settings.keepalive_interval_seconds,
                )
            )
            try:
                await self._process_messages(client, serial)
            finally:
                keepalive_task.cancel()

    async def _process_messages(
        self,
        client: aiomqtt.Client,
        serial: str,
    ) -> None:
        async for message in client.messages:
            incoming_topic = str(message.topic)
            downstream_topic = resolve_downstream_topic(
                incoming_topic, serial, self._topic_mapping
            )
            if downstream_topic is None:
                logger.debug("Received unmapped topic, skipping: %s", incoming_topic)
                continue

            payload = (
                message.payload
                if isinstance(message.payload, bytes)
                else str(message.payload)
            )
            logger.info(
                "Bridging %s -> %s%s",
                incoming_topic,
                downstream_topic,
                " [retain]" if message.retain else "",
            )
            await self._downstream.publish(
                downstream_topic,
                payload,
                retain=message.retain,
            )
