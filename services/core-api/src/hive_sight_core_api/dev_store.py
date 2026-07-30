from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
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
    DatasetLabellingSessionResponse,
    DatasetLabellingSessionStatus,
    DatasetRole,
    DataUseAgreementStatus,
    DevSessionResponse,
    HiveResponse,
    ImageQualityStatus,
    InspectionIntent,
    InspectionPhotoListResponse,
    InspectionPhotoResponse,
    InspectionResponse,
    PrelabelerRunResponse,
    ReviewDecisionResponse,
    ReviewDecisionValue,
    ReviewSubjectType,
    UploadStatus,
    WorkspaceDataUseAgreementAcceptanceResponse,
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
            dataset_role=dataset_role,
            reviewed_annotation_ids=reviewed_annotation_ids,
            source_group_key=session.source_group_key,
            image_quality_status=session.image_quality_status,
            assigned_by_user_id=user.user_id,
            assigned_at=self.clock(),
            assignment_note=assignment_note,
            exclusion_reason=exclusion_reason,
            benchmark_protected=dataset_role == DatasetRole.benchmark,
        )
        self.dataset_items[dataset_item.dataset_item_id] = dataset_item
        return dataset_item

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
