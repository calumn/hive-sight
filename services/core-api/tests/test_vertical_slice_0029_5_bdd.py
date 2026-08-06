from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from hive_sight_core_api.advisor_treatment_recommendation_workflow import (
    AdvisorTreatmentRecommendationWorkflow,
    DeterministicStubAdvisorTreatmentPlanAdapter,
    FailingAdvisorTreatmentPlanAdapter,
)
from hive_sight_core_api.dependencies import (
    build_dev_state,
    get_advisor_treatment_recommendation_workflow,
    get_dev_state,
)
from hive_sight_core_api.dev_users import DEV_USERS
from hive_sight_core_api.main import app
from hive_sight_core_api.models import (
    AdvisorRequestReadiness,
    AdvisorRequiredSituationalInputsContext,
    AdvisorTreatmentHistoryContext,
    AdvisorVarroaContextResponse,
    AdvisorVarroaContextStatus,
    AdvisorVarroaEvidence,
    AdvisorVarroaFrameMiteCountEvidence,
    AdvisorVarroaPhotoVisibleEvidence,
    FrameMiteCountStatus,
    HiveTreatmentCourseResponse,
    InspectionIntent,
    TreatmentEvidenceChainState,
    TreatmentRecommendationStatus,
)

FEATURES_DIR = Path(__file__).parent / "features"

scenarios(
    str(FEATURES_DIR / "vertical_slice_0029_5_advisor_treatment_recommendation_intake.feature")
)


@dataclass
class SliceContext:
    client: TestClient
    state: object
    seed = DEV_USERS[0]
    inspection_photo_id: UUID = field(default_factory=uuid4)
    inspection_id: UUID = field(default_factory=uuid4)
    jurisdiction_code: str = "gb-eng"
    ready: bool = True
    adapter_should_fail: bool = False
    allow_stub_adapter_for_product_data: bool = True
    response: object | None = None
    first_response: object | None = None
    first_course_id: str | None = None
    recommendation_id: str | None = None
    chain_id: str | None = None


@pytest.fixture
def slice_context(tmp_path: Path) -> SliceContext:
    state = build_dev_state(dataset_export_root=tmp_path / "exports", dev_users_enabled=True)
    context = SliceContext(client=TestClient(app), state=state)
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_advisor_treatment_recommendation_workflow] = (
        lambda: AdvisorTreatmentRecommendationWorkflow(
            store=state.store,
            context_builder=SyntheticAdvisorContextBuilder(context),
            adapter=(
                FailingAdvisorTreatmentPlanAdapter()
                if context.adapter_should_fail
                else DeterministicStubAdvisorTreatmentPlanAdapter()
            ),
            allow_stub_adapter_for_product_data=context.allow_stub_adapter_for_product_data,
        )
    )
    try:
        yield context
    finally:
        app.dependency_overrides.clear()


