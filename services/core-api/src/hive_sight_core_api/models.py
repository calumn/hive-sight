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


class InspectionIntent(StrEnum):
    training_data_collection = "training_data_collection"
    varroa_assessment = "varroa_assessment"


class AnnotationType(StrEnum):
    complete_visible_bee = "complete_visible_bee"
    partial_visible_bee = "partial_visible_bee"
    likely_varroa_detection = "likely_varroa_detection"


class CoordinateSpace(StrEnum):
    normalized = "normalized"
    source_image_pixels = "source_image_pixels"


class ReviewDecisionValue(StrEnum):
    approved = "approved"
    rejected = "rejected"
    uncertain = "uncertain"
    excluded = "excluded"


class ReviewSubjectType(StrEnum):
    annotation = "annotation"


class ReviewQueueSubjectType(StrEnum):
    training_crop = "training_crop"


class ReviewQueueItemStatus(StrEnum):
    available = "available"
    completed = "completed"
    cancelled = "cancelled"


class ReviewQueueOutcomeValue(StrEnum):
    approved = "approved"
    changes_requested = "changes_requested"
    not_determined = "not_determined"


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


class TrainingCropReviewStatus(StrEnum):
    review_pending = "review_pending"
    review_complete = "review_complete"
    excluded = "excluded"


class VisibleBeeStatus(StrEnum):
    unassessed = "unassessed"
    has_visible_bees = "has_visible_bees"
    no_visible_bees = "no_visible_bees"


class OrientationReliability(StrEnum):
    reliable = "reliable"
    unreliable = "unreliable"


class VarroaReviewSuitability(StrEnum):
    unassessed = "unassessed"
    appears_assessable = "appears_assessable"
    body_occluded_or_hard_to_assess = "body_occluded_or_hard_to_assess"


class VarroaReviewOutcomeValue(StrEnum):
    visible_varroa_present = "visible_varroa_present"
    no_visible_varroa = "no_visible_varroa"
    not_determined = "not_determined"


class TrainingCropExclusionReason(StrEnum):
    poor_image_quality = "poor_image_quality"
    no_visible_bees = "no_visible_bees"
    ambiguous_subject = "ambiguous_subject"
    unsuitable_crop = "unsuitable_crop"
    duplicate_or_near_duplicate = "duplicate_or_near_duplicate"
    other = "other"


class BeeEllipseAnnotationSource(StrEnum):
    human_from_scratch = "human_from_scratch"
    model_candidate = "model_candidate"
    imported_public_dataset = "imported_public_dataset"


class BeeEllipseReviewMethod(StrEnum):
    human_from_scratch = "human_from_scratch"
    human_reviewed_candidate = "human_reviewed_candidate"
    imported_reviewed = "imported_reviewed"


class CandidateAnnotationReviewDecision(StrEnum):
    accepted = "accepted"
    accepted_with_edits = "accepted_with_edits"


class FrameStandardStatus(StrEnum):
    known = "known"
    unknown = "unknown"
    other = "other"


class HiveConfigurationStatus(StrEnum):
    current = "current"


class HealthResponse(BaseModel):
    service: str
    status: str
    boundary: str
    persistence_backend: str | None = None
    database_purpose: str | None = None


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


class DevUserResponse(BaseModel):
    user_id: UUID
    display_name: str
    dev_user_code: str
    description: str
    workspace_id: UUID
    workspace_display_name: str
    workspace_membership_role: str
    reviewer_capability: bool
    dataset_curator_capability: bool
    contributor_access_scope: str
    is_default: bool


class DevUserListResponse(BaseModel):
    dev_users: list[DevUserResponse]


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


class ApiaryListResponse(BaseModel):
    apiaries: list[ApiaryResponse]


class HiveCreateRequest(BaseModel):
    apiary_id: UUID
    name: str = Field(min_length=1, max_length=120)


class HiveResponse(BaseModel):
    hive_id: UUID
    apiary_id: UUID
    workspace_id: UUID
    name: str


class HiveListResponse(BaseModel):
    hives: list[HiveResponse]


class FrameStandardResponse(BaseModel):
    frame_standard_id: str
    display_name: str
    hive_type: str
    frame_use: str
    top_bar_length_mm: int | None = None
    bottom_bar_length_mm: int | None = None
    side_bar_height_mm: int | None = None
    measurement_unit: str = "mm"
    source_note: str
    status: FrameStandardStatus


class HiveConfigurationUpsertRequest(BaseModel):
    workspace_id: UUID
    frame_standard_id: str = Field(min_length=1)
    notes: str | None = Field(default=None, max_length=500)
    effective_from: date | None = None


class HiveConfigurationResponse(BaseModel):
    hive_configuration_id: UUID
    hive_id: UUID
    workspace_id: UUID
    hive_type: str
    frame_use: str
    frame_standard_id: str
    frame_standard: FrameStandardResponse
    notes: str | None = None
    status: HiveConfigurationStatus
    effective_from: date
    configured_by_user_id: UUID
    configured_at: datetime
    updated_at: datetime


