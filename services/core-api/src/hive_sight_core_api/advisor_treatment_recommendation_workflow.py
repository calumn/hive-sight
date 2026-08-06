from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    AdvisorTreatmentAdapterType,
    AdvisorTreatmentCitationResponse,
    AdvisorTreatmentRecommendationCreateRequest,
    AdvisorTreatmentRequestSnapshotResponse,
    AdvisorTreatmentRequestStatus,
    AdvisorVarroaContextResponse,
    AdvisorVarroaContextSnapshotResponse,
    HiveTreatmentCourseListResponse,
    HiveTreatmentCourseResponse,
    TreatmentEvidenceChainDetailResponse,
    TreatmentEvidenceChainListResponse,
    TreatmentEvidenceChainResponse,
    TreatmentEvidenceChainState,
    TreatmentEvidenceChainSummaryResponse,
    TreatmentRecommendationListResponse,
    TreatmentRecommendationResponse,
    TreatmentRecommendationStatus,
)

ADVISOR_TREATMENT_REQUEST_CONTRACT_VERSION = "hivesight_advisor_treatment_plan_request_v1"
ADVISOR_TREATMENT_RESPONSE_CONTRACT_VERSION = "treatment_plan_v1"
STUB_ADAPTER_VERSION = "deterministic_stub_v1"


class AdvisorContextBuilder(Protocol):
    def assemble_context(
        self,
        user: UserContext,
        hive_id: UUID,
        inspection_photo_id: UUID,
        jurisdiction_id: str | None,
    ) -> AdvisorVarroaContextResponse:
        ...


@dataclass(frozen=True)
class AdvisorTreatmentPlanResponse:
    text: str
    grounding_status: str
    citations: list[AdvisorTreatmentCitationResponse]
    raw_payload: dict[str, object]
    contract_version: str | None = None
    answer_id: str | None = None


class AdvisorTreatmentPlanAdapter(Protocol):
    adapter_type: AdvisorTreatmentAdapterType
    adapter_version: str

    def request_treatment_plan(
        self,
        *,
        hive_id: UUID,
        jurisdiction_code: str,
        situational_context: str,
    ) -> AdvisorTreatmentPlanResponse:
        ...


@dataclass(frozen=True)
class DeterministicStubAdvisorTreatmentPlanAdapter:
    adapter_type: AdvisorTreatmentAdapterType = AdvisorTreatmentAdapterType.deterministic_stub
    adapter_version: str = STUB_ADAPTER_VERSION

    def request_treatment_plan(
        self,
        *,
        hive_id: UUID,
        jurisdiction_code: str,
        situational_context: str,
    ) -> AdvisorTreatmentPlanResponse:
        citation = AdvisorTreatmentCitationResponse(
            passage_id="stub-passage-varroa-integrated-pest-management",
            document_title="HiveSight Advisor deterministic treatment-plan stub",
            document_source="hivesight-advisor-stub",
            document_source_url=None,
            document_licence_terms="internal-test-only",
            is_superseded=False,
        )
        text = (
            "Deterministic stub suggestion: review current authorised Varroa treatment "
            f"guidance for jurisdiction {jurisdiction_code} before planning treatment."
        )
        payload = {
            "contract_version": ADVISOR_TREATMENT_RESPONSE_CONTRACT_VERSION,
            "answer_id": f"stub-answer-{hive_id}",
            "text": text,
            "grounding_status": "grounded",
            "citations": [citation.model_dump(mode="json")],
            "situational_context_excerpt": situational_context[:240],
        }
        return AdvisorTreatmentPlanResponse(
            text=text,
            grounding_status="grounded",
            citations=[citation],
            raw_payload=payload,
            contract_version=ADVISOR_TREATMENT_RESPONSE_CONTRACT_VERSION,
            answer_id=f"stub-answer-{hive_id}",
        )


