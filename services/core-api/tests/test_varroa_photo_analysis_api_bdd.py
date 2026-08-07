from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when
from test_vertical_slice_0025_varroa_review_slice import (
    _complete_crop,
    _completed_crop_with_two_bees,
    _headers,
)
from test_vertical_slice_0028_frame_mite_count import _patch_ellipse
from test_vertical_slice_0033_varroa_photo_analysis import (
    FailFirstThenDetectAdapter,
    _inspection_photo_id_for_crop,
    _review_photo_analysis,
    _run_photo_analysis,
)

from hive_sight_core_api.dependencies import (
    build_dev_state,
    get_dev_state,
    get_varroa_photo_analysis_workflow,
    get_varroa_review_workflow,
)
from hive_sight_core_api.main import app
from hive_sight_core_api.varroa_detector_adapters import LocalCommandVarroaDetectorAdapter
from hive_sight_core_api.varroa_photo_analysis_workflow import VarroaPhotoAnalysisWorkflow
from hive_sight_core_api.varroa_review_workflow import VarroaReviewWorkflow

scenarios("../../../acceptance/features/varroa/varroa-photo-analysis-evidence-and-adapter-readiness.feature")


@dataclass
class SliceContext:
    client: TestClient
    state: object
    workspace_id: str | None = None
    crop_id: str | None = None
    inspection_photo_id: str | None = None
    bee_annotation_id: str | None = None
    response: object | None = None


@pytest.fixture
def slice_context(tmp_path: Path) -> SliceContext:
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    try:
        yield SliceContext(client=TestClient(app), state=state)
    finally:
        app.dependency_overrides.clear()


@given("HiveSight is configured with an unavailable local command Varroa Detector adapter")
def configured_unavailable_local_adapter(slice_context: SliceContext, tmp_path: Path) -> None:
    missing_command = tmp_path / "missing-varroa-detector"
    adapter = LocalCommandVarroaDetectorAdapter(
        command=[str(missing_command)],
        model_reference="fake-model",
        timeout_seconds=1,
    )
    app.dependency_overrides[get_varroa_review_workflow] = lambda: VarroaReviewWorkflow(
        store=slice_context.state.store,
        image_loader=slice_context.state.object_storage.get_object,
        varroa_detector_adapter=adapter,
    )


@given("a photo has an eligible Head-Up Normalized Bee Crop")
def photo_has_eligible_head_up_crop(slice_context: SliceContext) -> None:
    workspace_id, crop_id, bee_annotation_id, _ = _completed_crop_with_two_bees(
        slice_context.client
    )
    slice_context.workspace_id = workspace_id
    slice_context.crop_id = crop_id
    slice_context.bee_annotation_id = bee_annotation_id


