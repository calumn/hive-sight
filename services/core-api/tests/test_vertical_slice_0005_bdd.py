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
NON_CURATOR_USER_ID = UUID("00000000-0000-0000-0000-000000000202")

scenarios(str(FEATURES_DIR / "vertical_slice_0005_ai_assisted_bee_annotation_bootstrap.feature"))


@dataclass
class SliceContext:
    client: TestClient
    state: DevState
    current_user_id: UUID | None = None
    workspace_id: str | None = None
    inspection_photo_id: str | None = None
    labelling_session_id: str | None = None
    complete_annotation_id: str | None = None
    partial_annotation_id: str | None = None
    response_body: dict[str, object] | None = None
    response_status_code: int | None = None


@pytest.fixture
def slice_context() -> SliceContext:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000002001"),
            UUID("00000000-0000-0000-0000-000000002002"),
            UUID("00000000-0000-0000-0000-000000002003"),
            UUID("00000000-0000-0000-0000-000000002004"),
            UUID("00000000-0000-0000-0000-000000002005"),
            UUID("00000000-0000-0000-0000-000000002006"),
            UUID("00000000-0000-0000-0000-000000002007"),
            UUID("00000000-0000-0000-0000-000000002008"),
            UUID("00000000-0000-0000-0000-000000002009"),
            UUID("00000000-0000-0000-0000-000000002010"),
        ],
        clock=lambda: datetime(2026, 7, 29, 16, 0, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    try:
        yield SliceContext(client=TestClient(app), state=state)
    finally:
        app.dependency_overrides.clear()


@given("the User is logged in with dataset curator capability")
def user_is_logged_in_with_dataset_curator_capability(slice_context: SliceContext) -> None:
    slice_context.current_user_id = CURATOR_USER_ID
    _create_session(slice_context, CURATOR_USER_ID)


@given("the User is logged in without dataset curator capability")
def user_is_logged_in_without_dataset_curator_capability(slice_context: SliceContext) -> None:
    slice_context.state.store.dataset_curator_user_ids.clear()
    slice_context.current_user_id = NON_CURATOR_USER_ID
    _create_session(slice_context, NON_CURATOR_USER_ID)


@given("the Workspace has accepted the Workspace Data Use Agreement for dataset labelling")
def workspace_has_accepted_data_use_agreement(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.current_user_id is not None

    response = slice_context.client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": slice_context.workspace_id, "terms_version": "2026-07-29"},
        headers={"x-hivesight-dev-user-id": str(slice_context.current_user_id)},
    )

    assert response.status_code == 200


@given("the Beekeeper has uploaded an Inspection Photo for dataset labelling")
def beekeeper_has_uploaded_photo(slice_context: SliceContext) -> None:
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
    slice_context.inspection_photo_id = intake_response.json()["inspection_photo"][
        "inspection_photo_id"
    ]


@given("an uploaded Inspection Photo contains an ambiguous bee-like object")
def uploaded_photo_contains_ambiguous_bee_like_object() -> None:
    return


@when("the Dataset Curator starts AI-assisted dataset labelling for that photo")
def dataset_curator_starts_labelling(slice_context: SliceContext) -> None:
    _start_labelling(slice_context)


@when("the User tries to start AI-assisted dataset labelling for that photo")
def user_tries_to_start_labelling(slice_context: SliceContext) -> None:
    _start_labelling(slice_context)


@when("the Dataset Curator records source grouping and image quality metadata")
def dataset_curator_records_metadata(slice_context: SliceContext) -> None:
    assert slice_context.current_user_id is not None
    assert slice_context.labelling_session_id is not None

    response = slice_context.client.patch(
        f"/v1/dataset-labelling-sessions/{slice_context.labelling_session_id}",
        json={
            "workspace_id": slice_context.workspace_id,
            "source_group_key": "frame-a-side-1",
            "image_quality_status": "usable",
        },
        headers={"x-hivesight-dev-user-id": str(slice_context.current_user_id)},
    )

    assert response.status_code == 200


@when("the Dataset Curator approves complete and partial bee draft annotations")
def dataset_curator_approves_bee_drafts(slice_context: SliceContext) -> None:
    evidence = _request_labelling_evidence(slice_context)
    annotations = evidence["draft_annotations"]
    assert isinstance(annotations, list)
    complete = next(
        annotation
        for annotation in annotations
        if annotation["annotation_type"] == "complete_visible_bee"
    )
    partial = next(
        annotation
        for annotation in annotations
        if annotation["annotation_type"] == "partial_visible_bee"
    )
    slice_context.complete_annotation_id = str(complete["annotation_id"])
    slice_context.partial_annotation_id = str(partial["annotation_id"])

    _approve_annotation(slice_context, slice_context.complete_annotation_id)
    _approve_annotation(slice_context, slice_context.partial_annotation_id)


@when("the Dataset Curator needs to mark an uncertain bee")
def dataset_curator_needs_to_mark_uncertain_bee() -> None:
    return


@then("the Core API shows reviewed dataset-labelling bee annotations")
def core_api_shows_reviewed_labelling_annotations(slice_context: SliceContext) -> None:
    evidence = _request_labelling_evidence(slice_context)
    reviewed_annotations = evidence["reviewed_annotations"]
    assert isinstance(reviewed_annotations, list)
    assert [annotation["annotation_id"] for annotation in reviewed_annotations] == [
        slice_context.complete_annotation_id,
        slice_context.partial_annotation_id,
    ]
    assert all(
        annotation["latest_review_decision"]["decision"] == "approved"
        for annotation in reviewed_annotations
    )


@then("the labelling evidence preserves draft source and curator provenance")
def evidence_preserves_source_and_curator_provenance(slice_context: SliceContext) -> None:
    evidence = _request_labelling_evidence(slice_context)
    assert evidence["labelling_session"]["source_group_key"] == "frame-a-side-1"
    assert evidence["labelling_session"]["image_quality_status"] == "usable"
    draft_annotations = evidence["draft_annotations"]
    assert isinstance(draft_annotations, list)
    assert all(annotation["source"] == "ai_assisted_draft" for annotation in draft_annotations)
    assert all(annotation["workflow_type"] == "dataset_labelling" for annotation in draft_annotations)
    decisions = evidence["latest_review_decisions"]
    assert isinstance(decisions, list)
    assert all(decision["reviewer_id"] == str(CURATOR_USER_ID) for decision in decisions)


@then("the labelling evidence does not assign dataset use")
def labelling_evidence_does_not_assign_dataset_use(slice_context: SliceContext) -> None:
    evidence = _request_labelling_evidence(slice_context)
    assert "dataset_role" not in evidence
    assert "dataset_item_id" not in evidence
    assert "dataset_version_id" not in evidence


@then("dataset labelling is blocked by dataset curator authorization")
def dataset_labelling_is_blocked_by_authorization(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 403
    assert slice_context.response_body is not None
    detail = slice_context.response_body["detail"]
    assert isinstance(detail, dict)
    assert detail["code"] == "dataset_curator_access_required"


@then("uncertain bee annotation type support remains a documented gap")
def uncertain_bee_support_remains_documented_gap() -> None:
    pytest.xfail("uncertain_bee annotation type is a documented gap for Slice 5.")


def _create_session(slice_context: SliceContext, user_id: UUID) -> None:
    response = slice_context.client.get(
        "/v1/dev/session",
        headers={"x-hivesight-dev-user-id": str(user_id)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "owner"
    slice_context.workspace_id = body["workspace_id"]


def _start_labelling(slice_context: SliceContext) -> None:
    assert slice_context.current_user_id is not None
    assert slice_context.workspace_id is not None
    assert slice_context.inspection_photo_id is not None

    response = slice_context.client.post(
        "/v1/dataset-labelling-sessions",
        json={
            "workspace_id": slice_context.workspace_id,
            "inspection_photo_id": slice_context.inspection_photo_id,
        },
        headers={"x-hivesight-dev-user-id": str(slice_context.current_user_id)},
    )
    slice_context.response_status_code = response.status_code
    slice_context.response_body = response.json()
    if response.status_code in {200, 201}:
        slice_context.labelling_session_id = response.json()["labelling_session_id"]


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


def _approve_annotation(slice_context: SliceContext, annotation_id: str) -> None:
    assert slice_context.current_user_id is not None
    assert slice_context.workspace_id is not None

    response = slice_context.client.post(
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
    assert response.status_code == 201
