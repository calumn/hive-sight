import logging
from dataclasses import dataclass
from uuid import UUID

from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.frame_level_varroa_result_workflow import FrameLevelVarroaResultWorkflow
from hive_sight_core_api.models import (
    AdvisorRequestReadiness,
    AdvisorRequiredSituationalInputsContext,
    AdvisorTreatmentHistoryContext,
    AdvisorVarroaContextResponse,
    AdvisorVarroaContextStatus,
    AdvisorVarroaEvidence,
    AdvisorVarroaFrameMiteCountEvidence,
    AdvisorVarroaPhotoVisibleEvidence,
    FrameLevelVarroaResultSummaryResponse,
    FrameMiteCountResponse,
    FrameMiteCountStatus,
    InspectionIntent,
)
from hive_sight_core_api.varroa_review_workflow import VarroaReviewWorkflow

CONTRACT_VERSION = "advisor_varroa_context_v1"
EVIDENCE_READINESS_INTEGRATION_TEST_ONLY = "integration_test_only"
NOT_ADVICE_REASON = (
    "HiveSight Advisor Varroa context is evidence only; not treatment advice and not a "
    "beekeeper-facing Varroa Assessment."
)
SITUATIONAL_INPUTS_NOT_MODELLED = [
    "brood_presence",
    "honey_super_status",
    "ambient_temperature",
    "organic_certification_status",
]
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class AdvisorVarroaContextWorkflow:
    store: InMemoryProductDataStore
    varroa_review_workflow: VarroaReviewWorkflow
    frame_level_varroa_result_workflow: FrameLevelVarroaResultWorkflow

    def assemble_context(
        self,
        user: UserContext,
        hive_id: UUID,
        inspection_photo_id: UUID,
        jurisdiction_id: str | None,
    ) -> AdvisorVarroaContextResponse:
        hive = self.store.get_hive(hive_id)
        if hive is None:
            raise DomainError("hive_not_found", "The requested Hive was not found.", 404)
        self.store.require_workspace_access(user, hive.workspace_id)
        self.store.require_data_use_agreement(hive.workspace_id)
        self.store.require_dataset_curator_capability(user)

        photo = self.store.get_inspection_photo(inspection_photo_id)
        if photo is None or photo.workspace_id != hive.workspace_id:
            raise DomainError(
                "inspection_photo_not_found",
                "The requested Inspection Photo was not found in this Workspace.",
                404,
            )
        inspection = self.store.require_inspection(hive.workspace_id, photo.inspection_id)
        if inspection.hive_id != hive_id:
            raise DomainError(
                "photo_hive_mismatch",
                "The selected Inspection Photo does not belong to the requested Hive.",
                409,
            )

        frame_count = self.varroa_review_workflow.count_frame_mites(
            user=user,
            workspace_id=hive.workspace_id,
            inspection_photo_id=inspection_photo_id,
        )
        photo_visible_evidence = (
            self.frame_level_varroa_result_workflow.get_photo_visible_summary(
                user=user,
                workspace_id=hive.workspace_id,
                inspection_photo_id=inspection_photo_id,
            )
        )
        status = (
            AdvisorVarroaContextStatus.not_available
            if frame_count.status == FrameMiteCountStatus.not_available
            else AdvisorVarroaContextStatus.available
        )
        readiness = _advisor_request_readiness(
            jurisdiction_id=jurisdiction_id,
            source_intent=inspection.intent,
            frame_count_status=frame_count.status,
            frame_count_caveat=frame_count.caveat,
            photo_visible_caveat=photo_visible_evidence.caveats,
        )
        response = AdvisorVarroaContextResponse(
            contract_version=CONTRACT_VERSION,
            status=status,
            workspace_id=hive.workspace_id,
            hive_id=hive.hive_id,
            apiary_id=hive.apiary_id,
            inspection_id=inspection.inspection_id,
            inspection_photo_id=inspection_photo_id,
            inspection_date=inspection.inspection_date,
            jurisdiction_id=jurisdiction_id,
            varroa_evidence=AdvisorVarroaEvidence(
                source_intent=inspection.intent,
                evidence_readiness=EVIDENCE_READINESS_INTEGRATION_TEST_ONLY,
                frame_mite_count=_frame_mite_count_evidence(frame_count),
                photo_visible_varroa_evidence=_photo_visible_evidence(photo_visible_evidence),
            ),
            treatment_history=AdvisorTreatmentHistoryContext(),
            advisor_required_situational_inputs=AdvisorRequiredSituationalInputsContext(
                missing_inputs=SITUATIONAL_INPUTS_NOT_MODELLED,
            ),
            advisor_request_readiness=readiness,
            not_advice_reason=NOT_ADVICE_REASON,
        )
        LOGGER.info(
            "Assembled Advisor Varroa context",
            extra={
                "workspace_id": str(response.workspace_id),
                "hive_id": str(response.hive_id),
                "inspection_photo_id": str(response.inspection_photo_id),
                "availability": response.status,
                "frame_count_status": frame_count.status,
                "processed_bee_count": frame_count.processed_bee_count,
                "likely_visible_varroa_detection_count": (
                    frame_count.likely_visible_varroa_detection_count
                ),
                "not_treatment_advice": True,
            },
        )
        return response


