from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from hive_sight_core_api.dev_store import InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    AnnotationCreate,
    DatasetLabellingEvidenceResponse,
    DatasetLabellingSessionResponse,
    ImageQualityStatus,
    InspectionPhotoEvidenceResponse,
    PrelabelerRunResponse,
    PrelabelerRunStatus,
)


@dataclass(frozen=True)
class PrelabellingRequest:
    inspection_photo_id: UUID
    original_object_key: str
    image_bytes: bytes | None
    source_image_width_px: int
    source_image_height_px: int


@dataclass(frozen=True)
class PrelabellingResult:
    prelabeler_name: str
    prelabeler_version: str
    provider: str
    adapter_version: str
    model_id: str | None
    checkpoint_id: str | None
    prompt_text: str | None
    box_threshold: float | None
    text_threshold: float | None
    runtime_mode: str
    annotations: list[AnnotationCreate]


class BeePrelabeler(Protocol):
    name: str
    version: str
    provider: str
    adapter_version: str
    model_id: str | None
    checkpoint_id: str | None
    prompt_text: str | None
    box_threshold: float | None
    text_threshold: float | None
    runtime_mode: str

    def create_draft_annotations(self, request: PrelabellingRequest) -> PrelabellingResult:
        """Create AI-assisted draft annotations for one original image."""


@dataclass(frozen=True)
class DeterministicBeePrelabeler:
    name: str = "deterministic-bee-prelabeler"
    version: str = "0.1.0"
    provider: str = "deterministic"
    adapter_version: str = "0.1.0"
    model_id: str | None = "deterministic-fixture"
    checkpoint_id: str | None = None
    prompt_text: str | None = "deterministic complete and partial visible bee fixture"
    box_threshold: float | None = None
    text_threshold: float | None = None
    runtime_mode: str = "local"

    def create_draft_annotations(self, request: PrelabellingRequest) -> PrelabellingResult:
        image_width = max(request.source_image_width_px, 1)
        image_height = max(request.source_image_height_px, 1)
        complete_box = _normalise_box(
            x=round(image_width * 0.18),
            y=round(image_height * 0.2),
            width=round(image_width * 0.2),
            height=round(image_height * 0.24),
            image_width=image_width,
            image_height=image_height,
        )
        partial_box = _normalise_box(
            x=round(image_width * 0.58),
            y=round(image_height * 0.58),
            width=round(image_width * 0.16),
            height=round(image_height * 0.18),
            image_width=image_width,
            image_height=image_height,
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
                AnnotationCreate(
                    annotation_type="complete_visible_bee",
                    x=complete_box[0],
                    y=complete_box[1],
                    width=complete_box[2],
                    height=complete_box[3],
                    coordinate_space="normalized",
                    source_image_width_px=image_width,
                    source_image_height_px=image_height,
                    confidence=0.81,
                    source="ai_assisted_draft",
                ),
                AnnotationCreate(
                    annotation_type="partial_visible_bee",
                    x=partial_box[0],
                    y=partial_box[1],
                    width=partial_box[2],
                    height=partial_box[3],
                    coordinate_space="normalized",
                    source_image_width_px=image_width,
                    source_image_height_px=image_height,
                    confidence=0.67,
                    source="ai_assisted_draft",
                ),
            ],
        )


