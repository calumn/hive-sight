from collections.abc import Callable
from datetime import UTC, datetime
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from hive_sight_core_api.analysis_processing_workflow import (
    AnalysisProcessingWorkflow,
    DeterministicStubAnalysisExecutor,
)
from hive_sight_core_api.analysis_request_workflow import AnalysisRequestWorkflow
from hive_sight_core_api.dev_store import (
    DevState,
    InMemoryEventRecorder,
    InMemoryObjectStorage,
    InMemoryProductDataStore,
    UploadPolicy,
    deterministic_id_factory,
)
from hive_sight_core_api.inspection_photo_access import InspectionPhotoAccess
from hive_sight_core_api.settings import Settings, load_settings


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