def _frame_mite_count_evidence(
    frame_count: FrameMiteCountResponse,
) -> AdvisorVarroaFrameMiteCountEvidence:
    return AdvisorVarroaFrameMiteCountEvidence(
        status=frame_count.status,
        eligible_bee_count=frame_count.eligible_bee_count,
        processed_bee_count=frame_count.processed_bee_count,
        bees_with_likely_varroa_count=frame_count.bees_with_likely_varroa_count,
        likely_visible_varroa_detection_count=frame_count.likely_visible_varroa_detection_count,
        model_determinate_coverage_percent=frame_count.model_determinate_coverage_percent,
        completed_training_crop_count=frame_count.completed_training_crop_count,
        unfinished_training_crop_count=frame_count.unfinished_training_crop_count,
        excluded_training_crop_count=frame_count.excluded_training_crop_count,
        not_assessed_bee_count=frame_count.not_assessed_bee_count,
        failed_bee_count=frame_count.failed_bee_count,
        not_assessed_reasons=frame_count.not_assessed_reasons,
        failure_reasons=frame_count.failure_reasons,
        adapter_type=frame_count.adapter_type,
        adapter_version=frame_count.adapter_version,
        model_reference=frame_count.model_reference,
        caveats=frame_count.caveat,
    )


def _photo_visible_evidence(
    summary: FrameLevelVarroaResultSummaryResponse,
) -> AdvisorVarroaPhotoVisibleEvidence:
    return AdvisorVarroaPhotoVisibleEvidence(
        readiness_state=summary.readiness_state,
        eligible_complete_bee_count=summary.eligible_complete_bee_count,
        reviewed_eligible_bee_count=summary.reviewed_eligible_bee_count,
        determinate_eligible_bee_count=summary.determinate_eligible_bee_count,
        visible_varroa_bee_count=summary.visible_varroa_bee_count,
        visible_mite_marker_count=summary.visible_mite_marker_count,
        active_negative_bee_count=summary.active_negative_bee_count,
        not_determined_bee_count=summary.not_determined_bee_count,
        review_completion_percent=summary.review_completion_percent,
        determinate_varroa_coverage_percent=summary.determinate_varroa_coverage_percent,
        caveats=summary.caveats,
    )


def _advisor_request_readiness(
    *,
    jurisdiction_id: str | None,
    source_intent: InspectionIntent,
    frame_count_status: FrameMiteCountStatus,
    frame_count_caveat: str,
    photo_visible_caveat: str,
) -> AdvisorRequestReadiness:
    blocking_reasons: list[str] = []
    if jurisdiction_id is None:
        blocking_reasons.append("jurisdiction_not_provided")
    if source_intent != InspectionIntent.varroa_assessment:
        blocking_reasons.append("source_intent_not_varroa_assessment")
    if frame_count_status == FrameMiteCountStatus.not_available:
        blocking_reasons.append("frame_mite_count_not_available")
    blocking_reasons.extend(
        [
            "treatment_history_not_modelled",
            "advisor_required_situational_inputs_not_modelled",
        ]
    )
    return AdvisorRequestReadiness(
        can_request_advice=False,
        blocking_reasons=blocking_reasons,
        caveats=[
            "Training Data Collection evidence is integration-test context only.",
            frame_count_caveat,
            photo_visible_caveat,
            "Hive Treatment History is not modelled yet.",
            "Advisor-required situational inputs are not modelled yet.",
        ],
    )
