from dataclasses import dataclass
from math import cos, radians, sin, sqrt
from uuid import UUID

from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    AnnotationType,
    BeeEllipseAnnotationSource,
    BeeEllipseReviewMethod,
    CoordinateSpace,
    InspectionIntent,
    InspectionPhotoEvidenceResponse,
    OrientedBeeEllipseCreateRequest,
    OrientedBeeEllipseResponse,
    OrientedBeeEllipseUpdateRequest,
    TrainingCropCreateRequest,
    TrainingCropEvidenceResponse,
    TrainingCropExclusionReason,
    TrainingCropListResponse,
    TrainingCropResponse,
    TrainingCropReviewStatus,
    TrainingCropUpdateRequest,
    VisibleBeeStatus,
)


@dataclass(frozen=True)
class TrainingCropWorkflow:
    store: InMemoryProductDataStore

    def create_training_crop(
        self,
        user: UserContext,
        request: TrainingCropCreateRequest,
    ) -> TrainingCropResponse:
        self._require_training_crop_photo(
            user=user,
            workspace_id=request.workspace_id,
            inspection_photo_id=request.inspection_photo_id,
        )
        _validate_crop_bounds(
            crop_x=request.crop_x,
            crop_y=request.crop_y,
            crop_width=request.crop_width,
            crop_height=request.crop_height,
            source_image_width_px=request.source_image_width_px,
            source_image_height_px=request.source_image_height_px,
        )
        created_at = self.store.clock()
        crop = TrainingCropResponse(
            training_crop_id=self.store.id_factory(),
            workspace_id=request.workspace_id,
            inspection_photo_id=request.inspection_photo_id,
            crop_x=request.crop_x,
            crop_y=request.crop_y,
            crop_width=request.crop_width,
            crop_height=request.crop_height,
            coordinate_space=CoordinateSpace.source_image_pixels,
            source_image_width_px=request.source_image_width_px,
            source_image_height_px=request.source_image_height_px,
            crop_image_width_px=request.crop_width,
            crop_image_height_px=request.crop_height,
            curriculum_stage="small_crop",
            review_status=TrainingCropReviewStatus.review_pending,
            visible_bee_status=VisibleBeeStatus.unassessed,
            exclusion_reason=None,
            notes=_clean_optional_text(request.notes),
            created_by_user_id=user.user_id,
            created_at=created_at,
            updated_at=created_at,
        )
        self.store.save_training_crop(crop)
        return crop

    def list_training_crops_for_photo(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_photo_id: UUID,
    ) -> TrainingCropListResponse:
        photo = self._require_training_crop_photo(
            user=user,
            workspace_id=workspace_id,
            inspection_photo_id=inspection_photo_id,
        )
        return TrainingCropListResponse(
            inspection_photo=photo,
            training_crops=[
                self._with_dataset_assignment(crop)
                for crop in self.store.list_training_crops_for_photo_id(
                    workspace_id=workspace_id,
                    inspection_photo_id=inspection_photo_id,
                )
            ],
        )

    def update_training_crop(
        self,
        user: UserContext,
        training_crop_id: UUID,
        request: TrainingCropUpdateRequest,
    ) -> TrainingCropResponse:
        crop = self.store.require_training_crop(
            user=user,
            workspace_id=request.workspace_id,
            training_crop_id=training_crop_id,
        )
        _require_no_available_review_queue_item(self.store, crop.training_crop_id)
        existing_ellipses = self.store.get_ellipses_for_training_crop(training_crop_id)
        bounds_updates = {
            key: value
            for key, value in {
                "crop_x": request.crop_x,
                "crop_y": request.crop_y,
                "crop_width": request.crop_width,
                "crop_height": request.crop_height,
            }.items()
            if value is not None
        }
        if _crop_is_locked(crop):
            if request.review_status != TrainingCropReviewStatus.review_pending or bounds_updates:
                _require_crop_editable(crop)
        if bounds_updates and existing_ellipses:
            raise DomainError(
                "crop_bounds_locked",
                "Training Crop bounds cannot be changed after bee ellipses exist.",
                409,
            )

        next_values = {
            "crop_x": crop.crop_x,
            "crop_y": crop.crop_y,
            "crop_width": crop.crop_width,
            "crop_height": crop.crop_height,
            "visible_bee_status": crop.visible_bee_status,
            "review_status": crop.review_status,
            "exclusion_reason": crop.exclusion_reason,
            "notes": crop.notes,
        }
        next_values.update(bounds_updates)
        if request.visible_bee_status is not None:
            next_values["visible_bee_status"] = request.visible_bee_status
        if request.review_status is not None:
            next_values["review_status"] = request.review_status
            if request.review_status == TrainingCropReviewStatus.review_pending:
                next_values["exclusion_reason"] = None
        if request.exclusion_reason is not None:
            next_values["exclusion_reason"] = request.exclusion_reason
        if request.notes is not None:
            next_values["notes"] = _clean_optional_text(request.notes)

        _validate_crop_bounds(
            crop_x=next_values["crop_x"],
            crop_y=next_values["crop_y"],
            crop_width=next_values["crop_width"],
            crop_height=next_values["crop_height"],
            source_image_width_px=crop.source_image_width_px,
            source_image_height_px=crop.source_image_height_px,
        )
        _validate_crop_review_state(
            visible_bee_status=next_values["visible_bee_status"],
            review_status=next_values["review_status"],
            exclusion_reason=next_values["exclusion_reason"],
            ellipse_count=len(existing_ellipses),
        )

        updated = crop.model_copy(
            update={
                **next_values,
                "crop_image_width_px": next_values["crop_width"],
                "crop_image_height_px": next_values["crop_height"],
                "updated_at": self.store.clock(),
            }
        )
        self.store.save_training_crop(updated)
        return updated

    def delete_training_crop(
        self,
        user: UserContext,
        workspace_id: UUID,
        training_crop_id: UUID,
    ) -> None:
        crop = self.store.require_training_crop(
            user=user,
            workspace_id=workspace_id,
            training_crop_id=training_crop_id,
        )
        _require_no_available_review_queue_item(self.store, crop.training_crop_id)
        if self.store.get_dataset_item_for_training_crop(crop.training_crop_id) is not None:
            raise DomainError(
                "training_crop_dataset_item_exists",
                "A Training Crop cannot be deleted after it has been assigned to a Dataset Item.",
                409,
            )
        self.store.delete_training_crop_record(crop.training_crop_id)

    def create_training_crop_ellipse(
        self,
        user: UserContext,
        training_crop_id: UUID,
        request: OrientedBeeEllipseCreateRequest,
    ) -> OrientedBeeEllipseResponse:
        crop = self.store.require_training_crop(
            user=user,
            workspace_id=request.workspace_id,
            training_crop_id=training_crop_id,
        )
        _require_no_available_review_queue_item(self.store, crop.training_crop_id)
        _require_crop_editable(crop)
        if crop.visible_bee_status == VisibleBeeStatus.no_visible_bees:
            raise DomainError(
                "no_visible_bees_conflicts_with_ellipses",
                "A no-visible-bees Training Crop cannot retain bee ellipses.",
                409,
            )
        _validate_bee_annotation_type(request.annotation_type)
        _validate_ellipse_provenance(request)
        rotation = _normalize_rotation(request.rotation_degrees)
        _validate_ellipse_for_crop(
            crop=crop,
            center_x=request.center_x,
            center_y=request.center_y,
            radius_x=request.radius_x,
            radius_y=request.radius_y,
            rotation_degrees=rotation,
            annotation_type=request.annotation_type,
        )
        created_at = self.store.clock()
        ellipse = OrientedBeeEllipseResponse(
            annotation_id=self.store.id_factory(),
            workspace_id=request.workspace_id,
            inspection_photo_id=crop.inspection_photo_id,
            training_crop_id=training_crop_id,
            annotation_type=request.annotation_type,
            center_x=request.center_x,
            center_y=request.center_y,
            radius_x=request.radius_x,
            radius_y=request.radius_y,
            rotation_degrees=rotation,
            coordinate_space=CoordinateSpace.source_image_pixels,
            source_image_width_px=crop.source_image_width_px,
            source_image_height_px=crop.source_image_height_px,
            source=request.source,
            review_method=request.review_method,
            model_candidate_id=request.model_candidate_id,
            candidate_confidence=request.candidate_confidence,
            candidate_threshold=request.candidate_threshold,
            raw_model_class=_clean_optional_text(request.raw_model_class),
            raw_yolo_obb=request.raw_yolo_obb,
            candidate_review_decision=request.candidate_review_decision,
            created_by_user_id=user.user_id,
            created_at=created_at,
            updated_at=created_at,
        )
        self.store.save_training_crop_ellipse(ellipse)
        if crop.visible_bee_status == VisibleBeeStatus.unassessed:
            self.store.save_training_crop(
                crop.model_copy(
                    update={
                        "visible_bee_status": VisibleBeeStatus.has_visible_bees,
                        "updated_at": created_at,
                    }
                )
            )
        return ellipse

    def update_training_crop_ellipse(
        self,
        user: UserContext,
        annotation_id: UUID,
        request: OrientedBeeEllipseUpdateRequest,
    ) -> OrientedBeeEllipseResponse:
        ellipse = self.store.get_training_crop_ellipse(annotation_id)
        if ellipse is None or ellipse.workspace_id != request.workspace_id:
            raise DomainError(
                "ellipse_not_found",
                "The requested oriented bee ellipse was not found in this Workspace.",
                404,
            )
        crop = self.store.require_training_crop(
            user=user,
            workspace_id=request.workspace_id,
            training_crop_id=ellipse.training_crop_id,
        )
        _require_no_available_review_queue_item(self.store, crop.training_crop_id)
        _require_crop_editable(crop)
        annotation_type = request.annotation_type or ellipse.annotation_type
        _validate_bee_annotation_type(annotation_type)
        next_values = {
            "annotation_type": annotation_type,
            "center_x": ellipse.center_x if request.center_x is None else request.center_x,
            "center_y": ellipse.center_y if request.center_y is None else request.center_y,
            "radius_x": ellipse.radius_x if request.radius_x is None else request.radius_x,
            "radius_y": ellipse.radius_y if request.radius_y is None else request.radius_y,
            "rotation_degrees": (
                ellipse.rotation_degrees
                if request.rotation_degrees is None
                else _normalize_rotation(request.rotation_degrees)
            ),
        }
        _validate_ellipse_for_crop(crop=crop, **next_values)
        updated = ellipse.model_copy(update={**next_values, "updated_at": self.store.clock()})
        self.store.save_training_crop_ellipse(updated)
        return updated

    def delete_training_crop_ellipse(
        self,
        user: UserContext,
        workspace_id: UUID,
        annotation_id: UUID,
    ) -> None:
        ellipse = self.store.get_training_crop_ellipse(annotation_id)
        if ellipse is None or ellipse.workspace_id != workspace_id:
            raise DomainError(
                "ellipse_not_found",
                "The requested oriented bee ellipse was not found in this Workspace.",
                404,
            )
        crop = self.store.require_training_crop(
            user=user,
            workspace_id=workspace_id,
            training_crop_id=ellipse.training_crop_id,
        )
        _require_no_available_review_queue_item(self.store, crop.training_crop_id)
        _require_crop_editable(crop)
        self.store.delete_training_crop_ellipse_record(annotation_id)

    def get_training_crop_evidence(
        self,
        user: UserContext,
        workspace_id: UUID,
        training_crop_id: UUID,
    ) -> TrainingCropEvidenceResponse:
        crop = self.store.require_training_crop(
            user=user,
            workspace_id=workspace_id,
            training_crop_id=training_crop_id,
        )
        photo = self._require_training_crop_photo(
            user=user,
            workspace_id=workspace_id,
            inspection_photo_id=crop.inspection_photo_id,
        )
        return TrainingCropEvidenceResponse(
            inspection_photo=InspectionPhotoEvidenceResponse(
                inspection_photo_id=photo.inspection_photo_id,
                filename=photo.filename,
                content_type=photo.content_type,
                view_url=(
                    f"/v1/inspection-photos/{photo.inspection_photo_id}/content"
                    f"?workspace_id={workspace_id}"
                ),
                width=crop.source_image_width_px,
                height=crop.source_image_height_px,
            ),
            training_crop=self._with_dataset_assignment(crop),
            bee_ellipses=self.store.get_ellipses_for_training_crop(training_crop_id),
            caveat=(
                "Training Crop annotations are human-created review evidence. "
                "Dataset use is assigned later through Bee Annotation Repository workflows."
            ),
        )

    def _with_dataset_assignment(self, crop: TrainingCropResponse) -> TrainingCropResponse:
        dataset_item = self.store.get_dataset_item_for_training_crop(crop.training_crop_id)
        if dataset_item is None:
            return crop.model_copy(update={"dataset_item_id": None, "dataset_role": None})
        return crop.model_copy(
            update={
                "dataset_item_id": dataset_item.dataset_item_id,
                "dataset_role": dataset_item.dataset_role,
            }
        )

    def _require_training_crop_photo(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_photo_id: UUID,
    ):
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
                "inspection_intent_not_for_training_crop",
                "Training Crops can be created only from training data collection Inspections.",
                409,
            )
        return photo