class SyntheticAdvisorContextBuilder:
    def __init__(self, context: SliceContext) -> None:
        self.context = context
        self.call_count = 0

    def assemble_context(
        self,
        *,
        user,
        hive_id: UUID,
        inspection_photo_id: UUID,
        jurisdiction_id: str | None,
    ) -> AdvisorVarroaContextResponse:
        self.call_count += 1
        seed = self.context.seed
        blockers = [] if self.context.ready else ["treatment_history_not_modelled"]
        return AdvisorVarroaContextResponse(
            status=AdvisorVarroaContextStatus.available,
            workspace_id=seed.workspace_id,
            hive_id=hive_id,
            apiary_id=seed.apiary_id,
            inspection_id=self.context.inspection_id,
            inspection_photo_id=inspection_photo_id,
            inspection_date=date(2026, 8, 6),
            jurisdiction_id=jurisdiction_id,
            varroa_evidence=AdvisorVarroaEvidence(
                source_intent=InspectionIntent.varroa_assessment,
                evidence_readiness="advisor_ready",
                frame_mite_count=AdvisorVarroaFrameMiteCountEvidence(
                    status=FrameMiteCountStatus.completed,
                    eligible_bee_count=120,
                    processed_bee_count=120,
                    bees_with_likely_varroa_count=9,
                    likely_visible_varroa_detection_count=11,
                    model_determinate_coverage_percent=100,
                    completed_training_crop_count=5,
                    unfinished_training_crop_count=0,
                    excluded_training_crop_count=0,
                    not_assessed_bee_count=0,
                    failed_bee_count=0,
                    adapter_type="deterministic_stub",
                    adapter_version="deterministic_stub_varroa_detector_v1",
                    model_reference="deterministic_stub_varroa_detector_v1",
                    caveats="Synthetic accepted Slice 0029.5 context.",
                ),
                photo_visible_varroa_evidence=AdvisorVarroaPhotoVisibleEvidence(
                    readiness_state="complete",
                    eligible_complete_bee_count=120,
                    reviewed_eligible_bee_count=120,
                    determinate_eligible_bee_count=120,
                    visible_varroa_bee_count=4,
                    visible_mite_marker_count=5,
                    active_negative_bee_count=116,
                    not_determined_bee_count=0,
                    review_completion_percent=100,
                    determinate_varroa_coverage_percent=100,
                    caveats="Synthetic accepted Slice 0029.5 context.",
                ),
            ),
            treatment_history=AdvisorTreatmentHistoryContext(status="modelled"),
            advisor_required_situational_inputs=AdvisorRequiredSituationalInputsContext(
                status="modelled"
            ),
            advisor_request_readiness=AdvisorRequestReadiness(
                can_request_advice=self.context.ready,
                blocking_reasons=blockers,
            ),
            not_advice_reason="HiveSight context only; treatment advice comes from Advisor.",
        )


def _headers() -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(DEV_USERS[0].user_id)}


def _request_advice(context: SliceContext):
    return context.client.post(
        f"/v1/hives/{context.seed.hive_id}/advisor-treatment-recommendations",
        json={
            "inspection_photo_id": str(context.inspection_photo_id),
            "jurisdiction_code": context.jurisdiction_code,
        },
        headers=_headers(),
    )


def _accept(context: SliceContext, recommendation_id: str | None = None):
    return context.client.post(
        f"/v1/treatment-recommendations/{recommendation_id or context.recommendation_id}/accept",
        json={"note": "Accepted from accepted Slice 0029.5 scenario."},
        headers=_headers(),
    )


def _decline(context: SliceContext, recommendation_id: str | None = None):
    return context.client.post(
        f"/v1/treatment-recommendations/{recommendation_id or context.recommendation_id}/decline",
        json={"note": "Declined from accepted Slice 0029.5 scenario."},
        headers=_headers(),
    )


def _create_pending_recommendation(context: SliceContext) -> dict:
    response = _request_advice(context)
    assert response.status_code == 201
    body = response.json()
    context.response = response
    context.recommendation_id = body["recommendation"]["treatment_recommendation_id"]
    context.chain_id = body["chain"]["treatment_evidence_chain_id"]
    return body


@given(
    "a Beekeeper can access a Hive with Advisor-ready Varroa Assessment context for one Inspection Photo"
)
def advisor_ready_context(slice_context: SliceContext) -> None:
    slice_context.ready = True


@given("a Beekeeper can access a Hive with Advisor Varroa context")
def advisor_context(slice_context: SliceContext) -> None:
    slice_context.ready = True


@given("the Hive has no open planned Varroa treatment course")
def no_open_treatment_course(slice_context: SliceContext) -> None:
    assert slice_context.state.store.hive_treatment_courses == {}


@given("HiveSight has a jurisdiction for the Advisor treatment-plan request")
def jurisdiction_available(slice_context: SliceContext) -> None:
    slice_context.jurisdiction_code = "gb-eng"


@given("the context has request-readiness blockers")
def context_has_readiness_blockers(slice_context: SliceContext) -> None:
    slice_context.ready = False


@given("the configured Advisor treatment-plan adapter fails to return usable advice")
def failing_adapter(slice_context: SliceContext) -> None:
    slice_context.adapter_should_fail = True


