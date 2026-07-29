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
    inspection_photo_id: UUID
    status: AnalysisRunStatus
    queued_at: datetime
    message: str


class ErrorResponse(BaseModel):
    code: str
    message: str


class DevSessionResponse(BaseModel):
    user_id: UUID
    workspace_id: UUID
    role: str
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
