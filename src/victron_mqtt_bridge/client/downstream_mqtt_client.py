import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import aiomqtt

from victron_mqtt_bridge.config import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DownstreamConnectionConfig:
    host: str
    port: int
    use_ssl: bool
    username: str | None
    password: str | None

    @classmethod
    def from_settings(cls, settings: Settings) -> "DownstreamConnectionConfig":
        return cls(
            host=settings.downstream_mqtt_host,
            port=settings.downstream_mqtt_port,
            use_ssl=settings.downstream_mqtt_use_ssl,
            username=settings.downstream_mqtt_username,
            password=settings.downstream_mqtt_password,
        )


class DownstreamMqttClient:
    """Publishes messages to the downstream MQTT broker.

    Implements MqttPublisher. Manages a single persistent aiomqtt connection
    that must be established via the async context manager before publishing.
    """

    def __init__(self, config: DownstreamConnectionConfig) -> None:
        self._config = config
        self._client: aiomqtt.Client | None = None

    @asynccontextmanager
    async def connected(self) -> AsyncGenerator["DownstreamMqttClient"]:
        tls_params = aiomqtt.TLSParameters() if self._config.use_ssl else None
        async with aiomqtt.Client(
            hostname=self._config.host,
            port=self._config.port,
            tls_params=tls_params,
            username=self._config.username,
            password=self._config.password,
        ) as client:
            self._client = client
            logger.info(
                "Connected to downstream broker",
                extra={"host": self._config.host, "port": self._config.port},
            )
            try:
                yield self
            finally:
                self._client = None

    async def publish(
        self,
        topic: str,
        payload: str | bytes,
        *,
        retain: bool,
    ) -> None:
        if self._client is None:
            raise RuntimeError("DownstreamMqttClient is not connected")
        await self._client.publish(topic, payload=payload, retain=retain)
        logger.debug(
            "Published to downstream", extra={"topic": topic, "retain": retain}
        )