@dataclass(frozen=True)
class FailingAdvisorTreatmentPlanAdapter:
    adapter_type: AdvisorTreatmentAdapterType = AdvisorTreatmentAdapterType.hivesight_advisor
    adapter_version: str = "failing_test_adapter_v1"

    def request_treatment_plan(
        self,
        *,
        hive_id: UUID,
        jurisdiction_code: str,
        situational_context: str,
    ) -> AdvisorTreatmentPlanResponse:
        raise AdvisorTreatmentPlanAdapterError("Advisor did not return usable treatment advice.")


class AdvisorTreatmentPlanAdapterError(RuntimeError):
    pass


@dataclass(frozen=True)
class AdvisorTreatmentRecommendationWorkflow:
    store: InMemoryProductDataStore
    context_builder: AdvisorContextBuilder
    adapter: AdvisorTreatmentPlanAdapter
    allow_stub_adapter_for_product_data: bool = True

    def request_treatment_advice(
        self,
        user: UserContext,
        hive_id: UUID,
        request: AdvisorTreatmentRecommendationCreateRequest,
    ) -> TreatmentEvidenceChainDetailResponse:
        self._require_hive_access(user=user, hive_id=hive_id)
        open_course = self._open_planned_varroa_course(hive_id=hive_id)
        if open_course is not None:
            raise DomainError(
                "open_planned_varroa_treatment_course_exists",
                "An open planned Varroa treatment course already exists for this Hive.",
                409,
            )
        pending = self._pending_recommendation_for_hive(hive_id=hive_id)
        if pending is not None:
            return self.get_treatment_evidence_chain(
                user=user,
                treatment_evidence_chain_id=pending.treatment_evidence_chain_id,
            )
        if (
            self.adapter.adapter_type == AdvisorTreatmentAdapterType.deterministic_stub
            and not self.allow_stub_adapter_for_product_data
        ):
            raise DomainError(
                "stub_advisor_treatment_adapter_not_allowed",
                "The deterministic Advisor treatment adapter cannot create product treatment advice.",
                409,
            )

        context = self.context_builder.assemble_context(
            user=user,
            hive_id=hive_id,
            inspection_photo_id=request.inspection_photo_id,
            jurisdiction_id=request.jurisdiction_code,
        )
        chain = self._create_chain(
            context=context,
            user=user,
            state=TreatmentEvidenceChainState.recommendation_pending,
        )
        context_snapshot = self._create_context_snapshot(context=context, user=user, chain=chain)
        if not context.advisor_request_readiness.can_request_advice:
            blocked_chain = chain.model_copy(
                update={
                    "state": TreatmentEvidenceChainState.blocked_not_ready,
                    "blocked_reasons": context.advisor_request_readiness.blocking_reasons,
                    "updated_at": self.store.clock(),
                }
            )
            self.store.save_treatment_evidence_chain(blocked_chain)
            return TreatmentEvidenceChainDetailResponse(
                chain=blocked_chain,
                context_snapshot=context_snapshot,
            )

        situational_context = _situational_context_from_advisor_varroa_context(context)
        request_payload = {
            "hive_id": str(hive_id),
            "jurisdiction_code": request.jurisdiction_code,
            "situational_context": situational_context,
        }
        request_snapshot_id = self.store.id_factory()
        try:
            advisor_response = self.adapter.request_treatment_plan(
                hive_id=hive_id,
                jurisdiction_code=request.jurisdiction_code,
                situational_context=situational_context,
            )
        except AdvisorTreatmentPlanAdapterError as exc:
            failed_snapshot = AdvisorTreatmentRequestSnapshotResponse(
                advisor_treatment_request_snapshot_id=request_snapshot_id,
                treatment_evidence_chain_id=chain.treatment_evidence_chain_id,
                workspace_id=context.workspace_id,
                apiary_id=context.apiary_id,
                hive_id=context.hive_id,
                inspection_id=context.inspection_id,
                inspection_photo_id=context.inspection_photo_id,
                advisor_context_contract_version=context.contract_version,
                advisor_request_contract_version=ADVISOR_TREATMENT_REQUEST_CONTRACT_VERSION,
                jurisdiction_code=request.jurisdiction_code,
                situational_context=situational_context,
                request_payload=request_payload,
                request_status=AdvisorTreatmentRequestStatus.failed,
                error_summary=str(exc),
                adapter_type=self.adapter.adapter_type,
                adapter_version=self.adapter.adapter_version,
                created_by_user_id=user.user_id,
                created_at=self.store.clock(),
            )
            self.store.save_advisor_treatment_request_snapshot(failed_snapshot)
            failed_chain = chain.model_copy(
                update={
                    "state": TreatmentEvidenceChainState.advisor_request_failed,
                    "updated_at": self.store.clock(),
                }
            )
            self.store.save_treatment_evidence_chain(failed_chain)
            return TreatmentEvidenceChainDetailResponse(
                chain=failed_chain,
                context_snapshot=context_snapshot,
                request_snapshot=failed_snapshot,
            )

        request_snapshot = AdvisorTreatmentRequestSnapshotResponse(
            advisor_treatment_request_snapshot_id=request_snapshot_id,
            treatment_evidence_chain_id=chain.treatment_evidence_chain_id,
            workspace_id=context.workspace_id,
            apiary_id=context.apiary_id,
            hive_id=context.hive_id,
            inspection_id=context.inspection_id,
            inspection_photo_id=context.inspection_photo_id,
            advisor_context_contract_version=context.contract_version,
            advisor_request_contract_version=ADVISOR_TREATMENT_REQUEST_CONTRACT_VERSION,
            jurisdiction_code=request.jurisdiction_code,
            situational_context=situational_context,
            request_payload=request_payload,
            request_status=AdvisorTreatmentRequestStatus.sent,
            adapter_type=self.adapter.adapter_type,
            adapter_version=self.adapter.adapter_version,
            created_by_user_id=user.user_id,
            created_at=self.store.clock(),
        )
        self.store.save_advisor_treatment_request_snapshot(request_snapshot)
        recommendation = TreatmentRecommendationResponse(
            treatment_recommendation_id=self.store.id_factory(),
            treatment_evidence_chain_id=chain.treatment_evidence_chain_id,
            advisor_treatment_request_snapshot_id=request_snapshot.advisor_treatment_request_snapshot_id,
            workspace_id=context.workspace_id,
            apiary_id=context.apiary_id,
            hive_id=context.hive_id,
            status=TreatmentRecommendationStatus.pending,
            advisor_response_payload=advisor_response.raw_payload,
            recommendation_text=advisor_response.text,
            grounding_status=advisor_response.grounding_status,
            citations=advisor_response.citations,
            advisor_answer_id=advisor_response.answer_id,
            adapter_type=self.adapter.adapter_type,
            adapter_version=self.adapter.adapter_version,
            advisor_response_contract_version=advisor_response.contract_version,
            response_received_at=self.store.clock(),
        )
        self.store.save_treatment_recommendation(recommendation)
        self.store.save_treatment_evidence_chain(chain)
        return TreatmentEvidenceChainDetailResponse(
            chain=chain,
            context_snapshot=context_snapshot,
            request_snapshot=request_snapshot,
            recommendation=recommendation,
        )

    def accept_recommendation(
        self,
        user: UserContext,
        treatment_recommendation_id: UUID,
        note: str | None,
    ) -> HiveTreatmentCourseResponse:
        recommendation = self._require_recommendation_access(user, treatment_recommendation_id)
        if recommendation.status == TreatmentRecommendationStatus.accepted:
            existing_course = self._course_for_recommendation(treatment_recommendation_id)
            if existing_course is None:
                raise DomainError(
                    "accepted_treatment_course_missing",
                    "The accepted Treatment Recommendation has no planned course.",
                    500,
                )
            return existing_course
        if recommendation.status == TreatmentRecommendationStatus.declined:
            raise DomainError(
                "treatment_recommendation_already_declined",
                "A declined Treatment Recommendation cannot be accepted in this slice.",
                409,
            )
        now = self.store.clock()
        accepted = recommendation.model_copy(
            update={
                "status": TreatmentRecommendationStatus.accepted,
                "decision_by_user_id": user.user_id,
                "decision_at": now,
                "decision_note": note,
            }
        )
        self.store.save_treatment_recommendation(accepted)
        chain = self.store.treatment_evidence_chains[accepted.treatment_evidence_chain_id]
        self.store.save_treatment_evidence_chain(
            chain.model_copy(
                update={
                    "state": TreatmentEvidenceChainState.recommendation_accepted,
                    "updated_at": now,
                }
            )
        )
        course = HiveTreatmentCourseResponse(
            hive_treatment_course_id=self.store.id_factory(),
            treatment_evidence_chain_id=accepted.treatment_evidence_chain_id,
            source_treatment_recommendation_id=accepted.treatment_recommendation_id,
            workspace_id=accepted.workspace_id,
            apiary_id=accepted.apiary_id,
            hive_id=accepted.hive_id,
            planned_course_snapshot={
                "recommendation_text": accepted.recommendation_text,
                "grounding_status": accepted.grounding_status,
                "citations": [citation.model_dump(mode="json") for citation in accepted.citations],
                "advisor_answer_id": accepted.advisor_answer_id,
            },
            accepted_by_user_id=user.user_id,
            accepted_at=now,
            acceptance_note=note,
            created_by_user_id=user.user_id,
            created_at=now,
        )
        return self.store.save_hive_treatment_course(course)

    def decline_recommendation(
        self,
        user: UserContext,
        treatment_recommendation_id: UUID,
        note: str | None,
    ) -> TreatmentRecommendationResponse:
        recommendation = self._require_recommendation_access(user, treatment_recommendation_id)
        if recommendation.status == TreatmentRecommendationStatus.declined:
            return recommendation
        if recommendation.status == TreatmentRecommendationStatus.accepted:
            raise DomainError(
                "accepted_treatment_recommendation_cannot_be_declined",
                "An accepted Treatment Recommendation cannot be declined in this slice.",
                409,
            )
        now = self.store.clock()
        declined = recommendation.model_copy(
            update={
                "status": TreatmentRecommendationStatus.declined,
                "decision_by_user_id": user.user_id,
                "decision_at": now,
                "decision_note": note,
            }
        )
        self.store.save_treatment_recommendation(declined)
        chain = self.store.treatment_evidence_chains[declined.treatment_evidence_chain_id]
        self.store.save_treatment_evidence_chain(
            chain.model_copy(
                update={
                    "state": TreatmentEvidenceChainState.recommendation_declined,
                    "updated_at": now,
                }
            )
        )
        return declined

    def list_treatment_recommendations(
        self,
        user: UserContext,
        hive_id: UUID,
    ) -> TreatmentRecommendationListResponse:
        self._require_hive_access(user=user, hive_id=hive_id)
        recommendations = [
            recommendation
            for recommendation in self.store.treatment_recommendations.values()
            if recommendation.hive_id == hive_id
        ]
        recommendations.sort(key=lambda recommendation: recommendation.response_received_at)
        return TreatmentRecommendationListResponse(treatment_recommendations=recommendations)

    def list_treatment_courses(
        self,
        user: UserContext,
        hive_id: UUID,
    ) -> HiveTreatmentCourseListResponse:
        self._require_hive_access(user=user, hive_id=hive_id)
        courses = [
            course for course in self.store.hive_treatment_courses.values() if course.hive_id == hive_id
        ]
        courses.sort(key=lambda course: course.created_at)
        return HiveTreatmentCourseListResponse(treatment_courses=courses)

    def list_advice_attempts(
        self,
        user: UserContext,
        hive_id: UUID,
    ) -> TreatmentEvidenceChainListResponse:
        self._require_hive_access(user=user, hive_id=hive_id)
        chains = [
            self._chain_summary(chain)
            for chain in self.store.treatment_evidence_chains.values()
            if chain.hive_id == hive_id
        ]
        chains.sort(key=lambda chain: chain.created_at)
        return TreatmentEvidenceChainListResponse(treatment_evidence_chains=chains)

    def get_treatment_evidence_chain(
        self,
        user: UserContext,
        treatment_evidence_chain_id: UUID,
    ) -> TreatmentEvidenceChainDetailResponse:
        chain = self.store.treatment_evidence_chains.get(treatment_evidence_chain_id)
        if chain is None:
            raise DomainError(
                "treatment_evidence_chain_not_found",
                "The requested Treatment Evidence Chain was not found.",
                404,
            )
        self.store.require_workspace_access(user, chain.workspace_id)
        recommendation = next(
            (
                item
                for item in self.store.treatment_recommendations.values()
                if item.treatment_evidence_chain_id == treatment_evidence_chain_id
            ),
            None,
        )
        course = next(
            (
                item
                for item in self.store.hive_treatment_courses.values()
                if item.treatment_evidence_chain_id == treatment_evidence_chain_id
            ),
            None,
        )
        context_snapshot = next(
            (
                item
                for item in self.store.advisor_varroa_context_snapshots.values()
                if item.treatment_evidence_chain_id == treatment_evidence_chain_id
            ),
            None,
        )
        request_snapshot = next(
            (
                item
                for item in self.store.advisor_treatment_request_snapshots.values()
                if item.treatment_evidence_chain_id == treatment_evidence_chain_id
            ),
            None,
        )
        return TreatmentEvidenceChainDetailResponse(
            chain=chain,
            context_snapshot=context_snapshot,
            request_snapshot=request_snapshot,
            recommendation=recommendation,
            treatment_course=course,
        )

    def _require_hive_access(self, user: UserContext, hive_id: UUID):
        hive = self.store.get_hive(hive_id)
        if hive is None:
            raise DomainError("hive_not_found", "The requested Hive was not found.", 404)
        self.store.require_workspace_access(user, hive.workspace_id)
        self.store.require_data_use_agreement(hive.workspace_id)
        return hive

    def _require_recommendation_access(
        self,
        user: UserContext,
        treatment_recommendation_id: UUID,
    ) -> TreatmentRecommendationResponse:
        recommendation = self.store.treatment_recommendations.get(treatment_recommendation_id)
        if recommendation is None:
            raise DomainError(
                "treatment_recommendation_not_found",
                "The requested Treatment Recommendation was not found.",
                404,
            )
        self.store.require_workspace_access(user, recommendation.workspace_id)
        self.store.require_data_use_agreement(recommendation.workspace_id)
        return recommendation

    def _pending_recommendation_for_hive(
        self,
        hive_id: UUID,
    ) -> TreatmentRecommendationResponse | None:
        return next(
            (
                recommendation
                for recommendation in self.store.treatment_recommendations.values()
                if recommendation.hive_id == hive_id
                and recommendation.concern == "varroa"
                and recommendation.status == TreatmentRecommendationStatus.pending
            ),
            None,
        )

    def _open_planned_varroa_course(self, hive_id: UUID) -> HiveTreatmentCourseResponse | None:
        return next(
            (
                course
                for course in self.store.hive_treatment_courses.values()
                if course.hive_id == hive_id
                and course.purpose == "varroa"
                and course.status == "planned"
            ),
            None,
        )

    def _course_for_recommendation(
        self,
        treatment_recommendation_id: UUID,
    ) -> HiveTreatmentCourseResponse | None:
        return next(
            (
                course
                for course in self.store.hive_treatment_courses.values()
                if course.source_treatment_recommendation_id == treatment_recommendation_id
            ),
            None,
        )

    def _create_chain(
        self,
        *,
        context: AdvisorVarroaContextResponse,
        user: UserContext,
        state: TreatmentEvidenceChainState,
    ) -> TreatmentEvidenceChainResponse:
        now = self.store.clock()
        chain = TreatmentEvidenceChainResponse(
            treatment_evidence_chain_id=self.store.id_factory(),
            workspace_id=context.workspace_id,
            apiary_id=context.apiary_id,
            hive_id=context.hive_id,
            inspection_id=context.inspection_id,
            inspection_photo_id=context.inspection_photo_id,
            state=state,
            created_by_user_id=user.user_id,
            created_at=now,
            updated_at=now,
        )
        return self.store.save_treatment_evidence_chain(chain)

    def _create_context_snapshot(
        self,
        *,
        context: AdvisorVarroaContextResponse,
        user: UserContext,
        chain: TreatmentEvidenceChainResponse,
    ) -> AdvisorVarroaContextSnapshotResponse:
        snapshot = AdvisorVarroaContextSnapshotResponse(
            advisor_varroa_context_snapshot_id=self.store.id_factory(),
            treatment_evidence_chain_id=chain.treatment_evidence_chain_id,
            workspace_id=context.workspace_id,
            apiary_id=context.apiary_id,
            hive_id=context.hive_id,
            inspection_id=context.inspection_id,
            inspection_photo_id=context.inspection_photo_id,
            advisor_context_contract_version=context.contract_version,
            context_payload=context.model_dump(mode="json"),
            context_summary=_context_summary(context),
            created_by_user_id=user.user_id,
            created_at=self.store.clock(),
        )
        return self.store.save_advisor_varroa_context_snapshot(snapshot)

    def _chain_summary(
        self,
        chain: TreatmentEvidenceChainResponse,
    ) -> TreatmentEvidenceChainSummaryResponse:
        recommendation = next(
            (
                item
                for item in self.store.treatment_recommendations.values()
                if item.treatment_evidence_chain_id == chain.treatment_evidence_chain_id
            ),
            None,
        )
        course = next(
            (
                item
                for item in self.store.hive_treatment_courses.values()
                if item.treatment_evidence_chain_id == chain.treatment_evidence_chain_id
            ),
            None,
        )
        return TreatmentEvidenceChainSummaryResponse(
            treatment_evidence_chain_id=chain.treatment_evidence_chain_id,
            hive_id=chain.hive_id,
            inspection_photo_id=chain.inspection_photo_id,
            state=chain.state,
            blocked_reasons=chain.blocked_reasons,
            treatment_recommendation_id=(
                recommendation.treatment_recommendation_id if recommendation is not None else None
            ),
            hive_treatment_course_id=(
                course.hive_treatment_course_id if course is not None else None
            ),
            created_at=chain.created_at,
            updated_at=chain.updated_at,
        )


