from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from hive_sight_analysis_service.model_runtime import ModelRuntime
from hive_sight_analysis_service.models import (
    AnalysisJobRequest,
    AnalysisJobResult,
    AnalysisJobStatus,
)


@dataclass(frozen=True)
class AnalysisJobRunner:
    model_runtime: ModelRuntime
    clock: Callable[[], datetime] = lambda: datetime.now(UTC)

    def run_analysis_job(self, request: AnalysisJobRequest) -> AnalysisJobResult:
        model_analysis = self.model_runtime.analyse_photo(
            original_object_key=request.original_object_key,
            requested_model_version=request.requested_model_version,
        )

        return AnalysisJobResult(
            analysis_run_id=request.analysis_run_id,
            inspection_photo_id=request.inspection_photo_id,
            model_version=model_analysis.model_version,
            status=AnalysisJobStatus.completed,
            complete_visible_bee_count=model_analysis.complete_visible_bee_count,
            partial_visible_bee_count=model_analysis.partial_visible_bee_count,
            likely_varroa_detections=model_analysis.likely_varroa_detections,
            tagged_image_object_key=model_analysis.tagged_image_object_key,
            completed_at=self.clock(),
        )

