import logging
from collections.abc import Callable
from dataclasses import dataclass
from io import BytesIO
from math import cos, radians, sin, sqrt
from time import perf_counter
from typing import Protocol
from uuid import UUID

from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    AnnotationType,
    FrameMiteCountBeeResultResponse,
    FrameMiteCountBeeStatus,
    FrameMiteCountResponse,
    FrameMiteCountStatus,
    HeadUpNormalizedBeeCropPreviewResponse,
    InspectionIntent,
    LikelyVarroaDetectionResponse,
    OrientedBeeEllipseResponse,
    TrainingCropResponse,
    TrainingCropReviewStatus,
    VarroaDetectorCoordinateSpace,
    VarroaDetectorPreviewResponse,
    VarroaDetectorPreviewStatus,
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
VARROA_DETECTOR_STUB_VERSION = "deterministic_stub_varroa_detector_v1"
VARROA_DETECTOR_STUB_CAVEAT = (
    "Deterministic stub preview only; not user-facing and not eligible for promotion."
)
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class HeadUpNormalizedCropImage:
    body: bytes
    content_type: str


@dataclass(frozen=True)
class VarroaDetectorRequest:
    workspace_id: UUID
    inspection_photo_id: UUID
    training_crop_id: UUID
    bee_annotation_id: UUID
    head_up_normalized_image_bytes: bytes
    image_width_px: int
    image_height_px: int
    transform_version: str
    transform_metadata: dict[str, object]
    source_geometry_snapshot: dict[str, object]


class VarroaDetectorFailure(Exception):
    def __init__(self, code: str, message: str, raw_error_payload: str | None = None) -> None:
        self.code = code
        self.message = message
        self.raw_error_payload = raw_error_payload
        super().__init__(message)


class VarroaDetectorAdapter(Protocol):
    adapter_type: str
    adapter_version: str
    model_reference: str

    def detect(self, request: VarroaDetectorRequest) -> list[LikelyVarroaDetectionResponse]:
        """Return likely visible Varroa mite detections for one Head-Up crop."""


@dataclass(frozen=True)
class DeterministicStubVarroaDetectorAdapter:
    adapter_type: str = "deterministic_stub"
    adapter_version: str = VARROA_DETECTOR_STUB_VERSION
    model_reference: str = VARROA_DETECTOR_STUB_VERSION

    def detect(self, request: VarroaDetectorRequest) -> list[LikelyVarroaDetectionResponse]:
        return [
            LikelyVarroaDetectionResponse(
                detection_id="deterministic-stub-detection-1",
                x=0.52,
                y=0.34,
                width=0.08,
                height=0.06,
                confidence=0.73,
                coordinate_space=VarroaDetectorCoordinateSpace.head_up_normalized_crop,
                source="deterministic_stub",
            )
        ]


