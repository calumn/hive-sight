from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.dev_store import DevState
from hive_sight_core_api.main import app

FEATURES_DIR = Path(__file__).parent / "features"
USER_ID = UUID("00000000-0000-0000-0000-000000000101")

scenarios(str(FEATURES_DIR / "vertical_slice_0008_inspection_intent_and_multi_photo_intake.feature"))


@dataclass
class SliceContext:
    client: TestClient
    state: DevState
    workspace_id: str | None = None
    hive_id: str | None = None
    inspection_id: str | None = None
    inspection_photo_id: str | None = None
    response_status_code: int | None = None
    response_body: dict[str, object] | None = None


@pytest.fixture
def slice_context() -> SliceContext:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000008101"),
            UUID("00000000-0000-0000-0000-000000008102"),
            UUID("00000000-0000-0000-0000-000000008103"),
            UUID("00000000-0000-0000-0000-000000008104"),
            UUID("00000000-0000-0000-0000-000000008105"),
            UUID("00000000-0000-0000-0000-000000008106"),
            UUID("00000000-0000-0000-0000-000000008107"),
            UUID("00000000-0000-0000-0000-000000008108"),
        ],
        clock=lambda: datetime(2026, 7, 29, 18, 30, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    try:
        yield SliceContext(client=TestClient(app), state=state)
    finally:
        app.dependency_overrides.clear()


@given("the User is logged in with an accepted Workspace Data Use Agreement")
def user_logged_in_with_terms(slice_context: SliceContext) -> None:
    workspace_id = slice_context.client.get(
        "/v1/dev/session",
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    ).json()["workspace_id"]
    accept_terms = slice_context.client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": workspace_id, "terms_version": "2026-07-29"},
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
    slice_context.workspace_id = workspace_id
    slice_context.hive_id = hive_id


@given("the Beekeeper has created a Varroa assessment Inspection")
def beekeeper_created_varroa_assessment_inspection(slice_context: SliceContext) -> None:
    slice_context.inspection_id = _create_inspection(slice_context, "varroa_assessment")


@given("the Beekeeper has uploaded a photo to a Varroa assessment Inspection")
def beekeeper_uploaded_varroa_assessment_photo(slice_context: SliceContext) -> None:
    slice_context.inspection_id = _create_inspection(slice_context, "varroa_assessment")
    slice_context.inspection_photo_id = _upload_photo(slice_context, "assessment-frame.jpg")


@given("the Beekeeper has uploaded a photo to a training data collection Inspection")
def beekeeper_uploaded_training_data_photo(slice_context: SliceContext) -> None:
    slice_context.inspection_id = _create_inspection(slice_context, "training_data_collection")
    slice_context.inspection_photo_id = _upload_photo(slice_context, "training-frame.jpg")


@when("the Beekeeper uploads two Inspection Photos to that Inspection")
def beekeeper_uploads_two_photos(slice_context: SliceContext) -> None:
    _upload_photo(slice_context, "frame-a.jpg")
    _upload_photo(slice_context, "frame-b.jpg")


@when("the Dataset Curator tries to start dataset labelling for that photo")
def dataset_curator_tries_to_start_labelling(slice_context: SliceContext) -> None:
    _start_labelling(slice_context)


@when("the Dataset Curator starts dataset labelling for that photo")
def dataset_curator_starts_labelling(slice_context: SliceContext) -> None:
    _start_labelling(slice_context)


@then("the Core API lists both Inspection Photos for that Inspection")
def core_api_lists_both_photos(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.inspection_id is not None
    response = slice_context.client.get(
        f"/v1/inspections/{slice_context.inspection_id}/photos"
        f"?workspace_id={slice_context.workspace_id}",
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    )
    assert response.status_code == 200
    body = response.json()
    assert [photo["filename"] for photo in body["photos"]] == ["frame-a.jpg", "frame-b.jpg"]
    slice_context.response_body = body


@then("the Inspection intent is shown as Varroa assessment")
def inspection_intent_is_varroa_assessment(slice_context: SliceContext) -> None:
    assert slice_context.response_body is not None
    assert slice_context.response_body["inspection"]["intent"] == "varroa_assessment"


@then("dataset labelling is blocked because the Inspection intent is Varroa assessment")
def labelling_blocked_by_intent(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 409
    assert slice_context.response_body is not None
    detail = slice_context.response_body["detail"]
    assert isinstance(detail, dict)
    assert detail["code"] == "inspection_intent_not_for_dataset_labelling"


@then("the Core API creates a Dataset Labelling Session")
def core_api_creates_labelling_session(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 201
    assert slice_context.response_body is not None
    assert slice_context.response_body["inspection_photo_id"] == slice_context.inspection_photo_id
    assert slice_context.response_body["status"] == "draft_ready"


def _create_inspection(slice_context: SliceContext, intent: str) -> str:
    assert slice_context.hive_id is not None
    response = slice_context.client.post(
        "/v1/inspections",
        json={
            "hive_id": slice_context.hive_id,
            "inspection_date": str(date(2026, 7, 29)),
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


def _start_labelling(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.inspection_photo_id is not None
    response = slice_context.client.post(
        "/v1/dataset-labelling-sessions",
        json={
            "workspace_id": slice_context.workspace_id,
            "inspection_photo_id": slice_context.inspection_photo_id,
        },
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    )
    slice_context.response_status_code = response.status_code
    slice_context.response_body = response.json()
