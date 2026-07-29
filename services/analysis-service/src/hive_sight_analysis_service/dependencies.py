from functools import lru_cache

from hive_sight_analysis_service.analysis_job_runner import AnalysisJobRunner
from hive_sight_analysis_service.model_runtime import ModelRuntime
from hive_sight_analysis_service.settings import Settings, load_settings


@lru_cache
def get_settings() -> Settings:
    return load_settings()


def get_model_runtime() -> ModelRuntime:
    settings = get_settings()
    return ModelRuntime(default_model_version=settings.model_version)


def get_analysis_job_runner() -> AnalysisJobRunner:
    return AnalysisJobRunner(model_runtime=get_model_runtime())

