from functools import lru_cache

from hive_sight_core_api.analysis_request_workflow import AnalysisRequestWorkflow
from hive_sight_core_api.inspection_photo_access import InspectionPhotoAccess
from hive_sight_core_api.settings import Settings, load_settings


@lru_cache
def get_settings() -> Settings:
    return load_settings()


def get_inspection_photo_access() -> InspectionPhotoAccess:
    settings = get_settings()
    return InspectionPhotoAccess(
        object_storage_endpoint=settings.object_storage_endpoint,
        object_storage_bucket=settings.object_storage_bucket,
    )


def get_analysis_request_workflow() -> AnalysisRequestWorkflow:
    return AnalysisRequestWorkflow()

