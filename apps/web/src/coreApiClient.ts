export type HealthResponse = {
  service: string;
  status: string;
  boundary: string;
};

export type DevSession = {
  userId: string;
  workspaceId: string;
  role: string;
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

export type Inspection = {
  inspectionId: string;
  hiveId: string;
  workspaceId: string;
  inspectionDate: string;
};

export type PhotoIntake = {
  inspectionPhoto: {
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

export type Annotation = {
  annotationId: string;
  workspaceId: string;
  inspectionPhotoId: string;
  analysisResultId: string;
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
};

export type AnalysisEvidence = {
  analysisRunId: string;
  analysisResultId: string;
  inspectionPhoto: {
    inspectionPhotoId: string;
    filename: string;
    contentType: string;
    viewUrl: string;
    width: number;
    height: number;
  };
  analysisResult: AnalysisResult;
  annotations: Annotation[];
  resultKind: "deterministic_stub";
  modelVersion: string;
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
  inspectionDate
}: {
  devUserId: string;
  hiveId: string;
  inspectionDate: string;
}): Promise<Inspection> {
  const response = await fetch(`${coreApiUrl}/v1/inspections`, {
    method: "POST",
    headers: jsonHeaders(devUserId),
    body: JSON.stringify({ hive_id: hiveId, inspection_date: inspectionDate })
  });
  await ensureOk(response);
  return parseInspection(await response.json());
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
    inspectionDate: requireString(record.inspection_date, "inspection_date")
  };
}

function parsePhotoIntake(value: unknown): PhotoIntake {
  const record = requireRecord(value, "Photo intake response");
  const photo = requireRecord(record.inspection_photo, "Inspection photo response");
  const analysisRun = requireRecord(record.analysis_run, "Analysis run response");
  return {
    inspectionPhoto: {
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
    },
    analysisRun: {
      analysisRunId: requireString(analysisRun.analysis_run_id, "analysis_run_id"),
      inspectionPhotoId: requireString(analysisRun.inspection_photo_id, "inspection_photo_id"),
      status: requireAnalysisStatus(analysisRun.status),
      queuedAt: requireString(analysisRun.queued_at, "queued_at"),
      message: requireString(analysisRun.message, "message")
    }
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
  const photo = requireRecord(record.inspection_photo, "Inspection photo evidence response");
  const annotations = requireArray(record.annotations, "annotations").map(parseAnnotation);
  return {
    analysisRunId: requireString(record.analysis_run_id, "analysis_run_id"),
    analysisResultId: requireString(record.analysis_result_id, "analysis_result_id"),
    inspectionPhoto: {
      inspectionPhotoId: requireString(photo.inspection_photo_id, "inspection_photo_id"),
      filename: requireString(photo.filename, "filename"),
      contentType: requireString(photo.content_type, "content_type"),
      viewUrl: requireString(photo.view_url, "view_url"),
      width: requireNumber(photo.width, "width"),
      height: requireNumber(photo.height, "height")
    },
    analysisResult: parseAnalysisResult(record.analysis_result),
    annotations,
    resultKind: requireResultKind(record.result_kind),
    modelVersion: requireString(record.model_version, "model_version"),
    caveat: requireString(record.caveat, "caveat")
  };
}

function parseAnnotation(value: unknown): Annotation {
  const record = requireRecord(value, "Annotation response");
  return {
    annotationId: requireString(record.annotation_id, "annotation_id"),
    workspaceId: requireString(record.workspace_id, "workspace_id"),
    inspectionPhotoId: requireString(record.inspection_photo_id, "inspection_photo_id"),
    analysisResultId: requireString(record.analysis_result_id, "analysis_result_id"),
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

function toCoreApiUrl(pathOrUrl: string): string {
  if (pathOrUrl.startsWith("http://") || pathOrUrl.startsWith("https://")) {
    return pathOrUrl;
  }
  return `${coreApiUrl}${pathOrUrl}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
