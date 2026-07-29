from dataclasses import dataclass
from io import BytesIO
from typing import Protocol

from hive_sight_core_api.dataset_labelling_workflow import PrelabellingRequest, PrelabellingResult
from hive_sight_core_api.models import AnnotationCreate


@dataclass(frozen=True)
class GroundingDinoDetection:
    label: str
    score: float
    x_min_px: float
    y_min_px: float
    x_max_px: float
    y_max_px: float


class GroundingDinoRunner(Protocol):
    def detect(
        self,
        request: PrelabellingRequest,
        prompt_text: str,
        box_threshold: float,
        text_threshold: float,
    ) -> list[GroundingDinoDetection]:
        """Run local Grounding DINO detection for one image."""


@dataclass(frozen=True)
class UnavailableGroundingDinoRunner:
    checkpoint_id: str | None

    def detect(
        self,
        request: PrelabellingRequest,
        prompt_text: str,
        box_threshold: float,
        text_threshold: float,
    ) -> list[GroundingDinoDetection]:
        raise RuntimeError("Grounding DINO runtime or checkpoint is not available locally.")


@dataclass
class TransformersGroundingDinoRunner:
    model_id: str
    device: str = "auto"
    local_files_only: bool = False

    _processor: object | None = None
    _model: object | None = None
    _resolved_device: str | None = None

    def detect(
        self,
        request: PrelabellingRequest,
        prompt_text: str,
        box_threshold: float,
        text_threshold: float,
    ) -> list[GroundingDinoDetection]:
        if request.image_bytes is None:
            raise RuntimeError("Inspection Photo bytes are not available for Grounding DINO.")

        try:
            import torch
            from PIL import Image
            from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor
        except ImportError as exc:
            raise RuntimeError(
                "Install the Core API grounding-dino optional dependencies before using "
                "HIVESIGHT_PRELABELER=grounding_dino."
            ) from exc

        processor, model, device = self._load_model(
            torch=torch,
            auto_processor=AutoProcessor,
            auto_model=AutoModelForZeroShotObjectDetection,
        )
        image = Image.open(BytesIO(request.image_bytes)).convert("RGB")
        text_labels = [_prompt_labels(prompt_text)]
        inputs = processor(images=image, text=text_labels, return_tensors="pt")
        inputs = {key: value.to(device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)

        results = processor.post_process_grounded_object_detection(
            outputs,
            threshold=box_threshold,
            text_threshold=text_threshold,
            target_sizes=[(image.height, image.width)],
            text_labels=text_labels,
        )[0]

        labels = results.get("text_labels") or results.get("labels") or []
        return [
            GroundingDinoDetection(
                label=str(label),
                score=float(score.detach().cpu().item() if hasattr(score, "detach") else score),
                x_min_px=float(box[0]),
                y_min_px=float(box[1]),
                x_max_px=float(box[2]),
                y_max_px=float(box[3]),
            )
            for box, score, label in zip(results["boxes"], results["scores"], labels, strict=False)
        ]

    def _load_model(self, torch, auto_processor, auto_model):
        if self._processor is not None and self._model is not None and self._resolved_device:
            return self._processor, self._model, self._resolved_device

        device = _resolve_device(torch, self.device)
        processor = auto_processor.from_pretrained(
            self.model_id,
            local_files_only=self.local_files_only,
        )
        model = auto_model.from_pretrained(
            self.model_id,
            local_files_only=self.local_files_only,
        ).to(device)
        model.eval()
        self._processor = processor
        self._model = model
        self._resolved_device = device
        return processor, model, device


@dataclass(frozen=True)
class GroundingDinoBeePrelabeler:
    runner: GroundingDinoRunner
    model_id: str
    checkpoint_id: str | None
    prompt_text: str = "honey bee . partial honey bee"
    box_threshold: float = 0.35
    text_threshold: float = 0.25
    max_box_area_ratio: float = 0.04
    name: str = "grounding-dino-bee-prelabeler"
    version: str = "0.1.0"
    provider: str = "grounding_dino"
    adapter_version: str = "0.1.0"
    runtime_mode: str = "local"

    def create_draft_annotations(self, request: PrelabellingRequest) -> PrelabellingResult:
        detections = self.runner.detect(
            request=request,
            prompt_text=self.prompt_text,
            box_threshold=self.box_threshold,
            text_threshold=self.text_threshold,
        )
        return PrelabellingResult(
            prelabeler_name=self.name,
            prelabeler_version=self.version,
            provider=self.provider,
            adapter_version=self.adapter_version,
            model_id=self.model_id,
            checkpoint_id=self.checkpoint_id,
            prompt_text=self.prompt_text,
            box_threshold=self.box_threshold,
            text_threshold=self.text_threshold,
            runtime_mode=self.runtime_mode,
            annotations=[
                annotation
                for detection in detections
                if (annotation := self._to_annotation(detection, request)) is not None
            ],
        )

    def _to_annotation(
        self,
        detection: GroundingDinoDetection,
        request: PrelabellingRequest,
    ) -> AnnotationCreate | None:
        annotation_type = _annotation_type_for_label(detection.label)
        if annotation_type is None or detection.score < self.box_threshold:
            return None

        image_width = max(request.source_image_width_px, 1)
        image_height = max(request.source_image_height_px, 1)
        x_min = min(max(detection.x_min_px, 0), image_width)
        y_min = min(max(detection.y_min_px, 0), image_height)
        x_max = min(max(detection.x_max_px, x_min), image_width)
        y_max = min(max(detection.y_max_px, y_min), image_height)
        width = x_max - x_min
        height = y_max - y_min
        if width <= 0 or height <= 0:
            return None
        if (width * height) / (image_width * image_height) > self.max_box_area_ratio:
            return None

        return AnnotationCreate(
            annotation_type=annotation_type,
            x=x_min / image_width,
            y=y_min / image_height,
            width=width / image_width,
            height=height / image_height,
            coordinate_space="normalized",
            source_image_width_px=image_width,
            source_image_height_px=image_height,
            confidence=detection.score,
            source="ai_assisted_draft",
        )


def _annotation_type_for_label(label: str) -> str | None:
    normalized = label.casefold()
    if "bee" not in normalized:
        return None
    if "partial" in normalized:
        return "partial_visible_bee"
    return "complete_visible_bee"


def _prompt_labels(prompt_text: str) -> list[str]:
    labels = [label.strip() for label in prompt_text.split(".") if label.strip()]
    return labels or ["honey bee"]


def _resolve_device(torch, requested_device: str) -> str:
    if requested_device != "auto":
        return requested_device
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"