@given("HiveSight has a pending Treatment Recommendation for a Hive")
@given("HiveSight has one pending Varroa Treatment Recommendation for a Hive")
@given("HiveSight has stored a Treatment Recommendation and related Treatment Evidence Chain")
@given("HiveSight has stored a Treatment Evidence Chain for Advisor treatment advice")
def pending_recommendation(slice_context: SliceContext) -> None:
    _create_pending_recommendation(slice_context)


@given("the Beekeeper has already accepted that recommendation once")
def recommendation_already_accepted_once(slice_context: SliceContext) -> None:
    response = _accept(slice_context)
    assert response.status_code == 200
    slice_context.first_response = response
    slice_context.first_course_id = response.json()["hive_treatment_course_id"]


@given("HiveSight has a declined Treatment Recommendation for a Hive")
def declined_recommendation(slice_context: SliceContext) -> None:
    _create_pending_recommendation(slice_context)
    response = _decline(slice_context)
    assert response.status_code == 200
    slice_context.first_response = response


@given("HiveSight has an accepted Treatment Recommendation for a Hive")
def accepted_recommendation(slice_context: SliceContext) -> None:
    _create_pending_recommendation(slice_context)
    response = _accept(slice_context)
    assert response.status_code == 200


@given("HiveSight is running in production-like configuration")
def production_like_configuration(slice_context: SliceContext) -> None:
    slice_context.allow_stub_adapter_for_product_data = False


@given("the configured Advisor treatment-plan adapter is the deterministic stub")
def deterministic_stub_adapter(slice_context: SliceContext) -> None:
    assert slice_context.adapter_should_fail is False


@given("a Hive already has an open planned Varroa treatment course")
def open_planned_course(slice_context: SliceContext) -> None:
    seed = slice_context.seed
    course = HiveTreatmentCourseResponse(
        hive_treatment_course_id=uuid4(),
        workspace_id=seed.workspace_id,
        apiary_id=seed.apiary_id,
        hive_id=seed.hive_id,
        planned_course_snapshot={"source": "pre-existing course"},
        created_by_user_id=seed.user_id,
        created_at=datetime(2026, 8, 6, tzinfo=UTC),
    )
    slice_context.state.store.save_hive_treatment_course(course)


@given(
    "a Hive has a blocked advice attempt, a failed advice attempt, a pending recommendation, and an accepted recommendation"
)
def mixed_history(slice_context: SliceContext) -> None:
    slice_context.ready = False
    blocked = _request_advice(slice_context)
    assert blocked.status_code == 201
    slice_context.ready = True
    slice_context.adapter_should_fail = True
    failed = _request_advice(slice_context)
    assert failed.status_code == 201
    slice_context.adapter_should_fail = False
    pending = _create_pending_recommendation(slice_context)
    chain = slice_context.state.store.treatment_evidence_chains[
        UUID(pending["chain"]["treatment_evidence_chain_id"])
    ]
    recommendation = slice_context.state.store.treatment_recommendations[
        UUID(pending["recommendation"]["treatment_recommendation_id"])
    ]
    accepted_chain = chain.model_copy(
        update={
            "treatment_evidence_chain_id": uuid4(),
            "state": TreatmentEvidenceChainState.recommendation_accepted,
        }
    )
    slice_context.state.store.save_treatment_evidence_chain(accepted_chain)
    slice_context.state.store.save_treatment_recommendation(
        recommendation.model_copy(
            update={
                "treatment_recommendation_id": uuid4(),
                "treatment_evidence_chain_id": accepted_chain.treatment_evidence_chain_id,
                "status": TreatmentRecommendationStatus.accepted,
            }
        )
    )


@when("the Beekeeper requests Advisor treatment advice for that Hive evidence")
@when("the Beekeeper requests Advisor treatment advice")
@when("the Beekeeper requests Advisor treatment advice again for the same Hive")
@when("a Beekeeper requests Advisor treatment advice")
@when("the Beekeeper requests a new Advisor treatment recommendation for that Hive")
def beekeeper_requests_advice(slice_context: SliceContext) -> None:
    slice_context.response = _request_advice(slice_context)


