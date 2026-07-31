from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from hive_configuration_test_support import configure_hive
from pytest_bdd import given, scenarios, then, when

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.dev_store import DevState
from hive_sight_core_api.main import app

FEATURES_DIR = Path(__file__).parent / "features"
USER_ID = UUID("00000000-0000-0000-0000-000000000101")

scenarios(str(FEATURES_DIR / "vertical_slice_0009_training_crop_ellipse_annotation.feature"))


@dataclass
class SliceContext:
    client: TestClient
    state: DevState
    workspace_id: str | None = None
    hive_id: str | None = None
    inspection_id: str | None = None
    inspection_photo_id: str | None = None
    training_crop_id: str | None = None
    response_status_code: int | None = None
    response_body: dict[str, object] | None = None


@pytest.fixture
def slice_context() -> SliceContext:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000009101"),
            UUID("00000000-0000-0000-0000-000000009102"),
            UUID("00000000-0000-0000-0000-000000009103"),
            UUID("00000000-0000-0000-0000-000000009104"),
            UUID("00000000-0000-0000-0000-000000009105"),
            UUID("00000000-0000-0000-0000-000000009106"),
            UUID("00000000-0000-0000-0000-000000009107"),
            UUID("00000000-0000-0000-0000-000000009108"),
        ],
        clock=lambda: datetime(2026, 7, 30, 13, 0, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    try:
        yield SliceContext(client=TestClient(app), state=state)
    finally:
        app.dependency_overrides.clear()


@given("the User is logged in with dataset curator capability for Training Crop annotation")
def user_logged_in_with_dataset_curator_capability(slice_context: SliceContext) -> None:
    workspace_id = slice_context.client.get(
        "/v1/dev/session",
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    ).json()["workspace_id"]
    accept_terms = slice_context.client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": workspace_id, "terms_version": "2026-07-30"},
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    )
    assert accept_terms.status_code == 200
    apiary_id = slice_context.client.post(
        "/v1/apiaries",
        json={"workspace_id": workspace_id, "name": "Home apiary"},
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    ).json()["apiary_id"]
    hive_id = slice_context.client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": "Hive A"},
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    ).json()["hive_id"]
    configure_hive(
        slice_context.client,
        workspace_id=workspace_id,
        hive_id=hive_id,
        user_id=USER_ID,
    )
    slice_context.workspace_id = workspace_id
    slice_context.hive_id = hive_id


@given("the Beekeeper has uploaded an Inspection Photo for Training Crop annotation")
def beekeeper_uploaded_training_photo(slice_context: SliceContext) -> None:
    slice_context.inspection_id = _create_inspection(slice_context, "training_data_collection")
    slice_context.inspection_photo_id = _upload_photo(slice_context, "training-frame.jpg")


@given("the Beekeeper has uploaded an Inspection Photo for Varroa assessment")
def beekeeper_uploaded_varroa_assessment_photo(slice_context: SliceContext) -> None:
    slice_context.inspection_id = _create_inspection(slice_context, "varroa_assessment")
    slice_context.inspection_photo_id = _upload_photo(slice_context, "assessment-frame.jpg")


@when("the Dataset Curator creates a Training Crop from that photo")
def dataset_curator_creates_training_crop(slice_context: SliceContext) -> None:
    _create_crop(slice_context)
    assert slice_context.response_status_code == 201
    assert slice_context.response_body is not None
    slice_context.training_crop_id = str(slice_context.response_body["training_crop_id"])


@when("the Dataset Curator tries to create a Training Crop from that photo")
def dataset_curator_tries_to_create_training_crop(slice_context: SliceContext) -> None:
    _create_crop(slice_context)


