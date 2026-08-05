import logging
from dataclasses import dataclass
from uuid import UUID

from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    AnnotationType,
    FrameLevelVarroaResultSummaryResponse,
    InspectionIntent,
    OrientationReliability,
    OrientedBeeEllipseResponse,
    TrainingCropResponse,
    TrainingCropReviewStatus,
    VarroaReviewOutcomeResponse,
    VarroaReviewOutcomeValue,
)


PHOTO_VISIBLE_EVIDENCE_SOURCE = "human_reviewed_model_curation"
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class FrameLevelVarroaResultWorkflow:
    store: InMemoryProductDataStore

    def get_photo_visible_summary(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_photo_id: UUID,
    ) -> FrameLevelVarroaResultSummaryResponse:
        self.store.require_workspace_access(user, workspace_id)
        self.store.require_data_use_agreement(workspace_id)
        self.store.require_dataset_curator_capability(user)
        photo = self.store.get_inspection_photo(inspection_photo_id)
        if photo is None or photo.workspace_id != workspace_id:
            raise DomainError(
                "inspection_photo_not_found",
                "The requested Inspection Photo was not found in this Workspace.",
                404,
            )
        inspection = self.store.require_inspection(workspace_id, photo.inspection_id)
        if inspection.intent != InspectionIntent.training_data_collection:
            raise DomainError(
                "inspection_intent_not_for_varroa_evidence_summary",
                "Photo-visible Varroa evidence summaries are available only for Training Data Collection inspections.",
                409,
            )

        crops = self.store.list_training_crops_for_photo_id(
            workspace_id=workspace_id,
            inspection_photo_id=inspection_photo_id,
        )
        completed_crops = [
            crop for crop in crops if crop.review_status == TrainingCropReviewStatus.review_complete
        ]
        unfinished_crop_count = len(crops) - len(completed_crops)
        counts = _SummaryCounts()
        for crop in completed_crops:
            counts.add_crop(
                crop=crop,
                ellipses=self.store.get_ellipses_for_training_crop(crop.training_crop_id),
                outcomes=self.store.list_varroa_review_outcomes_for_training_crop(
                    workspace_id=workspace_id,
                    training_crop_id=crop.training_crop_id,
                ),
            )

        readiness_state = _readiness_state(
            determinate_eligible_bee_count=counts.determinate_eligible_bee_count,
            eligible_complete_bee_count=counts.eligible_complete_bee_count,
        )
        caveats = _caveats(
            readiness_state=readiness_state,
            eligible_complete_bee_count=counts.eligible_complete_bee_count,
            determinate_eligible_bee_count=counts.determinate_eligible_bee_count,
            unfinished_crop_count=unfinished_crop_count,
            unreviewed_eligible_bee_count=counts.unreviewed_eligible_bee_count,
            not_determined_bee_count=counts.not_determined_bee_count,
            ineligible_or_not_assessed_bee_count=counts.ineligible_or_not_assessed_bee_count,
        )
        LOGGER.info(
            "Calculated photo-visible Varroa evidence summary",
            extra={
                "workspace_id": str(workspace_id),
                "inspection_photo_id": str(inspection_photo_id),
                "eligible_complete_bee_count": counts.eligible_complete_bee_count,
                "determinate_varroa_coverage_percent": _percent(
                    counts.determinate_eligible_bee_count,
                    counts.eligible_complete_bee_count,
                ),
                "readiness_state": readiness_state,
            },
        )
        return FrameLevelVarroaResultSummaryResponse(
            workspace_id=workspace_id,
            inspection_id=photo.inspection_id,
            inspection_photo_id=inspection_photo_id,
            source_image_filename=photo.filename,
            source_intent=inspection.intent,
            completed_training_crop_count=len(completed_crops),
            unfinished_training_crop_count=unfinished_crop_count,
            eligible_complete_bee_count=counts.eligible_complete_bee_count,
            reviewed_eligible_bee_count=counts.reviewed_eligible_bee_count,
            determinate_eligible_bee_count=counts.determinate_eligible_bee_count,
            visible_varroa_bee_count=counts.visible_varroa_bee_count,
            active_negative_bee_count=counts.active_negative_bee_count,
            not_determined_bee_count=counts.not_determined_bee_count,
            unreviewed_eligible_bee_count=counts.unreviewed_eligible_bee_count,
            ineligible_or_not_assessed_bee_count=counts.ineligible_or_not_assessed_bee_count,
            visible_mite_marker_count=counts.visible_mite_marker_count,
            review_completion_percent=_percent(
                counts.reviewed_eligible_bee_count,
                counts.eligible_complete_bee_count,
            ),
            determinate_varroa_coverage_percent=_percent(
                counts.determinate_eligible_bee_count,
                counts.eligible_complete_bee_count,
            ),
            evidence_source=PHOTO_VISIBLE_EVIDENCE_SOURCE,
            readiness_state=readiness_state,
            advisor_context_available=counts.determinate_eligible_bee_count > 0,
            caveats=caveats,
        )


