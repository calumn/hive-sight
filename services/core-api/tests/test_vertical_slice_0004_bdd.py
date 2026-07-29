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
REVIEWER_USER_ID = UUID("00000000-0000-0000-0000-000000000101")
NON_REVIEWER_USER_ID = UUID("00000000-0000-0000-0000-000000000202")

scenarios(str(FEATURES_DIR / "vertical_slice_0004_annotation_review_decision.feature"))


@dataclass
class SliceContext:
    client: TestClient
    state: DevState
    current_user_id: UUID | None = None
    workspace_id: str | None = None
    analysis_run_id: str | None = None
    annotation_id: str | None = None
    response_body: dict[str, object] | None = None
    response_status_code: int | None = None


@pytest.fixture
def slice_context() -> SliceContext:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000000001"),
            UUID("00000000-0000-0000-0000-000000000002"),
            UUID("00000000-0000-0000-0000-000000000003"),
            UUID("00000000-0000-0000-0000-000000000004"),
            UUID("00000000-0000-0000-0000-000000000005"),
            UUID("00000000-0000-0000-0000-000000000006"),
            UUID("00000000-0000-0000-0000-000000000007"),
            UUID("00000000-0000-0000-0000-000000000008"),
            UUID("00000000-0000-0000-0000-000000000009"),
            UUID("00000000-0000-0000-0000-000000000010"),
            UUID("00000000-0000-0000-0000-000000000011"),
        ],
        clock=lambda: datetime(2026, 7, 29, 14, 0, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    try:
        yield SliceContext(client=TestClient(app), state=state)
    finally:
        app.dependency_overrides.clear()


@given("the User is logged in with reviewer capability for annotation review")
def user_is_logged_in_with_reviewer_capability(slice_context: SliceContext) -> None:
    slice_context.current_user_id = REVIEWER_USER_ID
    _create_session(slice_context, REVIEWER_USER_ID)


@given("the User is logged in without reviewer capability for annotation review")
def user_is_logged_in_without_reviewer_capability(slice_context: SliceContext) -> None:
    slice_context.state.store.reviewer_user_ids.clear()
    slice_context.current_user_id = NON_REVIEWER_USER_ID
    _create_session(slice_context, NON_REVIEWER_USER_ID)


@given("the Workspace has accepted the Workspace Data Use Agreement for annotation review")
def workspace_has_accepted_data_use_agreement(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.current_user_id is not None

    response = slice_context.client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": slice_context.workspace_id, "terms_version": "2026-07-29"},
        headers={"x-hivesight-dev-user-id": str(slice_context.current_user_id)},
    )

    assert response.status_code == 200


@given("the Beekeeper has completed stub analysis with bee Annotations")
def beekeeper_has_completed_stub_analysis(slice_context: SliceContext) -> None:
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
        json={"hive_id": hive_id, "inspection_date": str(date(2026, 7, 29))},
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
    slice_context.analysis_run_id = intake_response.json()["analysis_run"]["analysis_run_id"]

    process_response = slice_context.client.post(
        f"/v1/analysis-runs/{slice_context.analysis_run_id}/process",
        json={"workspace_id": slice_context.workspace_id},
        headers={"x-hivesight-dev-user-id": str(slice_context.current_user_id)},
    )
    assert process_response.status_code == 202

    evidence_response = _request_analysis_evidence(slice_context)
    annotations = evidence_response.json()["annotations"]
    slice_context.annotation_id = annotations[0]["annotation_id"]


@when("the Reviewer approves one bee Annotation")
def reviewer_approves_one_bee_annotation(slice_context: SliceContext) -> None:
    _approve_annotation(slice_context)


@when("the User tries to approve one bee Annotation")
def user_tries_to_approve_one_bee_annotation(slice_context: SliceContext) -> None:
    _approve_annotation(slice_context)


@then("the Core API records the Review Decision")
def core_api_records_review_decision(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 201
    assert slice_context.response_body is not None
    assert slice_context.response_body["reviewer_id"] == str(REVIEWER_USER_ID)
    assert slice_context.response_body["subject_type"] == "annotation"
    assert slice_context.response_body["subject_id"] == slice_context.annotation_id
    assert slice_context.response_body["decision"] == "approved"
    assert slice_context.response_body["notes"] == "Accepted as a complete visible bee."


@then("the analysis evidence shows the latest review state for that Annotation")
def evidence_shows_latest_review_state(slice_context: SliceContext) -> None:
    evidence_response = _request_analysis_evidence(slice_context)
    annotations = evidence_response.json()["annotations"]
    reviewed_annotation = next(
        annotation
        for annotation in annotations
        if annotation["annotation_id"] == slice_context.annotation_id
    )

    assert reviewed_annotation["latest_review_decision"]["decision"] == "approved"
    assert reviewed_annotation["latest_review_decision"]["notes"] == (
        "Accepted as a complete visible bee."
    )


@then("the review state does not assign dataset use")
def review_state_does_not_assign_dataset_use(slice_context: SliceContext) -> None:
    assert slice_context.response_body is not None
    assert "dataset_role" not in slice_context.response_body
    assert "training_approved" not in slice_context.response_body.values()


@then("Annotation review is blocked by reviewer authorization")
def annotation_review_is_blocked_by_reviewer_authorization(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 403
    assert slice_context.response_body is not None
    detail = slice_context.response_body["detail"]
    assert isinstance(detail, dict)
    assert detail["code"] == "reviewer_access_required"


def _create_session(slice_context: SliceContext, user_id: UUID) -> None:
    response = slice_context.client.get(
        "/v1/dev/session",
        headers={"x-hivesight-dev-user-id": str(user_id)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "owner"
    slice_context.workspace_id = body["workspace_id"]


def _approve_annotation(slice_context: SliceContext) -> None:
    assert slice_context.current_user_id is not None
    assert slice_context.workspace_id is not None
    assert slice_context.annotation_id is not None

    response = slice_context.client.post(
        "/v1/review-decisions",
        json={
            "workspace_id": slice_context.workspace_id,
            "subject_type": "annotation",
            "subject_id": slice_context.annotation_id,
            "decision": "approved",
            "notes": "Accepted as a complete visible bee.",
        },
        headers={"x-hivesight-dev-user-id": str(slice_context.current_user_id)},
    )
    slice_context.response_status_code = response.status_code
    slice_context.response_body = response.json()


def _request_analysis_evidence(slice_context: SliceContext):
    assert slice_context.current_user_id is not None
    assert slice_context.workspace_id is not None
    assert slice_context.analysis_run_id is not None

    return slice_context.client.get(
        f"/v1/analysis-runs/{slice_context.analysis_run_id}/evidence"
        f"?workspace_id={slice_context.workspace_id}",
        headers={"x-hivesight-dev-user-id": str(slice_context.current_user_id)},
    )
