from collections.abc import Callable
from dataclasses import dataclass
from io import BytesIO
from math import cos, radians, sin, sqrt
from uuid import UUID

from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    AnnotationType,
    HeadUpNormalizedBeeCropPreviewResponse,
    InspectionIntent,
    OrientedBeeEllipseResponse,
    TrainingCropResponse,
    TrainingCropReviewStatus,
    VarroaMarkerResponse,
    VarroaReviewCandidateListResponse,
    VarroaReviewCandidateResponse,
    VarroaReviewOutcomeCreateRequest,
    VarroaReviewOutcomeResponse,
    VarroaReviewOutcomeValue,
    VarroaReviewSummaryResponse,
)

try:
    from PIL import Image
except ImportError:  # pragma: no cover - dependency is declared for the Core API package.
    Image = None


HEAD_UP_NORMALIZED_TRANSFORM_VERSION = "head_up_normalized_bee_crop_v1"
HEAD_UP_NORMALIZED_IMAGE_SIZE_PX = 512
HEAD_UP_NORMALIZED_MARGIN_RATIO = 0.8


@dataclass(frozen=True)
class HeadUpNormalizedCropImage:
    body: bytes
    content_type: str


@dataclass(frozen=True)
class VarroaReviewWorkflow:
    store: InMemoryProductDataStore
    image_loader: Callable[[str], bytes | None]

    def list_candidates(
        self,
        user: UserContext,
        workspace_id: UUID,
        training_crop_id: UUID,
    ) -> VarroaReviewCandidateListResponse:
        crop = self._require_crop_for_varroa_review(
            user=user,
            workspace_id=workspace_id,
            training_crop_id=training_crop_id,
        )
        candidates = [
            self._candidate_for_ellipse(workspace_id=workspace_id, crop=crop, ellipse=ellipse)
            for ellipse in self.store.get_ellipses_for_training_crop(training_crop_id)
        ]
        candidates.sort(key=_candidate_sort_key)
        return VarroaReviewCandidateListResponse(
            workspace_id=workspace_id,
            training_crop_id=training_crop_id,
            candidates=candidates,
            summary=_summary_for_candidates(candidates),
        )

    def get_preview_metadata(
        self,
        user: UserContext,
        workspace_id: UUID,
        training_crop_id: UUID,
        bee_annotation_id: UUID,
    ) -> HeadUpNormalizedBeeCropPreviewResponse:
        crop, ellipse = self._require_eligible_candidate(
            user=user,
            workspace_id=workspace_id,
            training_crop_id=training_crop_id,
            bee_annotation_id=bee_annotation_id,
        )
        return _preview_response(workspace_id=workspace_id, crop=crop, ellipse=ellipse)

    def get_preview_image(
        self,
        user: UserContext,
        workspace_id: UUID,
        training_crop_id: UUID,
        bee_annotation_id: UUID,
    ) -> HeadUpNormalizedCropImage:
        crop, ellipse = self._require_eligible_candidate(
            user=user,
            workspace_id=workspace_id,
            training_crop_id=training_crop_id,
            bee_annotation_id=bee_annotation_id,
        )
        photo = self.store.get_inspection_photo(crop.inspection_photo_id)
        if photo is None or photo.workspace_id != workspace_id:
            raise DomainError(
                "inspection_photo_not_found",
                "The source Inspection Photo for this Training Crop was not found.",
                404,
            )
        body = self.image_loader(photo.original_object_key)
        if body is None:
            raise DomainError(
                "source_image_not_available",
                "The source image bytes for this Head-Up Normalized Bee Crop are not available.",
                404,
            )
        if Image is None:
            raise DomainError(
                "image_processing_unavailable",
                "Image processing is unavailable in this Core API environment.",
                503,
            )

        image = Image.open(BytesIO(body)).convert("RGB")
        bounds = _source_crop_bounds(crop=crop, ellipse=ellipse)
        cropped = image.crop(bounds)
        rotation_applied_degrees = _head_up_rotation_degrees(ellipse.rotation_degrees)
        rotated = cropped.rotate(
            rotation_applied_degrees,
            resample=Image.Resampling.BICUBIC,
            expand=True,
            fillcolor=(255, 255, 255),
        )
        rotated.thumbnail(
            (HEAD_UP_NORMALIZED_IMAGE_SIZE_PX, HEAD_UP_NORMALIZED_IMAGE_SIZE_PX),
            Image.Resampling.LANCZOS,
        )
        canvas = Image.new(
            "RGB",
            (HEAD_UP_NORMALIZED_IMAGE_SIZE_PX, HEAD_UP_NORMALIZED_IMAGE_SIZE_PX),
            (255, 255, 255),
        )
        offset = (
            (HEAD_UP_NORMALIZED_IMAGE_SIZE_PX - rotated.width) // 2,
            (HEAD_UP_NORMALIZED_IMAGE_SIZE_PX - rotated.height) // 2,
        )
        canvas.paste(rotated, offset)
        output = BytesIO()
        canvas.save(output, format="PNG")
        return HeadUpNormalizedCropImage(body=output.getvalue(), content_type="image/png")

    def save_outcome(
        self,
        user: UserContext,
        training_crop_id: UUID,
        bee_annotation_id: UUID,
        request: VarroaReviewOutcomeCreateRequest,
    ) -> VarroaReviewOutcomeResponse:
        crop, ellipse = self._require_eligible_candidate(
            user=user,
            workspace_id=request.workspace_id,
            training_crop_id=training_crop_id,
            bee_annotation_id=bee_annotation_id,
        )
        _validate_outcome_request(request)
        existing = self.store.get_varroa_review_outcome_for_bee(
            workspace_id=request.workspace_id,
            bee_annotation_id=bee_annotation_id,
        )
        now = self.store.clock()
        outcome_id = existing.varroa_review_outcome_id if existing is not None else self.store.id_factory()
        created_at = existing.created_at if existing is not None else now
        created_by = existing.created_by_user_id if existing is not None else user.user_id
        markers = [
            VarroaMarkerResponse(
                varroa_marker_id=self.store.id_factory(),
                varroa_review_outcome_id=outcome_id,
                x=round(marker.x, 4),
                y=round(marker.y, 4),
                created_at=now,
            )
            for marker in request.markers
        ]
        outcome = VarroaReviewOutcomeResponse(
            varroa_review_outcome_id=outcome_id,
            workspace_id=request.workspace_id,
            inspection_photo_id=crop.inspection_photo_id,
            training_crop_id=training_crop_id,
            bee_annotation_id=bee_annotation_id,
            outcome=request.outcome,
            created_by_user_id=created_by,
            created_at=created_at,
            updated_by_user_id=user.user_id,
            updated_at=now,
            notes=_clean_optional_text(request.notes),
            source_context_snapshot=self._source_context_snapshot(crop),
            bee_annotation_geometry_snapshot=_ellipse_snapshot(ellipse),
            training_crop_review_status_snapshot=str(crop.review_status),
            transform_metadata=_transform_metadata(crop=crop, ellipse=ellipse),
            markers=markers,
        )
        return self.store.save_varroa_review_outcome(outcome)

    def _candidate_for_ellipse(
        self,
        workspace_id: UUID,
        crop: TrainingCropResponse,
        ellipse: OrientedBeeEllipseResponse,
    ) -> VarroaReviewCandidateResponse:
        reasons = _ineligibility_reasons(crop=crop, ellipse=ellipse)
        review = self.store.get_varroa_review_outcome_for_bee(
            workspace_id=workspace_id,
            bee_annotation_id=ellipse.annotation_id,
        )
        return VarroaReviewCandidateResponse(
            bee_annotation=ellipse,
            eligibility="eligible" if not reasons else "ineligible",
            ineligibility_reasons=reasons,
            review_outcome=review,
        )

    def _require_eligible_candidate(
        self,
        user: UserContext,
        workspace_id: UUID,
        training_crop_id: UUID,
        bee_annotation_id: UUID,
    ) -> tuple[TrainingCropResponse, OrientedBeeEllipseResponse]:
        crop = self._require_crop_for_varroa_review(
            user=user,
            workspace_id=workspace_id,
            training_crop_id=training_crop_id,
        )
        ellipse = self.store.get_training_crop_ellipse(bee_annotation_id)
        if (
            ellipse is None
            or ellipse.workspace_id != workspace_id
            or ellipse.training_crop_id != training_crop_id
        ):
            raise DomainError(
                "varroa_review_candidate_not_found",
                "The requested bee is not available for Varroa Review.",
                404,
            )
        reasons = _ineligibility_reasons(crop=crop, ellipse=ellipse)
        if reasons:
            code = (
                "training_crop_not_complete_for_varroa_review"
                if "training_crop_not_complete" in reasons
                else "varroa_review_candidate_ineligible"
            )
            raise DomainError(
                code,
                "This bee cannot receive a Varroa Review Outcome in this slice.",
                409,
            )
        return crop, ellipse

    def _require_crop_for_varroa_review(
        self,
        user: UserContext,
        workspace_id: UUID,
        training_crop_id: UUID,
    ) -> TrainingCropResponse:
        crop = self.store.require_training_crop(
            user=user,
            workspace_id=workspace_id,
            training_crop_id=training_crop_id,
        )
        photo = self.store.get_inspection_photo(crop.inspection_photo_id)
        if photo is None:
            raise DomainError(
                "inspection_photo_not_found",
                "The source Inspection Photo for this Training Crop was not found.",
                404,
            )
        inspection = self.store.require_inspection(workspace_id, photo.inspection_id)
        if inspection.intent != InspectionIntent.training_data_collection:
            raise DomainError(
                "inspection_intent_not_for_varroa_review",
                "Varroa Review is available only for Training Data Collection inspections.",
                409,
            )
        return crop

    def _source_context_snapshot(self, crop: TrainingCropResponse) -> dict[str, object]:
        photo = self.store.get_inspection_photo(crop.inspection_photo_id)
        if photo is None:
            return {}
        inspection = self.store.inspections.get(photo.inspection_id)
        hive = self.store.hives.get(inspection.hive_id) if inspection is not None else None
        configuration = (
            self.store.hive_configurations.get(hive.hive_id)
            if hive is not None
            else None
        )
        return {
            "inspection_id": str(inspection.inspection_id) if inspection is not None else None,
            "inspection_date": str(inspection.inspection_date) if inspection is not None else None,
            "inspection_intent": str(inspection.intent) if inspection is not None else None,
            "hive_id": str(hive.hive_id) if hive is not None else None,
            "hive_configuration_frame_standard_id": (
                configuration.frame_standard_id if configuration is not None else None
            ),
        }


