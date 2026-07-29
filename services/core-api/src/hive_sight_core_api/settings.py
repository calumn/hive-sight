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
    grounding_dino_model_id: str
    grounding_dino_checkpoint: str
    grounding_dino_prompt: str
    grounding_dino_box_threshold: float
    grounding_dino_text_threshold: float
    grounding_dino_max_box_area_ratio: float
    grounding_dino_device: str
    grounding_dino_local_files_only: bool


def load_settings() -> Settings:
    return Settings(
        allowed_origins=_csv_env(
            "CORE_API_ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ),
        database_url=os.getenv(
            "CORE_API_DATABASE_URL",
            "postgresql://hive_sight:hive_sight@localhost:5432/hive_sight_core",
        ),
        redis_url=os.getenv("CORE_API_REDIS_URL", "redis://localhost:6379/0"),
        object_storage_endpoint=os.getenv(
            "CORE_API_OBJECT_STORAGE_ENDPOINT",
            "http://localhost:9000",
        ),
        object_storage_bucket=os.getenv("CORE_API_OBJECT_STORAGE_BUCKET", "hive-sight-local"),
        prelabeler=os.getenv("HIVESIGHT_PRELABELER", "deterministic"),
        grounding_dino_model_id=os.getenv(
            "HIVESIGHT_GROUNDING_DINO_MODEL_ID",
            "IDEA-Research/grounding-dino-tiny",
        ),
        grounding_dino_checkpoint=os.getenv("HIVESIGHT_GROUNDING_DINO_CHECKPOINT", ""),
        grounding_dino_prompt=os.getenv(
            "HIVESIGHT_GROUNDING_DINO_PROMPT",
            "honey bee . partial honey bee",
        ),
        grounding_dino_box_threshold=_float_env("HIVESIGHT_GROUNDING_DINO_BOX_THRESHOLD", 0.35),
        grounding_dino_text_threshold=_float_env("HIVESIGHT_GROUNDING_DINO_TEXT_THRESHOLD", 0.25),
        grounding_dino_max_box_area_ratio=_float_env(
            "HIVESIGHT_GROUNDING_DINO_MAX_BOX_AREA_RATIO",
            0.04,
        ),
        grounding_dino_device=os.getenv("HIVESIGHT_GROUNDING_DINO_DEVICE", "auto"),
        grounding_dino_local_files_only=_bool_env(
            "HIVESIGHT_GROUNDING_DINO_LOCAL_FILES_ONLY",
            False,
        ),
    )


def _csv_env(name: str, default: str) -> list[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().casefold() in {"1", "true", "yes", "on"}
