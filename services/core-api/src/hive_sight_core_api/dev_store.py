import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from hashlib import sha256
from io import BytesIO
from math import cos, radians, sin
from pathlib import Path
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
    DatasetItemProvenanceResponse,
    DatasetItemResponse,
    DatasetLabellingSessionResponse,
    DatasetLabellingSessionStatus,
    DatasetRole,
    DataUseAgreementStatus,
    DevSessionResponse,
    FrameStandardResponse,
    FrameStandardStatus,
    GeneratedDatasetExportFileEntry,
    HiveConfigurationResponse,
    HiveConfigurationSnapshotResponse,
    HiveConfigurationUpsertRequest,
    HiveResponse,
    ImageQualityStatus,
    InspectionIntent,
    InspectionPhotoListResponse,
    InspectionPhotoResponse,
    InspectionResponse,
    OrientedBeeEllipseCreateRequest,
    OrientedBeeEllipseResponse,
    OrientedBeeEllipseUpdateRequest,
    PhysicalYoloObbExportResponse,
    PrelabelerRunResponse,
    ReviewDecisionResponse,
    ReviewDecisionValue,
    ReviewedEllipseSnapshot,
    ReviewSubjectType,
    TrainingCropCreateRequest,
    TrainingCropDatasetItemCreateRequest,
    TrainingCropEvidenceResponse,
    TrainingCropListResponse,
    TrainingCropResponse,
    TrainingCropUpdateRequest,
    UploadStatus,
    WorkspaceDataUseAgreementAcceptanceResponse,
    YoloObbExcludedItem,
    YoloObbExportResponse,
    YoloObbImageEntry,
    YoloObbLabelEntry,
)

try:
    from PIL import Image, UnidentifiedImageError
except ImportError:  # pragma: no cover - dependency is declared for the Core API package.
    Image = None
    UnidentifiedImageError = Exception

DEFAULT_DEV_REVIEWER_USER_ID = UUID("00000000-0000-0000-0000-000000000101")
DEFAULT_DEV_DATASET_CURATOR_USER_ID = UUID("00000000-0000-0000-0000-000000000101")


