from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from test_vertical_slice_0025_varroa_review_slice import (
    _complete_crop,
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


def test_dataset_curator_runs_stub_frame_mite_count_for_selected_photo(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, first_bee_id, second_bee_id = _completed_crop_with_two_bees(client)
        inspection_photo_id = _inspection_photo_id_for_crop(state, crop_id)

        response = _run_frame_mite_count(client, workspace_id, inspection_photo_id)

        assert response.status_code == 200
        body = response.json()
        assert body["workspace_id"] == workspace_id
        assert body["inspection_photo_id"] == inspection_photo_id
        assert body["source_intent"] == "training_data_collection"
        assert body["model_purpose"] == "varroa_detection"
        assert body["adapter_type"] == "deterministic_stub"
        assert body["adapter_version"] == "deterministic_stub_varroa_detector_v1"
        assert body["model_reference"] == "deterministic_stub_varroa_detector_v1"
        assert body["status"] == "completed"
        assert body["completed_training_crop_count"] == 1
        assert body["unfinished_training_crop_count"] == 0
        assert body["excluded_training_crop_count"] == 0
        assert body["eligible_bee_count"] == 2
        assert body["processed_bee_count"] == 2
        assert body["failed_bee_count"] == 0
        assert body["not_assessed_bee_count"] == 0
        assert body["likely_visible_varroa_detection_count"] == 2
        assert body["bees_with_likely_varroa_count"] == 2
        assert body["model_determinate_coverage_percent"] == 100
        assert body["advisor_context_available"] is False
        assert "not treatment advice" in body["caveat"]
        assert "not deduplicated physical bees" in body["caveat"]
        assert [result["bee_annotation_id"] for result in body["bee_results"]] == [
            first_bee_id,
            second_bee_id,
        ]
        assert {result["detection_count"] for result in body["bee_results"]} == {1}
        assert body["bee_results"][0]["crop_ordinal"] == 1
        assert body["bee_results"][0]["bee_ordinal"] == 1
        assert body["bee_results"][0]["head_up_normalized_crop"]["transform_version"] == (
            "head_up_normalized_bee_crop_v1"
        )
    finally:
        app.dependency_overrides.clear()


def test_frame_mite_count_discloses_ineligible_bees_without_treating_them_as_negatives(
    tmp_path: Path,
):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, complete_bee_id, partial_bee_id = _completed_crop_with_two_bees(
            client,
            second_annotation_type="partial_visible_bee",
        )
        inspection_photo_id = _inspection_photo_id_for_crop(state, crop_id)

        response = _run_frame_mite_count(client, workspace_id, inspection_photo_id)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed_with_warnings"
        assert body["eligible_bee_count"] == 1
        assert body["processed_bee_count"] == 1
        assert body["not_assessed_bee_count"] == 1
        assert body["likely_visible_varroa_detection_count"] == 1
        assert body["not_assessed_reasons"] == {"partial_visible_bee": 1}
        completed = next(
            result for result in body["bee_results"] if result["bee_annotation_id"] == complete_bee_id
        )
        partial = next(
            result for result in body["bee_results"] if result["bee_annotation_id"] == partial_bee_id
        )
        assert completed["status"] == "completed"
        assert partial["status"] == "not_assessed"
        assert partial["detection_count"] == 0
        assert partial["not_assessed_reason"] == "partial_visible_bee"
    finally:
        app.dependency_overrides.clear()


def test_frame_mite_count_is_not_available_when_no_eligible_bees_can_be_processed(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, first_bee_id, _ = _completed_crop_with_two_bees(
            client,
            second_annotation_type="partial_visible_bee",
            complete_crop=False,
        )
        _patch_ellipse(client, workspace_id, first_bee_id, annotation_type="partial_visible_bee")
        completed = _complete_crop(client, workspace_id, crop_id)
        assert completed.status_code == 200
        inspection_photo_id = _inspection_photo_id_for_crop(state, crop_id)

        response = _run_frame_mite_count(client, workspace_id, inspection_photo_id)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "not_available"
        assert body["eligible_bee_count"] == 0
        assert body["processed_bee_count"] == 0
        assert body["likely_visible_varroa_detection_count"] == 0
        assert body["not_assessed_bee_count"] == 2
        assert body["not_assessed_reasons"] == {"partial_visible_bee": 2}
        assert "No eligible Head-Up Normalized Bee Crops could be processed" in body["caveat"]
    finally:
        app.dependency_overrides.clear()


def test_per_bee_adapter_failures_are_reported_without_hiding_successful_counts(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    failing_adapter = FailFirstVarroaDetectorAdapter()
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_varroa_review_workflow] = lambda: VarroaReviewWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        varroa_detector_adapter=failing_adapter,
    )
    client = TestClient(app)
    try:
        workspace_id, crop_id, _, _ = _completed_crop_with_two_bees(client)
        inspection_photo_id = _inspection_photo_id_for_crop(state, crop_id)

        response = _run_frame_mite_count(client, workspace_id, inspection_photo_id)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed_with_warnings"
        assert body["eligible_bee_count"] == 2
        assert body["processed_bee_count"] == 1
        assert body["failed_bee_count"] == 1
        assert body["likely_visible_varroa_detection_count"] == 1
        assert body["failure_reasons"] == {"stub_adapter_failure": 1}
        assert [result["status"] for result in body["bee_results"]] == ["failed", "completed"]
    finally:
        app.dependency_overrides.clear()


def test_zero_model_detections_complete_without_creating_human_negative_evidence(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_varroa_review_workflow] = lambda: VarroaReviewWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        varroa_detector_adapter=ZeroDetectionVarroaDetectorAdapter(),
    )
    client = TestClient(app)
    try:
        workspace_id, crop_id, _, _ = _completed_crop_with_two_bees(client)
        inspection_photo_id = _inspection_photo_id_for_crop(state, crop_id)
        before_summary = _photo_visible_summary(client, workspace_id, inspection_photo_id)

        response = _run_frame_mite_count(client, workspace_id, inspection_photo_id)
        after_summary = _photo_visible_summary(client, workspace_id, inspection_photo_id)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"
        assert body["likely_visible_varroa_detection_count"] == 0
        assert body["bees_with_likely_varroa_count"] == 0
        assert body["processed_bee_count"] == 2
        assert before_summary == after_summary
        candidates = client.get(
            f"/v1/training-crops/{crop_id}/varroa-review-candidates?workspace_id={workspace_id}",
            headers=_headers(),
        ).json()
        assert all(candidate["review_outcome"] is None for candidate in candidates["candidates"])
    finally:
        app.dependency_overrides.clear()


def _run_frame_mite_count(client: TestClient, workspace_id: str, inspection_photo_id: str):
    return client.post(
        f"/v1/inspection-photos/{inspection_photo_id}/frame-mite-count",
        json={"workspace_id": workspace_id},
        headers=_headers(),
    )


def _photo_visible_summary(client: TestClient, workspace_id: str, inspection_photo_id: str) -> dict:
    response = client.get(
        f"/v1/inspection-photos/{inspection_photo_id}/photo-visible-varroa-summary"
        f"?workspace_id={workspace_id}",
        headers=_headers(),
    )
    assert response.status_code == 200
    return response.json()


def _inspection_photo_id_for_crop(state, crop_id: str) -> str:
    return str(state.store.training_crops[UUID(crop_id)].inspection_photo_id)


def _patch_ellipse(client: TestClient, workspace_id: str, annotation_id: str, **changes: object):
    response = client.patch(
        f"/v1/training-crop-bee-ellipses/{annotation_id}",
        json={"workspace_id": workspace_id, **changes},
        headers=_headers(),
    )
    assert response.status_code == 200
    return response.json()


class FailFirstVarroaDetectorAdapter(VarroaDetectorAdapter):
    adapter_type = "deterministic_stub"
    adapter_version = "fail_first_test_adapter_v1"
    model_reference = "fail_first_test_adapter_v1"

    def __init__(self) -> None:
        self.call_count = 0

    def detect(self, request: VarroaDetectorRequest):
        self.call_count += 1
        if self.call_count == 1:
            raise VarroaDetectorFailure(
                code="stub_adapter_failure",
                message="The configured Varroa Detector adapter failed safely.",
            )
        return [
            {
                "detection_id": "test-detection-1",
                "x": 0.5,
                "y": 0.5,
                "width": 0.1,
                "height": 0.1,
                "confidence": 0.8,
                "coordinate_space": "head_up_normalized_crop",
                "source": "test_adapter",
            }
        ]


class ZeroDetectionVarroaDetectorAdapter(VarroaDetectorAdapter):
    adapter_type = "deterministic_stub"
    adapter_version = "zero_detection_test_adapter_v1"
    model_reference = "zero_detection_test_adapter_v1"

    def detect(self, request: VarroaDetectorRequest):
        return []