class HiveConfigurationSnapshotResponse(BaseModel):
    hive_configuration_id: UUID
    hive_type: str
    frame_use: str
    frame_standard_id: str
    frame_standard_display_name: str
    top_bar_length_mm: int | None = None
    bottom_bar_length_mm: int | None = None
    side_bar_height_mm: int | None = None


class InspectionCreateRequest(BaseModel):
    hive_id: UUID
    inspection_date: date
    intent: InspectionIntent


class InspectionResponse(BaseModel):
    inspection_id: UUID
    hive_id: UUID
    workspace_id: UUID
    inspection_date: date
    intent: InspectionIntent


class InspectionListResponse(BaseModel):
    inspections: list[InspectionResponse]


class InspectionIntentUpdateRequest(BaseModel):
    workspace_id: UUID
    intent: InspectionIntent


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


class InspectionPhotoListResponse(BaseModel):
    inspection: InspectionResponse
    photos: list[InspectionPhotoResponse]


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


class AnalysisRunDetailListResponse(BaseModel):
    analysis_runs: list[AnalysisRunDetailResponse]


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
    provider: str
    adapter_version: str
    model_id: str | None = None
    checkpoint_id: str | None = None
    prompt_text: str | None = None
    box_threshold: float | None = None
    text_threshold: float | None = None
    runtime_mode: str
    status: PrelabelerRunStatus
    suggestion_count: int = 0
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


class TrainingCropDatasetItemCreateRequest(BaseModel):
    workspace_id: UUID
    dataset_role: DatasetRole
    source_group_key: str | None = Field(default=None, max_length=100)
    assignment_note: str | None = Field(default=None, max_length=500)
    exclusion_reason: DatasetExclusionReason | None = None


class ReviewedEllipseSnapshot(BaseModel):
    annotation_id: UUID
    annotation_type: AnnotationType
    center_x: float
    center_y: float
    radius_x: float
    radius_y: float
    rotation_degrees: float
    orientation_reliability: OrientationReliability = OrientationReliability.reliable
    coordinate_space: CoordinateSpace
    source_image_width_px: int
    source_image_height_px: int
    source: str
    review_method: BeeEllipseReviewMethod = BeeEllipseReviewMethod.human_from_scratch
    model_candidate_id: UUID | None = None
    candidate_confidence: float | None = None
    candidate_threshold: float | None = None
    raw_model_class: str | None = None
    raw_yolo_obb: list[float] | None = None
    candidate_review_decision: CandidateAnnotationReviewDecision | None = None
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


class DatasetItemProvenanceResponse(BaseModel):
    workspace_id: UUID
    apiary_id: UUID | None = None
    hive_id: UUID | None = None
    inspection_id: UUID | None = None
    inspection_photo_id: UUID
    training_crop_id: UUID | None = None
    hive_configuration: HiveConfigurationSnapshotResponse | None = None


class DatasetItemResponse(BaseModel):
    dataset_item_id: UUID
    workspace_id: UUID
    inspection_photo_id: UUID
    labelling_session_id: UUID | None = None
    training_crop_id: UUID | None = None
    source_evidence_type: str
    dataset_role: DatasetRole
    reviewed_annotation_ids: list[UUID]
    reviewed_ellipse_snapshots: list[ReviewedEllipseSnapshot] = Field(default_factory=list)
    crop_x: int | None = None
    crop_y: int | None = None
    crop_width: int | None = None
    crop_height: int | None = None
    crop_image_width_px: int | None = None
    crop_image_height_px: int | None = None
    curriculum_stage: str | None = None
    source_group_key: str | None = None
    image_quality_status: ImageQualityStatus
    provenance: DatasetItemProvenanceResponse | None = None
    permission_status: str = "workspace_data_use_agreement_accepted"
    assigned_by_user_id: UUID
    assigned_at: datetime
    assignment_note: str | None = None
    exclusion_reason: DatasetExclusionReason | None = None
    benchmark_protected: bool


class DatasetRepositoryWarningResponse(BaseModel):
    code: str
    severity: str
    message: str
    affected_dataset_item_ids: list[UUID] = Field(default_factory=list)


class DatasetVersionMembershipResponse(BaseModel):
    dataset_version_id: UUID
    human_readable_id: str
    purpose: str
    status: str
    membership: str
    excluded_reason: str | None = None
    created_at: datetime


class DatasetRepositoryLatestVersionSummary(BaseModel):
    dataset_version_id: UUID
    human_readable_id: str
    status: str
    created_at: datetime
    training_item_count: int
    validation_item_count: int
    benchmark_item_count: int
    excluded_item_count: int