@when("the Beekeeper accepts the recommendation")
@when("the Beekeeper accepts the same recommendation again")
def beekeeper_accepts_recommendation(slice_context: SliceContext) -> None:
    slice_context.response = _accept(slice_context)


@when("the Beekeeper declines the recommendation with an optional note")
@when("the Beekeeper declines the same recommendation again")
def beekeeper_declines_recommendation(slice_context: SliceContext) -> None:
    slice_context.response = _decline(slice_context)


@when("the Beekeeper tries to decline the accepted recommendation")
def beekeeper_declines_accepted(slice_context: SliceContext) -> None:
    slice_context.response = _decline(slice_context)


@when("the Beekeeper reads the Hive's Advisor treatment advice-attempt history")
def beekeeper_reads_attempt_history(slice_context: SliceContext) -> None:
    slice_context.response = slice_context.client.get(
        f"/v1/hives/{slice_context.seed.hive_id}/advisor-treatment-advice-attempts",
        headers=_headers(),
    )


@when("the Beekeeper reads a single Treatment Evidence Chain")
@when("the Beekeeper reads the single Treatment Evidence Chain")
def beekeeper_reads_single_chain(slice_context: SliceContext) -> None:
    if slice_context.chain_id is None:
        _create_pending_recommendation(slice_context)
    slice_context.response = slice_context.client.get(
        f"/v1/treatment-evidence-chains/{slice_context.chain_id}",
        headers=_headers(),
    )


@then("HiveSight sends the Advisor request through the configured Advisor treatment-plan adapter")
def advisor_request_sent(slice_context: SliceContext) -> None:
    assert slice_context.response.status_code == 201
    assert slice_context.response.json()["request_snapshot"]["request_status"] == "sent"


