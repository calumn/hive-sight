from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class AnalysisJobStatus(StrEnum):
    completed = "completed"
    failed = "failed"


class HealthResponse(BaseModel):
    service: str
    status: str
    boundary: str


class AnalysisJobRequest(BaseModel):
    analysis_run_id: UUID
    inspection_photo_id: UUID
    original_object_key: str = Field(min_length=1)
    requested_model_version: str | None = None


class ModelAnalysis(BaseModel):
    model_version: str
    complete_visible_bee_count: int
    partial_visible_bee_count: int
    likely_varroa_detections: int
    tagged_image_object_key: str | None


class AnalysisJobResult(BaseModel):
    analysis_run_id: UUID
    inspection_photo_id: UUID
    model_version: str
    status: AnalysisJobStatus
    complete_visible_bee_count: int
    partial_visible_bee_count: int
    likely_varroa_detections: int
    tagged_image_object_key: str | None
    completed_at: datetime