@when("a developer runs a Varroa Detector preview for that bee")
def developer_runs_detector_preview(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.crop_id and slice_context.bee_annotation_id
    slice_context.response = slice_context.client.post(
        f"/v1/training-crops/{slice_context.crop_id}/varroa-review-candidates/"
        f"{slice_context.bee_annotation_id}/detector-preview",
        json={"workspace_id": slice_context.workspace_id},
        headers=_headers(),
    )


@then("HiveSight reports that the Varroa Detector failed")
def detector_failed(slice_context: SliceContext) -> None:
    assert slice_context.response.status_code == 200
    assert slice_context.response.json()["status"] == "failed"
    assert slice_context.response.json()["failure_code"] == "varroa_detector_command_unavailable"


@then("HiveSight does not return deterministic stub detections")
def no_stub_detections(slice_context: SliceContext) -> None:
    body = slice_context.response.json()
    assert body["adapter_type"] == "local_command"
    assert body["detections"] == []


@given("a Varroa assessment photo has two eligible Head-Up Normalized Bee Crops")
def varroa_photo_has_two_eligible_bees(slice_context: SliceContext) -> None:
    workspace_id, crop_id, _, _ = _completed_crop_with_two_bees(slice_context.client)
    slice_context.workspace_id = workspace_id
    slice_context.crop_id = crop_id
    slice_context.inspection_photo_id = _inspection_photo_id_for_crop(slice_context.state, crop_id)


@given("one bee detector call fails during Photo Analysis")
def one_bee_detector_call_fails(slice_context: SliceContext) -> None:
    adapter = FailFirstThenDetectAdapter()
    app.dependency_overrides[get_varroa_photo_analysis_workflow] = lambda: VarroaPhotoAnalysisWorkflow(
        store=slice_context.state.store,
        image_loader=slice_context.state.object_storage.get_object,
        varroa_detector_adapter=adapter,
    )


@when("HiveSight runs Varroa Photo Analysis for that photo")
def run_photo_analysis(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.inspection_photo_id
    slice_context.response = _run_photo_analysis(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.inspection_photo_id,
    )


@then("HiveSight persists one Photo Analysis run for the photo")
def one_photo_analysis_run_persisted(slice_context: SliceContext) -> None:
    assert slice_context.response.status_code == 200
    listed = slice_context.client.get(
        f"/v1/inspection-photos/{slice_context.inspection_photo_id}/varroa-photo-analyses"
        f"?workspace_id={slice_context.workspace_id}",
        headers=_headers(),
    )
    assert listed.status_code == 200
    assert len(listed.json()["runs"]) == 1


@then("HiveSight persists one per-bee analysis record for each attempted eligible bee")
def per_bee_records_persisted(slice_context: SliceContext) -> None:
    assert len(slice_context.response.json()["bee_results"]) == 2


@then("the Photo Analysis is marked partial with analysed bees, failed bees, and mites found")
def photo_analysis_partial_counts(slice_context: SliceContext) -> None:
    body = slice_context.response.json()
    assert body["status"] == "partial"
    assert body["analysed_bees"] == 1
    assert body["failed_bees"] == 1
    assert body["mites_found"] == 1


@given("a Varroa assessment photo has no bees eligible for Varroa evaluation")
def varroa_photo_has_no_usable_bees(slice_context: SliceContext) -> None:
    workspace_id, crop_id, first_bee_id, _ = _completed_crop_with_two_bees(
        slice_context.client,
        second_annotation_type="partial_visible_bee",
        complete_crop=False,
    )
    _patch_ellipse(
        slice_context.client,
        workspace_id,
        first_bee_id,
        annotation_type="partial_visible_bee",
    )
    assert _complete_crop(slice_context.client, workspace_id, crop_id).status_code == 200
    slice_context.workspace_id = workspace_id
    slice_context.crop_id = crop_id
    slice_context.inspection_photo_id = _inspection_photo_id_for_crop(slice_context.state, crop_id)
    app.dependency_overrides[get_varroa_photo_analysis_workflow] = lambda: VarroaPhotoAnalysisWorkflow(
        store=slice_context.state.store,
        image_loader=slice_context.state.object_storage.get_object,
        product_candidate_geometries=(),
    )


@then("HiveSight records the Photo Analysis as no usable bees")
def photo_analysis_no_usable_bees(slice_context: SliceContext) -> None:
    assert slice_context.response.status_code == 200
    assert slice_context.response.json()["status"] == "no_usable_bees"


@then("the Photo Analysis cannot be accepted as Advisor evidence")
def no_usable_bees_not_acceptable(slice_context: SliceContext) -> None:
    response = _review_photo_analysis(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.response.json()["photo_analysis_run_id"],
        "accepted",
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "photo_analysis_not_acceptable"


@given("a completed Varroa Photo Analysis is unreviewed")
def completed_photo_analysis_unreviewed(slice_context: SliceContext) -> None:
    workspace_id, crop_id, _, _ = _completed_crop_with_two_bees(slice_context.client)
    inspection_photo_id = _inspection_photo_id_for_crop(slice_context.state, crop_id)
    response = _run_photo_analysis(slice_context.client, workspace_id, inspection_photo_id)
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["review_status"] == "unreviewed"
    slice_context.workspace_id = workspace_id
    slice_context.inspection_photo_id = inspection_photo_id
    slice_context.response = response


@when("the Beekeeper marks the Photo Analysis as accepted")
def beekeeper_accepts_photo_analysis(slice_context: SliceContext) -> None:
    slice_context.response = _review_photo_analysis(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.response.json()["photo_analysis_run_id"],
        "accepted",
        "Good enough to use.",
    )


@then("HiveSight marks that Photo Analysis as eligible for later Advisor evidence")
def accepted_photo_analysis_is_advisor_eligible(slice_context: SliceContext) -> None:
    assert slice_context.response.status_code == 200
    assert slice_context.response.json()["review_status"] == "accepted"
    assert slice_context.response.json()["advisor_evidence_eligible"] is True
