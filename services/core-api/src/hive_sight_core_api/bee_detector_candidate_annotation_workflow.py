from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from io import BytesIO
from math import degrees
from pathlib import Path
from collections.abc import Callable
from typing import Any, Protocol
from uuid import UUID

from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    AnnotationType,
    BeeAnnotationProposalListResponse,
    BeeAnnotationProposalRequest,
    BeeAnnotationProposalResponse,
    CoordinateSpace,
    ModelCandidateResponse,
    TrainingCropResponse,
    TrainingCropReviewStatus,
)


@dataclass(frozen=True)
class BeeAnnotationSuggestion:
    center_x: float
    center_y: float
    radius_x: float
    radius_y: float
    rotation_degrees: float
    confidence: float
    raw_model_class: str
    raw_yolo_obb: list[float]


class BeeDetectorInferenceAdapter(Protocol):
    adapter_type: str

    def check_available(self) -> bool:
        ...

    def suggest_bees(
        self,
        *,
        crop_png: bytes,
        crop: TrainingCropResponse,
        model_artifact_path: Path,
        confidence_threshold: float,
        max_suggestions: int,
    ) -> list[BeeAnnotationSuggestion]:
        ...


class FakeBeeDetectorInferenceAdapter:
    adapter_type = "fake"

    def check_available(self) -> bool:
        return True

    def suggest_bees(
        self,
        *,
        crop_png: bytes,
        crop: TrainingCropResponse,
        model_artifact_path: Path,
        confidence_threshold: float,
        max_suggestions: int,
    ) -> list[BeeAnnotationSuggestion]:
        _ = crop_png, model_artifact_path
        candidates = [
            BeeAnnotationSuggestion(
                center_x=crop.crop_x + crop.crop_width * 0.35,
                center_y=crop.crop_y + crop.crop_height * 0.45,
                radius_x=max(12, crop.crop_width * 0.08),
                radius_y=max(8, crop.crop_height * 0.04),
                rotation_degrees=18,
                confidence=0.84,
                raw_model_class="bee",
                raw_yolo_obb=[
                    crop.crop_width * 0.35,
                    crop.crop_height * 0.45,
                    crop.crop_width * 0.16,
                    crop.crop_height * 0.08,
                    18,
                ],
            ),
            BeeAnnotationSuggestion(
                center_x=crop.crop_x + crop.crop_width * 0.65,
                center_y=crop.crop_y + crop.crop_height * 0.55,
                radius_x=max(12, crop.crop_width * 0.07),
                radius_y=max(8, crop.crop_height * 0.035),
                rotation_degrees=-24,
                confidence=0.62,
                raw_model_class="bee",
                raw_yolo_obb=[
                    crop.crop_width * 0.65,
                    crop.crop_height * 0.55,
                    crop.crop_width * 0.14,
                    crop.crop_height * 0.07,
                    -24,
                ],
            ),
        ]
        return [
            candidate
            for candidate in candidates
            if candidate.confidence >= confidence_threshold
        ][:max_suggestions]


class UltralyticsYoloObbInferenceAdapter:
    adapter_type = "ultralytics_yolo_obb"

    def __init__(self, device: str = "cpu") -> None:
        self.device = device

    def check_available(self) -> bool:
        try:
            import ultralytics  # noqa: F401
        except ImportError:
            return False
        return True

    def suggest_bees(
        self,
        *,
        crop_png: bytes,
        crop: TrainingCropResponse,
        model_artifact_path: Path,
        confidence_threshold: float,
        max_suggestions: int,
    ) -> list[BeeAnnotationSuggestion]:
        try:
            from PIL import Image
            from ultralytics import YOLO
        except ImportError as exc:
            raise DomainError(
                "real_adapter_unavailable",
                "Run pnpm model:setup:bee before using the real Bee Localisation inference adapter.",
                409,
            ) from exc
        if not model_artifact_path.exists():
            raise DomainError(
                "model_candidate_artifact_missing",
                "The selected Model Candidate weights artifact is missing from local storage.",
                404,
            )
        image = Image.open(BytesIO(crop_png)).convert("RGB")
        model = YOLO(str(model_artifact_path))
        results = model.predict(
            source=image,
            conf=confidence_threshold,
            device=self.device,
            task="obb",
            verbose=False,
        )
        suggestions: list[BeeAnnotationSuggestion] = []
        for result in results:
            obb = getattr(result, "obb", None)
            if obb is None:
                continue
            xywhr_rows = getattr(obb, "xywhr", None)
            xyxyxyxy_rows = getattr(obb, "xyxyxyxy", None)
            confidences = getattr(obb, "conf", None)
            classes = getattr(obb, "cls", None)
            if xywhr_rows is None or confidences is None:
                continue
            for index, row in enumerate(xywhr_rows):
                values = _tensor_row(row)
                if len(values) < 5:
                    continue
                confidence = float(_tensor_row(confidences[index])[0])
                if confidence < confidence_threshold:
                    continue
                class_id = int(_tensor_row(classes[index])[0]) if classes is not None else 0
                raw_points = (
                    _tensor_row(xyxyxyxy_rows[index])
                    if xyxyxyxy_rows is not None
                    else [float(value) for value in values]
                )
                suggestions.append(
                    BeeAnnotationSuggestion(
                        center_x=crop.crop_x + float(values[0]),
                        center_y=crop.crop_y + float(values[1]),
                        radius_x=max(float(values[2]) / 2, 1),
                        radius_y=max(float(values[3]) / 2, 1),
                        rotation_degrees=degrees(float(values[4])),
                        confidence=confidence,
                        raw_model_class=f"class_{class_id}",
                        raw_yolo_obb=[float(value) for value in raw_points],
                    )
                )
        suggestions.sort(key=lambda suggestion: suggestion.confidence, reverse=True)
        return suggestions[:max_suggestions]


