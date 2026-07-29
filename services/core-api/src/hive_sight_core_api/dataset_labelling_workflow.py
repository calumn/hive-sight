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
    source_image_width_px: int
    source_image_height_px: int


@dataclass(frozen=True)
class PrelabellingResult:
    prelabeler_name: str
    prelabeler_version: str
    annotations: list[AnnotationCreate]


class BeePrelabeler(Protocol):
    name: str
    version: str

    def create_draft_annotations(self, request: PrelabellingRequest) -> PrelabellingResult:
        """Create AI-assisted draft annotations for one original image."""


@dataclass(frozen=True)
class DeterministicBeePrelabeler:
    name: str = "deterministic-bee-prelabeler"
    version: str = "0.1.0"

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
        try:
            prelabelling = self.prelabeler.create_draft_annotations(
                PrelabellingRequest(
                    inspection_photo_id=photo.inspection_photo_id,
                    original_object_key=photo.original_object_key,
                    source_image_width_px=self.source_image_width_px,
                    source_image_height_px=self.source_image_height_px,
                )
            )
        except Exception:  # noqa: BLE001 - adapter failures are recorded as session evidence.
            failed_run = PrelabelerRunResponse(
                prelabeler_run_id=prelabeler_run_id,
                prelabeler_name=self.prelabeler.name,
                prelabeler_version=self.prelabeler.version,
                status=PrelabelerRunStatus.failed,
                started_at=started_at,
                finished_at=self.clock(),
                error_code="prelabel_failed",
                error_message="Pre-labelling failed before draft annotations were created.",
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
            status=PrelabelerRunStatus.succeeded,
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
                width=self.source_image_width_px,
                height=self.source_image_height_px,
            ),
            labelling_session=session,
            draft_annotations=annotations,
            reviewed_annotations=reviewed_annotations,
            latest_review_decisions=latest_review_decisions,
            caveat=(
                "AI-assisted draft annotations are deterministic test suggestions for dataset "
                "labelling. Dataset use is not assigned in this slice."
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
