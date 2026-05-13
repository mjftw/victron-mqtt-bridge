# Changelog

## [0.2.0](https://github.com/mjftw/victron-mqtt-bridge/compare/v0.1.0...v0.2.0) (2026-05-13)


### Features

* add victron-snapshot CLI for one-shot topic exploration ([936c11f](https://github.com/mjftw/victron-mqtt-bridge/commit/936c11fed39c5e99019e116e540042147d2e7779))
* **ci:** add GitHub Actions workflow to lint, test, and push image ([a40c3bb](https://github.com/mjftw/victron-mqtt-bridge/commit/a40c3bb1293c17692fffa1b74fb7ecfd06d57467))
* **ci:** add Release Please for automated semver bumps via conventional commits ([cb1adae](https://github.com/mjftw/victron-mqtt-bridge/commit/cb1adae3b74117a5c6768d9b4891836d1edf05fd))
* **ci:** create GitHub Release with auto-generated notes on version tags ([2dab640](https://github.com/mjftw/victron-mqtt-bridge/commit/2dab6408c2ef9bc3f70f43b5f580662fd08f3363))
* **snapshot:** add --depth / -d option to limit output nesting ([0f154e0](https://github.com/mjftw/victron-mqtt-bridge/commit/0f154e01d3e3fa1b29ff9b00eb4042248ce5db61))
* **snapshot:** output nested JSON tree instead of flat key paths ([3507ceb](https://github.com/mjftw/victron-mqtt-bridge/commit/3507ceb7973f9a076ff9bff0879499ecaedc83c6))
* **victron-mqtt-bridge:** add FakeMqttPublisher and behavior-based unit tests ([fef7b7a](https://github.com/mjftw/victron-mqtt-bridge/commit/fef7b7aecf442a1714d66d1608a6bb89fe4dfeaa))
* **victron-mqtt-bridge:** add local-dev Mosquitto broker and wire up .env.example ([61def7f](https://github.com/mjftw/victron-mqtt-bridge/commit/61def7fbbbbd6a7ad563e79e39a66cc052ebc84c))
* **victron-mqtt-bridge:** add main entry point ([b6f1320](https://github.com/mjftw/victron-mqtt-bridge/commit/b6f132045f77ea21bf3474c407de2dfb430cead5))
* **victron-mqtt-bridge:** add MqttPublisher protocol and TopicMapping type ([0d788f2](https://github.com/mjftw/victron-mqtt-bridge/commit/0d788f2c2294200f522622753272b34a8591ca17))
* **victron-mqtt-bridge:** add multi-stage Dockerfile ([a5856ae](https://github.com/mjftw/victron-mqtt-bridge/commit/a5856ae3da9477f0e5ae9c72eb22d6d1acdd786a))
* **victron-mqtt-bridge:** add pre-flight connectivity checks ([1ec60b6](https://github.com/mjftw/victron-mqtt-bridge/commit/1ec60b6beb7577c0fecf6aeb8e82e0fc7012dda6))
* **victron-mqtt-bridge:** add Settings config module ([7dcba2b](https://github.com/mjftw/victron-mqtt-bridge/commit/7dcba2bdd399c7e523f75f57e8b28d1359e64803))
* **victron-mqtt-bridge:** add startup banner ([d97139d](https://github.com/mjftw/victron-mqtt-bridge/commit/d97139d3af2f7b112cd6b6bf858fe2863a6c4821))
* **victron-mqtt-bridge:** implement DownstreamMqttClient ([ca27712](https://github.com/mjftw/victron-mqtt-bridge/commit/ca2771281783d0325fffd160ab7016c92af5e3db))
* **victron-mqtt-bridge:** implement VictronMqttClient with serial discovery, keep-alive, and topic bridging ([18078a2](https://github.com/mjftw/victron-mqtt-bridge/commit/18078a2ca24de1a1c8d18e9bb3a6e1342638d93f))
* **victron-mqtt-bridge:** load TOPIC_MAPPING from env as a JSON string ([9e4a834](https://github.com/mjftw/victron-mqtt-bridge/commit/9e4a8343ffc125eac174ec0c96a12fb57cf8835b))
* **victron-mqtt-bridge:** log available topic tree on startup ([709a7e0](https://github.com/mjftw/victron-mqtt-bridge/commit/709a7e0be93f1e285647b5f806a952f2b44d1124))
* **victron-mqtt-bridge:** print non-secret settings on startup ([d171549](https://github.com/mjftw/victron-mqtt-bridge/commit/d171549fdb0749e541b3b84635b046060422433b))
* **victron-mqtt-bridge:** scaffold uv project with deps and tooling ([b822c96](https://github.com/mjftw/victron-mqtt-bridge/commit/b822c96ec95411ac45b4e18056495f42a6715978))
* **victron-mqtt-bridge:** support branch (subtree) topic mappings ([2a055a0](https://github.com/mjftw/victron-mqtt-bridge/commit/2a055a017a9ffeedc3f230bdb3ac6b9a1eccf30e))


### Bug Fixes

* **docker:** use /app workdir in builder so venv shebangs match runtime path ([4f11105](https://github.com/mjftw/victron-mqtt-bridge/commit/4f11105947f37521845ed4ee2cfb04d711d2b8de))
* **lint:** set ruff line-length to 120 and fix import ordering ([a664dfe](https://github.com/mjftw/victron-mqtt-bridge/commit/a664dfec1de70eb4aba322e1d40bf58cf254e551))
* **snapshot:** strip leading slash from topic to avoid double-slash in MQTT path ([3c50fe4](https://github.com/mjftw/victron-mqtt-bridge/commit/3c50fe4ec2c7cdc7100e5b06a8afce99376fa592))
* **victron-mqtt-bridge:** copy README.md into Docker builder stage ([f105d0a](https://github.com/mjftw/victron-mqtt-bridge/commit/f105d0a3d20516c6755fcaccb6a2f01ba7eee3b4))
* **victron-mqtt-bridge:** improve log messages and handle graceful shutdown ([cdb3e5d](https://github.com/mjftw/victron-mqtt-bridge/commit/cdb3e5d3624ee49ff95add05b3489a44fc9fbb5f))
* **victron-mqtt-bridge:** silence ty false positive and fix dev-watch deps ([0bafc50](https://github.com/mjftw/victron-mqtt-bridge/commit/0bafc50825b3cd9346eaf8cc491a0d9ad93d1c6f))


### Documentation

* add AGENTS.md with conventions and architecture context for AI agents ([56ae92d](https://github.com/mjftw/victron-mqtt-bridge/commit/56ae92d21e91d3f63e846b4f3323ceb2c278f7ea))
* add CONTRIBUTING guide and trim duplicated content from README ([1556309](https://github.com/mjftw/victron-mqtt-bridge/commit/1556309dab0247e0cb4b06a80bceede632e1ae54))
* add Docker Hub badge and pre-built image usage to README ([382e503](https://github.com/mjftw/victron-mqtt-bridge/commit/382e5034e4d7533ed9ed40245fb33873312d2131))
* clarify victron-snapshot as CLI for exploration and automations ([18e79be](https://github.com/mjftw/victron-mqtt-bridge/commit/18e79be6ea332433756c58a2aeb610d84037618c))
* expand why this exists with topic remapping motivation ([c53ec2e](https://github.com/mjftw/victron-mqtt-bridge/commit/c53ec2e760918b487d58da3d8d5467f1d152ec09))
* overhaul README and add MIT licence ([612312d](https://github.com/mjftw/victron-mqtt-bridge/commit/612312d94153f6770e52a678e932523e480d432c))
* **snapshot:** restore HOST argument description in help text ([3c2c92f](https://github.com/mjftw/victron-mqtt-bridge/commit/3c2c92f7aecff0f5cacfb716ec6443437433258d))
* trim features list to user-facing value only ([0bff4aa](https://github.com/mjftw/victron-mqtt-bridge/commit/0bff4aa0c5f108c964a392012e0a307b6919de87))
* **victron-mqtt-bridge:** add README with setup and env-var reference ([d3de045](https://github.com/mjftw/victron-mqtt-bridge/commit/d3de045609d50fc84d7057308267bcf73f62b365))
* **victron-mqtt-bridge:** add Victron MQTT topic reference ([53a5972](https://github.com/mjftw/victron-mqtt-bridge/commit/53a5972042c1ac0ffb8cf4d3e34d3d8a6d7ce42c))
* **victron-mqtt-bridge:** expand .env.example with inline documentation ([1b60a77](https://github.com/mjftw/victron-mqtt-bridge/commit/1b60a7733a7aafdf9e764f0924d10093778c4e6e))
* **victron-mqtt-bridge:** rewrite README with full project explanation ([ac217d2](https://github.com/mjftw/victron-mqtt-bridge/commit/ac217d28a8a5725780a10155d70f8623d4b50b01))