class BeeDetectorCandidateAnnotationWorkflow:
    def __init__(
        self,
        *,
        store: InMemoryProductDataStore,
        image_loader: Callable[[str], bytes | None],
        artifact_root: Path,
        adapter: BeeDetectorInferenceAdapter,
    ) -> None:
        self.store = store
        self.image_loader = image_loader
        self.artifact_root = artifact_root
        self.adapter = adapter

    def suggest_bee_annotations(
        self,
        *,
        user: UserContext,
        training_crop_id: UUID,
        request: BeeAnnotationProposalRequest,
    ) -> BeeAnnotationProposalListResponse:
        self._require_curator(user=user, workspace_id=request.workspace_id)
        crop = self.store.require_training_crop(
            user=user,
            workspace_id=request.workspace_id,
            training_crop_id=training_crop_id,
        )
        if crop.review_status != TrainingCropReviewStatus.review_pending:
            raise DomainError(
                "training_crop_not_editable",
                "Model Candidate pre-labelling can run only on editable Training Crops.",
                409,
            )
        candidate = self._require_model_candidate(
            workspace_id=request.workspace_id,
            model_candidate_id=request.model_candidate_id,
        )
        training_run = self.store.get_training_run(request.workspace_id, candidate.training_run_id)
        if training_run is None or training_run.status != "completed":
            raise DomainError(
                "model_candidate_training_run_not_completed",
                "The selected Model Candidate must come from a completed Training Run.",
                409,
            )
        dataset_version = self.store.get_dataset_version(
            request.workspace_id,
            training_run.dataset_version_id,
        )
        if dataset_version is None:
            raise DomainError(
                "model_candidate_dataset_version_missing",
                "The selected Model Candidate's Dataset Version is missing.",
                409,
            )
        dataset_item = self.store.get_dataset_item_for_training_crop(crop.training_crop_id)
        if dataset_item is not None and dataset_item.dataset_item_id in {
            *dataset_version.included_dataset_item_ids,
            *dataset_version.protected_benchmark_dataset_item_ids,
        }:
            raise DomainError(
                "crop_in_candidate_dataset_version",
                "The selected Model Candidate cannot pre-label a crop included in its own frozen Dataset Version.",
                409,
            )
        artifact = self.store.get_artifact(candidate.artifact_id)
        if artifact is None:
            raise DomainError(
                "model_candidate_artifact_missing",
                "The selected Model Candidate weights artifact is missing.",
                404,
            )
        artifact_path = self._artifact_path(artifact.relative_path)
        photo = self.store.get_inspection_photo(crop.inspection_photo_id)
        if photo is None or photo.workspace_id != request.workspace_id:
            raise DomainError("inspection_photo_not_found", "Inspection Photo not found.", 404)
        image_bytes = self.image_loader(photo.original_object_key)
        if image_bytes is None:
            raise DomainError(
                "training_crop_image_missing",
                "The Training Crop source image content is not available.",
                404,
            )
        crop_png = _render_crop_png(image_bytes=image_bytes, crop=crop)
        suggestions = self.adapter.suggest_bees(
            crop_png=crop_png,
            crop=crop,
            model_artifact_path=artifact_path,
            confidence_threshold=request.confidence_threshold,
            max_suggestions=request.max_suggestions,
        )
        suggestions.sort(key=lambda suggestion: suggestion.confidence, reverse=True)
        response_suggestions = [
            _proposal_response(
                suggestion=suggestion,
                workspace_id=request.workspace_id,
                training_crop_id=training_crop_id,
                candidate=candidate,
                threshold=request.confidence_threshold,
            )
            for suggestion in suggestions[: request.max_suggestions]
        ]
        return BeeAnnotationProposalListResponse(
            workspace_id=request.workspace_id,
            training_crop_id=training_crop_id,
            model_candidate_id=candidate.model_candidate_id,
            model_candidate_human_readable_id=candidate.human_readable_id,
            threshold=request.confidence_threshold,
            suggestions=response_suggestions,
            caveat=(
                "Model Candidate proposals are transient review aids. They become dataset evidence "
                "only when a Dataset Curator accepts them into reviewed Training Crop ellipses."
            ),
        )

    def _require_curator(self, *, user: UserContext, workspace_id: UUID) -> None:
        self.store.require_workspace_access(user, workspace_id)
        self.store.require_data_use_agreement(workspace_id)
        self.store.require_dataset_curator_capability(user)

    def _require_model_candidate(
        self,
        *,
        workspace_id: UUID,
        model_candidate_id: UUID | None,
    ) -> ModelCandidateResponse:
        if model_candidate_id is not None:
            candidate = self.store.get_model_candidate(workspace_id, model_candidate_id)
            if candidate is None:
                raise DomainError(
                    "model_candidate_not_found",
                    "The selected Model Candidate was not found in this Workspace.",
                    404,
                )
            return candidate
        candidates = [
            candidate
            for candidate in self.store.list_model_candidates(workspace_id)
            if candidate.status == "created" and candidate.model_purpose == "bee_detector"
        ]
        if not candidates:
            raise DomainError(
                "model_candidate_required",
                "Create a completed Bee Detector Model Candidate before requesting crop pre-labels.",
                409,
            )
        return candidates[0]

    def _artifact_path(self, relative_path: str) -> Path:
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise DomainError("artifact_path_invalid", "Artifact path is invalid.", 500)
        return self.artifact_root / relative


