from dataclasses import dataclass
from math import cos, radians, sin, sqrt
from uuid import UUID

from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    AnnotationType,
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
            training_crops=self.store.list_training_crops_for_photo_id(
                workspace_id=workspace_id,
                inspection_photo_id=inspection_photo_id,
            ),
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
        _require_crop_editable(crop)
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
        _require_crop_editable(crop)
        if crop.visible_bee_status == VisibleBeeStatus.no_visible_bees:
            raise DomainError(
                "no_visible_bees_conflicts_with_ellipses",
                "A no-visible-bees Training Crop cannot retain bee ellipses.",
                409,
            )
        _validate_bee_annotation_type(request.annotation_type)
        rotation = _normalize_rotation(request.rotation_degrees)
        _validate_ellipse_inside_crop(
            crop=crop,
            center_x=request.center_x,
            center_y=request.center_y,
            radius_x=request.radius_x,
            radius_y=request.radius_y,
            rotation_degrees=rotation,
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
            source="human_from_scratch",
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
        _validate_ellipse_inside_crop(crop=crop, **next_values)
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
            training_crop=crop,
            bee_ellipses=self.store.get_ellipses_for_training_crop(training_crop_id),
            caveat=(
                "Training Crop annotations are human-created review evidence. "
                "Dataset use is assigned later through Bee Annotation Repository workflows."
            ),
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


def _validate_ellipse_inside_crop(
    crop: TrainingCropResponse,
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
    rotation_degrees: float,
    annotation_type: AnnotationType | None = None,
) -> None:
    _ = annotation_type
    angle = radians(rotation_degrees)
    x_extent = sqrt((radius_x * cos(angle)) ** 2 + (radius_y * sin(angle)) ** 2)
    y_extent = sqrt((radius_x * sin(angle)) ** 2 + (radius_y * cos(angle)) ** 2)
    if (
        center_x - x_extent < crop.crop_x
        or center_y - y_extent < crop.crop_y
        or center_x + x_extent > crop.crop_x + crop.crop_width
        or center_y + y_extent > crop.crop_y + crop.crop_height
    ):
        raise DomainError(
            "ellipse_outside_crop_bounds",
            "Oriented bee ellipses must stay inside the Training Crop bounds.",
            422,
        )


def _require_crop_editable(crop: TrainingCropResponse) -> None:
    if crop.review_status in {
        TrainingCropReviewStatus.review_complete,
        TrainingCropReviewStatus.excluded,
    }:
        raise DomainError(
            "training_crop_locked",
            "Completed or excluded Training Crops are locked in this slice.",
            409,
        )


def _normalize_rotation(rotation_degrees: float) -> float:
    return rotation_degrees % 360


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
