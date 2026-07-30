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
from hive_sight_core_api.dataset_labelling_workflow import (
    BeePrelabeler,
    DatasetLabellingWorkflow,
    DeterministicBeePrelabeler,
)
from hive_sight_core_api.dataset_role_assignment_workflow import DatasetRoleAssignmentWorkflow
from hive_sight_core_api.dev_store import (
    DevState,
    InMemoryEventRecorder,
    InMemoryObjectStorage,
    InMemoryProductDataStore,
    UploadPolicy,
    deterministic_id_factory,
)
from hive_sight_core_api.grounding_dino_prelabeler import (
    GroundingDinoBeePrelabeler,
    TransformersGroundingDinoRunner,
)
from hive_sight_core_api.hive_configuration_workflow import HiveConfigurationWorkflow
from hive_sight_core_api.inspection_photo_access import InspectionPhotoAccess
from hive_sight_core_api.settings import Settings, load_settings
from hive_sight_core_api.training_crop_dataset_item_workflow import (
    TrainingCropDatasetItemWorkflow,
)
from hive_sight_core_api.training_crop_workflow import TrainingCropWorkflow

DEFAULT_DATASET_EXPORT_ROOT = Path(__file__).resolve().parents[4] / "var" / "exports" / "datasets"


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
) -> DevState:
    id_factory = deterministic_id_factory(id_values) if id_values is not None else None
    store = InMemoryProductDataStore(
        id_factory=id_factory or deterministic_id_factory([]),
        clock=clock,
    )
    return DevState(
        store=store,
        object_storage=InMemoryObjectStorage(),
        event_recorder=InMemoryEventRecorder(),
        upload_policy=UploadPolicy(max_size_bytes=max_upload_size_bytes),
        dataset_export_root=dataset_export_root,
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
    if settings.prelabeler == "grounding_dino":
        checkpoint_id = settings.grounding_dino_checkpoint or None
        return GroundingDinoBeePrelabeler(
            runner=TransformersGroundingDinoRunner(
                model_id=settings.grounding_dino_model_id,
                device=settings.grounding_dino_device,
                local_files_only=settings.grounding_dino_local_files_only,
            ),
            model_id=settings.grounding_dino_model_id,
            checkpoint_id=checkpoint_id,
            prompt_text=settings.grounding_dino_prompt,
            box_threshold=settings.grounding_dino_box_threshold,
            text_threshold=settings.grounding_dino_text_threshold,
            max_box_area_ratio=settings.grounding_dino_max_box_area_ratio,
        )
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
