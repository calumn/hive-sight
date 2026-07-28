from dataclasses import dataclass

from beehive_analysis_service.models import ModelAnalysis


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
            complete_visible_bee_count=0,
            partial_visible_bee_count=0,
            likely_varroa_detections=0,
            tagged_image_object_key=None,
        )