@then("HiveSight stores the full Advisor Varroa context snapshot")
def context_snapshot_stored(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["context_snapshot"]["context_payload"]


@then("HiveSight stores the Advisor request snapshot")
def request_snapshot_stored(slice_context: SliceContext) -> None:
    request_snapshot = slice_context.response.json()["request_snapshot"]
    assert request_snapshot["advisor_request_contract_version"]
    assert request_snapshot["jurisdiction_code"] == slice_context.jurisdiction_code
    assert request_snapshot["request_payload"]["jurisdiction_code"] == slice_context.jurisdiction_code
    assert "jurisdiction_id" not in request_snapshot["request_payload"]


@then("HiveSight stores the Advisor response as a pending Treatment Recommendation")
def pending_recommendation_stored(slice_context: SliceContext) -> None:
    body = slice_context.response.json()
    assert body["recommendation"]["status"] == "pending"
    assert body["recommendation"]["recommendation_text"]
    assert body["recommendation"]["advisor_answer_id"] == (
        f"stub-answer-{slice_context.seed.hive_id}"
    )
    assert body["recommendation"]["advisor_response_contract_version"] == "treatment_plan_v1"
    assert (
        body["recommendation"]["advisor_response_payload"]["contract_version"]
        == "treatment_plan_v1"
    )
    assert body["recommendation"]["advisor_response_payload"]["answer_id"]


@then(
    "the pending Treatment Recommendation is labelled as a suggested treatment plan requiring beekeeper decision"
)
def pending_label(slice_context: SliceContext) -> None:
    assert (
        slice_context.response.json()["recommendation"]["display_label"]
        == "suggested treatment plan requiring beekeeper decision"
    )


@then(
    "the Treatment Evidence Chain links the source context, request snapshot, response, Hive, Apiary, Workspace, Inspection, and Inspection Photo"
)
def chain_links_context(slice_context: SliceContext) -> None:
    body = slice_context.response.json()
    assert body["chain"]["hive_id"] == str(slice_context.seed.hive_id)
    assert body["chain"]["apiary_id"] == str(slice_context.seed.apiary_id)
    assert body["chain"]["workspace_id"] == str(slice_context.seed.workspace_id)
    assert body["context_snapshot"]["inspection_photo_id"] == str(slice_context.inspection_photo_id)
    assert body["request_snapshot"]["inspection_photo_id"] == str(slice_context.inspection_photo_id)
    assert body["recommendation"]["treatment_evidence_chain_id"] == body["chain"][
        "treatment_evidence_chain_id"
    ]


@then("HiveSight does not create a Hive Treatment Course yet")
@then("HiveSight does not create a Hive Treatment Course")
def no_course(slice_context: SliceContext) -> None:
    assert slice_context.state.store.hive_treatment_courses == {}


@then("HiveSight does not call HiveSight Advisor")
def advisor_not_called(slice_context: SliceContext) -> None:
    assert slice_context.response.status_code in {201, 409}
    if slice_context.response.status_code == 201:
        assert slice_context.response.json()["request_snapshot"] is None


@then("HiveSight does not create a Treatment Recommendation")
@then("HiveSight does not create a new Treatment Recommendation")
def no_recommendation(slice_context: SliceContext) -> None:
    if slice_context.response.status_code == 201:
        assert slice_context.response.json()["recommendation"] is None
    else:
        assert slice_context.state.store.treatment_recommendations == {}


@then("HiveSight records a blocked Treatment Evidence Chain with the readiness blockers")
def blocked_chain(slice_context: SliceContext) -> None:
    body = slice_context.response.json()
    assert body["chain"]["state"] == "blocked_not_ready"
    assert body["chain"]["blocked_reasons"] == ["treatment_history_not_modelled"]


@then("the blocked advice attempt is visible in the Hive's advice-attempt history")
@then("the failed advice attempt is visible in the Hive's advice-attempt history")
def attempt_visible_in_history(slice_context: SliceContext) -> None:
    response = slice_context.client.get(
        f"/v1/hives/{slice_context.seed.hive_id}/advisor-treatment-advice-attempts",
        headers=_headers(),
    )
    assert response.status_code == 200
    assert response.json()["treatment_evidence_chains"]


@then("HiveSight stores the failed Advisor request snapshot with adapter provenance")
def failed_snapshot(slice_context: SliceContext) -> None:
    body = slice_context.response.json()
    assert body["request_snapshot"]["request_status"] == "failed"
    assert body["request_snapshot"]["adapter_type"] == "hivesight_advisor"


@then("HiveSight records a failed Treatment Evidence Chain")
def failed_chain(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["chain"]["state"] == "advisor_request_failed"


@then("HiveSight records the recommendation decision as accepted")
def decision_accepted(slice_context: SliceContext) -> None:
    assert slice_context.response.status_code == 200
    assert slice_context.state.store.treatment_recommendations[
        UUID(slice_context.recommendation_id)
    ].status == TreatmentRecommendationStatus.accepted


@then("HiveSight creates a separate planned Hive Treatment Course for the same Hive")
def planned_course_created(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["hive_id"] == str(slice_context.seed.hive_id)
    assert slice_context.response.json()["status"] == "planned"


@then("the planned course is visible in Hive treatment-course history with status planned")
def course_history(slice_context: SliceContext) -> None:
    response = slice_context.client.get(
        f"/v1/hives/{slice_context.seed.hive_id}/treatment-courses",
        headers=_headers(),
    )
    assert response.status_code == 200
    assert response.json()["treatment_courses"][0]["status"] == "planned"


@then("the Hive Treatment Course keeps a provenance link to the Treatment Recommendation")
def course_provenance(slice_context: SliceContext) -> None:
    assert (
        slice_context.response.json()["source_treatment_recommendation_id"]
        == slice_context.recommendation_id
    )


@then("the planned course snapshots the beekeeper decision context")
def course_snapshot(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["planned_course_snapshot"]["recommendation_text"]


@then(
    "the Treatment Evidence Chain remains traceable from source context to Advisor request, Advisor response, beekeeper decision, and planned course"
)
def accepted_chain_traceable(slice_context: SliceContext) -> None:
    response = slice_context.client.get(
        f"/v1/treatment-evidence-chains/{slice_context.chain_id}",
        headers=_headers(),
    )
    body = response.json()
    assert body["context_snapshot"]
    assert body["request_snapshot"]
    assert body["recommendation"]["status"] == "accepted"
    assert body["treatment_course"]["status"] == "planned"


@then("HiveSight records the recommendation decision as declined")
def decision_declined(slice_context: SliceContext) -> None:
    assert slice_context.response.status_code == 200
    assert slice_context.response.json()["status"] == "declined"


@then("HiveSight keeps the original Advisor response unchanged")
def original_response_unchanged(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["advisor_response_payload"]["text"]


@then("HiveSight returns the existing pending Treatment Recommendation")
def existing_pending_returned(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["recommendation"]["treatment_recommendation_id"] == (
        slice_context.recommendation_id
    )


@then("HiveSight does not create a duplicate pending recommendation")
def no_duplicate_pending(slice_context: SliceContext) -> None:
    assert len(slice_context.state.store.treatment_recommendations) == 1


@then("HiveSight returns the same planned Hive Treatment Course both times")
def same_course_returned(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["hive_treatment_course_id"] == slice_context.first_course_id


@then("HiveSight creates only one planned Hive Treatment Course")
def one_course(slice_context: SliceContext) -> None:
    assert len(slice_context.state.store.hive_treatment_courses) == 1


@then("HiveSight returns the same declined Treatment Recommendation both times")
def same_decline(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["status"] == "declined"
    assert (
        slice_context.response.json()["treatment_recommendation_id"]
        == slice_context.first_response.json()["treatment_recommendation_id"]
    )


@then("HiveSight blocks the decline")
@then("HiveSight blocks the request")
@then("HiveSight blocks the request before creating treatment advice")
def request_blocked(slice_context: SliceContext) -> None:
    assert slice_context.response.status_code == 409


@then("HiveSight keeps the existing planned Hive Treatment Course")
def keeps_existing_course(slice_context: SliceContext) -> None:
    assert len(slice_context.state.store.hive_treatment_courses) == 1


@then("HiveSight explains that an open planned Varroa treatment course already exists")
def explains_open_course(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["detail"]["code"] == (
        "open_planned_varroa_treatment_course_exists"
    )


@then("HiveSight lists each Treatment Evidence Chain with a summary state")
def lists_chain_history(slice_context: SliceContext) -> None:
    body = slice_context.response.json()
    states = {item["state"] for item in body["treatment_evidence_chains"]}
    assert {
        "blocked_not_ready",
        "advisor_request_failed",
        "recommendation_pending",
        "recommendation_accepted",
    }.issubset(states)


@then("blocked and failed attempts are not shown as Treatment Recommendations")
def blocked_failed_not_recommendations(slice_context: SliceContext) -> None:
    response = slice_context.client.get(
        f"/v1/hives/{slice_context.seed.hive_id}/treatment-recommendations",
        headers=_headers(),
    )
    assert response.status_code == 200
    assert len(response.json()["treatment_recommendations"]) == 2


@then(
    "HiveSight includes the source context summary, request provenance, response provenance where present, decision where present, and planned course where present"
)
def single_chain_detail(slice_context: SliceContext) -> None:
    body = slice_context.response.json()
    assert body["context_snapshot"]["context_summary"]
    assert body["request_snapshot"]["adapter_version"]
    assert body["recommendation"]["adapter_version"]


@then(
    "HiveSight can return the full source context, outbound request payload, and inbound response payload for audit"
)
def full_audit_payloads(slice_context: SliceContext) -> None:
    body = slice_context.response.json()
    assert body["context_snapshot"]["context_payload"]
    assert body["request_snapshot"]["request_payload"]
    assert body["recommendation"]["advisor_response_payload"]


@then("HiveSight does not expose those records as Advisor learning, retrieval, or RAG material")
def no_learning_export(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["learning_export_allowed"] is False


@then("HiveSight does not anonymise or export the records in this slice")
def no_anonymised_export(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["anonymised_export_created"] is False
