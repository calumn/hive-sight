from collections.abc import Callable
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from hive_sight_core_api.analysis_processing_workflow import (
    AnalysisProcessingWorkflow,
    DeterministicStubAnalysisExecutor,
)
from hive_sight_core_api.analysis_request_workflow import AnalysisRequestWorkflow
from hive_sight_core_api.bee_detector_candidate_annotation_workflow import (
    BeeDetectorCandidateAnnotationWorkflow,
    FakeBeeDetectorInferenceAdapter,
    UltralyticsYoloObbInferenceAdapter,
)
from hive_sight_core_api.bee_detector_training_workflow import (
    BeeDetectorTrainingWorkflow,
    FakeBeeDetectorTrainingAdapter,
    UltralyticsYoloObbTrainingAdapter,
)
from hive_sight_core_api.dataset_labelling_workflow import (
    BeePrelabeler,
    DatasetLabellingWorkflow,
    DeterministicBeePrelabeler,
)
from hive_sight_core_api.dataset_repository_workflow import DatasetRepositoryWorkflow
from hive_sight_core_api.dataset_role_assignment_workflow import DatasetRoleAssignmentWorkflow
from hive_sight_core_api.dev_store import (
    DevState,
    FileSystemObjectStorage,
    InMemoryEventRecorder,
    InMemoryObjectStorage,
    InMemoryProductDataStore,
    UploadPolicy,
    deterministic_id_factory,
)
from hive_sight_core_api.hive_configuration_workflow import HiveConfigurationWorkflow
from hive_sight_core_api.inspection_photo_access import InspectionPhotoAccess
from hive_sight_core_api.settings import Settings, load_settings
from hive_sight_core_api.training_crop_dataset_item_workflow import (
    TrainingCropDatasetItemWorkflow,
)
from hive_sight_core_api.training_crop_workflow import TrainingCropWorkflow

DEFAULT_DATASET_EXPORT_ROOT = Path(__file__).resolve().parents[4] / "var" / "exports" / "datasets"
DEFAULT_MODEL_ARTIFACT_ROOT = Path(__file__).resolve().parents[4] / "var" / "model-runs"


@lru_cache
def get_settings() -> Settings:
    return load_settings()


@lru_cache
def get_dev_state() -> DevState:
    return build_dev_state()


def build_dev_state(
    id_values: list[UUID] | None = None,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    max_upload_size_bytes: int = 15 * 1024 * 1024,
    dataset_export_root: Path = DEFAULT_DATASET_EXPORT_ROOT,
    model_artifact_root: Path | None = None,
) -> DevState:
    id_factory = deterministic_id_factory(id_values) if id_values is not None else None
    settings = get_settings()
    resolved_id_factory = id_factory or deterministic_id_factory([])
    if settings.persistence_backend == "postgres":
        from hive_sight_core_api.postgres_store import PostgresProductDataStore

        store = PostgresProductDataStore(
            database_url=settings.database_url,
            id_factory=resolved_id_factory,
            clock=clock,
        )
    else:
        store = InMemoryProductDataStore(
            id_factory=resolved_id_factory,
            clock=clock,
        )
    return DevState(
        store=store,
        object_storage=_object_storage(settings),
        event_recorder=InMemoryEventRecorder(),
        upload_policy=UploadPolicy(max_size_bytes=max_upload_size_bytes),
        dataset_export_root=dataset_export_root,
        model_artifact_root=model_artifact_root or _model_artifact_root(settings),
    )


DevStateDep = Annotated[DevState, Depends(get_dev_state)]


def get_analysis_request_workflow(state: DevStateDep) -> AnalysisRequestWorkflow:
    return AnalysisRequestWorkflow(
        store=state.store,
        event_recorder=state.event_recorder,
        id_factory=state.store.id_factory,
        clock=state.store.clock,
    )


def get_analysis_processing_workflow(state: DevStateDep) -> AnalysisProcessingWorkflow:
    return AnalysisProcessingWorkflow(
        store=state.store,
        executor=DeterministicStubAnalysisExecutor(clock=state.store.clock),
        clock=state.store.clock,
    )


