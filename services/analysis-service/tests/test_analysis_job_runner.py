from datetime import UTC, datetime
from uuid import UUID

from hive_sight_analysis_service.analysis_job_runner import AnalysisJobRunner
from hive_sight_analysis_service.model_runtime import ModelRuntime
from hive_sight_analysis_service.models import AnalysisJobRequest, AnalysisJobStatus


def test_run_analysis_job_returns_stubbed_model_result_at_runner_seam() -> None:
    completed_at = datetime(2026, 7, 28, 12, 30, tzinfo=UTC)
    runner = AnalysisJobRunner(
        model_runtime=ModelRuntime(default_model_version="stub-varroa-detector-0.1.0"),
        clock=lambda: completed_at,
    )
    request = AnalysisJobRequest(
        analysis_run_id=UUID("00000000-0000-0000-0000-000000000001"),
        inspection_photo_id=UUID("00000000-0000-0000-0000-000000000002"),
        original_object_key="inspection-photos/example/original.jpg",
    )

    result = runner.run_analysis_job(request)

    assert result.analysis_run_id == request.analysis_run_id
    assert result.inspection_photo_id == request.inspection_photo_id
    assert result.model_version == "stub-varroa-detector-0.1.0"
    assert result.status == AnalysisJobStatus.completed
    assert result.complete_visible_bee_count == 3
    assert result.partial_visible_bee_count == 1
    assert result.likely_varroa_detections == 0
    assert result.completed_at == completed_at
    assert [annotation.annotation_type for annotation in result.annotations] == [
        "complete_visible_bee",
        "complete_visible_bee",
        "complete_visible_bee",
        "partial_visible_bee",
    ]
    assert all(annotation.coordinate_space == "normalized" for annotation in result.annotations)
    assert all(annotation.source_image_width_px == 1600 for annotation in result.annotations)
    assert all(annotation.source_image_height_px == 1200 for annotation in result.annotations)
    assert result.annotations[0].confidence == 0.92