FRAME_STANDARDS: tuple[FrameStandardResponse, ...] = (
    FrameStandardResponse(frame_standard_id="british_national_shallow_super", display_name="British National shallow super", hive_type="british_national", frame_use="shallow_super", top_bar_length_mm=432, bottom_bar_length_mm=356, side_bar_height_mm=140, source_note="Project-maintained starter metadata for dev traceability; verify before production calibration.", status=FrameStandardStatus.known),
    FrameStandardResponse(frame_standard_id="british_national_deep_brood", display_name="British National deep brood", hive_type="british_national", frame_use="deep_brood", top_bar_length_mm=432, bottom_bar_length_mm=356, side_bar_height_mm=216, source_note="Project-maintained starter metadata for dev traceability; verify before production calibration.", status=FrameStandardStatus.known),
    FrameStandardResponse(frame_standard_id="british_national_extra_deep_14x12", display_name="British National extra deep 14x12", hive_type="british_national", frame_use="extra_deep_14x12", top_bar_length_mm=432, bottom_bar_length_mm=356, side_bar_height_mm=305, source_note="Project-maintained starter metadata for dev traceability; verify before production calibration.", status=FrameStandardStatus.known),
    FrameStandardResponse(frame_standard_id="wbc_shallow_super", display_name="WBC shallow super", hive_type="wbc", frame_use="shallow_super", top_bar_length_mm=432, bottom_bar_length_mm=356, side_bar_height_mm=140, source_note="Project-maintained starter metadata for dev traceability; verify before production calibration.", status=FrameStandardStatus.known),
    FrameStandardResponse(frame_standard_id="wbc_deep_brood", display_name="WBC deep brood", hive_type="wbc", frame_use="deep_brood", top_bar_length_mm=432, bottom_bar_length_mm=356, side_bar_height_mm=216, source_note="Project-maintained starter metadata for dev traceability; verify before production calibration.", status=FrameStandardStatus.known),
    FrameStandardResponse(frame_standard_id="wbc_extra_deep_14x12", display_name="WBC extra deep 14x12", hive_type="wbc", frame_use="extra_deep_14x12", top_bar_length_mm=432, bottom_bar_length_mm=356, side_bar_height_mm=305, source_note="Project-maintained starter metadata for dev traceability; verify before production calibration.", status=FrameStandardStatus.known),
    FrameStandardResponse(frame_standard_id="smith_shallow_super", display_name="Smith shallow super", hive_type="smith", frame_use="shallow_super", top_bar_length_mm=394, bottom_bar_length_mm=356, side_bar_height_mm=140, source_note="Project-maintained starter metadata for dev traceability; verify before production calibration.", status=FrameStandardStatus.known),
    FrameStandardResponse(frame_standard_id="smith_deep_brood", display_name="Smith deep brood", hive_type="smith", frame_use="deep_brood", top_bar_length_mm=394, bottom_bar_length_mm=356, side_bar_height_mm=216, source_note="Project-maintained starter metadata for dev traceability; verify before production calibration.", status=FrameStandardStatus.known),
    FrameStandardResponse(frame_standard_id="british_commercial_shallow_super", display_name="British Commercial shallow super", hive_type="british_commercial", frame_use="shallow_super", top_bar_length_mm=432, bottom_bar_length_mm=406, side_bar_height_mm=152, source_note="Project-maintained starter metadata for dev traceability; verify before production calibration.", status=FrameStandardStatus.known),
    FrameStandardResponse(frame_standard_id="british_commercial_deep_brood", display_name="British Commercial deep brood", hive_type="british_commercial", frame_use="deep_brood", top_bar_length_mm=432, bottom_bar_length_mm=406, side_bar_height_mm=254, source_note="Project-maintained starter metadata for dev traceability; verify before production calibration.", status=FrameStandardStatus.known),
    FrameStandardResponse(frame_standard_id="langstroth_shallow_super", display_name="Langstroth shallow super", hive_type="langstroth", frame_use="shallow_super", top_bar_length_mm=483, bottom_bar_length_mm=447, side_bar_height_mm=137, source_note="Project-maintained starter metadata for dev traceability; verify before production calibration.", status=FrameStandardStatus.known),
    FrameStandardResponse(frame_standard_id="langstroth_deep_brood", display_name="Langstroth deep brood", hive_type="langstroth", frame_use="deep_brood", top_bar_length_mm=483, bottom_bar_length_mm=447, side_bar_height_mm=232, source_note="Project-maintained starter metadata for dev traceability; verify before production calibration.", status=FrameStandardStatus.known),
    FrameStandardResponse(frame_standard_id="unknown", display_name="Unknown", hive_type="unknown", frame_use="unknown", source_note="Explicitly unknown equipment context; count and flag in later training reports.", status=FrameStandardStatus.unknown),
    FrameStandardResponse(frame_standard_id="other", display_name="Other", hive_type="other", frame_use="other", source_note="Equipment context not in the starter catalogue; notes are required.", status=FrameStandardStatus.other),
)


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
    hive_configurations: dict[UUID, HiveConfigurationResponse] = field(default_factory=dict)
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

    def get_hive(self, hive_id: UUID) -> HiveResponse | None:
        return self.hives.get(hive_id)

    def list_frame_standards(self) -> list[FrameStandardResponse]:
        return list(FRAME_STANDARDS)

    def get_frame_standard(self, frame_standard_id: str) -> FrameStandardResponse | None:
        for frame_standard in FRAME_STANDARDS:
            if frame_standard.frame_standard_id == frame_standard_id:
                return frame_standard
        return None

    def get_current_hive_configuration(
        self,
        hive_id: UUID,
    ) -> HiveConfigurationResponse | None:
        return self.hive_configurations.get(hive_id)

    def save_hive_configuration(
        self,
        configuration: HiveConfigurationResponse,
    ) -> HiveConfigurationResponse:
        self.hive_configurations[configuration.hive_id] = configuration
        return configuration

    def upsert_hive_configuration(
        self,
        user: UserContext,
        hive_id: UUID,
        request: HiveConfigurationUpsertRequest,
    ) -> HiveConfigurationResponse:
        from hive_sight_core_api.hive_configuration_workflow import HiveConfigurationWorkflow

        return HiveConfigurationWorkflow(store=self).upsert_hive_configuration(
            user=user,
            hive_id=hive_id,
            request=request,
        )

    def get_hive_configuration(
        self,
        user: UserContext,
        workspace_id: UUID,
        hive_id: UUID,
    ) -> HiveConfigurationResponse:
        from hive_sight_core_api.hive_configuration_workflow import HiveConfigurationWorkflow

        return HiveConfigurationWorkflow(store=self).get_hive_configuration(
            user=user,
            workspace_id=workspace_id,
            hive_id=hive_id,
        )

    def create_inspection(
        self,
        user: UserContext,
        hive_id: UUID,
        inspection_date: date,
        intent: InspectionIntent,
    ) -> InspectionResponse:
        from hive_sight_core_api.hive_configuration_workflow import HiveConfigurationWorkflow

        return HiveConfigurationWorkflow(store=self).create_inspection(
            user=user,
            hive_id=hive_id,
            inspection_date=inspection_date,
            intent=intent,
        )

    def update_inspection_intent(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_id: UUID,
        intent: InspectionIntent,
    ) -> InspectionResponse:
        from hive_sight_core_api.hive_configuration_workflow import HiveConfigurationWorkflow

        return HiveConfigurationWorkflow(store=self).update_inspection_intent(
            user=user,
            workspace_id=workspace_id,
            inspection_id=inspection_id,
            intent=intent,
        )

    def save_inspection(self, inspection: InspectionResponse) -> InspectionResponse:
        self.inspections[inspection.inspection_id] = inspection
        return inspection

    def inspection_has_photos(self, inspection_id: UUID) -> bool:
        return any(photo.inspection_id == inspection_id for photo in self.inspection_photos.values())

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

    def get_inspection_photo(
        self,
        inspection_photo_id: UUID,
    ) -> InspectionPhotoResponse | None:
        return self.inspection_photos.get(inspection_photo_id)

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
        from hive_sight_core_api.training_crop_workflow import TrainingCropWorkflow

        return TrainingCropWorkflow(store=self).create_training_crop(user=user, request=request)

    def list_training_crops_for_photo(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_photo_id: UUID,
    ) -> TrainingCropListResponse:
        from hive_sight_core_api.training_crop_workflow import TrainingCropWorkflow

        return TrainingCropWorkflow(store=self).list_training_crops_for_photo(
            user=user,
            workspace_id=workspace_id,
            inspection_photo_id=inspection_photo_id,
        )
        
    def list_training_crops_for_photo_id(
        self,
        workspace_id: UUID,
        inspection_photo_id: UUID,
    ) -> list[TrainingCropResponse]:
        crops = [
            crop
            for crop in self.training_crops.values()
            if crop.workspace_id == workspace_id and crop.inspection_photo_id == inspection_photo_id
        ]
        crops.sort(key=lambda crop: crop.created_at)
        return crops

    def save_training_crop(self, crop: TrainingCropResponse) -> TrainingCropResponse:
        self.training_crops[crop.training_crop_id] = crop
        return crop

    def update_training_crop(
        self,
        user: UserContext,
        training_crop_id: UUID,
        request: TrainingCropUpdateRequest,
    ) -> TrainingCropResponse:
        from hive_sight_core_api.training_crop_workflow import TrainingCropWorkflow

        return TrainingCropWorkflow(store=self).update_training_crop(
            user=user,
            training_crop_id=training_crop_id,
            request=request,
        )

    def create_training_crop_ellipse(
        self,
        user: UserContext,
        training_crop_id: UUID,
        request: OrientedBeeEllipseCreateRequest,
    ) -> OrientedBeeEllipseResponse:
        from hive_sight_core_api.training_crop_workflow import TrainingCropWorkflow

        return TrainingCropWorkflow(store=self).create_training_crop_ellipse(
            user=user,
            training_crop_id=training_crop_id,
            request=request,
        )

    def save_training_crop_ellipse(
        self,
        ellipse: OrientedBeeEllipseResponse,
    ) -> OrientedBeeEllipseResponse:
        self.training_crop_ellipses[ellipse.annotation_id] = ellipse
        return ellipse

    def get_training_crop_ellipse(
        self,
        annotation_id: UUID,
    ) -> OrientedBeeEllipseResponse | None:
        return self.training_crop_ellipses.get(annotation_id)

    def update_training_crop_ellipse(
        self,
        user: UserContext,
        annotation_id: UUID,
        request: OrientedBeeEllipseUpdateRequest,
    ) -> OrientedBeeEllipseResponse:
        from hive_sight_core_api.training_crop_workflow import TrainingCropWorkflow

        return TrainingCropWorkflow(store=self).update_training_crop_ellipse(
            user=user,
            annotation_id=annotation_id,
            request=request,
        )

    def delete_training_crop_ellipse(
        self,
        user: UserContext,
        workspace_id: UUID,
        annotation_id: UUID,
    ) -> None:
        from hive_sight_core_api.training_crop_workflow import TrainingCropWorkflow

        TrainingCropWorkflow(store=self).delete_training_crop_ellipse(
            user=user,
            workspace_id=workspace_id,
            annotation_id=annotation_id,
        )

    def delete_training_crop_ellipse_record(self, annotation_id: UUID) -> None:
        del self.training_crop_ellipses[annotation_id]

    def get_training_crop_evidence(
        self,
        user: UserContext,
        workspace_id: UUID,
        training_crop_id: UUID,
    ) -> TrainingCropEvidenceResponse:
        from hive_sight_core_api.training_crop_workflow import TrainingCropWorkflow

        return TrainingCropWorkflow(store=self).get_training_crop_evidence(
            user=user,
            workspace_id=workspace_id,
            training_crop_id=training_crop_id,
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
            provenance=self._dataset_item_provenance_for_photo(
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
        from hive_sight_core_api.training_crop_dataset_item_workflow import (
            TrainingCropDatasetItemWorkflow,
        )

        return TrainingCropDatasetItemWorkflow(store=self).create_dataset_item_from_training_crop(
            user=user,
            training_crop_id=training_crop_id,
            request=request,
        )

    def save_dataset_item(self, dataset_item: DatasetItemResponse) -> DatasetItemResponse:
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

    def create_physical_yolo_obb_export_package(
        self,
        user: UserContext,
        workspace_id: UUID,
        image_loader: Callable[[str], bytes | None],
        export_root: Path,
    ) -> PhysicalYoloObbExportResponse:
        yolo_export = self.create_yolo_obb_export(user=user, workspace_id=workspace_id)
        if not yolo_export.image_entries:
            raise DomainError(
                "no_dataset_items_for_physical_export",
                "Create at least one training or validation Dataset Item before exporting a package.",
                409,
            )

        export_dir = export_root / f"dataset-export-{yolo_export.export_id}"
        if export_dir.exists():
            raise DomainError(
                "dataset_export_package_exists",
                "A physical dataset export package already exists for this export id.",
                409,
            )

        generated_files: list[GeneratedDatasetExportFileEntry] = []
        try:
            (export_dir / "images" / "train").mkdir(parents=True, exist_ok=False)
            (export_dir / "images" / "val").mkdir(parents=True, exist_ok=False)
            (export_dir / "labels" / "train").mkdir(parents=True, exist_ok=False)
            (export_dir / "labels" / "val").mkdir(parents=True, exist_ok=False)

            label_entries_by_item: dict[UUID, list[YoloObbLabelEntry]] = {}
            for label_entry in yolo_export.label_entries:
                label_entries_by_item.setdefault(label_entry.dataset_item_id, []).append(label_entry)

            exported_items: list[dict[str, object]] = []
            for index, image_entry in enumerate(yolo_export.image_entries, start=1):
                dataset_item = self.dataset_items[image_entry.dataset_item_id]
                labels = label_entries_by_item.get(dataset_item.dataset_item_id, [])
                if not labels:
                    raise DomainError(
                        "dataset_item_has_no_reviewed_ellipses",
                        "Physical export requires every included Dataset Item to have reviewed bee ellipses.",
                        409,
                    )
                photo = self.inspection_photos.get(dataset_item.inspection_photo_id)
                if photo is None:
                    raise DomainError(
                        "inspection_photo_not_found",
                        "The source Inspection Photo for a Dataset Item was not found.",
                        404,
                    )
                image_bytes = image_loader(photo.original_object_key)
                if image_bytes is None:
                    raise DomainError(
                        "source_image_missing",
                        "The source Inspection Photo bytes are missing from local object storage.",
                        409,
                    )

                split_dir = _physical_split_dir(dataset_item.dataset_role)
                filename_stem = f"bee-crop-{index:06d}-{dataset_item.dataset_item_id.hex[:8]}"
                image_relative_path = f"images/{split_dir}/{filename_stem}.png"
                label_relative_path = f"labels/{split_dir}/{filename_stem}.txt"
                crop_png = _render_training_crop_png(
                    image_bytes=image_bytes,
                    dataset_item=dataset_item,
                )
                label_text = "\n".join(label.label for label in labels) + "\n"

                image_path = export_dir / image_relative_path
                label_path = export_dir / label_relative_path
                image_path.write_bytes(crop_png)
                label_path.write_text(label_text, encoding="utf-8")

                image_file = _generated_file_entry(
                    export_dir=export_dir,
                    relative_path=image_relative_path,
                    file_kind="image",
                    split=split_dir,
                    dataset_item=dataset_item,
                    filename_stem=filename_stem,
                )
                label_file = _generated_file_entry(
                    export_dir=export_dir,
                    relative_path=label_relative_path,
                    file_kind="label",
                    split=split_dir,
                    dataset_item=dataset_item,
                    filename_stem=filename_stem,
                )
                generated_files.extend([image_file, label_file])
                exported_items.append(
                    {
                        "dataset_item_id": str(dataset_item.dataset_item_id),
                        "training_crop_id": str(dataset_item.training_crop_id),
                        "inspection_photo_id": str(dataset_item.inspection_photo_id),
                        "original_filename": photo.filename,
                        "dataset_role": dataset_item.dataset_role,
                        "export_filename_stem": filename_stem,
                        "image_file": image_file.model_dump(mode="json"),
                        "label_file": label_file.model_dump(mode="json"),
                        "label_rows": [label.label for label in labels],
                        "provenance": (
                            dataset_item.provenance.model_dump(mode="json")
                            if dataset_item.provenance
                            else None
                        ),
                    }
                )

            dataset_yaml_path = export_dir / "dataset.yaml"
            dataset_yaml_path.write_text(_dataset_yaml_text(yolo_export.class_map), encoding="utf-8")
            dataset_yaml_file = _generated_file_entry(
                export_dir=export_dir,
                relative_path="dataset.yaml",
                file_kind="dataset_yaml",
                split="metadata",
                dataset_item=None,
                filename_stem=None,
            )
            generated_files.append(dataset_yaml_file)

            manifest = {
                "export_id": str(yolo_export.export_id),
                "workspace_id": str(workspace_id),
                "export_format": "yolo_obb",
                "label_convention": yolo_export.label_convention,
                "coordinate_basis": yolo_export.coordinate_basis,
                "created_by_user_id": str(user.user_id),
                "created_at": yolo_export.created_at.isoformat(),
                "class_map": yolo_export.class_map,
                "training_item_count": yolo_export.training_item_count,
                "validation_item_count": yolo_export.validation_item_count,
                "benchmark_item_count": yolo_export.benchmark_item_count,
                "excluded_item_count": len(yolo_export.excluded_dataset_items),
                "included_dataset_item_ids": [
                    str(dataset_item_id) for dataset_item_id in yolo_export.included_dataset_item_ids
                ],
                "protected_benchmark_dataset_item_ids": [
                    str(dataset_item_id)
                    for dataset_item_id in yolo_export.protected_benchmark_dataset_item_ids
                ],
                "excluded_dataset_items": [
                    item.model_dump(mode="json") for item in yolo_export.excluded_dataset_items
                ],
                "exported_items": exported_items,
                "generated_files": [
                    file.model_dump(mode="json") for file in generated_files
                ],
                "caveat": yolo_export.caveat,
            }
            manifest_path = export_dir / "manifest.json"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            generated_files.append(
                _generated_file_entry(
                    export_dir=export_dir,
                    relative_path="manifest.json",
                    file_kind="manifest",
                    split="metadata",
                    dataset_item=None,
                    filename_stem=None,
                )
            )
        except Exception:
            if export_dir.exists():
                shutil.rmtree(export_dir, ignore_errors=True)
            raise

        return PhysicalYoloObbExportResponse(
            export_id=yolo_export.export_id,
            workspace_id=workspace_id,
            export_format="yolo_obb",
            package_path=str(export_dir),
            manifest_path=str(export_dir / "manifest.json"),
            dataset_yaml_path=str(export_dir / "dataset.yaml"),
            created_by_user_id=user.user_id,
            created_at=yolo_export.created_at,
            class_map=yolo_export.class_map,
            training_item_count=yolo_export.training_item_count,
            validation_item_count=yolo_export.validation_item_count,
            benchmark_item_count=yolo_export.benchmark_item_count,
            excluded_item_count=len(yolo_export.excluded_dataset_items),
            protected_benchmark_dataset_item_ids=yolo_export.protected_benchmark_dataset_item_ids,
            excluded_dataset_items=yolo_export.excluded_dataset_items,
            generated_files=generated_files,
            caveat=yolo_export.caveat,
        )

    def _dataset_item_provenance_for_training_crop(
        self,
        crop: TrainingCropResponse,
    ) -> DatasetItemProvenanceResponse:
        return self._dataset_item_provenance_for_photo(
            workspace_id=crop.workspace_id,
            inspection_photo_id=crop.inspection_photo_id,
            training_crop_id=crop.training_crop_id,
        )

    def _dataset_item_provenance_for_photo(
        self,
        workspace_id: UUID,
        inspection_photo_id: UUID,
        training_crop_id: UUID | None = None,
    ) -> DatasetItemProvenanceResponse:
        photo = self.inspection_photos.get(inspection_photo_id)
        inspection = self.inspections.get(photo.inspection_id) if photo else None
        hive = self.hives.get(inspection.hive_id) if inspection else None
        apiary = self.apiaries.get(hive.apiary_id) if hive else None
        return DatasetItemProvenanceResponse(
            workspace_id=workspace_id,
            apiary_id=apiary.apiary_id if apiary else None,
            hive_id=hive.hive_id if hive else None,
            inspection_id=inspection.inspection_id if inspection else None,
            inspection_photo_id=inspection_photo_id,
            training_crop_id=training_crop_id,
            hive_configuration=self._hive_configuration_snapshot(hive.hive_id if hive else None),
        )

    def _hive_configuration_snapshot(
        self,
        hive_id: UUID | None,
    ) -> HiveConfigurationSnapshotResponse | None:
        if hive_id is None:
            return None
        configuration = self.hive_configurations.get(hive_id)
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
    dataset_export_root: Path = Path("var/exports/datasets")


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


def _physical_split_dir(dataset_role: DatasetRole) -> str:
    if dataset_role == DatasetRole.training:
        return "train"
    if dataset_role == DatasetRole.validation:
        return "val"
    raise DomainError(
        "dataset_role_not_exportable",
        "Physical YOLO OBB packages export training and validation Dataset Items only.",
        409,
    )


def _render_training_crop_png(
    image_bytes: bytes,
    dataset_item: DatasetItemResponse,
) -> bytes:
    if Image is None:
        raise DomainError(
            "image_export_dependency_missing",
            "Pillow is required to create physical dataset export packages.",
            500,
        )
    if (
        dataset_item.crop_x is None
        or dataset_item.crop_y is None
        or dataset_item.crop_width is None
        or dataset_item.crop_height is None
    ):
        raise DomainError(
            "dataset_item_missing_crop_geometry",
            "Physical export requires crop-sourced Dataset Items.",
            409,
        )
    try:
        source_image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise DomainError(
            "source_image_unreadable",
            "The source Inspection Photo could not be read for physical export.",
            409,
        ) from exc

    crop_box = (
        dataset_item.crop_x,
        dataset_item.crop_y,
        dataset_item.crop_x + dataset_item.crop_width,
        dataset_item.crop_y + dataset_item.crop_height,
    )
    if (
        crop_box[0] < 0
        or crop_box[1] < 0
        or crop_box[2] > source_image.width
        or crop_box[3] > source_image.height
    ):
        raise DomainError(
            "training_crop_outside_source_image",
            "The Training Crop cannot be rendered from the available source image dimensions.",
            409,
        )
    crop = source_image.crop(crop_box)
    output = BytesIO()
    crop.save(output, format="PNG")
    return output.getvalue()


def _generated_file_entry(
    export_dir: Path,
    relative_path: str,
    file_kind: str,
    split: str,
    dataset_item: DatasetItemResponse | None,
    filename_stem: str | None,
) -> GeneratedDatasetExportFileEntry:
    file_path = export_dir / relative_path
    file_bytes = file_path.read_bytes()
    return GeneratedDatasetExportFileEntry(
        relative_path=relative_path,
        file_kind=file_kind,
        split=split,
        dataset_item_id=dataset_item.dataset_item_id if dataset_item else None,
        training_crop_id=dataset_item.training_crop_id if dataset_item else None,
        inspection_photo_id=dataset_item.inspection_photo_id if dataset_item else None,
        export_filename_stem=filename_stem,
        size_bytes=len(file_bytes),
        sha256=sha256(file_bytes).hexdigest(),
    )


def _dataset_yaml_text(class_map: dict[str, str]) -> str:
    names = "\n".join(
        f"  {class_id}: {class_name}" for class_id, class_name in sorted(class_map.items())
    )
    return (
        "path: .\n"
        "train: images/train\n"
        "val: images/val\n"
        "names:\n"
        f"{names}\n"
        "# HiveSight: YOLO OBB labels derived from canonical oriented bee ellipses.\n"
    )
