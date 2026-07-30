from datetime import UTC, datetime
from uuid import UUID

import pytest

from hive_sight_core_api.dependencies import build_dev_state
from hive_sight_core_api.dev_store import DomainError, UserContext
from hive_sight_core_api.models import (
    AnnotationType,
    CoordinateSpace,
    DatasetRole,
    OrientedBeeEllipseResponse,
    TrainingCropDatasetItemCreateRequest,
    TrainingCropResponse,
    TrainingCropReviewStatus,
    VisibleBeeStatus,
)
from hive_sight_core_api.training_crop_dataset_item_workflow import (
    TrainingCropDatasetItemWorkflow,
)

USER_ID = UUID("00000000-0000-0000-0000-000000000101")
WORKSPACE_ID = UUID("00000000-0000-0000-0000-000000022001")
TRAINING_CROP_ID = UUID("00000000-0000-0000-0000-000000022002")
INSPECTION_PHOTO_ID = UUID("00000000-0000-0000-0000-000000022003")


def test_workflow_requires_reviewed_training_crop_before_assignment() -> None:
    state = _state()
    workflow = TrainingCropDatasetItemWorkflow(store=state.store)
    _authorise_dataset_curator_workspace(state.store)
    state.store.training_crops[TRAINING_CROP_ID] = _crop(
        review_status=TrainingCropReviewStatus.review_pending,
    )

    with pytest.raises(DomainError) as exc:
        workflow.create_dataset_item_from_training_crop(
            user=UserContext(user_id=USER_ID),
            training_crop_id=TRAINING_CROP_ID,
            request=TrainingCropDatasetItemCreateRequest(
                workspace_id=WORKSPACE_ID,
                dataset_role=DatasetRole.training,
            ),
        )

    assert exc.value.code == "training_crop_review_required"


def test_workflow_captures_reviewed_ellipse_snapshot_on_assignment() -> None:
    state = _state()
    workflow = TrainingCropDatasetItemWorkflow(store=state.store)
    _authorise_dataset_curator_workspace(state.store)
    state.store.training_crops[TRAINING_CROP_ID] = _crop(
        review_status=TrainingCropReviewStatus.review_complete,
        visible_bee_status=VisibleBeeStatus.has_visible_bees,
    )
    state.store.training_crop_ellipses[UUID("00000000-0000-0000-0000-000000022004")] = (
        _ellipse()
    )

    dataset_item = workflow.create_dataset_item_from_training_crop(
        user=UserContext(user_id=USER_ID),
        training_crop_id=TRAINING_CROP_ID,
        request=TrainingCropDatasetItemCreateRequest(
            workspace_id=WORKSPACE_ID,
            dataset_role=DatasetRole.training,
        ),
    )

    assert dataset_item.source_evidence_type == "training_crop"
    assert dataset_item.reviewed_annotation_ids == [
        UUID("00000000-0000-0000-0000-000000022004")
    ]
    assert len(dataset_item.reviewed_ellipse_snapshots) == 1
    assert dataset_item.reviewed_ellipse_snapshots[0].center_x == 150


def _state():
    return build_dev_state(
        id_values=[UUID(f"00000000-0000-0000-0000-{index:012d}") for index in range(22001, 22010)],
        clock=lambda: datetime(2026, 7, 30, 15, 20, tzinfo=UTC),
    )


def _authorise_dataset_curator_workspace(store) -> None:
    session = store.ensure_dev_session(USER_ID)
    store.accept_data_use_agreement(
        user=UserContext(user_id=USER_ID),
        workspace_id=session.workspace_id,
        terms_version="2026-07-30",
    )
    workspace = store.workspaces.pop(session.workspace_id)
    store.workspaces[WORKSPACE_ID] = workspace.__class__(
        workspace_id=WORKSPACE_ID,
        data_use_agreement_status=workspace.data_use_agreement_status,
        data_use_agreement_terms_version=workspace.data_use_agreement_terms_version,
        data_use_agreement_accepted_at=workspace.data_use_agreement_accepted_at,
    )
    store.memberships[0] = store.memberships[0].__class__(
        user_id=USER_ID,
        workspace_id=WORKSPACE_ID,
    )


def _crop(
    review_status: TrainingCropReviewStatus,
    visible_bee_status: VisibleBeeStatus = VisibleBeeStatus.unassessed,
) -> TrainingCropResponse:
    return TrainingCropResponse(
        training_crop_id=TRAINING_CROP_ID,
        workspace_id=WORKSPACE_ID,
        inspection_photo_id=INSPECTION_PHOTO_ID,
        crop_x=100,
        crop_y=100,
        crop_width=300,
        crop_height=300,
        coordinate_space=CoordinateSpace.source_image_pixels,
        source_image_width_px=1000,
        source_image_height_px=800,
        crop_image_width_px=300,
        crop_image_height_px=300,
        curriculum_stage="small_crop",
        review_status=review_status,
        visible_bee_status=visible_bee_status,
        created_by_user_id=USER_ID,
        created_at=datetime(2026, 7, 30, 15, 20, tzinfo=UTC),
        updated_at=datetime(2026, 7, 30, 15, 20, tzinfo=UTC),
    )


def _ellipse() -> OrientedBeeEllipseResponse:
    return OrientedBeeEllipseResponse(
        annotation_id=UUID("00000000-0000-0000-0000-000000022004"),
        workspace_id=WORKSPACE_ID,
        inspection_photo_id=INSPECTION_PHOTO_ID,
        training_crop_id=TRAINING_CROP_ID,
        annotation_type=AnnotationType.complete_visible_bee,
        center_x=150,
        center_y=170,
        radius_x=20,
        radius_y=10,
        rotation_degrees=15,
        coordinate_space=CoordinateSpace.source_image_pixels,
        source_image_width_px=1000,
        source_image_height_px=800,
        source="human_from_scratch",
        created_by_user_id=USER_ID,
        created_at=datetime(2026, 7, 30, 15, 20, tzinfo=UTC),
        updated_at=datetime(2026, 7, 30, 15, 20, tzinfo=UTC),
    )