@dataclass(frozen=True)
class VarroaReviewWorkflow:
    store: InMemoryProductDataStore
    image_loader: Callable[[str], bytes | None]
    varroa_detector_adapter: VarroaDetectorAdapter = DeterministicStubVarroaDetectorAdapter()

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
        return self._build_head_up_normalized_crop_image(workspace_id=workspace_id, crop=crop, ellipse=ellipse)

    def preview_varroa_detections(
        self,
        user: UserContext,
        workspace_id: UUID,
        training_crop_id: UUID,
        bee_annotation_id: UUID,
    ) -> VarroaDetectorPreviewResponse:
        started = perf_counter()
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
                "The requested bee is not available for Varroa Detection preview.",
                404,
            )

        reasons = _ineligibility_reasons(crop=crop, ellipse=ellipse)
        if reasons:
            return self._not_assessed_preview_response(
                workspace_id=workspace_id,
                crop=crop,
                ellipse=ellipse,
                reason=", ".join(reasons),
                elapsed_ms=_elapsed_ms(started),
            )

        head_up_crop = _preview_response(workspace_id=workspace_id, crop=crop, ellipse=ellipse)
        try:
            image = self._build_head_up_normalized_crop_image(
                workspace_id=workspace_id,
                crop=crop,
                ellipse=ellipse,
            )
        except DomainError as error:
            if error.code in {
                "source_image_not_available",
                "image_processing_unavailable",
                "varroa_review_candidate_ineligible",
            }:
                return self._not_assessed_preview_response(
                    workspace_id=workspace_id,
                    crop=crop,
                    ellipse=ellipse,
                    reason=error.code,
                    elapsed_ms=_elapsed_ms(started),
                )
            raise

        request = VarroaDetectorRequest(
            workspace_id=workspace_id,
            inspection_photo_id=crop.inspection_photo_id,
            training_crop_id=training_crop_id,
            bee_annotation_id=bee_annotation_id,
            head_up_normalized_image_bytes=image.body,
            image_width_px=head_up_crop.image_width_px,
            image_height_px=head_up_crop.image_height_px,
            transform_version=head_up_crop.transform_version,
            transform_metadata=head_up_crop.transform_metadata,
            source_geometry_snapshot=head_up_crop.bee_annotation_geometry_snapshot,
        )
        try:
            detections = self.varroa_detector_adapter.detect(request)
        except VarroaDetectorFailure as error:
            response = VarroaDetectorPreviewResponse(
                workspace_id=workspace_id,
                inspection_photo_id=crop.inspection_photo_id,
                training_crop_id=training_crop_id,
                bee_annotation_id=bee_annotation_id,
                adapter_type=self.varroa_detector_adapter.adapter_type,
                adapter_version=self.varroa_detector_adapter.adapter_version,
                model_reference=self.varroa_detector_adapter.model_reference,
                status=VarroaDetectorPreviewStatus.failed,
                failure_code=error.code,
                failure_message=error.message,
                elapsed_ms=_elapsed_ms(started),
                not_user_facing_reason="Varroa Detector preview only; not user-facing.",
                detections=[],
                detection_count=0,
                head_up_normalized_crop=head_up_crop,
                caveat=(
                    f"{VARROA_DETECTOR_STUB_CAVEAT} Adapter failure cleared model-preview boxes."
                ),
            )
            self._log_detector_preview(response)
            return response

        response = VarroaDetectorPreviewResponse(
            workspace_id=workspace_id,
            inspection_photo_id=crop.inspection_photo_id,
            training_crop_id=training_crop_id,
            bee_annotation_id=bee_annotation_id,
            adapter_type=self.varroa_detector_adapter.adapter_type,
            adapter_version=self.varroa_detector_adapter.adapter_version,
            model_reference=self.varroa_detector_adapter.model_reference,
            status=VarroaDetectorPreviewStatus.completed,
            elapsed_ms=_elapsed_ms(started),
            not_user_facing_reason="Deterministic stub preview only; not user-facing.",
            detections=detections,
            detection_count=len(detections),
            head_up_normalized_crop=head_up_crop,
            caveat=VARROA_DETECTOR_STUB_CAVEAT,
        )
        self._log_detector_preview(response)
        return response

    def count_frame_mites(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_photo_id: UUID,
    ) -> FrameMiteCountResponse:
        started = perf_counter()
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
                "inspection_intent_not_for_frame_mite_count",
                "Frame mite counts are available only for Training Data Collection inspections.",
                409,
            )
        hive = self.store.get_hive(inspection.hive_id)

        crops = self.store.list_training_crops_for_photo_id(
            workspace_id=workspace_id,
            inspection_photo_id=inspection_photo_id,
        )
        completed_crops = [
            crop for crop in crops if crop.review_status == TrainingCropReviewStatus.review_complete
        ]
        excluded_crops = [
            crop for crop in crops if crop.review_status == TrainingCropReviewStatus.excluded
        ]
        unfinished_crops = [
            crop
            for crop in crops
            if crop.review_status
            not in {TrainingCropReviewStatus.review_complete, TrainingCropReviewStatus.excluded}
        ]
        bee_results: list[FrameMiteCountBeeResultResponse] = []
        not_assessed_reasons: dict[str, int] = {}
        failure_reasons: dict[str, int] = {}
        eligible_bee_count = 0

        for crop_ordinal, crop in enumerate(crops, start=1):
            if crop.review_status != TrainingCropReviewStatus.review_complete:
                continue
            ellipses = self.store.get_ellipses_for_training_crop(crop.training_crop_id)
            for bee_ordinal, ellipse in enumerate(ellipses, start=1):
                reasons = _ineligibility_reasons(crop=crop, ellipse=ellipse)
                if reasons:
                    reason = ", ".join(reasons)
                    _increment(not_assessed_reasons, reason)
                    bee_results.append(
                        FrameMiteCountBeeResultResponse(
                            training_crop_id=crop.training_crop_id,
                            bee_annotation_id=ellipse.annotation_id,
                            crop_ordinal=crop_ordinal,
                            bee_ordinal=bee_ordinal,
                            status=FrameMiteCountBeeStatus.not_assessed,
                            detection_count=0,
                            not_assessed_reason=reason,
                        )
                    )
                    continue

                eligible_bee_count += 1
                head_up_crop = _preview_response(workspace_id=workspace_id, crop=crop, ellipse=ellipse)
                try:
                    image = self._build_head_up_normalized_crop_image(
                        workspace_id=workspace_id,
                        crop=crop,
                        ellipse=ellipse,
                    )
                except DomainError as error:
                    if error.code in {
                        "source_image_not_available",
                        "image_processing_unavailable",
                        "varroa_review_candidate_ineligible",
                    }:
                        _increment(not_assessed_reasons, error.code)
                        bee_results.append(
                            FrameMiteCountBeeResultResponse(
                                training_crop_id=crop.training_crop_id,
                                bee_annotation_id=ellipse.annotation_id,
                                crop_ordinal=crop_ordinal,
                                bee_ordinal=bee_ordinal,
                                status=FrameMiteCountBeeStatus.not_assessed,
                                detection_count=0,
                                not_assessed_reason=error.code,
                                head_up_normalized_crop=head_up_crop,
                                transform_version=head_up_crop.transform_version,
                                transform_metadata=head_up_crop.transform_metadata,
                            )
                        )
                        continue
                    raise

                request = VarroaDetectorRequest(
                    workspace_id=workspace_id,
                    inspection_photo_id=inspection_photo_id,
                    training_crop_id=crop.training_crop_id,
                    bee_annotation_id=ellipse.annotation_id,
                    head_up_normalized_image_bytes=image.body,
                    image_width_px=head_up_crop.image_width_px,
                    image_height_px=head_up_crop.image_height_px,
                    transform_version=head_up_crop.transform_version,
                    transform_metadata=head_up_crop.transform_metadata,
                    source_geometry_snapshot=head_up_crop.bee_annotation_geometry_snapshot,
                )
                try:
                    detections = self.varroa_detector_adapter.detect(request)
                except VarroaDetectorFailure as error:
                    _increment(failure_reasons, error.code)
                    bee_results.append(
                        FrameMiteCountBeeResultResponse(
                            training_crop_id=crop.training_crop_id,
                            bee_annotation_id=ellipse.annotation_id,
                            crop_ordinal=crop_ordinal,
                            bee_ordinal=bee_ordinal,
                            status=FrameMiteCountBeeStatus.failed,
                            detection_count=0,
                            failure_code=error.code,
                            failure_message=error.message,
                            head_up_normalized_crop=head_up_crop,
                            transform_version=head_up_crop.transform_version,
                            transform_metadata=head_up_crop.transform_metadata,
                        )
                    )
                    continue

                bee_results.append(
                    FrameMiteCountBeeResultResponse(
                        training_crop_id=crop.training_crop_id,
                        bee_annotation_id=ellipse.annotation_id,
                        crop_ordinal=crop_ordinal,
                        bee_ordinal=bee_ordinal,
                        status=FrameMiteCountBeeStatus.completed,
                        detection_count=len(detections),
                        detections=detections,
                        head_up_normalized_crop=head_up_crop,
                        transform_version=head_up_crop.transform_version,
                        transform_metadata=head_up_crop.transform_metadata,
                    )
                )

        processed_bee_count = sum(
            1 for result in bee_results if result.status == FrameMiteCountBeeStatus.completed
        )
        failed_bee_count = sum(
            1 for result in bee_results if result.status == FrameMiteCountBeeStatus.failed
        )
        not_assessed_bee_count = sum(
            1 for result in bee_results if result.status == FrameMiteCountBeeStatus.not_assessed
        )
        detection_count = sum(result.detection_count for result in bee_results)
        bees_with_likely_varroa_count = sum(
            1
            for result in bee_results
            if result.status == FrameMiteCountBeeStatus.completed and result.detection_count > 0
        )
        status = _frame_count_status(
            processed_bee_count=processed_bee_count,
            failed_bee_count=failed_bee_count,
            not_assessed_bee_count=not_assessed_bee_count,
            unfinished_crop_count=len(unfinished_crops),
            excluded_crop_count=len(excluded_crops),
        )
        response = FrameMiteCountResponse(
            workspace_id=workspace_id,
            inspection_id=inspection.inspection_id,
            hive_id=inspection.hive_id,
            apiary_id=hive.apiary_id if hive is not None else None,
            inspection_date=inspection.inspection_date,
            inspection_photo_id=inspection_photo_id,
            source_image_filename=photo.filename,
            source_intent=inspection.intent,
            adapter_type=self.varroa_detector_adapter.adapter_type,
            adapter_version=self.varroa_detector_adapter.adapter_version,
            model_reference=self.varroa_detector_adapter.model_reference,
            status=status,
            elapsed_ms=_elapsed_ms(started),
            completed_training_crop_count=len(completed_crops),
            unfinished_training_crop_count=len(unfinished_crops),
            excluded_training_crop_count=len(excluded_crops),
            eligible_bee_count=eligible_bee_count,
            processed_bee_count=processed_bee_count,
            failed_bee_count=failed_bee_count,
            not_assessed_bee_count=not_assessed_bee_count,
            likely_visible_varroa_detection_count=detection_count,
            bees_with_likely_varroa_count=bees_with_likely_varroa_count,
            model_determinate_coverage_percent=_percent(processed_bee_count, eligible_bee_count),
            not_assessed_reasons=not_assessed_reasons,
            failure_reasons=failure_reasons,
            bee_results=bee_results,
            not_user_facing_reason="Model-assisted frame mite count only; not user-facing.",
            caveat=_frame_count_caveat(
                status=status,
                unfinished_crop_count=len(unfinished_crops),
                excluded_crop_count=len(excluded_crops),
                not_assessed_bee_count=not_assessed_bee_count,
                failed_bee_count=failed_bee_count,
            ),
            advisor_context_available=False,
        )
        self._log_frame_mite_count(response)
        return response

    def _build_head_up_normalized_crop_image(
        self,
        workspace_id: UUID,
        crop: TrainingCropResponse,
        ellipse: OrientedBeeEllipseResponse,
    ) -> HeadUpNormalizedCropImage:
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

    def _not_assessed_preview_response(
        self,
        *,
        workspace_id: UUID,
        crop: TrainingCropResponse,
        ellipse: OrientedBeeEllipseResponse,
        reason: str,
        elapsed_ms: int,
    ) -> VarroaDetectorPreviewResponse:
        response = VarroaDetectorPreviewResponse(
            workspace_id=workspace_id,
            inspection_photo_id=crop.inspection_photo_id,
            training_crop_id=crop.training_crop_id,
            bee_annotation_id=ellipse.annotation_id,
            adapter_type="not_called",
            adapter_version="not_called",
            model_reference="not_called",
            status=VarroaDetectorPreviewStatus.not_assessed,
            not_assessed_reason=reason,
            elapsed_ms=elapsed_ms,
            not_user_facing_reason="Varroa Detector preview only; not user-facing.",
            detections=[],
            detection_count=0,
            head_up_normalized_crop=None,
            caveat=(
                f"Bee not assessed for Varroa Detection: {reason}. "
                "This is not a negative Varroa result."
            ),
        )
        self._log_detector_preview(response)
        return response

    def _log_detector_preview(self, response: VarroaDetectorPreviewResponse) -> None:
        LOGGER.info(
            "Calculated Varroa Detector preview",
            extra={
                "workspace_id": str(response.workspace_id),
                "inspection_photo_id": str(response.inspection_photo_id),
                "training_crop_id": str(response.training_crop_id),
                "bee_annotation_id": str(response.bee_annotation_id),
                "adapter_type": response.adapter_type,
                "adapter_version": response.adapter_version,
                "detection_count": response.detection_count,
                "elapsed_ms": response.elapsed_ms,
                "status": str(response.status),
                "failure_code": response.failure_code,
            },
        )

    def _log_frame_mite_count(self, response: FrameMiteCountResponse) -> None:
        LOGGER.info(
            "Calculated model-assisted frame mite count",
            extra={
                "workspace_id": str(response.workspace_id),
                "inspection_id": str(response.inspection_id),
                "inspection_photo_id": str(response.inspection_photo_id),
                "adapter_type": response.adapter_type,
                "adapter_version": response.adapter_version,
                "status": str(response.status),
                "eligible_bee_count": response.eligible_bee_count,
                "processed_bee_count": response.processed_bee_count,
                "failed_bee_count": response.failed_bee_count,
                "likely_visible_varroa_detection_count": response.likely_visible_varroa_detection_count,
                "elapsed_ms": response.elapsed_ms,
            },
        )

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
        "mite_marker_allowed_area": _mite_marker_allowed_area(crop=crop, ellipse=ellipse),
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


