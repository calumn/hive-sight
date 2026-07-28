import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    allowed_origins: list[str]
    database_url: str
    redis_url: str
    object_storage_endpoint: str
    object_storage_bucket: str


def load_settings() -> Settings:
    return Settings(
        allowed_origins=_csv_env("CORE_API_ALLOWED_ORIGINS", "http://localhost:5173"),
        database_url=os.getenv(
            "CORE_API_DATABASE_URL",
            "postgresql://beehive:beehive@localhost:5432/beehive_core",
        ),
        redis_url=os.getenv("CORE_API_REDIS_URL", "redis://localhost:6379/0"),
        object_storage_endpoint=os.getenv(
            "CORE_API_OBJECT_STORAGE_ENDPOINT",
            "http://localhost:9000",
        ),
        object_storage_bucket=os.getenv("CORE_API_OBJECT_STORAGE_BUCKET", "beehive-monitor-local"),
    )


def _csv_env(name: str, default: str) -> list[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]
