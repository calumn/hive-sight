from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from math import cos, radians, sin, sqrt
from uuid import UUID, uuid4

from hive_sight_core_api.models import (
    AnalysisResultResponse,
    AnalysisRunResponse,
    AnalysisRunStatus,
    AnnotationCreate,
    AnnotationResponse,
    AnnotationType,
    AnnotationWorkflowType,
    ApiaryResponse,
    DatasetExclusionReason,
    DatasetItemResponse,
    DatasetItemProvenanceResponse,
    DatasetLabellingSessionResponse,
    DatasetLabellingSessionStatus,
    DatasetRole,
    DataUseAgreementStatus,
    DevSessionResponse,
    HiveResponse,
    ImageQualityStatus,
    InspectionIntent,
    InspectionPhotoEvidenceResponse,
    InspectionPhotoListResponse,
    InspectionPhotoResponse,
    InspectionResponse,
    OrientedBeeEllipseCreateRequest,
    OrientedBeeEllipseResponse,
    OrientedBeeEllipseUpdateRequest,
    PrelabelerRunResponse,
    ReviewedEllipseSnapshot,
    ReviewDecisionResponse,
    ReviewDecisionValue,
    ReviewSubjectType,
    TrainingCropCreateRequest,
    TrainingCropDatasetItemCreateRequest,
    TrainingCropEvidenceResponse,
    TrainingCropExclusionReason,
    TrainingCropListResponse,
    TrainingCropResponse,
    TrainingCropReviewStatus,
    TrainingCropUpdateRequest,
    UploadStatus,
    VisibleBeeStatus,
    WorkspaceDataUseAgreementAcceptanceResponse,
    YoloObbExcludedItem,
    YoloObbExportResponse,
    YoloObbImageEntry,
    YoloObbLabelEntry,
)

DEFAULT_DEV_REVIEWER_USER_ID = UUID("00000000-0000-0000-0000-000000000101")
DEFAULT_DEV_DATASET_CURATOR_USER_ID = UUID("00000000-0000-0000-0000-000000000101")


@dataclass(frozen=True)
class UserContext:
    user_id: UUID


@dataclass(frozen=True)
class WorkspaceRecord:
    workspace_id: UUID
    data_use_agreement_status: DataUseAgreementStatus = DataUseAgreementStatus.missing
    data_use_agreement_terms_version: str | None = None
    data_use_agreement_accepted_at: datetime | None = None


@dataclass(frozen=True)
class WorkspaceMembershipRecord:
    user_id: UUID
    workspace_id: UUID
    role: str = "owner"
    status: str = "active"


@dataclass
class InMemoryObjectStorage:
    objects: dict[str, bytes] = field(default_factory=dict)

    def put_object(self, object_key: str, body: bytes) -> None:
        self.objects[object_key] = body

    def get_object(self, object_key: str) -> bytes | None:
        return self.objects.get(object_key)


@dataclass
class InMemoryEventRecorder:
    analysis_requested: list[AnalysisRunResponse] = field(default_factory=list)

    def record_analysis_requested(self, analysis_run: AnalysisRunResponse) -> None:
        self.analysis_requested.append(analysis_run)


