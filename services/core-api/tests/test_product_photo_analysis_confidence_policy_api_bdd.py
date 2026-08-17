from dataclasses import dataclass
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


scenarios("../../../acceptance/features/varroa/product-photo-analysis-confidence-policy.feature")


@dataclass
class SliceContext:
    client: TestClient
    state: object
    workspace_id: str | None = None
    inspection_photo_id: str | None = None
    response: object | None = None
    adapter: object | None = None
    no_bees_found: bool = False


@pytest.fixture
def slice_context(tmp_path: Path) -> SliceContext:
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    context = SliceContext(client=TestClient(app), state=state)
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_varroa_photo_analysis_workflow] = lambda: VarroaPhotoAnalysisWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        varroa_detector_adapter=context.adapter or DeterministicDevelopmentAdapter(),
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


class DeterministicDevelopmentAdapter:
    adapter_type = "deterministic_stub"
    adapter_version = "product_photo_stub_v1"
    model_reference = "product_photo_stub_v1"
    command_contract_version = "varroa_detector_command_v1"

    def detect(self, request):
        return [_detection(confidence=0.9, source="deterministic_product_stub")]


class HighConfidenceNonStubAdapter:
    adapter_type = "local_command"
    adapter_version = "fake_local_command_v1"
    model_reference = "fake-varroa-model"
    command_contract_version = "varroa_detector_command_v1"

    def detect(self, request):
        return [_detection(confidence=0.91, source="fake_local_command")]


class LowConfidenceOnlyNonStubAdapter(HighConfidenceNonStubAdapter):
    def detect(self, request):
        return [_detection(confidence=0.62, source="fake_local_command")]


class ZeroDetectionNonStubAdapter(HighConfidenceNonStubAdapter):
    def detect(self, request):
        return []


def _detection(*, confidence: float, source: str) -> dict[str, object]:
    return {
        "detection_id": f"{source}-{confidence}",
        "x": 0.5,
        "y": 0.5,
        "width": 0.08,
        "height": 0.06,
        "confidence": confidence,
        "coordinate_space": "head_up_normalized_crop",
        "source": source,
    }


def _ensure_photo(context: SliceContext) -> None:
    if context.inspection_photo_id:
        return
    workspace_id, crop_id, _, _ = _completed_crop_with_two_bees(context.client)
    context.workspace_id = workspace_id
    context.inspection_photo_id = _inspection_photo_id_for_crop(context.state, crop_id)


def _analyse(context: SliceContext) -> None:
    _ensure_photo(context)
    assert context.workspace_id and context.inspection_photo_id
    started = context.client.post(
        f"/v1/inspection-photos/{context.inspection_photo_id}/varroa-photo-analyses",
        json={"workspace_id": context.workspace_id},
        headers=_headers(),
    )
    assert started.status_code == 202
    listed = context.client.get(
        f"/v1/inspection-photos/{context.inspection_photo_id}/varroa-photo-analyses"
        f"?workspace_id={context.workspace_id}",
        headers=_headers(),
    )
    assert listed.status_code == 200
    context.response = CompletedResponse(listed.json()["runs"][-1])


def _accept(context: SliceContext) -> None:
    assert context.response is not None and context.workspace_id is not None
    body = context.response.json()
    context.response = context.client.patch(
        f"/v1/varroa-photo-analyses/{body['photo_analysis_run_id']}/review",
        json={"workspace_id": context.workspace_id, "review_status": "accepted"},
        headers=_headers(),
    )
    assert context.response.status_code == 200


class CompletedResponse:
    status_code = 200

    def __init__(self, payload: dict):
        self._payload = payload

    def json(self) -> dict:
        return self._payload


@given("a Varroa Assessment Photo Analysis was produced by the deterministic development adapter")
def deterministic_analysis(slice_context: SliceContext) -> None:
    slice_context.adapter = DeterministicDevelopmentAdapter()
    _analyse(slice_context)


@given("a Varroa Assessment Photo Analysis was produced by a replaceable non-stub adapter")
def non_stub_analysis(slice_context: SliceContext) -> None:
    slice_context.adapter = HighConfidenceNonStubAdapter()
    _analyse(slice_context)


