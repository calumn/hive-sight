from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from hive_sight_core_api.bee_detector_training_workflow import BeeDetectorTrainingWorkflow
from hive_sight_core_api.dependencies import build_dev_state, get_bee_detector_training_workflow, get_dev_state
from hive_sight_core_api.main import app
from test_model_training_slice import (
    AvailableRealishOrientationAdapter,
    AvailableRealishTrainingAdapter,
    _create_reviewed_crop_item,
    _headers,
    _wait_for_training_run_purpose_status,
    _wait_for_training_run_status,
    _workspace,
)

FEATURES_DIR = Path(__file__).parent / "features"

scenarios(str(FEATURES_DIR / "vertical_slice_0023_real_bee_training_baseline.feature"))


@dataclass
class SliceContext:
    client: TestClient
    workspace_id: str | None = None
    dataset_version: dict[str, object] | None = None
    readiness: dict[str, object] | None = None
    training_start: dict[str, object] | None = None
    localisation_run: dict[str, object] | None = None
    orientation_run: dict[str, object] | None = None


@pytest.fixture
def slice_context(tmp_path: Path) -> SliceContext:
    state = build_dev_state(
        dataset_export_root=tmp_path / "exports",
        model_artifact_root=tmp_path / "model-runs",
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_bee_detector_training_workflow] = lambda: BeeDetectorTrainingWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        artifact_root=state.model_artifact_root,
        adapter=AvailableRealishTrainingAdapter(),
        orientation_adapter=AvailableRealishOrientationAdapter(),
        persistence_backend="postgres",
        database_purpose="dev",
        clock=state.store.clock,
    )
    try:
        yield SliceContext(client=TestClient(app))
    finally:
        app.dependency_overrides.clear()


@given("the Dataset Curator has enough marked bees for real Bee Training")
def enough_marked_bees(slice_context: SliceContext) -> None:
    slice_context.workspace_id = _workspace(slice_context.client)
    for offset in range(4):
        _create_reviewed_crop_item(slice_context.client, slice_context.workspace_id, "training", 10 + offset, 10)
        _create_reviewed_crop_item(slice_context.client, slice_context.workspace_id, "validation", 260 + offset, 10)


@given("the Dataset Curator has too little orientation evidence for real Bee Training")
def too_little_orientation_evidence(slice_context: SliceContext) -> None:
    slice_context.workspace_id = _workspace(slice_context.client)
    _create_reviewed_crop_item(slice_context.client, slice_context.workspace_id, "training", 10, 10)
    _create_reviewed_crop_item(slice_context.client, slice_context.workspace_id, "validation", 260, 10)


@when("the Dataset Curator creates a shared Marked-Bee Dataset Version")
def create_dataset_version(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    response = slice_context.client.post(
        "/v1/model-training/dataset-versions",
        json={"workspace_id": slice_context.workspace_id},
        headers=_headers(),
    )
    assert response.status_code == 201
    slice_context.dataset_version = response.json()
    assert slice_context.dataset_version["purpose"] == "marked_bee_detection_orientation"


@when("the Dataset Curator checks Bee Training readiness for that Dataset Version")
def check_bee_training_readiness(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.dataset_version is not None
    response = slice_context.client.get(
        "/v1/model-training/bee-training/readiness"
        f"?workspace_id={slice_context.workspace_id}"
        f"&dataset_version_id={slice_context.dataset_version['dataset_version_id']}",
        headers=_headers(),
    )
    assert response.status_code == 200
    slice_context.readiness = response.json()


@when("the Dataset Curator starts Bee Training")
def start_bee_training(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.dataset_version is not None
    response = slice_context.client.post(
        "/v1/model-training/bee-training/runs",
        json={
            "workspace_id": slice_context.workspace_id,
            "dataset_version_id": slice_context.dataset_version["dataset_version_id"],
            "acknowledge_high_severity_warnings": True,
        },
        headers=_headers(),
    )
    assert response.status_code == 202
    slice_context.training_start = response.json()


@then("Bee Localisation and Bee Orientation Training Runs complete from the same Dataset Version")
def both_runs_complete_from_same_dataset_version(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.dataset_version is not None
    assert slice_context.training_start is not None
    localisation_run = _wait_for_training_run_status(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.training_start["bee_localisation_training_run"]["training_run_id"],
        "completed",
    )
    orientation_run = _wait_for_training_run_purpose_status(
        slice_context.client,
        slice_context.workspace_id,
        "bee_orientation",
        "completed",
    )
    assert localisation_run["dataset_version_id"] == slice_context.dataset_version["dataset_version_id"]
    assert orientation_run["dataset_version_id"] == slice_context.dataset_version["dataset_version_id"]
    slice_context.localisation_run = localisation_run
    slice_context.orientation_run = orientation_run


@then("the Bee Orientation Training Run records training-run validation metrics only")
def orientation_metrics_are_training_validation_only(slice_context: SliceContext) -> None:
    assert slice_context.orientation_run is not None
    metrics = slice_context.orientation_run["metrics_summary"]
    assert metrics["predictive_training_performed"] is True
    assert metrics["metric_scope"] == "training_run_validation_not_benchmark"
    assert "validation_accuracy" in metrics
    assert "confusion_matrix" in metrics


@then("Bee Training is blocked by the Bee Orientation minimum evidence rule")
def bee_training_blocked_by_orientation_minimum(slice_context: SliceContext) -> None:
    assert slice_context.readiness is not None
    assert slice_context.readiness["eligible_to_start_bee_training"] is False
    assert slice_context.readiness["bee_orientation"]["eligible_to_start_training"] is False
    assert any(
        "at least 4 reliable complete visible bees" in warning["message"]
        for warning in slice_context.readiness["bee_orientation"]["warnings"]
    )