@dataclass
class InMemoryProductDataStore:
    id_factory: Callable[[], UUID] = uuid4
    clock: Callable[[], datetime] = lambda: datetime.now(UTC)
    users: set[UUID] = field(default_factory=set)
    workspaces: dict[UUID, WorkspaceRecord] = field(default_factory=dict)
    memberships: list[WorkspaceMembershipRecord] = field(default_factory=list)
    apiaries: dict[UUID, ApiaryResponse] = field(default_factory=dict)
    hives: dict[UUID, HiveResponse] = field(default_factory=dict)
    inspections: dict[UUID, InspectionResponse] = field(default_factory=dict)
    inspection_photos: dict[UUID, InspectionPhotoResponse] = field(default_factory=dict)
    analysis_runs: dict[UUID, AnalysisRunResponse] = field(default_factory=dict)
    analysis_results: dict[UUID, AnalysisResultResponse] = field(default_factory=dict)
    annotations: dict[UUID, AnnotationResponse] = field(default_factory=dict)
    review_decisions: dict[UUID, ReviewDecisionResponse] = field(default_factory=dict)
    dataset_labelling_sessions: dict[UUID, DatasetLabellingSessionResponse] = field(
        default_factory=dict
    )
    dataset_items: dict[UUID, DatasetItemResponse] = field(default_factory=dict)
    training_crops: dict[UUID, TrainingCropResponse] = field(default_factory=dict)
    training_crop_ellipses: dict[UUID, OrientedBeeEllipseResponse] = field(default_factory=dict)
    reviewer_user_ids: set[UUID] = field(
        default_factory=lambda: {DEFAULT_DEV_REVIEWER_USER_ID}
    )
    dataset_curator_user_ids: set[UUID] = field(
        default_factory=lambda: {DEFAULT_DEV_DATASET_CURATOR_USER_ID}
    )

    def ensure_dev_session(self, user_id: UUID) -> DevSessionResponse:
        self.users.add(user_id)
        membership = self._active_membership_for_user(user_id)
        if membership is None:
            workspace_id = self.id_factory()
            self.workspaces[workspace_id] = WorkspaceRecord(workspace_id=workspace_id)
            membership = WorkspaceMembershipRecord(user_id=user_id, workspace_id=workspace_id)
            self.memberships.append(membership)

        workspace = self.workspaces[membership.workspace_id]
        return DevSessionResponse(
            user_id=user_id,
            workspace_id=workspace.workspace_id,
            role=membership.role,
            reviewer_capability=user_id in self.reviewer_user_ids,
            dataset_curator_capability=user_id in self.dataset_curator_user_ids,
            workspace_data_use_agreement_status=workspace.data_use_agreement_status,
            workspace_data_use_agreement_terms_version=workspace.data_use_agreement_terms_version,
        )

    def accept_data_use_agreement(
        self,
        user: UserContext,
        workspace_id: UUID,
        terms_version: str,
    ) -> WorkspaceDataUseAgreementAcceptanceResponse:
        self.require_workspace_access(user, workspace_id)
        accepted_at = self.clock()
        self.workspaces[workspace_id] = WorkspaceRecord(
            workspace_id=workspace_id,
            data_use_agreement_status=DataUseAgreementStatus.accepted,
            data_use_agreement_terms_version=terms_version,
            data_use_agreement_accepted_at=accepted_at,
        )
        return WorkspaceDataUseAgreementAcceptanceResponse(
            workspace_id=workspace_id,
            status=DataUseAgreementStatus.accepted,
            terms_version=terms_version,
            accepted_at=accepted_at,
        )

    def create_apiary(self, user: UserContext, workspace_id: UUID, name: str) -> ApiaryResponse:
        self.require_workspace_access(user, workspace_id)
        apiary = ApiaryResponse(
            apiary_id=self.id_factory(),
            workspace_id=workspace_id,
            name=name,
        )
        self.apiaries[apiary.apiary_id] = apiary
        return apiary

    def create_hive(self, user: UserContext, apiary_id: UUID, name: str) -> HiveResponse:
        apiary = self.apiaries.get(apiary_id)
        if apiary is None:
            raise DomainError("inspection_not_found", "The requested apiary was not found.", 404)
        self.require_workspace_access(user, apiary.workspace_id)
        hive = HiveResponse(
            hive_id=self.id_factory(),
            apiary_id=apiary_id,
            workspace_id=apiary.workspace_id,
            name=name,
        )
        self.hives[hive.hive_id] = hive
        return hive

    def create_inspection(
        self,
        user: UserContext,
        hive_id: UUID,
        inspection_date: date,
        intent: InspectionIntent,
    ) -> InspectionResponse:
        hive = self.hives.get(hive_id)
        if hive is None:
            raise DomainError("inspection_not_found", "The requested hive was not found.", 404)
        self.require_workspace_access(user, hive.workspace_id)
        inspection = InspectionResponse(
            inspection_id=self.id_factory(),
            hive_id=hive_id,
            workspace_id=hive.workspace_id,
            inspection_date=inspection_date,
            intent=intent,
        )
        self.inspections[inspection.inspection_id] = inspection
        return inspection

    def update_inspection_intent(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_id: UUID,
        intent: InspectionIntent,
    ) -> InspectionResponse:
        self.require_workspace_access(user, workspace_id)
        inspection = self.require_inspection(workspace_id, inspection_id)
        if any(photo.inspection_id == inspection_id for photo in self.inspection_photos.values()):
            raise DomainError(
                "inspection_intent_locked",
                "Inspection intent cannot be changed after photos have been uploaded.",
                409,
            )
        updated = inspection.model_copy(update={"intent": intent})
        self.inspections[updated.inspection_id] = updated
        return updated

    def require_workspace_access(self, user: UserContext, workspace_id: UUID) -> None:
        if workspace_id not in self.workspaces:
            raise DomainError(
                "workspace_access_denied",
                "The current User does not have access to this Workspace.",
                403,
            )
        for membership in self.memberships:
            if (
                membership.user_id == user.user_id
                and membership.workspace_id == workspace_id
                and membership.status == "active"
                and membership.role == "owner"
            ):
                return
        raise DomainError(
            "workspace_access_denied",
            "The current User does not have access to this Workspace.",
            403,
        )

    def require_data_use_agreement(self, workspace_id: UUID) -> None:
        workspace = self.workspaces[workspace_id]
        if workspace.data_use_agreement_status != DataUseAgreementStatus.accepted:
            raise DomainError(
                "data_use_agreement_required",
                "Accept the Workspace Data Use Agreement before uploading inspection photos.",
                403,
            )

    def require_inspection(self, workspace_id: UUID, inspection_id: UUID) -> InspectionResponse:
        inspection = self.inspections.get(inspection_id)
        if inspection is None or inspection.workspace_id != workspace_id:
            raise DomainError(
                "inspection_not_found",
                "The requested Inspection was not found in this Workspace.",
                404,
            )
        return inspection

    def record_inspection_photo(
        self,
        inspection_photo_id: UUID,
        workspace_id: UUID,
        inspection_id: UUID,
        original_object_key: str,
        filename: str,
        content_type: str,
        size_bytes: int,
        uploaded_by_user_id: UUID,
    ) -> InspectionPhotoResponse:
        photo = InspectionPhotoResponse(
            inspection_photo_id=inspection_photo_id,
            inspection_id=inspection_id,
            workspace_id=workspace_id,
            original_object_key=original_object_key,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            upload_status=UploadStatus.accepted,
            uploaded_by_user_id=uploaded_by_user_id,
            uploaded_at=self.clock(),
        )
        self.inspection_photos[inspection_photo_id] = photo
        return photo

    def list_inspection_photos(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_id: UUID,
    ) -> InspectionPhotoListResponse:
        self.require_workspace_access(user, workspace_id)
        self.require_data_use_agreement(workspace_id)
        inspection = self.require_inspection(workspace_id, inspection_id)
        photos = [
            photo
            for photo in self.inspection_photos.values()
            if photo.workspace_id == workspace_id and photo.inspection_id == inspection_id
        ]
        photos.sort(key=lambda photo: photo.uploaded_at)
        return InspectionPhotoListResponse(inspection=inspection, photos=photos)

    def record_analysis_run(self, analysis_run: AnalysisRunResponse) -> AnalysisRunResponse:
        self.analysis_runs[analysis_run.analysis_run_id] = analysis_run
        return analysis_run

    def get_analysis_run(self, analysis_run_id: UUID) -> AnalysisRunResponse | None:
        return self.analysis_runs.get(analysis_run_id)

    def require_analysis_run(
        self,
        user: UserContext,
        workspace_id: UUID,
        analysis_run_id: UUID,
    ) -> AnalysisRunResponse:
        self.require_workspace_access(user, workspace_id)
        self.require_data_use_agreement(workspace_id)
        analysis_run = self.analysis_runs.get(analysis_run_id)
        if analysis_run is None or analysis_run.workspace_id != workspace_id:
            raise DomainError(
                "analysis_run_not_found",
                "The requested Analysis Run was not found in this Workspace.",
                404,
            )
        return analysis_run

    def require_queued_analysis_run(
        self,
        user: UserContext,
        workspace_id: UUID,
        analysis_run_id: UUID,
    ) -> AnalysisRunResponse:
        analysis_run = self.require_analysis_run(user, workspace_id, analysis_run_id)
        if analysis_run.status != AnalysisRunStatus.queued:
            raise DomainError(
                "analysis_run_not_queued",
                "Only queued Analysis Runs can be processed by this demo action.",
                409,
            )
        return analysis_run

    def mark_analysis_running(
        self,
        analysis_run: AnalysisRunResponse,
        started_at: datetime,
    ) -> AnalysisRunResponse:
        updated = analysis_run.model_copy(
            update={
                "status": AnalysisRunStatus.running,
                "started_at": started_at,
                "message": "Analysis is being processed by the private Analysis Service.",
            }
        )
        self.analysis_runs[updated.analysis_run_id] = updated
        return updated

    def complete_analysis_run(
        self,
        analysis_run: AnalysisRunResponse,
        model_version: str,
        complete_visible_bee_count: int,
        partial_visible_bee_count: int,
        likely_varroa_detections: int,
        tagged_image_object_key: str | None,
        annotations: list[AnnotationCreate],
        completed_at: datetime,
    ) -> AnalysisRunResponse:
        result = AnalysisResultResponse(
            analysis_result_id=self.id_factory(),
            analysis_run_id=analysis_run.analysis_run_id,
            inspection_photo_id=analysis_run.inspection_photo_id,
            workspace_id=analysis_run.workspace_id,
            model_version=model_version,
            complete_visible_bee_count=complete_visible_bee_count,
            partial_visible_bee_count=partial_visible_bee_count,
            likely_varroa_detections=likely_varroa_detections,
            tagged_image_object_key=tagged_image_object_key,
            result_kind="deterministic_stub",
            completed_at=completed_at,
        )
        self.analysis_results[analysis_run.analysis_run_id] = result
        for annotation in annotations:
            annotation_record = AnnotationResponse(
                annotation_id=self.id_factory(),
                workspace_id=analysis_run.workspace_id,
                inspection_photo_id=analysis_run.inspection_photo_id,
                analysis_result_id=result.analysis_result_id,
                labelling_session_id=None,
                workflow_type=AnnotationWorkflowType.analysis_result,
                annotation_type=annotation.annotation_type,
                x=annotation.x,
                y=annotation.y,
                width=annotation.width,
                height=annotation.height,
                coordinate_space=annotation.coordinate_space,
                source_image_width_px=annotation.source_image_width_px,
                source_image_height_px=annotation.source_image_height_px,
                confidence=annotation.confidence,
                source=annotation.source,
                created_at=completed_at,
            )
            self.annotations[annotation_record.annotation_id] = annotation_record
        updated = analysis_run.model_copy(
            update={
                "status": AnalysisRunStatus.completed,
                "completed_at": completed_at,
                "model_version": model_version,
                "message": "Analysis completed with a deterministic stub result.",
            }
        )
        self.analysis_runs[updated.analysis_run_id] = updated
        return updated

    def fail_analysis_run(
        self,
        analysis_run: AnalysisRunResponse,
        failure_code: str,
        failure_message: str,
        failed_at: datetime,
    ) -> AnalysisRunResponse:
        updated = analysis_run.model_copy(
            update={
                "status": AnalysisRunStatus.failed,
                "failed_at": failed_at,
                "failure_code": failure_code,
                "failure_message": failure_message,
                "message": failure_message,
            }
        )
        self.analysis_runs[updated.analysis_run_id] = updated
        return updated

    def get_analysis_result(self, analysis_run_id: UUID) -> AnalysisResultResponse | None:
        return self.analysis_results.get(analysis_run_id)

    def get_annotations_for_result(self, analysis_result_id: UUID) -> list[AnnotationResponse]:
        return [
            annotation.model_copy(
                update={
                    "latest_review_decision": self.latest_review_decision_for_subject(
                        annotation.annotation_id
                    )
                }
            )
            for annotation in self.annotations.values()
            if annotation.analysis_result_id == analysis_result_id
        ]

    def get_annotations_for_labelling_session(
        self,
        labelling_session_id: UUID,
    ) -> list[AnnotationResponse]:
        return [
            annotation.model_copy(
                update={
                    "latest_review_decision": self.latest_review_decision_for_subject(
                        annotation.annotation_id
                    )
                }
            )
            for annotation in self.annotations.values()
            if annotation.labelling_session_id == labelling_session_id
        ]

    def get_dataset_item_for_labelling_session(
        self,
        labelling_session_id: UUID,
    ) -> DatasetItemResponse | None:
        for dataset_item in self.dataset_items.values():
            if dataset_item.labelling_session_id == labelling_session_id:
                return dataset_item
        return None

    def record_review_decision(
        self,
        user: UserContext,
        workspace_id: UUID,
        subject_type: ReviewSubjectType,
        subject_id: UUID,
        decision: ReviewDecisionValue,
        notes: str | None,
    ) -> ReviewDecisionResponse:
        self.require_workspace_access(user, workspace_id)
        self.require_data_use_agreement(workspace_id)
        if subject_type != ReviewSubjectType.annotation:
            raise DomainError(
                "invalid_review_subject",
                "Review Decisions can only be recorded for Annotations.",
                422,
            )
        annotation = self.annotations.get(subject_id)
        if annotation is None or annotation.workspace_id != workspace_id:
            raise DomainError(
                "annotation_not_found",
                "The requested Annotation was not found in this Workspace.",
                404,
            )
        if annotation.workflow_type == AnnotationWorkflowType.dataset_labelling:
            self.require_dataset_curator_capability(user)
        else:
            self.require_reviewer_capability(user)
        review_decision = ReviewDecisionResponse(
            review_decision_id=self.id_factory(),
            workspace_id=workspace_id,
            reviewer_id=user.user_id,
            subject_type=subject_type,
            subject_id=subject_id,
            decision=decision,
            notes=notes,
            created_at=self.clock(),
        )
        self.review_decisions[review_decision.review_decision_id] = review_decision
        if annotation.labelling_session_id is not None:
            self.mark_labelling_session_review_in_progress(annotation.labelling_session_id)
        return review_decision

    def latest_review_decision_for_subject(
        self,
        subject_id: UUID,
    ) -> ReviewDecisionResponse | None:
        decisions = []
        for index, review_decision in enumerate(self.review_decisions.values()):
            if (
                review_decision.subject_type == ReviewSubjectType.annotation
                and review_decision.subject_id == subject_id
            ):
                decisions.append((index, review_decision))
        if not decisions:
            return None
        return max(
            decisions,
            key=lambda indexed_decision: (
                indexed_decision[1].created_at,
                indexed_decision[0],
            ),
        )[1]

    def require_reviewer_capability(self, user: UserContext) -> None:
        if user.user_id in self.reviewer_user_ids:
            return
        raise DomainError(
            "reviewer_access_required",
            "Internal reviewer capability is required to record Review Decisions.",
            403,
        )

    def require_dataset_curator_capability(self, user: UserContext) -> None:
        if user.user_id in self.dataset_curator_user_ids:
            return
        raise DomainError(
            "dataset_curator_access_required",
            "Internal dataset curator capability is required for dataset labelling.",
            403,
        )

    def require_inspection_photo_for_labelling(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_photo_id: UUID,
    ) -> InspectionPhotoResponse:
        self.require_workspace_access(user, workspace_id)
        self.require_data_use_agreement(workspace_id)
        photo = self.inspection_photos.get(inspection_photo_id)
        if photo is None or photo.workspace_id != workspace_id:
            raise DomainError(
                "inspection_photo_not_found",
                "The requested Inspection Photo was not found in this Workspace.",
                404,
            )
        inspection = self.require_inspection(workspace_id, photo.inspection_id)
        if inspection.intent != InspectionIntent.training_data_collection:
            raise DomainError(
                "inspection_intent_not_for_dataset_labelling",
                "Dataset labelling is available only for training data collection Inspections.",
                409,
            )
        return photo

    def require_inspection_photo_for_training_crop(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_photo_id: UUID,
    ) -> InspectionPhotoResponse:
        self.require_workspace_access(user, workspace_id)
        self.require_data_use_agreement(workspace_id)
        self.require_dataset_curator_capability(user)
        photo = self.inspection_photos.get(inspection_photo_id)
        if photo is None or photo.workspace_id != workspace_id:
            raise DomainError(
                "inspection_photo_not_found",
                "The requested Inspection Photo was not found in this Workspace.",
                404,
            )
        inspection = self.require_inspection(workspace_id, photo.inspection_id)
        if inspection.intent != InspectionIntent.training_data_collection:
            raise DomainError(
                "inspection_intent_not_for_training_crop",
                "Training Crops can be created only from training data collection Inspections.",
                409,
            )
        return photo

    def create_training_crop(
        self,
        user: UserContext,
        request: TrainingCropCreateRequest,
    ) -> TrainingCropResponse:
        self.require_inspection_photo_for_training_crop(
            user=user,
            workspace_id=request.workspace_id,
            inspection_photo_id=request.inspection_photo_id,
        )
        self._validate_crop_bounds(
            crop_x=request.crop_x,
            crop_y=request.crop_y,
            crop_width=request.crop_width,
            crop_height=request.crop_height,
            source_image_width_px=request.source_image_width_px,
            source_image_height_px=request.source_image_height_px,
        )
        created_at = self.clock()
        crop = TrainingCropResponse(
            training_crop_id=self.id_factory(),
            workspace_id=request.workspace_id,
            inspection_photo_id=request.inspection_photo_id,
            crop_x=request.crop_x,
            crop_y=request.crop_y,
            crop_width=request.crop_width,
            crop_height=request.crop_height,
            coordinate_space="source_image_pixels",
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
        self.training_crops[crop.training_crop_id] = crop
        return crop

    def list_training_crops_for_photo(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_photo_id: UUID,
    ) -> TrainingCropListResponse:
        photo = self.require_inspection_photo_for_training_crop(
            user=user,
            workspace_id=workspace_id,
            inspection_photo_id=inspection_photo_id,
        )
        crops = [
            crop
            for crop in self.training_crops.values()
            if crop.workspace_id == workspace_id and crop.inspection_photo_id == inspection_photo_id
        ]
        crops.sort(key=lambda crop: crop.created_at)
        return TrainingCropListResponse(inspection_photo=photo, training_crops=crops)

    def update_training_crop(
        self,
        user: UserContext,
        training_crop_id: UUID,
        request: TrainingCropUpdateRequest,
    ) -> TrainingCropResponse:
        crop = self.require_training_crop(
            user=user,
            workspace_id=request.workspace_id,
            training_crop_id=training_crop_id,
        )
        self._require_crop_editable(crop)
        existing_ellipses = self.get_ellipses_for_training_crop(training_crop_id)
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

        self._validate_crop_bounds(
            crop_x=next_values["crop_x"],
            crop_y=next_values["crop_y"],
            crop_width=next_values["crop_width"],
            crop_height=next_values["crop_height"],
            source_image_width_px=crop.source_image_width_px,
            source_image_height_px=crop.source_image_height_px,
        )
        self._validate_crop_review_state(
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
                "updated_at": self.clock(),
            }
        )
        self.training_crops[updated.training_crop_id] = updated
        return updated

    def create_training_crop_ellipse(
        self,
        user: UserContext,
        training_crop_id: UUID,
        request: OrientedBeeEllipseCreateRequest,
    ) -> OrientedBeeEllipseResponse:
        crop = self.require_training_crop(
            user=user,
            workspace_id=request.workspace_id,
            training_crop_id=training_crop_id,
        )
        self._require_crop_editable(crop)
        if crop.visible_bee_status == VisibleBeeStatus.no_visible_bees:
            raise DomainError(
                "no_visible_bees_conflicts_with_ellipses",
                "A no-visible-bees Training Crop cannot retain bee ellipses.",
                409,
            )
        self._validate_bee_annotation_type(request.annotation_type)
        rotation = _normalize_rotation(request.rotation_degrees)
        self._validate_ellipse_inside_crop(
            crop=crop,
            center_x=request.center_x,
            center_y=request.center_y,
            radius_x=request.radius_x,
            radius_y=request.radius_y,
            rotation_degrees=rotation,
        )
        created_at = self.clock()
        ellipse = OrientedBeeEllipseResponse(
            annotation_id=self.id_factory(),
            workspace_id=request.workspace_id,
            inspection_photo_id=crop.inspection_photo_id,
            training_crop_id=training_crop_id,
            annotation_type=request.annotation_type,
            center_x=request.center_x,
            center_y=request.center_y,
            radius_x=request.radius_x,
            radius_y=request.radius_y,
            rotation_degrees=rotation,
            coordinate_space="source_image_pixels",
            source_image_width_px=crop.source_image_width_px,
            source_image_height_px=crop.source_image_height_px,
            source="human_from_scratch",
            created_by_user_id=user.user_id,
            created_at=created_at,
            updated_at=created_at,
        )
        self.training_crop_ellipses[ellipse.annotation_id] = ellipse
        if crop.visible_bee_status == VisibleBeeStatus.unassessed:
            updated_crop = crop.model_copy(
                update={
                    "visible_bee_status": VisibleBeeStatus.has_visible_bees,
                    "updated_at": created_at,
                }
            )
            self.training_crops[updated_crop.training_crop_id] = updated_crop
        return ellipse

    def update_training_crop_ellipse(
        self,
        user: UserContext,
        annotation_id: UUID,
        request: OrientedBeeEllipseUpdateRequest,
    ) -> OrientedBeeEllipseResponse:
        ellipse = self.training_crop_ellipses.get(annotation_id)
        if ellipse is None or ellipse.workspace_id != request.workspace_id:
            raise DomainError(
                "ellipse_not_found",
                "The requested oriented bee ellipse was not found in this Workspace.",
                404,
            )
        crop = self.require_training_crop(
            user=user,
            workspace_id=request.workspace_id,
            training_crop_id=ellipse.training_crop_id,
        )
        self._require_crop_editable(crop)
        annotation_type = request.annotation_type or ellipse.annotation_type
        self._validate_bee_annotation_type(annotation_type)
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
        self._validate_ellipse_inside_crop(crop=crop, **next_values)
        updated = ellipse.model_copy(update={**next_values, "updated_at": self.clock()})
        self.training_crop_ellipses[updated.annotation_id] = updated
        return updated

    def delete_training_crop_ellipse(
        self,
        user: UserContext,
        workspace_id: UUID,
        annotation_id: UUID,
    ) -> None:
        ellipse = self.training_crop_ellipses.get(annotation_id)
        if ellipse is None or ellipse.workspace_id != workspace_id:
            raise DomainError(
                "ellipse_not_found",
                "The requested oriented bee ellipse was not found in this Workspace.",
                404,
            )
        crop = self.require_training_crop(
            user=user,
            workspace_id=workspace_id,
            training_crop_id=ellipse.training_crop_id,
        )
        self._require_crop_editable(crop)
        del self.training_crop_ellipses[annotation_id]

    def get_training_crop_evidence(
        self,
        user: UserContext,
        workspace_id: UUID,
        training_crop_id: UUID,
    ) -> TrainingCropEvidenceResponse:
        crop = self.require_training_crop(
            user=user,
            workspace_id=workspace_id,
            training_crop_id=training_crop_id,
        )
        photo = self.require_inspection_photo_for_training_crop(
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
            bee_ellipses=self.get_ellipses_for_training_crop(training_crop_id),
            caveat=(
                "Training Crop annotations are human-created review evidence. "
                "Dataset use is assigned later through Bee Annotation Repository workflows."
            ),
        )

    def require_training_crop(
        self,
        user: UserContext,
        workspace_id: UUID,
        training_crop_id: UUID,
    ) -> TrainingCropResponse:
        self.require_workspace_access(user, workspace_id)
        self.require_data_use_agreement(workspace_id)
        self.require_dataset_curator_capability(user)
        crop = self.training_crops.get(training_crop_id)
        if crop is None or crop.workspace_id != workspace_id:
            raise DomainError(
                "training_crop_not_found",
                "The requested Training Crop was not found in this Workspace.",
                404,
            )
        return crop

    def get_ellipses_for_training_crop(
        self,
        training_crop_id: UUID,
    ) -> list[OrientedBeeEllipseResponse]:
        ellipses = [
            ellipse
            for ellipse in self.training_crop_ellipses.values()
            if ellipse.training_crop_id == training_crop_id
        ]
        ellipses.sort(key=lambda ellipse: ellipse.created_at)
        return ellipses

    def _validate_crop_bounds(
        self,
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
        self,
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

    def _validate_bee_annotation_type(self, annotation_type: AnnotationType) -> None:
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
        self,
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

    def _require_crop_editable(self, crop: TrainingCropResponse) -> None:
        if crop.review_status in {
            TrainingCropReviewStatus.review_complete,
            TrainingCropReviewStatus.excluded,
        }:
            raise DomainError(
                "training_crop_locked",
                "Completed or excluded Training Crops are locked in this slice.",
                409,
            )

    def existing_labelling_session_for_photo(
        self,
        workspace_id: UUID,
        inspection_photo_id: UUID,
    ) -> DatasetLabellingSessionResponse | None:
        for session in self.dataset_labelling_sessions.values():
            if (
                session.workspace_id == workspace_id
                and session.inspection_photo_id == inspection_photo_id
            ):
                return session
        return None

    def record_dataset_labelling_session(
        self,
        workspace_id: UUID,
        inspection_photo_id: UUID,
        created_by_user_id: UUID,
        prelabeler_run: PrelabelerRunResponse,
        created_at: datetime,
    ) -> DatasetLabellingSessionResponse:
        status = (
            DatasetLabellingSessionStatus.draft_ready
            if prelabeler_run.status == "succeeded"
            else DatasetLabellingSessionStatus.prelabel_failed
        )
        session = DatasetLabellingSessionResponse(
            labelling_session_id=self.id_factory(),
            workspace_id=workspace_id,
            inspection_photo_id=inspection_photo_id,
            created_by_user_id=created_by_user_id,
            status=status,
            source_group_key=None,
            image_quality_status=ImageQualityStatus.unassessed,
            prelabeler_run=prelabeler_run,
            created_at=created_at,
            updated_at=created_at,
        )
        self.dataset_labelling_sessions[session.labelling_session_id] = session
        return session

    def record_dataset_labelling_annotation(
        self,
        workspace_id: UUID,
        inspection_photo_id: UUID,
        labelling_session_id: UUID,
        annotation: AnnotationCreate,
        created_at: datetime,
    ) -> AnnotationResponse:
        if annotation.annotation_type not in {
            AnnotationType.complete_visible_bee,
            AnnotationType.partial_visible_bee,
        }:
            raise DomainError(
                "unsupported_annotation_type",
                "Slice 5 dataset labelling supports complete and partial visible bee annotations.",
                422,
            )
        annotation_record = AnnotationResponse(
            annotation_id=self.id_factory(),
            workspace_id=workspace_id,
            inspection_photo_id=inspection_photo_id,
            analysis_result_id=None,
            labelling_session_id=labelling_session_id,
            workflow_type=AnnotationWorkflowType.dataset_labelling,
            annotation_type=annotation.annotation_type,
            x=annotation.x,
            y=annotation.y,
            width=annotation.width,
            height=annotation.height,
            coordinate_space=annotation.coordinate_space,
            source_image_width_px=annotation.source_image_width_px,
            source_image_height_px=annotation.source_image_height_px,
            confidence=annotation.confidence,
            source=annotation.source,
            created_at=created_at,
        )
        self.annotations[annotation_record.annotation_id] = annotation_record
        return annotation_record

    def require_labelling_session(
        self,
        user: UserContext,
        workspace_id: UUID,
        labelling_session_id: UUID,
    ) -> DatasetLabellingSessionResponse:
        self.require_workspace_access(user, workspace_id)
        self.require_data_use_agreement(workspace_id)
        self.require_dataset_curator_capability(user)
        session = self.dataset_labelling_sessions.get(labelling_session_id)
        if session is None or session.workspace_id != workspace_id:
            raise DomainError(
                "labelling_session_not_found",
                "The requested Dataset Labelling Session was not found in this Workspace.",
                404,
            )
        return session

    def update_labelling_session_metadata(
        self,
        user: UserContext,
        workspace_id: UUID,
        labelling_session_id: UUID,
        source_group_key: str | None,
        image_quality_status: ImageQualityStatus,
    ) -> DatasetLabellingSessionResponse:
        session = self.require_labelling_session(user, workspace_id, labelling_session_id)
        cleaned_group_key = source_group_key.strip() if source_group_key else None
        updated = session.model_copy(
            update={
                "source_group_key": cleaned_group_key or None,
                "image_quality_status": image_quality_status,
                "updated_at": self.clock(),
            }
        )
        self.dataset_labelling_sessions[updated.labelling_session_id] = updated
        return updated

    def mark_labelling_session_review_in_progress(
        self,
        labelling_session_id: UUID,
    ) -> None:
        session = self.dataset_labelling_sessions.get(labelling_session_id)
        if session is None or session.status == DatasetLabellingSessionStatus.prelabel_failed:
            return
        if session.status == DatasetLabellingSessionStatus.review_in_progress:
            return
        updated = session.model_copy(
            update={
                "status": DatasetLabellingSessionStatus.review_in_progress,
                "updated_at": self.clock(),
            }
        )
        self.dataset_labelling_sessions[updated.labelling_session_id] = updated

    def record_dataset_item(
        self,
        user: UserContext,
        workspace_id: UUID,
        labelling_session_id: UUID,
        dataset_role: DatasetRole,
        reviewed_annotation_ids: list[UUID],
        assignment_note: str | None,
        exclusion_reason: DatasetExclusionReason | None,
    ) -> DatasetItemResponse:
        session = self.require_labelling_session(user, workspace_id, labelling_session_id)
        existing = self.get_dataset_item_for_labelling_session(labelling_session_id)
        if existing is not None:
            raise DomainError(
                "dataset_item_already_assigned",
                "This Dataset Labelling Session has already been assigned to a Dataset Item.",
                409,
            )
        dataset_item = DatasetItemResponse(
            dataset_item_id=self.id_factory(),
            workspace_id=workspace_id,
            inspection_photo_id=session.inspection_photo_id,
            labelling_session_id=labelling_session_id,
            training_crop_id=None,
            source_evidence_type="dataset_labelling_session",
            dataset_role=dataset_role,
            reviewed_annotation_ids=reviewed_annotation_ids,
            reviewed_ellipse_snapshots=[],
            source_group_key=session.source_group_key,
            image_quality_status=session.image_quality_status,
            provenance=DatasetItemProvenanceResponse(
                workspace_id=workspace_id,
                inspection_photo_id=session.inspection_photo_id,
            ),
            assigned_by_user_id=user.user_id,
            assigned_at=self.clock(),
            assignment_note=assignment_note,
            exclusion_reason=exclusion_reason,
            benchmark_protected=dataset_role == DatasetRole.benchmark,
        )
        self.dataset_items[dataset_item.dataset_item_id] = dataset_item
        return dataset_item

    def create_dataset_item_from_training_crop(
        self,
        user: UserContext,
        training_crop_id: UUID,
        request: TrainingCropDatasetItemCreateRequest,
    ) -> DatasetItemResponse:
        crop = self.require_training_crop(
            user=user,
            workspace_id=request.workspace_id,
            training_crop_id=training_crop_id,
        )
        cleaned_note = _clean_optional_text(request.assignment_note)
        self._validate_dataset_item_exclusion(
            dataset_role=request.dataset_role,
            assignment_note=cleaned_note,
            exclusion_reason=request.exclusion_reason,
        )
        self._validate_training_crop_dataset_item_state(
            crop=crop,
            dataset_role=request.dataset_role,
        )
        existing = self.get_dataset_item_for_training_crop(training_crop_id)
        if existing is not None:
            raise DomainError(
                "dataset_item_already_assigned",
                "This Training Crop has already been assigned to a Dataset Item.",
                409,
            )

        ellipses = self.get_ellipses_for_training_crop(training_crop_id)
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
                created_by_user_id=ellipse.created_by_user_id,
                created_at=ellipse.created_at,
                updated_at=ellipse.updated_at,
            )
            for ellipse in ellipses
        ]
        provenance = self._dataset_item_provenance_for_training_crop(crop)
        dataset_item = DatasetItemResponse(
            dataset_item_id=self.id_factory(),
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
            source_group_key=None,
            image_quality_status=(
                ImageQualityStatus.exclude
                if request.dataset_role == DatasetRole.excluded
                else ImageQualityStatus.usable
            ),
            provenance=provenance,
            assigned_by_user_id=user.user_id,
            assigned_at=self.clock(),
            assignment_note=cleaned_note,
            exclusion_reason=request.exclusion_reason,
            benchmark_protected=request.dataset_role == DatasetRole.benchmark,
        )
        self.dataset_items[dataset_item.dataset_item_id] = dataset_item
        return dataset_item

    def get_dataset_item_for_training_crop(
        self,
        training_crop_id: UUID,
    ) -> DatasetItemResponse | None:
        for dataset_item in self.dataset_items.values():
            if dataset_item.training_crop_id == training_crop_id:
                return dataset_item
        return None

    def create_yolo_obb_export(
        self,
        user: UserContext,
        workspace_id: UUID,
    ) -> YoloObbExportResponse:
        self.require_workspace_access(user, workspace_id)
        self.require_data_use_agreement(workspace_id)
        self.require_dataset_curator_capability(user)

        included_ids: list[UUID] = []
        protected_benchmark_ids: list[UUID] = []
        excluded_items: list[YoloObbExcludedItem] = []
        image_entries: list[YoloObbImageEntry] = []
        label_entries: list[YoloObbLabelEntry] = []
        training_item_count = 0
        validation_item_count = 0
        benchmark_item_count = 0

        for dataset_item in self.dataset_items.values():
            if dataset_item.workspace_id != workspace_id:
                continue
            if dataset_item.dataset_role == DatasetRole.benchmark:
                benchmark_item_count += 1
                protected_benchmark_ids.append(dataset_item.dataset_item_id)
                continue
            if dataset_item.dataset_role == DatasetRole.excluded:
                excluded_items.append(
                    YoloObbExcludedItem(
                        dataset_item_id=dataset_item.dataset_item_id,
                        training_crop_id=dataset_item.training_crop_id,
                        dataset_role=dataset_item.dataset_role,
                        reason=dataset_item.exclusion_reason or "excluded",
                    )
                )
                continue
            if dataset_item.training_crop_id is None:
                excluded_items.append(
                    YoloObbExcludedItem(
                        dataset_item_id=dataset_item.dataset_item_id,
                        training_crop_id=None,
                        dataset_role=dataset_item.dataset_role,
                        reason="unsupported_source_evidence_type",
                    )
                )
                continue
            if dataset_item.dataset_role == DatasetRole.training:
                training_item_count += 1
            elif dataset_item.dataset_role == DatasetRole.validation:
                validation_item_count += 1

            included_ids.append(dataset_item.dataset_item_id)
            image_entries.append(
                YoloObbImageEntry(
                    dataset_item_id=dataset_item.dataset_item_id,
                    training_crop_id=dataset_item.training_crop_id,
                    inspection_photo_id=dataset_item.inspection_photo_id,
                    split=dataset_item.dataset_role,
                    crop_x=dataset_item.crop_x or 0,
                    crop_y=dataset_item.crop_y or 0,
                    crop_width=dataset_item.crop_width or 0,
                    crop_height=dataset_item.crop_height or 0,
                )
            )
            for ellipse in dataset_item.reviewed_ellipse_snapshots:
                class_id = _yolo_class_id(ellipse.annotation_type)
                points = _ellipse_to_crop_normalized_obb_points(dataset_item, ellipse)
                label_entries.append(
                    YoloObbLabelEntry(
                        dataset_item_id=dataset_item.dataset_item_id,
                        training_crop_id=dataset_item.training_crop_id,
                        annotation_id=ellipse.annotation_id,
                        split=dataset_item.dataset_role,
                        class_id=class_id,
                        class_name=ellipse.annotation_type,
                        label=" ".join([str(class_id), *[f"{point:.6f}" for point in points]]),
                        points=points,
                    )
                )

        return YoloObbExportResponse(
            export_id=self.id_factory(),
            workspace_id=workspace_id,
            export_format="yolo_obb",
            label_convention="class x1 y1 x2 y2 x3 y3 x4 y4",
            coordinate_basis="crop-relative normalized corner points",
            created_by_user_id=user.user_id,
            created_at=self.clock(),
            class_map={"0": "complete_visible_bee", "1": "partial_visible_bee"},
            included_dataset_item_ids=included_ids,
            excluded_dataset_items=excluded_items,
            protected_benchmark_dataset_item_ids=protected_benchmark_ids,
            training_item_count=training_item_count,
            validation_item_count=validation_item_count,
            benchmark_item_count=benchmark_item_count,
            image_entries=image_entries,
            label_entries=label_entries,
            caveat=(
                "YOLO OBB export rows are derived model-training projections. "
                "Reviewed oriented bee ellipses remain the canonical annotation evidence."
            ),
        )

    def _dataset_item_provenance_for_training_crop(
        self,
        crop: TrainingCropResponse,
    ) -> DatasetItemProvenanceResponse:
        photo = self.inspection_photos.get(crop.inspection_photo_id)
        inspection = self.inspections.get(photo.inspection_id) if photo else None
        hive = self.hives.get(inspection.hive_id) if inspection else None
        apiary = self.apiaries.get(hive.apiary_id) if hive else None
        return DatasetItemProvenanceResponse(
            workspace_id=crop.workspace_id,
            apiary_id=apiary.apiary_id if apiary else None,
            hive_id=hive.hive_id if hive else None,
            inspection_id=inspection.inspection_id if inspection else None,
            inspection_photo_id=crop.inspection_photo_id,
            training_crop_id=crop.training_crop_id,
        )

    def _validate_dataset_item_exclusion(
        self,
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
        self,
        crop: TrainingCropResponse,
        dataset_role: DatasetRole,
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
        ellipses = self.get_ellipses_for_training_crop(crop.training_crop_id)
        if crop.visible_bee_status != VisibleBeeStatus.has_visible_bees or not ellipses:
            raise DomainError(
                "reviewed_visible_bees_required",
                "Dataset Items for bee detector training require reviewed visible bee ellipses.",
                409,
            )

    def require_inspection_photo_for_view(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_photo_id: UUID,
    ) -> InspectionPhotoResponse:
        self.require_workspace_access(user, workspace_id)
        self.require_data_use_agreement(workspace_id)
        photo = self.inspection_photos.get(inspection_photo_id)
        if photo is None or photo.workspace_id != workspace_id:
            raise DomainError(
                "photo_view_unavailable",
                "The requested Inspection Photo is not available in this Workspace.",
                404,
            )
        return photo

    def _active_membership_for_user(self, user_id: UUID) -> WorkspaceMembershipRecord | None:
        for membership in self.memberships:
            if membership.user_id == user_id and membership.status == "active":
                return membership
        return None


@dataclass(frozen=True)
class UploadPolicy:
    allowed_content_types: frozenset[str] = frozenset(
        {"image/jpeg", "image/png", "image/webp"}
    )
    max_size_bytes: int = 15 * 1024 * 1024


@dataclass
class DevState:
    store: InMemoryProductDataStore
    object_storage: InMemoryObjectStorage
    event_recorder: InMemoryEventRecorder
    upload_policy: UploadPolicy


class DomainError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def deterministic_id_factory(id_values: list[UUID]) -> Callable[[], UUID]:
    values = list(id_values)

    def next_id() -> UUID:
        if not values:
            return uuid4()
        return values.pop(0)

    return next_id


def _normalize_rotation(rotation_degrees: float) -> float:
    return rotation_degrees % 360


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _yolo_class_id(annotation_type: AnnotationType) -> int:
    if annotation_type == AnnotationType.complete_visible_bee:
        return 0
    if annotation_type == AnnotationType.partial_visible_bee:
        return 1
    raise DomainError(
        "unsupported_yolo_obb_annotation_type",
        "YOLO OBB bee export supports complete and partial visible bee annotations only.",
        422,
    )


def _ellipse_to_crop_normalized_obb_points(
    dataset_item: DatasetItemResponse,
    ellipse: ReviewedEllipseSnapshot,
) -> list[float]:
    if (
        dataset_item.crop_x is None
        or dataset_item.crop_y is None
        or dataset_item.crop_width is None
        or dataset_item.crop_height is None
    ):
        raise DomainError(
            "dataset_item_missing_crop_geometry",
            "YOLO OBB export requires crop-sourced Dataset Items.",
            409,
        )
    crop_center_x = ellipse.center_x - dataset_item.crop_x
    crop_center_y = ellipse.center_y - dataset_item.crop_y
    angle = radians(ellipse.rotation_degrees)
    corners = [
        (-ellipse.radius_x, -ellipse.radius_y),
        (ellipse.radius_x, -ellipse.radius_y),
        (ellipse.radius_x, ellipse.radius_y),
        (-ellipse.radius_x, ellipse.radius_y),
    ]
    points: list[float] = []
    for dx, dy in corners:
        rotated_x = crop_center_x + (dx * cos(angle)) - (dy * sin(angle))
        rotated_y = crop_center_y + (dx * sin(angle)) + (dy * cos(angle))
        points.extend(
            [
                rotated_x / dataset_item.crop_width,
                rotated_y / dataset_item.crop_height,
            ]
        )
    return points
    TrainingCropDatasetItemCreateRequest,
