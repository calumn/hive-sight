from __future__ import annotations

import json
import logging
import platform
import shutil
import subprocess
import sys
import threading
import base64
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Protocol
from uuid import UUID

from PIL import Image, ImageOps

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
    BeeTrainingReadinessResponse,
    BeeTrainingStartRequest,
    BeeTrainingStartResponse,
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
MARKED_BEE_DATASET_PURPOSE = "marked_bee_detection_orientation"
LEGACY_BEE_DETECTOR_DATASET_PURPOSE = "bee_detector_training_baseline"
MARKED_BEE_MODEL_PURPOSE = "marked_bee"
MARKED_BEE_EXPORT_FORMAT = "marked_bee_dataset_v1"
ORIENTATION_EXPORT_FORMAT = "bee_orientation_head_up_down_v1"
ORIENTATION_PACKAGE_VERSION = "bee_orientation_head_up_down_v1"
ORIENTATION_CLASS_MAP = {"0": "head_up", "1": "head_down"}
ORIENTATION_IMAGE_SIZE = 224
ORIENTATION_ELLIPSE_MARGIN_RATIO = 0.2
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


class BeeOrientationTrainingAdapter(Protocol):
    adapter_type: str

    def check_available(self) -> bool:
        ...

    def run_training(
        self,
        *,
        training_run: TrainingRunResponse,
        run_dir: Path,
        dataset_package_dir: Path,
        package_result: dict[str, object],
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
            f"fake HiveSight Bee Localisation weights for {training_run.human_readable_id}\n",
            encoding="utf-8",
        )
        log_path = run_dir / "training.log"
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(
                "Fake adapter completed deterministic Bee Localisation smoke training.\n"
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
                "Run pnpm model:setup:bee before using the real Bee Localisation training adapter.",
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


class FakeBeeOrientationTrainingAdapter:
    adapter_type = "fake"

    def check_available(self) -> bool:
        return True

    def run_training(
        self,
        *,
        training_run: TrainingRunResponse,
        run_dir: Path,
        dataset_package_dir: Path,
        package_result: dict[str, object],
    ) -> TrainingAdapterResult:
        _ = dataset_package_dir
        manifest_path = run_dir / "fake-orientation-candidate.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "model_purpose": "bee_orientation",
                    "model_family": "bee_orientation_binary_classifier",
                    "adapter_type": "fake",
                    "predictive_training_performed": False,
                    "source_dataset_version_id": str(training_run.dataset_version_id),
                    "package_hash": package_result["package_hash"],
                    "class_map": ORIENTATION_CLASS_MAP,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        log_path = run_dir / "training.log"
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write("Fake Bee Orientation adapter validated package shape only.\n")
        return TrainingAdapterResult(
            metrics={
                "predictive_training_performed": False,
                "metric_scope": "fake_adapter_package_validation",
            },
            model_artifact_path=manifest_path,
            log_path=log_path,
            base_weights_source="fake_adapter_manifest",
        )


class TorchvisionBeeOrientationTrainingAdapter:
    adapter_type = "torchvision_orientation_classifier"

    def __init__(self, device: str = "cpu", architecture: str = "mobilenet_v3_small") -> None:
        self.device = device
        self.architecture = architecture

    def check_available(self) -> bool:
        try:
            import torch  # noqa: F401
            import torchvision  # noqa: F401
        except ImportError:
            return False
        return True

    def run_training(
        self,
        *,
        training_run: TrainingRunResponse,
        run_dir: Path,
        dataset_package_dir: Path,
        package_result: dict[str, object],
    ) -> TrainingAdapterResult:
        try:
            import torch
            from torch import nn
            from torch.utils.data import DataLoader, Dataset
            from torchvision import models, transforms
        except ImportError as exc:
            raise DomainError(
                "real_orientation_adapter_unavailable",
                "Run pnpm model:setup:bee before using the real Bee Orientation adapter.",
                409,
            ) from exc

        log_path = run_dir / "training.log"
        labels_path = dataset_package_dir / "labels.jsonl"
        labels = [
            json.loads(line)
            for line in labels_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        train_rows = [row for row in labels if str(row["split"]) == str(DatasetRole.training)]
        val_rows = [row for row in labels if str(row["split"]) == str(DatasetRole.validation)]
        if not train_rows or not val_rows:
            raise DomainError(
                "orientation_training_and_validation_required",
                "Bee Orientation real training requires Training and Validation examples.",
                409,
            )

        torch.manual_seed(training_run.random_seed)
        device = torch.device(self.device)
        transform = transforms.Compose(
            [
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

        class OrientationDataset(Dataset):
            def __init__(self, rows: list[dict[str, object]]) -> None:
                self.rows = rows

            def __len__(self) -> int:
                return len(self.rows)

            def __getitem__(self, index: int):
                row = self.rows[index]
                image = Image.open(dataset_package_dir / str(row["image_path"])).convert("RGB")
                return transform(image), int(row["class_id"])

        model = models.mobilenet_v3_small(weights=None, num_classes=2)
        model.to(device)
        optimiser = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()
        train_loader = DataLoader(
            OrientationDataset(train_rows),
            batch_size=max(1, int(training_run.training_settings["batch_size"])),
            shuffle=False,
        )
        val_loader = DataLoader(OrientationDataset(val_rows), batch_size=1, shuffle=False)
        epochs = int(training_run.training_settings["epochs"])
        epoch_metrics: list[dict[str, float]] = []
        model.train()
        for epoch in range(epochs):
            total_loss = 0.0
            correct = 0
            seen = 0
            for images, labels_tensor in train_loader:
                images = images.to(device)
                labels_tensor = labels_tensor.to(device)
                optimiser.zero_grad()
                outputs = model(images)
                loss = criterion(outputs, labels_tensor)
                loss.backward()
                optimiser.step()
                total_loss += float(loss.detach().cpu())
                predictions = outputs.argmax(dim=1)
                correct += int((predictions == labels_tensor).sum().item())
                seen += int(labels_tensor.numel())
            epoch_metrics.append(
                {
                    "epoch": float(epoch + 1),
                    "training_loss": total_loss / max(len(train_loader), 1),
                    "training_accuracy": correct / max(seen, 1),
                }
            )

        confusion = {
            "head_up": {"head_up": 0, "head_down": 0},
            "head_down": {"head_up": 0, "head_down": 0},
        }
        class_names = ["head_up", "head_down"]
        correct = 0
        seen = 0
        model.eval()
        with torch.no_grad():
            for images, labels_tensor in val_loader:
                images = images.to(device)
                labels_tensor = labels_tensor.to(device)
                prediction = int(model(images).argmax(dim=1).cpu().item())
                truth = int(labels_tensor.cpu().item())
                confusion[class_names[truth]][class_names[prediction]] += 1
                correct += int(prediction == truth)
                seen += 1
        validation_accuracy = correct / max(seen, 1)
        weights_path = run_dir / "weights" / "orientation-classifier.pt"
        weights_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "state_dict": model.state_dict(),
                "class_map": ORIENTATION_CLASS_MAP,
                "architecture": self.architecture,
                "package_hash": package_result["package_hash"],
            },
            weights_path,
        )
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(
                "Torchvision Bee Orientation training completed. "
                "Metrics are training-run validation only, not benchmark evidence.\n"
            )
        return TrainingAdapterResult(
            metrics={
                "predictive_training_performed": True,
                "metric_scope": "training_run_validation_not_benchmark",
                "architecture": self.architecture,
                "device": str(device),
                "validation_accuracy": validation_accuracy,
                "confusion_matrix": confusion,
                "epoch_metrics": epoch_metrics,
                "package_hash": package_result["package_hash"],
            },
            model_artifact_path=weights_path,
            log_path=log_path,
            base_weights_source="torchvision_random_initialisation",
        )


class BeeDetectorTrainingWorkflow:
    def __init__(
        self,
        *,
        store: InMemoryProductDataStore,
        image_loader: Callable[[str], bytes | None],
        artifact_root: Path,
        adapter: BeeDetectorTrainingAdapter,
        orientation_adapter: BeeOrientationTrainingAdapter | None = None,
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
        self.orientation_adapter = orientation_adapter or FakeBeeOrientationTrainingAdapter()
        self.persistence_backend = persistence_backend
        self.database_purpose = database_purpose
        self.clock = clock
        self.stale_after_seconds = stale_after_seconds
        self.heartbeat_interval_seconds = heartbeat_interval_seconds

    def readiness(
        self,
        user: UserContext,
        workspace_id: UUID,
        model_purpose: str = "bee_detector",
        dataset_version_id: UUID | None = None,
    ) -> ModelTrainingReadinessResponse:
        self._require_curator(user=user, workspace_id=workspace_id)
        if model_purpose == "bee_orientation":
            return self._orientation_readiness(
                user=user,
                workspace_id=workspace_id,
                dataset_version_id=dataset_version_id,
            )
        if model_purpose != "bee_detector":
            raise DomainError(
                "unsupported_model_purpose",
                "Only Bee Detection and Bee Orientation training readiness are supported.",
                422,
            )
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
            model_purpose="bee_detector",
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

    def _orientation_readiness(
        self,
        *,
        user: UserContext,
        workspace_id: UUID,
        dataset_version_id: UUID | None,
    ) -> ModelTrainingReadinessResponse:
        real_adapter_available = (
            self.orientation_adapter.check_available()
            if self.orientation_adapter.adapter_type != "fake"
            else False
        )
        active = self.store.active_training_run(workspace_id)
        dataset_version = None
        if dataset_version_id is not None:
            dataset_version = self.get_dataset_version(
                user=user,
                workspace_id=workspace_id,
                dataset_version_id=dataset_version_id,
            )
        elif self.store.list_dataset_versions(workspace_id):
            dataset_version = self.store.list_dataset_versions(workspace_id)[0]
        items = []
        if dataset_version is not None:
            item_ids = [
                *dataset_version.training_dataset_item_ids,
                *dataset_version.validation_dataset_item_ids,
                *dataset_version.protected_benchmark_dataset_item_ids,
            ]
            items = [
                self.store.dataset_items[item_id]
                for item_id in item_ids
                if item_id in self.store.dataset_items
            ]
        counts = self._orientation_evidence_counts(items)
        warnings = self._orientation_readiness_warnings(
            dataset_version=dataset_version,
            counts=counts,
            missing_source_image_count=self._orientation_missing_source_image_count(items),
        )
        has_blocker = any(warning.severity == ModelTrainingWarningSeverity.high for warning in warnings)
        return ModelTrainingReadinessResponse(
            workspace_id=workspace_id,
            persistence_backend=self.persistence_backend,
            database_purpose=self.database_purpose,
            adapter_type=self.orientation_adapter.adapter_type,
            real_adapter_available=real_adapter_available,
            model_purpose="bee_orientation",
            dataset_version_id=dataset_version.dataset_version_id if dataset_version else None,
            dataset_version_human_readable_id=(
                dataset_version.human_readable_id if dataset_version else None
            ),
            dataset_version_purpose=dataset_version.purpose if dataset_version else None,
            active_training_run_id=active.training_run_id if active else None,
            training_item_count=len(dataset_version.training_dataset_item_ids)
            if dataset_version
            else 0,
            validation_item_count=len(dataset_version.validation_dataset_item_ids)
            if dataset_version
            else 0,
            benchmark_item_count=len(dataset_version.protected_benchmark_dataset_item_ids)
            if dataset_version
            else 0,
            eligible_training_source_bee_count=counts["eligible_training"],
            eligible_validation_source_bee_count=counts["eligible_validation"],
            generated_training_example_count=counts["eligible_training"] * 2,
            generated_validation_example_count=counts["eligible_validation"] * 2,
            protected_benchmark_source_bee_count=counts["benchmark_protected"],
            excluded_unreliable_orientation_count=counts["orientation_unreliable"],
            excluded_partial_visible_bee_count=counts["partial_visible_bee_deferred"],
            eligible_to_create_dataset_version=False,
            eligible_to_start_training=(
                dataset_version is not None
                and active is None
                and counts["eligible_training"] >= self._minimum_orientation_source_bees()
                and counts["eligible_validation"] >= self._minimum_orientation_source_bees()
                and not has_blocker
                and dataset_version.purpose == MARKED_BEE_DATASET_PURPOSE
                and (self.orientation_adapter.adapter_type == "fake" or real_adapter_available)
            ),
            warnings=warnings,
        )

    def bee_training_readiness(
        self,
        *,
        user: UserContext,
        workspace_id: UUID,
        dataset_version_id: UUID | None = None,
    ) -> BeeTrainingReadinessResponse:
        localisation = self.readiness(
            user=user,
            workspace_id=workspace_id,
            model_purpose="bee_detector",
            dataset_version_id=dataset_version_id,
        )
        orientation = self.readiness(
            user=user,
            workspace_id=workspace_id,
            model_purpose="bee_orientation",
            dataset_version_id=dataset_version_id,
        )
        warnings = [
            *[
                warning.model_copy(update={"code": f"BEE_LOCALISATION_{warning.code}"})
                for warning in localisation.warnings
            ],
            *[
                warning.model_copy(update={"code": f"BEE_ORIENTATION_{warning.code}"})
                for warning in orientation.warnings
            ],
        ]
        return BeeTrainingReadinessResponse(
            workspace_id=workspace_id,
            dataset_version_id=orientation.dataset_version_id,
            dataset_version_human_readable_id=orientation.dataset_version_human_readable_id,
            active_training_run_id=localisation.active_training_run_id
            or orientation.active_training_run_id,
            bee_localisation=localisation,
            bee_orientation=orientation,
            eligible_to_start_bee_training=(
                localisation.eligible_to_start_training
                and orientation.eligible_to_start_training
                and orientation.dataset_version_id is not None
            ),
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
            "purpose": purpose or MARKED_BEE_DATASET_PURPOSE,
            "model_purpose": MARKED_BEE_MODEL_PURPOSE,
            "export_format": MARKED_BEE_EXPORT_FORMAT,
            "derived_export_formats": {
                "bee_detector": EXPORT_FORMAT,
                "bee_orientation": ORIENTATION_EXPORT_FORMAT,
            },
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
            purpose=purpose or MARKED_BEE_DATASET_PURPOSE,
            model_purpose=MARKED_BEE_MODEL_PURPOSE,
            status="active",
            export_format=MARKED_BEE_EXPORT_FORMAT,
            selection_criteria={
                "status": "active",
                "source_evidence_type": "training_crop",
                "required_review": "reviewed_ellipses",
                "roles": ["training", "validation", "benchmark", "excluded"],
                "shared_source_for": ["bee_detector", "bee_orientation"],
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
        if request.model_purpose not in {"bee_detector", "bee_orientation"}:
            raise DomainError(
                "unsupported_model_purpose",
                "Only Bee Detection and Bee Orientation Training Runs are supported.",
                422,
            )
        adapter = self._adapter_for_model_purpose(request.model_purpose)
        adapter_label = (
            "Bee Orientation" if request.model_purpose == "bee_orientation" else "Bee Localisation"
        )
        if adapter.adapter_type != "fake" and self.database_purpose == "test":
            raise DomainError(
                "real_adapter_refuses_test_database",
                f"Real {adapter_label} training must target the dev or QA database, not the resettable test database.",
                409,
            )
        if adapter.adapter_type != "fake" and not adapter.check_available():
            raise DomainError(
                "real_adapter_unavailable"
                if request.model_purpose == "bee_detector"
                else "real_orientation_adapter_unavailable",
                f"Run pnpm model:setup:bee before using the real {adapter_label} adapter.",
                409,
            )
        active_run = self.store.active_training_run(request.workspace_id)
        if active_run is not None:
            raise DomainError(
                "training_run_already_active",
                "Another Bee Training Run is already queued or running.",
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
        if request.model_purpose == "bee_orientation":
            if dataset_version.purpose != MARKED_BEE_DATASET_PURPOSE:
                raise DomainError(
                    "marked_bee_dataset_version_required",
                    "Bee Orientation training requires a Marked-Bee Dataset Version.",
                    409,
                )
            orientation_counts = self._orientation_evidence_counts(
                [
                    self.store.dataset_items[item_id]
                    for item_id in [
                        *dataset_version.training_dataset_item_ids,
                        *dataset_version.validation_dataset_item_ids,
                        *dataset_version.protected_benchmark_dataset_item_ids,
                    ]
                    if item_id in self.store.dataset_items
                ]
            )
            if (
                orientation_counts["eligible_training"] < self._minimum_orientation_source_bees()
                or orientation_counts["eligible_validation"] < self._minimum_orientation_source_bees()
            ):
                minimum_source_bees = self._minimum_orientation_source_bees()
                raise DomainError(
                    "orientation_training_and_validation_required",
                    f"Create at least {minimum_source_bees} reliable complete visible bees in Training and {minimum_source_bees} in Validation before starting Bee Orientation training.",
                    409,
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
            model_purpose=request.model_purpose,
            model_family=(
                "bee_orientation_binary_classifier"
                if request.model_purpose == "bee_orientation"
                else "yolo_obb"
            ),
            model_size=request.model_size,
            base_weights=(
                (
                    "fake_orientation_adapter_manifest"
                    if self.orientation_adapter.adapter_type == "fake"
                    else "torchvision_random_initialisation"
                )
                if request.model_purpose == "bee_orientation"
                else "yolo11n-obb.pt"
            ),
            base_weights_source="pending",
            status="queued",
            phase="queued",
            adapter_type=adapter.adapter_type,
            database_purpose=self.database_purpose,
            training_settings={
                "model_purpose": request.model_purpose,
                "model_size": request.model_size,
                "epochs": request.epochs,
                "image_size": (
                    ORIENTATION_IMAGE_SIZE
                    if request.model_purpose == "bee_orientation"
                    else request.image_size
                ),
                "batch_size": request.batch_size,
                **(
                    {
                        "ellipse_margin_ratio": ORIENTATION_ELLIPSE_MARGIN_RATIO,
                        "augmentation_policy": "head_down_rotate_180",
                        "package_format_version": ORIENTATION_PACKAGE_VERSION,
                    }
                    if request.model_purpose == "bee_orientation"
                    else {}
                ),
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

    def start_bee_training(
        self,
        *,
        user: UserContext,
        request: BeeTrainingStartRequest,
    ) -> BeeTrainingStartResponse:
        readiness = self.bee_training_readiness(
            user=user,
            workspace_id=request.workspace_id,
            dataset_version_id=request.dataset_version_id,
        )
        if not readiness.eligible_to_start_bee_training:
            raise DomainError(
                "bee_training_not_ready",
                "Bee Training cannot start until Bee Localisation and Bee Orientation readiness blockers are resolved.",
                409,
            )
        localisation_run = self.start_training_run(
            user=user,
            request=TrainingRunStartRequest(
                workspace_id=request.workspace_id,
                dataset_version_id=request.dataset_version_id,
                model_purpose="bee_detector",
                model_size=request.model_size,
                epochs=request.epochs,
                image_size=request.image_size,
                batch_size=request.batch_size,
                random_seed=request.random_seed,
                purpose_notes=request.purpose_notes,
                acknowledge_high_severity_warnings=request.acknowledge_high_severity_warnings,
            ),
        )
        thread = threading.Thread(
            target=self._start_orientation_after_localisation,
            args=(user, request, localisation_run.training_run_id),
            daemon=True,
            name=f"hivesight-bee-training-sequence-{localisation_run.training_run_id}",
        )
        thread.start()
        return BeeTrainingStartResponse(
            workspace_id=request.workspace_id,
            dataset_version_id=request.dataset_version_id,
            bee_localisation_training_run=localisation_run,
            bee_orientation_training_run=None,
            message="Bee Localisation training started. Bee Orientation will start after it completes.",
        )

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
        if training_run.model_purpose == "bee_orientation":
            return self._run_orientation_training_now(training_run, dataset_version, run_dir)
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

    def _run_orientation_training_now(
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
                "phase": "generating_package",
                "started_at": self.clock(),
                "last_heartbeat_at": self.clock(),
                "last_activity_message": "Preparing Bee Orientation package.",
                "progress_percent": 5,
                "latest_log_excerpt": self._latest_log_excerpt(log_path),
            }
        )
        self.store.save_training_run(running)
        try:
            package_dir = run_dir / "bee-orientation-package"
            package_result = self._write_orientation_package(
                dataset_version=dataset_version,
                package_dir=package_dir,
            )
            running = self._mark_training_run_phase(
                running,
                phase="training",
                message="Bee Orientation training adapter is running.",
                progress_percent=75,
                log_path=log_path,
            )
            adapter_result = self.orientation_adapter.run_training(
                training_run=running,
                run_dir=run_dir,
                dataset_package_dir=package_dir,
                package_result=package_result,
            )
            package_manifest_artifact = self._record_artifact(
                owner_type="training_run",
                owner_id=running.training_run_id,
                artifact_type="bee_orientation_package_manifest",
                path=package_dir / "manifest.json",
                content_type="application/json",
                required_or_diagnostic="required",
            )
            labels_artifact = self._record_artifact(
                owner_type="training_run",
                owner_id=running.training_run_id,
                artifact_type="bee_orientation_labels",
                path=package_dir / "labels.jsonl",
                content_type="application/jsonl",
                required_or_diagnostic="required",
            )
            exclusions_artifact = self._record_artifact(
                owner_type="training_run",
                owner_id=running.training_run_id,
                artifact_type="bee_orientation_exclusions",
                path=package_dir / "exclusions.jsonl",
                content_type="application/jsonl",
                required_or_diagnostic="diagnostic",
            )
            candidate_artifact = self._record_artifact(
                owner_type="training_run",
                owner_id=running.training_run_id,
                artifact_type=(
                    "fake_orientation_candidate_manifest"
                    if self.orientation_adapter.adapter_type == "fake"
                    else "orientation_model_weights"
                ),
                path=adapter_result.model_artifact_path,
                content_type=(
                    "application/json"
                    if self.orientation_adapter.adapter_type == "fake"
                    else "application/octet-stream"
                ),
                required_or_diagnostic="required",
            )
            contact_sheet_artifact = self._record_artifact(
                owner_type="training_run",
                owner_id=running.training_run_id,
                artifact_type="bee_orientation_contact_sheet",
                path=package_dir / "contact-sheet.md",
                content_type="text/markdown",
                required_or_diagnostic="diagnostic",
            )
            log_artifact = self._record_artifact(
                owner_type="training_run",
                owner_id=running.training_run_id,
                artifact_type="training_log",
                path=log_path,
                content_type="text/plain",
                required_or_diagnostic="diagnostic",
            )
            candidate = ModelCandidateResponse(
                model_candidate_id=self.store.id_factory(),
                workspace_id=running.workspace_id,
                human_readable_id=self._human_id(
                    "HS-MC", self.store.list_model_candidates(running.workspace_id)
                ),
                display_name=f"Bee orientation baseline {running.human_readable_id}",
                training_run_id=running.training_run_id,
                model_purpose="bee_orientation",
                model_family="bee_orientation_binary_classifier",
                adapter_type=running.adapter_type,
                artifact_id=candidate_artifact.artifact_id,
                status="created",
                promotion_status="not_evaluated",
                not_user_facing_reason="baseline_training_only",
                created_at=self.clock(),
            )
            self.store.save_model_candidate(candidate)
            metrics = {
                **adapter_result.metrics,
                "eligible_training_source_bee_count": package_result[
                    "eligible_training_source_bee_count"
                ],
                "eligible_validation_source_bee_count": package_result[
                    "eligible_validation_source_bee_count"
                ],
                "generated_training_example_count": package_result[
                    "generated_training_example_count"
                ],
                "generated_validation_example_count": package_result[
                    "generated_validation_example_count"
                ],
                "protected_benchmark_source_bee_count": package_result[
                    "protected_benchmark_source_bee_count"
                ],
                "excluded_unreliable_orientation_count": package_result[
                    "excluded_unreliable_orientation_count"
                ],
                "excluded_partial_visible_bee_count": package_result[
                    "excluded_partial_visible_bee_count"
                ],
                "package_hash": package_result["package_hash"],
            }
            updated = running.model_copy(
                update={
                    "status": "completed",
                    "phase": "completed",
                    "completed_at": self.clock(),
                    "last_heartbeat_at": self.clock(),
                    "last_activity_message": (
                        "Bee Orientation training completed and Model Candidate created."
                    ),
                    "progress_percent": 100,
                    "latest_log_excerpt": self._latest_log_excerpt(log_path),
                    "base_weights_source": adapter_result.base_weights_source,
                    "artifact_ids": [
                        package_manifest_artifact.artifact_id,
                        labels_artifact.artifact_id,
                        exclusions_artifact.artifact_id,
                        contact_sheet_artifact.artifact_id,
                        candidate_artifact.artifact_id,
                        log_artifact.artifact_id,
                    ],
                    "metrics_summary": metrics,
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
            failed = running.model_copy(
                update={
                    "status": "failed",
                    "phase": "failed",
                    "completed_at": self.clock(),
                    "last_heartbeat_at": self.clock(),
                    "last_activity_message": "Bee Orientation baseline failed.",
                    "progress_percent": None,
                    "latest_log_excerpt": self._latest_log_excerpt(log_path),
                    "failure_code": error.code,
                    "failure_message": error.message,
                }
            )
            self.store.save_training_run(failed)
            return failed
        except Exception as error:
            failed = running.model_copy(
                update={
                    "status": "failed",
                    "phase": "failed",
                    "completed_at": self.clock(),
                    "last_heartbeat_at": self.clock(),
                    "last_activity_message": "Bee Orientation baseline failed unexpectedly.",
                    "progress_percent": None,
                    "latest_log_excerpt": self._latest_log_excerpt(log_path),
                    "failure_code": "orientation_training_run_failed",
                    "failure_message": str(error),
                }
            )
            self.store.save_training_run(failed)
            LOGGER.exception(
                "bee_orientation_training_run_failed",
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

    def _start_orientation_after_localisation(
        self,
        user: UserContext,
        request: BeeTrainingStartRequest,
        localisation_training_run_id: UUID,
    ) -> None:
        while True:
            current = self.store.get_training_run(
                request.workspace_id,
                localisation_training_run_id,
            )
            if current is None:
                return
            if current.status == "completed":
                break
            if current.status in TERMINAL_TRAINING_RUN_STATUSES:
                LOGGER.info(
                    "bee_orientation_training_skipped_after_localisation_failure",
                    extra={
                        "workspace_id": str(request.workspace_id),
                        "bee_localisation_training_run_id": str(localisation_training_run_id),
                        "status": current.status,
                    },
                )
                return
            threading.Event().wait(0.2)
        self.start_training_run(
            user=user,
            request=TrainingRunStartRequest(
                workspace_id=request.workspace_id,
                dataset_version_id=request.dataset_version_id,
                model_purpose="bee_orientation",
                model_size=request.model_size,
                epochs=request.epochs,
                image_size=ORIENTATION_IMAGE_SIZE,
                batch_size=request.batch_size,
                random_seed=request.random_seed,
                purpose_notes=request.purpose_notes,
                acknowledge_high_severity_warnings=request.acknowledge_high_severity_warnings,
            ),
        )

    def _adapter_for_model_purpose(
        self,
        model_purpose: str,
    ) -> BeeDetectorTrainingAdapter | BeeOrientationTrainingAdapter:
        if model_purpose == "bee_orientation":
            return self.orientation_adapter
        return self.adapter

    def _minimum_orientation_source_bees(self) -> int:
        return 1 if self.orientation_adapter.adapter_type == "fake" else 4

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

    def _orientation_evidence_counts(self, items) -> Counter[str]:
        counts: Counter[str] = Counter()
        for item in items:
            for ellipse in item.reviewed_ellipse_snapshots:
                if item.dataset_role == DatasetRole.benchmark:
                    if (
                        ellipse.annotation_type == AnnotationType.complete_visible_bee
                        and str(ellipse.orientation_reliability) == "reliable"
                    ):
                        counts["benchmark_protected"] += 1
                    continue
                if ellipse.annotation_type == AnnotationType.partial_visible_bee:
                    counts["partial_visible_bee_deferred"] += 1
                    continue
                if ellipse.annotation_type != AnnotationType.complete_visible_bee:
                    counts["unsupported_annotation_type"] += 1
                    continue
                if str(ellipse.orientation_reliability) != "reliable":
                    counts["orientation_unreliable"] += 1
                    continue
                if item.dataset_role == DatasetRole.training:
                    counts["eligible_training"] += 1
                elif item.dataset_role == DatasetRole.validation:
                    counts["eligible_validation"] += 1
        return counts

    def _orientation_readiness_warnings(
        self,
        *,
        dataset_version: DatasetVersionResponse | None,
        counts: Counter[str],
        missing_source_image_count: int,
    ) -> list[ModelTrainingWarningResponse]:
        warnings: list[ModelTrainingWarningResponse] = []
        if dataset_version is None:
            warnings.append(
                _warning(
                    "NO_DATASET_VERSION",
                    "high",
                    "Create a Marked-Bee Dataset Version before Bee Orientation training.",
                )
            )
            return warnings
        if dataset_version.purpose != MARKED_BEE_DATASET_PURPOSE:
            warnings.append(
                _warning(
                    "MARKED_BEE_DATASET_VERSION_REQUIRED",
                    "high",
                    "Bee Orientation training requires a Marked-Bee Dataset Version.",
                )
            )
        minimum_source_bees = self._minimum_orientation_source_bees()
        if counts["eligible_training"] < minimum_source_bees:
            warnings.append(
                _warning(
                    "NO_RELIABLE_TRAINING_HEAD_ORIENTATION",
                    "high",
                    f"Bee Orientation training needs at least {minimum_source_bees} reliable complete visible bees in Training evidence.",
                )
            )
        if counts["eligible_validation"] < minimum_source_bees:
            warnings.append(
                _warning(
                    "NO_RELIABLE_VALIDATION_HEAD_ORIENTATION",
                    "high",
                    f"Bee Orientation training needs at least {minimum_source_bees} reliable complete visible bees in Validation evidence.",
                )
            )
        if missing_source_image_count > 0:
            warnings.append(
                _warning(
                    "SOURCE_IMAGE_BYTES_MISSING",
                    "high",
                    "One or more source images cannot be read for Bee Orientation training.",
                )
            )
        if counts["partial_visible_bee_deferred"] > 0:
            warnings.append(
                _warning(
                    "PARTIAL_VISIBLE_BEES_DEFERRED",
                    "warning",
                    "Partial visible bees are excluded from the first Bee Orientation baseline.",
                )
            )
        if counts["orientation_unreliable"] > 0:
            warnings.append(
                _warning(
                    "UNRELIABLE_ORIENTATION_EXCLUDED",
                    "warning",
                    "Bees marked with unreliable head orientation are excluded from the baseline.",
                )
            )
        if counts["benchmark_protected"] == 0:
            warnings.append(
                _warning(
                    "NO_ORIENTATION_BENCHMARK_ITEMS",
                    "warning",
                    "No protected benchmark bees exist for future Bee Orientation evaluation.",
                )
            )
        return warnings

    def _orientation_missing_source_image_count(self, items) -> int:
        missing_count = 0
        for item in items:
            photo = self.store.inspection_photos.get(item.inspection_photo_id)
            if photo is None or self.image_loader(photo.original_object_key) is None:
                missing_count += 1
        return missing_count

    def _write_orientation_package(
        self,
        *,
        dataset_version: DatasetVersionResponse,
        package_dir: Path,
    ) -> dict[str, object]:
        if package_dir.exists():
            shutil.rmtree(package_dir)
        (package_dir / "images" / "train").mkdir(parents=True)
        (package_dir / "images" / "val").mkdir(parents=True)
        labels: list[dict[str, object]] = []
        exclusions: list[dict[str, object]] = []
        image_payloads: list[dict[str, object]] = []
        items = [
            self.store.dataset_items[item_id]
            for item_id in [
                *dataset_version.training_dataset_item_ids,
                *dataset_version.validation_dataset_item_ids,
                *dataset_version.protected_benchmark_dataset_item_ids,
            ]
            if item_id in self.store.dataset_items
        ]
        for item in items:
            photo = self.store.inspection_photos.get(item.inspection_photo_id)
            if photo is None:
                raise DomainError(
                    "source_image_missing",
                    "A Dataset Item references a missing source image.",
                    409,
                )
            image_bytes = self.image_loader(photo.original_object_key)
            if image_bytes is None:
                raise DomainError(
                    "source_image_missing",
                    "A Dataset Item source image could not be read for Bee Orientation training.",
                    409,
                )
            source_hash = sha256(image_bytes).hexdigest()
            source_image = Image.open(BytesIO(image_bytes)).convert("RGB")
            for ellipse in item.reviewed_ellipse_snapshots:
                exclusion_reason = self._orientation_exclusion_reason(item, ellipse)
                if exclusion_reason is not None:
                    exclusions.append(
                        self._orientation_exclusion_entry(
                            item=item,
                            ellipse=ellipse,
                            reason=exclusion_reason,
                        )
                    )
                    continue
                split = "train" if item.dataset_role == DatasetRole.training else "val"
                head_up_image = self._orientation_head_up_image(source_image, ellipse)
                examples = [
                    ("head_up", "none", head_up_image),
                    ("head_down", "rotate_180", head_up_image.rotate(180)),
                ]
                for label_name, augmentation, generated_image in examples:
                    filename = (
                        f"{split}-{item.dataset_item_id.hex[:8]}-"
                        f"{ellipse.annotation_id.hex[:8]}-{label_name}.png"
                    )
                    relative_path = f"images/{split}/{filename}"
                    output_path = package_dir / relative_path
                    generated_image.save(output_path, format="PNG")
                    generated_bytes = output_path.read_bytes()
                    generated_hash = sha256(generated_bytes).hexdigest()
                    entry = {
                        "generated_example_id": (
                            f"{item.dataset_item_id}:{ellipse.annotation_id}:{label_name}"
                        ),
                        "dataset_item_id": str(item.dataset_item_id),
                        "training_crop_id": str(item.training_crop_id),
                        "inspection_photo_id": str(item.inspection_photo_id),
                        "annotation_id": str(ellipse.annotation_id),
                        "split": item.dataset_role,
                        "image_path": relative_path,
                        "label": label_name,
                        "class_id": 0 if label_name == "head_up" else 1,
                        "augmentation": augmentation,
                        "source_image_sha256": source_hash,
                        "image_sha256": generated_hash,
                        "transform": {
                            "source_rotation_degrees": ellipse.rotation_degrees,
                            "head_up_rotation_degrees": -90 - ellipse.rotation_degrees,
                            "image_size": ORIENTATION_IMAGE_SIZE,
                            "ellipse_margin_ratio": ORIENTATION_ELLIPSE_MARGIN_RATIO,
                        },
                    }
                    labels.append(entry)
                    image_payloads.append(
                        {
                            "path": relative_path,
                            "sha256": generated_hash,
                            "label": label_name,
                            "split": split,
                        }
                    )
        counts = {
            "eligible_training_source_bee_count": len(
                {
                    (label["dataset_item_id"], label["annotation_id"])
                    for label in labels
                    if label["split"] == DatasetRole.training
                }
            ),
            "eligible_validation_source_bee_count": len(
                {
                    (label["dataset_item_id"], label["annotation_id"])
                    for label in labels
                    if label["split"] == DatasetRole.validation
                }
            ),
            "generated_training_example_count": sum(
                1 for label in labels if label["split"] == DatasetRole.training
            ),
            "generated_validation_example_count": sum(
                1 for label in labels if label["split"] == DatasetRole.validation
            ),
            "protected_benchmark_source_bee_count": sum(
                1 for exclusion in exclusions if exclusion["reason"] == "benchmark_protected"
            ),
            "excluded_unreliable_orientation_count": sum(
                1 for exclusion in exclusions if exclusion["reason"] == "orientation_unreliable"
            ),
            "excluded_partial_visible_bee_count": sum(
                1 for exclusion in exclusions if exclusion["reason"] == "partial_visible_bee_deferred"
            ),
        }
        if (
            counts["eligible_training_source_bee_count"] < self._minimum_orientation_source_bees()
            or counts["eligible_validation_source_bee_count"] < self._minimum_orientation_source_bees()
        ):
            minimum_source_bees = self._minimum_orientation_source_bees()
            raise DomainError(
                "orientation_training_and_validation_required",
                f"Bee Orientation training requires at least {minimum_source_bees} reliable complete bees in Training and {minimum_source_bees} in Validation.",
                409,
            )
        hash_payload = {
            "package_format_version": ORIENTATION_PACKAGE_VERSION,
            "source_dataset_version_id": str(dataset_version.dataset_version_id),
            "class_map": ORIENTATION_CLASS_MAP,
            "image_size": ORIENTATION_IMAGE_SIZE,
            "ellipse_margin_ratio": ORIENTATION_ELLIPSE_MARGIN_RATIO,
            "labels": labels,
            "exclusions": exclusions,
            "images": image_payloads,
        }
        package_hash = sha256(
            json.dumps(hash_payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        manifest = {
            **hash_payload,
            **counts,
            "export_format": ORIENTATION_EXPORT_FORMAT,
            "package_hash": package_hash,
        }
        (package_dir / "labels.jsonl").write_text(
            "".join(json.dumps(label, sort_keys=True, default=str) + "\n" for label in labels),
            encoding="utf-8",
        )
        (package_dir / "exclusions.jsonl").write_text(
            "".join(
                json.dumps(exclusion, sort_keys=True, default=str) + "\n"
                for exclusion in exclusions
            ),
            encoding="utf-8",
        )
        (package_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        self._write_orientation_contact_sheet(package_dir=package_dir, labels=labels)
        return {**counts, "package_hash": package_hash}

    def _orientation_exclusion_reason(self, item, ellipse) -> str | None:
        if item.dataset_role == DatasetRole.benchmark:
            return "benchmark_protected"
        if item.dataset_role not in {DatasetRole.training, DatasetRole.validation}:
            return "unsupported_dataset_role"
        if ellipse.annotation_type == AnnotationType.partial_visible_bee:
            return "partial_visible_bee_deferred"
        if ellipse.annotation_type != AnnotationType.complete_visible_bee:
            return "unsupported_annotation_type"
        if str(ellipse.orientation_reliability) != "reliable":
            return "orientation_unreliable"
        return None

    def _orientation_exclusion_entry(self, *, item, ellipse, reason: str) -> dict[str, object]:
        return {
            "dataset_item_id": str(item.dataset_item_id),
            "training_crop_id": str(item.training_crop_id),
            "inspection_photo_id": str(item.inspection_photo_id),
            "annotation_id": str(ellipse.annotation_id),
            "dataset_role": item.dataset_role,
            "annotation_type": ellipse.annotation_type,
            "orientation_reliability": ellipse.orientation_reliability,
            "reason": reason,
        }

    def _orientation_head_up_image(self, source_image: Image.Image, ellipse) -> Image.Image:
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

    def _write_orientation_contact_sheet(
        self,
        *,
        package_dir: Path,
        labels: list[dict[str, object]],
    ) -> None:
        rows = [
            "# Bee Orientation package contact sheet",
            "",
            "No predictive model training was performed; this fake adapter validates the package only.",
            "",
            "| Split | Label | Preview |",
            "| --- | --- | --- |",
        ]
        for label in labels[:12]:
            image_bytes = (package_dir / str(label["image_path"])).read_bytes()
            encoded = base64.b64encode(image_bytes).decode("ascii")
            rows.append(
                f"| {label['split']} | {label['label']} | "
                f"![{label['label']}](data:image/png;base64,{encoded}) |"
            )
        (package_dir / "contact-sheet.md").write_text("\n".join(rows), encoding="utf-8")

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
                    "This Marked-Bee Dataset Version is shared source evidence for Bee Detection and Bee Orientation training baselines.",
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
        if training_run.model_purpose == "bee_orientation":
            training_note = (
                "No predictive model training was performed; this fake adapter validates the Bee Orientation package only."
                if not training_run.metrics_summary.get("predictive_training_performed")
                else (
                    "Predictive Bee Orientation training was performed. Validation metrics "
                    "are training-run validation only, not benchmark evidence, not user-facing "
                    "orientation readiness, and not Varroa Assessment readiness."
                )
            )
            body = [
                f"# Training Run {training_run.human_readable_id}",
                "",
                f"Dataset Version: {dataset_version.human_readable_id}",
                f"Database purpose: {training_run.database_purpose}",
                f"Adapter: {training_run.adapter_type}",
                f"Model Candidate: {candidate.human_readable_id}",
                f"Promotion status: {candidate.promotion_status}",
                "",
                training_note,
                "",
                "Classes: head_up, head_down",
                "",
                "## Metrics",
                json.dumps(training_run.metrics_summary, indent=2, sort_keys=True),
            ]
        else:
            body = [
                f"# Training Run {training_run.human_readable_id}",
                "",
                f"Dataset Version: {dataset_version.human_readable_id}",
                f"Database purpose: {training_run.database_purpose}",
                f"Adapter: {training_run.adapter_type}",
                f"Model Candidate: {candidate.human_readable_id}",
                f"Promotion status: {candidate.promotion_status}",
                "",
                "This run trains Bee Localisation only. It is not Varroa assessment, not production suitable, and not a user-facing Model Version.",
                "",
                "## Metrics",
                json.dumps(training_run.metrics_summary, indent=2, sort_keys=True),
            ]
        report_path.write_text(
            "\n".join(body),
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
