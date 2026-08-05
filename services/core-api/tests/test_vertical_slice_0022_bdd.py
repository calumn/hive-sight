from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app
from test_model_training_slice import (
    _create_reviewed_crop_item,
    _headers,
    _wait_for_training_run_status,
    _workspace,
)

FEATURES_DIR = Path(__file__).parent / "features"

scenarios(str(FEATURES_DIR / "vertical_slice_0022_bee_orientation_training_baseline.feature"))


@dataclass
class SliceContext:
    client: TestClient
    workspace_id: str | None = None
    dataset_version: dict[str, object] | None = None
    readiness: dict[str, object] | None = None
    training_run: dict[str, object] | None = None
    model_candidate: dict[str, object] | None = None
    response_status_code: int | None = None


@pytest.fixture
def slice_context(tmp_path: Path) -> SliceContext:
    state = build_dev_state(
        dataset_export_root=tmp_path / "exports",
        model_artifact_root=tmp_path / "model-runs",
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    try:
        yield SliceContext(client=TestClient(app))
    finally:
        app.dependency_overrides.clear()


@given("the User is logged in with dataset curator capability for Bee Orientation training")
def curator_logged_in(slice_context: SliceContext) -> None:
    slice_context.workspace_id = _workspace(slice_context.client)


@given("the Dataset Curator has reliable complete marked bees in training and validation")
def reliable_marked_bees(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    _create_reviewed_crop_item(slice_context.client, slice_context.workspace_id, "training", 10, 10)
    _create_reviewed_crop_item(
        slice_context.client,
        slice_context.workspace_id,
        "validation",
        260,
        10,
    )


@when("the Dataset Curator creates a shared Marked-Bee Dataset Version")
def create_marked_bee_dataset_version(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    response = slice_context.client.post(
        "/v1/model-training/dataset-versions",
        json={"workspace_id": slice_context.workspace_id},
        headers=_headers(),
    )
    slice_context.response_status_code = response.status_code
    slice_context.dataset_version = response.json()
    assert response.status_code == 201
    assert slice_context.dataset_version["purpose"] == "marked_bee_detection_orientation"
    assert slice_context.dataset_version["model_purpose"] == "marked_bee"


@when("the Dataset Curator checks Bee Orientation readiness for that Dataset Version")
def check_orientation_readiness(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.dataset_version is not None
    response = slice_context.client.get(
        "/v1/model-training/readiness"
        f"?workspace_id={slice_context.workspace_id}&model_purpose=bee_orientation"
        f"&dataset_version_id={slice_context.dataset_version['dataset_version_id']}",
        headers=_headers(),
    )
    slice_context.response_status_code = response.status_code
    slice_context.readiness = response.json()
    assert response.status_code == 200
    assert slice_context.readiness["model_purpose"] == "bee_orientation"
    assert slice_context.readiness["eligible_to_start_training"] is True


@when("the Dataset Curator starts the fake Bee Orientation Training Run")
def start_orientation_training_run(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.dataset_version is not None
    response = slice_context.client.post(
        "/v1/model-training/training-runs",
        json={
            "workspace_id": slice_context.workspace_id,
            "dataset_version_id": slice_context.dataset_version["dataset_version_id"],
            "model_purpose": "bee_orientation",
            "acknowledge_high_severity_warnings": True,
        },
        headers=_headers(),
    )
    slice_context.response_status_code = response.status_code
    slice_context.training_run = response.json()
    assert response.status_code == 202


@then("the Bee Orientation Training Run completes without predictive training metrics")
def orientation_training_completes(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.training_run is not None
    completed = _wait_for_training_run_status(
        slice_context.client,
        slice_context.workspace_id,
        str(slice_context.training_run["training_run_id"]),
        "completed",
    )
    slice_context.training_run = completed
    assert completed["model_purpose"] == "bee_orientation"
    assert completed["model_family"] == "bee_orientation_binary_classifier"
    assert completed["metrics_summary"]["predictive_training_performed"] is False
    assert "accuracy" not in completed["metrics_summary"]


@then("the non-user-facing Bee Orientation Model Candidate is recorded")
def orientation_candidate_recorded(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.training_run is not None
    response = slice_context.client.get(
        f"/v1/model-training/model-candidates?workspace_id={slice_context.workspace_id}",
        headers=_headers(),
    )
    candidates = response.json()["model_candidates"]
    candidate = next(
        candidate
        for candidate in candidates
        if candidate["model_candidate_id"] == slice_context.training_run["model_candidate_id"]
    )
    assert candidate["model_purpose"] == "bee_orientation"
    assert candidate["model_family"] == "bee_orientation_binary_classifier"
    assert candidate["not_user_facing_reason"] == "baseline_training_only"
