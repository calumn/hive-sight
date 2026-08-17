from dataclasses import dataclass, field
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from test_vertical_slice_0025_varroa_review_slice import _completed_crop_with_two_bees, _headers
from test_vertical_slice_0033_varroa_photo_analysis import (
    FailFirstThenDetectAdapter,
    _inspection_photo_id_for_crop,
)

from hive_sight_core_api.dependencies import (
    build_dev_state,
    get_dev_state,
    get_varroa_photo_analysis_workflow,
)
from hive_sight_core_api.main import app
from hive_sight_core_api.varroa_photo_analysis_workflow import VarroaPhotoAnalysisWorkflow


scenarios("../../../acceptance/features/varroa/varroa-photo-analysis-workflow.feature")


@dataclass
class SliceContext:
    client: TestClient
    state: object
    workspace_id: str | None = None
    inspection_photo_id: str | None = None
    response: object | None = None
    start_response: object | None = None
    fail_first_detector_call: bool = False
    no_bees_found: bool = False


@pytest.fixture
def slice_context(tmp_path: Path) -> SliceContext:
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    context = SliceContext(client=TestClient(app), state=state)
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_varroa_photo_analysis_workflow] = lambda: VarroaPhotoAnalysisWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        varroa_detector_adapter=(FailFirstThenDetectAdapter() if context.fail_first_detector_call else NoneAdapter()),
        product_candidate_geometries=(
            ()
            if context.no_bees_found
            else (
                {"x": 0.32, "y": 0.5, "width": 0.22, "height": 0.44, "rotation_degrees": 0.0},
                {"x": 0.68, "y": 0.5, "width": 0.22, "height": 0.44, "rotation_degrees": 0.0},
            )
        ),
    )
    try:
        yield context
    finally:
        app.dependency_overrides.clear()


class NoneAdapter:
    adapter_type = "deterministic_stub"
    adapter_version = "product_photo_stub_v1"
    model_reference = "product_photo_stub_v1"
    command_contract_version = "varroa_detector_command_v1"

    def detect(self, request):
        return [
            {
                "detection_id": "deterministic-visible-varroa",
                "x": 0.5,
                "y": 0.5,
                "width": 0.08,
                "height": 0.06,
                "confidence": 0.9,
                "coordinate_space": "head_up_normalized_crop",
                "source": "deterministic_product_stub",
            }
        ]


def _ensure_photo(context: SliceContext) -> None:
    if context.inspection_photo_id:
        return
    workspace_id, crop_id, _, _ = _completed_crop_with_two_bees(context.client)
    context.workspace_id = workspace_id
    context.inspection_photo_id = _inspection_photo_id_for_crop(context.state, crop_id)


def _analyse(context: SliceContext) -> None:
    assert context.workspace_id and context.inspection_photo_id
    context.start_response = context.client.post(
        f"/v1/inspection-photos/{context.inspection_photo_id}/varroa-photo-analyses",
        json={"workspace_id": context.workspace_id},
        headers=_headers(),
    )
    assert context.start_response.status_code == 202
    context.response = context.client.get(
        f"/v1/inspection-photos/{context.inspection_photo_id}/varroa-photo-analyses"
        f"?workspace_id={context.workspace_id}",
        headers=_headers(),
    )
    assert context.response.status_code == 200
    context.response = _latest_run_response(context.response)


def _latest_run_response(response):
    class CompletedResponse:
        def __init__(self, payload):
            self._payload = payload
            self.status_code = 200

        def json(self):
            return self._payload

    return CompletedResponse(response.json()["runs"][-1])


@given("a Workspace member has a Varroa Assessment Inspection with an uploaded photo")
def uploaded_varroa_photo(slice_context: SliceContext) -> None:
    _ensure_photo(slice_context)


@given("that photo has no prior Photo Analysis")
def no_prior_analysis(slice_context: SliceContext) -> None:
    _ensure_photo(slice_context)


@when("the Workspace member requests photo analysis")
def request_photo_analysis(slice_context: SliceContext) -> None:
    _analyse(slice_context)