def get_dataset_labelling_workflow(state: DevStateDep) -> DatasetLabellingWorkflow:
    settings = get_settings()
    return DatasetLabellingWorkflow(
        store=state.store,
        prelabeler=build_bee_prelabeler(settings),
        image_loader=state.object_storage.get_object,
        clock=state.store.clock,
    )


def build_bee_prelabeler(settings: Settings) -> BeePrelabeler:
    if settings.prelabeler == "deterministic":
        return DeterministicBeePrelabeler()
    raise ValueError(f"Unknown HiveSight pre-labeller provider: {settings.prelabeler}")


def get_dataset_role_assignment_workflow(
    state: DevStateDep,
) -> DatasetRoleAssignmentWorkflow:
    return DatasetRoleAssignmentWorkflow(store=state.store)


def get_hive_configuration_workflow(state: DevStateDep) -> HiveConfigurationWorkflow:
    return HiveConfigurationWorkflow(store=state.store)


def get_training_crop_workflow(state: DevStateDep) -> TrainingCropWorkflow:
    return TrainingCropWorkflow(store=state.store)


def get_training_crop_dataset_item_workflow(
    state: DevStateDep,
) -> TrainingCropDatasetItemWorkflow:
    return TrainingCropDatasetItemWorkflow(store=state.store)


def get_dataset_repository_workflow(state: DevStateDep) -> DatasetRepositoryWorkflow:
    settings = get_settings()
    return DatasetRepositoryWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        persistence_backend=settings.persistence_backend,
        database_purpose=settings.database_purpose,
    )


def get_inspection_photo_access(state: DevStateDep) -> InspectionPhotoAccess:
    settings = get_settings()
    analysis_workflow = AnalysisRequestWorkflow(
        store=state.store,
        event_recorder=state.event_recorder,
        id_factory=state.store.id_factory,
        clock=state.store.clock,
    )
    return InspectionPhotoAccess(
        object_storage_endpoint=settings.object_storage_endpoint,
        object_storage_bucket=settings.object_storage_bucket,
        store=state.store,
        object_storage=state.object_storage,
        analysis_workflow=analysis_workflow,
        upload_policy=state.upload_policy,
    )


def get_bee_detector_training_workflow(state: DevStateDep) -> BeeDetectorTrainingWorkflow:
    settings = get_settings()
    adapter = (
        UltralyticsYoloObbTrainingAdapter(
            base_weights=settings.yolo_base_weights,
            device=settings.yolo_device,
        )
        if settings.bee_detector_training_adapter == "ultralytics_yolo_obb"
        else FakeBeeDetectorTrainingAdapter()
    )
    return BeeDetectorTrainingWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        artifact_root=state.model_artifact_root,
        adapter=adapter,
        persistence_backend=settings.persistence_backend,
        database_purpose=settings.database_purpose,
        clock=state.store.clock,
        stale_after_seconds=settings.training_run_stale_after_seconds,
        heartbeat_interval_seconds=settings.training_run_heartbeat_interval_seconds,
    )


def get_bee_detector_candidate_annotation_workflow(
    state: DevStateDep,
) -> BeeDetectorCandidateAnnotationWorkflow:
    settings = get_settings()
    adapter = (
        UltralyticsYoloObbInferenceAdapter(device=settings.yolo_device)
        if settings.bee_detector_training_adapter == "ultralytics_yolo_obb"
        else FakeBeeDetectorInferenceAdapter()
    )
    return BeeDetectorCandidateAnnotationWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        artifact_root=state.model_artifact_root,
        adapter=adapter,
    )


def _model_artifact_root(settings: Settings) -> Path:
    configured = Path(settings.model_artifact_root)
    if configured.is_absolute():
        return configured
    return Path(__file__).resolve().parents[4] / configured


def _object_storage(settings: Settings) -> InMemoryObjectStorage | FileSystemObjectStorage:
    if settings.persistence_backend != "postgres":
        return InMemoryObjectStorage()
    configured = Path(settings.object_storage_root)
    root = configured if configured.is_absolute() else Path(__file__).resolve().parents[4] / configured
    return FileSystemObjectStorage(root=root)
