from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from beehive_core_api.models import AnalysisRunRequest, AnalysisRunResponse, AnalysisRunStatus


@dataclass(frozen=True)
class AnalysisRequestWorkflow:
    id_factory: Callable[[], UUID] = uuid4
    clock: Callable[[], datetime] = lambda: datetime.now(UTC)

    def request_analysis(self, request: AnalysisRunRequest) -> AnalysisRunResponse:
        return AnalysisRunResponse(
            analysis_run_id=self.id_factory(),
            inspection_photo_id=request.inspection_photo_id,
            status=AnalysisRunStatus.queued,
            queued_at=self.clock(),
            message="Analysis request accepted by Core API scaffold; queue publishing is not wired yet.",
        )

    def get_analysis_status(self, analysis_run_id: UUID) -> AnalysisRunResponse:
        return AnalysisRunResponse(
            analysis_run_id=analysis_run_id,
            inspection_photo_id=self.id_factory(),
            status=AnalysisRunStatus.queued,
            queued_at=self.clock(),
            message="Analysis status is stubbed until persistence and queue integration are added.",
        )