@dataclass(frozen=True)
class DatasetLabellingWorkflow:
    store: InMemoryProductDataStore
    prelabeler: BeePrelabeler
    image_loader: Callable[[str], bytes | None] = lambda _: None
    clock: Callable[[], datetime] = lambda: datetime.now(UTC)
    source_image_width_px: int = 1600
    source_image_height_px: int = 1200

    def start_labelling(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_photo_id: UUID,
    ) -> DatasetLabellingSessionResponse:
        photo = self.store.require_inspection_photo_for_labelling(
            user=user,
            workspace_id=workspace_id,
            inspection_photo_id=inspection_photo_id,
        )
        self.store.require_dataset_curator_capability(user)
        existing_session = self.store.existing_labelling_session_for_photo(
            workspace_id=workspace_id,
            inspection_photo_id=inspection_photo_id,
        )
        if existing_session is not None:
            return existing_session

        started_at = self.clock()
        prelabeler_run_id = self.store.id_factory()
        image_bytes = self.image_loader(photo.original_object_key)
        source_image_width_px, source_image_height_px = _source_image_size(
            image_bytes=image_bytes,
            fallback_width=self.source_image_width_px,
            fallback_height=self.source_image_height_px,
        )
        try:
            prelabelling = self.prelabeler.create_draft_annotations(
                PrelabellingRequest(
                    inspection_photo_id=photo.inspection_photo_id,
                    original_object_key=photo.original_object_key,
                    image_bytes=image_bytes,
                    source_image_width_px=source_image_width_px,
                    source_image_height_px=source_image_height_px,
                )
            )
        except Exception:  # noqa: BLE001 - adapter failures are recorded as session evidence.
            failed_run = PrelabelerRunResponse(
                prelabeler_run_id=prelabeler_run_id,
                prelabeler_name=self.prelabeler.name,
                prelabeler_version=self.prelabeler.version,
                provider=self.prelabeler.provider,
                adapter_version=self.prelabeler.adapter_version,
                model_id=self.prelabeler.model_id,
                checkpoint_id=self.prelabeler.checkpoint_id,
                prompt_text=self.prelabeler.prompt_text,
                box_threshold=self.prelabeler.box_threshold,
                text_threshold=self.prelabeler.text_threshold,
                runtime_mode=self.prelabeler.runtime_mode,
                status=PrelabelerRunStatus.failed,
                suggestion_count=0,
                started_at=started_at,
                finished_at=self.clock(),
                error_code="prelabeler_unavailable",
                error_message=(
                    "Pre-labelling helper failed before draft annotations were created."
                ),
            )
            return self.store.record_dataset_labelling_session(
                workspace_id=workspace_id,
                inspection_photo_id=photo.inspection_photo_id,
                created_by_user_id=user.user_id,
                prelabeler_run=failed_run,
                created_at=started_at,
            )

        finished_at = self.clock()
        prelabeler_run = PrelabelerRunResponse(
            prelabeler_run_id=prelabeler_run_id,
            prelabeler_name=prelabelling.prelabeler_name,
            prelabeler_version=prelabelling.prelabeler_version,
            provider=prelabelling.provider,
            adapter_version=prelabelling.adapter_version,
            model_id=prelabelling.model_id,
            checkpoint_id=prelabelling.checkpoint_id,
            prompt_text=prelabelling.prompt_text,
            box_threshold=prelabelling.box_threshold,
            text_threshold=prelabelling.text_threshold,
            runtime_mode=prelabelling.runtime_mode,
            status=PrelabelerRunStatus.succeeded,
            suggestion_count=len(prelabelling.annotations),
            started_at=started_at,
            finished_at=finished_at,
            error_code=None,
            error_message=None,
        )
        session = self.store.record_dataset_labelling_session(
            workspace_id=workspace_id,
            inspection_photo_id=photo.inspection_photo_id,
            created_by_user_id=user.user_id,
            prelabeler_run=prelabeler_run,
            created_at=started_at,
        )
        for annotation in prelabelling.annotations:
            self.store.record_dataset_labelling_annotation(
                workspace_id=workspace_id,
                inspection_photo_id=photo.inspection_photo_id,
                labelling_session_id=session.labelling_session_id,
                annotation=annotation,
                created_at=finished_at,
            )
        return session

    def update_session_metadata(
        self,
        user: UserContext,
        workspace_id: UUID,
        labelling_session_id: UUID,
        source_group_key: str | None,
        image_quality_status: ImageQualityStatus,
    ) -> DatasetLabellingSessionResponse:
        return self.store.update_labelling_session_metadata(
            user=user,
            workspace_id=workspace_id,
            labelling_session_id=labelling_session_id,
            source_group_key=source_group_key,
            image_quality_status=image_quality_status,
        )

    def get_labelling_evidence(
        self,
        user: UserContext,
        workspace_id: UUID,
        labelling_session_id: UUID,
    ) -> DatasetLabellingEvidenceResponse:
        session = self.store.require_labelling_session(
            user=user,
            workspace_id=workspace_id,
            labelling_session_id=labelling_session_id,
        )
        photo = self.store.require_inspection_photo_for_labelling(
            user=user,
            workspace_id=workspace_id,
            inspection_photo_id=session.inspection_photo_id,
        )
        annotations = self.store.get_annotations_for_labelling_session(labelling_session_id)
        source_image_width_px, source_image_height_px = _evidence_image_size(
            annotations=annotations,
            image_bytes=self.image_loader(photo.original_object_key),
            fallback_width=self.source_image_width_px,
            fallback_height=self.source_image_height_px,
        )
        reviewed_annotations = [
            annotation
            for annotation in annotations
            if annotation.latest_review_decision is not None
            and annotation.latest_review_decision.decision == "approved"
        ]
        latest_review_decisions = [
            annotation.latest_review_decision
            for annotation in annotations
            if annotation.latest_review_decision is not None
        ]
        return DatasetLabellingEvidenceResponse(
            inspection_photo=InspectionPhotoEvidenceResponse(
                inspection_photo_id=photo.inspection_photo_id,
                filename=photo.filename,
                content_type=photo.content_type,
                view_url=(
                    f"/v1/inspection-photos/{photo.inspection_photo_id}/content"
                    f"?workspace_id={workspace_id}"
                ),
                width=source_image_width_px,
                height=source_image_height_px,
            ),
            labelling_session=session,
            draft_annotations=annotations,
            reviewed_annotations=reviewed_annotations,
            latest_review_decisions=latest_review_decisions,
            dataset_item=self.store.get_dataset_item_for_labelling_session(labelling_session_id),
            caveat=(
                "AI-assisted draft annotations are machine suggestions for dataset labelling. "
                "Dataset use is not assigned automatically; it is assigned only through explicit "
                "Dataset Role assignment."
            ),
        )


