from dataclasses import dataclass


@dataclass
class PublishedMessage:
    topic: str
    payload: str | bytes
    retain: bool


class FakeMqttPublisher:
    """In-memory MqttPublisher that records every publish call.

    Satisfies the MqttPublisher Protocol structurally — no inheritance, no
    patching. Inject into any component that depends on MqttPublisher and
    assert on .published afterwards.
    """

    def __init__(self) -> None:
        self.published: list[PublishedMessage] = []

    async def publish(
        self,
        topic: str,
        payload: str | bytes,
        *,
        retain: bool,
    ) -> None:
        self.published.append(
            PublishedMessage(topic=topic, payload=payload, retain=retain)
        )