class DatasetRepositoryItemListEntry(BaseModel):
    dataset_item_id: UUID
    human_readable_id: str
    workspace_id: UUID
    dataset_role: DatasetRole
    status: str = "active"
    source_evidence_type: str
    inspection_id: UUID | None = None
    inspection_date: date | None = None
    inspection_intent: InspectionIntent | None = None
    inspection_photo_id: UUID
    source_image_id: UUID
    source_filename: str | None = None
    apiary_id: UUID | None = None
    apiary_name: str | None = None
    hive_id: UUID | None = None
    hive_name: str | None = None
    hive_configuration_summary: str | None = None
    training_crop_id: UUID | None = None
    crop_x: int | None = None
    crop_y: int | None = None
    crop_width: int | None = None
    crop_height: int | None = None
    crop_image_width_px: int | None = None
    crop_image_height_px: int | None = None
    curriculum_stage: str | None = None
    complete_visible_bee_count: int
    partial_visible_bee_count: int
    annotation_source_counts: dict[str, int]
    review_method_counts: dict[str, int]
    source_group_key: str | None = None
    image_quality_status: ImageQualityStatus
    assigned_by_user_id: UUID
    assigned_at: datetime
    assignment_note: str | None = None
    exclusion_reason: DatasetExclusionReason | None = None
    benchmark_protected: bool
    export_eligibility: str
    latest_dataset_version_membership: DatasetVersionMembershipResponse | None = None
    dataset_version_memberships: list[DatasetVersionMembershipResponse] = Field(default_factory=list)
    is_new_since_latest_dataset_version: bool
    preview_status: str
    thumbnail_url: str | None = None


class DatasetRepositoryItemDetail(DatasetRepositoryItemListEntry):
    reviewed_ellipse_snapshots: list[ReviewedEllipseSnapshot]
    provenance: DatasetItemProvenanceResponse | None = None
    permission_status: str
    preview_url: str | None = None


class DatasetRepositorySummaryResponse(BaseModel):
    workspace_id: UUID
    dataset_item_count: int
    active_dataset_item_count: int
    unassigned_completed_crop_count: int
    new_since_latest_dataset_version_count: int
    role_counts: dict[str, int]
    annotation_class_counts: dict[str, int]
    annotation_source_counts: dict[str, int]
    review_method_counts: dict[str, int]
    curriculum_stage_distribution: dict[str, int]
    image_quality_distribution: dict[str, int]
    hive_configuration_distribution: dict[str, int]
    source_group_distribution: dict[str, int]
    inspection_distribution: dict[str, int]
    inspection_intent_distribution: dict[str, int]
    hive_distribution: dict[str, int]
    source_image_distribution: dict[str, int]
    latest_dataset_version: DatasetRepositoryLatestVersionSummary | None = None
    persistence_backend: str
    database_purpose: str
    warnings: list[DatasetRepositoryWarningResponse]


class DatasetRepositoryItemListResponse(BaseModel):
    summary: DatasetRepositorySummaryResponse
    items: list[DatasetRepositoryItemListEntry]


class YoloObbExportRequest(BaseModel):
    workspace_id: UUID


class PhysicalYoloObbExportRequest(BaseModel):
    workspace_id: UUID


class YoloObbLabelEntry(BaseModel):
    dataset_item_id: UUID
    training_crop_id: UUID
    annotation_id: UUID
    split: DatasetRole
    class_id: int
    class_name: AnnotationType
    label: str
    points: list[float]


class YoloObbImageEntry(BaseModel):
    dataset_item_id: UUID
    training_crop_id: UUID
    inspection_photo_id: UUID
    split: DatasetRole
    crop_x: int
    crop_y: int
    crop_width: int
    crop_height: int


class YoloObbExcludedItem(BaseModel):
    dataset_item_id: UUID
    training_crop_id: UUID | None = None
    dataset_role: DatasetRole
    reason: str


class YoloObbExportResponse(BaseModel):
    export_id: UUID
    workspace_id: UUID
    export_format: str
    label_convention: str
    coordinate_basis: str
    created_by_user_id: UUID
    created_at: datetime
    class_map: dict[str, str]
    included_dataset_item_ids: list[UUID]
    excluded_dataset_items: list[YoloObbExcludedItem]
    protected_benchmark_dataset_item_ids: list[UUID]
    training_item_count: int
    validation_item_count: int
    benchmark_item_count: int
    image_entries: list[YoloObbImageEntry]
    label_entries: list[YoloObbLabelEntry]
    caveat: str


class GeneratedDatasetExportFileEntry(BaseModel):
    relative_path: str
    file_kind: str
    split: str
    dataset_item_id: UUID | None = None
    training_crop_id: UUID | None = None
    inspection_photo_id: UUID | None = None
    export_filename_stem: str | None = None
    size_bytes: int
    sha256: str


