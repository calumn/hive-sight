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
    _wait_for_benchmark_evaluation_status,
    _wait_for_training_run_status,
    _workspace,
)

FEATURES_DIR = Path(__file__).parent / "features"

scenarios(
    str(FEATURES_DIR / "vertical_slice_0015_4_model_candidate_evaluation_and_benchmark_report.feature")
)


@dataclass
class SliceContext:
    client: TestClient
    workspace_id: str | None = None
    model_candidate_id: str | None = None
    benchmark_evaluation: dict[str, object] | None = None
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


@given("the User is logged in with dataset curator capability for benchmark evaluation")
def curator_logged_in(slice_context: SliceContext) -> None:
    slice_context.workspace_id = _workspace(slice_context.client)


@given(
    "the Dataset Curator has a completed Bee Detector Model Candidate with protected benchmark Training Crops"
)
def candidate_with_benchmark_items(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    _create_reviewed_crop_item(slice_context.client, slice_context.workspace_id, "training", 10, 10)
    _create_reviewed_crop_item(
        slice_context.client,
        slice_context.workspace_id,
        "validation",
        260,
        10,
    )
    _create_reviewed_crop_item(
        slice_context.client,
        slice_context.workspace_id,
        "benchmark",
        10,
        260,
    )
    dataset_version = slice_context.client.post(
        "/v1/model-training/dataset-versions",
        json={"workspace_id": slice_context.workspace_id},
        headers=_headers(),
    ).json()
    training_run = slice_context.client.post(
        "/v1/model-training/training-runs",
        json={
            "workspace_id": slice_context.workspace_id,
            "dataset_version_id": dataset_version["dataset_version_id"],
            "acknowledge_high_severity_warnings": True,
        },
        headers=_headers(),
    ).json()
    completed_training_run = _wait_for_training_run_status(
        slice_context.client,
        slice_context.workspace_id,
        training_run["training_run_id"],
        "completed",
    )
    slice_context.model_candidate_id = completed_training_run["model_candidate_id"]


@when("the Dataset Curator starts a Benchmark Evaluation for that Model Candidate")
def start_benchmark_evaluation(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.model_candidate_id is not None
    response = slice_context.client.post(
        "/v1/model-training/benchmark-evaluations",
        json={
            "workspace_id": slice_context.workspace_id,
            "model_candidate_id": slice_context.model_candidate_id,
        },
        headers=_headers(),
    )
    slice_context.response_status_code = response.status_code
    slice_context.response_body = response.json()
    slice_context.benchmark_evaluation = response.json()


@then("the Benchmark Evaluation completes with metrics and a benchmark report")
def benchmark_evaluation_completes(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 202
    assert slice_context.workspace_id is not None
    assert slice_context.benchmark_evaluation is not None
    completed = _wait_for_benchmark_evaluation_status(
        slice_context.client,
        slice_context.workspace_id,
        str(slice_context.benchmark_evaluation["benchmark_evaluation_id"]),
        "completed",
    )
    assert completed["metrics_summary"]["metric_scope"] == "training_crop_benchmark_only"
    assert completed["metrics_summary"]["benchmark_item_count"] == 1
    assert completed["raw_prediction_artifact_id"] is not None
    assert completed["report_artifact_id"] is not None


@given("an ordinary Beekeeper has an accepted Workspace Data Use Agreement for benchmark evaluation")
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


@when("the ordinary Beekeeper starts a Benchmark Evaluation")
def ordinary_starts_evaluation(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    response = slice_context.client.post(
        "/v1/model-training/benchmark-evaluations",
        json={
            "workspace_id": slice_context.workspace_id,
            "model_candidate_id": "00000000-0000-0000-0000-000000009999",
        },
        headers={"x-hivesight-dev-user-id": str(ORDINARY_USER_ID)},
    )
    slice_context.response_status_code = response.status_code
    slice_context.response_body = response.json()


@then("the Core API rejects the benchmark evaluation request")
def core_api_rejects_request(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 403
    assert slice_context.response_body is not None
    assert slice_context.response_body["detail"]["code"] == "dataset_curator_access_required"