def _validate_outcome_request(request: VarroaReviewOutcomeCreateRequest) -> None:
    if any(marker.x < 0 or marker.x > 1 or marker.y < 0 or marker.y > 1 for marker in request.markers):
        raise DomainError(
            "varroa_marker_out_of_bounds",
            "Varroa marker coordinates must be normalized values from 0 to 1.",
            422,
        )
    if request.outcome == VarroaReviewOutcomeValue.visible_varroa_present and not request.markers:
        raise DomainError(
            "visible_varroa_requires_marker",
            "Visible Varroa requires at least one marker.",
            422,
        )
    if request.outcome != VarroaReviewOutcomeValue.visible_varroa_present and request.markers:
        raise DomainError(
            "non_positive_varroa_outcome_requires_no_markers",
            "No-visible-Varroa and not-determined outcomes require zero markers.",
            422,
        )
    if request.outcome == VarroaReviewOutcomeValue.not_determined and not _clean_optional_text(
        request.notes
    ):
        raise DomainError(
            "not_determined_requires_note",
            "Not determined requires a note.",
            422,
        )


def _ineligibility_reasons(
    crop: TrainingCropResponse,
    ellipse: OrientedBeeEllipseResponse,
) -> list[str]:
    reasons: list[str] = []
    if crop.review_status != TrainingCropReviewStatus.review_complete:
        reasons.append("training_crop_not_complete")
    if ellipse.annotation_type != AnnotationType.complete_visible_bee:
        reasons.append("partial_visible_bee")
    if str(ellipse.orientation_reliability) != "reliable":
        reasons.append("unreliable_orientation")
    return reasons


