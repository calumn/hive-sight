from __future__ import annotations

import json
import threading
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from hive_sight_core_api.bee_detector_candidate_annotation_workflow import (
    BeeDetectorInferenceAdapter,
    BeeAnnotationSuggestion,
    _render_crop_png,
)
from hive_sight_core_api.bee_detector_training_workflow import TERMINAL_TRAINING_RUN_STATUSES
from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    ArtifactResponse,
    BenchmarkEvaluationCancelRequest,
    BenchmarkEvaluationItemResultResponse,
    BenchmarkEvaluationReadinessResponse,
    BenchmarkEvaluationResponse,
    BenchmarkEvaluationStartRequest,
    BenchmarkEvaluationWarningResponse,
    DatasetItemResponse,
    ModelTrainingWarningSeverity,
    ReviewedEllipseSnapshot,
)

TERMINAL_BENCHMARK_EVALUATION_STATUSES = {"completed", "failed", "cancelled"}
MATCH_STRATEGY = "ellipse_match_v1"
BENCHMARK_SCOPE = "training_crop_benchmark_only"


@dataclass(frozen=True)
class EvaluationItemOutput:
    result: BenchmarkEvaluationItemResultResponse
    predictions: list[dict[str, object]]


class BeeDetectorBenchmarkEvaluationWorkflow:
    def __init__(
        self,
        *,
        store: InMemoryProductDataStore,
        image_loader: Callable[[str], bytes | None],
        artifact_root: Path,
        adapter: BeeDetectorInferenceAdapter,
        persistence_backend: str,
        database_purpose: str,
        clock: Callable[[], datetime],
        stale_after_seconds: int = 300,
        heartbeat_interval_seconds: int = 5,
    ) -> None:
        self.store = store
        self.image_loader = image_loader
        self.artifact_root = artifact_root
        self.adapter = adapter
        self.persistence_backend = persistence_backend
        self.database_purpose = database_purpose
        self.clock = clock
        self.stale_after_seconds = stale_after_seconds
        self.heartbeat_interval_seconds = heartbeat_interval_seconds

    def readiness(
        self,
        *,
        user: UserContext,
        workspace_id: UUID,
        model_candidate_id: UUID,
    ) -> BenchmarkEvaluationReadinessResponse:
        self._require_curator(user=user, workspace_id=workspace_id)
        candidate, training_run, dataset_version = self._candidate_context(
            workspace_id=workspace_id,
            model_candidate_id=model_candidate_id,
        )
        active_training = self.store.active_training_run(workspace_id)
        active_evaluation = self.store.active_benchmark_evaluation(workspace_id)
        active_model_job_id = None
        active_model_job_type = None
        if active_training is not None:
            active_model_job_id = active_training.training_run_id
            active_model_job_type = "training_run"
        elif active_evaluation is not None:
            active_model_job_id = active_evaluation.benchmark_evaluation_id
            active_model_job_type = "benchmark_evaluation"
        warnings = self._benchmark_warnings(
            training_dataset_item_ids=[
                *dataset_version.training_dataset_item_ids,
                *dataset_version.validation_dataset_item_ids,
            ],
            benchmark_item_ids=dataset_version.protected_benchmark_dataset_item_ids,
        )
        return BenchmarkEvaluationReadinessResponse(
            workspace_id=workspace_id,
            model_candidate_id=candidate.model_candidate_id,
            model_candidate_human_readable_id=candidate.human_readable_id,
            adapter_type=self.adapter.adapter_type,
            training_adapter_type=training_run.adapter_type,
            evaluation_adapter_type=self.adapter.adapter_type,
            database_purpose=self.database_purpose,
            benchmark_item_count=len(dataset_version.protected_benchmark_dataset_item_ids),
            eligible_to_start_evaluation=(
                active_model_job_id is None
                and len(dataset_version.protected_benchmark_dataset_item_ids) > 0
                and self._blocking_evaluation_reason(
                    candidate_adapter_type=candidate.adapter_type,
                    benchmark_item_ids=dataset_version.protected_benchmark_dataset_item_ids,
                )
                is None
            ),
            active_model_job_id=active_model_job_id,
            active_model_job_type=active_model_job_type,
            warnings=warnings,
        )

    def start_evaluation(
        self,
        *,
        user: UserContext,
        request: BenchmarkEvaluationStartRequest,
    ) -> BenchmarkEvaluationResponse:
        self._require_curator(user=user, workspace_id=request.workspace_id)
        candidate, training_run, dataset_version = self._candidate_context(
            workspace_id=request.workspace_id,
            model_candidate_id=request.model_candidate_id,
        )
        if self.store.active_training_run(request.workspace_id) is not None:
            raise DomainError(
                "model_job_already_active",
                "Another model job is already active in this local environment.",
                409,
            )
        if self.store.active_benchmark_evaluation(request.workspace_id) is not None:
            raise DomainError(
                "model_job_already_active",
                "Another model job is already active in this local environment.",
                409,
            )
        blocking_reason = self._blocking_evaluation_reason(
            candidate_adapter_type=candidate.adapter_type,
            benchmark_item_ids=dataset_version.protected_benchmark_dataset_item_ids,
        )
        if blocking_reason is not None:
            raise blocking_reason
        warnings = self._benchmark_warnings(
            training_dataset_item_ids=[
                *dataset_version.training_dataset_item_ids,
                *dataset_version.validation_dataset_item_ids,
            ],
            benchmark_item_ids=dataset_version.protected_benchmark_dataset_item_ids,
        )
        high_warning_codes = [
            warning.code
            for warning in warnings
            if warning.severity == ModelTrainingWarningSeverity.high
        ]
        if high_warning_codes and not request.acknowledge_high_severity_warnings:
            raise DomainError(
                "benchmark_warnings_require_acknowledgement",
                "Acknowledge high-severity benchmark warnings before running evaluation.",
                409,
            )
        created_at = self.clock()
        evaluation_id = self.store.id_factory()
        evaluation = BenchmarkEvaluationResponse(
            benchmark_evaluation_id=evaluation_id,
            workspace_id=request.workspace_id,
            human_readable_id=self._human_id(
                "HS-BE", self.store.list_benchmark_evaluations(request.workspace_id)
            ),
            model_candidate_id=candidate.model_candidate_id,
            model_candidate_human_readable_id=candidate.human_readable_id,
            training_run_id=training_run.training_run_id,
            dataset_version_id=dataset_version.dataset_version_id,
            status="queued",
            phase="queued",
            adapter_type=self.adapter.adapter_type,
            training_adapter_type=training_run.adapter_type,
            evaluation_adapter_type=self.adapter.adapter_type,
            database_purpose=self.database_purpose,
            confidence_threshold=request.confidence_threshold,
            match_strategy=MATCH_STRATEGY,
            benchmark_scope=BENCHMARK_SCOPE,
            started_at=None,
            completed_at=None,
            last_heartbeat_at=created_at,
            last_activity_message="Benchmark Evaluation queued.",
            progress_percent=0,
            latest_log_excerpt=None,
            warning_acknowledgement={
                "acknowledged": bool(high_warning_codes),
                "warning_codes": high_warning_codes,
                "acknowledged_by_user_id": str(user.user_id) if high_warning_codes else None,
                "acknowledged_at": created_at.isoformat() if high_warning_codes else None,
            }
            if high_warning_codes
            else None,
            warnings=warnings,
            metrics_summary={},
            item_results=[],
            raw_prediction_artifact_id=None,
            report_artifact_id=None,
            artifact_ids=[],
            created_by_user_id=user.user_id,
            created_at=created_at,
        )
        self.store.save_benchmark_evaluation(evaluation)
        self._start_background_evaluation(evaluation)
        return self._with_runtime_state(evaluation)

    def list_evaluations(
        self,
        *,
        user: UserContext,
        workspace_id: UUID,
    ) -> list[BenchmarkEvaluationResponse]:
        self._require_curator(user=user, workspace_id=workspace_id)
        return [
            self._with_runtime_state(evaluation)
            for evaluation in self.store.list_benchmark_evaluations(workspace_id)
        ]

    def get_evaluation(
        self,
        *,
        user: UserContext,
        workspace_id: UUID,
        benchmark_evaluation_id: UUID,
    ) -> BenchmarkEvaluationResponse:
        self._require_curator(user=user, workspace_id=workspace_id)
        evaluation = self.store.get_benchmark_evaluation(workspace_id, benchmark_evaluation_id)
        if evaluation is None:
            raise DomainError(
                "benchmark_evaluation_not_found",
                "Benchmark Evaluation not found.",
                404,
            )
        return self._with_runtime_state(evaluation)

    def cancel_evaluation(
        self,
        *,
        user: UserContext,
        benchmark_evaluation_id: UUID,
        request: BenchmarkEvaluationCancelRequest,
    ) -> BenchmarkEvaluationResponse:
        self._require_curator(user=user, workspace_id=request.workspace_id)
        evaluation = self.get_evaluation(
            user=user,
            workspace_id=request.workspace_id,
            benchmark_evaluation_id=benchmark_evaluation_id,
        )
        if evaluation.status in TERMINAL_BENCHMARK_EVALUATION_STATUSES:
            raise DomainError(
                "benchmark_evaluation_already_terminal",
                "Only queued or running Benchmark Evaluations can be cancelled.",
                409,
            )
        cancelled = evaluation.model_copy(
            update={
                "status": "cancelling",
                "phase": "cancelling",
                "last_heartbeat_at": self.clock(),
                "last_activity_message": "Cancellation requested.",
                "cancel_requested_at": self.clock(),
                "cancel_requested_by_user_id": user.user_id,
                "cancel_reason": _clean_optional_text(request.reason),
            }
        )
        self.store.save_benchmark_evaluation(cancelled)
        return self._with_runtime_state(cancelled)

    def _run_evaluation_now(
        self,
        evaluation: BenchmarkEvaluationResponse,
    ) -> BenchmarkEvaluationResponse:
        run_dir = self._evaluation_dir(evaluation)
        run_dir.mkdir(parents=True, exist_ok=True)
        log_path = run_dir / "benchmark-evaluation.log"
        self._append_log(log_path, "Benchmark Evaluation worker started.")
        running = evaluation.model_copy(
            update={
                "status": "running",
                "phase": "evaluating_items",
                "started_at": self.clock(),
                "last_heartbeat_at": self.clock(),
                "last_activity_message": "Evaluating protected benchmark Training Crops.",
                "progress_percent": 5,
                "latest_log_excerpt": self._latest_log_excerpt(log_path),
            }
        )
        self.store.save_benchmark_evaluation(running)
        heartbeat_stop = threading.Event()
        heartbeat_thread = threading.Thread(
            target=self._heartbeat_while_active,
            args=(running.workspace_id, running.benchmark_evaluation_id, log_path, heartbeat_stop),
            daemon=True,
            name=f"hivesight-benchmark-heartbeat-{running.benchmark_evaluation_id}",
        )
        heartbeat_thread.start()
        try:
            candidate, _, dataset_version = self._candidate_context(
                workspace_id=running.workspace_id,
                model_candidate_id=running.model_candidate_id,
            )
            artifact = self.store.get_artifact(candidate.artifact_id)
            if artifact is None:
                raise DomainError(
                    "model_candidate_artifact_missing",
                    "The Model Candidate weights artifact is missing.",
                    404,
                )
            model_artifact_path = self._artifact_path(artifact.relative_path)
            item_results: list[BenchmarkEvaluationItemResultResponse] = []
            raw_predictions: list[dict[str, object]] = []
            benchmark_ids = dataset_version.protected_benchmark_dataset_item_ids
            for index, dataset_item_id in enumerate(benchmark_ids, start=1):
                current = self.store.get_benchmark_evaluation(
                    running.workspace_id,
                    running.benchmark_evaluation_id,
                )
                if current is not None and current.status == "cancelling":
                    cancelled = current.model_copy(
                        update={
                            "status": "cancelled",
                            "phase": "cancelled",
                            "completed_at": self.clock(),
                            "last_heartbeat_at": self.clock(),
                            "last_activity_message": "Benchmark Evaluation cancelled between items.",
                            "progress_percent": None,
                            "latest_log_excerpt": self._latest_log_excerpt(log_path),
                        }
                    )
                    self.store.save_benchmark_evaluation(cancelled)
                    heartbeat_stop.set()
                    heartbeat_thread.join(timeout=1)
                    return cancelled
                item = self.store.dataset_items[dataset_item_id]
                output = self._evaluate_item(
                    item=item,
                    model_artifact_path=model_artifact_path,
                    confidence_threshold=running.confidence_threshold,
                )
                item_results.append(output.result)
                raw_predictions.append(
                    {
                        "dataset_item_id": str(item.dataset_item_id),
                        "human_readable_id": _dataset_item_label(item.dataset_item_id),
                        "predictions": output.predictions,
                    }
                )
                progress = 5 + (index / max(len(benchmark_ids), 1)) * 80
                running = running.model_copy(
                    update={
                        "last_heartbeat_at": self.clock(),
                        "last_activity_message": f"Evaluated benchmark item {index} of {len(benchmark_ids)}.",
                        "progress_percent": round(progress, 1),
                        "latest_log_excerpt": self._latest_log_excerpt(log_path),
                    }
                )
                self.store.save_benchmark_evaluation(running)
            metrics = _metrics(
                item_results,
                confidence_threshold=running.confidence_threshold,
            )
            raw_artifact_id = self._write_raw_prediction_artifact(
                evaluation=running,
                raw_predictions=raw_predictions,
            )
            completed = running.model_copy(
                update={
                    "status": "completed",
                    "phase": "completed",
                    "completed_at": self.clock(),
                    "last_heartbeat_at": self.clock(),
                    "last_activity_message": "Benchmark Evaluation completed.",
                    "progress_percent": 100,
                    "metrics_summary": metrics,
                    "item_results": item_results,
                    "raw_prediction_artifact_id": raw_artifact_id,
                    "artifact_ids": [raw_artifact_id],
                    "latest_log_excerpt": self._latest_log_excerpt(log_path),
                }
            )
            report_artifact_id = self._write_report_artifact(completed)
            log_artifact_id = self._record_artifact(
                owner_type="benchmark_evaluation",
                owner_id=completed.benchmark_evaluation_id,
                artifact_type="benchmark_evaluation_log",
                path=log_path,
                content_type="text/plain",
                required_or_diagnostic="diagnostic",
            ).artifact_id
            completed = completed.model_copy(
                update={
                    "report_artifact_id": report_artifact_id,
                    "artifact_ids": [raw_artifact_id, report_artifact_id, log_artifact_id],
                }
            )
            self.store.save_benchmark_evaluation(completed)
            completed_candidate = candidate.model_copy(update={"promotion_status": "benchmark_reported"})
            self.store.save_model_candidate(completed_candidate)
            heartbeat_stop.set()
            heartbeat_thread.join(timeout=1)
            return completed
        except DomainError as error:
            heartbeat_stop.set()
            heartbeat_thread.join(timeout=1)
            failed = running.model_copy(
                update={
                    "status": "failed",
                    "phase": "failed",
                    "completed_at": self.clock(),
                    "last_heartbeat_at": self.clock(),
                    "last_activity_message": "Benchmark Evaluation failed.",
                    "progress_percent": None,
                    "latest_log_excerpt": self._latest_log_excerpt(log_path),
                    "failure_code": error.code,
                    "failure_message": error.message,
                }
            )
            self.store.save_benchmark_evaluation(failed)
            return failed
        except Exception as error:
            heartbeat_stop.set()
            heartbeat_thread.join(timeout=1)
            failed = running.model_copy(
                update={
                    "status": "failed",
                    "phase": "failed",
                    "completed_at": self.clock(),
                    "last_heartbeat_at": self.clock(),
                    "last_activity_message": "Benchmark Evaluation failed unexpectedly.",
                    "progress_percent": None,
                    "latest_log_excerpt": self._latest_log_excerpt(log_path),
                    "failure_code": "benchmark_evaluation_failed",
                    "failure_message": str(error),
                }
            )
            self.store.save_benchmark_evaluation(failed)
            return failed

    def _evaluate_item(
        self,
        *,
        item: DatasetItemResponse,
        model_artifact_path: Path,
        confidence_threshold: float,
    ) -> EvaluationItemOutput:
        if item.training_crop_id is None:
            raise DomainError(
                "unsupported_benchmark_item_type",
                "Only Training Crop benchmark Dataset Items can be evaluated in this slice.",
                409,
            )
        crop = self.store.training_crops.get(item.training_crop_id)
        if crop is None:
            raise DomainError("training_crop_missing", "Benchmark Training Crop is missing.", 409)
        photo = self.store.inspection_photos.get(item.inspection_photo_id)
        if photo is None:
            raise DomainError("source_image_missing", "Benchmark source image is missing.", 409)
        image_bytes = self.image_loader(photo.original_object_key)
        if image_bytes is None:
            raise DomainError(
                "source_image_missing",
                "Benchmark source image bytes are missing.",
                409,
            )
        crop_png = _render_crop_png(image_bytes=image_bytes, crop=crop)
        suggestions = self.adapter.suggest_bees(
            crop_png=crop_png,
            crop=crop,
            model_artifact_path=model_artifact_path,
            confidence_threshold=confidence_threshold,
            max_suggestions=200,
        )
        matched_count = _matched_count(item.reviewed_ellipse_snapshots, suggestions)
        prediction_count = len(suggestions)
        ground_truth_count = len(item.reviewed_ellipse_snapshots)
        hive_snapshot = item.provenance.hive_configuration if item.provenance else None
        return EvaluationItemOutput(
            result=BenchmarkEvaluationItemResultResponse(
                dataset_item_id=item.dataset_item_id,
                human_readable_id=_dataset_item_label(item.dataset_item_id),
                source_group_key=item.source_group_key,
                hive_configuration_frame_standard_id=(
                    hive_snapshot.frame_standard_id if hive_snapshot else None
                ),
                curriculum_stage=item.curriculum_stage,
                ground_truth_count=ground_truth_count,
                prediction_count=prediction_count,
                matched_count=matched_count,
                false_positive_count=max(prediction_count - matched_count, 0),
                false_negative_count=max(ground_truth_count - matched_count, 0),
            ),
            predictions=[
                {
                    "center_x": suggestion.center_x,
                    "center_y": suggestion.center_y,
                    "radius_x": suggestion.radius_x,
                    "radius_y": suggestion.radius_y,
                    "rotation_degrees": suggestion.rotation_degrees,
                    "confidence": suggestion.confidence,
                    "raw_model_class": suggestion.raw_model_class,
                    "raw_yolo_obb": suggestion.raw_yolo_obb,
                    "normalized_geometry": {
                        "coordinate_space": "source_image_pixels",
                        "match_strategy": MATCH_STRATEGY,
                    },
                }
                for suggestion in suggestions
            ],
        )

    def _blocking_evaluation_reason(
        self,
        *,
        candidate_adapter_type: str,
        benchmark_item_ids: list[UUID],
    ) -> DomainError | None:
        if not benchmark_item_ids:
            return DomainError(
                "benchmark_items_required",
                "At least one protected benchmark Dataset Item is required.",
                409,
            )
        if self.adapter.adapter_type != "fake" and candidate_adapter_type == "fake":
            return DomainError(
                "fake_candidate_real_evaluation_not_allowed",
                "A fake-trained Model Candidate cannot be evaluated with the real YOLO adapter.",
                409,
            )
        if self.adapter.adapter_type != "fake" and self.database_purpose == "test":
            return DomainError(
                "real_adapter_refuses_test_database",
                "Real YOLO evaluation must target the dev or QA database, not the resettable test database.",
                409,
            )
        if self.adapter.adapter_type != "fake" and not self.adapter.check_available():
            return DomainError(
                "real_adapter_unavailable",
                "Run pnpm model:setup:bee before using the real Bee Localisation evaluation adapter.",
                409,
            )
        for dataset_item_id in benchmark_item_ids:
            item = self.store.dataset_items.get(dataset_item_id)
            if item is None:
                return DomainError(
                    "benchmark_item_missing",
                    "A protected benchmark Dataset Item is missing.",
                    409,
                )
            if item.source_evidence_type != "training_crop" or item.training_crop_id is None:
                return DomainError(
                    "unsupported_benchmark_item_type",
                    "Only Training Crop benchmark Dataset Items can be evaluated in this slice.",
                    409,
                )
            if item.permission_status != "workspace_data_use_agreement_accepted":
                return DomainError(
                    "benchmark_permission_not_valid",
                    "Benchmark evidence cannot be evaluated unless contribution permission is valid.",
                    409,
                )
            if not item.reviewed_ellipse_snapshots:
                return DomainError(
                    "benchmark_item_unreviewed",
                    "Every benchmark Dataset Item needs reviewed ellipse evidence.",
                    409,
                )
            if item.crop_width is None or item.crop_height is None:
                return DomainError(
                    "benchmark_geometry_missing",
                    "Every benchmark Dataset Item needs crop geometry.",
                    409,
                )
            photo = self.store.inspection_photos.get(item.inspection_photo_id)
            if photo is None or self.image_loader(photo.original_object_key) is None:
                return DomainError(
                    "benchmark_image_bytes_missing",
                    "Every benchmark Dataset Item needs available image bytes.",
                    409,
                )
        return None

    def _benchmark_warnings(
        self,
        training_dataset_item_ids: list[UUID],
        *,
        benchmark_item_ids: list[UUID],
    ) -> list[BenchmarkEvaluationWarningResponse]:
        warnings: list[BenchmarkEvaluationWarningResponse] = []
        training_items = [
            item
            for item_id in training_dataset_item_ids
            if (item := self.store.dataset_items.get(item_id)) is not None
        ]
        benchmark_items = [
            item
            for item_id in benchmark_item_ids
            if (item := self.store.dataset_items.get(item_id)) is not None
        ]
        training_photo_ids = {item.inspection_photo_id for item in training_items}
        benchmark_photo_ids = {item.inspection_photo_id for item in benchmark_items}
        if training_photo_ids & benchmark_photo_ids:
            warnings.append(
                _warning(
                    "BENCHMARK_SOURCE_IMAGE_LEAKAGE",
                    "high",
                    "At least one benchmark item shares a source image with training or validation evidence.",
                )
            )
        training_source_groups = {
            item.source_group_key for item in training_items if item.source_group_key is not None
        }
        benchmark_source_groups = {
            item.source_group_key for item in benchmark_items if item.source_group_key is not None
        }
        if training_source_groups & benchmark_source_groups:
            warnings.append(
                _warning(
                    "BENCHMARK_SOURCE_GROUP_LEAKAGE",
                    "high",
                    "At least one benchmark item shares a source group with training or validation evidence.",
                )
            )
        if len(benchmark_items) < 20:
            warnings.append(
                _warning(
                    "SMALL_BENCHMARK_SET",
                    "warning",
                    "Fewer than 20 benchmark items; metrics are workflow evidence only.",
                )
            )
        if not any(
            str(ellipse.review_method) == "human_from_scratch"
            or ellipse.source == "human_from_scratch"
            for item in benchmark_items
            for ellipse in item.reviewed_ellipse_snapshots
        ):
            warnings.append(
                _warning(
                    "NO_HUMAN_FROM_SCRATCH_BENCHMARK_ITEMS",
                    "warning",
                    "No human-from-scratch benchmark evidence exists for automation-bias comparison.",
                )
            )
        source_groups = Counter(item.source_group_key or "unknown" for item in benchmark_items)
        if len(source_groups) <= 1 and len(benchmark_items) > 1:
            warnings.append(
                _warning(
                    "BENCHMARK_EASY_ONLY",
                    "warning",
                    "Benchmark items lack source-group diversity.",
                )
            )
        return warnings

    def _candidate_context(self, *, workspace_id: UUID, model_candidate_id: UUID):
        candidate = self.store.get_model_candidate(workspace_id, model_candidate_id)
        if candidate is None:
            raise DomainError("model_candidate_not_found", "Model Candidate not found.", 404)
        if candidate.status != "created" or candidate.model_purpose != "bee_detector":
            raise DomainError(
                "model_candidate_not_evaluable",
                "Only created Bee Detector Model Candidates can be evaluated.",
                409,
            )
        training_run = self.store.get_training_run(workspace_id, candidate.training_run_id)
        if training_run is None or training_run.status != "completed":
            raise DomainError(
                "model_candidate_training_run_not_completed",
                "The selected Model Candidate must come from a completed Training Run.",
                409,
            )
        dataset_version = self.store.get_dataset_version(workspace_id, training_run.dataset_version_id)
        if dataset_version is None:
            raise DomainError(
                "model_candidate_dataset_version_missing",
                "The selected Model Candidate's Dataset Version is missing.",
                409,
            )
        return candidate, training_run, dataset_version

    def _start_background_evaluation(self, evaluation: BenchmarkEvaluationResponse) -> None:
        thread = threading.Thread(
            target=self._run_evaluation_now,
            args=(evaluation,),
            daemon=True,
            name=f"hivesight-benchmark-evaluation-{evaluation.benchmark_evaluation_id}",
        )
        thread.start()

    def _heartbeat_while_active(
        self,
        workspace_id: UUID,
        benchmark_evaluation_id: UUID,
        log_path: Path,
        stop_event: threading.Event,
    ) -> None:
        while not stop_event.wait(self.heartbeat_interval_seconds):
            current = self.store.get_benchmark_evaluation(workspace_id, benchmark_evaluation_id)
            if current is None or current.status in TERMINAL_BENCHMARK_EVALUATION_STATUSES:
                return
            self.store.save_benchmark_evaluation(
                current.model_copy(
                    update={
                        "last_heartbeat_at": self.clock(),
                        "last_activity_message": "Benchmark Evaluation is still running.",
                        "latest_log_excerpt": self._latest_log_excerpt(log_path),
                    }
                )
            )

    def _with_runtime_state(
        self,
        evaluation: BenchmarkEvaluationResponse,
    ) -> BenchmarkEvaluationResponse:
        is_stale = False
        if (
            evaluation.status not in TERMINAL_BENCHMARK_EVALUATION_STATUSES
            and evaluation.last_heartbeat_at is not None
        ):
            is_stale = self.clock() - evaluation.last_heartbeat_at > timedelta(
                seconds=self.stale_after_seconds
            )
        return evaluation.model_copy(
            update={"is_stale": is_stale, "stale_after_seconds": self.stale_after_seconds}
        )

    def _write_raw_prediction_artifact(
        self,
        *,
        evaluation: BenchmarkEvaluationResponse,
        raw_predictions: list[dict[str, object]],
    ) -> UUID:
        path = self._evaluation_dir(evaluation) / "raw-predictions.json"
        path.write_text(
            json.dumps(
                {
                    "benchmark_evaluation_id": str(evaluation.benchmark_evaluation_id),
                    "model_candidate_id": str(evaluation.model_candidate_id),
                    "confidence_threshold": evaluation.confidence_threshold,
                    "match_strategy": MATCH_STRATEGY,
                    "predictions": raw_predictions,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return self._record_artifact(
            owner_type="benchmark_evaluation",
            owner_id=evaluation.benchmark_evaluation_id,
            artifact_type="benchmark_raw_predictions",
            path=path,
            content_type="application/json",
            required_or_diagnostic="diagnostic",
        ).artifact_id

    def _write_report_artifact(self, evaluation: BenchmarkEvaluationResponse) -> UUID:
        path = self._evaluation_dir(evaluation) / "benchmark-evaluation-report.md"
        path.write_text(
            "\n".join(
                [
                    f"# Benchmark Evaluation {evaluation.human_readable_id}",
                    "",
                    f"Model Candidate: {evaluation.model_candidate_human_readable_id}",
                    f"Adapter: {evaluation.evaluation_adapter_type}",
                    f"Training adapter: {evaluation.training_adapter_type}",
                    f"Database purpose: {evaluation.database_purpose}",
                    f"Benchmark scope: Training Crop benchmark only",
                    f"Confidence threshold: {evaluation.confidence_threshold:.2f}",
                    f"Match strategy: {evaluation.match_strategy}",
                    "",
                    "## Metrics",
                    json.dumps(evaluation.metrics_summary, indent=2, sort_keys=True),
                    "",
                    "## Warnings",
                    *[
                        f"- {warning.severity}: {warning.code} - {warning.message}"
                        for warning in evaluation.warnings
                    ],
                    "",
                    "## Per-Item Summary",
                    *[
                        (
                            f"- {item.human_readable_id}: ground truth {item.ground_truth_count}, "
                            f"predictions {item.prediction_count}, matched {item.matched_count}, "
                            f"false positives {item.false_positive_count}, false negatives {item.false_negative_count}"
                        )
                        for item in evaluation.item_results
                    ],
                    "",
                    "This report is internal model-governance evidence. It is not beekeeper-facing inspection output and does not evaluate Varroa detection.",
                ]
            ),
            encoding="utf-8",
        )
        return self._record_artifact(
            owner_type="benchmark_evaluation",
            owner_id=evaluation.benchmark_evaluation_id,
            artifact_type="benchmark_evaluation_report",
            path=path,
            content_type="text/markdown",
            required_or_diagnostic="required",
        ).artifact_id

    def _record_artifact(
        self,
        *,
        owner_type: str,
        owner_id: UUID,
        artifact_type: str,
        path: Path,
        content_type: str,
        required_or_diagnostic: str,
    ) -> ArtifactResponse:
        file_bytes = path.read_bytes()
        artifact = ArtifactResponse(
            artifact_id=self.store.id_factory(),
            owner_type=owner_type,
            owner_id=owner_id,
            artifact_type=artifact_type,
            relative_path=str(path.relative_to(self.artifact_root)),
            content_type=content_type,
            size_bytes=len(file_bytes),
            sha256=sha256(file_bytes).hexdigest(),
            required_or_diagnostic=required_or_diagnostic,
            availability_status="available",
            created_at=self.clock(),
        )
        self.store.save_artifact(artifact)
        return artifact

    def _evaluation_dir(self, evaluation: BenchmarkEvaluationResponse) -> Path:
        return (
            self.artifact_root
            / "benchmark-evaluations"
            / f"benchmark-evaluation-{evaluation.benchmark_evaluation_id}"
        )

    def _artifact_path(self, relative_path: str) -> Path:
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise DomainError("artifact_path_invalid", "Artifact path is invalid.", 500)
        return self.artifact_root / relative

    def _latest_log_excerpt(self, log_path: Path, max_chars: int = 2000) -> str | None:
        if not log_path.exists():
            return None
        content = log_path.read_text(encoding="utf-8", errors="replace")
        return content[-max_chars:] if content else None

    def _append_log(self, log_path: Path, message: str) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as file:
            file.write(f"{self.clock().isoformat()} {message}\n")

    def _require_curator(self, *, user: UserContext, workspace_id: UUID) -> None:
        self.store.require_workspace_access(user, workspace_id)
        self.store.require_data_use_agreement(workspace_id)
        self.store.require_dataset_curator_capability(user)

    def _human_id(self, prefix: str, existing: list[object]) -> str:
        return f"{prefix}-{len(existing) + 1:06d}"


def _matched_count(
    ground_truth: list[ReviewedEllipseSnapshot],
    predictions: list[BeeAnnotationSuggestion],
) -> int:
    unmatched_predictions = list(predictions)
    matched = 0
    for ellipse in ground_truth:
        match = next(
            (
                prediction
                for prediction in unmatched_predictions
                if _ellipse_centres_match(ellipse, prediction)
            ),
            None,
        )
        if match is not None:
            matched += 1
            unmatched_predictions.remove(match)
    return matched


def _ellipse_centres_match(
    ellipse: ReviewedEllipseSnapshot,
    prediction: BeeAnnotationSuggestion,
) -> bool:
    tolerance = max(float(ellipse.radius_x), float(ellipse.radius_y), 1.0)
    return (
        abs(float(ellipse.center_x) - prediction.center_x) <= tolerance
        and abs(float(ellipse.center_y) - prediction.center_y) <= tolerance
    )


def _metrics(
    item_results: list[BenchmarkEvaluationItemResultResponse],
    *,
    confidence_threshold: float,
) -> dict[str, object]:
    matched = sum(item.matched_count for item in item_results)
    predicted = sum(item.prediction_count for item in item_results)
    ground_truth = sum(item.ground_truth_count for item in item_results)
    precision = matched / predicted if predicted else None
    recall = matched / ground_truth if ground_truth else None
    return {
        "metric_scope": "training_crop_benchmark_only",
        "match_strategy": MATCH_STRATEGY,
        "confidence_threshold": confidence_threshold,
        "benchmark_item_count": len(item_results),
        "ground_truth_count": ground_truth,
        "prediction_count": predicted,
        "matched_count": matched,
        "false_positive_count": sum(item.false_positive_count for item in item_results),
        "false_negative_count": sum(item.false_negative_count for item in item_results),
        "precision": precision,
        "recall": recall,
    }


def _warning(
    code: str,
    severity: str,
    message: str,
) -> BenchmarkEvaluationWarningResponse:
    return BenchmarkEvaluationWarningResponse(
        code=code,
        severity=ModelTrainingWarningSeverity(severity),
        message=message,
    )


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _dataset_item_label(dataset_item_id: UUID) -> str:
    return f"Dataset Item {dataset_item_id.hex[:8]}"
