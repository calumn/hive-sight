from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from hive_sight_core_api.dev_store import InMemoryEventRecorder, InMemoryProductDataStore
from hive_sight_core_api.models import AnalysisRunRequest, AnalysisRunResponse, AnalysisRunStatus


@dataclass(frozen=True)
class AnalysisRequestWorkflow:
    store: InMemoryProductDataStore | None = None
    event_recorder: InMemoryEventRecorder | None = None
    id_factory: Callable[[], UUID] = uuid4
    clock: Callable[[], datetime] = lambda: datetime.now(UTC)

    def request_analysis(self, request: AnalysisRunRequest) -> AnalysisRunResponse:
        analysis_run = AnalysisRunResponse(
            analysis_run_id=self.id_factory(),
            inspection_photo_id=request.inspection_photo_id,
            status=AnalysisRunStatus.queued,
            queued_at=self.clock(),
            message="Analysis request queued for the private Analysis Service.",
        )
        if self.store is not None:
            self.store.record_analysis_run(analysis_run)
        if self.event_recorder is not None:
            self.event_recorder.record_analysis_requested(analysis_run)
        return analysis_run

    def get_analysis_status(self, analysis_run_id: UUID) -> AnalysisRunResponse:
        if self.store is not None:
            analysis_run = self.store.get_analysis_run(analysis_run_id)
            if analysis_run is not None:
                return analysis_run

        return AnalysisRunResponse(
            analysis_run_id=analysis_run_id,
            inspection_photo_id=self.id_factory(),
            status=AnalysisRunStatus.queued,
            queued_at=self.clock(),
            message="Analysis status is stubbed until persistence and queue integration are added.",
        )