class PhysicalYoloObbExportResponse(BaseModel):
    export_id: UUID
    workspace_id: UUID
    export_format: str
    package_path: str
    manifest_path: str
    dataset_yaml_path: str
    created_by_user_id: UUID
    created_at: datetime
    class_map: dict[str, str]
    training_item_count: int
    validation_item_count: int
    benchmark_item_count: int
    excluded_item_count: int
    protected_benchmark_dataset_item_ids: list[UUID]
    excluded_dataset_items: list[YoloObbExcludedItem]
    generated_files: list[GeneratedDatasetExportFileEntry]
    caveat: str


class ModelTrainingWarningSeverity(StrEnum):
    info = "info"
    warning = "warning"
    high = "high"


class ModelTrainingWarningResponse(BaseModel):
    code: str
    severity: ModelTrainingWarningSeverity
    message: str


class ArtifactResponse(BaseModel):
    artifact_id: UUID
    owner_type: str
    owner_id: UUID
    artifact_type: str
    relative_path: str
    content_type: str
    size_bytes: int
    sha256: str
    required_or_diagnostic: str
    availability_status: str
    created_at: datetime


class ModelTrainingReadinessResponse(BaseModel):
    workspace_id: UUID
    persistence_backend: str
    database_purpose: str
    adapter_type: str
    real_adapter_available: bool
    active_training_run_id: UUID | None = None
    model_purpose: str = "bee_detector"
    dataset_version_id: UUID | None = None
    dataset_version_human_readable_id: str | None = None
    dataset_version_purpose: str | None = None
    training_item_count: int
    validation_item_count: int
    benchmark_item_count: int
    eligible_training_source_bee_count: int = 0
    eligible_validation_source_bee_count: int = 0
    generated_training_example_count: int = 0
    generated_validation_example_count: int = 0
    protected_benchmark_source_bee_count: int = 0
    excluded_unreliable_orientation_count: int = 0
    excluded_partial_visible_bee_count: int = 0
    eligible_to_create_dataset_version: bool
    eligible_to_start_training: bool
    warnings: list[ModelTrainingWarningResponse]


class BeeTrainingReadinessResponse(BaseModel):
    workspace_id: UUID
    dataset_version_id: UUID | None = None
    dataset_version_human_readable_id: str | None = None
    active_training_run_id: UUID | None = None
    bee_localisation: ModelTrainingReadinessResponse
    bee_orientation: ModelTrainingReadinessResponse
    eligible_to_start_bee_training: bool
    warnings: list[ModelTrainingWarningResponse]


class DatasetVersionCreateRequest(BaseModel):
    workspace_id: UUID
    purpose: str = "marked_bee_detection_orientation"


class DatasetVersionResponse(BaseModel):
    dataset_version_id: UUID
    workspace_id: UUID
    human_readable_id: str
    purpose: str
    model_purpose: str
    status: str
    export_format: str
    selection_criteria: dict[str, object]
    manifest_hash: str
    included_dataset_item_ids: list[UUID]
    training_dataset_item_ids: list[UUID]
    validation_dataset_item_ids: list[UUID]
    protected_benchmark_dataset_item_ids: list[UUID]
    excluded_dataset_items: list[YoloObbExcludedItem]
    training_item_count: int
    validation_item_count: int
    benchmark_item_count: int
    excluded_item_count: int
    annotation_class_counts: dict[str, int]
    annotation_source_counts: dict[str, int]
    review_method_counts: dict[str, int]
    source_group_distribution: dict[str, int]
    hive_configuration_distribution: dict[str, int]
    curriculum_stage_distribution: dict[str, int]
    image_quality_distribution: dict[str, int]
    warnings: list[ModelTrainingWarningResponse]
    preview_artifact_ids: list[UUID]
    report_artifact_id: UUID | None = None
    created_by_user_id: UUID
    created_at: datetime


class TrainingRunStartRequest(BaseModel):
    workspace_id: UUID
    dataset_version_id: UUID
    model_purpose: str = "bee_detector"
    model_size: str = "nano"
    epochs: int = Field(default=1, ge=1, le=100)
    image_size: int = Field(default=640, ge=128, le=2048)
    batch_size: int = Field(default=1, ge=1, le=64)
    random_seed: int = Field(default=42, ge=0)
    purpose_notes: str | None = Field(default=None, max_length=500)
    acknowledge_high_severity_warnings: bool = False


class BeeTrainingStartRequest(BaseModel):
    workspace_id: UUID
    dataset_version_id: UUID
    model_size: str = "nano"
    epochs: int = Field(default=1, ge=1, le=100)
    image_size: int = Field(default=640, ge=128, le=2048)
    batch_size: int = Field(default=1, ge=1, le=64)
    random_seed: int = Field(default=42, ge=0)
    purpose_notes: str | None = Field(default=None, max_length=500)
    acknowledge_high_severity_warnings: bool = False


class TrainingRunCancelRequest(BaseModel):
    workspace_id: UUID
    reason: str | None = Field(default=None, max_length=500)


class TrainingRunAbandonRequest(BaseModel):
    workspace_id: UUID
    reason: str = Field(min_length=1, max_length=500)
    force: bool = False


