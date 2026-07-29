from dataclasses import dataclass

from hive_sight_analysis_service.models import ModelAnalysis, ModelAnnotation


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
            complete_visible_bee_count=3,
            partial_visible_bee_count=1,
            likely_varroa_detections=0,
            tagged_image_object_key=None,
            annotations=[
                ModelAnnotation(
                    annotation_type="complete_visible_bee",
                    x=0.12,
                    y=0.18,
                    width=0.16,
                    height=0.22,
                    coordinate_space="normalized",
                    source_image_width_px=1600,
                    source_image_height_px=1200,
                    confidence=0.92,
                    source="deterministic_stub",
                ),
                ModelAnnotation(
                    annotation_type="complete_visible_bee",
                    x=0.46,
                    y=0.2,
                    width=0.18,
                    height=0.24,
                    coordinate_space="normalized",
                    source_image_width_px=1600,
                    source_image_height_px=1200,
                    confidence=0.89,
                    source="deterministic_stub",
                ),
                ModelAnnotation(
                    annotation_type="complete_visible_bee",
                    x=0.64,
                    y=0.52,
                    width=0.17,
                    height=0.22,
                    coordinate_space="normalized",
                    source_image_width_px=1600,
                    source_image_height_px=1200,
                    confidence=0.87,
                    source="deterministic_stub",
                ),
                ModelAnnotation(
                    annotation_type="partial_visible_bee",
                    x=0.28,
                    y=0.62,
                    width=0.14,
                    height=0.18,
                    coordinate_space="normalized",
                    source_image_width_px=1600,
                    source_image_height_px=1200,
                    confidence=0.74,
                    source="deterministic_stub",
                ),
            ],
        )
