from dataclasses import dataclass
from uuid import UUID

from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    DatasetExclusionReason,
    DatasetItemProvenanceResponse,
    DatasetItemResponse,
    DatasetRole,
    HiveConfigurationSnapshotResponse,
    ImageQualityStatus,
    ReviewedEllipseSnapshot,
    TrainingCropDatasetItemCreateRequest,
    TrainingCropResponse,
    TrainingCropReviewStatus,
    VisibleBeeStatus,
)


@dataclass(frozen=True)
class TrainingCropDatasetItemWorkflow:
    store: InMemoryProductDataStore

    def create_dataset_item_from_training_crop(
        self,
        user: UserContext,
        training_crop_id: UUID,
        request: TrainingCropDatasetItemCreateRequest,
    ) -> DatasetItemResponse:
        crop = self.store.require_training_crop(
            user=user,
            workspace_id=request.workspace_id,
            training_crop_id=training_crop_id,
        )
        cleaned_note = _clean_optional_text(request.assignment_note)
        cleaned_source_group_key = _clean_optional_text(request.source_group_key)
        _validate_dataset_item_exclusion(
            dataset_role=request.dataset_role,
            assignment_note=cleaned_note,
            exclusion_reason=request.exclusion_reason,
        )
        self._validate_dataset_role_leakage(
            crop=crop,
            dataset_role=request.dataset_role,
            source_group_key=cleaned_source_group_key,
        )
        ellipses = self.store.get_ellipses_for_training_crop(training_crop_id)
        _validate_training_crop_dataset_item_state(
            crop=crop,
            dataset_role=request.dataset_role,
            ellipse_count=len(ellipses),
        )
        if self.store.get_dataset_item_for_training_crop(training_crop_id) is not None:
            raise DomainError(
                "dataset_item_already_assigned",
                "This Training Crop has already been assigned to a Dataset Item.",
                409,
            )

        ellipse_snapshots = [
            ReviewedEllipseSnapshot(
                annotation_id=ellipse.annotation_id,
                annotation_type=ellipse.annotation_type,
                center_x=ellipse.center_x,
                center_y=ellipse.center_y,
                radius_x=ellipse.radius_x,
                radius_y=ellipse.radius_y,
                rotation_degrees=ellipse.rotation_degrees,
                coordinate_space=ellipse.coordinate_space,
                source_image_width_px=ellipse.source_image_width_px,
                source_image_height_px=ellipse.source_image_height_px,
                source=ellipse.source,
                review_method=ellipse.review_method,
                model_candidate_id=ellipse.model_candidate_id,
                candidate_confidence=ellipse.candidate_confidence,
                candidate_threshold=ellipse.candidate_threshold,
                raw_model_class=ellipse.raw_model_class,
                raw_yolo_obb=ellipse.raw_yolo_obb,
                candidate_review_decision=ellipse.candidate_review_decision,
                created_by_user_id=ellipse.created_by_user_id,
                created_at=ellipse.created_at,
                updated_at=ellipse.updated_at,
            )
            for ellipse in ellipses
        ]
        dataset_item = DatasetItemResponse(
            dataset_item_id=self.store.id_factory(),
            workspace_id=request.workspace_id,
            inspection_photo_id=crop.inspection_photo_id,
            labelling_session_id=None,
            training_crop_id=training_crop_id,
            source_evidence_type="training_crop",
            dataset_role=request.dataset_role,
            reviewed_annotation_ids=[ellipse.annotation_id for ellipse in ellipses],
            reviewed_ellipse_snapshots=ellipse_snapshots,
            crop_x=crop.crop_x,
            crop_y=crop.crop_y,
            crop_width=crop.crop_width,
            crop_height=crop.crop_height,
            crop_image_width_px=crop.crop_image_width_px,
            crop_image_height_px=crop.crop_image_height_px,
            curriculum_stage=crop.curriculum_stage,
            source_group_key=cleaned_source_group_key,
            image_quality_status=(
                ImageQualityStatus.exclude
                if request.dataset_role == DatasetRole.excluded
                else ImageQualityStatus.usable
            ),
            provenance=_dataset_item_provenance_for_training_crop(self.store, crop),
            assigned_by_user_id=user.user_id,
            assigned_at=self.store.clock(),
            assignment_note=cleaned_note,
            exclusion_reason=request.exclusion_reason,
            benchmark_protected=request.dataset_role == DatasetRole.benchmark,
        )
        self.store.save_dataset_item(dataset_item)
        return dataset_item

    def _validate_dataset_role_leakage(
        self,
        crop: TrainingCropResponse,
        dataset_role: DatasetRole,
        source_group_key: str | None,
    ) -> None:
        if dataset_role == DatasetRole.benchmark and source_group_key is None:
            raise DomainError(
                "benchmark_source_group_key_required",
                "Benchmark Dataset Items require a source group key.",
                422,
            )
        if dataset_role not in {DatasetRole.training, DatasetRole.validation, DatasetRole.benchmark}:
            return
        conflicting_roles = (
            {DatasetRole.training, DatasetRole.validation}
            if dataset_role == DatasetRole.benchmark
            else {DatasetRole.benchmark}
        )
        for existing in self.store.dataset_items.values():
            if existing.workspace_id != crop.workspace_id:
                continue
            if existing.dataset_role not in conflicting_roles:
                continue
            if existing.inspection_photo_id == crop.inspection_photo_id:
                raise DomainError(
                    "benchmark_source_image_leakage_conflict",
                    "Benchmark Dataset Items cannot share a Source Image with training or validation Dataset Items.",
                    409,
                )
            if (
                source_group_key is not None
                and existing.source_group_key is not None
                and existing.source_group_key == source_group_key
            ):
                raise DomainError(
                    "benchmark_source_group_leakage_conflict",
                    "Benchmark Dataset Items cannot share a source group key with training or validation Dataset Items.",
                    409,
                )