@then("HiveSight starts one Photo Analysis for that Inspection Photo")
def one_analysis_started(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    assert slice_context.start_response is not None
    assert slice_context.start_response.status_code == 202


@then("HiveSight reports the Photo Analysis as unreviewed")
def analysis_is_unreviewed(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["review_status"] == "unreviewed"


@then("HiveSight reports the number of analysed eligible bees and bees with likely visible Varroa")
def analysis_reports_bee_counts(slice_context: SliceContext) -> None:
    body = slice_context.response.json()
    assert body["analysed_bees"] == 2
    assert body["bees_with_likely_varroa"] == 2


@then("HiveSight does not require a Training Crop")
def analysis_does_not_require_training_crop(slice_context: SliceContext) -> None:
    assert all(result["training_crop_id"] is None for result in slice_context.response.json()["bee_results"])


@given("a Photo Analysis localises complete bees")
def product_analysis_has_complete_bees(slice_context: SliceContext) -> None:
    _ensure_photo(slice_context)


@given("orientation or Varroa Detection cannot process one of those bees")
def one_bee_processing_fails(slice_context: SliceContext) -> None:
    slice_context.fail_first_detector_call = True


@when("HiveSight completes the Photo Analysis")
def complete_photo_analysis(slice_context: SliceContext) -> None:
    _analyse(slice_context)


@then("HiveSight reports the Photo Analysis as partial")
def analysis_is_partial(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["status"] == "partial"


@then("HiveSight reports the failed-bee count and caveat")
def partial_analysis_has_caveat(slice_context: SliceContext) -> None:
    body = slice_context.response.json()
    assert body["failed_bees"] == 1
    assert "incomplete" in body["caveat"]


@then("a Workspace member can accept the result")
def partial_analysis_can_be_accepted(slice_context: SliceContext) -> None:
    body = slice_context.response.json()
    accepted = slice_context.client.patch(
        f"/v1/varroa-photo-analyses/{body['photo_analysis_run_id']}/review",
        json={"workspace_id": slice_context.workspace_id, "review_status": "accepted"},
        headers=_headers(),
    )
    assert accepted.status_code == 200


@given("a Photo Analysis finds no complete bees in an Inspection Photo")
def product_analysis_finds_no_bees(slice_context: SliceContext) -> None:
    _ensure_photo(slice_context)
    slice_context.no_bees_found = True


@then("HiveSight reports no bees found")
def analysis_reports_no_bees_found(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["status"] == "no_usable_bees"


@then("a Workspace member cannot accept the result")
def no_bees_cannot_be_accepted(slice_context: SliceContext) -> None:
    body = slice_context.response.json()
    accepted = slice_context.client.patch(
        f"/v1/varroa-photo-analyses/{body['photo_analysis_run_id']}/review",
        json={"workspace_id": slice_context.workspace_id, "review_status": "accepted"},
        headers=_headers(),
    )
    assert accepted.status_code == 409


@given("a completed or partial Photo Analysis is unreviewed")
def completed_analysis_is_unreviewed(slice_context: SliceContext) -> None:
    _ensure_photo(slice_context)
    _analyse(slice_context)
    assert slice_context.response.json()["review_status"] == "unreviewed"


@when("a Workspace member marks it accepted")
def mark_analysis_accepted(slice_context: SliceContext) -> None:
    body = slice_context.response.json()
    slice_context.response = slice_context.client.patch(
        f"/v1/varroa-photo-analyses/{body['photo_analysis_run_id']}/review",
        json={"workspace_id": slice_context.workspace_id, "review_status": "accepted"},
        headers=_headers(),
    )


@then("HiveSight marks it as development integration evidence for later Advisor integration testing")
def accepted_analysis_is_advisor_eligible(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["advisor_evidence_eligibility"] == "development_integration_only"


@when("a Workspace member changes it to needs expert review with a note")
def mark_analysis_needs_expert_review(slice_context: SliceContext) -> None:
    body = slice_context.response.json()
    slice_context.response = slice_context.client.patch(
        f"/v1/varroa-photo-analyses/{body['photo_analysis_run_id']}/review",
        json={
            "workspace_id": slice_context.workspace_id,
            "review_status": "needs_expert_review",
            "review_note": "Please review the model evidence.",
        },
        headers=_headers(),
    )


@then("HiveSight marks it ineligible for later Advisor evidence")
def nonaccepted_analysis_is_not_advisor_eligible(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["advisor_evidence_eligibility"] == "ineligible"