@given("every localised complete bee has usable orientation and Varroa Detector evidence")
def all_bees_have_detector_evidence(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    body = slice_context.response.json()
    assert body["status"] == "completed"
    assert body["analysed_bees"] == body["eligible_bees"]


@given('the Varroa Detector evidence satisfies product photo confidence policy version "product_photo_confidence_policy_v1"')
def detector_evidence_satisfies_policy(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    assert slice_context.response.json()["confidence_policy_version"] == "product_photo_confidence_policy_v1"


@given("a Varroa Assessment Photo Analysis includes a bee with only Varroa detections below the policy confidence floor")
def low_confidence_only_analysis(slice_context: SliceContext) -> None:
    slice_context.adapter = LowConfidenceOnlyNonStubAdapter()
    _analyse(slice_context)


@given("a completed non-stub Varroa Assessment Photo Analysis has zero likely Varroa detections")
def zero_detection_analysis(slice_context: SliceContext) -> None:
    slice_context.adapter = ZeroDetectionNonStubAdapter()
    _analyse(slice_context)
    assert slice_context.response is not None
    assert slice_context.response.json()["bees_with_likely_varroa"] == 0


@given("every eligible complete bee has a completed detector call with acceptable provenance")
def every_bee_has_completed_detector_call(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    body = slice_context.response.json()
    assert body["status"] == "completed"
    assert all(result["status"] == "completed" for result in body["bee_results"])
    assert body["adapter_type"] == "local_command"


@given("a Varroa Assessment Photo Analysis has eligible complete bees that were not assessed for Varroa")
def partial_analysis(slice_context: SliceContext) -> None:
    slice_context.adapter = FailFirstThenDetectAdapter()
    _analyse(slice_context)
    assert slice_context.response is not None
    assert slice_context.response.json()["status"] == "partial"


@when("a Workspace member views the Photo Analysis confidence policy")
def view_confidence_policy(slice_context: SliceContext) -> None:
    assert slice_context.response is not None


@when("HiveSight applies the Product Photo Analysis Confidence Policy")
def apply_confidence_policy(slice_context: SliceContext) -> None:
    assert slice_context.response is not None


@when("the Workspace member marks the Photo Analysis accepted")
@when("a Workspace member marks the Photo Analysis accepted")
def mark_accepted(slice_context: SliceContext) -> None:
    _accept(slice_context)


@then("HiveSight labels the run as development model evidence only")
def labels_development_only(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    body = slice_context.response.json()
    assert body["confidence_policy_status"] == "development_evidence_only"
    assert "development_model_evidence" in body["confidence_policy_caveats"]


@then("HiveSight reports the Advisor evidence eligibility as ineligible")
def reports_ineligible(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    assert slice_context.response.json()["advisor_evidence_eligibility"] == "ineligible"


@then("HiveSight reports the Advisor evidence eligibility as development integration only")
def reports_development_integration(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    assert slice_context.response.json()["advisor_evidence_eligibility"] == "development_integration_only"


@then("HiveSight does not label the run as product-candidate evidence")
def not_product_candidate(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    assert slice_context.response.json()["advisor_evidence_eligibility"] != "product_candidate"


@then("HiveSight records the confidence policy status as advisor candidate possible")
def records_advisor_candidate_possible(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    assert slice_context.response.json()["confidence_policy_status"] == "advisor_candidate_possible"


@then("HiveSight reports that accepted review is required before later Advisor use")
def review_required(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    assert slice_context.response.json()["review_status"] == "unreviewed"
    assert slice_context.response.json()["advisor_evidence_eligibility"] == "ineligible"


@then("HiveSight reports the Advisor evidence eligibility as product candidate")
def reports_product_candidate(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    assert slice_context.response.json()["advisor_evidence_eligibility"] == "product_candidate"


@then("HiveSight keeps the detection visible in the evidence detail")
def keeps_detection_visible(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    body = slice_context.response.json()
    assert any(result["detections"] for result in body["bee_results"])


@then("HiveSight reports a confidence warning for Varroa Detection")
def reports_confidence_warning(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    body = slice_context.response.json()
    assert body["confidence_policy_status"] == "blocked_by_confidence_policy"
    assert body["varroa_detection_policy_status"] == "blocked_by_confidence_policy"
    assert "low_confidence_varroa_detection_only" in body["confidence_policy_caveats"]


@then("HiveSight does not state that no Varroa is present in the hive")
def does_not_claim_no_varroa(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    messages = " ".join(slice_context.response.json()["confidence_policy_caveat_messages"]).lower()
    assert "no varroa is present" not in messages


@then("HiveSight reports the unassessed bee count as a coverage limitation")
def reports_unassessed_bees(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    body = slice_context.response.json()
    assert body["confidence_policy_status"] == "blocked_by_coverage_policy"
    assert body["unassessed_complete_bees"] == 1


@then("HiveSight does not treat unassessed bees as no-visible-Varroa evidence")
def unassessed_not_negative(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    body = slice_context.response.json()
    assert body["failed_bees"] == body["unassessed_complete_bees"]
    assert "unassessed_complete_bees_present" in body["confidence_policy_caveats"]