def _normalise_box(
    x: int,
    y: int,
    width: int,
    height: int,
    image_width: int,
    image_height: int,
) -> tuple[float, float, float, float]:
    safe_x = min(max(x, 0), image_width - 1)
    safe_y = min(max(y, 0), image_height - 1)
    safe_width = min(max(width, 1), image_width - safe_x)
    safe_height = min(max(height, 1), image_height - safe_y)
    return (
        safe_x / image_width,
        safe_y / image_height,
        safe_width / image_width,
        safe_height / image_height,
    )


def _evidence_image_size(
    annotations: list,
    image_bytes: bytes | None,
    fallback_width: int,
    fallback_height: int,
) -> tuple[int, int]:
    if annotations:
        return (
            max(annotations[0].source_image_width_px, 1),
            max(annotations[0].source_image_height_px, 1),
        )
    return _source_image_size(
        image_bytes=image_bytes,
        fallback_width=fallback_width,
        fallback_height=fallback_height,
    )


def _source_image_size(
    image_bytes: bytes | None,
    fallback_width: int,
    fallback_height: int,
) -> tuple[int, int]:
    if image_bytes is None:
        return (fallback_width, fallback_height)
    png_size = _png_size(image_bytes)
    if png_size is not None:
        return png_size
    jpeg_size = _jpeg_size(image_bytes)
    if jpeg_size is not None:
        return jpeg_size
    return (fallback_width, fallback_height)


def _png_size(image_bytes: bytes) -> tuple[int, int] | None:
    if len(image_bytes) < 24 or not image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    return (
        int.from_bytes(image_bytes[16:20], "big"),
        int.from_bytes(image_bytes[20:24], "big"),
    )


def _jpeg_size(image_bytes: bytes) -> tuple[int, int] | None:
    if len(image_bytes) < 4 or image_bytes[:2] != b"\xff\xd8":
        return None
    index = 2
    while index + 9 < len(image_bytes):
        if image_bytes[index] != 0xFF:
            index += 1
            continue
        marker = image_bytes[index + 1]
        index += 2
        if marker in {0xD8, 0xD9}:
            continue
        if index + 2 > len(image_bytes):
            return None
        segment_length = int.from_bytes(image_bytes[index : index + 2], "big")
        if segment_length < 2 or index + segment_length > len(image_bytes):
            return None
        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            height = int.from_bytes(image_bytes[index + 3 : index + 5], "big")
            width = int.from_bytes(image_bytes[index + 5 : index + 7], "big")
            return (width, height)
        index += segment_length
    return None
