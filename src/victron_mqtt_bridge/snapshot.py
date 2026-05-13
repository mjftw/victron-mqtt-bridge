"""One-shot snapshot of Victron MQTT topics, written as JSON.

Usage:
    victron-snapshot 192.168.1.83
    victron-snapshot 192.168.1.83 --topic 'solarcharger/' --topic 'system/0/Dc/Battery/'
    victron-snapshot 192.168.1.83 --topic 'solarcharger/' -o snapshot.json

Each --topic is a relative Victron path (segment after N/<serial>/).
A trailing '/' subscribes to the whole branch via '#'; otherwise an exact topic is used.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import TextIO

import aiomqtt
import click

from victron_mqtt_bridge.client.victron_mqtt_client import (
    VICTRON_DATA_PREFIX_TEMPLATE,
    discover_serial,
    send_keepalive,
)

logger = logging.getLogger(__name__)


async def _collect(
    host: str,
    use_ssl: bool,
    topics: tuple[str, ...],
    timeout: float,
) -> dict[str, object]:
    """Connect to the Victron broker, subscribe to topics, and collect messages."""
    port = 8883 if use_ssl else 1883
    tls_params = aiomqtt.TLSParameters() if use_ssl else None
    results: dict[str, object] = {}

    async with aiomqtt.Client(hostname=host, port=port, tls_params=tls_params) as client:
        serial = await discover_serial(client)
        prefix = VICTRON_DATA_PREFIX_TEMPLATE.format(serial=serial)

        for topic in topics:
            # Strip any leading slash — topics are relative to the device prefix.
            # "/" (the default "everything") becomes just "#" after stripping.
            relative = topic.lstrip("/")
            mqtt_topic = f"{prefix}{relative}#" if (not relative or relative.endswith("/")) else f"{prefix}{relative}"
            await client.subscribe(mqtt_topic)
            logger.debug("Subscribed to %s", mqtt_topic)

        await send_keepalive(client, serial)

        try:
            async with asyncio.timeout(timeout):
                async for message in client.messages:
                    topic_str = str(message.topic)
                    if not topic_str.startswith(prefix):
                        continue
                    relative = topic_str[len(prefix):]
                    try:
                        results[relative] = json.loads(message.payload)
                    except (json.JSONDecodeError, TypeError):
                        results[relative] = str(message.payload)
        except TimeoutError:
            pass

    return results


@click.command()
@click.argument("host")
@click.option(
    "--ssl", "use_ssl", is_flag=True, default=False,
    help="Use TLS/SSL on port 8883 (default: plain MQTT on port 1883).",
)
@click.option(
    "--topic",
    "topics",
    multiple=True,
    default=["/"],
    show_default=True,
    help=(
        "Relative Victron topic path to snapshot. "
        "Trailing '/' subscribes to the whole branch (e.g. 'solarcharger/'). "
        "Exact path for a single leaf (e.g. 'system/0/Dc/Battery/Soc'). "
        "May be repeated. Defaults to '/' (everything)."
    ),
)
@click.option(
    "--timeout",
    default=5.0,
    show_default=True,
    help="Seconds to wait for messages before exiting.",
)
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    default=None,
    help="File to write JSON output to. Defaults to stdout.",
)
def snapshot(
    host: str,
    use_ssl: bool,
    topics: tuple[str, ...],
    timeout: float,
    output: Path | None,
) -> None:
    """Collect a one-shot JSON snapshot of matching Victron MQTT topics.

    HOST is the hostname or IP address of the Victron Cerbo GX MQTT broker.

    Connects, subscribes, and collects messages for --timeout seconds.
    The output contains the latest value seen for each topic during that window.
    """
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    results = asyncio.run(_collect(host, use_ssl, topics, timeout))

    def _write(f: TextIO) -> None:
        json.dump(results, f, indent=2, sort_keys=True)
        f.write("\n")

    if output is None:
        _write(sys.stdout)
    else:
        output.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
        click.echo(f"Wrote {len(results)} topics to {output}", err=True)
