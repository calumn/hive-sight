export type HealthResponse = {
  service: string;
  status: string;
  boundary: string;
  persistenceBackend: string | null;
  databasePurpose: string | null;
};

export type DevSession = {
  userId: string;
  workspaceId: string;
  role: string;
  reviewerCapability: boolean;
  datasetCuratorCapability: boolean;
  workspaceDataUseAgreementStatus: "missing" | "accepted";
  workspaceDataUseAgreementTermsVersion: string | null;
};

export type DevUser = {
  userId: string;
  displayName: string;
  devUserCode: string;
  description: string;
  workspaceId: string;
  workspaceDisplayName: string;
  workspaceMembershipRole: string;
  reviewerCapability: boolean;
  datasetCuratorCapability: boolean;
  contributorAccessScope: string;
  isDefault: boolean;
};

export type DevUserList = {
  devUsers: DevUser[];
};

export type Apiary = {
  apiaryId: string;
  workspaceId: string;
  name: string;
};

export type ApiaryList = {
  apiaries: Apiary[];
};

export type Hive = {
  hiveId: string;
  apiaryId: string;
  workspaceId: string;
  name: string;
};

export type HiveList = {
  hives: Hive[];
};

export type FrameStandardStatus = "known" | "unknown" | "other";

export type FrameStandard = {
  frameStandardId: string;
  displayName: string;
  hiveType: string;
  frameUse: string;
  topBarLengthMm: number | null;
  bottomBarLengthMm: number | null;
  sideBarHeightMm: number | null;
  measurementUnit: string;
  sourceNote: string;
  status: FrameStandardStatus;
};

export type HiveConfiguration = {
  hiveConfigurationId: string;
  hiveId: string;
  workspaceId: string;
  hiveType: string;
  frameUse: string;
  frameStandardId: string;
  frameStandard: FrameStandard;
  notes: string | null;
  status: "current";
  effectiveFrom: string;
  configuredByUserId: string;
  configuredAt: string;
  updatedAt: string;
};

export type InspectionIntent = "training_data_collection" | "varroa_assessment";

export type Inspection = {
  inspectionId: string;
  hiveId: string;
  workspaceId: string;
  inspectionDate: string;
  intent: InspectionIntent;
};

export type InspectionList = {
  inspections: Inspection[];
};

export type InspectionPhoto = {
  inspectionPhotoId: string;
  inspectionId: string;
  workspaceId: string;
  originalObjectKey: string;
  filename: string;
  contentType: string;
  sizeBytes: number;
  uploadStatus: "accepted";
  uploadedByUserId: string;
  uploadedAt: string;
};

export type InspectionPhotoList = {
  inspection: Inspection;
  photos: InspectionPhoto[];
};

export type PhotoIntake = {
  inspectionPhoto: InspectionPhoto;
  analysisRun: {
    analysisRunId: string;
    inspectionPhotoId: string;
    status: "queued" | "running" | "completed" | "failed";
    queuedAt: string;
    message: string;
  };
};

export type AnalysisResult = {
  analysisResultId: string;
  analysisRunId: string;
  inspectionPhotoId: string;
  workspaceId: string;
  modelVersion: string;
  completeVisibleBeeCount: number;
  partialVisibleBeeCount: number;
  likelyVarroaDetections: number;
  taggedImageObjectKey: string | null;
  resultKind: "deterministic_stub";
  completedAt: string;
};

export type AnnotationType = "complete_visible_bee" | "partial_visible_bee" | "likely_varroa_detection";

export type BeeAnnotationType = "complete_visible_bee" | "partial_visible_bee";

export type ReviewDecisionValue = "approved" | "rejected" | "uncertain" | "excluded";

export type ImageQualityStatus = "unassessed" | "usable" | "poor_quality" | "exclude";

export type DatasetRole = "training" | "validation" | "benchmark" | "excluded";

export type ModelPurpose = "bee_detector" | "marked_bee" | "bee_orientation";

export type TrainingExportFormat =
  | "yolo_obb_v1"
  | "marked_bee_dataset_v1"
  | "bee_orientation_head_up_down_v1";

export type DatasetExclusionReason =
  | "poor_image_quality"
  | "ambiguous_subject"
  | "duplicate_or_near_duplicate"
  | "privacy_concern"
  | "unsuitable_crop"
  | "insufficient_review_confidence"
  | "other";

export type VisibleBeeStatus = "unassessed" | "has_visible_bees" | "no_visible_bees";

export type OrientationReliability = "reliable" | "unreliable";

export type VarroaReviewSuitability =
  | "unassessed"
  | "appears_assessable"
  | "body_occluded_or_hard_to_assess";

export type VarroaReviewOutcomeValue =
  | "visible_varroa_present"
  | "no_visible_varroa"
  | "not_determined";

export type TrainingCropReviewStatus = "review_pending" | "review_complete" | "excluded";

export type TrainingCropExclusionReason =
  | "poor_image_quality"
  | "no_visible_bees"
  | "ambiguous_subject"
  | "unsuitable_crop"
  | "duplicate_or_near_duplicate"
  | "other";

export type DatasetLabellingSessionStatus =
  | "draft_ready"
  | "review_in_progress"
  | "prelabel_failed";

export type PrelabelerRun = {
  prelabelerRunId: string;
  prelabelerName: string;
  prelabelerVersion: string;
  provider: "deterministic";
  adapterVersion: string;
  modelId: string | null;
  checkpointId: string | null;
  promptText: string | null;
  boxThreshold: number | null;
  textThreshold: number | null;
  runtimeMode: "local";
  status: "succeeded" | "failed";
  suggestionCount: number;
  startedAt: string;
  finishedAt: string | null;
  errorCode: string | null;
  errorMessage: string | null;
};

export type DatasetLabellingSession = {
  labellingSessionId: string;
  workspaceId: string;
  inspectionPhotoId: string;
  createdByUserId: string;
  status: DatasetLabellingSessionStatus;
  sourceGroupKey: string | null;
  imageQualityStatus: ImageQualityStatus;
  prelabelerRun: PrelabelerRun;
  createdAt: string;
  updatedAt: string;
};

export type ReviewDecision = {
  reviewDecisionId: string;
  workspaceId: string;
  reviewerId: string;
  subjectType: "annotation";
  subjectId: string;
  decision: ReviewDecisionValue;
  notes: string | null;
  createdAt: string;
};

export type DatasetItem = {
  datasetItemId: string;
  workspaceId: string;
  inspectionPhotoId: string;
  labellingSessionId: string | null;
  trainingCropId: string | null;
  sourceEvidenceType: "dataset_labelling_session" | "training_crop";
  datasetRole: DatasetRole;
  reviewedAnnotationIds: string[];
  reviewedEllipseSnapshots: ReviewedEllipseSnapshot[];
  cropX: number | null;
  cropY: number | null;
  cropWidth: number | null;
  cropHeight: number | null;
  cropImageWidthPx: number | null;
  cropImageHeightPx: number | null;
  curriculumStage: string | null;
  sourceGroupKey: string | null;
  imageQualityStatus: ImageQualityStatus;
  permissionStatus: string;
  assignedByUserId: string;
  assignedAt: string;
  assignmentNote: string | null;
  exclusionReason: DatasetExclusionReason | null;
  benchmarkProtected: boolean;
};

export type DatasetVersionMembership = {
  datasetVersionId: string;
  humanReadableId: string;
  purpose: string;
  status: string;
  membership:
    | "included"
    | "training"
    | "validation"
    | "protected_benchmark"
    | "excluded"
    | "not_in_version";
  excludedReason: string | null;
  createdAt: string;
};

export type DatasetRepositoryWarning = {
  code: string;
  severity: "info" | "warning";
  message: string;
  affectedDatasetItemIds: string[];
};

export type DatasetRepositoryLatestVersionSummary = {
  datasetVersionId: string;
  humanReadableId: string;
  status: string;
  createdAt: string;
  trainingItemCount: number;
  validationItemCount: number;
  benchmarkItemCount: number;
  excludedItemCount: number;
};

export type DatasetRepositorySummary = {
  workspaceId: string;
  datasetItemCount: number;
  activeDatasetItemCount: number;
  unassignedCompletedCropCount: number;
  newSinceLatestDatasetVersionCount: number;
  roleCounts: Record<string, number>;
  annotationClassCounts: Record<string, number>;
  annotationSourceCounts: Record<string, number>;
  reviewMethodCounts: Record<string, number>;
  curriculumStageDistribution: Record<string, number>;
  imageQualityDistribution: Record<string, number>;
  hiveConfigurationDistribution: Record<string, number>;
  sourceGroupDistribution: Record<string, number>;
  inspectionDistribution: Record<string, number>;
  inspectionIntentDistribution: Record<string, number>;
  hiveDistribution: Record<string, number>;
  sourceImageDistribution: Record<string, number>;
  latestDatasetVersion: DatasetRepositoryLatestVersionSummary | null;
  persistenceBackend: string;
  databasePurpose: string;
  warnings: DatasetRepositoryWarning[];
};

export type DatasetRepositoryItem = {
  datasetItemId: string;
  humanReadableId: string;
  workspaceId: string;
  datasetRole: DatasetRole;
  status: string;
  sourceEvidenceType: string;
  inspectionId: string | null;
  inspectionDate: string | null;
  inspectionIntent: InspectionIntent | null;
  inspectionPhotoId: string;
  sourceImageId: string;
  sourceFilename: string | null;
  apiaryId: string | null;
  apiaryName: string | null;
  hiveId: string | null;
  hiveName: string | null;
  hiveConfigurationSummary: string | null;
  trainingCropId: string | null;
  cropX: number | null;
  cropY: number | null;
  cropWidth: number | null;
  cropHeight: number | null;
  cropImageWidthPx: number | null;
  cropImageHeightPx: number | null;
  curriculumStage: string | null;
  completeVisibleBeeCount: number;
  partialVisibleBeeCount: number;
  annotationSourceCounts: Record<string, number>;
  reviewMethodCounts: Record<string, number>;
  sourceGroupKey: string | null;
  imageQualityStatus: ImageQualityStatus;
  assignedByUserId: string;
  assignedAt: string;
  assignmentNote: string | null;
  exclusionReason: DatasetExclusionReason | null;
  benchmarkProtected: boolean;
  exportEligibility: string;
  latestDatasetVersionMembership: DatasetVersionMembership | null;
  datasetVersionMemberships: DatasetVersionMembership[];
  isNewSinceLatestDatasetVersion: boolean;
  previewStatus: string;
  thumbnailUrl: string | null;
};

export type DatasetRepositoryItemDetail = DatasetRepositoryItem & {
  reviewedEllipseSnapshots: ReviewedEllipseSnapshot[];
  permissionStatus: string;
  previewUrl: string | null;
};

export type DatasetRepositoryItemList = {
  summary: DatasetRepositorySummary;
  items: DatasetRepositoryItem[];
};

export type Annotation = {
  annotationId: string;
  workspaceId: string;
  inspectionPhotoId: string;
  analysisResultId: string | null;
  labellingSessionId: string | null;
  workflowType: "analysis_result" | "dataset_labelling";
  annotationType: AnnotationType;
  x: number;
  y: number;
  width: number;
  height: number;
  coordinateSpace: "normalized";
  sourceImageWidthPx: number;
  sourceImageHeightPx: number;
  confidence: number;
  source: string;
  createdAt: string;
  latestReviewDecision: ReviewDecision | null;
};

export type InspectionPhotoEvidence = {
  inspectionPhotoId: string;
  filename: string;
  contentType: string;
  viewUrl: string;
  width: number;
  height: number;
};

export type AnalysisEvidence = {
  analysisRunId: string;
  analysisResultId: string;
  inspectionPhoto: InspectionPhotoEvidence;
  analysisResult: AnalysisResult;
  annotations: Annotation[];
  resultKind: "deterministic_stub";
  modelVersion: string;
  caveat: string;
};

export type DatasetLabellingEvidence = {
  inspectionPhoto: InspectionPhotoEvidence;
  labellingSession: DatasetLabellingSession;
  draftAnnotations: Annotation[];
  reviewedAnnotations: Annotation[];
  latestReviewDecisions: ReviewDecision[];
  datasetItem: DatasetItem | null;
  caveat: string;
};

export type TrainingCrop = {
  trainingCropId: string;
  workspaceId: string;
  inspectionPhotoId: string;
  cropX: number;
  cropY: number;
  cropWidth: number;
  cropHeight: number;
  coordinateSpace: "source_image_pixels";
  sourceImageWidthPx: number;
  sourceImageHeightPx: number;
  cropImageWidthPx: number;
  cropImageHeightPx: number;
  curriculumStage: string;
  reviewStatus: TrainingCropReviewStatus;
  visibleBeeStatus: VisibleBeeStatus;
  exclusionReason: TrainingCropExclusionReason | null;
  datasetItemId: string | null;
  datasetRole: DatasetRole | null;
  notes: string | null;
  createdByUserId: string;
  createdAt: string;
  updatedAt: string;
};

export type TrainingCropList = {
  inspectionPhoto: InspectionPhoto;
  trainingCrops: TrainingCrop[];
};

export type OrientedBeeEllipse = {
  annotationId: string;
  workspaceId: string;
  inspectionPhotoId: string;
  trainingCropId: string;
  annotationType: BeeAnnotationType;
  centerX: number;
  centerY: number;
  radiusX: number;
  radiusY: number;
  rotationDegrees: number;
  orientationReliability: OrientationReliability;
  coordinateSpace: "source_image_pixels";
  sourceImageWidthPx: number;
  sourceImageHeightPx: number;
  source: string;
  reviewMethod: "human_from_scratch" | "human_reviewed_candidate" | "imported_reviewed";
  modelCandidateId: string | null;
  candidateConfidence: number | null;
  candidateThreshold: number | null;
  rawModelClass: string | null;
  rawYoloObb: number[] | null;
  candidateReviewDecision: "accepted" | "accepted_with_edits" | null;
  varroaReviewSuitability: VarroaReviewSuitability;
  suspectedVisibleVarroa: boolean;
  varroaReviewSuitabilityUpdatedByUserId: string | null;
  varroaReviewSuitabilityUpdatedAt: string | null;
  suspectedVisibleVarroaUpdatedByUserId: string | null;
  suspectedVisibleVarroaUpdatedAt: string | null;
  createdByUserId: string;
  createdAt: string;
  updatedAt: string;
};

export type BeeAnnotationProposal = {
  proposalId: string;
  workspaceId: string;
  trainingCropId: string;
  modelCandidateId: string;
  modelCandidateHumanReadableId: string;
  annotationType: BeeAnnotationType;
  centerX: number;
  centerY: number;
  radiusX: number;
  radiusY: number;
  rotationDegrees: number;
  coordinateSpace: "source_image_pixels";
  confidence: number;
  threshold: number;
  rawModelClass: string;
  rawYoloObb: number[];
};

export type BeeAnnotationProposalList = {
  workspaceId: string;
  trainingCropId: string;
  modelCandidateId: string;
  modelCandidateHumanReadableId: string;
  threshold: number;
  suggestions: BeeAnnotationProposal[];
  caveat: string;
};

export type ReviewedEllipseSnapshot = {
  annotationId: string;
  annotationType: BeeAnnotationType;
  centerX: number;
  centerY: number;
  radiusX: number;
  radiusY: number;
  rotationDegrees: number;
  orientationReliability: OrientationReliability;
  coordinateSpace: "source_image_pixels";
  sourceImageWidthPx: number;
  sourceImageHeightPx: number;
  source: string;
  createdByUserId: string;
  createdAt: string;
  updatedAt: string;
};

export type TrainingCropEvidence = {
  inspectionPhoto: InspectionPhotoEvidence;
  trainingCrop: TrainingCrop;
  beeEllipses: OrientedBeeEllipse[];
  caveat: string;
};

export type VarroaMarker = {
  varroaMarkerId: string;
  varroaReviewOutcomeId: string;
  markerType: "point";
  x: number;
  y: number;
  createdAt: string;
};

export type VarroaReviewOutcome = {
  varroaReviewOutcomeId: string;
  workspaceId: string;
  inspectionPhotoId: string;
  trainingCropId: string;
  beeAnnotationId: string;
  outcome: VarroaReviewOutcomeValue;
  samplingPurpose: "model_curation";
  datasetSelectionMethod: "human_selected";
  reviewStrength: "single_curator_review";
  annotationSource: "human_from_scratch";
  createdByUserId: string;
  createdAt: string;
  updatedByUserId: string;
  updatedAt: string;
  notes: string | null;
  markers: VarroaMarker[];
};

export type VarroaReviewCandidate = {
  beeAnnotation: OrientedBeeEllipse;
  eligibility: "eligible" | "ineligible";
  ineligibilityReasons: string[];
  reviewOutcome: VarroaReviewOutcome | null;
};

export type VarroaReviewSummary = {
  eligibleBeeCount: number;
  reviewedBeeCount: number;
  visibleVarroaBeeCount: number;
  noVisibleVarroaBeeCount: number;
  notDeterminedBeeCount: number;
  totalMarkerCount: number;
  suspectedVisibleVarroaCueCount: number;
  hardToAssessCueCount: number;
  ineligibleDeferredBeeCount: number;
  caveat: string;
};

export type VarroaReviewCandidateList = {
  workspaceId: string;
  trainingCropId: string;
  candidates: VarroaReviewCandidate[];
  summary: VarroaReviewSummary;
};

export type FrameLevelVarroaResultSummary = {
  workspaceId: string;
  inspectionId: string;
  inspectionPhotoId: string;
  sourceImageFilename: string;
  sourceIntent: InspectionIntent;
  completedTrainingCropCount: number;
  unfinishedTrainingCropCount: number;
  eligibleCompleteBeeCount: number;
  reviewedEligibleBeeCount: number;
  determinateEligibleBeeCount: number;
  visibleVarroaBeeCount: number;
  activeNegativeBeeCount: number;
  notDeterminedBeeCount: number;
  unreviewedEligibleBeeCount: number;
  ineligibleOrNotAssessedBeeCount: number;
  visibleMiteMarkerCount: number;
  reviewCompletionPercent: number;
  determinateVarroaCoveragePercent: number;
  evidenceSource: string;
  readinessState: "not_available" | "partial_evidence" | "complete_reviewed_evidence";
  advisorContextAvailable: boolean;
  caveats: string;
};

export type HeadUpNormalizedBeeCropPreview = {
  workspaceId: string;
  inspectionPhotoId: string;
  trainingCropId: string;
  beeAnnotationId: string;
  annotationType: BeeAnnotationType;
  orientationReliability: OrientationReliability;
  imageWidthPx: number;
  imageHeightPx: number;
  transformVersion: string;
  imageUrl: string;
  transformMetadata: Record<string, unknown>;
};

export type ReviewQueueItemStatus = "available" | "completed" | "cancelled";

export type ReviewQueueOutcomeValue = "approved" | "changes_requested" | "not_determined";

export type ReviewQueueEllipseEvidence = {
  annotationId: string;
  annotationType: BeeAnnotationType;
  centerX: number;
  centerY: number;
  radiusX: number;
  radiusY: number;
  rotationDegrees: number;
  coordinateSpace: "source_image_pixels";
  sourceImageWidthPx: number;
  sourceImageHeightPx: number;
};

export type ReviewQueueEvidenceSnapshot = {
  safeSourceLabel: string;
  trainingCropId: string;
  trainingCropLabel: string;
  inspectionPhotoId: string;
  imageViewUrl: string;
  cropX: number;
  cropY: number;
  cropWidth: number;
  cropHeight: number;
  sourceImageWidthPx: number;
  sourceImageHeightPx: number;
  cropImageWidthPx: number;
  cropImageHeightPx: number;
  reviewedEllipses: ReviewQueueEllipseEvidence[];
  reviewedEllipseCount: number;
  completeVisibleBeeCount: number;
  partialVisibleBeeCount: number;
  cropReviewStatus: TrainingCropReviewStatus;
  visibleBeeStatus: VisibleBeeStatus;
  requestedAt: string;
};

