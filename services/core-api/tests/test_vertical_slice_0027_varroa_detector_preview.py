from dataclasses import dataclass
from pathlib import Path

from fastapi.testclient import TestClient
from test_vertical_slice_0025_varroa_review_slice import (
    _completed_crop_with_two_bees,
    _headers,
)

from hive_sight_core_api.dependencies import (
    build_dev_state,
    get_dev_state,
    get_varroa_review_workflow,
)
from hive_sight_core_api.main import app
from hive_sight_core_api.varroa_review_workflow import (
    VarroaDetectorAdapter,
    VarroaDetectorFailure,
    VarroaDetectorRequest,
    VarroaReviewWorkflow,
)


def test_dataset_curator_runs_stub_varroa_detector_preview_for_eligible_bee(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, bee_annotation_id, _ = _completed_crop_with_two_bees(client)

        response = _run_preview(client, workspace_id, crop_id, bee_annotation_id)

        assert response.status_code == 200
        body = response.json()
        assert body["workspace_id"] == workspace_id
        assert body["training_crop_id"] == crop_id
        assert body["bee_annotation_id"] == bee_annotation_id
        assert body["model_purpose"] == "varroa_detection"
        assert body["adapter_type"] == "deterministic_stub"
        assert body["adapter_version"] == "deterministic_stub_varroa_detector_v1"
        assert body["model_reference"] == "deterministic_stub_varroa_detector_v1"
        assert body["status"] == "completed"
        assert body["failure_code"] is None
        assert body["detection_count"] == 1
        assert body["elapsed_ms"] >= 0
        assert body["not_user_facing_reason"] == "Deterministic stub preview only; not user-facing."
        assert "not eligible for promotion" in body["caveat"]
        detection = body["detections"][0]
        assert detection["source"] == "deterministic_stub"
        assert detection["coordinate_space"] == "head_up_normalized_crop"
        assert detection["x"] == 0.52
        assert detection["y"] == 0.34
        assert detection["width"] == 0.08
        assert detection["height"] == 0.06
        assert detection["confidence"] == 0.73
        assert body["head_up_normalized_crop"]["transform_version"] == "head_up_normalized_bee_crop_v1"

        candidates = _candidates(client, workspace_id, crop_id)
        selected = next(
            candidate
            for candidate in candidates["candidates"]
            if candidate["bee_annotation"]["annotation_id"] == bee_annotation_id
        )
        assert selected["review_outcome"] is None
    finally:
        app.dependency_overrides.clear()


def test_varroa_detector_preview_reports_ineligible_bee_as_not_assessed(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, _, partial_bee_id = _completed_crop_with_two_bees(
            client,
            second_annotation_type="partial_visible_bee",
        )

        response = _run_preview(client, workspace_id, crop_id, partial_bee_id)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "not_assessed"
        assert body["not_assessed_reason"] == "partial_visible_bee"
        assert body["detections"] == []
        assert body["detection_count"] == 0
        assert body["failure_code"] is None
        assert "not assessed" in body["caveat"]
        assert "not a negative Varroa result" in body["caveat"]
    finally:
        app.dependency_overrides.clear()


def test_varroa_detector_preview_failure_does_not_mutate_human_review(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_varroa_review_workflow] = lambda: VarroaReviewWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        varroa_detector_adapter=FailingVarroaDetectorAdapter(),
    )
    client = TestClient(app)
    try:
        workspace_id, crop_id, bee_annotation_id, _ = _completed_crop_with_two_bees(client)
        saved = client.put(
            f"/v1/training-crops/{crop_id}/varroa-review-candidates/{bee_annotation_id}/outcome",
            json={
                "workspace_id": workspace_id,
                "outcome": "visible_varroa_present",
                "markers": [{"x": 0.25, "y": 0.35}],
            },
            headers=_headers(),
        )
        assert saved.status_code == 200

        response = _run_preview(client, workspace_id, crop_id, bee_annotation_id)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "failed"
        assert body["failure_code"] == "stub_adapter_failure"
        assert body["failure_message"] == "The configured Varroa Detector adapter failed safely."
        assert body["detections"] == []
        assert body["detection_count"] == 0
        reopened = _candidates(client, workspace_id, crop_id)
        selected = next(
            candidate
            for candidate in reopened["candidates"]
            if candidate["bee_annotation"]["annotation_id"] == bee_annotation_id
        )
        assert selected["review_outcome"]["outcome"] == "visible_varroa_present"
        assert selected["review_outcome"]["markers"][0]["x"] == 0.25
    finally:
        app.dependency_overrides.clear()


def _run_preview(client: TestClient, workspace_id: str, crop_id: str, bee_annotation_id: str):
    return client.post(
        f"/v1/training-crops/{crop_id}/varroa-review-candidates/{bee_annotation_id}/detector-preview",
        json={"workspace_id": workspace_id},
        headers=_headers(),
    )


def _candidates(client: TestClient, workspace_id: str, crop_id: str) -> dict:
    response = client.get(
        f"/v1/training-crops/{crop_id}/varroa-review-candidates?workspace_id={workspace_id}",
        headers=_headers(),
    )
    assert response.status_code == 200
    return response.json()


@dataclass(frozen=True)
class FailingVarroaDetectorAdapter(VarroaDetectorAdapter):
    adapter_type: str = "deterministic_stub"
    adapter_version: str = "deterministic_stub_varroa_detector_v1"
    model_reference: str = "deterministic_stub_varroa_detector_v1"

    def detect(self, request: VarroaDetectorRequest):
        raise VarroaDetectorFailure(
            code="stub_adapter_failure",
            message="The configured Varroa Detector adapter failed safely.",
        )


def test_zero_detection_adapter_response_is_completed_not_negative(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_varroa_review_workflow] = lambda: VarroaReviewWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        varroa_detector_adapter=ZeroDetectionVarroaDetectorAdapter(),
    )
    client = TestClient(app)
    try:
        workspace_id, crop_id, bee_annotation_id, _ = _completed_crop_with_two_bees(client)

        response = _run_preview(client, workspace_id, crop_id, bee_annotation_id)

        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        assert response.json()["detections"] == []
        assert response.json()["detection_count"] == 0
        candidates = _candidates(client, workspace_id, crop_id)
        selected = next(
            candidate
            for candidate in candidates["candidates"]
            if candidate["bee_annotation"]["annotation_id"] == bee_annotation_id
        )
        assert selected["review_outcome"] is None
    finally:
        app.dependency_overrides.clear()


@dataclass(frozen=True)
class ZeroDetectionVarroaDetectorAdapter(VarroaDetectorAdapter):
    adapter_type: str = "deterministic_stub"
    adapter_version: str = "zero_detection_test_adapter_v1"
    model_reference: str = "zero_detection_test_adapter_v1"

    def detect(self, request: VarroaDetectorRequest):
        return []