@dataclass
class _SummaryCounts:
    eligible_complete_bee_count: int = 0
    reviewed_eligible_bee_count: int = 0
    determinate_eligible_bee_count: int = 0
    visible_varroa_bee_count: int = 0
    active_negative_bee_count: int = 0
    not_determined_bee_count: int = 0
    unreviewed_eligible_bee_count: int = 0
    ineligible_or_not_assessed_bee_count: int = 0
    visible_mite_marker_count: int = 0

    def add_crop(
        self,
        crop: TrainingCropResponse,
        ellipses: list[OrientedBeeEllipseResponse],
        outcomes: list[VarroaReviewOutcomeResponse],
    ) -> None:
        _ = crop
        outcomes_by_bee = {outcome.bee_annotation_id: outcome for outcome in outcomes}
        for ellipse in ellipses:
            if _is_eligible_complete_bee(ellipse):
                self.eligible_complete_bee_count += 1
                outcome = outcomes_by_bee.get(ellipse.annotation_id)
                if outcome is None:
                    self.unreviewed_eligible_bee_count += 1
                    continue
                self.reviewed_eligible_bee_count += 1
                if outcome.outcome == VarroaReviewOutcomeValue.visible_varroa_present:
                    self.visible_varroa_bee_count += 1
                    self.determinate_eligible_bee_count += 1
                    self.visible_mite_marker_count += len(outcome.markers)
                elif outcome.outcome == VarroaReviewOutcomeValue.no_visible_varroa:
                    self.active_negative_bee_count += 1
                    self.determinate_eligible_bee_count += 1
                elif outcome.outcome == VarroaReviewOutcomeValue.not_determined:
                    self.not_determined_bee_count += 1
            else:
                self.ineligible_or_not_assessed_bee_count += 1


def _is_eligible_complete_bee(ellipse: OrientedBeeEllipseResponse) -> bool:
    return (
        getattr(ellipse, "annotation_type") == AnnotationType.complete_visible_bee
        and getattr(ellipse, "orientation_reliability") == OrientationReliability.reliable
    )


def _percent(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def _readiness_state(
    *,
    determinate_eligible_bee_count: int,
    eligible_complete_bee_count: int,
) -> str:
    if determinate_eligible_bee_count == 0:
        return "not_available"
    if determinate_eligible_bee_count == eligible_complete_bee_count:
        return "complete_reviewed_evidence"
    return "partial_evidence"


def _caveats(
    *,
    readiness_state: str,
    eligible_complete_bee_count: int,
    determinate_eligible_bee_count: int,
    unfinished_crop_count: int,
    unreviewed_eligible_bee_count: int,
    not_determined_bee_count: int,
    ineligible_or_not_assessed_bee_count: int,
) -> str:
    caveats = ["Photo-visible evidence only; not treatment advice."]
    if readiness_state == "not_available":
        caveats.append("No determinate eligible bee outcome is available yet.")
    if determinate_eligible_bee_count < eligible_complete_bee_count:
        caveats.append("Determinate Varroa coverage is incomplete.")
    if unfinished_crop_count == 1:
        caveats.append("1 unfinished crop was not included.")
    elif unfinished_crop_count > 1:
        caveats.append(f"{unfinished_crop_count} unfinished crops were not included.")
    if unreviewed_eligible_bee_count > 0:
        caveats.append(f"{unreviewed_eligible_bee_count} eligible bees are not reviewed yet.")
    if not_determined_bee_count > 0:
        caveats.append(f"{not_determined_bee_count} reviewed bees are not determined.")
    if ineligible_or_not_assessed_bee_count > 0:
        caveats.append(
            f"{ineligible_or_not_assessed_bee_count} bees were ineligible or not assessed for Varroa."
        )
    return " ".join(caveats)
