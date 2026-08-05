from __future__ import annotations

import json
import threading
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from uuid import UUID

from PIL import Image, ImageOps

from hive_sight_core_api.bee_detector_benchmark_evaluation_workflow import (
    TERMINAL_BENCHMARK_EVALUATION_STATUSES,
)
from hive_sight_core_api.bee_detector_training_workflow import (
    ORIENTATION_ELLIPSE_MARGIN_RATIO,
    ORIENTATION_IMAGE_SIZE,
)
from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    AnnotationType,
    ArtifactResponse,
    BenchmarkEvaluationCancelRequest,
    BenchmarkEvaluationItemResultResponse,
    BenchmarkEvaluationResponse,
    BenchmarkEvaluationStartRequest,
    BenchmarkEvaluationWarningResponse,
    DatasetItemResponse,
    DatasetRole,
    ModelTrainingWarningSeverity,
    OrientationBenchmarkReadinessResponse,
    ReviewedEllipseSnapshot,
)

ORIENTATION_BENCHMARK_SCOPE = "bee_orientation_head_direction_benchmark_only"
ORIENTATION_MATCH_STRATEGY = "head_up_down_classifier_v1"
ORIENTATION_CLASS_NAMES = ["head_up", "head_down"]


@dataclass(frozen=True)
class OrientationBenchmarkExample:
    expected_label: str
    image: Image.Image
    augmentation: str


@dataclass(frozen=True)
class OrientationBenchmarkPrediction:
    expected_label: str
    predicted_label: str
    confidence: float | None
    augmentation: str


class FakeBeeOrientationBenchmarkAdapter:
    adapter_type = "fake"

    def check_available(self) -> bool:
        return True

    def predict(
        self,
        *,
        examples: list[OrientationBenchmarkExample],
        model_artifact_path: Path,
    ) -> list[OrientationBenchmarkPrediction]:
        _ = model_artifact_path
        return [
            OrientationBenchmarkPrediction(
                expected_label=example.expected_label,
                predicted_label=example.expected_label,
                confidence=None,
                augmentation=example.augmentation,
            )
            for example in examples
        ]