def _validate_crop_bounds(
    crop_x: int,
    crop_y: int,
    crop_width: int,
    crop_height: int,
    source_image_width_px: int,
    source_image_height_px: int,
) -> None:
    if (
        crop_x < 0
        or crop_y < 0
        or crop_width <= 0
        or crop_height <= 0
        or crop_x + crop_width > source_image_width_px
        or crop_y + crop_height > source_image_height_px
    ):
        raise DomainError(
            "invalid_crop_bounds",
            "Training Crop bounds must fit inside the source Inspection Photo.",
            422,
        )


def _validate_crop_review_state(
    visible_bee_status: VisibleBeeStatus,
    review_status: TrainingCropReviewStatus,
    exclusion_reason: TrainingCropExclusionReason | None,
    ellipse_count: int,
) -> None:
    if visible_bee_status == VisibleBeeStatus.no_visible_bees and ellipse_count > 0:
        raise DomainError(
            "no_visible_bees_conflicts_with_ellipses",
            "A no-visible-bees Training Crop cannot retain bee ellipses.",
            409,
        )
    if (
        review_status == TrainingCropReviewStatus.review_complete
        and visible_bee_status == VisibleBeeStatus.has_visible_bees
        and ellipse_count == 0
    ):
        raise DomainError(
            "visible_bees_require_ellipse",
            "A reviewed Training Crop with visible bees requires at least one bee ellipse.",
            409,
        )
    if (
        review_status == TrainingCropReviewStatus.review_complete
        and visible_bee_status == VisibleBeeStatus.unassessed
    ):
        raise DomainError(
            "visible_bee_status_required",
            "A reviewed Training Crop requires an assessed visible bee status.",
            409,
        )
    if review_status == TrainingCropReviewStatus.excluded and exclusion_reason is None:
        raise DomainError(
            "exclusion_reason_required",
            "An excluded Training Crop requires an exclusion reason.",
            409,
        )


