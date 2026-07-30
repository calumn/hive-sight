export type HealthResponse = {
  service: string;
  status: string;
  boundary: string;
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

export type Apiary = {
  apiaryId: string;
  workspaceId: string;
  name: string;
};

export type Hive = {
  hiveId: string;
  apiaryId: string;
  workspaceId: string;
  name: string;
};

export type InspectionIntent = "training_data_collection" | "varroa_assessment";

export type Inspection = {
  inspectionId: string;
  hiveId: string;
  workspaceId: string;
  inspectionDate: string;
  intent: InspectionIntent;
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

export type ReviewDecisionValue = "approved" | "rejected" | "uncertain" | "excluded";

export type ImageQualityStatus = "unassessed" | "usable" | "poor_quality" | "exclude";

export type DatasetRole = "training" | "validation" | "benchmark" | "excluded";

export type DatasetExclusionReason =
  | "poor_image_quality"
  | "ambiguous_subject"
  | "duplicate_or_near_duplicate"
  | "privacy_concern"
  | "unsuitable_crop"
  | "insufficient_review_confidence"
  | "other";

export type DatasetLabellingSessionStatus =
  | "draft_ready"
  | "review_in_progress"
  | "prelabel_failed";

export type PrelabelerRun = {
  prelabelerRunId: string;
  prelabelerName: string;
  prelabelerVersion: string;
  provider: "deterministic" | "grounding_dino";
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
  labellingSessionId: string;
  datasetRole: DatasetRole;
  reviewedAnnotationIds: string[];
  sourceGroupKey: string | null;
  imageQualityStatus: ImageQualityStatus;
  assignedByUserId: string;
  assignedAt: string;
  assignmentNote: string | null;
  exclusionReason: DatasetExclusionReason | null;
  benchmarkProtected: boolean;
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
    boundary: requireString(record.boundary, "boundary")
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

function parseApiary(value: unknown): Apiary {
  const record = requireRecord(value, "Apiary response");
  return {
    apiaryId: requireString(record.apiary_id, "apiary_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    name: requireString(record.name, "name")
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

function parseDatasetItem(value: unknown): DatasetItem {
  const record = requireRecord(value, "Dataset item response");
  return {
    datasetItemId: requireString(record.dataset_item_id, "dataset_item_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    inspectionPhotoId: requireString(record.inspection_photo_id, "inspection_photo_id"),
    labellingSessionId: requireString(record.labelling_session_id, "labelling_session_id"),
    datasetRole: requireDatasetRole(record.dataset_role),
    reviewedAnnotationIds: requireArray(
      record.reviewed_annotation_ids,
      "reviewed_annotation_ids"
    ).map((annotationId) => requireString(annotationId, "reviewed_annotation_ids[]")),
    sourceGroupKey: optionalString(record.source_group_key, "source_group_key"),
    imageQualityStatus: requireImageQualityStatus(record.image_quality_status),
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

function requireCoordinateSpace(value: unknown): "normalized" {
  if (value === "normalized") {
    return value;
  }
  throw new Error("Core API response had an unexpected coordinate space");
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

function requirePrelabelerRunStatus(value: unknown): "succeeded" | "failed" {
  if (value === "succeeded" || value === "failed") {
    return value;
  }
  throw new Error("Core API response had an unexpected prelabeler run status");
}

function requirePrelabelerProvider(value: unknown): "deterministic" | "grounding_dino" {
  if (value === "deterministic" || value === "grounding_dino") {
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

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