@when("the Dataset Curator adds a complete visible bee ellipse to that crop")
def dataset_curator_adds_complete_visible_bee_ellipse(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.training_crop_id is not None
    response = slice_context.client.post(
        f"/v1/training-crops/{slice_context.training_crop_id}/bee-ellipses",
        json={
            "workspace_id": slice_context.workspace_id,
            "annotation_type": "complete_visible_bee",
            "center_x": 320,
            "center_y": 320,
            "radius_x": 40,
            "radius_y": 20,
            "rotation_degrees": 25,
        },
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    )
    assert response.status_code == 201


@when("the Dataset Curator marks the Training Crop review complete with visible bees")
def dataset_curator_completes_visible_bee_crop(slice_context: SliceContext) -> None:
    _update_crop(
        slice_context,
        {
            "visible_bee_status": "has_visible_bees",
            "review_status": "review_complete",
            "notes": "Reviewed crop has a clear visible bee.",
        },
    )


@when("the Dataset Curator marks the Training Crop review complete with no visible bees")
def dataset_curator_completes_no_visible_bee_crop(slice_context: SliceContext) -> None:
    _update_crop(
        slice_context,
        {
            "visible_bee_status": "no_visible_bees",
            "review_status": "review_complete",
            "notes": "Reviewed crop has no visible bees.",
        },
    )


@then("the Core API shows completed Training Crop evidence")
def core_api_shows_completed_training_crop_evidence(slice_context: SliceContext) -> None:
    evidence = _get_evidence(slice_context)
    crop = evidence["training_crop"]
    ellipses = evidence["bee_ellipses"]
    assert isinstance(crop, dict)
    assert isinstance(ellipses, list)
    assert crop["review_status"] == "review_complete"
    assert crop["visible_bee_status"] == "has_visible_bees"
    assert len(ellipses) == 1
    ellipse = ellipses[0]
    assert isinstance(ellipse, dict)
    assert ellipse["annotation_type"] == "complete_visible_bee"
    assert ellipse["coordinate_space"] == "source_image_pixels"
    assert ellipse["rotation_degrees"] == 25
    slice_context.response_body = evidence


@then("the Training Crop evidence is not assigned to dataset use")
def training_crop_evidence_not_assigned_to_dataset_use(slice_context: SliceContext) -> None:
    assert slice_context.response_body is not None
    assert slice_context.response_body["training_crop"]["dataset_role"] is None
    assert slice_context.response_body["training_crop"]["dataset_item_id"] is None
    assert "Dataset use is assigned later" in str(slice_context.response_body["caveat"])


@then("the Core API shows a completed no-visible-bees Training Crop with no ellipses")
def core_api_shows_completed_no_visible_bees_crop(slice_context: SliceContext) -> None:
    evidence = _get_evidence(slice_context)
    crop = evidence["training_crop"]
    ellipses = evidence["bee_ellipses"]
    assert isinstance(crop, dict)
    assert isinstance(ellipses, list)
    assert crop["review_status"] == "review_complete"
    assert crop["visible_bee_status"] == "no_visible_bees"
    assert ellipses == []


@then("Training Crop creation is blocked because the Inspection intent is Varroa assessment")
def training_crop_creation_blocked_by_varroa_intent(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 409
    assert slice_context.response_body is not None
    detail = slice_context.response_body["detail"]
    assert isinstance(detail, dict)
    assert detail["code"] == "inspection_intent_not_for_training_crop"


def _create_inspection(slice_context: SliceContext, intent: str) -> str:
    assert slice_context.hive_id is not None
    response = slice_context.client.post(
        "/v1/inspections",
        json={
            "hive_id": slice_context.hive_id,
            "inspection_date": str(date(2026, 7, 30)),
            "intent": intent,
        },
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    )
    assert response.status_code == 201
    return response.json()["inspection_id"]


def _upload_photo(slice_context: SliceContext, filename: str) -> str:
    assert slice_context.workspace_id is not None
    assert slice_context.inspection_id is not None
    response = slice_context.client.post(
        "/v1/inspection-photos/intake"
        f"?workspace_id={slice_context.workspace_id}&inspection_id={slice_context.inspection_id}",
        content=b"fake-image-bytes",
        headers={
            "content-type": "image/jpeg",
            "x-hivesight-dev-user-id": str(USER_ID),
            "x-hivesight-filename": filename,
        },
    )
    assert response.status_code == 202
    return response.json()["inspection_photo"]["inspection_photo_id"]


def _create_crop(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.inspection_photo_id is not None
    response = slice_context.client.post(
        "/v1/training-crops",
        json={
            "workspace_id": slice_context.workspace_id,
            "inspection_photo_id": slice_context.inspection_photo_id,
            "crop_x": 100,
            "crop_y": 100,
            "crop_width": 640,
            "crop_height": 640,
            "source_image_width_px": 1600,
            "source_image_height_px": 1200,
            "notes": "Candidate crop from source photo.",
        },
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    )
    slice_context.response_status_code = response.status_code
    slice_context.response_body = response.json()


def _update_crop(slice_context: SliceContext, values: dict[str, object]) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.training_crop_id is not None
    response = slice_context.client.patch(
        f"/v1/training-crops/{slice_context.training_crop_id}",
        json={"workspace_id": slice_context.workspace_id, **values},
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    )
    assert response.status_code == 200
    slice_context.response_status_code = response.status_code
    slice_context.response_body = response.json()


def _get_evidence(slice_context: SliceContext) -> dict[str, object]:
    assert slice_context.workspace_id is not None
    assert slice_context.training_crop_id is not None
    response = slice_context.client.get(
        f"/v1/training-crops/{slice_context.training_crop_id}/evidence"
        f"?workspace_id={slice_context.workspace_id}",
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    )
    assert response.status_code == 200
    return response.json()