def _mite_marker_allowed_area(
    crop: TrainingCropResponse,
    ellipse: OrientedBeeEllipseResponse,
) -> dict[str, float]:
    left, top, right, bottom = _source_crop_bounds(crop=crop, ellipse=ellipse)
    crop_width = right - left
    crop_height = bottom - top
    rotated_width = _rotated_extent(crop_width, crop_height, _head_up_rotation_degrees(ellipse.rotation_degrees), "x")
    rotated_height = _rotated_extent(crop_width, crop_height, _head_up_rotation_degrees(ellipse.rotation_degrees), "y")
    scale = min(
        1.0,
        HEAD_UP_NORMALIZED_IMAGE_SIZE_PX / rotated_width,
        HEAD_UP_NORMALIZED_IMAGE_SIZE_PX / rotated_height,
    )
    canvas_offset_x = (HEAD_UP_NORMALIZED_IMAGE_SIZE_PX - rotated_width * scale) / 2
    canvas_offset_y = (HEAD_UP_NORMALIZED_IMAGE_SIZE_PX - rotated_height * scale) / 2
    rotated_center_x, rotated_center_y = _rotate_point_in_expanded_canvas(
        x=ellipse.center_x - left,
        y=ellipse.center_y - top,
        width=crop_width,
        height=crop_height,
        angle_degrees=_head_up_rotation_degrees(ellipse.rotation_degrees),
        rotated_width=rotated_width,
        rotated_height=rotated_height,
    )
    marker_radius_x = max(8.0, min(ellipse.radius_x, ellipse.radius_y) * scale * 1.25)
    marker_radius_y = max(8.0, max(ellipse.radius_x, ellipse.radius_y) * scale * 1.1)
    return {
        "center_x": round((canvas_offset_x + rotated_center_x * scale) / HEAD_UP_NORMALIZED_IMAGE_SIZE_PX, 6),
        "center_y": round((canvas_offset_y + rotated_center_y * scale) / HEAD_UP_NORMALIZED_IMAGE_SIZE_PX, 6),
        "radius_x": round(marker_radius_x / HEAD_UP_NORMALIZED_IMAGE_SIZE_PX, 6),
        "radius_y": round(marker_radius_y / HEAD_UP_NORMALIZED_IMAGE_SIZE_PX, 6),
    }