export type ReviewQueueItem = {
  reviewQueueItemId: string;
  humanReadableId: string;
  subjectType: "training_crop";
  subjectId: string;
  status: ReviewQueueItemStatus;
  requestNotes: string | null;
  requestedAt: string;
  cancelledAt: string | null;
  cancellationNotes: string | null;
  completedAt: string | null;
  completedOutcome: ReviewQueueOutcomeValue | null;
  completedReviewerDisplayIdentity: string | null;
  evidenceSnapshot: ReviewQueueEvidenceSnapshot;
};

export type ReviewQueueItemList = {
  reviewQueueItems: ReviewQueueItem[];
};

export type YoloObbLabelEntry = {
  datasetItemId: string;
  trainingCropId: string;
  annotationId: string;
  split: DatasetRole;
  classId: number;
  className: BeeAnnotationType;
  label: string;
  points: number[];
};

export type YoloObbImageEntry = {
  datasetItemId: string;
  trainingCropId: string;
  inspectionPhotoId: string;
  split: DatasetRole;
  cropX: number;
  cropY: number;
  cropWidth: number;
  cropHeight: number;
};

export type YoloObbExcludedItem = {
  datasetItemId: string;
  trainingCropId: string | null;
  datasetRole: DatasetRole;
  reason: string;
};

export type YoloObbExport = {
  exportId: string;
  workspaceId: string;
  exportFormat: "yolo_obb";
  labelConvention: string;
  coordinateBasis: string;
  createdByUserId: string;
  createdAt: string;
  classMap: Record<string, string>;
  includedDatasetItemIds: string[];
  excludedDatasetItems: YoloObbExcludedItem[];
  protectedBenchmarkDatasetItemIds: string[];
  trainingItemCount: number;
  validationItemCount: number;
  benchmarkItemCount: number;
  imageEntries: YoloObbImageEntry[];
  labelEntries: YoloObbLabelEntry[];
  caveat: string;
};

export type GeneratedDatasetExportFile = {
  relativePath: string;
  fileKind: "manifest" | "dataset_yaml" | "image" | "label";
  split: "train" | "val" | "metadata";
  datasetItemId: string | null;
  trainingCropId: string | null;
  inspectionPhotoId: string | null;
  exportFilenameStem: string | null;
  sizeBytes: number;
  sha256: string;
};

export type PhysicalYoloObbExport = {
  exportId: string;
  workspaceId: string;
  exportFormat: "yolo_obb";
  packagePath: string;
  manifestPath: string;
  datasetYamlPath: string;
  createdByUserId: string;
  createdAt: string;
  classMap: Record<string, string>;
  trainingItemCount: number;
  validationItemCount: number;
  benchmarkItemCount: number;
  excludedItemCount: number;
  protectedBenchmarkDatasetItemIds: string[];
  excludedDatasetItems: YoloObbExcludedItem[];
  generatedFiles: GeneratedDatasetExportFile[];
  caveat: string;
};

export type ModelTrainingWarningSeverity = "info" | "warning" | "high";

export type ModelTrainingWarning = {
  code: string;
  severity: ModelTrainingWarningSeverity;
  message: string;
};

export type TrainingAdapterType = "fake" | "ultralytics_yolo_obb" | "torchvision_orientation_classifier";

export type ModelTrainingReadiness = {
  workspaceId: string;
  persistenceBackend: string;
  adapterType: TrainingAdapterType;
  databasePurpose: string;
  realAdapterAvailable: boolean;
  modelPurpose: ModelPurpose;
  datasetVersionId: string | null;
  datasetVersionHumanReadableId: string | null;
  datasetVersionPurpose: string | null;
  eligibleToCreateDatasetVersion: boolean;
  eligibleToStartTraining: boolean;
  activeTrainingRunId: string | null;
  trainingItemCount: number;
  validationItemCount: number;
  benchmarkItemCount: number;
  eligibleTrainingSourceBeeCount: number;
  eligibleValidationSourceBeeCount: number;
  generatedTrainingExampleCount: number;
  generatedValidationExampleCount: number;
  protectedBenchmarkSourceBeeCount: number;
  excludedUnreliableOrientationCount: number;
  excludedPartialVisibleBeeCount: number;
  warnings: ModelTrainingWarning[];
};

export type BeeTrainingReadiness = {
  workspaceId: string;
  datasetVersionId: string | null;
  datasetVersionHumanReadableId: string | null;
  activeTrainingRunId: string | null;
  beeLocalisation: ModelTrainingReadiness;
  beeOrientation: ModelTrainingReadiness;
  eligibleToStartBeeTraining: boolean;
  warnings: ModelTrainingWarning[];
};

export type Artifact = {
  artifactId: string;
  workspaceId: string;
  artifactKind: string;
  relativePath: string;
  mediaType: string;
  sizeBytes: number;
  sha256: string;
  createdAt: string;
};

export type DatasetVersion = {
  datasetVersionId: string;
  humanReadableId: string;
  workspaceId: string;
  purpose: string;
  modelPurpose: ModelPurpose;
  status: string;
  exportFormat: TrainingExportFormat;
  selectionCriteria: Record<string, unknown>;
  manifestHash: string;
  createdByUserId: string;
  createdAt: string;
  includedDatasetItemIds: string[];
  trainingDatasetItemIds: string[];
  validationDatasetItemIds: string[];
  protectedBenchmarkDatasetItemIds: string[];
  excludedDatasetItems: YoloObbExcludedItem[];
  trainingItemCount: number;
  validationItemCount: number;
  benchmarkItemCount: number;
  excludedItemCount: number;
  annotationClassCounts: Record<string, number>;
  annotationSourceCounts: Record<string, number>;
  reviewMethodCounts: Record<string, number>;
  sourceGroupDistribution: Record<string, number>;
  hiveConfigurationDistribution: Record<string, number>;
  curriculumStageDistribution: Record<string, number>;
  imageQualityDistribution: Record<string, number>;
  reportArtifactId: string | null;
  previewArtifactIds: string[];
  warnings: ModelTrainingWarning[];
};

export type TrainingRun = {
  trainingRunId: string;
  humanReadableId: string;
  workspaceId: string;
  datasetVersionId: string;
  modelPurpose: ModelPurpose;
  modelFamily: string;
  modelSize: string;
  baseWeights: string;
  baseWeightsSource: string;
  adapterType: TrainingAdapterType;
  status: "queued" | "running" | "cancelling" | "completed" | "failed" | "cancelled" | "abandoned";
  phase: string;
  databasePurpose: string;
  trainingSettings: Record<string, unknown>;
  randomSeed: number;
  gitCommitSha: string | null;
  gitDirtyStatus: string;
  environmentSummary: Record<string, unknown>;
  warningAcknowledgement: Record<string, unknown> | null;
  startedAt: string | null;
  completedAt: string | null;
  lastHeartbeatAt: string | null;
  lastActivityMessage: string | null;
  progressPercent: number | null;
  currentEpoch: number | null;
  totalEpochs: number | null;
  latestLogExcerpt: string | null;
  cancelRequestedAt: string | null;
  cancelRequestedByUserId: string | null;
  cancelReason: string | null;
  abandonedAt: string | null;
  abandonedByUserId: string | null;
  abandonReason: string | null;
  isStale: boolean;
  staleAfterSeconds: number | null;
  failureCode: string | null;
  failureMessage: string | null;
  artifactIds: string[];
  metricsSummary: Record<string, unknown>;
  modelCandidateId: string | null;
  reportArtifactId: string | null;
  createdByUserId: string;
  createdAt: string;
  purposeNotes: string | null;
};

export type TrainingRunList = {
  trainingRuns: TrainingRun[];
};

export type BeeTrainingStart = {
  workspaceId: string;
  datasetVersionId: string;
  beeLocalisationTrainingRun: TrainingRun;
  beeOrientationTrainingRun: TrainingRun | null;
  message: string;
};

export type TrainingRunDeleteResponse = {
  trainingRunId: string;
  deleted: boolean;
  message: string;
};

export type ModelCandidate = {
  modelCandidateId: string;
  humanReadableId: string;
  displayName: string;
  workspaceId: string;
  trainingRunId: string;
  modelPurpose: ModelPurpose;
  modelFamily: string;
  adapterType: TrainingAdapterType;
  artifactId: string;
  status: string;
  promotionStatus: string;
  notUserFacingReason: string;
  createdAt: string;
};

export type ModelCandidateList = {
  modelCandidates: ModelCandidate[];
};

export type BenchmarkEvaluationWarning = ModelTrainingWarning;

export type BenchmarkEvaluationReadiness = {
  workspaceId: string;
  modelCandidateId: string;
  modelCandidateHumanReadableId: string;
  adapterType: TrainingAdapterType;
  trainingAdapterType: TrainingAdapterType;
  evaluationAdapterType: TrainingAdapterType;
  databasePurpose: string;
  benchmarkItemCount: number;
  eligibleToStartEvaluation: boolean;
  activeModelJobId: string | null;
  activeModelJobType: string | null;
  warnings: BenchmarkEvaluationWarning[];
};

export type OrientationBenchmarkReadiness = BenchmarkEvaluationReadiness & {
  datasetVersionId: string;
  datasetVersionHumanReadableId: string;
  benchmarkItemCount: number;
  eligibleBenchmarkBeeCount: number;
  excludedUnreliableOrientationCount: number;
  excludedPartialVisibleBeeCount: number;
};

export type BenchmarkEvaluationItemResult = {
  datasetItemId: string;
  humanReadableId: string;
  sourceGroupKey: string | null;
  hiveConfigurationFrameStandardId: string | null;
  curriculumStage: string | null;
  groundTruthCount: number;
  predictionCount: number;
  matchedCount: number;
  falsePositiveCount: number;
  falseNegativeCount: number;
};

export type BenchmarkEvaluation = {
  benchmarkEvaluationId: string;
  workspaceId: string;
  humanReadableId: string;
  modelCandidateId: string;
  modelCandidateHumanReadableId: string;
  trainingRunId: string;
  datasetVersionId: string;
  modelPurpose: ModelPurpose;
  status: "queued" | "running" | "cancelling" | "completed" | "failed" | "cancelled";
  phase: string;
  adapterType: TrainingAdapterType;
  trainingAdapterType: TrainingAdapterType;
  evaluationAdapterType: TrainingAdapterType;
  databasePurpose: string;
  confidenceThreshold: number;
  matchStrategy: string;
  benchmarkScope: string;
  startedAt: string | null;
  completedAt: string | null;
  lastHeartbeatAt: string | null;
  lastActivityMessage: string | null;
  progressPercent: number | null;
  latestLogExcerpt: string | null;
  cancelRequestedAt: string | null;
  cancelRequestedByUserId: string | null;
  cancelReason: string | null;
  failureCode: string | null;
  failureMessage: string | null;
  isStale: boolean;
  staleAfterSeconds: number | null;
  warningAcknowledgement: Record<string, unknown> | null;
  warnings: BenchmarkEvaluationWarning[];
  metricsSummary: Record<string, unknown>;
  itemResults: BenchmarkEvaluationItemResult[];
  rawPredictionArtifactId: string | null;
  reportArtifactId: string | null;
  artifactIds: string[];
  createdByUserId: string;
  createdAt: string;
};

export type BenchmarkEvaluationList = {
  benchmarkEvaluations: BenchmarkEvaluation[];
};

export type AnalysisRunDetail = {
  analysisRunId: string;
  workspaceId: string;
  inspectionPhotoId: string;
  status: "queued" | "running" | "completed" | "failed";
  queuedAt: string;
  startedAt: string | null;
  completedAt: string | null;
  failedAt: string | null;
  failureCode: string | null;
  failureMessage: string | null;
  requestedModelVersion: string | null;
  modelVersion: string | null;
  message: string;
  analysisResult: AnalysisResult | null;
};

export type AnalysisRunDetailList = {
  analysisRuns: AnalysisRunDetail[];
};

export type ApiError = {
  code: string;
  message: string;
  status: number;
};

const coreApiUrl = import.meta.env.VITE_CORE_API_URL ?? "http://localhost:8000";

export async function fetchCoreHealth(): Promise<HealthResponse> {
  const response = await fetch(`${coreApiUrl}/healthz`);
  await ensureOk(response);
  return parseHealthResponse(await response.json());
}

export async function fetchDevSession(devUserId: string): Promise<DevSession> {
  const response = await fetch(`${coreApiUrl}/v1/dev/session`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseDevSession(await response.json());
}

export async function fetchDevUsers(): Promise<DevUserList> {
  const response = await fetch(`${coreApiUrl}/v1/dev/users`);
  await ensureOk(response);
  return parseDevUserList(await response.json());
}

export async function acceptWorkspaceDataUseAgreement({
  devUserId,
  workspaceId,
  termsVersion
}: {
  devUserId: string;
  workspaceId: string;
  termsVersion: string;
}): Promise<DevSession> {
  const response = await fetch(`${coreApiUrl}/v1/workspace-data-use-agreements/acceptances`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({ workspace_id: workspaceId, terms_version: termsVersion })
  });
  await ensureOk(response);
  return fetchDevSession(devUserId);
}

export async function createApiary({
  devUserId,
  workspaceId,
  name
}: {
  devUserId: string;
  workspaceId: string;
  name: string;
}): Promise<Apiary> {
  const response = await fetch(`${coreApiUrl}/v1/apiaries`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({ workspace_id: workspaceId, name })
  });
  await ensureOk(response);
  return parseApiary(await response.json());
}

export async function fetchApiaries({
  devUserId,
  workspaceId
}: {
  devUserId: string;
  workspaceId: string;
}): Promise<ApiaryList> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(`${coreApiUrl}/v1/apiaries?${params}`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseApiaryList(await response.json());
}

export async function createHive({
  devUserId,
  apiaryId,
  name
}: {
  devUserId: string;
  apiaryId: string;
  name: string;
}): Promise<Hive> {
  const response = await fetch(`${coreApiUrl}/v1/hives`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({ apiary_id: apiaryId, name })
  });
  await ensureOk(response);
  return parseHive(await response.json());
}

export async function fetchHives({
  devUserId,
  workspaceId,
  apiaryId
}: {
  devUserId: string;
  workspaceId: string;
  apiaryId: string;
}): Promise<HiveList> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(`${coreApiUrl}/v1/apiaries/${apiaryId}/hives?${params}`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseHiveList(await response.json());
}

export async function fetchFrameStandards({
  devUserId
}: {
  devUserId: string;
}): Promise<FrameStandard[]> {
  const response = await fetch(`${coreApiUrl}/v1/frame-standards`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return requireArray(await response.json(), "Frame Standard list response").map(parseFrameStandard);
}

export async function upsertHiveConfiguration({
  devUserId,
  workspaceId,
  hiveId,
  frameStandardId,
  notes
}: {
  devUserId: string;
  workspaceId: string;
  hiveId: string;
  frameStandardId: string;
  notes: string;
}): Promise<HiveConfiguration> {
  const trimmedNotes = notes.trim();
  const response = await fetch(`${coreApiUrl}/v1/hives/${hiveId}/configuration`, {
    method: "PUT",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({
      workspace_id: workspaceId,
      frame_standard_id: frameStandardId,
      notes: trimmedNotes.length > 0 ? trimmedNotes : null
    })
  });
  await ensureOk(response);
  return parseHiveConfiguration(await response.json());
}

export async function fetchHiveConfiguration({
  devUserId,
  workspaceId,
  hiveId
}: {
  devUserId: string;
  workspaceId: string;
  hiveId: string;
}): Promise<HiveConfiguration> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(`${coreApiUrl}/v1/hives/${hiveId}/configuration?${params}`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseHiveConfiguration(await response.json());
}

export async function createInspection({
  devUserId,
  hiveId,
  inspectionDate,
  intent
}: {
  devUserId: string;
  hiveId: string;
  inspectionDate: string;
  intent: InspectionIntent;
}): Promise<Inspection> {
  const response = await fetch(`${coreApiUrl}/v1/inspections`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({ hive_id: hiveId, inspection_date: inspectionDate, intent })
  });
  await ensureOk(response);
  return parseInspection(await response.json());
}

export async function fetchHiveInspections({
  devUserId,
  workspaceId,
  hiveId,
  intent
}: {
  devUserId: string;
  workspaceId: string;
  hiveId: string;
  intent?: InspectionIntent;
}): Promise<InspectionList> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  if (intent) {
    params.set("intent", intent);
  }
  const response = await fetch(`${coreApiUrl}/v1/hives/${hiveId}/inspections?${params}`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseInspectionList(await response.json());
}

export async function fetchInspectionPhotos({
  devUserId,
  workspaceId,
  inspectionId
}: {
  devUserId: string;
  workspaceId: string;
  inspectionId: string;
}): Promise<InspectionPhotoList> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(`${coreApiUrl}/v1/inspections/${inspectionId}/photos?${params}`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseInspectionPhotoList(await response.json());
}

export async function uploadInspectionPhoto({
  devUserId,
  workspaceId,
  inspectionId,
  file
}: {
  devUserId: string;
  workspaceId: string;
  inspectionId: string;
  file: File;
}): Promise<PhotoIntake> {
  const params = new URLSearchParams({ workspace_id: workspaceId, inspection_id: inspectionId });
  const response = await fetch(`${coreApiUrl}/v1/inspection-photos/intake?${params}`, {
    method: "POST",
    headers: {
      ...devAuthHeaders(devUserId),
      "content-type": file.type,
      "x-hivesight-filename": file.name
    },
    body: await file.arrayBuffer()
  });
  await ensureOk(response);
  return parsePhotoIntake(await response.json());
}

export async function fetchAnalysisRunDetail({
  devUserId,
  workspaceId,
  analysisRunId
}: {
  devUserId: string;
  workspaceId: string;
  analysisRunId: string;
}): Promise<AnalysisRunDetail> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(`${coreApiUrl}/v1/analysis-runs/${analysisRunId}/detail?${params}`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseAnalysisRunDetail(await response.json());
}

export async function fetchInspectionAnalysisRuns({
  devUserId,
  workspaceId,
  inspectionId
}: {
  devUserId: string;
  workspaceId: string;
  inspectionId: string;
}): Promise<AnalysisRunDetailList> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(
    `${coreApiUrl}/v1/inspections/${inspectionId}/analysis-runs?${params}`,
    {
      headers: devAuthHeaders(devUserId)
    }
  );
  await ensureOk(response);
  return parseAnalysisRunDetailList(await response.json());
}

export async function processAnalysisRun({
  devUserId,
  workspaceId,
  analysisRunId
}: {
  devUserId: string;
  workspaceId: string;
  analysisRunId: string;
}): Promise<AnalysisRunDetail> {
  const response = await fetch(`${coreApiUrl}/v1/analysis-runs/${analysisRunId}/process`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({ workspace_id: workspaceId })
  });
  await ensureOk(response);
  return parseAnalysisRunDetail(await response.json());
}

export async function fetchAnalysisEvidence({
  devUserId,
  workspaceId,
  analysisRunId
}: {
  devUserId: string;
  workspaceId: string;
  analysisRunId: string;
}): Promise<AnalysisEvidence> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(`${coreApiUrl}/v1/analysis-runs/${analysisRunId}/evidence?${params}`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseAnalysisEvidence(await response.json());
}

