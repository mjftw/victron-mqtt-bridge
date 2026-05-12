# AGENTS.md

Context and conventions for AI agents working in this repository. Read this before making any changes.

---

## What this repo is

A lightweight Python service that bridges a [Victron Cerbo GX](https://www.victronenergy.com/panel-systems-remote-monitoring/cerbo-gx) MQTT broker to a downstream MQTT broker (e.g. Home Assistant, InfluxDB, Node-RED). Two problems make a plain MQTT bridge insufficient:

1. The Cerbo GX requires a periodic keepalive publish to `R/<serial>/keepalive` or it stops streaming after ~60 s. This service manages that automatically.
2. Victron topics are serial-prefixed and deeply nested. This service remaps selected topics to stable, user-defined downstream names so downstream clients never see Victron internals.

---

## Repo structure

```
src/victron_mqtt_bridge/
├── config.py                      # pydantic-settings; all env config in one place
├── topic_mapping.py               # TopicMapping type alias + resolve_topic() pure fn
├── main.py                        # entry point; wires all components together
├── banner.py                      # startup banner display
├── connectivity.py                # pre-flight broker reachability check
└── client/
    ├── publisher.py               # MqttPublisher Protocol (the interface)
    ├── downstream_mqtt_client.py  # concrete MqttPublisher for the downstream broker
    └── victron_mqtt_client.py     # Victron connection, serial discovery, keepalive, routing

tests/
├── fakes/fake_mqtt_publisher.py        # in-memory MqttPublisher; use in all tests
├── test_topic_mapping.py               # unit tests for resolve_topic()
└── client/test_victron_mqtt_client.py  # unit tests for routing and fake behaviour

local-dev/                         # docker-compose for a local Mosquitto broker
docs/                              # Victron topic reference
.github/workflows/
├── ci.yaml                        # lint + typecheck + test; build + push image on tags
└── release-please.yaml            # automated semver bump + GitHub Release via Release Please
```

---

## Tech stack

| Tool | Role |
|---|---|
| Python 3.13 | Runtime |
| [uv](https://docs.astral.sh/uv/) | Dependency management and virtualenv |
| [aiomqtt](https://aiomqtt.bo5ter.de/) | Async MQTT client |
| [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | Config from env / `.env` |
| [ruff](https://docs.astral.sh/ruff/) | Linting and formatting |
| [ty](https://github.com/astral-sh/ty) | Type checking |
| [pytest](https://docs.pytest.org/) + [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) | Testing |
| [just](https://just.systems) | Task runner |
| Docker | Image build; local dev broker |

---

## Running checks

Always run checks before committing:

```sh
just          # lint + typecheck + test in one step
```

Individual commands:

```sh
just lint       # ruff check src/ tests/
just format     # ruff format src/ tests/
just typecheck  # ty check src/
just test       # pytest
```

CI runs the same checks on every push and PR. All must pass before merging.

---

## Code style

### General

- **Functional style, minimal mutability.** Prefer pure functions over stateful methods. Extract logic from classes into module-level functions when it doesn't need `self`.
- **Strict typing everywhere.** All functions and methods must have complete type annotations — parameters and return types. `ty` enforces this in CI.
- **Concise and readable over clever.** Clear names, straightforward constructs.
- **No narrating comments.** Only comment non-obvious intent, trade-offs, or constraints. Never restate what the code does.

### Python specifics

Use Python 3.12+ syntax throughout:

```python
# Type aliases — use the `type` keyword, not TypeAlias
type TopicMapping = Mapping[str, str]

# Unions — use X | Y, not Optional[X] or Union[X, Y]
def foo(x: str | None) -> str | None: ...
```

**Protocols over ABCs** for interfaces. Mark them `@runtime_checkable` when structural `isinstance` checks are needed:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class MqttPublisher(Protocol):
    async def publish(self, topic: str, payload: str | bytes, *, retain: bool) -> None: ...
```

**Dataclasses** for plain data containers (no behaviour). Prefer frozen when the data is immutable.

**Module-level logger** in every module that emits logs:

```python
logger = logging.getLogger(__name__)
```

**Section dividers** in longer modules to group related functions:

```python
# ---------------------------------------------------------------------------
# Keep-alive
# ---------------------------------------------------------------------------
```

### Ruff rules in force

`E`, `F`, `I` (isort), `UP` (pyupgrade), `ANN` (annotations), `S` (bandit security). `S101` (assert) is allowed in `tests/**`.

---

## Testing

### Conventions

- Test files live under `tests/`, mirroring the `src/` structure.
- **No mocks.** Use `FakeMqttPublisher` (`tests/fakes/fake_mqtt_publisher.py`) — a real implementation of the `MqttPublisher` Protocol that records every `publish()` call. Add new fakes to `tests/fakes/` following the same pattern.
- **Test naming:** `test_should_<expected behaviour>_when_<condition>`:

```python
def test_should_return_none_when_topic_is_not_in_mapping() -> None: ...
async def test_should_record_published_message_when_publish_is_called() -> None: ...
```

- **Pure functions first.** Extract logic into pure functions so it can be tested without any broker or network. `resolve_topic()` is the model for this.
- `asyncio_mode = "auto"` is set in `pyproject.toml` — no `@pytest.mark.asyncio` decorator needed on individual tests.

### Adding a new fake

Create `tests/fakes/fake_<name>.py`. Implement the Protocol structurally (no inheritance). Record calls in a public list attribute (e.g. `published`). Add a `test_should_satisfy_<protocol>_protocol` test to confirm structural compatibility.

---

## Architecture constraints

- **All config comes from environment variables** via `Settings` in `config.py` (pydantic-settings). Never hardcode host, port, credentials, or topic mappings. Never add a config file format — only env vars / `.env`.
- **The keepalive is mandatory.** The Cerbo GX stops streaming after ~60 s without a publish to `R/<serial>/keepalive`. Do not remove or break the keepalive loop in `VictronMqttClient`.
- **Serial is discovered at runtime.** The Victron serial number is not known at config time; it is discovered by subscribing to `N/+/system/0/Serial` on connection. Any code that builds Victron topic strings must use the discovered serial.
- **Topic mapping precedence:** exact key wins over branch key; among branch keys, the longest (most specific) wins. This is implemented in `resolve_topic()` — do not duplicate or bypass this logic.
- **`MqttPublisher` is the only interface between the Victron client and the downstream broker.** Keep it narrow (single `publish` method). Do not add methods to the Protocol unless strictly necessary.

---

## Commit style

**[Conventional Commits](https://www.conventionalcommits.org/)** — required, not optional. Release Please reads commits to calculate the next semver version and generate the changelog.

```
<type>(<scope>): <short description>
```

| Type | Bump |
|---|---|
| `feat` | minor |
| `fix`, `perf` | patch |
| `feat!` / `BREAKING CHANGE:` footer | major |
| `chore`, `docs`, `refactor`, `test` | none |

Commits must be single-purpose. One logical change per commit.

---

## Release process

Do **not** manually edit `pyproject.toml` version, create git tags, or write release notes.

1. Merge conventional commits to `main` as normal.
2. Release Please maintains an auto-updated PR (e.g. `chore(main): release 1.2.0`) that bumps the version in `pyproject.toml` and updates `CHANGELOG.md`.
3. Merge the Release PR when ready to ship.
4. Release Please creates the tag and GitHub Release automatically.
5. CI builds and pushes `mjftw/victron-mqtt-bridge:<version>` to Docker Hub.

---

## CI summary

| Workflow | Trigger | Jobs |
|---|---|---|
| `ci.yaml` | push (any branch), PR to `main` | `check`: lint + typecheck + test |
| `ci.yaml` | push to `main` or version tag | `build-push`: Docker build + push to Docker Hub |
| `release-please.yaml` | push to `main` | Creates/updates the release PR |

Docker Hub credentials are stored as `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` repository secrets. The release job uses the built-in `GITHUB_TOKEN`.