def _render_crop_png(*, image_bytes: bytes, crop: TrainingCropResponse) -> bytes:
    try:
        from PIL import Image
    except ImportError as exc:
        raise DomainError(
            "image_renderer_unavailable",
            "Pillow is required to render Training Crop images for model pre-labelling.",
            500,
        ) from exc
    try:
        source_image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        raise DomainError(
            "source_image_unreadable",
            "The Training Crop source image could not be read.",
            422,
        ) from exc
    crop_box = (
        crop.crop_x,
        crop.crop_y,
        crop.crop_x + crop.crop_width,
        crop.crop_y + crop.crop_height,
    )
    if crop_box[2] > source_image.width or crop_box[3] > source_image.height:
        raise DomainError(
            "training_crop_outside_source_image",
            "The Training Crop cannot be rendered from the available source image dimensions.",
            409,
        )
    output = BytesIO()
    source_image.crop(crop_box).save(output, format="PNG")
    return output.getvalue()


def _proposal_response(
    *,
    suggestion: BeeAnnotationSuggestion,
    workspace_id: UUID,
    training_crop_id: UUID,
    candidate: ModelCandidateResponse,
    threshold: float,
) -> BeeAnnotationProposalResponse:
    stable_key = "|".join(
        [
            str(candidate.model_candidate_id),
            str(training_crop_id),
            f"{suggestion.center_x:.2f}",
            f"{suggestion.center_y:.2f}",
            f"{suggestion.confidence:.4f}",
        ]
    )
    return BeeAnnotationProposalResponse(
        proposal_id=f"proposal-{sha1(stable_key.encode('utf-8')).hexdigest()[:12]}",
        workspace_id=workspace_id,
        training_crop_id=training_crop_id,
        model_candidate_id=candidate.model_candidate_id,
        model_candidate_human_readable_id=candidate.human_readable_id,
        annotation_type=AnnotationType.complete_visible_bee,
        center_x=suggestion.center_x,
        center_y=suggestion.center_y,
        radius_x=suggestion.radius_x,
        radius_y=suggestion.radius_y,
        rotation_degrees=suggestion.rotation_degrees,
        coordinate_space=CoordinateSpace.source_image_pixels,
        confidence=suggestion.confidence,
        threshold=threshold,
        raw_model_class=suggestion.raw_model_class,
        raw_yolo_obb=suggestion.raw_yolo_obb,
    )


def _tensor_row(value: Any) -> list[float]:
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, list):
        if value and isinstance(value[0], list):
            return [float(item) for item in value[0]]
        return [float(item) for item in value]
    return [float(value)]
