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
CURATOR_USER_ID = UUID("00000000-0000-0000-0000-000000000101")

scenarios(str(FEATURES_DIR / "vertical_slice_0006_dataset_role_assignment.feature"))


@dataclass
class SliceContext:
    client: TestClient
    state: DevState
    current_user_id: UUID | None = None
    workspace_id: str | None = None
    labelling_session_id: str | None = None
    response_body: dict[str, object] | None = None
    response_status_code: int | None = None


@pytest.fixture
def slice_context() -> SliceContext:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000006101"),
            UUID("00000000-0000-0000-0000-000000006102"),
            UUID("00000000-0000-0000-0000-000000006103"),
            UUID("00000000-0000-0000-0000-000000006104"),
            UUID("00000000-0000-0000-0000-000000006105"),
            UUID("00000000-0000-0000-0000-000000006106"),
            UUID("00000000-0000-0000-0000-000000006107"),
            UUID("00000000-0000-0000-0000-000000006108"),
            UUID("00000000-0000-0000-0000-000000006109"),
            UUID("00000000-0000-0000-0000-000000006110"),
            UUID("00000000-0000-0000-0000-000000006111"),
            UUID("00000000-0000-0000-0000-000000006112"),
        ],
        clock=lambda: datetime(2026, 7, 29, 17, 30, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    try:
        yield SliceContext(client=TestClient(app), state=state)
    finally:
        app.dependency_overrides.clear()


@given("the User is logged in with dataset curator capability for Dataset Role assignment")
def user_is_logged_in_with_dataset_curator_capability(slice_context: SliceContext) -> None:
    slice_context.current_user_id = CURATOR_USER_ID
    _create_session(slice_context)


@given("the User is logged in without dataset curator capability for Dataset Role assignment")
def user_is_logged_in_without_dataset_curator_capability(slice_context: SliceContext) -> None:
    slice_context.state.store.dataset_curator_user_ids.clear()
    slice_context.current_user_id = CURATOR_USER_ID
    _create_session(slice_context)
    slice_context.state.store.dataset_curator_user_ids.add(CURATOR_USER_ID)


@given("the Workspace has accepted the Workspace Data Use Agreement for Dataset Role assignment")
def workspace_has_accepted_data_use_agreement(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.current_user_id is not None
    response = slice_context.client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": slice_context.workspace_id, "terms_version": "2026-07-29"},
        headers={"x-hivesight-dev-user-id": str(slice_context.current_user_id)},
    )
    assert response.status_code == 200


@given("the Dataset Curator has reviewed bee Draft Annotations in a Dataset Labelling Session")
def curator_has_reviewed_bee_draft_annotations(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.current_user_id is not None

    apiary_id = slice_context.client.post(
        "/v1/apiaries",
        json={"workspace_id": slice_context.workspace_id, "name": "Home apiary"},
        headers={"x-hivesight-dev-user-id": str(slice_context.current_user_id)},
    ).json()["apiary_id"]
    hive_id = slice_context.client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": "Hive A"},
        headers={"x-hivesight-dev-user-id": str(slice_context.current_user_id)},
    ).json()["hive_id"]
    inspection_id = slice_context.client.post(
        "/v1/inspections",
        json={
            "hive_id": hive_id,
            "inspection_date": str(date(2026, 7, 29)),
            "intent": "training_data_collection",
        },
        headers={"x-hivesight-dev-user-id": str(slice_context.current_user_id)},
    ).json()["inspection_id"]
    intake_response = slice_context.client.post(
        "/v1/inspection-photos/intake"
        f"?workspace_id={slice_context.workspace_id}&inspection_id={inspection_id}",
        content=b"fake-image-bytes",
        headers={
            "content-type": "image/jpeg",
            "x-hivesight-dev-user-id": str(slice_context.current_user_id),
            "x-hivesight-filename": "frame-1.jpg",
        },
    )
    assert intake_response.status_code == 202
    inspection_photo_id = intake_response.json()["inspection_photo"]["inspection_photo_id"]

    start_response = slice_context.client.post(
        "/v1/dataset-labelling-sessions",
        json={
            "workspace_id": slice_context.workspace_id,
            "inspection_photo_id": inspection_photo_id,
        },
        headers={"x-hivesight-dev-user-id": str(slice_context.current_user_id)},
    )
    assert start_response.status_code == 201
    slice_context.labelling_session_id = start_response.json()["labelling_session_id"]

    evidence = _request_labelling_evidence(slice_context)
    annotation_id = evidence["draft_annotations"][0]["annotation_id"]
    review_response = slice_context.client.post(
        "/v1/review-decisions",
        json={
            "workspace_id": slice_context.workspace_id,
            "subject_type": "annotation",
            "subject_id": annotation_id,
            "decision": "approved",
            "notes": "Accepted for dataset labelling evidence.",
        },
        headers={"x-hivesight-dev-user-id": str(slice_context.current_user_id)},
    )
    assert review_response.status_code == 201


@when("the Dataset Curator assigns the reviewed labelling evidence to benchmark")
def curator_assigns_reviewed_evidence_to_benchmark(slice_context: SliceContext) -> None:
    _assign_dataset_role(slice_context, dataset_role="benchmark")


@when("the User tries to assign the reviewed labelling evidence to training")
def user_tries_to_assign_reviewed_evidence_to_training(slice_context: SliceContext) -> None:
    slice_context.state.store.dataset_curator_user_ids.clear()
    _assign_dataset_role(slice_context, dataset_role="training")


@then("the Core API creates a protected benchmark Dataset Item")
def core_api_creates_protected_benchmark_dataset_item(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 201
    assert slice_context.response_body is not None
    assert slice_context.response_body["dataset_role"] == "benchmark"
    assert slice_context.response_body["benchmark_protected"] is True
    assert slice_context.response_body["assigned_by_user_id"] == str(CURATOR_USER_ID)


@then("the labelling evidence projects the Dataset Item")
def labelling_evidence_projects_dataset_item(slice_context: SliceContext) -> None:
    evidence = _request_labelling_evidence(slice_context)
    dataset_item = evidence["dataset_item"]
    assert isinstance(dataset_item, dict)
    assert dataset_item["dataset_role"] == "benchmark"
    assert dataset_item["benchmark_protected"] is True


@then("no Dataset Version or Training Run is created")
def no_dataset_version_or_training_run_is_created(slice_context: SliceContext) -> None:
    assert slice_context.response_body is not None
    assert "dataset_version_id" not in slice_context.response_body
    assert "training_run_id" not in slice_context.response_body


@then("Dataset Role assignment is blocked by dataset curator authorization")
def dataset_role_assignment_is_blocked_by_authorization(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 403
    assert slice_context.response_body is not None
    detail = slice_context.response_body["detail"]
    assert isinstance(detail, dict)
    assert detail["code"] == "dataset_curator_access_required"


def _create_session(slice_context: SliceContext) -> None:
    assert slice_context.current_user_id is not None
    response = slice_context.client.get(
        "/v1/dev/session",
        headers={"x-hivesight-dev-user-id": str(slice_context.current_user_id)},
    )
    assert response.status_code == 200
    slice_context.workspace_id = response.json()["workspace_id"]


def _assign_dataset_role(slice_context: SliceContext, dataset_role: str) -> None:
    assert slice_context.current_user_id is not None
    assert slice_context.workspace_id is not None
    assert slice_context.labelling_session_id is not None
    response = slice_context.client.post(
        "/v1/dataset-items",
        json={
            "workspace_id": slice_context.workspace_id,
            "labelling_session_id": slice_context.labelling_session_id,
            "dataset_role": dataset_role,
            "assignment_note": "Protected benchmark candidate.",
            "exclusion_reason": None,
        },
        headers={"x-hivesight-dev-user-id": str(slice_context.current_user_id)},
    )
    slice_context.response_status_code = response.status_code
    slice_context.response_body = response.json()


def _request_labelling_evidence(slice_context: SliceContext) -> dict[str, object]:
    assert slice_context.current_user_id is not None
    assert slice_context.workspace_id is not None
    assert slice_context.labelling_session_id is not None
    response = slice_context.client.get(
        f"/v1/dataset-labelling-sessions/{slice_context.labelling_session_id}/evidence"
        f"?workspace_id={slice_context.workspace_id}",
        headers={"x-hivesight-dev-user-id": str(slice_context.current_user_id)},
    )
    assert response.status_code == 200
    return response.json()
