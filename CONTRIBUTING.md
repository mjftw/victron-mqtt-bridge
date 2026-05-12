# Contributing

Contributions are welcome — bug fixes, new features, documentation improvements, and test coverage are all appreciated. Please read this guide before opening a pull request.

---

## Table of Contents

- [Getting started](#getting-started)
- [Development workflow](#development-workflow)
- [Commit style](#commit-style)
- [Pull requests](#pull-requests)
- [Releases](#releases)
- [Code style](#code-style)
- [Project structure](#project-structure)
- [Testing approach](#testing-approach)
- [License](#license)

---

## Getting started

You will need:

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- [just](https://just.systems) (optional but recommended)
- Docker (for local broker and image builds)

```sh
git clone https://github.com/mjftw/victron-mqtt-bridge.git
cd victron-mqtt-bridge
uv sync          # install all deps including dev
cp .env.example .env
```

---

## Development workflow

Run all checks before pushing:

```sh
just             # lint + typecheck + test in one step
```

Individual commands:

| Command | Description |
|---|---|
| `just` | lint + typecheck + test (default) |
| `just lint` | `ruff check` |
| `just format` | `ruff format` |
| `just typecheck` | `ty check` |
| `just test` | `pytest` |
| `just run` | run the bridge locally (reads `.env`) |
| `just build` | build Docker image |
| `just dev-up` | start local Mosquitto broker |
| `just dev-down` | stop local Mosquitto broker |
| `just dev-watch` | start broker + bridge and subscribe to all topics |

A local Mosquitto broker (`local-dev/docker-compose.yaml`) is available as the downstream target while developing:

```sh
just dev-up     # start broker on localhost:1883
just run        # run the bridge against it
just dev-watch  # tail all messages arriving on the broker
just dev-down   # stop the broker
```

Without `just`:

```sh
docker compose -f local-dev/docker-compose.yaml up -d
mosquitto_sub -h localhost -t '#' -v
```

---

## Commit style

This project uses **[Conventional Commits](https://www.conventionalcommits.org/)** — the format is required because it drives automated version bumps and changelog generation (see [Releases](#releases) below).

```
<type>(<scope>): <short description>

[optional body explaining why, not what]
```

**Types:**

| Type | When to use | Version bump |
|---|---|---|
| `feat` | new user-facing capability | minor |
| `fix` | bug fix | patch |
| `chore` | maintenance, deps, config | none |
| `docs` | documentation only | none |
| `refactor` | internal restructure, no behaviour change | none |
| `test` | adding or fixing tests | none |
| `perf` | performance improvement | patch |

**Breaking changes** — add `!` after the type or include a `BREAKING CHANGE:` footer:

```
feat!: remove LEGACY_MODE env var

BREAKING CHANGE: LEGACY_MODE is no longer supported. Remove it from your .env.
```

Breaking changes trigger a **major** version bump.

**Examples:**

```
feat(config): add SSL support for upstream Victron broker
fix(keepalive): prevent double-send on reconnect
docs: document branch mapping precedence rules
chore(deps): update aiomqtt to 2.6.0
```

Commits should be single-purpose. Avoid bundling unrelated changes in one commit.

---

## Pull requests

1. Fork the repository and create a branch from `main`.
2. Open an issue first for non-trivial changes so the approach can be discussed before you invest time writing code.
3. Run `just` and ensure all checks pass before opening a PR.
4. Write conventional commits — the PR title and commit messages are what populate the changelog.
5. Keep the PR focused. Separate unrelated fixes or improvements into their own PRs.

CI runs lint, typecheck, and tests on every PR. A PR cannot be merged until all checks are green.

---

## Releases

Releases are fully automated via [Release Please](https://github.com/googleapis/release-please).

**How it works:**

1. Conventional commits are pushed to `main` as normal development continues.
2. Release Please maintains an open PR titled something like `chore(main): release 1.2.0`. It accumulates all unreleased commits, calculates the next version from commit types, bumps the version in `pyproject.toml`, and updates `CHANGELOG.md`.
3. When it is time to cut a release, merge the Release PR.
4. Release Please automatically creates the git tag and a GitHub Release with the generated changelog.
5. CI picks up the new tag, builds the Docker image, and pushes it to Docker Hub as `mjftw/victron-mqtt-bridge:<version>`.

**Version rules (semver):**

| Commit type | Version bump |
|---|---|
| `fix`, `perf` | patch — `1.2.3` → `1.2.4` |
| `feat` | minor — `1.2.3` → `1.3.0` |
| `feat!` or `BREAKING CHANGE:` | major — `1.2.3` → `2.0.0` |
| `chore`, `docs`, `refactor`, `test` | no bump |

You do not need to manually edit the version in `pyproject.toml`, create tags, or write release notes.

---

## Code style

- **Functional style, strict typing, minimal mutability.** Prefer pure functions over stateful classes where practical.
- **Concise and readable over clever.** Clear names and straightforward constructs are preferred.
- **No comments that narrate the code.** Comments should explain non-obvious intent, trade-offs, or constraints — not restate what the code does.
- **Strict type annotations on all public functions and methods.** The type checker (`ty`) is run in CI.
- **Linting:** `ruff` enforces `E`, `F`, `I`, `UP`, `ANN`, and `S` rules. Run `just format` to auto-fix formatting issues.

---

## Project structure

```
src/victron_mqtt_bridge/
├── config.py                      # all settings (pydantic-settings, env-driven)
├── topic_mapping.py               # TopicMapping type alias + resolve_topic()
├── main.py                        # entry point; wires components together
└── client/
    ├── publisher.py               # MqttPublisher Protocol
    ├── downstream_mqtt_client.py  # publishes to the downstream broker
    └── victron_mqtt_client.py     # connects to Victron, runs keepalive, bridges messages

tests/
├── fakes/fake_mqtt_publisher.py        # in-memory MqttPublisher for use in tests
├── test_topic_mapping.py               # unit tests for resolve_topic()
└── client/test_victron_mqtt_client.py  # behaviour-based tests (test_should_X_when_Y)
```

---

## Testing approach

Tests live under `tests/`. Run them with `just test` or `uv run pytest`.

No mocks. `FakeMqttPublisher` (`tests/fakes/fake_mqtt_publisher.py`) is a real implementation of the `MqttPublisher` Protocol that records every `publish()` call in memory. Test against real behaviour, not implementation details.

Name test functions `test_should_<expected behaviour>_when_<condition>`. This keeps tests readable as specifications:

```python
async def test_should_remap_topic_when_leaf_mapping_matches() -> None:
    ...
```

Pure functions (like `resolve_topic()`) are tested directly with known inputs — no broker or network needed.

---

## License

By submitting a pull request you agree that your contributions will be licensed under the [MIT licence](LICENSE). There is no formal CLA.