def _candidate_sort_key(candidate: VarroaReviewCandidateResponse) -> tuple[int, str]:
    if candidate.bee_annotation.suspected_visible_varroa:
        bucket = 0
    elif candidate.eligibility == "eligible" and candidate.review_outcome is None:
        bucket = 1
    elif candidate.eligibility == "eligible":
        bucket = 2
    else:
        bucket = 3
    return bucket, str(candidate.bee_annotation.annotation_id)


def _summary_for_candidates(
    candidates: list[VarroaReviewCandidateResponse],
) -> VarroaReviewSummaryResponse:
    outcomes = [candidate.review_outcome for candidate in candidates if candidate.review_outcome]
    return VarroaReviewSummaryResponse(
        eligible_bee_count=sum(1 for candidate in candidates if candidate.eligibility == "eligible"),
        reviewed_bee_count=len(outcomes),
        visible_varroa_bee_count=sum(
            1 for outcome in outcomes if outcome.outcome == VarroaReviewOutcomeValue.visible_varroa_present
        ),
        no_visible_varroa_bee_count=sum(
            1 for outcome in outcomes if outcome.outcome == VarroaReviewOutcomeValue.no_visible_varroa
        ),
        not_determined_bee_count=sum(
            1 for outcome in outcomes if outcome.outcome == VarroaReviewOutcomeValue.not_determined
        ),
        total_marker_count=sum(len(outcome.markers) for outcome in outcomes),
        suspected_visible_varroa_cue_count=sum(
            1 for candidate in candidates if candidate.bee_annotation.suspected_visible_varroa
        ),
        hard_to_assess_cue_count=sum(
            1
            for candidate in candidates
            if str(candidate.bee_annotation.varroa_review_suitability)
            == "body_occluded_or_hard_to_assess"
        ),
        ineligible_deferred_bee_count=sum(
            1 for candidate in candidates if candidate.eligibility != "eligible"
        ),
        caveat="Model-curation summary only; not a Varroa assessment.",
    )


