import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    allowed_origins: list[str]
    database_url: str
    redis_url: str
    object_storage_endpoint: str
    object_storage_bucket: str
    prelabeler: str
    bee_detector_training_adapter: str
    model_artifact_root: str
    database_purpose: str
    yolo_base_weights: str
    yolo_device: str
    object_storage_root: str = "var/object-storage"
    persistence_backend: str = "in_memory"


def load_settings() -> Settings:
    return Settings(
        allowed_origins=_csv_env(
            "CORE_API_ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ),
        persistence_backend=os.getenv("HIVESIGHT_PERSISTENCE_BACKEND", "in_memory"),
        database_url=os.getenv(
            "CORE_API_DATABASE_URL",
            "postgresql://hive_sight:hive_sight@localhost:5432/hive_sight_core_dev",
        ),
        redis_url=os.getenv("CORE_API_REDIS_URL", "redis://localhost:6379/0"),
        object_storage_endpoint=os.getenv(
            "CORE_API_OBJECT_STORAGE_ENDPOINT",
            "http://localhost:9000",
        ),
        object_storage_bucket=os.getenv("CORE_API_OBJECT_STORAGE_BUCKET", "hive-sight-local"),
        object_storage_root=os.getenv("HIVESIGHT_OBJECT_STORAGE_ROOT", "var/object-storage"),
        prelabeler=os.getenv("HIVESIGHT_PRELABELER", "deterministic"),
        bee_detector_training_adapter=os.getenv("HIVESIGHT_BEE_TRAINING_ADAPTER", "fake"),
        model_artifact_root=os.getenv("HIVESIGHT_MODEL_ARTIFACT_ROOT", "var/model-runs"),
        database_purpose=os.getenv("HIVESIGHT_DATABASE_PURPOSE", "dev"),
        yolo_base_weights=os.getenv("HIVESIGHT_YOLO_BASE_WEIGHTS", "yolo11n-obb.pt"),
        yolo_device=os.getenv("HIVESIGHT_YOLO_DEVICE", "cpu"),
    )


def _csv_env(name: str, default: str) -> list[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]