class TorchvisionBeeOrientationBenchmarkAdapter:
    adapter_type = "torchvision_orientation_classifier"

    def __init__(self, device: str = "cpu") -> None:
        self.device = device

    def check_available(self) -> bool:
        try:
            import torch  # noqa: F401
            import torchvision  # noqa: F401
        except ImportError:
            return False
        return True

    def predict(
        self,
        *,
        examples: list[OrientationBenchmarkExample],
        model_artifact_path: Path,
    ) -> list[OrientationBenchmarkPrediction]:
        try:
            import torch
            from torchvision import models, transforms
        except ImportError as exc:
            raise DomainError(
                "real_orientation_benchmark_adapter_unavailable",
                "Run pnpm model:setup:bee before using the real Bee Orientation benchmark adapter.",
                409,
            ) from exc

        checkpoint = torch.load(model_artifact_path, map_location=self.device)
        architecture = checkpoint.get("architecture", "mobilenet_v3_small")
        if architecture != "mobilenet_v3_small":
            raise DomainError(
                "unsupported_orientation_model_architecture",
                "Only mobilenet_v3_small Bee Orientation candidates can be evaluated in this slice.",
                409,
            )
        model = models.mobilenet_v3_small(weights=None, num_classes=2)
        model.load_state_dict(checkpoint["state_dict"])
        device = torch.device(self.device)
        model.to(device)
        model.eval()
        transform = transforms.Compose(
            [
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )
        predictions: list[OrientationBenchmarkPrediction] = []
        with torch.no_grad():
            for example in examples:
                tensor = transform(example.image.convert("RGB")).unsqueeze(0).to(device)
                probabilities = torch.softmax(model(tensor), dim=1)[0].detach().cpu()
                predicted_index = int(probabilities.argmax().item())
                predictions.append(
                    OrientationBenchmarkPrediction(
                        expected_label=example.expected_label,
                        predicted_label=ORIENTATION_CLASS_NAMES[predicted_index],
                        confidence=float(probabilities[predicted_index].item()),
                        augmentation=example.augmentation,
                    )
                )
        return predictions


@dataclass(frozen=True)
class OrientationItemOutput:
    result: BenchmarkEvaluationItemResultResponse
    raw_prediction_row: dict[str, object]
    correct_count: int
    example_count: int
    confusion: dict[str, dict[str, int]]
    confidences: list[float]


class BeeOrientationBenchmarkEvaluationWorkflow:
    def __init__(
        self,
        *,
        store: InMemoryProductDataStore,
        image_loader: Callable[[str], bytes | None],
        artifact_root: Path,
        adapter: FakeBeeOrientationBenchmarkAdapter | TorchvisionBeeOrientationBenchmarkAdapter,
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
    ) -> OrientationBenchmarkReadinessResponse:
        self._require_curator(user=user, workspace_id=workspace_id)
        candidate, training_run, dataset_version = self._candidate_context(
            workspace_id=workspace_id,
            model_candidate_id=model_candidate_id,
        )
        counts = self._benchmark_counts(dataset_version.protected_benchmark_dataset_item_ids)
        active_job_id = None
        active_job_type = None
        if (active_training := self.store.active_training_run(workspace_id)) is not None:
            active_job_id = active_training.training_run_id
            active_job_type = "training_run"
        elif (active_evaluation := self.store.active_benchmark_evaluation(workspace_id)) is not None:
            active_job_id = active_evaluation.benchmark_evaluation_id
            active_job_type = "benchmark_evaluation"
        warnings = self._warnings(counts)
        blocker = self._blocking_evaluation_reason(
            candidate_adapter_type=candidate.adapter_type,
            eligible_benchmark_bee_count=counts["eligible"],
        )
        eligible_to_start = active_job_id is None and blocker is None
        return OrientationBenchmarkReadinessResponse(
            workspace_id=workspace_id,
            model_candidate_id=candidate.model_candidate_id,
            model_candidate_human_readable_id=candidate.human_readable_id,
            dataset_version_id=dataset_version.dataset_version_id,
            dataset_version_human_readable_id=dataset_version.human_readable_id,
            adapter_type=self.adapter.adapter_type,
            training_adapter_type=training_run.adapter_type,
            evaluation_adapter_type=self.adapter.adapter_type,
            database_purpose=self.database_purpose,
            benchmark_item_count=len(dataset_version.protected_benchmark_dataset_item_ids),
            eligible_benchmark_bee_count=counts["eligible"],
            excluded_unreliable_orientation_count=counts["orientation_unreliable"],
            excluded_partial_visible_bee_count=counts["partial_visible_bee"],
            eligible_to_start_evaluation=eligible_to_start,
            eligible_to_start_benchmark=eligible_to_start,
            active_model_job_id=active_job_id,
            active_model_job_type=active_job_type,
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
        counts = self._benchmark_counts(dataset_version.protected_benchmark_dataset_item_ids)
        blocker = self._blocking_evaluation_reason(
            candidate_adapter_type=candidate.adapter_type,
            eligible_benchmark_bee_count=counts["eligible"],
        )
        if blocker is not None:
            raise blocker
        warnings = self._warnings(counts)
        high_warning_codes = [
            warning.code
            for warning in warnings
            if warning.severity == ModelTrainingWarningSeverity.high
        ]
        if high_warning_codes and not request.acknowledge_high_severity_warnings:
            raise DomainError(
                "orientation_benchmark_warnings_require_acknowledgement",
                "Acknowledge high-severity Bee Orientation benchmark warnings before running evaluation.",
                409,
            )
        created_at = self.clock()
        evaluation = BenchmarkEvaluationResponse(
            benchmark_evaluation_id=self.store.id_factory(),
            workspace_id=request.workspace_id,
            human_readable_id=self._human_id(
                "HS-OB", self.store.list_benchmark_evaluations(request.workspace_id)
            ),
            model_candidate_id=candidate.model_candidate_id,
            model_candidate_human_readable_id=candidate.human_readable_id,
            training_run_id=training_run.training_run_id,
            dataset_version_id=dataset_version.dataset_version_id,
            model_purpose="bee_orientation",
            status="queued",
            phase="queued",
            adapter_type=self.adapter.adapter_type,
            training_adapter_type=training_run.adapter_type,
            evaluation_adapter_type=self.adapter.adapter_type,
            database_purpose=self.database_purpose,
            confidence_threshold=request.confidence_threshold,
            match_strategy=ORIENTATION_MATCH_STRATEGY,
            benchmark_scope=ORIENTATION_BENCHMARK_SCOPE,
            started_at=None,
            completed_at=None,
            last_heartbeat_at=created_at,
            last_activity_message="Bee Orientation Benchmark Evaluation queued.",
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

    def _run_evaluation_now(
        self,
        evaluation: BenchmarkEvaluationResponse,
    ) -> BenchmarkEvaluationResponse:
        run_dir = self._evaluation_dir(evaluation)
        run_dir.mkdir(parents=True, exist_ok=True)
        log_path = run_dir / "orientation-benchmark-evaluation.log"
        self._append_log(log_path, "Bee Orientation Benchmark Evaluation worker started.")
        running = evaluation.model_copy(
            update={
                "status": "running",
                "phase": "evaluating_items",
                "started_at": self.clock(),
                "last_heartbeat_at": self.clock(),
                "last_activity_message": "Evaluating protected Bee Orientation benchmark bees.",
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
            name=f"hivesight-orientation-benchmark-heartbeat-{running.benchmark_evaluation_id}",
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
                    "The Bee Orientation Model Candidate artifact is missing.",
                    404,
                )
            model_artifact_path = self._artifact_path(artifact.relative_path)
            item_results: list[BenchmarkEvaluationItemResultResponse] = []
            raw_predictions: list[dict[str, object]] = []
            correct_count = 0
            example_count = 0
            confusion = _empty_confusion()
            confidences: list[float] = []
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
                            "last_activity_message": "Bee Orientation Benchmark Evaluation cancelled between items.",
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
                )
                if output.result.ground_truth_count > 0:
                    item_results.append(output.result)
                    raw_predictions.append(output.raw_prediction_row)
                    correct_count += output.correct_count
                    example_count += output.example_count
                    _merge_confusion(confusion, output.confusion)
                    confidences.extend(output.confidences)
                progress = 5 + (index / max(len(benchmark_ids), 1)) * 80
                running = running.model_copy(
                    update={
                        "last_heartbeat_at": self.clock(),
                        "last_activity_message": f"Evaluated orientation benchmark item {index} of {len(benchmark_ids)}.",
                        "progress_percent": round(progress, 1),
                        "latest_log_excerpt": self._latest_log_excerpt(log_path),
                    }
                )
                self.store.save_benchmark_evaluation(running)
            metrics = self._metrics(
                item_results=item_results,
                correct_count=correct_count,
                example_count=example_count,
                confusion=confusion,
                confidences=confidences,
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
                    "last_activity_message": "Bee Orientation Benchmark Evaluation completed.",
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
                artifact_type="bee_orientation_benchmark_log",
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
            self.store.save_model_candidate(
                candidate.model_copy(update={"promotion_status": "benchmark_reported"})
            )
            heartbeat_stop.set()
            heartbeat_thread.join(timeout=1)
            return completed
        except DomainError as error:
            return self._fail_evaluation(
                running=running,
                log_path=log_path,
                heartbeat_stop=heartbeat_stop,
                heartbeat_thread=heartbeat_thread,
                failure_code=error.code,
                failure_message=error.message,
            )
        except Exception as error:
            return self._fail_evaluation(
                running=running,
                log_path=log_path,
                heartbeat_stop=heartbeat_stop,
                heartbeat_thread=heartbeat_thread,
                failure_code="bee_orientation_benchmark_evaluation_failed",
                failure_message=str(error),
            )

    def _evaluate_item(
        self,
        *,
        item: DatasetItemResponse,
        model_artifact_path: Path,
    ) -> OrientationItemOutput:
        eligible_ellipses = [
            ellipse
            for ellipse in item.reviewed_ellipse_snapshots
            if ellipse.annotation_type == AnnotationType.complete_visible_bee
            and str(ellipse.orientation_reliability) == "reliable"
        ]
        if not eligible_ellipses:
            return OrientationItemOutput(
                result=self._empty_item_result(item),
                raw_prediction_row={
                    "dataset_item_id": str(item.dataset_item_id),
                    "human_readable_id": _dataset_item_label(item.dataset_item_id),
                    "source_group_key": item.source_group_key,
                    "examples": [],
                    "exclusion_reason": "no_eligible_reliable_complete_visible_bees",
                },
                correct_count=0,
                example_count=0,
                confusion=_empty_confusion(),
                confidences=[],
            )
        if item.training_crop_id is None:
            raise DomainError(
                "unsupported_orientation_benchmark_item_type",
                "Only Training Crop benchmark Dataset Items can be evaluated for Bee Orientation.",
                409,
            )
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
        source_image = Image.open(BytesIO(image_bytes)).convert("RGB")
        raw_examples: list[dict[str, object]] = []
        correct_count = 0
        example_count = 0
        confusion = _empty_confusion()
        confidences: list[float] = []
        for ellipse in eligible_ellipses:
            head_up_image = _orientation_head_up_image(source_image, ellipse)
            examples = [
                OrientationBenchmarkExample(
                    expected_label="head_up",
                    image=head_up_image,
                    augmentation="none",
                ),
                OrientationBenchmarkExample(
                    expected_label="head_down",
                    image=head_up_image.rotate(180),
                    augmentation="rotate_180",
                ),
            ]
            predictions = self.adapter.predict(
                examples=examples,
                model_artifact_path=model_artifact_path,
            )
            example_rows = []
            for prediction in predictions:
                is_correct = prediction.expected_label == prediction.predicted_label
                correct_count += int(is_correct)
                example_count += 1
                confusion[prediction.expected_label][prediction.predicted_label] += 1
                if prediction.confidence is not None:
                    confidences.append(prediction.confidence)
                example_rows.append(
                    {
                        "annotation_id": str(ellipse.annotation_id),
                        "annotation_type": ellipse.annotation_type,
                        "orientation_reliability": ellipse.orientation_reliability,
                        "expected_label": prediction.expected_label,
                        "predicted_label": prediction.predicted_label,
                        "confidence": prediction.confidence,
                        "augmentation": prediction.augmentation,
                        "correct": is_correct,
                    }
                )
            raw_examples.extend(example_rows)
        hive_snapshot = item.provenance.hive_configuration if item.provenance else None
        return OrientationItemOutput(
            result=BenchmarkEvaluationItemResultResponse(
                dataset_item_id=item.dataset_item_id,
                human_readable_id=_dataset_item_label(item.dataset_item_id),
                source_group_key=item.source_group_key,
                hive_configuration_frame_standard_id=(
                    hive_snapshot.frame_standard_id if hive_snapshot else None
                ),
                curriculum_stage=item.curriculum_stage,
                ground_truth_count=example_count,
                prediction_count=example_count,
                matched_count=correct_count,
                false_positive_count=max(example_count - correct_count, 0),
                false_negative_count=max(example_count - correct_count, 0),
            ),
            raw_prediction_row={
                "dataset_item_id": str(item.dataset_item_id),
                "human_readable_id": _dataset_item_label(item.dataset_item_id),
                "source_group_key": item.source_group_key,
                "training_crop_id": str(item.training_crop_id),
                "inspection_photo_id": str(item.inspection_photo_id),
                "examples": raw_examples,
            },
            correct_count=correct_count,
            example_count=example_count,
            confusion=confusion,
            confidences=confidences,
        )

    def _candidate_context(self, *, workspace_id: UUID, model_candidate_id: UUID):
        candidate = self.store.get_model_candidate(workspace_id, model_candidate_id)
        if candidate is None:
            raise DomainError("model_candidate_not_found", "Model Candidate not found.", 404)
        if candidate.status != "created" or candidate.model_purpose != "bee_orientation":
            raise DomainError(
                "model_candidate_not_orientation_evaluable",
                "Only created Bee Orientation Model Candidates can be evaluated by the Bee Orientation benchmark.",
                409,
            )
        training_run = self.store.get_training_run(workspace_id, candidate.training_run_id)
        if training_run is None or training_run.status != "completed":
            raise DomainError(
                "model_candidate_training_run_not_completed",
                "The selected Bee Orientation Model Candidate must come from a completed Training Run.",
                409,
            )
        dataset_version = self.store.get_dataset_version(workspace_id, training_run.dataset_version_id)
        if dataset_version is None:
            raise DomainError(
                "model_candidate_dataset_version_missing",
                "The selected Bee Orientation Model Candidate's Dataset Version is missing.",
                409,
            )
        return candidate, training_run, dataset_version

    def _blocking_evaluation_reason(
        self,
        *,
        candidate_adapter_type: str,
        eligible_benchmark_bee_count: int,
    ) -> DomainError | None:
        if eligible_benchmark_bee_count == 0:
            return DomainError(
                "orientation_benchmark_bees_required",
                "Benchmark items exist, but none contain reliable complete visible bees eligible for Bee Orientation evaluation.",
                409,
            )
        if self.adapter.adapter_type != "fake" and candidate_adapter_type == "fake":
            return DomainError(
                "fake_candidate_real_orientation_evaluation_not_allowed",
                "A fake Bee Orientation Model Candidate cannot be evaluated with the real orientation benchmark adapter.",
                409,
            )
        if self.adapter.adapter_type != "fake" and self.database_purpose == "test":
            return DomainError(
                "real_adapter_refuses_test_database",
                "Real Bee Orientation benchmark evaluation must target the dev or QA database, not the resettable test database.",
                409,
            )
        if self.adapter.adapter_type != "fake" and not self.adapter.check_available():
            return DomainError(
                "real_orientation_benchmark_adapter_unavailable",
                "Run pnpm model:setup:bee before using the real Bee Orientation benchmark adapter.",
                409,
            )
        return None

    def _benchmark_counts(self, benchmark_item_ids: list[UUID]) -> Counter[str]:
        counts: Counter[str] = Counter()
        for dataset_item_id in benchmark_item_ids:
            item = self.store.dataset_items.get(dataset_item_id)
            if item is None:
                continue
            counts["benchmark_items"] += 1
            for ellipse in item.reviewed_ellipse_snapshots:
                if ellipse.annotation_type == AnnotationType.partial_visible_bee:
                    counts["partial_visible_bee"] += 1
                    continue
                if ellipse.annotation_type != AnnotationType.complete_visible_bee:
                    counts["unsupported_annotation_type"] += 1
                    continue
                if str(ellipse.orientation_reliability) != "reliable":
                    counts["orientation_unreliable"] += 1
                    continue
                counts["eligible"] += 1
        return counts

    def _warnings(self, counts: Counter[str]) -> list[BenchmarkEvaluationWarningResponse]:
        warnings: list[BenchmarkEvaluationWarningResponse] = []
        if counts["benchmark_items"] == 0:
            warnings.append(
                _warning(
                    "NO_ORIENTATION_BENCHMARK_ITEMS",
                    "high",
                    "At least one protected Benchmark Dataset Item is required for Bee Orientation evaluation.",
                )
            )
        if counts["eligible"] == 0:
            warnings.append(
                _warning(
                    "NO_ELIGIBLE_ORIENTATION_BENCHMARK_BEES",
                    "high",
                    "Benchmark items exist, but none contain reliable complete visible bees eligible for Bee Orientation evaluation.",
                )
            )
        if counts["eligible"] < 20:
            warnings.append(
                _warning(
                    "SMALL_ORIENTATION_BENCHMARK_SET",
                    "warning",
                    "Fewer than 20 reliable complete benchmark bees; metrics are early workflow evidence.",
                )
            )
        if counts["orientation_unreliable"] > 0:
            warnings.append(
                _warning(
                    "UNRELIABLE_ORIENTATION_EXCLUDED",
                    "warning",
                    "Bees marked with unreliable head orientation are excluded from the Bee Orientation benchmark.",
                )
            )
        if counts["partial_visible_bee"] > 0:
            warnings.append(
                _warning(
                    "PARTIAL_VISIBLE_BEES_DEFERRED",
                    "warning",
                    "Partial visible bees are excluded from the first Bee Orientation benchmark.",
                )
            )
        return warnings

    def _metrics(
        self,
        *,
        item_results: list[BenchmarkEvaluationItemResultResponse],
        correct_count: int,
        example_count: int,
        confusion: dict[str, dict[str, int]],
        confidences: list[float],
    ) -> dict[str, object]:
        return {
            "metric_scope": "bee_orientation_benchmark_only",
            "match_strategy": ORIENTATION_MATCH_STRATEGY,
            "benchmark_scope": ORIENTATION_BENCHMARK_SCOPE,
            "evaluated_bee_count": len(item_results),
            "evaluated_example_count": example_count,
            "correct_example_count": correct_count,
            "accuracy": correct_count / example_count if example_count else None,
            "confusion_matrix": confusion,
            "confidence_distribution": _confidence_distribution(confidences),
            "fake_adapter_workflow_evidence_only": self.adapter.adapter_type == "fake",
        }

    def _write_raw_prediction_artifact(
        self,
        *,
        evaluation: BenchmarkEvaluationResponse,
        raw_predictions: list[dict[str, object]],
    ) -> UUID:
        path = self._evaluation_dir(evaluation) / "raw-orientation-predictions.json"
        path.write_text(
            json.dumps(
                {
                    "benchmark_evaluation_id": str(evaluation.benchmark_evaluation_id),
                    "model_candidate_id": str(evaluation.model_candidate_id),
                    "model_purpose": "bee_orientation",
                    "benchmark_scope": ORIENTATION_BENCHMARK_SCOPE,
                    "adapter_type": evaluation.evaluation_adapter_type,
                    "predictions": raw_predictions,
                },
                indent=2,
                sort_keys=True,
                default=str,
            ),
            encoding="utf-8",
        )
        return self._record_artifact(
            owner_type="benchmark_evaluation",
            owner_id=evaluation.benchmark_evaluation_id,
            artifact_type="bee_orientation_benchmark_raw_predictions",
            path=path,
            content_type="application/json",
            required_or_diagnostic="diagnostic",
        ).artifact_id

    def _write_report_artifact(self, evaluation: BenchmarkEvaluationResponse) -> UUID:
        path = self._evaluation_dir(evaluation) / "bee-orientation-benchmark-report.md"
        fake_note = (
            "Fake-adapter results are workflow evidence only and must not be presented as real model quality."
            if evaluation.evaluation_adapter_type == "fake"
            else "Real-adapter results are benchmark evidence for this Bee Orientation candidate only."
        )
        path.write_text(
            "\n".join(
                [
                    f"# Bee Orientation Benchmark Evaluation {evaluation.human_readable_id}",
                    "",
                    f"Model Candidate: {evaluation.model_candidate_human_readable_id}",
                    f"Adapter: {evaluation.evaluation_adapter_type}",
                    f"Training adapter: {evaluation.training_adapter_type}",
                    f"Database purpose: {evaluation.database_purpose}",
                    f"Benchmark scope: {ORIENTATION_BENCHMARK_SCOPE}",
                    f"Match strategy: {ORIENTATION_MATCH_STRATEGY}",
                    "",
                    fake_note,
                    "",
                    "This report evaluates head-direction prediction only. It does not evaluate Bee Localisation quality, does not evaluate Varroa Detection quality, and does not make this candidate available for Varroa Assessment.",
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
                            f"- {item.human_readable_id}: examples {item.ground_truth_count}, "
                            f"correct {item.matched_count}, incorrect {item.false_negative_count}"
                        )
                        for item in evaluation.item_results
                    ],
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return self._record_artifact(
            owner_type="benchmark_evaluation",
            owner_id=evaluation.benchmark_evaluation_id,
            artifact_type="bee_orientation_benchmark_report",
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

    def _start_background_evaluation(self, evaluation: BenchmarkEvaluationResponse) -> None:
        thread = threading.Thread(
            target=self._run_evaluation_now,
            args=(evaluation,),
            daemon=True,
            name=f"hivesight-orientation-benchmark-evaluation-{evaluation.benchmark_evaluation_id}",
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
                        "last_activity_message": "Bee Orientation Benchmark Evaluation is still running.",
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

    def _fail_evaluation(
        self,
        *,
        running: BenchmarkEvaluationResponse,
        log_path: Path,
        heartbeat_stop: threading.Event,
        heartbeat_thread: threading.Thread,
        failure_code: str,
        failure_message: str,
    ) -> BenchmarkEvaluationResponse:
        heartbeat_stop.set()
        heartbeat_thread.join(timeout=1)
        failed = running.model_copy(
            update={
                "status": "failed",
                "phase": "failed",
                "completed_at": self.clock(),
                "last_heartbeat_at": self.clock(),
                "last_activity_message": "Bee Orientation Benchmark Evaluation failed.",
                "progress_percent": None,
                "latest_log_excerpt": self._latest_log_excerpt(log_path),
                "failure_code": failure_code,
                "failure_message": failure_message,
            }
        )
        self.store.save_benchmark_evaluation(failed)
        return failed

    def _evaluation_dir(self, evaluation: BenchmarkEvaluationResponse) -> Path:
        return (
            self.artifact_root
            / "orientation-benchmark-evaluations"
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

    def _empty_item_result(self, item: DatasetItemResponse) -> BenchmarkEvaluationItemResultResponse:
        hive_snapshot = item.provenance.hive_configuration if item.provenance else None
        return BenchmarkEvaluationItemResultResponse(
            dataset_item_id=item.dataset_item_id,
            human_readable_id=_dataset_item_label(item.dataset_item_id),
            source_group_key=item.source_group_key,
            hive_configuration_frame_standard_id=(
                hive_snapshot.frame_standard_id if hive_snapshot else None
            ),
            curriculum_stage=item.curriculum_stage,
            ground_truth_count=0,
            prediction_count=0,
            matched_count=0,
            false_positive_count=0,
            false_negative_count=0,
        )

    def _require_curator(self, *, user: UserContext, workspace_id: UUID) -> None:
        self.store.require_workspace_access(user, workspace_id)
        self.store.require_data_use_agreement(workspace_id)
        self.store.require_dataset_curator_capability(user)

    def _human_id(self, prefix: str, existing: list[object]) -> str:
        return f"{prefix}-{len(existing) + 1:06d}"


def _orientation_head_up_image(source_image: Image.Image, ellipse: ReviewedEllipseSnapshot) -> Image.Image:
    margin = 1 + ORIENTATION_ELLIPSE_MARGIN_RATIO
    half_side = max(ellipse.radius_x, ellipse.radius_y) * margin
    left = int(round(ellipse.center_x - half_side))
    top = int(round(ellipse.center_y - half_side))
    right = int(round(ellipse.center_x + half_side))
    bottom = int(round(ellipse.center_y + half_side))
    crop = source_image.crop((left, top, right, bottom))
    pad_left = max(0, -left)
    pad_top = max(0, -top)
    pad_right = max(0, right - source_image.width)
    pad_bottom = max(0, bottom - source_image.height)
    if any((pad_left, pad_top, pad_right, pad_bottom)):
        crop = ImageOps.expand(
            crop,
            border=(pad_left, pad_top, pad_right, pad_bottom),
            fill=(0, 0, 0),
        )
    crop = ImageOps.pad(crop, (ORIENTATION_IMAGE_SIZE, ORIENTATION_IMAGE_SIZE), color=(0, 0, 0))
    return crop.rotate(-90 - ellipse.rotation_degrees, resample=Image.Resampling.BICUBIC)


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


def _empty_confusion() -> dict[str, dict[str, int]]:
    return {
        "head_up": {"head_up": 0, "head_down": 0},
        "head_down": {"head_up": 0, "head_down": 0},
    }


def _merge_confusion(
    target: dict[str, dict[str, int]],
    source: dict[str, dict[str, int]],
) -> None:
    for expected_label, predictions in source.items():
        for predicted_label, count in predictions.items():
            target[expected_label][predicted_label] += count


def _confidence_distribution(confidences: list[float]) -> dict[str, float | int] | None:
    if not confidences:
        return None
    return {
        "count": len(confidences),
        "minimum": min(confidences),
        "maximum": max(confidences),
        "mean": sum(confidences) / len(confidences),
    }


def _dataset_item_label(dataset_item_id: UUID) -> str:
    return f"Dataset Item {dataset_item_id.hex[:8]}"