class TrainingRunDeleteRequest(BaseModel):
    workspace_id: UUID
    reason: str = Field(min_length=1, max_length=500)
    confirm_no_candidate_or_required_artifacts: bool = False


class TrainingRunDeleteResponse(BaseModel):
    training_run_id: UUID
    deleted: bool
    message: str


class TrainingRunResponse(BaseModel):
    training_run_id: UUID
    workspace_id: UUID
    human_readable_id: str
    dataset_version_id: UUID
    model_purpose: str
    model_family: str
    model_size: str
    base_weights: str
    base_weights_source: str
    status: str
    phase: str
    adapter_type: str
    database_purpose: str
    training_settings: dict[str, object]
    random_seed: int
    git_commit_sha: str | None = None
    git_dirty_status: str
    environment_summary: dict[str, object]
    warning_acknowledgement: dict[str, object] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_heartbeat_at: datetime | None = None
    last_activity_message: str | None = None
    progress_percent: float | None = None
    current_epoch: int | None = None
    total_epochs: int | None = None
    latest_log_excerpt: str | None = None
    cancel_requested_at: datetime | None = None
    cancel_requested_by_user_id: UUID | None = None
    cancel_reason: str | None = None
    abandoned_at: datetime | None = None
    abandoned_by_user_id: UUID | None = None
    abandon_reason: str | None = None
    is_stale: bool = False
    stale_after_seconds: int | None = None
    failure_code: str | None = None
    failure_message: str | None = None
    artifact_ids: list[UUID]
    metrics_summary: dict[str, object]
    report_artifact_id: UUID | None = None
    model_candidate_id: UUID | None = None
    created_by_user_id: UUID
    created_at: datetime
    purpose_notes: str | None = None


class ModelCandidateResponse(BaseModel):
    model_candidate_id: UUID
    workspace_id: UUID
    human_readable_id: str
    display_name: str
    training_run_id: UUID
    model_purpose: str
    model_family: str
    adapter_type: str
    artifact_id: UUID
    status: str
    promotion_status: str
    not_user_facing_reason: str
    created_at: datetime


class TrainingRunListResponse(BaseModel):
    training_runs: list[TrainingRunResponse]


class BeeTrainingStartResponse(BaseModel):
    workspace_id: UUID
    dataset_version_id: UUID
    bee_localisation_training_run: TrainingRunResponse
    bee_orientation_training_run: TrainingRunResponse | None = None
    message: str


class DatasetVersionListResponse(BaseModel):
    dataset_versions: list[DatasetVersionResponse]


class ModelCandidateListResponse(BaseModel):
    model_candidates: list[ModelCandidateResponse]


class BenchmarkEvaluationStartRequest(BaseModel):
    workspace_id: UUID
    model_candidate_id: UUID
    confidence_threshold: float = Field(default=0.10, ge=0, le=1)
    acknowledge_high_severity_warnings: bool = False


class BenchmarkEvaluationCancelRequest(BaseModel):
    workspace_id: UUID
    reason: str | None = Field(default=None, max_length=500)


class BenchmarkEvaluationWarningResponse(BaseModel):
    code: str
    severity: ModelTrainingWarningSeverity
    message: str


class BenchmarkEvaluationReadinessResponse(BaseModel):
    workspace_id: UUID
    model_candidate_id: UUID
    model_candidate_human_readable_id: str
    adapter_type: str
    training_adapter_type: str
    evaluation_adapter_type: str
    database_purpose: str
    benchmark_item_count: int
    eligible_to_start_evaluation: bool
    active_model_job_id: UUID | None = None
    active_model_job_type: str | None = None
    warnings: list[BenchmarkEvaluationWarningResponse]


class OrientationBenchmarkReadinessResponse(BaseModel):
    workspace_id: UUID
    model_candidate_id: UUID
    model_candidate_human_readable_id: str
    dataset_version_id: UUID
    dataset_version_human_readable_id: str
    adapter_type: str
    training_adapter_type: str
    evaluation_adapter_type: str
    database_purpose: str
    benchmark_item_count: int
    eligible_benchmark_bee_count: int
    excluded_unreliable_orientation_count: int
    excluded_partial_visible_bee_count: int
    eligible_to_start_evaluation: bool
    eligible_to_start_benchmark: bool
    active_model_job_id: UUID | None = None
    active_model_job_type: str | None = None
    warnings: list[BenchmarkEvaluationWarningResponse]


class BenchmarkEvaluationItemResultResponse(BaseModel):
    dataset_item_id: UUID
    human_readable_id: str
    source_group_key: str | None = None
    hive_configuration_frame_standard_id: str | None = None
    curriculum_stage: str | None = None
    ground_truth_count: int
    prediction_count: int
    matched_count: int
    false_positive_count: int
    false_negative_count: int


