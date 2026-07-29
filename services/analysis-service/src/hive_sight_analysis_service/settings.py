import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str
    object_storage_endpoint: str
    object_storage_bucket: str
    model_version: str


def load_settings() -> Settings:
    return Settings(
        database_url=os.getenv(
            "ANALYSIS_DATABASE_URL",
            "postgresql://hive_sight:hive_sight@localhost:5432/hive_sight_analysis",
        ),
        redis_url=os.getenv("ANALYSIS_REDIS_URL", "redis://localhost:6379/1"),
        object_storage_endpoint=os.getenv(
            "ANALYSIS_OBJECT_STORAGE_ENDPOINT",
            "http://localhost:9000",
        ),
        object_storage_bucket=os.getenv("ANALYSIS_OBJECT_STORAGE_BUCKET", "hive-sight-local"),
        model_version=os.getenv("ANALYSIS_MODEL_VERSION", "stub-varroa-detector-0.1.0"),
    )
