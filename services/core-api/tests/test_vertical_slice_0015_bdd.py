from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app
from test_model_training_slice import (
    ORDINARY_USER_ID,
    _create_reviewed_crop_item,
    _headers,
    _workspace,
)

FEATURES_DIR = Path(__file__).parent / "features"

scenarios(str(FEATURES_DIR / "vertical_slice_0015_yolo_obb_training_baseline.feature"))


@dataclass
class SliceContext:
    client: TestClient
    workspace_id: str | None = None
    dataset_version: dict[str, object] | None = None
    training_run: dict[str, object] | None = None
    response_status_code: int | None = None
    response_body: dict[str, object] | None = None


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


@given("the User is logged in with dataset curator capability for model training")
def curator_logged_in(slice_context: SliceContext) -> None:
    slice_context.workspace_id = _workspace(slice_context.client)


@given("the Dataset Curator has active reviewed Training Crop Dataset Items for training and validation")
def reviewed_training_crop_items(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    _create_reviewed_crop_item(slice_context.client, slice_context.workspace_id, "training", 10, 10)
    _create_reviewed_crop_item(
        slice_context.client,
        slice_context.workspace_id,
        "validation",
        260,
        10,
    )


@when("the Dataset Curator creates a Bee Detector Dataset Version")
def create_dataset_version(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    response = slice_context.client.post(
        "/v1/model-training/dataset-versions",
        json={"workspace_id": slice_context.workspace_id},
        headers=_headers(),
    )
    slice_context.response_status_code = response.status_code
    slice_context.response_body = response.json()
    slice_context.dataset_version = response.json()


@when("the Dataset Curator starts a fake Bee Detector Training Run with warning acknowledgement")
def start_training_run(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.dataset_version is not None
    response = slice_context.client.post(
        "/v1/model-training/training-runs",
        json={
            "workspace_id": slice_context.workspace_id,
            "dataset_version_id": slice_context.dataset_version["dataset_version_id"],
            "acknowledge_high_severity_warnings": True,
        },
        headers=_headers(),
    )
    slice_context.response_status_code = response.status_code
    slice_context.response_body = response.json()
    slice_context.training_run = response.json()


@then("the Training Run creates a non-user-facing Bee Detector Model Candidate")
def training_run_creates_candidate(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 202
    assert slice_context.training_run is not None
    assert slice_context.training_run["status"] == "completed"
    assert slice_context.training_run["model_purpose"] == "bee_detector"
    assert slice_context.training_run["model_candidate_id"] is not None


@then("the Dataset Version report protects benchmark data from training input")
def dataset_version_protects_benchmark(slice_context: SliceContext) -> None:
    assert slice_context.dataset_version is not None
    assert slice_context.dataset_version["protected_benchmark_dataset_item_ids"] == []
    assert slice_context.dataset_version["training_item_count"] == 1
    assert slice_context.dataset_version["validation_item_count"] == 1


@given("an ordinary Beekeeper has an accepted Workspace Data Use Agreement")
def ordinary_beekeeper(slice_context: SliceContext) -> None:
    state = build_dev_state()
    state.store.dataset_curator_user_ids.clear()
    app.dependency_overrides[get_dev_state] = lambda: state
    slice_context.client = TestClient(app)
    response = slice_context.client.get(
        "/v1/dev/session",
        headers={"x-hivesight-dev-user-id": str(ORDINARY_USER_ID)},
    )
    slice_context.workspace_id = response.json()["workspace_id"]
    slice_context.client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": slice_context.workspace_id, "terms_version": "2026-07-31"},
        headers={"x-hivesight-dev-user-id": str(ORDINARY_USER_ID)},
    )


@when("the ordinary Beekeeper checks model training readiness")
def ordinary_checks_readiness(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    response = slice_context.client.get(
        f"/v1/model-training/readiness?workspace_id={slice_context.workspace_id}",
        headers={"x-hivesight-dev-user-id": str(ORDINARY_USER_ID)},
    )
    slice_context.response_status_code = response.status_code
    slice_context.response_body = response.json()


@then("the Core API rejects the model training request")
def core_api_rejects_request(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 403
    assert slice_context.response_body is not None
    assert slice_context.response_body["detail"]["code"] == "dataset_curator_access_required"