def _validate_bee_annotation_type(annotation_type: AnnotationType) -> None:
    if annotation_type not in {
        AnnotationType.complete_visible_bee,
        AnnotationType.partial_visible_bee,
    }:
        raise DomainError(
            "unsupported_training_crop_annotation_type",
            "Training Crop annotation supports complete and partial visible bees only.",
            422,
        )


def _validate_ellipse_provenance(request: OrientedBeeEllipseCreateRequest) -> None:
    if request.source == BeeEllipseAnnotationSource.human_from_scratch:
        if request.review_method != BeeEllipseReviewMethod.human_from_scratch:
            raise DomainError(
                "invalid_ellipse_provenance",
                "Human-from-scratch ellipses must use the human_from_scratch review method.",
                422,
            )
        if any(
            value is not None
            for value in (
                request.model_candidate_id,
                request.candidate_confidence,
                request.candidate_threshold,
                request.raw_model_class,
                request.raw_yolo_obb,
                request.candidate_review_decision,
            )
        ):
            raise DomainError(
                "invalid_ellipse_provenance",
                "Human-from-scratch ellipses cannot carry Model Candidate provenance.",
                422,
            )
        return
    if request.source == BeeEllipseAnnotationSource.model_candidate:
        if request.review_method != BeeEllipseReviewMethod.human_reviewed_candidate:
            raise DomainError(
                "invalid_ellipse_provenance",
                "Model Candidate ellipses must be recorded as human-reviewed candidates.",
                422,
            )
        if (
            request.model_candidate_id is None
            or request.candidate_confidence is None
            or request.candidate_threshold is None
            or request.raw_model_class is None
            or request.raw_yolo_obb is None
            or request.candidate_review_decision is None
        ):
            raise DomainError(
                "invalid_ellipse_provenance",
                "Model Candidate ellipses require candidate confidence, threshold, raw class, raw OBB, and review decision.",
                422,
            )
        return
    raise DomainError(
        "invalid_ellipse_provenance",
        "Only human-from-scratch and Model Candidate ellipse sources are supported for Training Crop review.",
        422,
    )


