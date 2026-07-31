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
    training_item_count: int
    validation_item_count: int
    benchmark_item_count: int
    eligible_to_create_dataset_version: bool
    eligible_to_start_training: bool
    warnings: list[ModelTrainingWarningResponse]


class DatasetVersionCreateRequest(BaseModel):
    workspace_id: UUID
    purpose: str = "bee_detector_training_baseline"


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


class DatasetVersionListResponse(BaseModel):
    dataset_versions: list[DatasetVersionResponse]


class ModelCandidateListResponse(BaseModel):
    model_candidates: list[ModelCandidateResponse]


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


class ProcessAnalysisRunRequest(BaseModel):
    workspace_id: UUID