def _context_summary(context: AdvisorVarroaContextResponse) -> dict[str, object]:
    frame_count = context.varroa_evidence.frame_mite_count
    photo_evidence = context.varroa_evidence.photo_visible_varroa_evidence
    return {
        "status": context.status,
        "contract_version": context.contract_version,
        "source_intent": context.varroa_evidence.source_intent,
        "evidence_readiness": context.varroa_evidence.evidence_readiness,
        "processed_bee_count": frame_count.processed_bee_count,
        "likely_visible_varroa_detection_count": (
            frame_count.likely_visible_varroa_detection_count
        ),
        "visible_varroa_bee_count": photo_evidence.visible_varroa_bee_count,
        "visible_mite_marker_count": photo_evidence.visible_mite_marker_count,
        "can_request_advice": context.advisor_request_readiness.can_request_advice,
        "blocking_reasons": context.advisor_request_readiness.blocking_reasons,
    }


def _situational_context_from_advisor_varroa_context(
    context: AdvisorVarroaContextResponse,
) -> str:
    summary = _context_summary(context)
    return (
        "HiveSight Varroa evidence context. "
        f"Inspection date: {context.inspection_date}. "
        f"Source intent: {summary['source_intent']}. "
        f"Processed bees: {summary['processed_bee_count']}. "
        "Likely visible Varroa detections: "
        f"{summary['likely_visible_varroa_detection_count']}. "
        f"Human visible Varroa bee count: {summary['visible_varroa_bee_count']}. "
        f"Human visible mite marker count: {summary['visible_mite_marker_count']}. "
        "Use this as evidence context for a suggested treatment plan only."
    )