def _validate_ellipse_for_crop(
    crop: TrainingCropResponse,
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
    rotation_degrees: float,
    annotation_type: AnnotationType | None = None,
) -> None:
    angle = radians(rotation_degrees)
    x_extent = sqrt((radius_x * cos(angle)) ** 2 + (radius_y * sin(angle)) ** 2)
    y_extent = sqrt((radius_x * sin(angle)) ** 2 + (radius_y * cos(angle)) ** 2)
    ellipse_bounds = (
        center_x - x_extent,
        center_y - y_extent,
        center_x + x_extent,
        center_y + y_extent,
    )
    crop_bounds = (
        crop.crop_x,
        crop.crop_y,
        crop.crop_x + crop.crop_width,
        crop.crop_y + crop.crop_height,
    )
    if annotation_type == AnnotationType.partial_visible_bee:
        if not _bounds_overlap(ellipse_bounds, crop_bounds):
            raise DomainError(
                "ellipse_outside_crop_bounds",
                "Partial visible bee ellipses must overlap the Training Crop bounds.",
                422,
            )
        return

    if not _bounds_inside(ellipse_bounds, crop_bounds):
        raise DomainError(
            "ellipse_outside_crop_bounds",
            "Complete visible bee ellipses must stay inside the Training Crop bounds.",
            422,
        )