export async function fetchInspectionPhotoObjectUrl({
  devUserId,
  viewUrl
}: {
  devUserId: string;
  viewUrl: string;
}): Promise<string> {
  const response = await fetch(toCoreApiUrl(viewUrl), {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

export async function createReviewDecision({
  devUserId,
  workspaceId,
  subjectId,
  decision,
  notes
}: {
  devUserId: string;
  workspaceId: string;
  subjectId: string;
  decision: ReviewDecisionValue;
  notes: string;
}): Promise<ReviewDecision> {
  const trimmedNotes = notes.trim();
  const response = await fetch(`${coreApiUrl}/v1/review-decisions`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({
      workspace_id: workspaceId,
      subject_type: "annotation",
      subject_id: subjectId,
      decision,
      notes: trimmedNotes.length > 0 ? trimmedNotes : null
    })
  });
  await ensureOk(response);
  return parseReviewDecision(await response.json());
}

export async function startDatasetLabellingSession({
  devUserId,
  workspaceId,
  inspectionPhotoId
}: {
  devUserId: string;
  workspaceId: string;
  inspectionPhotoId: string;
}): Promise<DatasetLabellingSession> {
  const response = await fetch(`${coreApiUrl}/v1/dataset-labelling-sessions`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({ workspace_id: workspaceId, inspection_photo_id: inspectionPhotoId })
  });
  await ensureOk(response);
  return parseDatasetLabellingSession(await response.json());
}

export async function updateDatasetLabellingSessionMetadata({
  devUserId,
  workspaceId,
  labellingSessionId,
  sourceGroupKey,
  imageQualityStatus
}: {
  devUserId: string;
  workspaceId: string;
  labellingSessionId: string;
  sourceGroupKey: string;
  imageQualityStatus: ImageQualityStatus;
}): Promise<DatasetLabellingSession> {
  const response = await fetch(`${coreApiUrl}/v1/dataset-labelling-sessions/${labellingSessionId}`, {
    method: "PATCH",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({
      workspace_id: workspaceId,
      source_group_key: sourceGroupKey.trim().length > 0 ? sourceGroupKey.trim() : null,
      image_quality_status: imageQualityStatus
    })
  });
  await ensureOk(response);
  return parseDatasetLabellingSession(await response.json());
}

export async function fetchDatasetLabellingEvidence({
  devUserId,
  workspaceId,
  labellingSessionId
}: {
  devUserId: string;
  workspaceId: string;
  labellingSessionId: string;
}): Promise<DatasetLabellingEvidence> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(
    `${coreApiUrl}/v1/dataset-labelling-sessions/${labellingSessionId}/evidence?${params}`,
    {
      headers: devAuthHeaders(devUserId)
    }
  );
  await ensureOk(response);
  return parseDatasetLabellingEvidence(await response.json());
}

export async function createDatasetItem({
  devUserId,
  workspaceId,
  labellingSessionId,
  datasetRole,
  assignmentNote,
  exclusionReason
}: {
  devUserId: string;
  workspaceId: string;
  labellingSessionId: string;
  datasetRole: DatasetRole;
  assignmentNote: string;
  exclusionReason: DatasetExclusionReason | null;
}): Promise<DatasetItem> {
  const trimmedNote = assignmentNote.trim();
  const response = await fetch(`${coreApiUrl}/v1/dataset-items`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({
      workspace_id: workspaceId,
      labelling_session_id: labellingSessionId,
      dataset_role: datasetRole,
      assignment_note: trimmedNote.length > 0 ? trimmedNote : null,
      exclusion_reason: exclusionReason
    })
  });
  await ensureOk(response);
  return parseDatasetItem(await response.json());
}

export async function createTrainingCropDatasetItem({
  devUserId,
  workspaceId,
  trainingCropId,
  datasetRole,
  sourceGroupKey,
  assignmentNote,
  exclusionReason
}: {
  devUserId: string;
  workspaceId: string;
  trainingCropId: string;
  datasetRole: DatasetRole;
  sourceGroupKey: string;
  assignmentNote: string;
  exclusionReason: DatasetExclusionReason | null;
}): Promise<DatasetItem> {
  const trimmedNote = assignmentNote.trim();
  const trimmedSourceGroupKey = sourceGroupKey.trim();
  const response = await fetch(`${coreApiUrl}/v1/training-crops/${trainingCropId}/dataset-item`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({
      workspace_id: workspaceId,
      dataset_role: datasetRole,
      source_group_key: trimmedSourceGroupKey.length > 0 ? trimmedSourceGroupKey : null,
      assignment_note: trimmedNote.length > 0 ? trimmedNote : null,
      exclusion_reason: exclusionReason
    })
  });
  await ensureOk(response);
  return parseDatasetItem(await response.json());
}

export async function fetchDatasetRepositorySummary({
  devUserId,
  workspaceId
}: {
  devUserId: string;
  workspaceId: string;
}): Promise<DatasetRepositorySummary> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(`${coreApiUrl}/v1/dataset-repository/summary?${params}`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseDatasetRepositorySummary(await response.json());
}

export async function fetchDatasetRepositoryItems({
  devUserId,
  workspaceId,
  datasetRole
}: {
  devUserId: string;
  workspaceId: string;
  datasetRole?: DatasetRole;
}): Promise<DatasetRepositoryItemList> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  if (datasetRole) {
    params.set("dataset_role", datasetRole);
  }
  const response = await fetch(`${coreApiUrl}/v1/dataset-repository/items?${params}`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseDatasetRepositoryItemList(await response.json());
}

export async function fetchDatasetRepositoryItemDetail({
  devUserId,
  workspaceId,
  datasetItemId
}: {
  devUserId: string;
  workspaceId: string;
  datasetItemId: string;
}): Promise<DatasetRepositoryItemDetail> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(
    `${coreApiUrl}/v1/dataset-repository/items/${datasetItemId}?${params}`,
    { headers: devAuthHeaders(devUserId) }
  );
  await ensureOk(response);
  return parseDatasetRepositoryItemDetail(await response.json());
}

export async function createYoloObbExport({
  devUserId,
  workspaceId
}: {
  devUserId: string;
  workspaceId: string;
}): Promise<YoloObbExport> {
  const response = await fetch(`${coreApiUrl}/v1/dataset-exports/yolo-obb`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({ workspace_id: workspaceId })
  });
  await ensureOk(response);
  return parseYoloObbExport(await response.json());
}

export async function createPhysicalYoloObbExport({
  devUserId,
  workspaceId
}: {
  devUserId: string;
  workspaceId: string;
}): Promise<PhysicalYoloObbExport> {
  const response = await fetch(`${coreApiUrl}/v1/dataset-exports/yolo-obb/package`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({ workspace_id: workspaceId })
  });
  await ensureOk(response);
  return parsePhysicalYoloObbExport(await response.json());
}

export async function fetchModelTrainingReadiness({
  devUserId,
  workspaceId,
  modelPurpose = "bee_detector",
  datasetVersionId
}: {
  devUserId: string;
  workspaceId: string;
  modelPurpose?: ModelPurpose;
  datasetVersionId?: string | null;
}): Promise<ModelTrainingReadiness> {
  const params = new URLSearchParams({ workspace_id: workspaceId, model_purpose: modelPurpose });
  if (datasetVersionId) {
    params.set("dataset_version_id", datasetVersionId);
  }
  const response = await fetch(`${coreApiUrl}/v1/model-training/readiness?${params}`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseModelTrainingReadiness(await response.json());
}

export async function fetchBeeTrainingReadiness({
  devUserId,
  workspaceId,
  datasetVersionId
}: {
  devUserId: string;
  workspaceId: string;
  datasetVersionId?: string | null;
}): Promise<BeeTrainingReadiness> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  if (datasetVersionId) {
    params.set("dataset_version_id", datasetVersionId);
  }
  const response = await fetch(`${coreApiUrl}/v1/model-training/bee-training/readiness?${params}`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseBeeTrainingReadiness(await response.json());
}

export async function createDatasetVersion({
  devUserId,
  workspaceId,
  sourceDatasetItemIds
}: {
  devUserId: string;
  workspaceId: string;
  sourceDatasetItemIds?: string[];
}): Promise<DatasetVersion> {
  const response = await fetch(`${coreApiUrl}/v1/model-training/dataset-versions`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({
      workspace_id: workspaceId,
      source_dataset_item_ids: sourceDatasetItemIds ?? null
    })
  });
  await ensureOk(response);
  return parseDatasetVersion(await response.json());
}

export async function startModelTrainingRun({
  devUserId,
  workspaceId,
  datasetVersionId,
  modelPurpose = "bee_detector",
  acknowledgeHighSeverityWarnings
}: {
  devUserId: string;
  workspaceId: string;
  datasetVersionId: string;
  modelPurpose?: ModelPurpose;
  acknowledgeHighSeverityWarnings: boolean;
}): Promise<TrainingRun> {
  const response = await fetch(`${coreApiUrl}/v1/model-training/training-runs`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({
      workspace_id: workspaceId,
      dataset_version_id: datasetVersionId,
      model_purpose: modelPurpose,
      acknowledge_high_severity_warnings: acknowledgeHighSeverityWarnings
    })
  });
  await ensureOk(response);
  return parseTrainingRun(await response.json());
}

export async function startBeeTrainingRun({
  devUserId,
  workspaceId,
  datasetVersionId,
  acknowledgeHighSeverityWarnings
}: {
  devUserId: string;
  workspaceId: string;
  datasetVersionId: string;
  acknowledgeHighSeverityWarnings: boolean;
}): Promise<BeeTrainingStart> {
  const response = await fetch(`${coreApiUrl}/v1/model-training/bee-training/runs`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({
      workspace_id: workspaceId,
      dataset_version_id: datasetVersionId,
      acknowledge_high_severity_warnings: acknowledgeHighSeverityWarnings
    })
  });
  await ensureOk(response);
  return parseBeeTrainingStart(await response.json());
}

export async function fetchTrainingRuns({
  devUserId,
  workspaceId
}: {
  devUserId: string;
  workspaceId: string;
}): Promise<TrainingRunList> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(`${coreApiUrl}/v1/model-training/training-runs?${params}`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseTrainingRunList(await response.json());
}

export async function fetchModelCandidates({
  devUserId,
  workspaceId
}: {
  devUserId: string;
  workspaceId: string;
}): Promise<ModelCandidateList> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(`${coreApiUrl}/v1/model-training/model-candidates?${params}`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseModelCandidateList(await response.json());
}

export async function fetchBenchmarkEvaluationReadiness({
  devUserId,
  workspaceId,
  modelCandidateId
}: {
  devUserId: string;
  workspaceId: string;
  modelCandidateId: string;
}): Promise<BenchmarkEvaluationReadiness> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(
    `${coreApiUrl}/v1/model-training/model-candidates/${modelCandidateId}/benchmark-readiness?${params}`,
    {
      headers: devAuthHeaders(devUserId)
    }
  );
  await ensureOk(response);
  return parseBenchmarkEvaluationReadiness(await response.json());
}

export async function fetchOrientationBenchmarkReadiness({
  devUserId,
  workspaceId,
  modelCandidateId
}: {
  devUserId: string;
  workspaceId: string;
  modelCandidateId: string;
}): Promise<OrientationBenchmarkReadiness> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(
    `${coreApiUrl}/v1/model-training/model-candidates/${modelCandidateId}/orientation-benchmark-readiness?${params}`,
    {
      headers: devAuthHeaders(devUserId)
    }
  );
  await ensureOk(response);
  return parseOrientationBenchmarkReadiness(await response.json());
}

export async function startBenchmarkEvaluation({
  devUserId,
  workspaceId,
  modelCandidateId,
  acknowledgeHighSeverityWarnings
}: {
  devUserId: string;
  workspaceId: string;
  modelCandidateId: string;
  acknowledgeHighSeverityWarnings: boolean;
}): Promise<BenchmarkEvaluation> {
  const response = await fetch(`${coreApiUrl}/v1/model-training/benchmark-evaluations`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({
      workspace_id: workspaceId,
      model_candidate_id: modelCandidateId,
      confidence_threshold: 0.1,
      acknowledge_high_severity_warnings: acknowledgeHighSeverityWarnings
    })
  });
  await ensureOk(response);
  return parseBenchmarkEvaluation(await response.json());
}

export async function startOrientationBenchmarkEvaluation({
  devUserId,
  workspaceId,
  modelCandidateId,
  acknowledgeHighSeverityWarnings
}: {
  devUserId: string;
  workspaceId: string;
  modelCandidateId: string;
  acknowledgeHighSeverityWarnings: boolean;
}): Promise<BenchmarkEvaluation> {
  const response = await fetch(`${coreApiUrl}/v1/model-training/orientation-benchmark-evaluations`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({
      workspace_id: workspaceId,
      model_candidate_id: modelCandidateId,
      acknowledge_high_severity_warnings: acknowledgeHighSeverityWarnings
    })
  });
  await ensureOk(response);
  return parseBenchmarkEvaluation(await response.json());
}

export async function fetchBenchmarkEvaluations({
  devUserId,
  workspaceId
}: {
  devUserId: string;
  workspaceId: string;
}): Promise<BenchmarkEvaluationList> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(`${coreApiUrl}/v1/model-training/benchmark-evaluations?${params}`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseBenchmarkEvaluationList(await response.json());
}

export async function cancelBenchmarkEvaluation({
  devUserId,
  workspaceId,
  benchmarkEvaluationId,
  reason
}: {
  devUserId: string;
  workspaceId: string;
  benchmarkEvaluationId: string;
  reason: string;
}): Promise<BenchmarkEvaluation> {
  const response = await fetch(
    `${coreApiUrl}/v1/model-training/benchmark-evaluations/${benchmarkEvaluationId}/cancel`,
    {
      method: "POST",
      headers: jsonHeaders(devUserId),
      body: JSON.stringify({ workspace_id: workspaceId, reason })
    }
  );
  await ensureOk(response);
  return parseBenchmarkEvaluation(await response.json());
}

export async function cancelTrainingRun({
  devUserId,
  workspaceId,
  trainingRunId,
  reason
}: {
  devUserId: string;
  workspaceId: string;
  trainingRunId: string;
  reason: string;
}): Promise<TrainingRun> {
  const response = await fetch(
    `${coreApiUrl}/v1/model-training/training-runs/${trainingRunId}/cancel`,
    {
      method: "POST",
      headers: jsonHeaders(devUserId),
      body: JSON.stringify({ workspace_id: workspaceId, reason })
    }
  );
  await ensureOk(response);
  return parseTrainingRun(await response.json());
}

export async function abandonTrainingRun({
  devUserId,
  workspaceId,
  trainingRunId,
  reason,
  force = false
}: {
  devUserId: string;
  workspaceId: string;
  trainingRunId: string;
  reason: string;
  force?: boolean;
}): Promise<TrainingRun> {
  const response = await fetch(
    `${coreApiUrl}/v1/model-training/training-runs/${trainingRunId}/abandon`,
    {
      method: "POST",
      headers: jsonHeaders(devUserId),
      body: JSON.stringify({ workspace_id: workspaceId, reason, force })
    }
  );
  await ensureOk(response);
  return parseTrainingRun(await response.json());
}

export async function deleteTrainingRun({
  devUserId,
  workspaceId,
  trainingRunId,
  reason
}: {
  devUserId: string;
  workspaceId: string;
  trainingRunId: string;
  reason: string;
}): Promise<TrainingRunDeleteResponse> {
  const response = await fetch(
    `${coreApiUrl}/v1/model-training/training-runs/${trainingRunId}`,
    {
      method: "DELETE",
      headers: jsonHeaders(devUserId),
      body: JSON.stringify({
        workspace_id: workspaceId,
        reason,
        confirm_no_candidate_or_required_artifacts: true
      })
    }
  );
  await ensureOk(response);
  return parseTrainingRunDeleteResponse(await response.json());
}

export async function createTrainingCrop({
  devUserId,
  workspaceId,
  inspectionPhotoId,
  cropX,
  cropY,
  cropWidth,
  cropHeight,
  sourceImageWidthPx,
  sourceImageHeightPx,
  notes
}: {
  devUserId: string;
  workspaceId: string;
  inspectionPhotoId: string;
  cropX: number;
  cropY: number;
  cropWidth: number;
  cropHeight: number;
  sourceImageWidthPx: number;
  sourceImageHeightPx: number;
  notes: string;
}): Promise<TrainingCrop> {
  const trimmedNotes = notes.trim();
  const response = await fetch(`${coreApiUrl}/v1/training-crops`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({
      workspace_id: workspaceId,
      inspection_photo_id: inspectionPhotoId,
      crop_x: cropX,
      crop_y: cropY,
      crop_width: cropWidth,
      crop_height: cropHeight,
      source_image_width_px: sourceImageWidthPx,
      source_image_height_px: sourceImageHeightPx,
      notes: trimmedNotes.length > 0 ? trimmedNotes : null
    })
  });
  await ensureOk(response);
  return parseTrainingCrop(await response.json());
}

export async function fetchTrainingCropsForPhoto({
  devUserId,
  workspaceId,
  inspectionPhotoId
}: {
  devUserId: string;
  workspaceId: string;
  inspectionPhotoId: string;
}): Promise<TrainingCropList> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(
    `${coreApiUrl}/v1/inspection-photos/${inspectionPhotoId}/training-crops?${params}`,
    { headers: devAuthHeaders(devUserId) }
  );
  await ensureOk(response);
  return parseTrainingCropList(await response.json());
}

export async function updateTrainingCrop({
  devUserId,
  workspaceId,
  trainingCropId,
  cropX,
  cropY,
  cropWidth,
  cropHeight,
  visibleBeeStatus,
  reviewStatus,
  exclusionReason,
  notes
}: {
  devUserId: string;
  workspaceId: string;
  trainingCropId: string;
  cropX?: number;
  cropY?: number;
  cropWidth?: number;
  cropHeight?: number;
  visibleBeeStatus?: VisibleBeeStatus;
  reviewStatus?: TrainingCropReviewStatus;
  exclusionReason?: TrainingCropExclusionReason | null;
  notes?: string;
}): Promise<TrainingCrop> {
  const body: Record<string, unknown> = { workspace_id: workspaceId };
  if (cropX !== undefined) body.crop_x = cropX;
  if (cropY !== undefined) body.crop_y = cropY;
  if (cropWidth !== undefined) body.crop_width = cropWidth;
  if (cropHeight !== undefined) body.crop_height = cropHeight;
  if (visibleBeeStatus !== undefined) body.visible_bee_status = visibleBeeStatus;
  if (reviewStatus !== undefined) body.review_status = reviewStatus;
  if (exclusionReason !== undefined) body.exclusion_reason = exclusionReason;
  if (notes !== undefined) body.notes = notes.trim().length > 0 ? notes.trim() : null;

  const response = await fetch(`${coreApiUrl}/v1/training-crops/${trainingCropId}`, {
    method: "PATCH",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify(body)
  });
  await ensureOk(response);
  return parseTrainingCrop(await response.json());
}

export async function deleteTrainingCrop({
  devUserId,
  workspaceId,
  trainingCropId
}: {
  devUserId: string;
  workspaceId: string;
  trainingCropId: string;
}): Promise<void> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(`${coreApiUrl}/v1/training-crops/${trainingCropId}?${params}`, {
    method: "DELETE",
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
}

export async function fetchTrainingCropEvidence({
  devUserId,
  workspaceId,
  trainingCropId
}: {
  devUserId: string;
  workspaceId: string;
  trainingCropId: string;
}): Promise<TrainingCropEvidence> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(`${coreApiUrl}/v1/training-crops/${trainingCropId}/evidence?${params}`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseTrainingCropEvidence(await response.json());
}

export async function fetchVarroaReviewCandidates({
  devUserId,
  workspaceId,
  trainingCropId
}: {
  devUserId: string;
  workspaceId: string;
  trainingCropId: string;
}): Promise<VarroaReviewCandidateList> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(
    `${coreApiUrl}/v1/training-crops/${trainingCropId}/varroa-review-candidates?${params}`,
    { headers: devAuthHeaders(devUserId) }
  );
  await ensureOk(response);
  return parseVarroaReviewCandidateList(await response.json());
}

export async function fetchPhotoVisibleVarroaSummary({
  devUserId,
  workspaceId,
  inspectionPhotoId
}: {
  devUserId: string;
  workspaceId: string;
  inspectionPhotoId: string;
}): Promise<FrameLevelVarroaResultSummary> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(
    `${coreApiUrl}/v1/inspection-photos/${inspectionPhotoId}/photo-visible-varroa-summary?${params}`,
    { headers: devAuthHeaders(devUserId) }
  );
  await ensureOk(response);
  return parseFrameLevelVarroaResultSummary(await response.json());
}