def _preview_response(
    workspace_id: UUID,
    crop: TrainingCropResponse,
    ellipse: OrientedBeeEllipseResponse,
) -> HeadUpNormalizedBeeCropPreviewResponse:
    return HeadUpNormalizedBeeCropPreviewResponse(
        workspace_id=workspace_id,
        inspection_photo_id=crop.inspection_photo_id,
        training_crop_id=crop.training_crop_id,
        bee_annotation_id=ellipse.annotation_id,
        annotation_type=ellipse.annotation_type,
        orientation_reliability=ellipse.orientation_reliability,
        image_width_px=HEAD_UP_NORMALIZED_IMAGE_SIZE_PX,
        image_height_px=HEAD_UP_NORMALIZED_IMAGE_SIZE_PX,
        transform_version=HEAD_UP_NORMALIZED_TRANSFORM_VERSION,
        image_url=(
            f"/v1/training-crops/{crop.training_crop_id}/varroa-review-candidates/"
            f"{ellipse.annotation_id}/head-up-normalized-image?workspace_id={workspace_id}"
        ),
        transform_metadata=_transform_metadata(crop=crop, ellipse=ellipse),
        bee_annotation_geometry_snapshot=_ellipse_snapshot(ellipse),
    )


def _transform_metadata(
    crop: TrainingCropResponse,
    ellipse: OrientedBeeEllipseResponse,
) -> dict[str, object]:
    return {
        "transform_version": HEAD_UP_NORMALIZED_TRANSFORM_VERSION,
        "output_size_px": HEAD_UP_NORMALIZED_IMAGE_SIZE_PX,
        "margin_ratio": HEAD_UP_NORMALIZED_MARGIN_RATIO,
        "rotation_applied_degrees": round(_head_up_rotation_degrees(ellipse.rotation_degrees), 4),
        "source_crop_bounds": list(_source_crop_bounds(crop=crop, ellipse=ellipse)),
        "resize_pad_policy": "fit_with_white_padding",
    }


def _ellipse_snapshot(ellipse: OrientedBeeEllipseResponse) -> dict[str, object]:
    return {
        "annotation_id": str(ellipse.annotation_id),
        "annotation_type": str(ellipse.annotation_type),
        "center_x": ellipse.center_x,
        "center_y": ellipse.center_y,
        "radius_x": ellipse.radius_x,
        "radius_y": ellipse.radius_y,
        "rotation_degrees": ellipse.rotation_degrees,
        "orientation_reliability": str(ellipse.orientation_reliability),
        "coordinate_space": str(ellipse.coordinate_space),
        "source": ellipse.source,
    }


def _source_crop_bounds(
    crop: TrainingCropResponse,
    ellipse: OrientedBeeEllipseResponse,
) -> tuple[int, int, int, int]:
    angle = radians(ellipse.rotation_degrees)
    x_extent = sqrt((ellipse.radius_x * cos(angle)) ** 2 + (ellipse.radius_y * sin(angle)) ** 2)
    y_extent = sqrt((ellipse.radius_x * sin(angle)) ** 2 + (ellipse.radius_y * cos(angle)) ** 2)
    margin = max(x_extent, y_extent) * HEAD_UP_NORMALIZED_MARGIN_RATIO
    left = max(crop.crop_x, int(ellipse.center_x - x_extent - margin))
    top = max(crop.crop_y, int(ellipse.center_y - y_extent - margin))
    right = min(crop.crop_x + crop.crop_width, int(ellipse.center_x + x_extent + margin))
    bottom = min(crop.crop_y + crop.crop_height, int(ellipse.center_y + y_extent + margin))
    if right <= left or bottom <= top:
        raise DomainError(
            "varroa_review_candidate_ineligible",
            "The selected bee cannot be transformed into a Head-Up Normalized Bee Crop.",
            409,
        )
    return left, top, right, bottom


def _head_up_rotation_degrees(rotation_degrees: float) -> float:
    return 90 - rotation_degrees


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
