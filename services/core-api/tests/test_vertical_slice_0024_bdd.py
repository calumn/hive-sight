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
    _wait_for_benchmark_evaluation_status,
    _wait_for_training_run_purpose_status,
    _workspace,
)

FEATURES_DIR = Path(__file__).parent / "features"

scenarios(str(FEATURES_DIR / "vertical_slice_0024_bee_orientation_benchmark_evaluation.feature"))


@dataclass
class SliceContext:
    client: TestClient
    workspace_id: str | None = None
    orientation_candidate_id: str | None = None
    readiness: dict[str, object] | None = None
    evaluation: dict[str, object] | None = None


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


@given("the Dataset Curator has a completed Bee Orientation Model Candidate with protected Benchmark evidence")
def orientation_candidate_with_benchmark(slice_context: SliceContext) -> None:
    slice_context.workspace_id = _workspace(slice_context.client)
    _create_reviewed_crop_item(slice_context.client, slice_context.workspace_id, "training", 10, 10)
    _create_reviewed_crop_item(slice_context.client, slice_context.workspace_id, "validation", 260, 10)
    _create_reviewed_crop_item(slice_context.client, slice_context.workspace_id, "benchmark", 10, 260)
    slice_context.orientation_candidate_id = _create_orientation_candidate(slice_context)


@given("the Dataset Curator has a completed Bee Orientation Model Candidate with only unreliable Benchmark bees")
def orientation_candidate_with_unreliable_benchmark(slice_context: SliceContext) -> None:
    slice_context.workspace_id = _workspace(slice_context.client)
    _create_reviewed_crop_item(slice_context.client, slice_context.workspace_id, "training", 10, 10)
    _create_reviewed_crop_item(slice_context.client, slice_context.workspace_id, "validation", 260, 10)
    _create_reviewed_crop_item(
        slice_context.client,
        slice_context.workspace_id,
        "benchmark",
        10,
        260,
        orientation_reliability="unreliable",
    )
    slice_context.orientation_candidate_id = _create_orientation_candidate(slice_context)


@when("the Dataset Curator checks Bee Orientation benchmark readiness")
def check_orientation_benchmark_readiness(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.orientation_candidate_id is not None
    response = slice_context.client.get(
        "/v1/model-training/model-candidates/"
        f"{slice_context.orientation_candidate_id}/orientation-benchmark-readiness"
        f"?workspace_id={slice_context.workspace_id}",
        headers=_headers(),
    )
    assert response.status_code == 200
    slice_context.readiness = response.json()


@when("the Dataset Curator runs the Bee Orientation benchmark")
def run_orientation_benchmark(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.orientation_candidate_id is not None
    response = slice_context.client.post(
        "/v1/model-training/orientation-benchmark-evaluations",
        json={
            "workspace_id": slice_context.workspace_id,
            "model_candidate_id": slice_context.orientation_candidate_id,
        },
        headers=_headers(),
    )
    assert response.status_code == 202
    slice_context.evaluation = _wait_for_benchmark_evaluation_status(
        slice_context.client,
        slice_context.workspace_id,
        response.json()["benchmark_evaluation_id"],
        "completed",
    )


@then("the Bee Orientation Benchmark Evaluation completes with head direction metrics")
def benchmark_completes_with_head_direction_metrics(slice_context: SliceContext) -> None:
    assert slice_context.evaluation is not None
    assert slice_context.evaluation["model_purpose"] == "bee_orientation"
    assert slice_context.evaluation["metrics_summary"]["metric_scope"] == "bee_orientation_benchmark_only"
    assert slice_context.evaluation["metrics_summary"]["evaluated_bee_count"] == 1
    assert "accuracy" in slice_context.evaluation["metrics_summary"]
    assert "confusion_matrix" in slice_context.evaluation["metrics_summary"]
    assert slice_context.evaluation["raw_prediction_artifact_id"] is not None


@then("the Bee Orientation benchmark report remains purpose-limited")
def benchmark_report_remains_purpose_limited(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.evaluation is not None
    response = slice_context.client.get(
        "/v1/model-training/artifacts/"
        f"{slice_context.evaluation['report_artifact_id']}?workspace_id={slice_context.workspace_id}",
        headers=_headers(),
    )
    assert response.status_code == 200
    assert "head-direction prediction only" in response.text
    assert "does not evaluate Bee Localisation quality" in response.text
    assert "does not evaluate Varroa Detection quality" in response.text


@then("Bee Orientation benchmark readiness is blocked by the eligible bee rule")
def benchmark_readiness_blocked(slice_context: SliceContext) -> None:
    assert slice_context.readiness is not None
    assert slice_context.readiness["eligible_to_start_benchmark"] is False
    assert slice_context.readiness["eligible_benchmark_bee_count"] == 0
    assert any(
        warning["code"] == "NO_ELIGIBLE_ORIENTATION_BENCHMARK_BEES"
        for warning in slice_context.readiness["warnings"]
    )


def _create_orientation_candidate(slice_context: SliceContext) -> str:
    assert slice_context.workspace_id is not None
    dataset_version = slice_context.client.post(
        "/v1/model-training/dataset-versions",
        json={"workspace_id": slice_context.workspace_id},
        headers=_headers(),
    )
    assert dataset_version.status_code == 201
    training_response = slice_context.client.post(
        "/v1/model-training/bee-training/runs",
        json={
            "workspace_id": slice_context.workspace_id,
            "dataset_version_id": dataset_version.json()["dataset_version_id"],
            "acknowledge_high_severity_warnings": True,
        },
        headers=_headers(),
    )
    assert training_response.status_code == 202
    orientation_run = _wait_for_training_run_purpose_status(
        slice_context.client,
        slice_context.workspace_id,
        "bee_orientation",
        "completed",
    )
    return str(orientation_run["model_candidate_id"])
