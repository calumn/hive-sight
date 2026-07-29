from dataclasses import dataclass

from hive_sight_analysis_service.models import ModelAnalysis


@dataclass(frozen=True)
class ModelRuntime:
    default_model_version: str

    def analyse_photo(
        self,
        original_object_key: str,
        requested_model_version: str | None = None,
    ) -> ModelAnalysis:
        model_version = requested_model_version or self.default_model_version

        return ModelAnalysis(
            model_version=model_version,
            complete_visible_bee_count=48,
            partial_visible_bee_count=3,
            likely_varroa_detections=1,
            tagged_image_object_key=None,
        )