class BenchmarkEvaluationResponse(BaseModel):
    benchmark_evaluation_id: UUID
    workspace_id: UUID
    human_readable_id: str
    model_candidate_id: UUID
    model_candidate_human_readable_id: str
    training_run_id: UUID
    dataset_version_id: UUID
    model_purpose: str = "bee_detector"
    status: str
    phase: str
    adapter_type: str
    training_adapter_type: str
    evaluation_adapter_type: str
    database_purpose: str
    confidence_threshold: float
    match_strategy: str
    benchmark_scope: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_heartbeat_at: datetime | None = None
    last_activity_message: str | None = None
    progress_percent: float | None = None
    latest_log_excerpt: str | None = None
    cancel_requested_at: datetime | None = None
    cancel_requested_by_user_id: UUID | None = None
    cancel_reason: str | None = None
    failure_code: str | None = None
    failure_message: str | None = None
    is_stale: bool = False
    stale_after_seconds: int | None = None
    warning_acknowledgement: dict[str, object] | None = None
    warnings: list[BenchmarkEvaluationWarningResponse]
    metrics_summary: dict[str, object]
    item_results: list[BenchmarkEvaluationItemResultResponse]
    raw_prediction_artifact_id: UUID | None = None
    report_artifact_id: UUID | None = None
    artifact_ids: list[UUID]
    created_by_user_id: UUID
    created_at: datetime


class BenchmarkEvaluationListResponse(BaseModel):
    benchmark_evaluations: list[BenchmarkEvaluationResponse]


class DirectedEllipseLocalCleanupRequest(BaseModel):
    workspace_id: UUID
    reason: str | None = Field(default=None, max_length=500)
    confirm_remove_dataset_and_model_evidence: bool = False


class DirectedEllipseLocalCleanupResponse(BaseModel):
    workspace_id: UUID
    dataset_items_removed: int
    dataset_versions_removed: int
    training_runs_removed: int
    model_candidates_removed: int
    artifacts_removed: int
    artifact_paths_removed: int
    training_crops_reopened: int
    training_crop_ellipses_preserved: int
    inspection_photos_preserved: int
    caveat: str


class TrainingCropCreateRequest(BaseModel):
    workspace_id: UUID
    inspection_photo_id: UUID
    crop_x: int = Field(ge=0)
    crop_y: int = Field(ge=0)
    crop_width: int = Field(gt=0)
    crop_height: int = Field(gt=0)
    source_image_width_px: int = Field(gt=0)
    source_image_height_px: int = Field(gt=0)
    notes: str | None = Field(default=None, max_length=500)


class TrainingCropUpdateRequest(BaseModel):
    workspace_id: UUID
    crop_x: int | None = Field(default=None, ge=0)
    crop_y: int | None = Field(default=None, ge=0)
    crop_width: int | None = Field(default=None, gt=0)
    crop_height: int | None = Field(default=None, gt=0)
    visible_bee_status: VisibleBeeStatus | None = None
    review_status: TrainingCropReviewStatus | None = None
    exclusion_reason: TrainingCropExclusionReason | None = None
    notes: str | None = Field(default=None, max_length=500)


class TrainingCropResponse(BaseModel):
    training_crop_id: UUID
    workspace_id: UUID
    inspection_photo_id: UUID
    crop_x: int
    crop_y: int
    crop_width: int
    crop_height: int
    coordinate_space: CoordinateSpace
    source_image_width_px: int
    source_image_height_px: int
    crop_image_width_px: int
    crop_image_height_px: int
    curriculum_stage: str
    review_status: TrainingCropReviewStatus
    visible_bee_status: VisibleBeeStatus
    exclusion_reason: TrainingCropExclusionReason | None = None
    dataset_item_id: UUID | None = None
    dataset_role: DatasetRole | None = None
    notes: str | None = None
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


class TrainingCropListResponse(BaseModel):
    inspection_photo: InspectionPhotoResponse
    training_crops: list[TrainingCropResponse]


class OrientedBeeEllipseCreateRequest(BaseModel):
    workspace_id: UUID
    annotation_type: AnnotationType
    center_x: float = Field(ge=0)
    center_y: float = Field(ge=0)
    radius_x: float = Field(gt=0)
    radius_y: float = Field(gt=0)
    rotation_degrees: float = 0
    orientation_reliability: OrientationReliability = OrientationReliability.reliable
    source: BeeEllipseAnnotationSource = BeeEllipseAnnotationSource.human_from_scratch
    review_method: BeeEllipseReviewMethod = BeeEllipseReviewMethod.human_from_scratch
    model_candidate_id: UUID | None = None
    candidate_confidence: float | None = Field(default=None, ge=0, le=1)
    candidate_threshold: float | None = Field(default=None, ge=0, le=1)
    raw_model_class: str | None = Field(default=None, max_length=100)
    raw_yolo_obb: list[float] | None = Field(default=None, min_length=5, max_length=8)
    candidate_review_decision: CandidateAnnotationReviewDecision | None = None


