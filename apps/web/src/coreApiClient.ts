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

function requireRecord(value: unknown, label: string): Record<string, unknown> {
  if (!isRecord(value)) {
    throw new Error(`${label} was not an object`);
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

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
