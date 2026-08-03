from __future__ import annotations

import json
import logging
import platform
import shutil
import subprocess
import sys
import threading
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Protocol
from uuid import UUID

from hive_sight_core_api.dev_store import (
    DomainError,
    InMemoryProductDataStore,
    UserContext,
    _dataset_yaml_text,
    _ellipse_to_crop_normalized_obb_points,
    _generated_file_entry,
    _physical_split_dir,
    _render_training_crop_png,
    _yolo_class_id,
)
from hive_sight_core_api.models import (
    AnnotationType,
    ArtifactResponse,
    DatasetRole,
    DatasetVersionResponse,
    ModelCandidateResponse,
    ModelTrainingReadinessResponse,
    ModelTrainingWarningResponse,
    ModelTrainingWarningSeverity,
    TrainingRunAbandonRequest,
    TrainingRunCancelRequest,
    TrainingRunDeleteResponse,
    TrainingRunDeleteRequest,
    TrainingRunResponse,
    TrainingRunStartRequest,
    YoloObbExcludedItem,
    YoloObbLabelEntry,
)

CLASS_MAP = {"0": "complete_visible_bee", "1": "partial_visible_bee"}
EXPORT_FORMAT = "yolo_obb_v1"
CONVERSION_VERSION = "ellipse_to_yolo_obb_v1"
LOGGER = logging.getLogger(__name__)
TERMINAL_TRAINING_RUN_STATUSES = {"completed", "failed", "cancelled", "abandoned"}


class BeeDetectorTrainingAdapter(Protocol):
    adapter_type: str

    def check_available(self) -> bool:
        ...

    def run_training(
        self,
        *,
        training_run: TrainingRunResponse,
        run_dir: Path,
        dataset_package_dir: Path,
    ) -> TrainingAdapterResult:
        ...


@dataclass(frozen=True)
class TrainingAdapterResult:
    metrics: dict[str, object]
    model_artifact_path: Path
    log_path: Path
    base_weights_source: str


class FakeBeeDetectorTrainingAdapter:
    adapter_type = "fake"

    def check_available(self) -> bool:
        return True

    def run_training(
        self,
        *,
        training_run: TrainingRunResponse,
        run_dir: Path,
        dataset_package_dir: Path,
    ) -> TrainingAdapterResult:
        _ = dataset_package_dir
        weights_path = run_dir / "weights" / "best.pt"
        weights_path.parent.mkdir(parents=True, exist_ok=True)
        weights_path.write_text(
            f"fake HiveSight Bee Detector weights for {training_run.human_readable_id}\n",
            encoding="utf-8",
        )
        log_path = run_dir / "training.log"
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(
                "Fake adapter completed deterministic Bee Detector smoke training.\n"
            )
        return TrainingAdapterResult(
            metrics={
                "precision": 0.5,
                "recall": 0.5,
                "map50": 0.5,
                "metric_scope": "fake_adapter_smoke_metrics",
            },
            model_artifact_path=weights_path,
            log_path=log_path,
            base_weights_source="fake_generated",
        )


class UltralyticsYoloObbTrainingAdapter:
    adapter_type = "ultralytics_yolo_obb"

    def __init__(self, base_weights: str = "yolo11n-obb.pt", device: str = "cpu") -> None:
        self.base_weights = base_weights
        self.device = device

    def check_available(self) -> bool:
        try:
            import ultralytics  # noqa: F401
        except ImportError:
            return False
        return True

    def run_training(
        self,
        *,
        training_run: TrainingRunResponse,
        run_dir: Path,
        dataset_package_dir: Path,
    ) -> TrainingAdapterResult:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise DomainError(
                "real_adapter_unavailable",
                "Run pnpm model:setup:yolo before using the real YOLO training adapter.",
                409,
            ) from exc

        model = YOLO(self.base_weights)
        result_dir = run_dir / "ultralytics"
        model.train(
            data=str(dataset_package_dir / "data.yaml"),
            epochs=int(training_run.training_settings["epochs"]),
            imgsz=int(training_run.training_settings["image_size"]),
            batch=int(training_run.training_settings["batch_size"]),
            seed=training_run.random_seed,
            device=self.device,
            project=str(result_dir),
            name="train",
            exist_ok=True,
            task="obb",
        )
        weights_path = result_dir / "train" / "weights" / "best.pt"
        if not weights_path.exists():
            raise DomainError(
                "model_weights_missing",
                "The real YOLO adapter finished without producing usable model weights.",
                500,
            )
        log_path = run_dir / "training.log"
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(
                "Ultralytics YOLO OBB training completed. See ultralytics/train for raw outputs.\n"
            )
        return TrainingAdapterResult(
            metrics={"metric_scope": "ultralytics_training_smoke_metrics"},
            model_artifact_path=weights_path,
            log_path=log_path,
            base_weights_source="local_cache_or_downloaded",
        )


