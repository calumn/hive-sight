from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel

from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    AnalysisRunDetailResponse,
    AnalysisRunResponse,
)


class AnalysisJobRequest(BaseModel):
    analysis_run_id: UUID
    inspection_photo_id: UUID
    original_object_key: str
    requested_model_version: str | None = None


class AnalysisJobResult(BaseModel):
    analysis_run_id: UUID
    inspection_photo_id: UUID
    model_version: str
    complete_visible_bee_count: int
    partial_visible_bee_count: int
    likely_varroa_detections: int
    tagged_image_object_key: str | None
    completed_at: datetime


class AnalysisExecutor(Protocol):
    def run_analysis_job(self, request: AnalysisJobRequest) -> AnalysisJobResult:
        """Run one private analysis job and return normalized result data."""


@dataclass(frozen=True)
class DeterministicStubAnalysisExecutor:
    default_model_version: str = "stub-varroa-detector-0.1.0"
    clock: Callable[[], datetime] = lambda: datetime.now(UTC)

    def run_analysis_job(self, request: AnalysisJobRequest) -> AnalysisJobResult:
        return AnalysisJobResult(
            analysis_run_id=request.analysis_run_id,
            inspection_photo_id=request.inspection_photo_id,
            model_version=request.requested_model_version or self.default_model_version,
            complete_visible_bee_count=48,
            partial_visible_bee_count=3,
            likely_varroa_detections=1,
            tagged_image_object_key=None,
            completed_at=self.clock(),
        )


@dataclass(frozen=True)
class AnalysisProcessingWorkflow:
    store: InMemoryProductDataStore
    executor: AnalysisExecutor
    clock: Callable[[], datetime] = lambda: datetime.now(UTC)

    def process_queued_analysis(
        self,
        user: UserContext,
        workspace_id: UUID,
        analysis_run_id: UUID,
    ) -> AnalysisRunDetailResponse:
        analysis_run = self.store.require_queued_analysis_run(
            user=user,
            workspace_id=workspace_id,
            analysis_run_id=analysis_run_id,
        )
        inspection_photo = self.store.inspection_photos.get(analysis_run.inspection_photo_id)
        if inspection_photo is None or inspection_photo.workspace_id != workspace_id:
            raise DomainError(
                "analysis_run_not_found",
                "The Analysis Run does not have an Inspection Photo in this Workspace.",
                404,
            )

        running_run = self.store.mark_analysis_running(analysis_run, started_at=self.clock())
        try:
            result = self.executor.run_analysis_job(
                AnalysisJobRequest(
                    analysis_run_id=running_run.analysis_run_id,
                    inspection_photo_id=running_run.inspection_photo_id,
                    original_object_key=inspection_photo.original_object_key,
                    requested_model_version=running_run.requested_model_version,
                )
            )
        except Exception as exc:
            failed_run = self.store.fail_analysis_run(
                running_run,
                failure_code="analysis_processing_failed",
                failure_message="Analysis processing failed before a result was produced.",
                failed_at=self.clock(),
            )
            raise DomainError(
                failed_run.failure_code or "analysis_processing_failed",
                failed_run.failure_message or "Analysis processing failed.",
                502,
            ) from exc

        completed_run = self.store.complete_analysis_run(
            running_run,
            model_version=result.model_version,
            complete_visible_bee_count=result.complete_visible_bee_count,
            partial_visible_bee_count=result.partial_visible_bee_count,
            likely_varroa_detections=result.likely_varroa_detections,
            tagged_image_object_key=result.tagged_image_object_key,
            completed_at=result.completed_at,
        )
        return self.get_analysis_run_detail(user, workspace_id, completed_run.analysis_run_id)

    def get_analysis_run_detail(
        self,
        user: UserContext,
        workspace_id: UUID,
        analysis_run_id: UUID,
    ) -> AnalysisRunDetailResponse:
        analysis_run = self.store.require_analysis_run(user, workspace_id, analysis_run_id)
        return self._to_detail(analysis_run)

    def _to_detail(self, analysis_run: AnalysisRunResponse) -> AnalysisRunDetailResponse:
        return AnalysisRunDetailResponse(
            analysis_run_id=analysis_run.analysis_run_id,
            workspace_id=analysis_run.workspace_id,
            inspection_photo_id=analysis_run.inspection_photo_id,
            status=analysis_run.status,
            queued_at=analysis_run.queued_at,
            started_at=analysis_run.started_at,
            completed_at=analysis_run.completed_at,
            failed_at=analysis_run.failed_at,
            failure_code=analysis_run.failure_code,
            failure_message=analysis_run.failure_message,
            requested_model_version=analysis_run.requested_model_version,
            model_version=analysis_run.model_version,
            message=analysis_run.message,
            analysis_result=self.store.get_analysis_result(analysis_run.analysis_run_id),
        )
