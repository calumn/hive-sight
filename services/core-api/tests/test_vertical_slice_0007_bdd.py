from dataclasses import replace
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

from hive_sight_core_api.dependencies import build_bee_prelabeler
from hive_sight_core_api.settings import Settings

FEATURES_DIR = Path(__file__).parent / "features"

scenarios(str(FEATURES_DIR / "vertical_slice_0007_grounding_dino_pre_labelling_adapter.feature"))


@given("Grounding DINO has been retired by ADR 0005")
def grounding_dino_retired() -> None:
    adr = Path(__file__).parents[3] / "architecture/adr/0005-retire-grounding-dino-for-bee-candidate-annotation.md"
    assert adr.exists()
    assert "Grounding DINO is retired" in adr.read_text(encoding="utf-8")


@when("the Core API pre-labeller dependency is configured for Grounding DINO")
def configured_for_grounding_dino() -> None:
    with pytest.raises(ValueError, match="Unknown HiveSight pre-labeller provider"):
        build_bee_prelabeler(replace(_settings(), prelabeler="grounding_dino"))


@then("the Core API rejects that pre-labeller configuration")
def rejected_configuration() -> None:
    assert True


@then("deterministic pre-labelling remains the supported local default")
def deterministic_default_remains_supported() -> None:
    prelabeler = build_bee_prelabeler(_settings())
    assert prelabeler.provider == "deterministic"


def _settings() -> Settings:
    return Settings(
        allowed_origins=["http://localhost:5173"],
        database_url="postgresql://hive_sight:hive_sight@localhost:5432/hive_sight_core_dev",
        redis_url="redis://localhost:6379/0",
        object_storage_endpoint="http://localhost:9000",
        object_storage_bucket="hive-sight-local",
        prelabeler="deterministic",
        bee_detector_training_adapter="fake",
        bee_orientation_training_adapter="fake",
        model_artifact_root="var/model-runs",
        database_purpose="dev",
        yolo_base_weights="yolo11n-obb.pt",
        yolo_device="cpu",
        bee_orientation_device="cpu",
        training_run_stale_after_seconds=300,
        training_run_heartbeat_interval_seconds=5,
    )