class OrientedBeeEllipseUpdateRequest(BaseModel):
    workspace_id: UUID
    annotation_type: AnnotationType | None = None
    center_x: float | None = Field(default=None, ge=0)
    center_y: float | None = Field(default=None, ge=0)
    radius_x: float | None = Field(default=None, gt=0)
    radius_y: float | None = Field(default=None, gt=0)
    rotation_degrees: float | None = None
    orientation_reliability: OrientationReliability | None = None
    varroa_review_suitability: VarroaReviewSuitability | None = None
    suspected_visible_varroa: bool | None = None


class OrientedBeeEllipseResponse(BaseModel):
    annotation_id: UUID
    workspace_id: UUID
    inspection_photo_id: UUID
    training_crop_id: UUID
    annotation_type: AnnotationType
    center_x: float
    center_y: float
    radius_x: float
    radius_y: float
    rotation_degrees: float
    orientation_reliability: OrientationReliability = OrientationReliability.reliable
    coordinate_space: CoordinateSpace
    source_image_width_px: int
    source_image_height_px: int
    source: str
    review_method: BeeEllipseReviewMethod = BeeEllipseReviewMethod.human_from_scratch
    model_candidate_id: UUID | None = None
    candidate_confidence: float | None = None
    candidate_threshold: float | None = None
    raw_model_class: str | None = None
    raw_yolo_obb: list[float] | None = None
    candidate_review_decision: CandidateAnnotationReviewDecision | None = None
    varroa_review_suitability: VarroaReviewSuitability = VarroaReviewSuitability.unassessed
    suspected_visible_varroa: bool = False
    varroa_review_suitability_updated_by_user_id: UUID | None = None
    varroa_review_suitability_updated_at: datetime | None = None
    suspected_visible_varroa_updated_by_user_id: UUID | None = None
    suspected_visible_varroa_updated_at: datetime | None = None
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


class BeeAnnotationProposalResponse(BaseModel):
    proposal_id: str
    workspace_id: UUID
    training_crop_id: UUID
    model_candidate_id: UUID
    model_candidate_human_readable_id: str
    annotation_type: AnnotationType
    center_x: float
    center_y: float
    radius_x: float
    radius_y: float
    rotation_degrees: float
    coordinate_space: CoordinateSpace
    confidence: float
    threshold: float
    raw_model_class: str
    raw_yolo_obb: list[float]


class BeeAnnotationProposalRequest(BaseModel):
    workspace_id: UUID
    model_candidate_id: UUID | None = None
    confidence_threshold: float = Field(default=0.10, ge=0, le=1)
    max_suggestions: int = Field(default=50, ge=1, le=50)


class BeeAnnotationProposalListResponse(BaseModel):
    workspace_id: UUID
    training_crop_id: UUID
    model_candidate_id: UUID
    model_candidate_human_readable_id: str
    threshold: float
    suggestions: list[BeeAnnotationProposalResponse]
    caveat: str


class TrainingCropEvidenceResponse(BaseModel):
    inspection_photo: InspectionPhotoEvidenceResponse
    training_crop: TrainingCropResponse
    bee_ellipses: list[OrientedBeeEllipseResponse]
    caveat: str


class VarroaMarkerCreateRequest(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class VarroaMarkerResponse(BaseModel):
    varroa_marker_id: UUID
    varroa_review_outcome_id: UUID
    marker_type: str = "point"
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    created_at: datetime


class VarroaReviewOutcomeCreateRequest(BaseModel):
    workspace_id: UUID
    outcome: VarroaReviewOutcomeValue
    markers: list[VarroaMarkerCreateRequest] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=500)


class VarroaReviewOutcomeResponse(BaseModel):
    varroa_review_outcome_id: UUID
    workspace_id: UUID
    inspection_photo_id: UUID
    training_crop_id: UUID
    bee_annotation_id: UUID
    outcome: VarroaReviewOutcomeValue
    sampling_purpose: str = "model_curation"
    dataset_selection_method: str = "human_selected"
    review_strength: str = "single_curator_review"
    annotation_source: str = "human_from_scratch"
    created_by_user_id: UUID
    created_at: datetime
    updated_by_user_id: UUID
    updated_at: datetime
    notes: str | None = None
    source_context_snapshot: dict[str, object]
    bee_annotation_geometry_snapshot: dict[str, object]
    training_crop_review_status_snapshot: str
    transform_metadata: dict[str, object]
    markers: list[VarroaMarkerResponse] = Field(default_factory=list)


class VarroaReviewCandidateResponse(BaseModel):
    bee_annotation: OrientedBeeEllipseResponse
    eligibility: str
    ineligibility_reasons: list[str] = Field(default_factory=list)
    review_outcome: VarroaReviewOutcomeResponse | None = None


class VarroaReviewSummaryResponse(BaseModel):
    eligible_bee_count: int
    reviewed_bee_count: int
    visible_varroa_bee_count: int
    no_visible_varroa_bee_count: int
    not_determined_bee_count: int
    total_marker_count: int
    suspected_visible_varroa_cue_count: int
    hard_to_assess_cue_count: int
    ineligible_deferred_bee_count: int
    caveat: str


