from datetime import UTC, datetime
from uuid import UUID

import pytest

from hive_sight_core_api.dependencies import build_dev_state
from hive_sight_core_api.dev_store import DomainError, UserContext
from hive_sight_core_api.models import (
    AnnotationType,
    InspectionIntent,
    InspectionPhotoResponse,
    InspectionResponse,
    OrientedBeeEllipseCreateRequest,
    TrainingCropCreateRequest,
    TrainingCropUpdateRequest,
    UploadStatus,
    VisibleBeeStatus,
)
from hive_sight_core_api.training_crop_workflow import TrainingCropWorkflow

USER_ID = UUID("00000000-0000-0000-0000-000000000101")
WORKSPACE_ID = UUID("00000000-0000-0000-0000-000000021001")
INSPECTION_PHOTO_ID = UUID("00000000-0000-0000-0000-000000021002")


def test_workflow_validates_crop_bounds_before_saving() -> None:
    state = _state()
    workflow = TrainingCropWorkflow(store=state.store)
    _authorise_dataset_curator_workspace(state.store)

    with pytest.raises(DomainError) as exc:
        workflow.create_training_crop(
            user=UserContext(user_id=USER_ID),
            request=TrainingCropCreateRequest(
                workspace_id=WORKSPACE_ID,
                inspection_photo_id=INSPECTION_PHOTO_ID,
                crop_x=900,
                crop_y=100,
                crop_width=300,
                crop_height=300,
                source_image_width_px=1000,
                source_image_height_px=800,
            ),
        )

    assert exc.value.code == "invalid_crop_bounds"
    assert state.store.training_crops == {}


def test_workflow_locks_crop_bounds_after_first_ellipse() -> None:
    state = _state()
    workflow = TrainingCropWorkflow(store=state.store)
    _authorise_dataset_curator_workspace(state.store)
    crop = workflow.create_training_crop(user=UserContext(user_id=USER_ID), request=_crop_request())
    workflow.create_training_crop_ellipse(
        user=UserContext(user_id=USER_ID),
        training_crop_id=crop.training_crop_id,
        request=_ellipse_request(crop.training_crop_id),
    )

    with pytest.raises(DomainError) as exc:
        workflow.update_training_crop(
            user=UserContext(user_id=USER_ID),
            training_crop_id=crop.training_crop_id,
            request=TrainingCropUpdateRequest(workspace_id=WORKSPACE_ID, crop_x=120),
        )

    assert exc.value.code == "crop_bounds_locked"


def test_workflow_rejects_no_visible_bees_with_existing_ellipses() -> None:
    state = _state()
    workflow = TrainingCropWorkflow(store=state.store)
    _authorise_dataset_curator_workspace(state.store)
    crop = workflow.create_training_crop(user=UserContext(user_id=USER_ID), request=_crop_request())
    workflow.create_training_crop_ellipse(
        user=UserContext(user_id=USER_ID),
        training_crop_id=crop.training_crop_id,
        request=_ellipse_request(crop.training_crop_id),
    )

    with pytest.raises(DomainError) as exc:
        workflow.update_training_crop(
            user=UserContext(user_id=USER_ID),
            training_crop_id=crop.training_crop_id,
            request=TrainingCropUpdateRequest(
                workspace_id=WORKSPACE_ID,
                visible_bee_status=VisibleBeeStatus.no_visible_bees,
            ),
        )

    assert exc.value.code == "no_visible_bees_conflicts_with_ellipses"


def _state():
    return build_dev_state(
        id_values=[UUID(f"00000000-0000-0000-0000-{index:012d}") for index in range(21001, 21020)],
        clock=lambda: datetime(2026, 7, 30, 15, 10, tzinfo=UTC),
    )


def _authorise_dataset_curator_workspace(store) -> None:
    session = store.ensure_dev_session(USER_ID)
    store.accept_data_use_agreement(
        user=UserContext(user_id=USER_ID),
        workspace_id=session.workspace_id,
        terms_version="2026-07-30",
    )
    store.workspaces[WORKSPACE_ID] = store.workspaces.pop(session.workspace_id)
    store.workspaces[WORKSPACE_ID] = store.workspaces[WORKSPACE_ID].__class__(
        workspace_id=WORKSPACE_ID,
        data_use_agreement_status=store.workspaces[WORKSPACE_ID].data_use_agreement_status,
        data_use_agreement_terms_version=store.workspaces[
            WORKSPACE_ID
        ].data_use_agreement_terms_version,
        data_use_agreement_accepted_at=store.workspaces[
            WORKSPACE_ID
        ].data_use_agreement_accepted_at,
    )
    store.memberships[0] = store.memberships[0].__class__(
        user_id=USER_ID,
        workspace_id=WORKSPACE_ID,
    )
    store.inspection_photos[INSPECTION_PHOTO_ID] = InspectionPhotoResponse(
        inspection_photo_id=INSPECTION_PHOTO_ID,
        inspection_id=UUID("00000000-0000-0000-0000-000000021003"),
        workspace_id=WORKSPACE_ID,
        original_object_key="photos/frame.png",
        filename="frame.png",
        content_type="image/png",
        size_bytes=10,
        upload_status=UploadStatus.accepted,
        uploaded_by_user_id=USER_ID,
        uploaded_at=datetime(2026, 7, 30, 15, 10, tzinfo=UTC),
    )
    store.inspections[UUID("00000000-0000-0000-0000-000000021003")] = InspectionResponse(
        inspection_id=UUID("00000000-0000-0000-0000-000000021003"),
        hive_id=UUID("00000000-0000-0000-0000-000000021004"),
        workspace_id=WORKSPACE_ID,
        inspection_date=datetime(2026, 7, 30, 15, 10, tzinfo=UTC).date(),
        intent=InspectionIntent.training_data_collection,
    )


def _crop_request() -> TrainingCropCreateRequest:
    return TrainingCropCreateRequest(
        workspace_id=WORKSPACE_ID,
        inspection_photo_id=INSPECTION_PHOTO_ID,
        crop_x=100,
        crop_y=100,
        crop_width=300,
        crop_height=300,
        source_image_width_px=1000,
        source_image_height_px=800,
    )


def _ellipse_request(training_crop_id: UUID) -> OrientedBeeEllipseCreateRequest:
    _ = training_crop_id
    return OrientedBeeEllipseCreateRequest(
        workspace_id=WORKSPACE_ID,
        annotation_type=AnnotationType.complete_visible_bee,
        center_x=180,
        center_y=180,
        radius_x=20,
        radius_y=10,
        rotation_degrees=0,
    )
