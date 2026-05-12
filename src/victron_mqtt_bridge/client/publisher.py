from typing import Protocol, runtime_checkable


@runtime_checkable
class MqttPublisher(Protocol):
    """Publishes a single message to an MQTT broker.

    Concrete implementations manage their own connection lifecycle.
    Typed as a Protocol so tests can inject a fake without touching the network.
    """

    async def publish(
        self,
        topic: str,
        payload: str | bytes,
        *,
        retain: bool,
    ) -> None: ...