class BeeDetectorTrainingWorkflow:
    def __init__(
        self,
        *,
        store: InMemoryProductDataStore,
        image_loader: Callable[[str], bytes | None],
        artifact_root: Path,
        adapter: BeeDetectorTrainingAdapter,
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

    def readiness(self, user: UserContext, workspace_id: UUID) -> ModelTrainingReadinessResponse:
        self._require_curator(user=user, workspace_id=workspace_id)
        real_adapter_available = (
            self.adapter.check_available() if self.adapter.adapter_type != "fake" else False
        )
        counts = Counter(
            item.dataset_role
            for item in self.store.dataset_items.values()
            if item.workspace_id == workspace_id
        )
        active = self.store.active_training_run(workspace_id)
        warnings = self._readiness_warnings(
            training_count=counts[DatasetRole.training],
            validation_count=counts[DatasetRole.validation],
            benchmark_count=counts[DatasetRole.benchmark],
        )
        return ModelTrainingReadinessResponse(
            workspace_id=workspace_id,
            persistence_backend=self.persistence_backend,
            database_purpose=self.database_purpose,
            adapter_type=self.adapter.adapter_type,
            real_adapter_available=real_adapter_available,
            active_training_run_id=active.training_run_id if active else None,
            training_item_count=counts[DatasetRole.training],
            validation_item_count=counts[DatasetRole.validation],
            benchmark_item_count=counts[DatasetRole.benchmark],
            eligible_to_create_dataset_version=(
                counts[DatasetRole.training] >= 1 and counts[DatasetRole.validation] >= 1
            ),
            eligible_to_start_training=active is None
            and (self.adapter.adapter_type == "fake" or real_adapter_available),
            warnings=warnings,
        )

    def create_dataset_version(
        self,
        *,
        user: UserContext,
        workspace_id: UUID,
        purpose: str,
    ) -> DatasetVersionResponse:
        self._require_curator(user=user, workspace_id=workspace_id)
        dataset_version_id = self.store.id_factory()
        created_at = self.clock()
        included_ids: list[UUID] = []
        training_ids: list[UUID] = []
        validation_ids: list[UUID] = []
        benchmark_ids: list[UUID] = []
        excluded_items: list[YoloObbExcludedItem] = []
        class_counts: Counter[str] = Counter()
        source_counts: Counter[str] = Counter()
        review_counts: Counter[str] = Counter()
        source_group_counts: Counter[str] = Counter()
        hive_counts: Counter[str] = Counter()
        curriculum_counts: Counter[str] = Counter()
        quality_counts: Counter[str] = Counter()
        label_entries: list[YoloObbLabelEntry] = []

        items = sorted(
            [
                item
                for item in self.store.dataset_items.values()
                if item.workspace_id == workspace_id
            ],
            key=lambda item: str(item.dataset_item_id),
        )
        for item in items:
            quality_counts[str(item.image_quality_status)] += 1
            if item.dataset_role == DatasetRole.benchmark:
                benchmark_ids.append(item.dataset_item_id)
                continue
            if item.dataset_role == DatasetRole.excluded:
                excluded_items.append(_excluded_item(item, str(item.exclusion_reason or "excluded")))
                continue
            reason = self._eligible_training_item_exclusion_reason(item)
            if reason is not None:
                excluded_items.append(_excluded_item(item, reason))
                continue
            included_ids.append(item.dataset_item_id)
            if item.dataset_role == DatasetRole.training:
                training_ids.append(item.dataset_item_id)
            elif item.dataset_role == DatasetRole.validation:
                validation_ids.append(item.dataset_item_id)
            source_group_counts[item.source_group_key or "unknown"] += 1
            curriculum_counts[item.curriculum_stage or "unknown"] += 1
            hive_snapshot = item.provenance.hive_configuration if item.provenance else None
            hive_counts[
                hive_snapshot.frame_standard_id if hive_snapshot is not None else "unknown"
            ] += 1
            for ellipse in item.reviewed_ellipse_snapshots:
                class_counts[str(ellipse.annotation_type)] += 1
                source_counts[ellipse.source] += 1
                review_counts[str(ellipse.review_method or _review_method_for_source(ellipse.source))] += 1
                points = _ellipse_to_crop_normalized_obb_points(item, ellipse)
                if any(point < 0 or point > 1 for point in points):
                    excluded_items.append(_excluded_item(item, "invalid_label_geometry"))
                    break
                label_entries.append(
                    YoloObbLabelEntry(
                        dataset_item_id=item.dataset_item_id,
                        training_crop_id=item.training_crop_id,
                        annotation_id=ellipse.annotation_id,
                        split=item.dataset_role,
                        class_id=_yolo_class_id(ellipse.annotation_type),
                        class_name=ellipse.annotation_type,
                        label=" ".join(
                            [
                                str(_yolo_class_id(ellipse.annotation_type)),
                                *[f"{point:.6f}" for point in points],
                            ]
                        ),
                        points=points,
                    )
                )

        if not training_ids or not validation_ids:
            raise DomainError(
                "training_and_validation_required",
                "Create at least one training and one validation Dataset Item before creating a Dataset Version.",
                409,
            )

        warnings = self._dataset_warnings(
            training_count=len(training_ids),
            validation_count=len(validation_ids),
            benchmark_count=len(benchmark_ids),
            class_counts=class_counts,
            review_counts=review_counts,
            source_group_counts=source_group_counts,
        )
        manifest_payload = {
            "workspace_id": str(workspace_id),
            "purpose": purpose,
            "model_purpose": "bee_detector",
            "export_format": EXPORT_FORMAT,
            "included_dataset_item_ids": [str(item_id) for item_id in included_ids],
            "protected_benchmark_dataset_item_ids": [str(item_id) for item_id in benchmark_ids],
            "excluded_dataset_items": [item.model_dump(mode="json") for item in excluded_items],
            "class_map": CLASS_MAP,
            "conversion_version": CONVERSION_VERSION,
        }
        manifest_hash = sha256(
            json.dumps(manifest_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()
        dataset_version = DatasetVersionResponse(
            dataset_version_id=dataset_version_id,
            workspace_id=workspace_id,
            human_readable_id=self._human_id("HS-DV", self.store.list_dataset_versions(workspace_id)),
            purpose=purpose,
            model_purpose="bee_detector",
            status="active",
            export_format=EXPORT_FORMAT,
            selection_criteria={
                "status": "active",
                "source_evidence_type": "training_crop",
                "required_review": "reviewed_ellipses",
                "roles": ["training", "validation", "benchmark", "excluded"],
            },
            manifest_hash=manifest_hash,
            included_dataset_item_ids=included_ids,
            training_dataset_item_ids=training_ids,
            validation_dataset_item_ids=validation_ids,
            protected_benchmark_dataset_item_ids=benchmark_ids,
            excluded_dataset_items=excluded_items,
            training_item_count=len(training_ids),
            validation_item_count=len(validation_ids),
            benchmark_item_count=len(benchmark_ids),
            excluded_item_count=len(excluded_items),
            annotation_class_counts=dict(class_counts),
            annotation_source_counts=dict(source_counts),
            review_method_counts=dict(review_counts),
            source_group_distribution=dict(source_group_counts),
            hive_configuration_distribution=dict(hive_counts),
            curriculum_stage_distribution=dict(curriculum_counts),
            image_quality_distribution=dict(quality_counts),
            warnings=warnings,
            preview_artifact_ids=[],
            report_artifact_id=None,
            created_by_user_id=user.user_id,
            created_at=created_at,
        )
        self.store.save_dataset_version(dataset_version)
        package_dir = self._write_dataset_package(
            dataset_version=dataset_version,
            label_entries=label_entries,
            manifest_payload=manifest_payload,
        )
        preview_ids = self._write_preview_artifacts(
            owner_type="dataset_version",
            owner_id=dataset_version_id,
            package_dir=package_dir,
            created_at=created_at,
        )
        report_id = self._write_dataset_report(dataset_version, created_at)
        dataset_version = dataset_version.model_copy(
            update={"preview_artifact_ids": preview_ids, "report_artifact_id": report_id}
        )
        self.store.save_dataset_version(dataset_version)
        return dataset_version

    def list_dataset_versions(
        self,
        *,
        user: UserContext,
        workspace_id: UUID,
    ) -> list[DatasetVersionResponse]:
        self._require_curator(user=user, workspace_id=workspace_id)
        return self.store.list_dataset_versions(workspace_id)

    def get_dataset_version(
        self,
        *,
        user: UserContext,
        workspace_id: UUID,
        dataset_version_id: UUID,
    ) -> DatasetVersionResponse:
        self._require_curator(user=user, workspace_id=workspace_id)
        dataset_version = self.store.get_dataset_version(workspace_id, dataset_version_id)
        if dataset_version is None:
            raise DomainError("dataset_version_not_found", "Dataset Version not found.", 404)
        return dataset_version

    def start_training_run(
        self,
        *,
        user: UserContext,
        request: TrainingRunStartRequest,
    ) -> TrainingRunResponse:
        self._require_curator(user=user, workspace_id=request.workspace_id)
        if self.adapter.adapter_type != "fake" and self.database_purpose == "test":
            raise DomainError(
                "real_adapter_refuses_test_database",
                "Real YOLO training must target the dev or QA database, not the resettable test database.",
                409,
            )
        if self.adapter.adapter_type != "fake" and not self.adapter.check_available():
            raise DomainError(
                "real_adapter_unavailable",
                "Run pnpm model:setup:yolo before using the real YOLO training adapter.",
                409,
            )
        active_run = self.store.active_training_run(request.workspace_id)
        if active_run is not None:
            raise DomainError(
                "training_run_already_active",
                "Another Bee Detector Training Run is already queued or running.",
                409,
            )
        if self.store.active_benchmark_evaluation(request.workspace_id) is not None:
            raise DomainError(
                "model_job_already_active",
                "Another model job is already active in this local environment.",
                409,
            )
        dataset_version = self.get_dataset_version(
            user=user,
            workspace_id=request.workspace_id,
            dataset_version_id=request.dataset_version_id,
        )
        high_warnings = [
            warning.code
            for warning in dataset_version.warnings
            if warning.severity == ModelTrainingWarningSeverity.high
        ]
        if high_warnings and not request.acknowledge_high_severity_warnings:
            raise DomainError(
                "high_severity_warnings_require_acknowledgement",
                "Acknowledge high-severity Dataset Version warnings before starting training.",
                409,
            )
        created_at = self.clock()
        training_run_id = self.store.id_factory()
        run_dir = self.artifact_root / "training-runs" / f"training-run-{training_run_id}"
        training_run = TrainingRunResponse(
            training_run_id=training_run_id,
            workspace_id=request.workspace_id,
            human_readable_id=self._human_id("HS-TR", self.store.list_training_runs(request.workspace_id)),
            dataset_version_id=dataset_version.dataset_version_id,
            model_purpose="bee_detector",
            model_family="yolo_obb",
            model_size=request.model_size,
            base_weights="yolo11n-obb.pt",
            base_weights_source="pending",
            status="queued",
            phase="queued",
            adapter_type=self.adapter.adapter_type,
            database_purpose=self.database_purpose,
            training_settings={
                "model_size": request.model_size,
                "epochs": request.epochs,
                "image_size": request.image_size,
                "batch_size": request.batch_size,
            },
            random_seed=request.random_seed,
            git_commit_sha=_git_value(["git", "rev-parse", "HEAD"]),
            git_dirty_status=_git_dirty_status(),
            environment_summary={
                "python_version": sys.version.split()[0],
                "platform": platform.platform(),
                "persistence_backend": self.persistence_backend,
            },
            warning_acknowledgement={
                "acknowledged": bool(high_warnings),
                "warning_codes": high_warnings,
                "acknowledged_by_user_id": str(user.user_id) if high_warnings else None,
                "acknowledged_at": created_at.isoformat() if high_warnings else None,
            }
            if high_warnings
            else None,
            started_at=None,
            completed_at=None,
            last_heartbeat_at=created_at,
            last_activity_message="Training Run queued.",
            progress_percent=0,
            current_epoch=None,
            total_epochs=request.epochs,
            latest_log_excerpt=None,
            failure_code=None,
            failure_message=None,
            artifact_ids=[],
            metrics_summary={},
            report_artifact_id=None,
            model_candidate_id=None,
            created_by_user_id=user.user_id,
            created_at=created_at,
            purpose_notes=request.purpose_notes,
        )
        self.store.save_training_run(training_run)
        self._start_background_training(training_run, dataset_version, run_dir)
        LOGGER.info(
            "bee_detector_training_run_queued",
            extra={
                "workspace_id": str(training_run.workspace_id),
                "training_run_id": str(training_run.training_run_id),
                "dataset_version_id": str(training_run.dataset_version_id),
                "adapter_type": training_run.adapter_type,
            },
        )
        return self._with_runtime_state(training_run)

    def list_training_runs(
        self,
        *,
        user: UserContext,
        workspace_id: UUID,
    ) -> list[TrainingRunResponse]:
        self._require_curator(user=user, workspace_id=workspace_id)
        return [
            self._with_runtime_state(training_run)
            for training_run in self.store.list_training_runs(workspace_id)
        ]

    def get_training_run(
        self,
        *,
        user: UserContext,
        workspace_id: UUID,
        training_run_id: UUID,
    ) -> TrainingRunResponse:
        self._require_curator(user=user, workspace_id=workspace_id)
        training_run = self.store.get_training_run(workspace_id, training_run_id)
        if training_run is None:
            raise DomainError("training_run_not_found", "Training Run not found.", 404)
        return self._with_runtime_state(training_run)

    def cancel_training_run(
        self,
        *,
        user: UserContext,
        training_run_id: UUID,
        request: TrainingRunCancelRequest,
    ) -> TrainingRunResponse:
        self._require_curator(user=user, workspace_id=request.workspace_id)
        training_run = self._require_training_run(request.workspace_id, training_run_id)
        if training_run.status in TERMINAL_TRAINING_RUN_STATUSES:
            raise DomainError(
                "training_run_already_terminal",
                "Only queued or running Training Runs can be cancelled.",
                409,
            )
        cancelled = training_run.model_copy(
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
        self.store.save_training_run(cancelled)
        LOGGER.info(
            "bee_detector_training_run_cancellation_requested",
            extra={
                "workspace_id": str(cancelled.workspace_id),
                "training_run_id": str(cancelled.training_run_id),
            },
        )
        return self._with_runtime_state(cancelled)

    def abandon_training_run(
        self,
        *,
        user: UserContext,
        training_run_id: UUID,
        request: TrainingRunAbandonRequest,
    ) -> TrainingRunResponse:
        self._require_curator(user=user, workspace_id=request.workspace_id)
        training_run = self._require_training_run(request.workspace_id, training_run_id)
        if training_run.status in TERMINAL_TRAINING_RUN_STATUSES:
            raise DomainError(
                "training_run_already_terminal",
                "Only active Training Runs can be abandoned.",
                409,
            )
        runtime_state = self._with_runtime_state(training_run)
        if not runtime_state.is_stale and not request.force:
            raise DomainError(
                "training_run_not_stale",
                "Only stale Training Runs can be abandoned without force.",
                409,
            )
        abandoned = training_run.model_copy(
            update={
                "status": "abandoned",
                "phase": "abandoned",
                "completed_at": self.clock(),
                "last_heartbeat_at": self.clock(),
                "last_activity_message": "Training Run abandoned by Dataset Curator.",
                "abandoned_at": self.clock(),
                "abandoned_by_user_id": user.user_id,
                "abandon_reason": request.reason.strip(),
                "is_stale": False,
                "stale_after_seconds": self.stale_after_seconds,
            }
        )
        self.store.save_training_run(abandoned)
        LOGGER.info(
            "bee_detector_training_run_abandoned",
            extra={
                "workspace_id": str(abandoned.workspace_id),
                "training_run_id": str(abandoned.training_run_id),
            },
        )
        return abandoned

    def delete_training_run(
        self,
        *,
        user: UserContext,
        training_run_id: UUID,
        request: TrainingRunDeleteRequest,
    ) -> TrainingRunDeleteResponse:
        self._require_curator(user=user, workspace_id=request.workspace_id)
        training_run = self._require_training_run(request.workspace_id, training_run_id)
        if not request.confirm_no_candidate_or_required_artifacts:
            raise DomainError(
                "training_run_delete_requires_confirmation",
                "Confirm that the Training Run has no Model Candidate or required artifacts before deleting it.",
                409,
            )
        if training_run.model_candidate_id is not None or training_run.artifact_ids:
            raise DomainError(
                "training_run_has_governance_evidence",
                "Training Runs with Model Candidates or artifacts cannot be deleted.",
                409,
            )
        if training_run.status not in {"queued", "running", "cancelling", "abandoned", "cancelled"}:
            raise DomainError(
                "training_run_delete_not_allowed",
                "Only active, cancelled, or abandoned Training Runs without evidence can be deleted.",
                409,
            )
        self.store.delete_training_run(training_run.training_run_id)
        LOGGER.info(
            "bee_detector_training_run_deleted",
            extra={
                "workspace_id": str(training_run.workspace_id),
                "training_run_id": str(training_run.training_run_id),
            },
        )
        return TrainingRunDeleteResponse(
            training_run_id=training_run.training_run_id,
            deleted=True,
            message="Training Run deleted.",
        )

    def list_model_candidates(
        self,
        *,
        user: UserContext,
        workspace_id: UUID,
    ) -> list[ModelCandidateResponse]:
        self._require_curator(user=user, workspace_id=workspace_id)
        return self.store.list_model_candidates(workspace_id)

    def get_model_candidate(
        self,
        *,
        user: UserContext,
        workspace_id: UUID,
        model_candidate_id: UUID,
    ) -> ModelCandidateResponse:
        self._require_curator(user=user, workspace_id=workspace_id)
        candidate = self.store.get_model_candidate(workspace_id, model_candidate_id)
        if candidate is None:
            raise DomainError("model_candidate_not_found", "Model Candidate not found.", 404)
        return candidate

    def get_artifact(
        self,
        *,
        user: UserContext,
        workspace_id: UUID,
        artifact_id: UUID,
    ) -> tuple[ArtifactResponse, bytes]:
        self._require_curator(user=user, workspace_id=workspace_id)
        artifact = self.store.get_artifact(artifact_id)
        if artifact is None:
            raise DomainError("artifact_not_found", "Artifact not found.", 404)
        owner = self._artifact_owner_workspace(artifact)
        if owner != workspace_id:
            raise DomainError("artifact_not_found", "Artifact not found.", 404)
        artifact_path = self._artifact_path(artifact)
        if not artifact_path.exists() or not artifact_path.is_file():
            raise DomainError("artifact_missing", "The recorded artifact file is missing.", 404)
        return artifact, artifact_path.read_bytes()

    def _run_training_now(
        self,
        training_run: TrainingRunResponse,
        dataset_version: DatasetVersionResponse,
        run_dir: Path,
    ) -> TrainingRunResponse:
        run_dir.mkdir(parents=True, exist_ok=True)
        log_path = run_dir / "training.log"
        self._append_training_log(log_path, "Training Run worker started.")
        running = training_run.model_copy(
            update={
                "status": "running",
                "phase": "exporting_dataset",
                "started_at": self.clock(),
                "last_heartbeat_at": self.clock(),
                "last_activity_message": "Preparing YOLO OBB dataset package.",
                "progress_percent": 5,
                "latest_log_excerpt": self._latest_log_excerpt(log_path),
            }
        )
        self.store.save_training_run(running)
        heartbeat_stop = threading.Event()
        try:
            dataset_package_dir = self._dataset_package_dir(dataset_version)
            running = self._mark_training_run_phase(
                running,
                phase="training",
                message="Training adapter is running.",
                progress_percent=10,
                log_path=log_path,
            )
            heartbeat_thread = threading.Thread(
                target=self._heartbeat_while_active,
                args=(running.workspace_id, running.training_run_id, log_path, heartbeat_stop),
                daemon=True,
                name=f"hivesight-training-heartbeat-{running.training_run_id}",
            )
            heartbeat_thread.start()
            adapter_result = self.adapter.run_training(
                training_run=running,
                run_dir=run_dir,
                dataset_package_dir=dataset_package_dir,
            )
            heartbeat_stop.set()
            heartbeat_thread.join(timeout=1)
            current_run = self.store.get_training_run(running.workspace_id, running.training_run_id)
            if current_run is None:
                return running
            if current_run.status == "cancelling":
                cancelled = current_run.model_copy(
                    update={
                        "status": "cancelled",
                        "phase": "cancelled",
                        "completed_at": self.clock(),
                        "last_heartbeat_at": self.clock(),
                        "last_activity_message": "Training stopped after cancellation request.",
                        "progress_percent": None,
                        "latest_log_excerpt": self._latest_log_excerpt(log_path),
                    }
                )
                self.store.save_training_run(cancelled)
                return cancelled
            if current_run.status in TERMINAL_TRAINING_RUN_STATUSES:
                return current_run
            running = self._mark_training_run_phase(
                current_run,
                phase="recording_artifacts",
                message="Recording model artifacts.",
                progress_percent=90,
                log_path=adapter_result.log_path,
            )
            if not adapter_result.model_artifact_path.exists():
                raise DomainError(
                    "model_weights_missing",
                    "Training completed without producing usable model weights.",
                    500,
                )
            model_artifact = self._record_artifact(
                owner_type="training_run",
                owner_id=running.training_run_id,
                artifact_type="model_weights",
                path=adapter_result.model_artifact_path,
                content_type="application/octet-stream",
                required_or_diagnostic="required",
            )
            log_artifact = self._record_artifact(
                owner_type="training_run",
                owner_id=running.training_run_id,
                artifact_type="training_log",
                path=adapter_result.log_path,
                content_type="text/plain",
                required_or_diagnostic="diagnostic",
            )
            candidate = ModelCandidateResponse(
                model_candidate_id=self.store.id_factory(),
                workspace_id=running.workspace_id,
                human_readable_id=self._human_id(
                    "HS-MC", self.store.list_model_candidates(running.workspace_id)
                ),
                display_name=f"Bee detector baseline {running.human_readable_id}",
                training_run_id=running.training_run_id,
                model_purpose="bee_detector",
                model_family="yolo_obb",
                adapter_type=running.adapter_type,
                artifact_id=model_artifact.artifact_id,
                status="created",
                promotion_status="not_evaluated",
                not_user_facing_reason="baseline_training_only",
                created_at=self.clock(),
            )
            self.store.save_model_candidate(candidate)
            updated = running.model_copy(
                update={
                    "status": "completed",
                    "phase": "completed",
                    "completed_at": self.clock(),
                    "last_heartbeat_at": self.clock(),
                    "last_activity_message": "Training completed and Model Candidate created.",
                    "progress_percent": 100,
                    "latest_log_excerpt": self._latest_log_excerpt(adapter_result.log_path),
                    "base_weights_source": adapter_result.base_weights_source,
                    "artifact_ids": [model_artifact.artifact_id, log_artifact.artifact_id],
                    "metrics_summary": adapter_result.metrics,
                    "model_candidate_id": candidate.model_candidate_id,
                }
            )
            report_id = self._write_training_report(updated, dataset_version, candidate)
            artifact_manifest_id = self._write_artifact_manifest(updated, report_id)
            updated = updated.model_copy(
                update={
                    "artifact_ids": [*updated.artifact_ids, report_id, artifact_manifest_id],
                    "report_artifact_id": report_id,
                }
            )
            self.store.save_training_run(updated)
            return updated
        except DomainError as error:
            heartbeat_stop.set()
            failed = running.model_copy(
                update={
                    "status": "failed",
                    "phase": "failed",
                    "completed_at": self.clock(),
                    "last_heartbeat_at": self.clock(),
                    "last_activity_message": "Training failed.",
                    "progress_percent": None,
                    "latest_log_excerpt": self._latest_log_excerpt(log_path),
                    "failure_code": error.code,
                    "failure_message": error.message,
                }
            )
            self.store.save_training_run(failed)
            return failed
        except Exception as error:
            heartbeat_stop.set()
            failed = running.model_copy(
                update={
                    "status": "failed",
                    "phase": "failed",
                    "completed_at": self.clock(),
                    "last_heartbeat_at": self.clock(),
                    "last_activity_message": "Training failed unexpectedly.",
                    "progress_percent": None,
                    "latest_log_excerpt": self._latest_log_excerpt(log_path),
                    "failure_code": "training_run_failed",
                    "failure_message": str(error),
                }
            )
            self.store.save_training_run(failed)
            LOGGER.exception(
                "bee_detector_training_run_failed",
                extra={
                    "workspace_id": str(failed.workspace_id),
                    "training_run_id": str(failed.training_run_id),
                },
            )
            return failed

    def _start_background_training(
        self,
        training_run: TrainingRunResponse,
        dataset_version: DatasetVersionResponse,
        run_dir: Path,
    ) -> None:
        thread = threading.Thread(
            target=self._run_training_now,
            args=(training_run, dataset_version, run_dir),
            daemon=True,
            name=f"hivesight-training-run-{training_run.training_run_id}",
        )
        thread.start()

    def _heartbeat_while_active(
        self,
        workspace_id: UUID,
        training_run_id: UUID,
        log_path: Path,
        stop_event: threading.Event,
    ) -> None:
        while not stop_event.wait(self.heartbeat_interval_seconds):
            current = self.store.get_training_run(workspace_id, training_run_id)
            if current is None or current.status in TERMINAL_TRAINING_RUN_STATUSES:
                return
            self.store.save_training_run(
                current.model_copy(
                    update={
                        "last_heartbeat_at": self.clock(),
                        "last_activity_message": "Training adapter is still running.",
                        "latest_log_excerpt": self._latest_log_excerpt(log_path),
                    }
                )
            )

    def _mark_training_run_phase(
        self,
        training_run: TrainingRunResponse,
        *,
        phase: str,
        message: str,
        progress_percent: float | None,
        log_path: Path,
    ) -> TrainingRunResponse:
        self._append_training_log(log_path, message)
        updated = training_run.model_copy(
            update={
                "phase": phase,
                "last_heartbeat_at": self.clock(),
                "last_activity_message": message,
                "progress_percent": progress_percent,
                "latest_log_excerpt": self._latest_log_excerpt(log_path),
            }
        )
        self.store.save_training_run(updated)
        LOGGER.info(
            "bee_detector_training_run_phase_changed",
            extra={
                "workspace_id": str(updated.workspace_id),
                "training_run_id": str(updated.training_run_id),
                "phase": phase,
            },
        )
        return updated

    def _require_training_run(
        self,
        workspace_id: UUID,
        training_run_id: UUID,
    ) -> TrainingRunResponse:
        training_run = self.store.get_training_run(workspace_id, training_run_id)
        if training_run is None:
            raise DomainError("training_run_not_found", "Training Run not found.", 404)
        return training_run

    def _with_runtime_state(self, training_run: TrainingRunResponse) -> TrainingRunResponse:
        is_stale = False
        if (
            training_run.status not in TERMINAL_TRAINING_RUN_STATUSES
            and training_run.last_heartbeat_at is not None
        ):
            is_stale = self.clock() - training_run.last_heartbeat_at > timedelta(
                seconds=self.stale_after_seconds
            )
        return training_run.model_copy(
            update={
                "is_stale": is_stale,
                "stale_after_seconds": self.stale_after_seconds,
            }
        )

    def _latest_log_excerpt(self, log_path: Path, max_chars: int = 2000) -> str | None:
        if not log_path.exists():
            return None
        content = log_path.read_text(encoding="utf-8", errors="replace")
        return content[-max_chars:] if content else None

    def _append_training_log(self, log_path: Path, message: str) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = self.clock().isoformat()
        with log_path.open("a", encoding="utf-8") as file:
            file.write(f"{timestamp} {message}\n")

    def _write_dataset_package(
        self,
        *,
        dataset_version: DatasetVersionResponse,
        label_entries: list[YoloObbLabelEntry],
        manifest_payload: dict[str, object],
    ) -> Path:
        package_dir = self._dataset_package_dir(dataset_version)
        if package_dir.exists():
            shutil.rmtree(package_dir)
        (package_dir / "images" / "train").mkdir(parents=True)
        (package_dir / "images" / "val").mkdir(parents=True)
        (package_dir / "labels" / "train").mkdir(parents=True)
        (package_dir / "labels" / "val").mkdir(parents=True)
        labels_by_item: dict[UUID, list[YoloObbLabelEntry]] = {}
        for label in label_entries:
            labels_by_item.setdefault(label.dataset_item_id, []).append(label)
        generated: list[dict[str, object]] = []
        for index, item_id in enumerate(dataset_version.included_dataset_item_ids, start=1):
            item = self.store.dataset_items[item_id]
            photo = self.store.inspection_photos.get(item.inspection_photo_id)
            if photo is None:
                continue
            image_bytes = self.image_loader(photo.original_object_key)
            if image_bytes is None:
                continue
            split = _physical_split_dir(item.dataset_role)
            filename_stem = f"bee-crop-{index:06d}-{item.dataset_item_id.hex[:8]}"
            image_relative_path = f"images/{split}/{filename_stem}.png"
            label_relative_path = f"labels/{split}/{filename_stem}.txt"
            (package_dir / image_relative_path).write_bytes(
                _render_training_crop_png(image_bytes=image_bytes, dataset_item=item)
            )
            label_text = "\n".join(label.label for label in labels_by_item.get(item_id, [])) + "\n"
            (package_dir / label_relative_path).write_text(label_text, encoding="utf-8")
            generated.append(
                _generated_file_entry(
                    export_dir=package_dir,
                    relative_path=image_relative_path,
                    file_kind="image",
                    split=split,
                    dataset_item=item,
                    filename_stem=filename_stem,
                ).model_dump(mode="json")
            )
            generated.append(
                _generated_file_entry(
                    export_dir=package_dir,
                    relative_path=label_relative_path,
                    file_kind="label",
                    split=split,
                    dataset_item=item,
                    filename_stem=filename_stem,
                ).model_dump(mode="json")
            )
        (package_dir / "data.yaml").write_text(
            _dataset_yaml_text(CLASS_MAP, dataset_path=str(package_dir.resolve())),
            encoding="utf-8",
        )
        sidecar = {
            **manifest_payload,
            "dataset_version_id": str(dataset_version.dataset_version_id),
            "human_readable_id": dataset_version.human_readable_id,
            "conversion_version": CONVERSION_VERSION,
            "generated_files": generated,
        }
        (package_dir / "dataset-version.json").write_text(
            json.dumps(dataset_version.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        (package_dir / "manifest.json").write_text(
            json.dumps(sidecar, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        self._record_artifact(
            owner_type="dataset_version",
            owner_id=dataset_version.dataset_version_id,
            artifact_type="yolo_obb_package_manifest",
            path=package_dir / "manifest.json",
            content_type="application/json",
            required_or_diagnostic="required",
        )
        self._record_artifact(
            owner_type="dataset_version",
            owner_id=dataset_version.dataset_version_id,
            artifact_type="data_yaml",
            path=package_dir / "data.yaml",
            content_type="text/yaml",
            required_or_diagnostic="required",
        )
        return package_dir

    def _write_preview_artifacts(
        self,
        *,
        owner_type: str,
        owner_id: UUID,
        package_dir: Path,
        created_at: datetime,
    ) -> list[UUID]:
        _ = created_at
        preview_dir = package_dir / "previews"
        preview_dir.mkdir(exist_ok=True)
        preview_ids: list[UUID] = []
        for image_path in sorted((package_dir / "images").glob("*/*.png"))[:5]:
            preview_path = preview_dir / f"{image_path.stem}-preview.png"
            shutil.copyfile(image_path, preview_path)
            artifact = self._record_artifact(
                owner_type=owner_type,
                owner_id=owner_id,
                artifact_type="label_preview",
                path=preview_path,
                content_type="image/png",
                required_or_diagnostic="diagnostic",
            )
            preview_ids.append(artifact.artifact_id)
        return preview_ids

    def _write_dataset_report(
        self,
        dataset_version: DatasetVersionResponse,
        created_at: datetime,
    ) -> UUID:
        report_path = self._dataset_package_dir(dataset_version) / "dataset-version-report.md"
        report_path.write_text(
            "\n".join(
                [
                    f"# Dataset Version {dataset_version.human_readable_id}",
                    "",
                    f"Created: {created_at.isoformat()}",
                    f"Model purpose: {dataset_version.model_purpose}",
                    f"Export format: {dataset_version.export_format}",
                    f"Training items: {dataset_version.training_item_count}",
                    f"Validation items: {dataset_version.validation_item_count}",
                    f"Protected benchmark items: {dataset_version.benchmark_item_count}",
                    f"Excluded items: {dataset_version.excluded_item_count}",
                    "",
                    "## Warnings",
                    *[
                        f"- {warning.severity}: {warning.code} - {warning.message}"
                        for warning in dataset_version.warnings
                    ],
                    "",
                    "This Dataset Version is Bee Detector training evidence only.",
                ]
            ),
            encoding="utf-8",
        )
        return self._record_artifact(
            owner_type="dataset_version",
            owner_id=dataset_version.dataset_version_id,
            artifact_type="dataset_version_report",
            path=report_path,
            content_type="text/markdown",
            required_or_diagnostic="required",
        ).artifact_id

    def _write_training_report(
        self,
        training_run: TrainingRunResponse,
        dataset_version: DatasetVersionResponse,
        candidate: ModelCandidateResponse,
    ) -> UUID:
        run_dir = self.artifact_root / "training-runs" / f"training-run-{training_run.training_run_id}"
        report_path = run_dir / "training-run-report.md"
        report_path.write_text(
            "\n".join(
                [
                    f"# Training Run {training_run.human_readable_id}",
                    "",
                    f"Dataset Version: {dataset_version.human_readable_id}",
                    f"Database purpose: {training_run.database_purpose}",
                    f"Adapter: {training_run.adapter_type}",
                    f"Model Candidate: {candidate.human_readable_id}",
                    f"Promotion status: {candidate.promotion_status}",
                    "",
                    "This run trains Bee Detector localisation only. It is not Varroa assessment, not production suitable, and not a user-facing Model Version.",
                    "",
                    "## Metrics",
                    json.dumps(training_run.metrics_summary, indent=2, sort_keys=True),
                ]
            ),
            encoding="utf-8",
        )
        return self._record_artifact(
            owner_type="training_run",
            owner_id=training_run.training_run_id,
            artifact_type="training_run_report",
            path=report_path,
            content_type="text/markdown",
            required_or_diagnostic="required",
        ).artifact_id

    def _write_artifact_manifest(self, training_run: TrainingRunResponse, report_id: UUID) -> UUID:
        run_dir = self.artifact_root / "training-runs" / f"training-run-{training_run.training_run_id}"
        artifact_ids = [*training_run.artifact_ids, report_id]
        manifest_path = run_dir / "model-artifacts.json"
        manifest_path.write_text(
            json.dumps(
                [
                    self.store.artifacts[artifact_id].model_dump(mode="json")
                    for artifact_id in artifact_ids
                    if artifact_id in self.store.artifacts
                ],
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return self._record_artifact(
            owner_type="training_run",
            owner_id=training_run.training_run_id,
            artifact_type="artifact_manifest",
            path=manifest_path,
            content_type="application/json",
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

    def _artifact_path(self, artifact: ArtifactResponse) -> Path:
        relative = Path(artifact.relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise DomainError("artifact_path_invalid", "Artifact path is invalid.", 500)
        return self.artifact_root / relative

    def _artifact_owner_workspace(self, artifact: ArtifactResponse) -> UUID | None:
        if artifact.owner_type == "dataset_version":
            owner = self.store.dataset_versions.get(artifact.owner_id)
            return owner.workspace_id if owner else None
        if artifact.owner_type == "training_run":
            owner = self.store.training_runs.get(artifact.owner_id)
            return owner.workspace_id if owner else None
        if artifact.owner_type == "benchmark_evaluation":
            owner = self.store.benchmark_evaluations.get(artifact.owner_id)
            return owner.workspace_id if owner else None
        return None

    def _dataset_package_dir(self, dataset_version: DatasetVersionResponse) -> Path:
        return (
            self.artifact_root
            / "dataset-versions"
            / f"dataset-version-{dataset_version.dataset_version_id}"
        )

    def _eligible_training_item_exclusion_reason(self, item) -> str | None:
        if item.source_evidence_type != "training_crop":
            return "unsupported_source_evidence_type"
        if item.training_crop_id is None:
            return "unsupported_source_evidence_type"
        if not item.reviewed_ellipse_snapshots:
            return "annotation_not_reviewed"
        if item.crop_width is None or item.crop_height is None:
            return "missing_crop_geometry"
        photo = self.store.inspection_photos.get(item.inspection_photo_id)
        if photo is None:
            return "source_image_missing"
        if self.image_loader(photo.original_object_key) is None:
            return "source_image_missing"
        return None

    def _dataset_warnings(
        self,
        *,
        training_count: int,
        validation_count: int,
        benchmark_count: int,
        class_counts: Counter[str],
        review_counts: Counter[str],
        source_group_counts: Counter[str],
    ) -> list[ModelTrainingWarningResponse]:
        warnings = self._readiness_warnings(
            training_count=training_count,
            validation_count=validation_count,
            benchmark_count=benchmark_count,
        )
        for class_name in ("complete_visible_bee", "partial_visible_bee"):
            if class_counts[class_name] == 0:
                warnings.append(
                    _warning(
                        "CLASS_MISSING",
                        "warning",
                        f"No {class_name} examples are present in this Dataset Version.",
                    )
                )
        if review_counts and review_counts["human_from_scratch"] == 0:
            warnings.append(
                _warning(
                    "AUTOMATION_BIAS_RISK",
                    "high",
                    "No human-from-scratch reviewed examples are present for automation-bias comparison.",
                )
            )
        if len(source_group_counts) <= 1 and training_count + validation_count > 1:
            warnings.append(
                _warning(
                    "SOURCE_GROUP_IMBALANCE",
                    "warning",
                    "Included evidence comes from one source group or lacks source group diversity.",
                )
            )
        return warnings

    def _readiness_warnings(
        self,
        *,
        training_count: int,
        validation_count: int,
        benchmark_count: int,
    ) -> list[ModelTrainingWarningResponse]:
        warnings: list[ModelTrainingWarningResponse] = []
        if training_count < 20:
            warnings.append(
                _warning("SMALL_TRAINING_SET", "warning", "Fewer than 20 training items.")
            )
        if validation_count < 5:
            warnings.append(
                _warning("SMALL_VALIDATION_SET", "warning", "Fewer than 5 validation items.")
            )
        if benchmark_count == 0:
            warnings.append(
                _warning("NO_BENCHMARK_ITEMS", "high", "No protected benchmark items exist.")
            )
        if self.adapter.adapter_type != "fake" and not self.adapter.check_available():
            warnings.append(
                _warning(
                    "REAL_ADAPTER_UNAVAILABLE",
                    "high",
                    "The real YOLO training adapter is not available in this environment.",
                )
            )
        return warnings

    def _require_curator(self, *, user: UserContext, workspace_id: UUID) -> None:
        self.store.require_workspace_access(user, workspace_id)
        self.store.require_data_use_agreement(workspace_id)
        self.store.require_dataset_curator_capability(user)

    def _human_id(self, prefix: str, existing: list[object]) -> str:
        return f"{prefix}-{len(existing) + 1:06d}"


def _warning(code: str, severity: str, message: str) -> ModelTrainingWarningResponse:
    return ModelTrainingWarningResponse(
        code=code,
        severity=ModelTrainingWarningSeverity(severity),
        message=message,
    )


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _excluded_item(item, reason: str) -> YoloObbExcludedItem:
    return YoloObbExcludedItem(
        dataset_item_id=item.dataset_item_id,
        training_crop_id=item.training_crop_id,
        dataset_role=item.dataset_role,
        reason=reason,
    )


def _review_method_for_source(source: str) -> str:
    if source == "human_from_scratch":
        return "human_from_scratch"
    if source == "imported_public_dataset":
        return "imported_reviewed"
    return "human_reviewed_candidate"


def _git_value(args: list[str]) -> str | None:
    try:
        result = subprocess.run(args, check=False, capture_output=True, text=True)
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _git_dirty_status() -> str:
    value = _git_value(["git", "status", "--porcelain"])
    if value is None:
        return "unknown"
    return "dirty" if value else "clean"
