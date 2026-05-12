import asyncio
from dataclasses import dataclass

_TCP_TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True)
class ConnectivityResult:
    label: str
    host: str
    port: int
    reachable: bool
    error: str | None = None

    def display_line(self) -> str:
        status = "✓" if self.reachable else "✗"
        addr = f"{self.host}:{self.port}"
        detail = f" — {self.error}" if self.error else ""
        return f"  {status} {self.label} ({addr}){detail}"


async def _check_tcp(
    label: str,
    host: str,
    port: int,
    timeout: float = _TCP_TIMEOUT_SECONDS,
) -> ConnectivityResult:
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        writer.close()
        await writer.wait_closed()
        return ConnectivityResult(label=label, host=host, port=port, reachable=True)
    except TimeoutError:
        return ConnectivityResult(
            label=label,
            host=host,
            port=port,
            reachable=False,
            error=f"timed out after {timeout:.0f}s",
        )
    except OSError as exc:
        return ConnectivityResult(
            label=label,
            host=host,
            port=port,
            reachable=False,
            error=str(exc),
        )


async def check_all(
    victron_host: str,
    victron_port: int,
    downstream_host: str,
    downstream_port: int,
) -> list[ConnectivityResult]:
    """Run TCP reachability checks for both brokers concurrently."""
    return list(
        await asyncio.gather(
            _check_tcp("Victron broker", victron_host, victron_port),
            _check_tcp("Downstream broker", downstream_host, downstream_port),
        )
    )
