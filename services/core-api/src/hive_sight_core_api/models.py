from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class AnalysisRunStatus(StrEnum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class DataUseAgreementStatus(StrEnum):
    missing = "missing"
    accepted = "accepted"


class UploadStatus(StrEnum):
    accepted = "accepted"


class AnnotationType(StrEnum):
    complete_visible_bee = "complete_visible_bee"
    partial_visible_bee = "partial_visible_bee"
    likely_varroa_detection = "likely_varroa_detection"


class CoordinateSpace(StrEnum):
    normalized = "normalized"


class ReviewDecisionValue(StrEnum):
    approved = "approved"
    rejected = "rejected"
    uncertain = "uncertain"
    excluded = "excluded"


class ReviewSubjectType(StrEnum):
    annotation = "annotation"


class AnnotationWorkflowType(StrEnum):
    analysis_result = "analysis_result"
    dataset_labelling = "dataset_labelling"


class DatasetLabellingSessionStatus(StrEnum):
    draft_ready = "draft_ready"
    review_in_progress = "review_in_progress"
    prelabel_failed = "prelabel_failed"


class ImageQualityStatus(StrEnum):
    unassessed = "unassessed"
    usable = "usable"
    poor_quality = "poor_quality"
    exclude = "exclude"


class PrelabelerRunStatus(StrEnum):
    succeeded = "succeeded"
    failed = "failed"


class DatasetRole(StrEnum):
    training = "training"
    validation = "validation"
    benchmark = "benchmark"
    excluded = "excluded"


class DatasetExclusionReason(StrEnum):
    poor_image_quality = "poor_image_quality"
    ambiguous_subject = "ambiguous_subject"
    duplicate_or_near_duplicate = "duplicate_or_near_duplicate"
    privacy_concern = "privacy_concern"
    unsuitable_crop = "unsuitable_crop"
    insufficient_review_confidence = "insufficient_review_confidence"
    other = "other"


class HealthResponse(BaseModel):
    service: str
    status: str
    boundary: str


class UploadUrlResponse(BaseModel):
    inspection_photo_id: UUID
    upload_url: str
    object_key: str
    expires_in_seconds: int
    method: str = "PUT"


class AnalysisRunRequest(BaseModel):
    workspace_id: UUID
    inspection_photo_id: UUID
    original_object_key: str = Field(min_length=1)
    requested_model_version: str | None = None


class AnalysisRunResponse(BaseModel):
    analysis_run_id: UUID
    workspace_id: UUID
    inspection_photo_id: UUID
    status: AnalysisRunStatus
    queued_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    failure_code: str | None = None
    failure_message: str | None = None
    requested_model_version: str | None = None
    model_version: str | None = None
    message: str


class ErrorResponse(BaseModel):
    code: str
    message: str


class DevSessionResponse(BaseModel):
    user_id: UUID
    workspace_id: UUID
    role: str
    reviewer_capability: bool
    dataset_curator_capability: bool
    workspace_data_use_agreement_status: DataUseAgreementStatus
    workspace_data_use_agreement_terms_version: str | None


class WorkspaceDataUseAgreementAcceptanceRequest(BaseModel):
    workspace_id: UUID
    terms_version: str = Field(min_length=1)


class WorkspaceDataUseAgreementAcceptanceResponse(BaseModel):
    workspace_id: UUID
    status: DataUseAgreementStatus
    terms_version: str
    accepted_at: datetime


class ApiaryCreateRequest(BaseModel):
    workspace_id: UUID
    name: str = Field(min_length=1, max_length=120)


class ApiaryResponse(BaseModel):
    apiary_id: UUID
    workspace_id: UUID
    name: str


class HiveCreateRequest(BaseModel):
    apiary_id: UUID
    name: str = Field(min_length=1, max_length=120)


class HiveResponse(BaseModel):
    hive_id: UUID
    apiary_id: UUID
    workspace_id: UUID
    name: str


class InspectionCreateRequest(BaseModel):
    hive_id: UUID
    inspection_date: date


class InspectionResponse(BaseModel):
    inspection_id: UUID
    hive_id: UUID
    workspace_id: UUID
    inspection_date: date


class InspectionPhotoResponse(BaseModel):
    inspection_photo_id: UUID
    inspection_id: UUID
    workspace_id: UUID
    original_object_key: str
    filename: str
    content_type: str
    size_bytes: int
    upload_status: UploadStatus
    uploaded_by_user_id: UUID
    uploaded_at: datetime


class PhotoIntakeResponse(BaseModel):
    inspection_photo: InspectionPhotoResponse
    analysis_run: AnalysisRunResponse


class AnalysisResultResponse(BaseModel):
    analysis_result_id: UUID
    analysis_run_id: UUID
    inspection_photo_id: UUID
    workspace_id: UUID
    model_version: str
    complete_visible_bee_count: int
    partial_visible_bee_count: int
    likely_varroa_detections: int
    tagged_image_object_key: str | None
    result_kind: str
    completed_at: datetime


class AnnotationCreate(BaseModel):
    annotation_type: AnnotationType
    x: float
    y: float
    width: float
    height: float
    coordinate_space: CoordinateSpace
    source_image_width_px: int
    source_image_height_px: int
    confidence: float
    source: str


class ReviewDecisionResponse(BaseModel):
    review_decision_id: UUID
    workspace_id: UUID
    reviewer_id: UUID
    subject_type: ReviewSubjectType
    subject_id: UUID
    decision: ReviewDecisionValue
    notes: str | None = None
    created_at: datetime


class AnnotationResponse(BaseModel):
    annotation_id: UUID
    workspace_id: UUID
    inspection_photo_id: UUID
    analysis_result_id: UUID | None = None
    labelling_session_id: UUID | None = None
    workflow_type: AnnotationWorkflowType = AnnotationWorkflowType.analysis_result
    annotation_type: AnnotationType
    x: float
    y: float
    width: float
    height: float
    coordinate_space: CoordinateSpace
    source_image_width_px: int
    source_image_height_px: int
    confidence: float
    source: str
    created_at: datetime
    latest_review_decision: ReviewDecisionResponse | None = None


class AnalysisRunDetailResponse(BaseModel):
    analysis_run_id: UUID
    workspace_id: UUID
    inspection_photo_id: UUID
    status: AnalysisRunStatus
    queued_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    failure_code: str | None = None
    failure_message: str | None = None
    requested_model_version: str | None = None
    model_version: str | None = None
    message: str
    analysis_result: AnalysisResultResponse | None = None


class InspectionPhotoEvidenceResponse(BaseModel):
    inspection_photo_id: UUID
    filename: str
    content_type: str
    view_url: str
    width: int
    height: int


class AnalysisEvidenceResponse(BaseModel):
    analysis_run_id: UUID
    analysis_result_id: UUID
    inspection_photo: InspectionPhotoEvidenceResponse
    analysis_result: AnalysisResultResponse
    annotations: list[AnnotationResponse]
    result_kind: str
    model_version: str
    caveat: str


class ReviewDecisionCreateRequest(BaseModel):
    workspace_id: UUID
    subject_type: ReviewSubjectType
    subject_id: UUID
    decision: ReviewDecisionValue
    notes: str | None = Field(default=None, max_length=500)


class StartDatasetLabellingRequest(BaseModel):
    workspace_id: UUID
    inspection_photo_id: UUID


class UpdateDatasetLabellingSessionRequest(BaseModel):
    workspace_id: UUID
    source_group_key: str | None = Field(default=None, max_length=100)
    image_quality_status: ImageQualityStatus


class PrelabelerRunResponse(BaseModel):
    prelabeler_run_id: UUID
    prelabeler_name: str
    prelabeler_version: str
    status: PrelabelerRunStatus
    started_at: datetime
    finished_at: datetime | None = None
    error_code: str | None = None
    error_message: str | None = None


class DatasetLabellingSessionResponse(BaseModel):
    labelling_session_id: UUID
    workspace_id: UUID
    inspection_photo_id: UUID
    created_by_user_id: UUID
    status: DatasetLabellingSessionStatus
    source_group_key: str | None = None
    image_quality_status: ImageQualityStatus = ImageQualityStatus.unassessed
    prelabeler_run: PrelabelerRunResponse
    created_at: datetime
    updated_at: datetime


class DatasetLabellingEvidenceResponse(BaseModel):
    inspection_photo: InspectionPhotoEvidenceResponse
    labelling_session: DatasetLabellingSessionResponse
    draft_annotations: list[AnnotationResponse]
    reviewed_annotations: list[AnnotationResponse]
    latest_review_decisions: list[ReviewDecisionResponse]
    dataset_item: "DatasetItemResponse | None" = None
    caveat: str


class DatasetItemCreateRequest(BaseModel):
    workspace_id: UUID
    labelling_session_id: UUID
    dataset_role: DatasetRole
    assignment_note: str | None = Field(default=None, max_length=500)
    exclusion_reason: DatasetExclusionReason | None = None


class DatasetItemResponse(BaseModel):
    dataset_item_id: UUID
    workspace_id: UUID
    inspection_photo_id: UUID
    labelling_session_id: UUID
    dataset_role: DatasetRole
    reviewed_annotation_ids: list[UUID]
    source_group_key: str | None = None
    image_quality_status: ImageQualityStatus
    assigned_by_user_id: UUID
    assigned_at: datetime
    assignment_note: str | None = None
    exclusion_reason: DatasetExclusionReason | None = None
    benchmark_protected: bool


class ProcessAnalysisRunRequest(BaseModel):
    workspace_id: UUID