def _rotated_extent(width: int, height: int, angle_degrees: float, axis: str) -> float:
    angle = radians(angle_degrees)
    if axis == "x":
        return abs(width * cos(angle)) + abs(height * sin(angle))
    return abs(width * sin(angle)) + abs(height * cos(angle))


def _rotate_point_in_expanded_canvas(
    *,
    x: float,
    y: float,
    width: int,
    height: int,
    angle_degrees: float,
    rotated_width: float,
    rotated_height: float,
) -> tuple[float, float]:
    angle = radians(angle_degrees)
    source_center_x = width / 2
    source_center_y = height / 2
    translated_x = x - source_center_x
    translated_y = y - source_center_y
    rotated_x = translated_x * cos(angle) - translated_y * sin(angle)
    rotated_y = translated_x * sin(angle) + translated_y * cos(angle)
    return rotated_x + rotated_width / 2, rotated_y + rotated_height / 2


def _head_up_rotation_degrees(rotation_degrees: float) -> float:
    return rotation_degrees + 90


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _increment(counts: dict[str, int], key: str) -> None:
    counts[key] = counts.get(key, 0) + 1


def _percent(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def _frame_count_status(
    *,
    processed_bee_count: int,
    failed_bee_count: int,
    not_assessed_bee_count: int,
    unfinished_crop_count: int,
    excluded_crop_count: int,
) -> FrameMiteCountStatus:
    if processed_bee_count == 0:
        return FrameMiteCountStatus.not_available
    if (
        failed_bee_count > 0
        or not_assessed_bee_count > 0
        or unfinished_crop_count > 0
        or excluded_crop_count > 0
    ):
        return FrameMiteCountStatus.completed_with_warnings
    return FrameMiteCountStatus.completed


def _frame_count_caveat(
    *,
    status: FrameMiteCountStatus,
    unfinished_crop_count: int,
    excluded_crop_count: int,
    not_assessed_bee_count: int,
    failed_bee_count: int,
) -> str:
    caveats = [
        "Model-assisted frame mite count only; not treatment advice and not a human Varroa review.",
        "Count is over bee annotations on this selected Inspection Photo, not deduplicated physical bees.",
    ]
    if status == FrameMiteCountStatus.not_available:
        caveats.append("No eligible Head-Up Normalized Bee Crops could be processed.")
    if unfinished_crop_count > 0:
        caveats.append(f"{unfinished_crop_count} unfinished crops were not included.")
    if excluded_crop_count > 0:
        caveats.append(f"{excluded_crop_count} excluded crops were not included.")
    if not_assessed_bee_count > 0:
        caveats.append(f"{not_assessed_bee_count} bees were not assessed by the detector.")
    if failed_bee_count > 0:
        caveats.append(f"{failed_bee_count} eligible bees failed during detector processing.")
    return " ".join(caveats)


def _elapsed_ms(started: float) -> int:
    return max(0, round((perf_counter() - started) * 1000))
