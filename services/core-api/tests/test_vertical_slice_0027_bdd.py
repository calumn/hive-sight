from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when
from test_vertical_slice_0025_varroa_review_slice import (
    _completed_crop_with_two_bees,
    _headers,
)
from test_vertical_slice_0027_varroa_detector_preview import (
    FailingVarroaDetectorAdapter,
    _candidates,
    _run_preview,
)

from hive_sight_core_api.dependencies import (
    build_dev_state,
    get_dev_state,
    get_varroa_review_workflow,
)
from hive_sight_core_api.main import app
from hive_sight_core_api.varroa_review_workflow import VarroaReviewWorkflow

FEATURES_DIR = Path(__file__).parent / "features"

scenarios(str(FEATURES_DIR / "vertical_slice_0027_varroa_detector_adapter_seam.feature"))


@dataclass
class SliceContext:
    client: TestClient
    workspace_id: str | None = None
    crop_id: str | None = None
    bee_annotation_id: str | None = None
    second_bee_annotation_id: str | None = None
    response: object | None = None
    summary_before: dict[str, object] | None = None


@pytest.fixture
def slice_context(tmp_path: Path) -> SliceContext:
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    try:
        yield SliceContext(client=TestClient(app))
    finally:
        app.dependency_overrides.clear()


@given("a completed Training Crop contains a reliable complete visible bee")
@given("HiveSight is using the deterministic stub Varroa Detector adapter")
def completed_crop_with_eligible_bee(slice_context: SliceContext) -> None:
    (
        slice_context.workspace_id,
        slice_context.crop_id,
        slice_context.bee_annotation_id,
        slice_context.second_bee_annotation_id,
    ) = _completed_crop_with_two_bees(slice_context.client)


@given("HiveSight can generate a Head-Up Normalized Bee Crop for that bee")
def can_generate_head_up_crop(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.crop_id and slice_context.bee_annotation_id
    response = slice_context.client.get(
        f"/v1/training-crops/{slice_context.crop_id}/varroa-review-candidates/"
        f"{slice_context.bee_annotation_id}/head-up-normalized-preview"
        f"?workspace_id={slice_context.workspace_id}",
        headers=_headers(),
    )
    assert response.status_code == 200


@given("a Training Crop contains a partial visible bee or an unreliable-orientation bee")
def crop_with_ineligible_bee(slice_context: SliceContext) -> None:
    (
        slice_context.workspace_id,
        slice_context.crop_id,
        _,
        slice_context.bee_annotation_id,
    ) = _completed_crop_with_two_bees(
        slice_context.client,
        second_annotation_type="partial_visible_bee",
    )


@given("a bee already has a saved human Varroa Review Outcome")
def bee_has_human_review_outcome(slice_context: SliceContext) -> None:
    completed_crop_with_eligible_bee(slice_context)
    assert slice_context.workspace_id and slice_context.crop_id and slice_context.bee_annotation_id
    saved = slice_context.client.put(
        f"/v1/training-crops/{slice_context.crop_id}/varroa-review-candidates/"
        f"{slice_context.bee_annotation_id}/outcome",
        json={
            "workspace_id": slice_context.workspace_id,
            "outcome": "visible_varroa_present",
            "markers": [{"x": 0.25, "y": 0.35}],
        },
        headers=_headers(),
    )
    assert saved.status_code == 200
    slice_context.summary_before = _candidates(slice_context.client, slice_context.workspace_id, slice_context.crop_id)[
        "summary"
    ]


@given("the configured Varroa Detector adapter cannot process the Head-Up Normalized Bee Crop")
def configured_adapter_fails(slice_context: SliceContext) -> None:
    state = build_dev_state(dataset_export_root=Path("/tmp/hivesight-slice-0027-bdd"))
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_varroa_review_workflow] = lambda: VarroaReviewWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        varroa_detector_adapter=FailingVarroaDetectorAdapter(),
    )
    slice_context.client = TestClient(app)
    completed_crop_with_eligible_bee(slice_context)