def _validate_dataset_item_exclusion(
    dataset_role: DatasetRole,
    assignment_note: str | None,
    exclusion_reason: DatasetExclusionReason | None,
) -> None:
    if dataset_role == DatasetRole.excluded and exclusion_reason is None:
        raise DomainError(
            "exclusion_reason_required",
            "Excluded Dataset Items require an exclusion reason.",
            422,
        )
    if dataset_role != DatasetRole.excluded and exclusion_reason is not None:
        raise DomainError(
            "exclusion_reason_not_allowed",
            "Only excluded Dataset Items may carry an exclusion reason.",
            422,
        )
    if exclusion_reason == DatasetExclusionReason.other and assignment_note is None:
        raise DomainError(
            "assignment_note_required",
            "The 'other' exclusion reason requires an assignment note.",
            422,
        )


def _validate_training_crop_dataset_item_state(
    crop: TrainingCropResponse,
    dataset_role: DatasetRole,
    ellipse_count: int,
) -> None:
    if crop.review_status == TrainingCropReviewStatus.review_pending:
        raise DomainError(
            "training_crop_review_required",
            "Assign a Dataset Role only after Training Crop review is complete or excluded.",
            409,
        )
    if crop.review_status == TrainingCropReviewStatus.excluded:
        if dataset_role != DatasetRole.excluded:
            raise DomainError(
                "training_crop_excluded_requires_excluded_role",
                "Excluded Training Crops can only create excluded Dataset Items.",
                409,
            )
        return
    if crop.visible_bee_status == VisibleBeeStatus.no_visible_bees:
        if dataset_role != DatasetRole.excluded:
            raise DomainError(
                "no_visible_bees_requires_excluded_role",
                "No-visible-bees Training Crops can only create excluded Dataset Items in this slice.",
                409,
            )
        return
    if crop.visible_bee_status != VisibleBeeStatus.has_visible_bees or ellipse_count == 0:
        raise DomainError(
            "reviewed_visible_bees_required",
            "Dataset Items for bee detector training require reviewed visible bee ellipses.",
            409,
        )


def _dataset_item_provenance_for_training_crop(
    store: InMemoryProductDataStore,
    crop: TrainingCropResponse,
) -> DatasetItemProvenanceResponse:
    photo = store.inspection_photos.get(crop.inspection_photo_id)
    inspection = store.inspections.get(photo.inspection_id) if photo else None
    hive = store.hives.get(inspection.hive_id) if inspection else None
    apiary = store.apiaries.get(hive.apiary_id) if hive else None
    return DatasetItemProvenanceResponse(
        workspace_id=crop.workspace_id,
        apiary_id=apiary.apiary_id if apiary else None,
        hive_id=hive.hive_id if hive else None,
        inspection_id=inspection.inspection_id if inspection else None,
        inspection_photo_id=crop.inspection_photo_id,
        training_crop_id=crop.training_crop_id,
        hive_configuration=_hive_configuration_snapshot(store, hive.hive_id if hive else None),
    )


def _hive_configuration_snapshot(
    store: InMemoryProductDataStore,
    hive_id: UUID | None,
) -> HiveConfigurationSnapshotResponse | None:
    if hive_id is None:
        return None
    configuration = store.hive_configurations.get(hive_id)
    if configuration is None:
        return None
    frame_standard = configuration.frame_standard
    return HiveConfigurationSnapshotResponse(
        hive_configuration_id=configuration.hive_configuration_id,
        hive_type=configuration.hive_type,
        frame_use=configuration.frame_use,
        frame_standard_id=configuration.frame_standard_id,
        frame_standard_display_name=frame_standard.display_name,
        top_bar_length_mm=frame_standard.top_bar_length_mm,
        bottom_bar_length_mm=frame_standard.bottom_bar_length_mm,
        side_bar_height_mm=frame_standard.side_bar_height_mm,
    )


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
