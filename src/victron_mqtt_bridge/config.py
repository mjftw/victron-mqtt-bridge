from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    victron_mqtt_host: str
    victron_mqtt_use_ssl: bool = False
    keepalive_interval_seconds: int = 60

    # JSON-encoded mapping of Victron relative paths to downstream topics.
    # e.g. TOPIC_MAPPING='{"system/0/Dc/Battery/Soc": "victron/battery/soc"}'
    topic_mapping: dict[str, str]

    downstream_mqtt_host: str
    downstream_mqtt_port: int = 1883
    downstream_mqtt_use_ssl: bool = False
    downstream_mqtt_username: str | None = None
    downstream_mqtt_password: str | None = None

    @property
    def victron_mqtt_port(self) -> int:
        return 8883 if self.victron_mqtt_use_ssl else 1883
