import pytest

from tests.fakes.fake_mqtt_publisher import FakeMqttPublisher
from victron_mqtt_bridge.client.publisher import MqttPublisher
from victron_mqtt_bridge.client.victron_mqtt_client import resolve_downstream_topic

SERIAL = "abc123def456"
MAPPING = {
    "battery/0/Soc": "home/battery/soc",
    "system/0/Ac/Grid/L1/Power": "home/grid/l1/power",
}


# ---------------------------------------------------------------------------
# resolve_downstream_topic — pure routing logic
# ---------------------------------------------------------------------------


def test_should_return_downstream_topic_when_incoming_topic_is_in_mapping() -> None:
    incoming = f"N/{SERIAL}/battery/0/Soc"
    result = resolve_downstream_topic(incoming, SERIAL, MAPPING)
    assert result == "home/battery/soc"


def test_should_return_correct_topic_for_each_mapped_path() -> None:
    for relative_path, expected_downstream in MAPPING.items():
        incoming = f"N/{SERIAL}/{relative_path}"
        result = resolve_downstream_topic(incoming, SERIAL, MAPPING)
        assert result == expected_downstream


def test_should_return_none_when_topic_is_not_in_mapping() -> None:
    incoming = f"N/{SERIAL}/dc/0/Voltage"
    result = resolve_downstream_topic(incoming, SERIAL, MAPPING)
    assert result is None


def test_should_return_none_when_topic_belongs_to_different_serial() -> None:
    incoming = "N/other_serial/battery/0/Soc"
    result = resolve_downstream_topic(incoming, SERIAL, MAPPING)
    assert result is None


def test_should_return_none_when_topic_does_not_have_victron_prefix() -> None:
    result = resolve_downstream_topic("unrelated/topic", SERIAL, MAPPING)
    assert result is None


def test_should_handle_nested_paths_correctly_when_resolving_topic() -> None:
    incoming = f"N/{SERIAL}/system/0/Ac/Grid/L1/Power"
    result = resolve_downstream_topic(incoming, SERIAL, MAPPING)
    assert result == "home/grid/l1/power"


def test_should_return_none_when_mapping_is_empty() -> None:
    incoming = f"N/{SERIAL}/battery/0/Soc"
    result = resolve_downstream_topic(incoming, SERIAL, {})
    assert result is None


# ---------------------------------------------------------------------------
# FakeMqttPublisher — verifies the fake satisfies the Protocol and records correctly
# ---------------------------------------------------------------------------


def test_should_satisfy_mqtt_publisher_protocol() -> None:
    fake = FakeMqttPublisher()
    assert isinstance(fake, MqttPublisher)


@pytest.mark.asyncio
async def test_should_record_published_message_when_publish_is_called() -> None:
    fake = FakeMqttPublisher()
    await fake.publish("some/topic", b"payload", retain=False)
    assert len(fake.published) == 1
    assert fake.published[0].topic == "some/topic"
    assert fake.published[0].payload == b"payload"
    assert fake.published[0].retain is False


@pytest.mark.asyncio
async def test_should_preserve_retain_flag_when_recording_published_message() -> None:
    fake = FakeMqttPublisher()
    await fake.publish("sensor/temp", "23.5", retain=True)
    assert fake.published[0].retain is True


@pytest.mark.asyncio
async def test_should_record_all_messages_when_multiple_publishes_occur() -> None:
    fake = FakeMqttPublisher()
    await fake.publish("topic/a", "1", retain=False)
    await fake.publish("topic/b", "2", retain=True)
    await fake.publish("topic/c", "3", retain=False)
    assert len(fake.published) == 3
    assert [m.topic for m in fake.published] == ["topic/a", "topic/b", "topic/c"]


@pytest.mark.asyncio
async def test_should_accept_bytes_payload_when_publishing() -> None:
    fake = FakeMqttPublisher()
    await fake.publish("raw/data", b"\x00\x01\x02", retain=False)
    assert fake.published[0].payload == b"\x00\x01\x02"