@when("the Dataset Curator runs the Varroa Detector preview for the bee")
@when("the Dataset Curator runs the Varroa Detector preview for that bee")
@when("the Dataset Curator runs the Varroa Detector preview")
def run_preview(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.crop_id and slice_context.bee_annotation_id
    slice_context.response = _run_preview(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.crop_id,
        slice_context.bee_annotation_id,
    )


@when("the Dataset Curator tries to run the Varroa Detector preview for that bee")
def run_preview_for_ineligible(slice_context: SliceContext) -> None:
    run_preview(slice_context)


@then("HiveSight sends the Head-Up Normalized Bee Crop through the configured Varroa Detector adapter")
def adapter_completed(slice_context: SliceContext) -> None:
    assert _body(slice_context)["status"] == "completed"


@then("HiveSight shows one deterministic Likely Varroa Detection as a model-preview box")
def one_detection(slice_context: SliceContext) -> None:
    body = _body(slice_context)
    assert body["detection_count"] == 1
    assert body["detections"][0]["source"] == "deterministic_stub"


@then("HiveSight shows the detection location, size, confidence, and elapsed time in the preview details")
def detection_details(slice_context: SliceContext) -> None:
    body = _body(slice_context)
    detection = body["detections"][0]
    assert detection["x"] == 0.52
    assert detection["y"] == 0.34
    assert detection["width"] == 0.08
    assert detection["height"] == 0.06
    assert detection["confidence"] == 0.73
    assert body["elapsed_ms"] >= 0


@then("HiveSight labels the result as model preview evidence only")
def model_preview_only(slice_context: SliceContext) -> None:
    assert "preview" in _body(slice_context)["caveat"].lower()


@then("HiveSight does not save a Varroa Review Outcome")
def no_outcome_saved(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.crop_id and slice_context.bee_annotation_id
    candidate = _selected_candidate(slice_context)
    assert candidate["review_outcome"] is None


@then("HiveSight returns adapter provenance including workspace, model purpose, adapter type, adapter version, model reference, and input transform version")
def provenance_returned(slice_context: SliceContext) -> None:
    body = _body(slice_context)
    assert body["workspace_id"] == slice_context.workspace_id
    assert body["model_purpose"] == "varroa_detection"
    assert body["adapter_type"] == "deterministic_stub"
    assert body["adapter_version"]
    assert body["model_reference"]
    assert body["head_up_normalized_crop"]["transform_version"] == "head_up_normalized_bee_crop_v1"


@then("HiveSight labels the detections as deterministic stub output")
def labels_stub(slice_context: SliceContext) -> None:
    assert _body(slice_context)["detections"][0]["source"] == "deterministic_stub"


@then("HiveSight marks the output as not user-facing and not eligible for promotion")
def not_user_facing(slice_context: SliceContext) -> None:
    body = _body(slice_context)
    assert "not user-facing" in body["not_user_facing_reason"]
    assert "not eligible for promotion" in body["caveat"]


@then("HiveSight returns a detector preview status of not_assessed")
def not_assessed(slice_context: SliceContext) -> None:
    assert _body(slice_context)["status"] == "not_assessed"


@then("HiveSight does not call the Varroa Detector adapter")
def adapter_not_called(slice_context: SliceContext) -> None:
    assert _body(slice_context)["adapter_type"] == "not_called"


@then("HiveSight explains why the bee is not assessed for Varroa Detection")
def not_assessed_reason(slice_context: SliceContext) -> None:
    assert _body(slice_context)["not_assessed_reason"] == "partial_visible_bee"


@then("HiveSight does not treat the bee as a negative Varroa result")
def not_negative(slice_context: SliceContext) -> None:
    assert _body(slice_context)["detections"] == []
    assert "not a negative Varroa result" in _body(slice_context)["caveat"]


@then("HiveSight shows the model preview separately from the saved human outcome")
def preview_separate_from_human_outcome(slice_context: SliceContext) -> None:
    assert _body(slice_context)["detection_count"] == 1
    assert _selected_candidate(slice_context)["review_outcome"]["outcome"] == "visible_varroa_present"


@then("HiveSight leaves the human Varroa Review Outcome and markers unchanged")
def human_outcome_unchanged(slice_context: SliceContext) -> None:
    outcome = _selected_candidate(slice_context)["review_outcome"]
    assert outcome["outcome"] == "visible_varroa_present"
    assert outcome["markers"][0]["x"] == 0.25


@then("HiveSight does not change the photo-visible Varroa evidence summary")
def summary_unchanged(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.crop_id and slice_context.summary_before is not None
    summary_after = _candidates(slice_context.client, slice_context.workspace_id, slice_context.crop_id)["summary"]
    assert summary_after == slice_context.summary_before


@then("HiveSight clears any previous model-preview boxes")
def clears_previous_preview_boxes(slice_context: SliceContext) -> None:
    assert _body(slice_context)["detections"] == []


@then("HiveSight returns a detector preview status of failed")
def failed_status(slice_context: SliceContext) -> None:
    assert _body(slice_context)["status"] == "failed"


@then("HiveSight reports the adapter failure reason")
def reports_failure_reason(slice_context: SliceContext) -> None:
    assert _body(slice_context)["failure_code"] == "stub_adapter_failure"


@then("HiveSight records no Likely Varroa Detections")
def no_detections(slice_context: SliceContext) -> None:
    assert _body(slice_context)["detection_count"] == 0


@then("HiveSight does not create or change a Varroa Review Outcome")
def no_outcome_change(slice_context: SliceContext) -> None:
    candidate = _selected_candidate(slice_context)
    assert candidate["review_outcome"] is None


def _body(slice_context: SliceContext) -> dict[str, object]:
    assert slice_context.response is not None
    assert slice_context.response.status_code == 200
    return slice_context.response.json()


def _selected_candidate(slice_context: SliceContext) -> dict[str, object]:
    assert slice_context.workspace_id and slice_context.crop_id and slice_context.bee_annotation_id
    candidates = _candidates(slice_context.client, slice_context.workspace_id, slice_context.crop_id)
    return next(
        candidate
        for candidate in candidates["candidates"]
        if candidate["bee_annotation"]["annotation_id"] == slice_context.bee_annotation_id
    )