export async function fetchHeadUpNormalizedBeeCropPreview({
  devUserId,
  workspaceId,
  trainingCropId,
  beeAnnotationId
}: {
  devUserId: string;
  workspaceId: string;
  trainingCropId: string;
  beeAnnotationId: string;
}): Promise<HeadUpNormalizedBeeCropPreview> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(
    `${coreApiUrl}/v1/training-crops/${trainingCropId}/varroa-review-candidates/${beeAnnotationId}/head-up-normalized-preview?${params}`,
    { headers: devAuthHeaders(devUserId) }
  );
  await ensureOk(response);
  return parseHeadUpNormalizedBeeCropPreview(await response.json());
}

export async function fetchHeadUpNormalizedBeeCropImageObjectUrl({
  devUserId,
  imageUrl
}: {
  devUserId: string;
  imageUrl: string;
}): Promise<string> {
  const response = await fetch(toCoreApiUrl(imageUrl), {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

export async function saveVarroaReviewOutcome({
  devUserId,
  workspaceId,
  trainingCropId,
  beeAnnotationId,
  outcome,
  markers,
  notes
}: {
  devUserId: string;
  workspaceId: string;
  trainingCropId: string;
  beeAnnotationId: string;
  outcome: VarroaReviewOutcomeValue;
  markers: { x: number; y: number }[];
  notes: string;
}): Promise<VarroaReviewOutcome> {
  const response = await fetch(
    `${coreApiUrl}/v1/training-crops/${trainingCropId}/varroa-review-candidates/${beeAnnotationId}/outcome`,
    {
      method: "PUT",
      headers: jsonHeaders(devUserId),
      body: JSON.stringify({
        workspace_id: workspaceId,
        outcome,
        markers,
        notes: notes.trim().length > 0 ? notes.trim() : null
      })
    }
  );
  await ensureOk(response);
  return parseVarroaReviewOutcome(await response.json());
}

export async function requestTrainingCropReview({
  devUserId,
  workspaceId,
  trainingCropId,
  requestNotes
}: {
  devUserId: string;
  workspaceId: string;
  trainingCropId: string;
  requestNotes: string;
}): Promise<ReviewQueueItem> {
  const trimmedNotes = requestNotes.trim();
  const response = await fetch(`${coreApiUrl}/v1/review-queue/items`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({
      workspace_id: workspaceId,
      training_crop_id: trainingCropId,
      request_notes: trimmedNotes.length > 0 ? trimmedNotes : null
    })
  });
  await ensureOk(response);
  return parseReviewQueueItem(await response.json());
}

export async function fetchReviewWork({
  devUserId
}: {
  devUserId: string;
}): Promise<ReviewQueueItemList> {
  const response = await fetch(`${coreApiUrl}/v1/review-queue/work`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseReviewQueueItemList(await response.json());
}

export async function fetchReviewHistory({
  devUserId
}: {
  devUserId: string;
}): Promise<ReviewQueueItemList> {
  const response = await fetch(`${coreApiUrl}/v1/review-queue/history`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseReviewQueueItemList(await response.json());
}

export async function fetchRequestedReviews({
  devUserId,
  workspaceId
}: {
  devUserId: string;
  workspaceId: string;
}): Promise<ReviewQueueItemList> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(`${coreApiUrl}/v1/review-queue/requested?${params}`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseReviewQueueItemList(await response.json());
}

export async function fetchReviewWorkItem({
  devUserId,
  reviewQueueItemId
}: {
  devUserId: string;
  reviewQueueItemId: string;
}): Promise<ReviewQueueItem> {
  const response = await fetch(`${coreApiUrl}/v1/review-queue/items/${reviewQueueItemId}`, {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  return parseReviewQueueItem(await response.json());
}

export async function completeReviewWorkItem({
  devUserId,
  reviewQueueItemId,
  reviewOutcome,
  reviewNotes
}: {
  devUserId: string;
  reviewQueueItemId: string;
  reviewOutcome: ReviewQueueOutcomeValue;
  reviewNotes: string;
}): Promise<ReviewQueueItem> {
  const trimmedNotes = reviewNotes.trim();
  const response = await fetch(`${coreApiUrl}/v1/review-queue/items/${reviewQueueItemId}/outcomes`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({
      review_outcome: reviewOutcome,
      review_notes: trimmedNotes.length > 0 ? trimmedNotes : null
    })
  });
  await ensureOk(response);
  return parseReviewQueueItem(await response.json());
}

export async function cancelReviewWorkItem({
  devUserId,
  reviewQueueItemId,
  cancellationNotes
}: {
  devUserId: string;
  reviewQueueItemId: string;
  cancellationNotes: string;
}): Promise<ReviewQueueItem> {
  const response = await fetch(`${coreApiUrl}/v1/review-queue/items/${reviewQueueItemId}/cancel`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({ cancellation_notes: cancellationNotes.trim() })
  });
  await ensureOk(response);
  return parseReviewQueueItem(await response.json());
}

export async function fetchReviewQueueImageObjectUrl({
  devUserId,
  imageViewUrl
}: {
  devUserId: string;
  imageViewUrl: string;
}): Promise<string> {
  const response = await fetch(toCoreApiUrl(imageViewUrl), {
    headers: devAuthHeaders(devUserId)
  });
  await ensureOk(response);
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

export async function createTrainingCropEllipse({
  devUserId,
  workspaceId,
  trainingCropId,
  annotationType,
  centerX,
  centerY,
  radiusX,
  radiusY,
  rotationDegrees,
  orientationReliability,
  provenance
}: {
  devUserId: string;
  workspaceId: string;
  trainingCropId: string;
  annotationType: BeeAnnotationType;
  centerX: number;
  centerY: number;
  radiusX: number;
  radiusY: number;
  rotationDegrees: number;
  orientationReliability?: OrientationReliability;
  provenance?: {
    source: "model_candidate";
    reviewMethod: "human_reviewed_candidate";
    modelCandidateId: string;
    candidateConfidence: number;
    candidateThreshold: number;
    rawModelClass: string;
    rawYoloObb: number[];
    candidateReviewDecision: "accepted" | "accepted_with_edits";
  };
}): Promise<OrientedBeeEllipse> {
  const body: Record<string, unknown> = {
    workspace_id: workspaceId,
    annotation_type: annotationType,
    center_x: centerX,
    center_y: centerY,
    radius_x: radiusX,
    radius_y: radiusY,
    rotation_degrees: rotationDegrees,
    orientation_reliability: orientationReliability ?? "reliable"
  };
  if (provenance) {
    body.source = provenance.source;
    body.review_method = provenance.reviewMethod;
    body.model_candidate_id = provenance.modelCandidateId;
    body.candidate_confidence = provenance.candidateConfidence;
    body.candidate_threshold = provenance.candidateThreshold;
    body.raw_model_class = provenance.rawModelClass;
    body.raw_yolo_obb = provenance.rawYoloObb;
    body.candidate_review_decision = provenance.candidateReviewDecision;
  }
  const response = await fetch(`${coreApiUrl}/v1/training-crops/${trainingCropId}/bee-ellipses`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify(body)
  });
  await ensureOk(response);
  return parseOrientedBeeEllipse(await response.json());
}

export async function suggestTrainingCropBeeAnnotations({
  devUserId,
  workspaceId,
  trainingCropId,
  modelCandidateId,
  confidenceThreshold,
  maxSuggestions = 50
}: {
  devUserId: string;
  workspaceId: string;
  trainingCropId: string;
  modelCandidateId: string | null;
  confidenceThreshold: number;
  maxSuggestions?: number;
}): Promise<BeeAnnotationProposalList> {
  const response = await fetch(
    `${coreApiUrl}/v1/training-crops/${trainingCropId}/candidate-bee-annotations`,
    {
      method: "POST",
      headers: jsonHeaders(devUserId),
      body: JSON.stringify({
        workspace_id: workspaceId,
        model_candidate_id: modelCandidateId,
        confidence_threshold: confidenceThreshold,
        max_suggestions: maxSuggestions
      })
    }
  );
  await ensureOk(response);
  return parseBeeAnnotationProposalList(await response.json());
}

export async function updateTrainingCropEllipse({
  devUserId,
  workspaceId,
  annotationId,
  annotationType,
  centerX,
  centerY,
  radiusX,
  radiusY,
  rotationDegrees,
  orientationReliability,
  varroaReviewSuitability,
  suspectedVisibleVarroa
}: {
  devUserId: string;
  workspaceId: string;
  annotationId: string;
  annotationType?: BeeAnnotationType;
  centerX?: number;
  centerY?: number;
  radiusX?: number;
  radiusY?: number;
  rotationDegrees?: number;
  orientationReliability?: OrientationReliability;
  varroaReviewSuitability?: VarroaReviewSuitability;
  suspectedVisibleVarroa?: boolean;
}): Promise<OrientedBeeEllipse> {
  const body: Record<string, unknown> = { workspace_id: workspaceId };
  if (annotationType !== undefined) body.annotation_type = annotationType;
  if (centerX !== undefined) body.center_x = centerX;
  if (centerY !== undefined) body.center_y = centerY;
  if (radiusX !== undefined) body.radius_x = radiusX;
  if (radiusY !== undefined) body.radius_y = radiusY;
  if (rotationDegrees !== undefined) body.rotation_degrees = rotationDegrees;
  if (orientationReliability !== undefined) body.orientation_reliability = orientationReliability;
  if (varroaReviewSuitability !== undefined) body.varroa_review_suitability = varroaReviewSuitability;
  if (suspectedVisibleVarroa !== undefined) body.suspected_visible_varroa = suspectedVisibleVarroa;
  const response = await fetch(`${coreApiUrl}/v1/training-crop-bee-ellipses/${annotationId}`, {
    method: "PATCH",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify(body)
  });
  await ensureOk(response);
  return parseOrientedBeeEllipse(await response.json());
}

export async function deleteTrainingCropEllipse({
  devUserId,
  workspaceId,
  annotationId
}: {
  devUserId: string;
  workspaceId: string;
  annotationId: string;
}): Promise<void> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  const response = await fetch(
    `${coreApiUrl}/v1/training-crop-bee-ellipses/${annotationId}?${params}`,
    {
      method: "DELETE",
      headers: devAuthHeaders(devUserId)
    }
  );
  await ensureOk(response);
}

function devAuthHeaders(devUserId: string): HeadersInit {
  return { "x-hivesight-dev-user-id": devUserId };
}

function jsonHeaders(devUserId: string): HeadersInit {
  return { ...devAuthHeaders(devUserId), "content-type": "application/json" };
}

async function ensureOk(response: Response): Promise<void> {
  if (response.ok) {
    return;
  }

  let message = `Core API request failed: ${response.status}`;
  let code = "core_api_request_failed";
  try {
    const value = await response.json();
    if (isRecord(value) && isRecord(value.detail)) {
      if (typeof value.detail.message === "string") {
        message = value.detail.message;
      }
      if (typeof value.detail.code === "string") {
        code = value.detail.code;
      }
    }
  } catch {
    // Keep the transport-level fallback message.
  }
  throw { code, message, status: response.status } satisfies ApiError;
}

function parseHealthResponse(value: unknown): HealthResponse {
  const record = requireRecord(value, "Core API health response");
  return {
    service: requireString(record.service, "service"),
    status: requireString(record.status, "status"),
    boundary: requireString(record.boundary, "boundary"),
    persistenceBackend:
      record.persistence_backend === undefined
        ? null
        : optionalString(record.persistence_backend, "persistence_backend"),
    databasePurpose:
      record.database_purpose === undefined
        ? null
        : optionalString(record.database_purpose, "database_purpose")
  };
}

function parseDevSession(value: unknown): DevSession {
  const record = requireRecord(value, "Dev session response");
  return {
    userId: requireString(record.user_id, "user_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    role: requireString(record.role, "role"),
    reviewerCapability: requireBoolean(record.reviewer_capability, "reviewer_capability"),
    datasetCuratorCapability: requireBoolean(
      record.dataset_curator_capability,
      "dataset_curator_capability"
    ),
    workspaceDataUseAgreementStatus: requireAgreementStatus(
      record.workspace_data_use_agreement_status
    ),
    workspaceDataUseAgreementTermsVersion: optionalString(
      record.workspace_data_use_agreement_terms_version,
      "workspace_data_use_agreement_terms_version"
    )
  };
}

function parseDevUser(value: unknown): DevUser {
  const record = requireRecord(value, "Development User response");
  return {
    userId: requireString(record.user_id, "user_id"),
    displayName: requireString(record.display_name, "display_name"),
    devUserCode: requireString(record.dev_user_code, "dev_user_code"),
    description: requireString(record.description, "description"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    workspaceDisplayName: requireString(record.workspace_display_name, "workspace_display_name"),
    workspaceMembershipRole: requireString(
      record.workspace_membership_role,
      "workspace_membership_role"
    ),
    reviewerCapability: requireBoolean(record.reviewer_capability, "reviewer_capability"),
    datasetCuratorCapability: requireBoolean(
      record.dataset_curator_capability,
      "dataset_curator_capability"
    ),
    contributorAccessScope: requireString(
      record.contributor_access_scope,
      "contributor_access_scope"
    ),
    isDefault: requireBoolean(record.is_default, "is_default")
  };
}

function parseDevUserList(value: unknown): DevUserList {
  const record = requireRecord(value, "Development User list response");
  return {
    devUsers: requireArray(record.dev_users, "dev_users").map(parseDevUser)
  };
}

function parseApiary(value: unknown): Apiary {
  const record = requireRecord(value, "Apiary response");
  return {
    apiaryId: requireString(record.apiary_id, "apiary_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    name: requireString(record.name, "name")
  };
}

function parseApiaryList(value: unknown): ApiaryList {
  const record = requireRecord(value, "Apiary list response");
  return {
    apiaries: requireArray(record.apiaries, "apiaries").map(parseApiary)
  };
}

function parseHive(value: unknown): Hive {
  const record = requireRecord(value, "Hive response");
  return {
    hiveId: requireString(record.hive_id, "hive_id"),
    apiaryId: requireString(record.apiary_id, "apiary_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    name: requireString(record.name, "name")
  };
}

function parseHiveList(value: unknown): HiveList {
  const record = requireRecord(value, "Hive list response");
  return {
    hives: requireArray(record.hives, "hives").map(parseHive)
  };
}

function parseFrameStandard(value: unknown): FrameStandard {
  const record = requireRecord(value, "Frame Standard response");
  return {
    frameStandardId: requireString(record.frame_standard_id, "frame_standard_id"),
    displayName: requireString(record.display_name, "display_name"),
    hiveType: requireString(record.hive_type, "hive_type"),
    frameUse: requireString(record.frame_use, "frame_use"),
    topBarLengthMm: optionalNumber(record.top_bar_length_mm, "top_bar_length_mm"),
    bottomBarLengthMm: optionalNumber(record.bottom_bar_length_mm, "bottom_bar_length_mm"),
    sideBarHeightMm: optionalNumber(record.side_bar_height_mm, "side_bar_height_mm"),
    measurementUnit: requireString(record.measurement_unit, "measurement_unit"),
    sourceNote: requireString(record.source_note, "source_note"),
    status: requireFrameStandardStatus(record.status)
  };
}

function parseHiveConfiguration(value: unknown): HiveConfiguration {
  const record = requireRecord(value, "Hive Configuration response");
  return {
    hiveConfigurationId: requireString(
      record.hive_configuration_id,
      "hive_configuration_id"
    ),
    hiveId: requireString(record.hive_id, "hive_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    hiveType: requireString(record.hive_type, "hive_type"),
    frameUse: requireString(record.frame_use, "frame_use"),
    frameStandardId: requireString(record.frame_standard_id, "frame_standard_id"),
    frameStandard: parseFrameStandard(record.frame_standard),
    notes: optionalString(record.notes, "notes"),
    status: requireHiveConfigurationStatus(record.status),
    effectiveFrom: requireString(record.effective_from, "effective_from"),
    configuredByUserId: requireString(record.configured_by_user_id, "configured_by_user_id"),
    configuredAt: requireString(record.configured_at, "configured_at"),
    updatedAt: requireString(record.updated_at, "updated_at")
  };
}

function parseInspection(value: unknown): Inspection {
  const record = requireRecord(value, "Inspection response");
  return {
    inspectionId: requireString(record.inspection_id, "inspection_id"),
    hiveId: requireString(record.hive_id, "hive_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    inspectionDate: requireString(record.inspection_date, "inspection_date"),
    intent: requireInspectionIntent(record.intent)
  };
}

function parsePhotoIntake(value: unknown): PhotoIntake {
  const record = requireRecord(value, "Photo intake response");
  const analysisRun = requireRecord(record.analysis_run, "Analysis run response");
  return {
    inspectionPhoto: parseInspectionPhoto(record.inspection_photo),
    analysisRun: {
      analysisRunId: requireString(analysisRun.analysis_run_id, "analysis_run_id"),
      inspectionPhotoId: requireString(analysisRun.inspection_photo_id, "inspection_photo_id"),
      status: requireAnalysisStatus(analysisRun.status),
      queuedAt: requireString(analysisRun.queued_at, "queued_at"),
      message: requireString(analysisRun.message, "message")
    }
  };
}

function parseInspectionPhotoList(value: unknown): InspectionPhotoList {
  const record = requireRecord(value, "Inspection photo list response");
  return {
    inspection: parseInspection(record.inspection),
    photos: requireArray(record.photos, "photos").map(parseInspectionPhoto)
  };
}

function parseInspectionList(value: unknown): InspectionList {
  const record = requireRecord(value, "Inspection list response");
  return {
    inspections: requireArray(record.inspections, "inspections").map(parseInspection)
  };
}

function parseInspectionPhoto(value: unknown): InspectionPhoto {
  const photo = requireRecord(value, "Inspection photo response");
  return {
    inspectionPhotoId: requireString(photo.inspection_photo_id, "inspection_photo_id"),
    inspectionId: requireString(photo.inspection_id, "inspection_id"),
    workspaceId: requireString(photo.workspace_id, "workspace_id"),
    originalObjectKey: requireString(photo.original_object_key, "original_object_key"),
    filename: requireString(photo.filename, "filename"),
    contentType: requireString(photo.content_type, "content_type"),
    sizeBytes: requireNumber(photo.size_bytes, "size_bytes"),
    uploadStatus: requireUploadStatus(photo.upload_status),
    uploadedByUserId: requireString(photo.uploaded_by_user_id, "uploaded_by_user_id"),
    uploadedAt: requireString(photo.uploaded_at, "uploaded_at")
  };
}

function parseAnalysisRunDetail(value: unknown): AnalysisRunDetail {
  const record = requireRecord(value, "Analysis run detail response");
  return {
    analysisRunId: requireString(record.analysis_run_id, "analysis_run_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    inspectionPhotoId: requireString(record.inspection_photo_id, "inspection_photo_id"),
    status: requireAnalysisStatus(record.status),
    queuedAt: requireString(record.queued_at, "queued_at"),
    startedAt: optionalString(record.started_at, "started_at"),
    completedAt: optionalString(record.completed_at, "completed_at"),
    failedAt: optionalString(record.failed_at, "failed_at"),
    failureCode: optionalString(record.failure_code, "failure_code"),
    failureMessage: optionalString(record.failure_message, "failure_message"),
    requestedModelVersion: optionalString(record.requested_model_version, "requested_model_version"),
    modelVersion: optionalString(record.model_version, "model_version"),
    message: requireString(record.message, "message"),
    analysisResult:
      record.analysis_result === null ? null : parseAnalysisResult(record.analysis_result)
  };
}

function parseAnalysisRunDetailList(value: unknown): AnalysisRunDetailList {
  const record = requireRecord(value, "Analysis run detail list response");
  return {
    analysisRuns: requireArray(record.analysis_runs, "analysis_runs").map(parseAnalysisRunDetail)
  };
}

function parseAnalysisResult(value: unknown): AnalysisResult {
  const record = requireRecord(value, "Analysis result response");
  return {
    analysisResultId: requireString(record.analysis_result_id, "analysis_result_id"),
    analysisRunId: requireString(record.analysis_run_id, "analysis_run_id"),
    inspectionPhotoId: requireString(record.inspection_photo_id, "inspection_photo_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    modelVersion: requireString(record.model_version, "model_version"),
    completeVisibleBeeCount: requireNumber(
      record.complete_visible_bee_count,
      "complete_visible_bee_count"
    ),
    partialVisibleBeeCount: requireNumber(
      record.partial_visible_bee_count,
      "partial_visible_bee_count"
    ),
    likelyVarroaDetections: requireNumber(
      record.likely_varroa_detections,
      "likely_varroa_detections"
    ),
    taggedImageObjectKey: optionalString(record.tagged_image_object_key, "tagged_image_object_key"),
    resultKind: requireResultKind(record.result_kind),
    completedAt: requireString(record.completed_at, "completed_at")
  };
}

function parseAnalysisEvidence(value: unknown): AnalysisEvidence {
  const record = requireRecord(value, "Analysis evidence response");
  const annotations = requireArray(record.annotations, "annotations").map(parseAnnotation);
  return {
    analysisRunId: requireString(record.analysis_run_id, "analysis_run_id"),
    analysisResultId: requireString(record.analysis_result_id, "analysis_result_id"),
    inspectionPhoto: parseInspectionPhotoEvidence(record.inspection_photo),
    analysisResult: parseAnalysisResult(record.analysis_result),
    annotations,
    resultKind: requireResultKind(record.result_kind),
    modelVersion: requireString(record.model_version, "model_version"),
    caveat: requireString(record.caveat, "caveat")
  };
}

function parseDatasetLabellingEvidence(value: unknown): DatasetLabellingEvidence {
  const record = requireRecord(value, "Dataset labelling evidence response");
  return {
    inspectionPhoto: parseInspectionPhotoEvidence(record.inspection_photo),
    labellingSession: parseDatasetLabellingSession(record.labelling_session),
    draftAnnotations: requireArray(record.draft_annotations, "draft_annotations").map(
      parseAnnotation
    ),
    reviewedAnnotations: requireArray(record.reviewed_annotations, "reviewed_annotations").map(
      parseAnnotation
    ),
    latestReviewDecisions: requireArray(
      record.latest_review_decisions,
      "latest_review_decisions"
    ).map(parseReviewDecision),
    datasetItem: record.dataset_item === null ? null : parseDatasetItem(record.dataset_item),
    caveat: requireString(record.caveat, "caveat")
  };
}

function parseTrainingCropList(value: unknown): TrainingCropList {
  const record = requireRecord(value, "Training Crop list response");
  return {
    inspectionPhoto: parseInspectionPhoto(record.inspection_photo),
    trainingCrops: requireArray(record.training_crops, "training_crops").map(parseTrainingCrop)
  };
}

function parseTrainingCropEvidence(value: unknown): TrainingCropEvidence {
  const record = requireRecord(value, "Training Crop evidence response");
  return {
    inspectionPhoto: parseInspectionPhotoEvidence(record.inspection_photo),
    trainingCrop: parseTrainingCrop(record.training_crop),
    beeEllipses: requireArray(record.bee_ellipses, "bee_ellipses").map(parseOrientedBeeEllipse),
    caveat: requireString(record.caveat, "caveat")
  };
}

function parseReviewQueueItemList(value: unknown): ReviewQueueItemList {
  const record = requireRecord(value, "Review Queue Item list response");
  return {
    reviewQueueItems: requireArray(record.review_queue_items, "review_queue_items").map(
      parseReviewQueueItem
    )
  };
}

function parseReviewQueueItem(value: unknown): ReviewQueueItem {
  const record = requireRecord(value, "Review Queue Item response");
  return {
    reviewQueueItemId: requireString(record.review_queue_item_id, "review_queue_item_id"),
    humanReadableId: requireString(record.human_readable_id, "human_readable_id"),
    subjectType: requireReviewQueueSubjectType(record.subject_type),
    subjectId: requireString(record.subject_id, "subject_id"),
    status: requireReviewQueueItemStatus(record.status),
    requestNotes: optionalString(record.request_notes, "request_notes"),
    requestedAt: requireString(record.requested_at, "requested_at"),
    cancelledAt: optionalString(record.cancelled_at, "cancelled_at"),
    cancellationNotes: optionalString(record.cancellation_notes, "cancellation_notes"),
    completedAt: optionalString(record.completed_at, "completed_at"),
    completedOutcome:
      record.completed_outcome === null
        ? null
        : requireReviewQueueOutcomeValue(record.completed_outcome),
    completedReviewerDisplayIdentity: optionalString(
      record.completed_reviewer_display_identity,
      "completed_reviewer_display_identity"
    ),
    evidenceSnapshot: parseReviewQueueEvidenceSnapshot(record.evidence_snapshot)
  };
}

function parseReviewQueueEvidenceSnapshot(value: unknown): ReviewQueueEvidenceSnapshot {
  const record = requireRecord(value, "Review Queue evidence snapshot");
  return {
    safeSourceLabel: requireString(record.safe_source_label, "safe_source_label"),
    trainingCropId: requireString(record.training_crop_id, "training_crop_id"),
    trainingCropLabel: requireString(record.training_crop_label, "training_crop_label"),
    inspectionPhotoId: requireString(record.inspection_photo_id, "inspection_photo_id"),
    imageViewUrl: requireString(record.image_view_url, "image_view_url"),
    cropX: requireNumber(record.crop_x, "crop_x"),
    cropY: requireNumber(record.crop_y, "crop_y"),
    cropWidth: requireNumber(record.crop_width, "crop_width"),
    cropHeight: requireNumber(record.crop_height, "crop_height"),
    sourceImageWidthPx: requireNumber(record.source_image_width_px, "source_image_width_px"),
    sourceImageHeightPx: requireNumber(record.source_image_height_px, "source_image_height_px"),
    cropImageWidthPx: requireNumber(record.crop_image_width_px, "crop_image_width_px"),
    cropImageHeightPx: requireNumber(record.crop_image_height_px, "crop_image_height_px"),
    reviewedEllipses: requireArray(record.reviewed_ellipses, "reviewed_ellipses").map(
      parseReviewQueueEllipseEvidence
    ),
    reviewedEllipseCount: requireNumber(record.reviewed_ellipse_count, "reviewed_ellipse_count"),
    completeVisibleBeeCount: requireNumber(
      record.complete_visible_bee_count,
      "complete_visible_bee_count"
    ),
    partialVisibleBeeCount: requireNumber(
      record.partial_visible_bee_count,
      "partial_visible_bee_count"
    ),
    cropReviewStatus: requireTrainingCropReviewStatus(record.crop_review_status),
    visibleBeeStatus: requireVisibleBeeStatus(record.visible_bee_status),
    requestedAt: requireString(record.requested_at, "requested_at")
  };
}

function parseReviewQueueEllipseEvidence(value: unknown): ReviewQueueEllipseEvidence {
  const record = requireRecord(value, "Review Queue ellipse evidence");
  return {
    annotationId: requireString(record.annotation_id, "annotation_id"),
    annotationType: requireBeeAnnotationType(record.annotation_type),
    centerX: requireNumber(record.center_x, "center_x"),
    centerY: requireNumber(record.center_y, "center_y"),
    radiusX: requireNumber(record.radius_x, "radius_x"),
    radiusY: requireNumber(record.radius_y, "radius_y"),
    rotationDegrees: requireNumber(record.rotation_degrees, "rotation_degrees"),
    coordinateSpace: requireSourceImagePixelCoordinateSpace(record.coordinate_space),
    sourceImageWidthPx: requireNumber(record.source_image_width_px, "source_image_width_px"),
    sourceImageHeightPx: requireNumber(record.source_image_height_px, "source_image_height_px")
  };
}

function parseTrainingCrop(value: unknown): TrainingCrop {
  const record = requireRecord(value, "Training Crop response");
  return {
    trainingCropId: requireString(record.training_crop_id, "training_crop_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    inspectionPhotoId: requireString(record.inspection_photo_id, "inspection_photo_id"),
    cropX: requireNumber(record.crop_x, "crop_x"),
    cropY: requireNumber(record.crop_y, "crop_y"),
    cropWidth: requireNumber(record.crop_width, "crop_width"),
    cropHeight: requireNumber(record.crop_height, "crop_height"),
    coordinateSpace: requireSourceImagePixelCoordinateSpace(record.coordinate_space),
    sourceImageWidthPx: requireNumber(record.source_image_width_px, "source_image_width_px"),
    sourceImageHeightPx: requireNumber(record.source_image_height_px, "source_image_height_px"),
    cropImageWidthPx: requireNumber(record.crop_image_width_px, "crop_image_width_px"),
    cropImageHeightPx: requireNumber(record.crop_image_height_px, "crop_image_height_px"),
    curriculumStage: requireString(record.curriculum_stage, "curriculum_stage"),
    reviewStatus: requireTrainingCropReviewStatus(record.review_status),
    visibleBeeStatus: requireVisibleBeeStatus(record.visible_bee_status),
    exclusionReason:
      record.exclusion_reason === null
        ? null
        : requireTrainingCropExclusionReason(record.exclusion_reason),
    datasetItemId: optionalString(record.dataset_item_id, "dataset_item_id"),
    datasetRole: record.dataset_role === null ? null : requireDatasetRole(record.dataset_role),
    notes: optionalString(record.notes, "notes"),
    createdByUserId: requireString(record.created_by_user_id, "created_by_user_id"),
    createdAt: requireString(record.created_at, "created_at"),
    updatedAt: requireString(record.updated_at, "updated_at")
  };
}

function parseOrientedBeeEllipse(value: unknown): OrientedBeeEllipse {
  const record = requireRecord(value, "Oriented bee ellipse response");
  return {
    annotationId: requireString(record.annotation_id, "annotation_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    inspectionPhotoId: requireString(record.inspection_photo_id, "inspection_photo_id"),
    trainingCropId: requireString(record.training_crop_id, "training_crop_id"),
    annotationType: requireBeeAnnotationType(record.annotation_type),
    centerX: requireNumber(record.center_x, "center_x"),
    centerY: requireNumber(record.center_y, "center_y"),
    radiusX: requireNumber(record.radius_x, "radius_x"),
    radiusY: requireNumber(record.radius_y, "radius_y"),
    rotationDegrees: requireNumber(record.rotation_degrees, "rotation_degrees"),
    orientationReliability: requireOrientationReliability(
      record.orientation_reliability ?? "reliable"
    ),
    coordinateSpace: requireSourceImagePixelCoordinateSpace(record.coordinate_space),
    sourceImageWidthPx: requireNumber(record.source_image_width_px, "source_image_width_px"),
    sourceImageHeightPx: requireNumber(record.source_image_height_px, "source_image_height_px"),
    source: requireString(record.source, "source"),
    reviewMethod: requireReviewMethod(record.review_method),
    modelCandidateId: optionalString(record.model_candidate_id, "model_candidate_id"),
    candidateConfidence: optionalNumber(record.candidate_confidence, "candidate_confidence"),
    candidateThreshold: optionalNumber(record.candidate_threshold, "candidate_threshold"),
    rawModelClass: optionalString(record.raw_model_class, "raw_model_class"),
    rawYoloObb:
      record.raw_yolo_obb === null || record.raw_yolo_obb === undefined
        ? null
        : requireArray(record.raw_yolo_obb, "raw_yolo_obb").map((point) =>
            requireNumber(point, "raw_yolo_obb point")
          ),
    candidateReviewDecision: requireCandidateReviewDecision(record.candidate_review_decision),
    varroaReviewSuitability: requireVarroaReviewSuitability(
      record.varroa_review_suitability ?? "unassessed"
    ),
    suspectedVisibleVarroa: requireBoolean(record.suspected_visible_varroa ?? false, "suspected_visible_varroa"),
    varroaReviewSuitabilityUpdatedByUserId: optionalString(
      record.varroa_review_suitability_updated_by_user_id,
      "varroa_review_suitability_updated_by_user_id"
    ),
    varroaReviewSuitabilityUpdatedAt: optionalString(
      record.varroa_review_suitability_updated_at,
      "varroa_review_suitability_updated_at"
    ),
    suspectedVisibleVarroaUpdatedByUserId: optionalString(
      record.suspected_visible_varroa_updated_by_user_id,
      "suspected_visible_varroa_updated_by_user_id"
    ),
    suspectedVisibleVarroaUpdatedAt: optionalString(
      record.suspected_visible_varroa_updated_at,
      "suspected_visible_varroa_updated_at"
    ),
    createdByUserId: requireString(record.created_by_user_id, "created_by_user_id"),
    createdAt: requireString(record.created_at, "created_at"),
    updatedAt: requireString(record.updated_at, "updated_at")
  };
}

function parseVarroaReviewCandidateList(value: unknown): VarroaReviewCandidateList {
  const record = requireRecord(value, "Varroa Review candidate list response");
  return {
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    trainingCropId: requireString(record.training_crop_id, "training_crop_id"),
    candidates: requireArray(record.candidates, "candidates").map(parseVarroaReviewCandidate),
    summary: parseVarroaReviewSummary(record.summary)
  };
}

function parseVarroaReviewCandidate(value: unknown): VarroaReviewCandidate {
  const record = requireRecord(value, "Varroa Review candidate response");
  return {
    beeAnnotation: parseOrientedBeeEllipse(record.bee_annotation),
    eligibility: requireVarroaReviewEligibility(record.eligibility),
    ineligibilityReasons: requireArray(record.ineligibility_reasons, "ineligibility_reasons").map(
      (reason) => requireString(reason, "ineligibility_reasons[]")
    ),
    reviewOutcome:
      record.review_outcome === null ? null : parseVarroaReviewOutcome(record.review_outcome)
  };
}

function parseVarroaReviewSummary(value: unknown): VarroaReviewSummary {
  const record = requireRecord(value, "Varroa Review summary response");
  return {
    eligibleBeeCount: requireNumber(record.eligible_bee_count, "eligible_bee_count"),
    reviewedBeeCount: requireNumber(record.reviewed_bee_count, "reviewed_bee_count"),
    visibleVarroaBeeCount: requireNumber(record.visible_varroa_bee_count, "visible_varroa_bee_count"),
    noVisibleVarroaBeeCount: requireNumber(
      record.no_visible_varroa_bee_count,
      "no_visible_varroa_bee_count"
    ),
    notDeterminedBeeCount: requireNumber(record.not_determined_bee_count, "not_determined_bee_count"),
    totalMarkerCount: requireNumber(record.total_marker_count, "total_marker_count"),
    suspectedVisibleVarroaCueCount: requireNumber(
      record.suspected_visible_varroa_cue_count,
      "suspected_visible_varroa_cue_count"
    ),
    hardToAssessCueCount: requireNumber(record.hard_to_assess_cue_count, "hard_to_assess_cue_count"),
    ineligibleDeferredBeeCount: requireNumber(
      record.ineligible_deferred_bee_count,
      "ineligible_deferred_bee_count"
    ),
    caveat: requireString(record.caveat, "caveat")
  };
}

function parseFrameLevelVarroaResultSummary(value: unknown): FrameLevelVarroaResultSummary {
  const record = requireRecord(value, "Photo-visible Varroa evidence summary response");
  return {
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    inspectionId: requireString(record.inspection_id, "inspection_id"),
    inspectionPhotoId: requireString(record.inspection_photo_id, "inspection_photo_id"),
    sourceImageFilename: requireString(record.source_image_filename, "source_image_filename"),
    sourceIntent: requireInspectionIntent(record.source_intent),
    completedTrainingCropCount: requireNumber(
      record.completed_training_crop_count,
      "completed_training_crop_count"
    ),
    unfinishedTrainingCropCount: requireNumber(
      record.unfinished_training_crop_count,
      "unfinished_training_crop_count"
    ),
    eligibleCompleteBeeCount: requireNumber(
      record.eligible_complete_bee_count,
      "eligible_complete_bee_count"
    ),
    reviewedEligibleBeeCount: requireNumber(
      record.reviewed_eligible_bee_count,
      "reviewed_eligible_bee_count"
    ),
    determinateEligibleBeeCount: requireNumber(
      record.determinate_eligible_bee_count,
      "determinate_eligible_bee_count"
    ),
    visibleVarroaBeeCount: requireNumber(record.visible_varroa_bee_count, "visible_varroa_bee_count"),
    activeNegativeBeeCount: requireNumber(record.active_negative_bee_count, "active_negative_bee_count"),
    notDeterminedBeeCount: requireNumber(record.not_determined_bee_count, "not_determined_bee_count"),
    unreviewedEligibleBeeCount: requireNumber(
      record.unreviewed_eligible_bee_count,
      "unreviewed_eligible_bee_count"
    ),
    ineligibleOrNotAssessedBeeCount: requireNumber(
      record.ineligible_or_not_assessed_bee_count,
      "ineligible_or_not_assessed_bee_count"
    ),
    visibleMiteMarkerCount: requireNumber(
      record.visible_mite_marker_count,
      "visible_mite_marker_count"
    ),
    reviewCompletionPercent: requireNumber(
      record.review_completion_percent,
      "review_completion_percent"
    ),
    determinateVarroaCoveragePercent: requireNumber(
      record.determinate_varroa_coverage_percent,
      "determinate_varroa_coverage_percent"
    ),
    evidenceSource: requireString(record.evidence_source, "evidence_source"),
    readinessState: requireFrameLevelVarroaReadinessState(record.readiness_state),
    advisorContextAvailable: requireBoolean(
      record.advisor_context_available,
      "advisor_context_available"
    ),
    caveats: requireString(record.caveats, "caveats")
  };
}

function parseHeadUpNormalizedBeeCropPreview(value: unknown): HeadUpNormalizedBeeCropPreview {
  const record = requireRecord(value, "Head-Up Normalized Bee Crop preview response");
  return {
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    inspectionPhotoId: requireString(record.inspection_photo_id, "inspection_photo_id"),
    trainingCropId: requireString(record.training_crop_id, "training_crop_id"),
    beeAnnotationId: requireString(record.bee_annotation_id, "bee_annotation_id"),
    annotationType: requireBeeAnnotationType(record.annotation_type),
    orientationReliability: requireOrientationReliability(record.orientation_reliability),
    imageWidthPx: requireNumber(record.image_width_px, "image_width_px"),
    imageHeightPx: requireNumber(record.image_height_px, "image_height_px"),
    transformVersion: requireString(record.transform_version, "transform_version"),
    imageUrl: requireString(record.image_url, "image_url"),
    transformMetadata:
      record.transform_metadata === undefined
        ? {}
        : requireRecord(record.transform_metadata, "transform_metadata")
  };
}

function parseVarroaReviewOutcome(value: unknown): VarroaReviewOutcome {
  const record = requireRecord(value, "Varroa Review Outcome response");
  return {
    varroaReviewOutcomeId: requireString(record.varroa_review_outcome_id, "varroa_review_outcome_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    inspectionPhotoId: requireString(record.inspection_photo_id, "inspection_photo_id"),
    trainingCropId: requireString(record.training_crop_id, "training_crop_id"),
    beeAnnotationId: requireString(record.bee_annotation_id, "bee_annotation_id"),
    outcome: requireVarroaReviewOutcomeValue(record.outcome),
    samplingPurpose: requireLiteral(record.sampling_purpose, "model_curation", "sampling_purpose"),
    datasetSelectionMethod: requireLiteral(
      record.dataset_selection_method,
      "human_selected",
      "dataset_selection_method"
    ),
    reviewStrength: requireLiteral(record.review_strength, "single_curator_review", "review_strength"),
    annotationSource: requireLiteral(record.annotation_source, "human_from_scratch", "annotation_source"),
    createdByUserId: requireString(record.created_by_user_id, "created_by_user_id"),
    createdAt: requireString(record.created_at, "created_at"),
    updatedByUserId: requireString(record.updated_by_user_id, "updated_by_user_id"),
    updatedAt: requireString(record.updated_at, "updated_at"),
    notes: optionalString(record.notes, "notes"),
    markers: requireArray(record.markers, "markers").map(parseVarroaMarker)
  };
}

function parseVarroaMarker(value: unknown): VarroaMarker {
  const record = requireRecord(value, "Varroa marker response");
  return {
    varroaMarkerId: requireString(record.varroa_marker_id, "varroa_marker_id"),
    varroaReviewOutcomeId: requireString(
      record.varroa_review_outcome_id,
      "varroa_review_outcome_id"
    ),
    markerType: requireLiteral(record.marker_type, "point", "marker_type"),
    x: requireNumber(record.x, "x"),
    y: requireNumber(record.y, "y"),
    createdAt: requireString(record.created_at, "created_at")
  };
}

function parseBeeAnnotationProposalList(value: unknown): BeeAnnotationProposalList {
  const record = requireRecord(value, "Bee annotation proposal list response");
  return {
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    trainingCropId: requireString(record.training_crop_id, "training_crop_id"),
    modelCandidateId: requireString(record.model_candidate_id, "model_candidate_id"),
    modelCandidateHumanReadableId: requireString(
      record.model_candidate_human_readable_id,
      "model_candidate_human_readable_id"
    ),
    threshold: requireNumber(record.threshold, "threshold"),
    suggestions: requireArray(record.suggestions, "suggestions").map(parseBeeAnnotationProposal),
    caveat: requireString(record.caveat, "caveat")
  };
}

function parseBeeAnnotationProposal(value: unknown): BeeAnnotationProposal {
  const record = requireRecord(value, "Bee annotation proposal response");
  return {
    proposalId: requireString(record.proposal_id, "proposal_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    trainingCropId: requireString(record.training_crop_id, "training_crop_id"),
    modelCandidateId: requireString(record.model_candidate_id, "model_candidate_id"),
    modelCandidateHumanReadableId: requireString(
      record.model_candidate_human_readable_id,
      "model_candidate_human_readable_id"
    ),
    annotationType: requireBeeAnnotationType(record.annotation_type),
    centerX: requireNumber(record.center_x, "center_x"),
    centerY: requireNumber(record.center_y, "center_y"),
    radiusX: requireNumber(record.radius_x, "radius_x"),
    radiusY: requireNumber(record.radius_y, "radius_y"),
    rotationDegrees: requireNumber(record.rotation_degrees, "rotation_degrees"),
    coordinateSpace: requireSourceImagePixelCoordinateSpace(record.coordinate_space),
    confidence: requireNumber(record.confidence, "confidence"),
    threshold: requireNumber(record.threshold, "threshold"),
    rawModelClass: requireString(record.raw_model_class, "raw_model_class"),
    rawYoloObb: requireArray(record.raw_yolo_obb, "raw_yolo_obb").map((point) =>
      requireNumber(point, "raw_yolo_obb point")
    )
  };
}

function parseReviewedEllipseSnapshot(value: unknown): ReviewedEllipseSnapshot {
  const record = requireRecord(value, "Reviewed ellipse snapshot response");
  return {
    annotationId: requireString(record.annotation_id, "annotation_id"),
    annotationType: requireBeeAnnotationType(record.annotation_type),
    centerX: requireNumber(record.center_x, "center_x"),
    centerY: requireNumber(record.center_y, "center_y"),
    radiusX: requireNumber(record.radius_x, "radius_x"),
    radiusY: requireNumber(record.radius_y, "radius_y"),
    rotationDegrees: requireNumber(record.rotation_degrees, "rotation_degrees"),
    orientationReliability: requireOrientationReliability(
      record.orientation_reliability ?? "reliable"
    ),
    coordinateSpace: requireSourceImagePixelCoordinateSpace(record.coordinate_space),
    sourceImageWidthPx: requireNumber(record.source_image_width_px, "source_image_width_px"),
    sourceImageHeightPx: requireNumber(record.source_image_height_px, "source_image_height_px"),
    source: requireString(record.source, "source"),
    createdByUserId: requireString(record.created_by_user_id, "created_by_user_id"),
    createdAt: requireString(record.created_at, "created_at"),
    updatedAt: requireString(record.updated_at, "updated_at")
  };
}

function parseDatasetItem(value: unknown): DatasetItem {
  const record = requireRecord(value, "Dataset item response");
  return {
    datasetItemId: requireString(record.dataset_item_id, "dataset_item_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    inspectionPhotoId: requireString(record.inspection_photo_id, "inspection_photo_id"),
    labellingSessionId: optionalString(record.labelling_session_id, "labelling_session_id"),
    trainingCropId: optionalString(record.training_crop_id, "training_crop_id"),
    sourceEvidenceType: requireDatasetItemSourceEvidenceType(record.source_evidence_type),
    datasetRole: requireDatasetRole(record.dataset_role),
    reviewedAnnotationIds: requireArray(
      record.reviewed_annotation_ids,
      "reviewed_annotation_ids"
    ).map((annotationId) => requireString(annotationId, "reviewed_annotation_ids[]")),
    reviewedEllipseSnapshots: requireArray(
      record.reviewed_ellipse_snapshots,
      "reviewed_ellipse_snapshots"
    ).map(parseReviewedEllipseSnapshot),
    cropX: optionalNumber(record.crop_x, "crop_x"),
    cropY: optionalNumber(record.crop_y, "crop_y"),
    cropWidth: optionalNumber(record.crop_width, "crop_width"),
    cropHeight: optionalNumber(record.crop_height, "crop_height"),
    cropImageWidthPx: optionalNumber(record.crop_image_width_px, "crop_image_width_px"),
    cropImageHeightPx: optionalNumber(record.crop_image_height_px, "crop_image_height_px"),
    curriculumStage: optionalString(record.curriculum_stage, "curriculum_stage"),
    sourceGroupKey: optionalString(record.source_group_key, "source_group_key"),
    imageQualityStatus: requireImageQualityStatus(record.image_quality_status),
    permissionStatus: requireString(record.permission_status, "permission_status"),
    assignedByUserId: requireString(record.assigned_by_user_id, "assigned_by_user_id"),
    assignedAt: requireString(record.assigned_at, "assigned_at"),
    assignmentNote: optionalString(record.assignment_note, "assignment_note"),
    exclusionReason:
      record.exclusion_reason === null
        ? null
        : requireDatasetExclusionReason(record.exclusion_reason),
    benchmarkProtected: requireBoolean(record.benchmark_protected, "benchmark_protected")
  };
}

function parseDatasetVersionMembership(value: unknown): DatasetVersionMembership {
  const record = requireRecord(value, "Dataset Version membership response");
  return {
    datasetVersionId: requireString(record.dataset_version_id, "dataset_version_id"),
    humanReadableId: requireString(record.human_readable_id, "human_readable_id"),
    purpose: requireString(record.purpose, "purpose"),
    status: requireString(record.status, "status"),
    membership: requireDatasetVersionMembership(record.membership),
    excludedReason: optionalString(record.excluded_reason, "excluded_reason"),
    createdAt: requireString(record.created_at, "created_at")
  };
}

function parseDatasetRepositoryWarning(value: unknown): DatasetRepositoryWarning {
  const record = requireRecord(value, "Dataset repository warning response");
  return {
    code: requireString(record.code, "code"),
    severity: requireDatasetRepositoryWarningSeverity(record.severity),
    message: requireString(record.message, "message"),
    affectedDatasetItemIds: requireArray(
      record.affected_dataset_item_ids,
      "affected_dataset_item_ids"
    ).map((id) => requireString(id, "affected_dataset_item_ids[]"))
  };
}

function parseDatasetRepositoryLatestVersionSummary(
  value: unknown
): DatasetRepositoryLatestVersionSummary {
  const record = requireRecord(value, "Dataset repository latest version response");
  return {
    datasetVersionId: requireString(record.dataset_version_id, "dataset_version_id"),
    humanReadableId: requireString(record.human_readable_id, "human_readable_id"),
    status: requireString(record.status, "status"),
    createdAt: requireString(record.created_at, "created_at"),
    trainingItemCount: requireNumber(record.training_item_count, "training_item_count"),
    validationItemCount: requireNumber(record.validation_item_count, "validation_item_count"),
    benchmarkItemCount: requireNumber(record.benchmark_item_count, "benchmark_item_count"),
    excludedItemCount: requireNumber(record.excluded_item_count, "excluded_item_count")
  };
}

function parseDatasetRepositorySummary(value: unknown): DatasetRepositorySummary {
  const record = requireRecord(value, "Dataset repository summary response");
  return {
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    datasetItemCount: requireNumber(record.dataset_item_count, "dataset_item_count"),
    activeDatasetItemCount: requireNumber(
      record.active_dataset_item_count,
      "active_dataset_item_count"
    ),
    unassignedCompletedCropCount: requireNumber(
      record.unassigned_completed_crop_count,
      "unassigned_completed_crop_count"
    ),
    newSinceLatestDatasetVersionCount: requireNumber(
      record.new_since_latest_dataset_version_count,
      "new_since_latest_dataset_version_count"
    ),
    roleCounts: parseNumberMap(record.role_counts, "role_counts"),
    annotationClassCounts: parseNumberMap(
      record.annotation_class_counts,
      "annotation_class_counts"
    ),
    annotationSourceCounts: parseNumberMap(
      record.annotation_source_counts,
      "annotation_source_counts"
    ),
    reviewMethodCounts: parseNumberMap(record.review_method_counts, "review_method_counts"),
    curriculumStageDistribution: parseNumberMap(
      record.curriculum_stage_distribution,
      "curriculum_stage_distribution"
    ),
    imageQualityDistribution: parseNumberMap(
      record.image_quality_distribution,
      "image_quality_distribution"
    ),
    hiveConfigurationDistribution: parseNumberMap(
      record.hive_configuration_distribution,
      "hive_configuration_distribution"
    ),
    sourceGroupDistribution: parseNumberMap(
      record.source_group_distribution,
      "source_group_distribution"
    ),
    inspectionDistribution: parseNumberMap(
      record.inspection_distribution,
      "inspection_distribution"
    ),
    inspectionIntentDistribution: parseNumberMap(
      record.inspection_intent_distribution,
      "inspection_intent_distribution"
    ),
    hiveDistribution: parseNumberMap(record.hive_distribution, "hive_distribution"),
    sourceImageDistribution: parseNumberMap(
      record.source_image_distribution,
      "source_image_distribution"
    ),
    latestDatasetVersion:
      record.latest_dataset_version === null
        ? null
        : parseDatasetRepositoryLatestVersionSummary(record.latest_dataset_version),
    persistenceBackend: requireString(record.persistence_backend, "persistence_backend"),
    databasePurpose: requireString(record.database_purpose, "database_purpose"),
    warnings: requireArray(record.warnings, "warnings").map(parseDatasetRepositoryWarning)
  };
}

function parseDatasetRepositoryItem(value: unknown): DatasetRepositoryItem {
  const record = requireRecord(value, "Dataset repository item response");
  return {
    datasetItemId: requireString(record.dataset_item_id, "dataset_item_id"),
    humanReadableId: requireString(record.human_readable_id, "human_readable_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    datasetRole: requireDatasetRole(record.dataset_role),
    status: requireString(record.status, "status"),
    sourceEvidenceType: requireString(record.source_evidence_type, "source_evidence_type"),
    inspectionId: optionalString(record.inspection_id, "inspection_id"),
    inspectionDate: optionalString(record.inspection_date, "inspection_date"),
    inspectionIntent:
      record.inspection_intent === null ? null : requireInspectionIntent(record.inspection_intent),
    inspectionPhotoId: requireString(record.inspection_photo_id, "inspection_photo_id"),
    sourceImageId: requireString(record.source_image_id, "source_image_id"),
    sourceFilename: optionalString(record.source_filename, "source_filename"),
    apiaryId: optionalString(record.apiary_id, "apiary_id"),
    apiaryName: optionalString(record.apiary_name, "apiary_name"),
    hiveId: optionalString(record.hive_id, "hive_id"),
    hiveName: optionalString(record.hive_name, "hive_name"),
    hiveConfigurationSummary: optionalString(
      record.hive_configuration_summary,
      "hive_configuration_summary"
    ),
    trainingCropId: optionalString(record.training_crop_id, "training_crop_id"),
    cropX: optionalNumber(record.crop_x, "crop_x"),
    cropY: optionalNumber(record.crop_y, "crop_y"),
    cropWidth: optionalNumber(record.crop_width, "crop_width"),
    cropHeight: optionalNumber(record.crop_height, "crop_height"),
    cropImageWidthPx: optionalNumber(record.crop_image_width_px, "crop_image_width_px"),
    cropImageHeightPx: optionalNumber(record.crop_image_height_px, "crop_image_height_px"),
    curriculumStage: optionalString(record.curriculum_stage, "curriculum_stage"),
    completeVisibleBeeCount: requireNumber(
      record.complete_visible_bee_count,
      "complete_visible_bee_count"
    ),
    partialVisibleBeeCount: requireNumber(
      record.partial_visible_bee_count,
      "partial_visible_bee_count"
    ),
    annotationSourceCounts: parseNumberMap(
      record.annotation_source_counts,
      "annotation_source_counts"
    ),
    reviewMethodCounts: parseNumberMap(record.review_method_counts, "review_method_counts"),
    sourceGroupKey: optionalString(record.source_group_key, "source_group_key"),
    imageQualityStatus: requireImageQualityStatus(record.image_quality_status),
    assignedByUserId: requireString(record.assigned_by_user_id, "assigned_by_user_id"),
    assignedAt: requireString(record.assigned_at, "assigned_at"),
    assignmentNote: optionalString(record.assignment_note, "assignment_note"),
    exclusionReason:
      record.exclusion_reason === null
        ? null
        : requireDatasetExclusionReason(record.exclusion_reason),
    benchmarkProtected: requireBoolean(record.benchmark_protected, "benchmark_protected"),
    exportEligibility: requireString(record.export_eligibility, "export_eligibility"),
    latestDatasetVersionMembership:
      record.latest_dataset_version_membership === null
        ? null
        : parseDatasetVersionMembership(record.latest_dataset_version_membership),
    datasetVersionMemberships: requireArray(
      record.dataset_version_memberships,
      "dataset_version_memberships"
    ).map(parseDatasetVersionMembership),
    isNewSinceLatestDatasetVersion: requireBoolean(
      record.is_new_since_latest_dataset_version,
      "is_new_since_latest_dataset_version"
    ),
    previewStatus: requireString(record.preview_status, "preview_status"),
    thumbnailUrl: optionalString(record.thumbnail_url, "thumbnail_url")
  };
}

function parseDatasetRepositoryItemList(value: unknown): DatasetRepositoryItemList {
  const record = requireRecord(value, "Dataset repository item list response");
  return {
    summary: parseDatasetRepositorySummary(record.summary),
    items: requireArray(record.items, "items").map(parseDatasetRepositoryItem)
  };
}

function parseDatasetRepositoryItemDetail(value: unknown): DatasetRepositoryItemDetail {
  const record = requireRecord(value, "Dataset repository item detail response");
  return {
    ...parseDatasetRepositoryItem(value),
    reviewedEllipseSnapshots: requireArray(
      record.reviewed_ellipse_snapshots,
      "reviewed_ellipse_snapshots"
    ).map(parseReviewedEllipseSnapshot),
    permissionStatus: requireString(record.permission_status, "permission_status"),
    previewUrl: optionalString(record.preview_url, "preview_url")
  };
}

function parseYoloObbExport(value: unknown): YoloObbExport {
  const record = requireRecord(value, "YOLO OBB export response");
  return {
    exportId: requireString(record.export_id, "export_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    exportFormat: requireYoloObbExportFormat(record.export_format),
    labelConvention: requireString(record.label_convention, "label_convention"),
    coordinateBasis: requireString(record.coordinate_basis, "coordinate_basis"),
    createdByUserId: requireString(record.created_by_user_id, "created_by_user_id"),
    createdAt: requireString(record.created_at, "created_at"),
    classMap: parseStringMap(record.class_map, "class_map"),
    includedDatasetItemIds: requireArray(
      record.included_dataset_item_ids,
      "included_dataset_item_ids"
    ).map((id) => requireString(id, "included_dataset_item_ids[]")),
    excludedDatasetItems: requireArray(
      record.excluded_dataset_items,
      "excluded_dataset_items"
    ).map(parseYoloObbExcludedItem),
    protectedBenchmarkDatasetItemIds: requireArray(
      record.protected_benchmark_dataset_item_ids,
      "protected_benchmark_dataset_item_ids"
    ).map((id) => requireString(id, "protected_benchmark_dataset_item_ids[]")),
    trainingItemCount: requireNumber(record.training_item_count, "training_item_count"),
    validationItemCount: requireNumber(record.validation_item_count, "validation_item_count"),
    benchmarkItemCount: requireNumber(record.benchmark_item_count, "benchmark_item_count"),
    imageEntries: requireArray(record.image_entries, "image_entries").map(parseYoloObbImageEntry),
    labelEntries: requireArray(record.label_entries, "label_entries").map(parseYoloObbLabelEntry),
    caveat: requireString(record.caveat, "caveat")
  };
}

function parsePhysicalYoloObbExport(value: unknown): PhysicalYoloObbExport {
  const record = requireRecord(value, "Physical YOLO OBB export response");
  return {
    exportId: requireString(record.export_id, "export_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    exportFormat: requireYoloObbExportFormat(record.export_format),
    packagePath: requireString(record.package_path, "package_path"),
    manifestPath: requireString(record.manifest_path, "manifest_path"),
    datasetYamlPath: requireString(record.dataset_yaml_path, "dataset_yaml_path"),
    createdByUserId: requireString(record.created_by_user_id, "created_by_user_id"),
    createdAt: requireString(record.created_at, "created_at"),
    classMap: parseStringMap(record.class_map, "class_map"),
    trainingItemCount: requireNumber(record.training_item_count, "training_item_count"),
    validationItemCount: requireNumber(record.validation_item_count, "validation_item_count"),
    benchmarkItemCount: requireNumber(record.benchmark_item_count, "benchmark_item_count"),
    excludedItemCount: requireNumber(record.excluded_item_count, "excluded_item_count"),
    protectedBenchmarkDatasetItemIds: requireArray(
      record.protected_benchmark_dataset_item_ids,
      "protected_benchmark_dataset_item_ids"
    ).map((id) => requireString(id, "protected_benchmark_dataset_item_ids[]")),
    excludedDatasetItems: requireArray(
      record.excluded_dataset_items,
      "excluded_dataset_items"
    ).map(parseYoloObbExcludedItem),
    generatedFiles: requireArray(record.generated_files, "generated_files").map(
      parseGeneratedDatasetExportFile
    ),
    caveat: requireString(record.caveat, "caveat")
  };
}

function parseModelTrainingReadiness(value: unknown): ModelTrainingReadiness {
  const record = requireRecord(value, "Model training readiness response");
  return {
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    persistenceBackend: requireString(record.persistence_backend, "persistence_backend"),
    adapterType: requireTrainingAdapterType(record.adapter_type),
    databasePurpose: requireString(record.database_purpose, "database_purpose"),
    realAdapterAvailable: requireBoolean(record.real_adapter_available, "real_adapter_available"),
    modelPurpose: requireModelPurpose(record.model_purpose),
    datasetVersionId: optionalString(record.dataset_version_id, "dataset_version_id"),
    datasetVersionHumanReadableId: optionalString(
      record.dataset_version_human_readable_id,
      "dataset_version_human_readable_id"
    ),
    datasetVersionPurpose: optionalString(record.dataset_version_purpose, "dataset_version_purpose"),
    eligibleToCreateDatasetVersion: requireBoolean(
      record.eligible_to_create_dataset_version,
      "eligible_to_create_dataset_version"
    ),
    eligibleToStartTraining: requireBoolean(
      record.eligible_to_start_training,
      "eligible_to_start_training"
    ),
    activeTrainingRunId: optionalString(record.active_training_run_id, "active_training_run_id"),
    trainingItemCount: requireNumber(record.training_item_count, "training_item_count"),
    validationItemCount: requireNumber(record.validation_item_count, "validation_item_count"),
    benchmarkItemCount: requireNumber(record.benchmark_item_count, "benchmark_item_count"),
    eligibleTrainingSourceBeeCount: requireNumber(
      record.eligible_training_source_bee_count,
      "eligible_training_source_bee_count"
    ),
    eligibleValidationSourceBeeCount: requireNumber(
      record.eligible_validation_source_bee_count,
      "eligible_validation_source_bee_count"
    ),
    generatedTrainingExampleCount: requireNumber(
      record.generated_training_example_count,
      "generated_training_example_count"
    ),
    generatedValidationExampleCount: requireNumber(
      record.generated_validation_example_count,
      "generated_validation_example_count"
    ),
    protectedBenchmarkSourceBeeCount: requireNumber(
      record.protected_benchmark_source_bee_count,
      "protected_benchmark_source_bee_count"
    ),
    excludedUnreliableOrientationCount: requireNumber(
      record.excluded_unreliable_orientation_count,
      "excluded_unreliable_orientation_count"
    ),
    excludedPartialVisibleBeeCount: requireNumber(
      record.excluded_partial_visible_bee_count,
      "excluded_partial_visible_bee_count"
    ),
    warnings: requireArray(record.warnings, "warnings").map(parseModelTrainingWarning)
  };
}

function parseBeeTrainingReadiness(value: unknown): BeeTrainingReadiness {
  const record = requireRecord(value, "Bee Training readiness response");
  return {
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    datasetVersionId: optionalString(record.dataset_version_id, "dataset_version_id"),
    datasetVersionHumanReadableId: optionalString(
      record.dataset_version_human_readable_id,
      "dataset_version_human_readable_id"
    ),
    activeTrainingRunId: optionalString(record.active_training_run_id, "active_training_run_id"),
    beeLocalisation: parseModelTrainingReadiness(record.bee_localisation),
    beeOrientation: parseModelTrainingReadiness(record.bee_orientation),
    eligibleToStartBeeTraining: requireBoolean(
      record.eligible_to_start_bee_training,
      "eligible_to_start_bee_training"
    ),
    warnings: requireArray(record.warnings, "warnings").map(parseModelTrainingWarning)
  };
}

function parseDatasetVersion(value: unknown): DatasetVersion {
  const record = requireRecord(value, "Dataset Version response");
  return {
    datasetVersionId: requireString(record.dataset_version_id, "dataset_version_id"),
    humanReadableId: requireString(record.human_readable_id, "human_readable_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    purpose: requireString(record.purpose, "purpose"),
    modelPurpose: requireModelPurpose(record.model_purpose),
    status: requireString(record.status, "status"),
    exportFormat: requireTrainingExportFormat(record.export_format),
    selectionCriteria: requireRecord(record.selection_criteria, "selection_criteria"),
    manifestHash: requireString(record.manifest_hash, "manifest_hash"),
    createdByUserId: requireString(record.created_by_user_id, "created_by_user_id"),
    createdAt: requireString(record.created_at, "created_at"),
    includedDatasetItemIds: requireArray(
      record.included_dataset_item_ids,
      "included_dataset_item_ids"
    ).map((id) => requireString(id, "included_dataset_item_ids[]")),
    trainingDatasetItemIds: requireArray(
      record.training_dataset_item_ids,
      "training_dataset_item_ids"
    ).map((id) => requireString(id, "training_dataset_item_ids[]")),
    validationDatasetItemIds: requireArray(
      record.validation_dataset_item_ids,
      "validation_dataset_item_ids"
    ).map((id) => requireString(id, "validation_dataset_item_ids[]")),
    protectedBenchmarkDatasetItemIds: requireArray(
      record.protected_benchmark_dataset_item_ids,
      "protected_benchmark_dataset_item_ids"
    ).map((id) => requireString(id, "protected_benchmark_dataset_item_ids[]")),
    excludedDatasetItems: requireArray(
      record.excluded_dataset_items,
      "excluded_dataset_items"
    ).map(parseYoloObbExcludedItem),
    trainingItemCount: requireNumber(record.training_item_count, "training_item_count"),
    validationItemCount: requireNumber(record.validation_item_count, "validation_item_count"),
    benchmarkItemCount: requireNumber(record.benchmark_item_count, "benchmark_item_count"),
    excludedItemCount: requireNumber(record.excluded_item_count, "excluded_item_count"),
    annotationClassCounts: parseNumberMap(record.annotation_class_counts, "annotation_class_counts"),
    annotationSourceCounts: parseNumberMap(
      record.annotation_source_counts,
      "annotation_source_counts"
    ),
    reviewMethodCounts: parseNumberMap(record.review_method_counts, "review_method_counts"),
    sourceGroupDistribution: parseNumberMap(
      record.source_group_distribution,
      "source_group_distribution"
    ),
    hiveConfigurationDistribution: parseNumberMap(
      record.hive_configuration_distribution,
      "hive_configuration_distribution"
    ),
    curriculumStageDistribution: parseNumberMap(
      record.curriculum_stage_distribution,
      "curriculum_stage_distribution"
    ),
    imageQualityDistribution: parseNumberMap(
      record.image_quality_distribution,
      "image_quality_distribution"
    ),
    reportArtifactId: optionalString(record.report_artifact_id, "report_artifact_id"),
    previewArtifactIds: requireArray(record.preview_artifact_ids, "preview_artifact_ids").map(
      (id) => requireString(id, "preview_artifact_ids[]")
    ),
    warnings: requireArray(record.warnings, "warnings").map(parseModelTrainingWarning)
  };
}

function parseTrainingRun(value: unknown): TrainingRun {
  const record = requireRecord(value, "Training Run response");
  return {
    trainingRunId: requireString(record.training_run_id, "training_run_id"),
    humanReadableId: requireString(record.human_readable_id, "human_readable_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    datasetVersionId: requireString(record.dataset_version_id, "dataset_version_id"),
    modelPurpose: requireModelPurpose(record.model_purpose),
    modelFamily: requireString(record.model_family, "model_family"),
    modelSize: requireString(record.model_size, "model_size"),
    baseWeights: requireString(record.base_weights, "base_weights"),
    baseWeightsSource: requireString(record.base_weights_source, "base_weights_source"),
    adapterType: requireTrainingAdapterType(record.adapter_type),
    status: requireTrainingRunStatus(record.status),
    phase: requireString(record.phase, "phase"),
    databasePurpose: requireString(record.database_purpose, "database_purpose"),
    trainingSettings: requireRecord(record.training_settings, "training_settings"),
    randomSeed: requireNumber(record.random_seed, "random_seed"),
    gitCommitSha: optionalString(record.git_commit_sha, "git_commit_sha"),
    gitDirtyStatus: requireString(record.git_dirty_status, "git_dirty_status"),
    environmentSummary: requireRecord(record.environment_summary, "environment_summary"),
    warningAcknowledgement:
      record.warning_acknowledgement === null
        ? null
        : requireRecord(record.warning_acknowledgement, "warning_acknowledgement"),
    startedAt: optionalString(record.started_at, "started_at"),
    completedAt: optionalString(record.completed_at, "completed_at"),
    lastHeartbeatAt: optionalString(record.last_heartbeat_at, "last_heartbeat_at"),
    lastActivityMessage: optionalString(record.last_activity_message, "last_activity_message"),
    progressPercent: optionalNumber(record.progress_percent, "progress_percent"),
    currentEpoch: optionalNumber(record.current_epoch, "current_epoch"),
    totalEpochs: optionalNumber(record.total_epochs, "total_epochs"),
    latestLogExcerpt: optionalString(record.latest_log_excerpt, "latest_log_excerpt"),
    cancelRequestedAt: optionalString(record.cancel_requested_at, "cancel_requested_at"),
    cancelRequestedByUserId: optionalString(
      record.cancel_requested_by_user_id,
      "cancel_requested_by_user_id"
    ),
    cancelReason: optionalString(record.cancel_reason, "cancel_reason"),
    abandonedAt: optionalString(record.abandoned_at, "abandoned_at"),
    abandonedByUserId: optionalString(record.abandoned_by_user_id, "abandoned_by_user_id"),
    abandonReason: optionalString(record.abandon_reason, "abandon_reason"),
    isStale: requireBoolean(record.is_stale, "is_stale"),
    staleAfterSeconds: optionalNumber(record.stale_after_seconds, "stale_after_seconds"),
    failureCode: optionalString(record.failure_code, "failure_code"),
    failureMessage: optionalString(record.failure_message, "failure_message"),
    artifactIds: requireArray(record.artifact_ids, "artifact_ids").map((id) =>
      requireString(id, "artifact_ids[]")
    ),
    metricsSummary: requireRecord(record.metrics_summary, "metrics_summary"),
    modelCandidateId: optionalString(record.model_candidate_id, "model_candidate_id"),
    reportArtifactId: optionalString(record.report_artifact_id, "report_artifact_id"),
    createdByUserId: requireString(record.created_by_user_id, "created_by_user_id"),
    createdAt: requireString(record.created_at, "created_at"),
    purposeNotes: optionalString(record.purpose_notes, "purpose_notes")
  };
}

function parseBeeTrainingStart(value: unknown): BeeTrainingStart {
  const record = requireRecord(value, "Bee Training start response");
  const orientationRun = record.bee_orientation_training_run;
  return {
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    datasetVersionId: requireString(record.dataset_version_id, "dataset_version_id"),
    beeLocalisationTrainingRun: parseTrainingRun(record.bee_localisation_training_run),
    beeOrientationTrainingRun:
      orientationRun === null || orientationRun === undefined ? null : parseTrainingRun(orientationRun),
    message: requireString(record.message, "message")
  };
}

function parseTrainingRunDeleteResponse(value: unknown): TrainingRunDeleteResponse {
  const record = requireRecord(value, "Training Run delete response");
  return {
    trainingRunId: requireString(record.training_run_id, "training_run_id"),
    deleted: requireBoolean(record.deleted, "deleted"),
    message: requireString(record.message, "message")
  };
}

function parseTrainingRunList(value: unknown): TrainingRunList {
  const record = requireRecord(value, "Training Run list response");
  return {
    trainingRuns: requireArray(record.training_runs, "training_runs").map(parseTrainingRun)
  };
}

function parseModelCandidate(value: unknown): ModelCandidate {
  const record = requireRecord(value, "Model Candidate response");
  return {
    modelCandidateId: requireString(record.model_candidate_id, "model_candidate_id"),
    humanReadableId: requireString(record.human_readable_id, "human_readable_id"),
    displayName: requireString(record.display_name, "display_name"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    trainingRunId: requireString(record.training_run_id, "training_run_id"),
    modelPurpose: requireModelPurpose(record.model_purpose),
    modelFamily: requireString(record.model_family, "model_family"),
    adapterType: requireTrainingAdapterType(record.adapter_type),
    artifactId: requireString(record.artifact_id, "artifact_id"),
    status: requireString(record.status, "status"),
    promotionStatus: requireString(record.promotion_status, "promotion_status"),
    notUserFacingReason: requireString(
      record.not_user_facing_reason,
      "not_user_facing_reason"
    ),
    createdAt: requireString(record.created_at, "created_at")
  };
}

function parseModelCandidateList(value: unknown): ModelCandidateList {
  const record = requireRecord(value, "Model Candidate list response");
  return {
    modelCandidates: requireArray(record.model_candidates, "model_candidates").map(
      parseModelCandidate
    )
  };
}

function parseBenchmarkEvaluationReadiness(value: unknown): BenchmarkEvaluationReadiness {
  const record = requireRecord(value, "Benchmark Evaluation readiness response");
  return {
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    modelCandidateId: requireString(record.model_candidate_id, "model_candidate_id"),
    modelCandidateHumanReadableId: requireString(
      record.model_candidate_human_readable_id,
      "model_candidate_human_readable_id"
    ),
    adapterType: requireTrainingAdapterType(record.adapter_type),
    trainingAdapterType: requireTrainingAdapterType(record.training_adapter_type),
    evaluationAdapterType: requireTrainingAdapterType(record.evaluation_adapter_type),
    databasePurpose: requireString(record.database_purpose, "database_purpose"),
    benchmarkItemCount: requireNumber(record.benchmark_item_count, "benchmark_item_count"),
    eligibleToStartEvaluation: requireBoolean(
      record.eligible_to_start_evaluation,
      "eligible_to_start_evaluation"
    ),
    activeModelJobId: optionalString(record.active_model_job_id, "active_model_job_id"),
    activeModelJobType: optionalString(record.active_model_job_type, "active_model_job_type"),
    warnings: requireArray(record.warnings, "warnings").map(parseModelTrainingWarning)
  };
}

function parseOrientationBenchmarkReadiness(value: unknown): OrientationBenchmarkReadiness {
  const readiness = parseBenchmarkEvaluationReadiness(value);
  const record = requireRecord(value, "Bee Orientation Benchmark readiness response");
  return {
    ...readiness,
    datasetVersionId: requireString(record.dataset_version_id, "dataset_version_id"),
    datasetVersionHumanReadableId: requireString(
      record.dataset_version_human_readable_id,
      "dataset_version_human_readable_id"
    ),
    eligibleBenchmarkBeeCount: requireNumber(
      record.eligible_benchmark_bee_count,
      "eligible_benchmark_bee_count"
    ),
    excludedUnreliableOrientationCount: requireNumber(
      record.excluded_unreliable_orientation_count,
      "excluded_unreliable_orientation_count"
    ),
    excludedPartialVisibleBeeCount: requireNumber(
      record.excluded_partial_visible_bee_count,
      "excluded_partial_visible_bee_count"
    )
  };
}

function parseBenchmarkEvaluationItemResult(value: unknown): BenchmarkEvaluationItemResult {
  const record = requireRecord(value, "Benchmark Evaluation item result");
  return {
    datasetItemId: requireString(record.dataset_item_id, "dataset_item_id"),
    humanReadableId: requireString(record.human_readable_id, "human_readable_id"),
    sourceGroupKey: optionalString(record.source_group_key, "source_group_key"),
    hiveConfigurationFrameStandardId: optionalString(
      record.hive_configuration_frame_standard_id,
      "hive_configuration_frame_standard_id"
    ),
    curriculumStage: optionalString(record.curriculum_stage, "curriculum_stage"),
    groundTruthCount: requireNumber(record.ground_truth_count, "ground_truth_count"),
    predictionCount: requireNumber(record.prediction_count, "prediction_count"),
    matchedCount: requireNumber(record.matched_count, "matched_count"),
    falsePositiveCount: requireNumber(record.false_positive_count, "false_positive_count"),
    falseNegativeCount: requireNumber(record.false_negative_count, "false_negative_count")
  };
}

function parseBenchmarkEvaluation(value: unknown): BenchmarkEvaluation {
  const record = requireRecord(value, "Benchmark Evaluation response");
  return {
    benchmarkEvaluationId: requireString(record.benchmark_evaluation_id, "benchmark_evaluation_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    humanReadableId: requireString(record.human_readable_id, "human_readable_id"),
    modelCandidateId: requireString(record.model_candidate_id, "model_candidate_id"),
    modelCandidateHumanReadableId: requireString(
      record.model_candidate_human_readable_id,
      "model_candidate_human_readable_id"
    ),
    trainingRunId: requireString(record.training_run_id, "training_run_id"),
    datasetVersionId: requireString(record.dataset_version_id, "dataset_version_id"),
    modelPurpose: requireModelPurpose(record.model_purpose),
    status: requireBenchmarkEvaluationStatus(record.status),
    phase: requireString(record.phase, "phase"),
    adapterType: requireTrainingAdapterType(record.adapter_type),
    trainingAdapterType: requireTrainingAdapterType(record.training_adapter_type),
    evaluationAdapterType: requireTrainingAdapterType(record.evaluation_adapter_type),
    databasePurpose: requireString(record.database_purpose, "database_purpose"),
    confidenceThreshold: requireNumber(record.confidence_threshold, "confidence_threshold"),
    matchStrategy: requireString(record.match_strategy, "match_strategy"),
    benchmarkScope: requireString(record.benchmark_scope, "benchmark_scope"),
    startedAt: optionalString(record.started_at, "started_at"),
    completedAt: optionalString(record.completed_at, "completed_at"),
    lastHeartbeatAt: optionalString(record.last_heartbeat_at, "last_heartbeat_at"),
    lastActivityMessage: optionalString(record.last_activity_message, "last_activity_message"),
    progressPercent: optionalNumber(record.progress_percent, "progress_percent"),
    latestLogExcerpt: optionalString(record.latest_log_excerpt, "latest_log_excerpt"),
    cancelRequestedAt: optionalString(record.cancel_requested_at, "cancel_requested_at"),
    cancelRequestedByUserId: optionalString(
      record.cancel_requested_by_user_id,
      "cancel_requested_by_user_id"
    ),
    cancelReason: optionalString(record.cancel_reason, "cancel_reason"),
    failureCode: optionalString(record.failure_code, "failure_code"),
    failureMessage: optionalString(record.failure_message, "failure_message"),
    isStale: requireBoolean(record.is_stale, "is_stale"),
    staleAfterSeconds: optionalNumber(record.stale_after_seconds, "stale_after_seconds"),
    warningAcknowledgement:
      record.warning_acknowledgement === null
        ? null
        : requireRecord(record.warning_acknowledgement, "warning_acknowledgement"),
    warnings: requireArray(record.warnings, "warnings").map(parseModelTrainingWarning),
    metricsSummary: requireRecord(record.metrics_summary, "metrics_summary"),
    itemResults: requireArray(record.item_results, "item_results").map(
      parseBenchmarkEvaluationItemResult
    ),
    rawPredictionArtifactId: optionalString(
      record.raw_prediction_artifact_id,
      "raw_prediction_artifact_id"
    ),
    reportArtifactId: optionalString(record.report_artifact_id, "report_artifact_id"),
    artifactIds: requireArray(record.artifact_ids, "artifact_ids").map((id) =>
      requireString(id, "artifact_ids[]")
    ),
    createdByUserId: requireString(record.created_by_user_id, "created_by_user_id"),
    createdAt: requireString(record.created_at, "created_at")
  };
}

function parseBenchmarkEvaluationList(value: unknown): BenchmarkEvaluationList {
  const record = requireRecord(value, "Benchmark Evaluation list response");
  return {
    benchmarkEvaluations: requireArray(
      record.benchmark_evaluations,
      "benchmark_evaluations"
    ).map(parseBenchmarkEvaluation)
  };
}

function parseModelTrainingWarning(value: unknown): ModelTrainingWarning {
  const record = requireRecord(value, "Model training warning response");
  return {
    code: requireString(record.code, "code"),
    severity: requireModelTrainingWarningSeverity(record.severity),
    message: requireString(record.message, "message")
  };
}

function parseGeneratedDatasetExportFile(value: unknown): GeneratedDatasetExportFile {
  const record = requireRecord(value, "Generated dataset export file response");
  return {
    relativePath: requireString(record.relative_path, "relative_path"),
    fileKind: requireGeneratedDatasetExportFileKind(record.file_kind),
    split: requireGeneratedDatasetExportSplit(record.split),
    datasetItemId: optionalString(record.dataset_item_id, "dataset_item_id"),
    trainingCropId: optionalString(record.training_crop_id, "training_crop_id"),
    inspectionPhotoId: optionalString(record.inspection_photo_id, "inspection_photo_id"),
    exportFilenameStem: optionalString(record.export_filename_stem, "export_filename_stem"),
    sizeBytes: requireNumber(record.size_bytes, "size_bytes"),
    sha256: requireString(record.sha256, "sha256")
  };
}

function parseYoloObbLabelEntry(value: unknown): YoloObbLabelEntry {
  const record = requireRecord(value, "YOLO OBB label entry response");
  return {
    datasetItemId: requireString(record.dataset_item_id, "dataset_item_id"),
    trainingCropId: requireString(record.training_crop_id, "training_crop_id"),
    annotationId: requireString(record.annotation_id, "annotation_id"),
    split: requireDatasetRole(record.split),
    classId: requireNumber(record.class_id, "class_id"),
    className: requireBeeAnnotationType(record.class_name),
    label: requireString(record.label, "label"),
    points: requireArray(record.points, "points").map((point) => requireNumber(point, "points[]"))
  };
}

function parseYoloObbImageEntry(value: unknown): YoloObbImageEntry {
  const record = requireRecord(value, "YOLO OBB image entry response");
  return {
    datasetItemId: requireString(record.dataset_item_id, "dataset_item_id"),
    trainingCropId: requireString(record.training_crop_id, "training_crop_id"),
    inspectionPhotoId: requireString(record.inspection_photo_id, "inspection_photo_id"),
    split: requireDatasetRole(record.split),
    cropX: requireNumber(record.crop_x, "crop_x"),
    cropY: requireNumber(record.crop_y, "crop_y"),
    cropWidth: requireNumber(record.crop_width, "crop_width"),
    cropHeight: requireNumber(record.crop_height, "crop_height")
  };
}

function parseYoloObbExcludedItem(value: unknown): YoloObbExcludedItem {
  const record = requireRecord(value, "YOLO OBB excluded item response");
  return {
    datasetItemId: requireString(record.dataset_item_id, "dataset_item_id"),
    trainingCropId: optionalString(record.training_crop_id, "training_crop_id"),
    datasetRole: requireDatasetRole(record.dataset_role),
    reason: requireString(record.reason, "reason")
  };
}

function parseInspectionPhotoEvidence(value: unknown): InspectionPhotoEvidence {
  const photo = requireRecord(value, "Inspection photo evidence response");
  return {
    inspectionPhotoId: requireString(photo.inspection_photo_id, "inspection_photo_id"),
    filename: requireString(photo.filename, "filename"),
    contentType: requireString(photo.content_type, "content_type"),
    viewUrl: requireString(photo.view_url, "view_url"),
    width: requireNumber(photo.width, "width"),
    height: requireNumber(photo.height, "height")
  };
}

function parseAnnotation(value: unknown): Annotation {
  const record = requireRecord(value, "Annotation response");
  return {
    annotationId: requireString(record.annotation_id, "annotation_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    inspectionPhotoId: requireString(record.inspection_photo_id, "inspection_photo_id"),
    analysisResultId: optionalString(record.analysis_result_id, "analysis_result_id"),
    labellingSessionId: optionalString(record.labelling_session_id, "labelling_session_id"),
    workflowType: requireAnnotationWorkflowType(record.workflow_type),
    annotationType: requireAnnotationType(record.annotation_type),
    x: requireNumber(record.x, "x"),
    y: requireNumber(record.y, "y"),
    width: requireNumber(record.width, "width"),
    height: requireNumber(record.height, "height"),
    coordinateSpace: requireCoordinateSpace(record.coordinate_space),
    sourceImageWidthPx: requireNumber(record.source_image_width_px, "source_image_width_px"),
    sourceImageHeightPx: requireNumber(record.source_image_height_px, "source_image_height_px"),
    confidence: requireNumber(record.confidence, "confidence"),
    source: requireString(record.source, "source"),
    createdAt: requireString(record.created_at, "created_at"),
    latestReviewDecision:
      record.latest_review_decision === null
        ? null
        : parseReviewDecision(record.latest_review_decision)
  };
}

function parseDatasetLabellingSession(value: unknown): DatasetLabellingSession {
  const record = requireRecord(value, "Dataset labelling session response");
  return {
    labellingSessionId: requireString(record.labelling_session_id, "labelling_session_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    inspectionPhotoId: requireString(record.inspection_photo_id, "inspection_photo_id"),
    createdByUserId: requireString(record.created_by_user_id, "created_by_user_id"),
    status: requireDatasetLabellingSessionStatus(record.status),
    sourceGroupKey: optionalString(record.source_group_key, "source_group_key"),
    imageQualityStatus: requireImageQualityStatus(record.image_quality_status),
    prelabelerRun: parsePrelabelerRun(record.prelabeler_run),
    createdAt: requireString(record.created_at, "created_at"),
    updatedAt: requireString(record.updated_at, "updated_at")
  };
}

function parsePrelabelerRun(value: unknown): PrelabelerRun {
  const record = requireRecord(value, "Prelabeler run response");
  return {
    prelabelerRunId: requireString(record.prelabeler_run_id, "prelabeler_run_id"),
    prelabelerName: requireString(record.prelabeler_name, "prelabeler_name"),
    prelabelerVersion: requireString(record.prelabeler_version, "prelabeler_version"),
    provider: requirePrelabelerProvider(record.provider),
    adapterVersion: requireString(record.adapter_version, "adapter_version"),
    modelId: optionalString(record.model_id, "model_id"),
    checkpointId: optionalString(record.checkpoint_id, "checkpoint_id"),
    promptText: optionalString(record.prompt_text, "prompt_text"),
    boxThreshold: optionalNumber(record.box_threshold, "box_threshold"),
    textThreshold: optionalNumber(record.text_threshold, "text_threshold"),
    runtimeMode: requireRuntimeMode(record.runtime_mode),
    status: requirePrelabelerRunStatus(record.status),
    suggestionCount: requireNumber(record.suggestion_count, "suggestion_count"),
    startedAt: requireString(record.started_at, "started_at"),
    finishedAt: optionalString(record.finished_at, "finished_at"),
    errorCode: optionalString(record.error_code, "error_code"),
    errorMessage: optionalString(record.error_message, "error_message")
  };
}

function parseReviewDecision(value: unknown): ReviewDecision {
  const record = requireRecord(value, "Review decision response");
  return {
    reviewDecisionId: requireString(record.review_decision_id, "review_decision_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    reviewerId: requireString(record.reviewer_id, "reviewer_id"),
    subjectType: requireReviewSubjectType(record.subject_type),
    subjectId: requireString(record.subject_id, "subject_id"),
    decision: requireReviewDecisionValue(record.decision),
    notes: optionalString(record.notes, "notes"),
    createdAt: requireString(record.created_at, "created_at")
  };
}

function requireRecord(value: unknown, label: string): Record<string, unknown> {
  if (!isRecord(value)) {
    throw new Error(`${label} was not an object`);
  }
  return value;
}

function requireArray(value: unknown, field: string): unknown[] {
  if (!Array.isArray(value)) {
    throw new Error(`Core API response field ${field} was not an array`);
  }
  return value;
}

function parseStringMap(value: unknown, field: string): Record<string, string> {
  const record = requireRecord(value, field);
  return Object.fromEntries(
    Object.entries(record).map(([key, mapValue]) => [key, requireString(mapValue, `${field}.${key}`)])
  );
}

function parseNumberMap(value: unknown, field: string): Record<string, number> {
  const record = requireRecord(value, field);
  return Object.fromEntries(
    Object.entries(record).map(([key, mapValue]) => [key, requireNumber(mapValue, `${field}.${key}`)])
  );
}

function requireString(value: unknown, field: string): string {
  if (typeof value !== "string") {
    throw new Error(`Core API response field ${field} was not a string`);
  }
  return value;
}

function optionalString(value: unknown, field: string): string | null {
  if (value === null) {
    return null;
  }
  return requireString(value, field);
}

function requireNumber(value: unknown, field: string): number {
  if (typeof value !== "number") {
    throw new Error(`Core API response field ${field} was not a number`);
  }
  return value;
}

function optionalNumber(value: unknown, field: string): number | null {
  if (value === null) {
    return null;
  }
  return requireNumber(value, field);
}

function requireBoolean(value: unknown, field: string): boolean {
  if (typeof value !== "boolean") {
    throw new Error(`Core API response field ${field} was not a boolean`);
  }
  return value;
}

function requireAgreementStatus(value: unknown): "missing" | "accepted" {
  if (value === "missing" || value === "accepted") {
    return value;
  }
  throw new Error("Core API response had an unexpected data-use agreement status");
}

function requireUploadStatus(value: unknown): "accepted" {
  if (value === "accepted") {
    return value;
  }
  throw new Error("Core API response had an unexpected upload status");
}

function requireInspectionIntent(value: unknown): InspectionIntent {
  if (value === "training_data_collection" || value === "varroa_assessment") {
    return value;
  }
  throw new Error("Core API response had an unexpected inspection intent");
}

function requireFrameStandardStatus(value: unknown): FrameStandardStatus {
  if (value === "known" || value === "unknown" || value === "other") {
    return value;
  }
  throw new Error("Core API response had an unexpected Frame Standard status");
}

function requireHiveConfigurationStatus(value: unknown): "current" {
  if (value === "current") {
    return value;
  }
  throw new Error("Core API response had an unexpected Hive Configuration status");
}

function requireAnalysisStatus(value: unknown): PhotoIntake["analysisRun"]["status"] {
  if (value === "queued" || value === "running" || value === "completed" || value === "failed") {
    return value;
  }
  throw new Error("Core API response had an unexpected analysis status");
}

function requireResultKind(value: unknown): "deterministic_stub" {
  if (value === "deterministic_stub") {
    return value;
  }
  throw new Error("Core API response had an unexpected analysis result kind");
}

function requireAnnotationType(value: unknown): AnnotationType {
  if (
    value === "complete_visible_bee" ||
    value === "partial_visible_bee" ||
    value === "likely_varroa_detection"
  ) {
    return value;
  }
  throw new Error("Core API response had an unexpected annotation type");
}

function requireBeeAnnotationType(value: unknown): BeeAnnotationType {
  if (value === "complete_visible_bee" || value === "partial_visible_bee") {
    return value;
  }
  throw new Error("Core API response had an unexpected bee annotation type");
}

function requireOrientationReliability(value: unknown): OrientationReliability {
  if (value === "reliable" || value === "unreliable") {
    return value;
  }
  throw new Error("Core API response had an unexpected Orientation Reliability");
}

function requireVarroaReviewSuitability(value: unknown): VarroaReviewSuitability {
  if (
    value === "unassessed" ||
    value === "appears_assessable" ||
    value === "body_occluded_or_hard_to_assess"
  ) {
    return value;
  }
  throw new Error("Core API response had an unexpected Varroa Review Suitability");
}

function requireVarroaReviewOutcomeValue(value: unknown): VarroaReviewOutcomeValue {
  if (
    value === "visible_varroa_present" ||
    value === "no_visible_varroa" ||
    value === "not_determined"
  ) {
    return value;
  }
  throw new Error("Core API response had an unexpected Varroa Review Outcome");
}

function requireVarroaReviewEligibility(value: unknown): "eligible" | "ineligible" {
  if (value === "eligible" || value === "ineligible") {
    return value;
  }
  throw new Error("Core API response had an unexpected Varroa Review eligibility");
}

function requireFrameLevelVarroaReadinessState(
  value: unknown
): "not_available" | "partial_evidence" | "complete_reviewed_evidence" {
  if (
    value === "not_available" ||
    value === "partial_evidence" ||
    value === "complete_reviewed_evidence"
  ) {
    return value;
  }
  throw new Error("Core API response had an unexpected photo-visible Varroa readiness state");
}

function requireLiteral<T extends string>(value: unknown, expected: T, field: string): T {
  if (value === expected) {
    return expected;
  }
  throw new Error(`Core API response field ${field} was not ${expected}`);
}

function requireCoordinateSpace(value: unknown): "normalized" {
  if (value === "normalized") {
    return value;
  }
  throw new Error("Core API response had an unexpected coordinate space");
}

function requireSourceImagePixelCoordinateSpace(value: unknown): "source_image_pixels" {
  if (value === "source_image_pixels") {
    return value;
  }
  throw new Error("Core API response had an unexpected source pixel coordinate space");
}

function requireAnnotationWorkflowType(value: unknown): "analysis_result" | "dataset_labelling" {
  if (value === "analysis_result" || value === "dataset_labelling") {
    return value;
  }
  throw new Error("Core API response had an unexpected annotation workflow type");
}

function requireDatasetLabellingSessionStatus(value: unknown): DatasetLabellingSessionStatus {
  if (value === "draft_ready" || value === "review_in_progress" || value === "prelabel_failed") {
    return value;
  }
  throw new Error("Core API response had an unexpected dataset labelling session status");
}

function requireImageQualityStatus(value: unknown): ImageQualityStatus {
  if (
    value === "unassessed" ||
    value === "usable" ||
    value === "poor_quality" ||
    value === "exclude"
  ) {
    return value;
  }
  throw new Error("Core API response had an unexpected image quality status");
}

function requireDatasetRole(value: unknown): DatasetRole {
  if (
    value === "training" ||
    value === "validation" ||
    value === "benchmark" ||
    value === "excluded"
  ) {
    return value;
  }
  throw new Error("Core API response had an unexpected dataset role");
}

function requireDatasetVersionMembership(
  value: unknown
): DatasetVersionMembership["membership"] {
  if (
    value === "included" ||
    value === "training" ||
    value === "validation" ||
    value === "protected_benchmark" ||
    value === "excluded" ||
    value === "not_in_version"
  ) {
    return value;
  }
  throw new Error("Core API response had an unexpected Dataset Version membership");
}

function requireDatasetRepositoryWarningSeverity(
  value: unknown
): DatasetRepositoryWarning["severity"] {
  if (value === "info" || value === "warning") {
    return value;
  }
  throw new Error("Core API response had an unexpected repository warning severity");
}

function requireDatasetItemSourceEvidenceType(
  value: unknown
): "dataset_labelling_session" | "training_crop" {
  if (value === "dataset_labelling_session" || value === "training_crop") {
    return value;
  }
  throw new Error("Core API response had an unexpected Dataset Item source evidence type");
}

function requireYoloObbExportFormat(value: unknown): "yolo_obb" {
  if (value === "yolo_obb") {
    return value;
  }
  throw new Error("Core API response had an unexpected export format");
}

function requireTrainingExportFormat(value: unknown): TrainingExportFormat {
  if (
    value === "yolo_obb_v1" ||
    value === "marked_bee_dataset_v1" ||
    value === "bee_orientation_head_up_down_v1"
  ) {
    return value;
  }
  throw new Error("Core API response had an unexpected training export format");
}

function requireModelPurpose(value: unknown): ModelPurpose {
  if (value === "bee_detector" || value === "marked_bee" || value === "bee_orientation") {
    return value;
  }
  throw new Error("Core API response had an unexpected model purpose");
}

function requireTrainingAdapterType(value: unknown): TrainingAdapterType {
  if (
    value === "fake" ||
    value === "ultralytics_yolo_obb" ||
    value === "torchvision_orientation_classifier"
  ) {
    return value;
  }
  throw new Error("Core API response had an unexpected training adapter type");
}

function requireReviewMethod(
  value: unknown
): "human_from_scratch" | "human_reviewed_candidate" | "imported_reviewed" {
  if (
    value === "human_from_scratch" ||
    value === "human_reviewed_candidate" ||
    value === "imported_reviewed"
  ) {
    return value;
  }
  throw new Error("Core API response had an unexpected ellipse review method");
}

function requireCandidateReviewDecision(
  value: unknown
): "accepted" | "accepted_with_edits" | null {
  if (value === null) {
    return null;
  }
  if (value === "accepted" || value === "accepted_with_edits") {
    return value;
  }
  throw new Error("Core API response had an unexpected candidate review decision");
}

function requireModelTrainingWarningSeverity(value: unknown): ModelTrainingWarningSeverity {
  if (value === "info" || value === "warning" || value === "high") {
    return value;
  }
  throw new Error("Core API response had an unexpected model training warning severity");
}

function requireTrainingRunStatus(value: unknown): TrainingRun["status"] {
  if (
    value === "queued" ||
    value === "running" ||
    value === "cancelling" ||
    value === "completed" ||
    value === "failed" ||
    value === "cancelled" ||
    value === "abandoned"
  ) {
    return value;
  }
  throw new Error("Core API response had an unexpected Training Run status");
}

function requireBenchmarkEvaluationStatus(value: unknown): BenchmarkEvaluation["status"] {
  if (
    value === "queued" ||
    value === "running" ||
    value === "cancelling" ||
    value === "completed" ||
    value === "failed" ||
    value === "cancelled"
  ) {
    return value;
  }
  throw new Error("Core API response had an unexpected Benchmark Evaluation status");
}

function requireGeneratedDatasetExportFileKind(
  value: unknown
): "manifest" | "dataset_yaml" | "image" | "label" {
  if (value === "manifest" || value === "dataset_yaml" || value === "image" || value === "label") {
    return value;
  }
  throw new Error("Core API response had an unexpected generated file kind");
}

function requireGeneratedDatasetExportSplit(value: unknown): "train" | "val" | "metadata" {
  if (value === "train" || value === "val" || value === "metadata") {
    return value;
  }
  throw new Error("Core API response had an unexpected generated file split");
}

function requireDatasetExclusionReason(value: unknown): DatasetExclusionReason {
  if (
    value === "poor_image_quality" ||
    value === "ambiguous_subject" ||
    value === "duplicate_or_near_duplicate" ||
    value === "privacy_concern" ||
    value === "unsuitable_crop" ||
    value === "insufficient_review_confidence" ||
    value === "other"
  ) {
    return value;
  }
  throw new Error("Core API response had an unexpected dataset exclusion reason");
}

function requireVisibleBeeStatus(value: unknown): VisibleBeeStatus {
  if (value === "unassessed" || value === "has_visible_bees" || value === "no_visible_bees") {
    return value;
  }
  throw new Error("Core API response had an unexpected visible bee status");
}

function requireTrainingCropReviewStatus(value: unknown): TrainingCropReviewStatus {
  if (value === "review_pending" || value === "review_complete" || value === "excluded") {
    return value;
  }
  throw new Error("Core API response had an unexpected Training Crop review status");
}

function requireTrainingCropExclusionReason(value: unknown): TrainingCropExclusionReason {
  if (
    value === "poor_image_quality" ||
    value === "no_visible_bees" ||
    value === "ambiguous_subject" ||
    value === "unsuitable_crop" ||
    value === "duplicate_or_near_duplicate" ||
    value === "other"
  ) {
    return value;
  }
  throw new Error("Core API response had an unexpected Training Crop exclusion reason");
}

function requirePrelabelerRunStatus(value: unknown): "succeeded" | "failed" {
  if (value === "succeeded" || value === "failed") {
    return value;
  }
  throw new Error("Core API response had an unexpected prelabeler run status");
}

function requirePrelabelerProvider(value: unknown): "deterministic" {
  if (value === "deterministic") {
    return value;
  }
  throw new Error("Core API response had an unexpected prelabeler provider");
}

function requireRuntimeMode(value: unknown): "local" {
  if (value === "local") {
    return value;
  }
  throw new Error("Core API response had an unexpected runtime mode");
}

function requireReviewSubjectType(value: unknown): "annotation" {
  if (value === "annotation") {
    return value;
  }
  throw new Error("Core API response had an unexpected review subject type");
}

function requireReviewQueueSubjectType(value: unknown): "training_crop" {
  if (value === "training_crop") {
    return value;
  }
  throw new Error("Core API response had an unexpected Review Queue subject type");
}

function requireReviewQueueItemStatus(value: unknown): ReviewQueueItemStatus {
  if (value === "available" || value === "completed" || value === "cancelled") {
    return value;
  }
  throw new Error("Core API response had an unexpected Review Queue Item status");
}

function requireReviewQueueOutcomeValue(value: unknown): ReviewQueueOutcomeValue {
  if (value === "approved" || value === "changes_requested" || value === "not_determined") {
    return value;
  }
  throw new Error("Core API response had an unexpected Review Queue outcome");
}

function requireReviewDecisionValue(value: unknown): ReviewDecisionValue {
  if (
    value === "approved" ||
    value === "rejected" ||
    value === "uncertain" ||
    value === "excluded"
  ) {
    return value;
  }
  throw new Error("Core API response had an unexpected review decision");
}

function toCoreApiUrl(pathOrUrl: string): string {
  if (pathOrUrl.startsWith("http://") || pathOrUrl.startsWith("https://")) {
    return pathOrUrl;
  }
  return `${coreApiUrl}${pathOrUrl}`;
}

export function toCoreApiContentUrl(pathOrUrl: string): string {
  return toCoreApiUrl(pathOrUrl);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
