from datetime import UTC, datetime
from uuid import UUID

from beehive_core_api.analysis_request_workflow import AnalysisRequestWorkflow
from beehive_core_api.models import AnalysisRunRequest, AnalysisRunStatus


def test_request_analysis_queues_analysis_run_at_workflow_seam() -> None:
    analysis_run_id = UUID("00000000-0000-0000-0000-000000000001")
    workspace_id = UUID("00000000-0000-0000-0000-000000000002")
    inspection_photo_id = UUID("00000000-0000-0000-0000-000000000003")
    queued_at = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)
    workflow = AnalysisRequestWorkflow(id_factory=lambda: analysis_run_id, clock=lambda: queued_at)

    response = workflow.request_analysis(
        AnalysisRunRequest(
            workspace_id=workspace_id,
            inspection_photo_id=inspection_photo_id,
            original_object_key="inspection-photos/example/original.jpg",
        )
    )

    assert response.analysis_run_id == analysis_run_id
    assert response.inspection_photo_id == inspection_photo_id
    assert response.status == AnalysisRunStatus.queued
    assert response.queued_at == queued_at