def _bounds_inside(
    inner_bounds: tuple[float, float, float, float],
    outer_bounds: tuple[float, float, float, float],
) -> bool:
    inner_left, inner_top, inner_right, inner_bottom = inner_bounds
    outer_left, outer_top, outer_right, outer_bottom = outer_bounds
    return (
        inner_left >= outer_left
        and inner_top >= outer_top
        and inner_right <= outer_right
        and inner_bottom <= outer_bottom
    )


def _bounds_overlap(
    left_bounds: tuple[float, float, float, float],
    right_bounds: tuple[float, float, float, float],
) -> bool:
    left_left, left_top, left_right, left_bottom = left_bounds
    right_left, right_top, right_right, right_bottom = right_bounds
    return (
        left_right > right_left
        and left_left < right_right
        and left_bottom > right_top
        and left_top < right_bottom
    )


def _crop_is_locked(crop: TrainingCropResponse) -> bool:
    return crop.review_status in {
        TrainingCropReviewStatus.review_complete,
        TrainingCropReviewStatus.excluded,
    }


def _require_crop_editable(crop: TrainingCropResponse) -> None:
    if _crop_is_locked(crop):
        raise DomainError(
            "training_crop_locked",
            "Completed or excluded Training Crops must be reopened before editing.",
            409,
        )


def _require_no_available_review_queue_item(
    store: InMemoryProductDataStore,
    training_crop_id: UUID,
) -> None:
    if store.active_review_queue_item_for_training_crop(training_crop_id) is not None:
        raise DomainError(
            "training_crop_review_request_active",
            "Cancel the available Review Queue Item before editing this Training Crop.",
            409,
        )


def _normalize_rotation(rotation_degrees: float) -> float:
    return rotation_degrees % 360


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