class VarroaReviewCandidateListResponse(BaseModel):
    workspace_id: UUID
    training_crop_id: UUID
    candidates: list[VarroaReviewCandidateResponse]
    summary: VarroaReviewSummaryResponse


class FrameLevelVarroaResultSummaryResponse(BaseModel):
    workspace_id: UUID
    inspection_id: UUID
    inspection_photo_id: UUID
    source_image_filename: str
    source_intent: InspectionIntent
    completed_training_crop_count: int
    unfinished_training_crop_count: int
    eligible_complete_bee_count: int
    reviewed_eligible_bee_count: int
    determinate_eligible_bee_count: int
    visible_varroa_bee_count: int
    active_negative_bee_count: int
    not_determined_bee_count: int
    unreviewed_eligible_bee_count: int
    ineligible_or_not_assessed_bee_count: int
    visible_mite_marker_count: int
    review_completion_percent: float
    determinate_varroa_coverage_percent: float
    evidence_source: str
    readiness_state: str
    advisor_context_available: bool
    caveats: str


class HeadUpNormalizedBeeCropPreviewResponse(BaseModel):
    workspace_id: UUID
    inspection_photo_id: UUID
    training_crop_id: UUID
    bee_annotation_id: UUID
    annotation_type: AnnotationType
    orientation_reliability: OrientationReliability
    image_width_px: int
    image_height_px: int
    transform_version: str
    image_url: str
    transform_metadata: dict[str, object]
    bee_annotation_geometry_snapshot: dict[str, object]


class ReviewQueueEllipseEvidence(BaseModel):
    annotation_id: UUID
    annotation_type: AnnotationType
    center_x: float
    center_y: float
    radius_x: float
    radius_y: float
    rotation_degrees: float
    coordinate_space: CoordinateSpace
    source_image_width_px: int
    source_image_height_px: int


class ReviewQueueEvidenceSnapshot(BaseModel):
    safe_source_label: str
    training_crop_id: UUID
    training_crop_label: str
    inspection_photo_id: UUID
    image_view_url: str
    crop_x: int
    crop_y: int
    crop_width: int
    crop_height: int
    source_image_width_px: int
    source_image_height_px: int
    crop_image_width_px: int
    crop_image_height_px: int
    reviewed_ellipses: list[ReviewQueueEllipseEvidence]
    reviewed_ellipse_count: int
    complete_visible_bee_count: int
    partial_visible_bee_count: int
    crop_review_status: TrainingCropReviewStatus
    visible_bee_status: VisibleBeeStatus
    requested_at: datetime


class ReviewQueueItemRecord(BaseModel):
    review_queue_item_id: UUID
    human_readable_id: str
    workspace_id: UUID
    subject_type: ReviewQueueSubjectType
    subject_id: UUID
    requested_by_user_id: UUID
    original_crop_reviewer_user_id: UUID
    status: ReviewQueueItemStatus
    request_notes: str | None = None
    requested_at: datetime
    cancelled_at: datetime | None = None
    cancelled_by_user_id: UUID | None = None
    cancellation_notes: str | None = None
    completed_at: datetime | None = None
    completed_by_outcome_id: UUID | None = None
    evidence_snapshot: ReviewQueueEvidenceSnapshot


class ReviewQueueOutcomeRecord(BaseModel):
    review_queue_outcome_id: UUID
    review_queue_item_id: UUID
    reviewer_id: UUID
    review_outcome: ReviewQueueOutcomeValue
    review_notes: str | None = None
    created_at: datetime


class ReviewQueueItemCreateRequest(BaseModel):
    workspace_id: UUID
    training_crop_id: UUID
    request_notes: str | None = Field(default=None, max_length=500)


class ReviewQueueItemCancelRequest(BaseModel):
    cancellation_notes: str = Field(min_length=1, max_length=500)


class ReviewQueueOutcomeCreateRequest(BaseModel):
    review_outcome: ReviewQueueOutcomeValue
    review_notes: str | None = Field(default=None, max_length=500)


class ReviewQueueItemResponse(BaseModel):
    review_queue_item_id: UUID
    human_readable_id: str
    subject_type: ReviewQueueSubjectType
    subject_id: UUID
    status: ReviewQueueItemStatus
    request_notes: str | None = None
    requested_at: datetime
    cancelled_at: datetime | None = None
    cancellation_notes: str | None = None
    completed_at: datetime | None = None
    completed_outcome: ReviewQueueOutcomeValue | None = None
    completed_reviewer_display_identity: str | None = None
    evidence_snapshot: ReviewQueueEvidenceSnapshot


class ReviewQueueItemListResponse(BaseModel):
    review_queue_items: list[ReviewQueueItemResponse]


class ProcessAnalysisRunRequest(BaseModel):
    workspace_id: UUID
