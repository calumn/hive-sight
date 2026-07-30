from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

FEATURES_DIR = Path(__file__).parent / "features"
USER_ID = UUID("00000000-0000-0000-0000-000000000101")
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000202")

scenarios(str(FEATURES_DIR / "vertical_slice_0003_annotation_evidence_review.feature"))


@dataclass
class SliceContext:
    client: TestClient
    workspace_id: str | None = None
    analysis_run_id: str | None = None
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
        ],
        clock=lambda: datetime(2026, 7, 29, 13, 15, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    try:
        yield SliceContext(client=TestClient(app))
    finally:
        app.dependency_overrides.clear()


@given("the User is logged in with an owner Workspace Membership for evidence review")
def user_is_logged_in_with_owner_workspace(slice_context: SliceContext) -> None:
    response = slice_context.client.get(
        "/v1/dev/session",
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "owner"
    slice_context.workspace_id = body["workspace_id"]


@given("the Workspace has accepted the Workspace Data Use Agreement for evidence review")
def workspace_has_accepted_data_use_agreement(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None

    response = slice_context.client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": slice_context.workspace_id, "terms_version": "2026-07-29"},
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


@given("the Beekeeper has uploaded and processed an Inspection Photo")
def beekeeper_has_uploaded_and_processed_inspection_photo(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None

    apiary_id = slice_context.client.post(
        "/v1/apiaries",
        json={"workspace_id": slice_context.workspace_id, "name": "Home apiary"},
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    ).json()["apiary_id"]
    hive_id = slice_context.client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": "Hive A"},
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    ).json()["hive_id"]
    inspection_id = slice_context.client.post(
        "/v1/inspections",
        json={
            "hive_id": hive_id,
            "inspection_date": str(date(2026, 7, 29)),
            "intent": "varroa_assessment",
        },
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    ).json()["inspection_id"]

    intake_response = slice_context.client.post(
        "/v1/inspection-photos/intake"
        f"?workspace_id={slice_context.workspace_id}&inspection_id={inspection_id}",
        content=b"fake-image-bytes",
        headers={
            "content-type": "image/jpeg",
            "x-hivesight-dev-user-id": str(USER_ID),
            "x-hivesight-filename": "frame-1.jpg",
        },
    )
    assert intake_response.status_code == 202
    slice_context.analysis_run_id = intake_response.json()["analysis_run"]["analysis_run_id"]

    process_response = slice_context.client.post(
        f"/v1/analysis-runs/{slice_context.analysis_run_id}/process",
        json={"workspace_id": slice_context.workspace_id},
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    )
    assert process_response.status_code == 202


@when("the Beekeeper requests analysis evidence for the Analysis Run")
def beekeeper_requests_analysis_evidence(slice_context: SliceContext) -> None:
    _request_analysis_evidence(slice_context=slice_context, user_id=USER_ID)


@when("another User requests analysis evidence for the Analysis Run")
def another_user_requests_analysis_evidence(slice_context: SliceContext) -> None:
    _request_analysis_evidence(slice_context=slice_context, user_id=OTHER_USER_ID)


@then("the Core API returns the original Inspection Photo evidence reference")
def core_api_returns_original_photo_evidence_reference(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 200
    assert slice_context.response_body is not None
    photo = slice_context.response_body["inspection_photo"]
    assert isinstance(photo, dict)
    assert photo["filename"] == "frame-1.jpg"
    assert str(photo["view_url"]).startswith("/v1/inspection-photos/")


@then("the Core API returns complete and partial visible bee Annotations")
def core_api_returns_bee_annotations(slice_context: SliceContext) -> None:
    assert slice_context.response_body is not None
    annotations = slice_context.response_body["annotations"]
    assert isinstance(annotations, list)
    assert [annotation["annotation_type"] for annotation in annotations] == [
        "complete_visible_bee",
        "complete_visible_bee",
        "complete_visible_bee",
        "partial_visible_bee",
    ]
    assert all(annotation["coordinate_space"] == "normalized" for annotation in annotations)
    assert all(annotation["source_image_width_px"] == 1600 for annotation in annotations)
    assert all(annotation["source_image_height_px"] == 1200 for annotation in annotations)


@then("the Core API returns counts that match the bee Annotations")
def core_api_returns_counts_matching_annotations(slice_context: SliceContext) -> None:
    assert slice_context.response_body is not None
    result = slice_context.response_body["analysis_result"]
    assert isinstance(result, dict)
    assert result["complete_visible_bee_count"] == 3
    assert result["partial_visible_bee_count"] == 1
    assert result["likely_varroa_detections"] == 0


@then("the Core API identifies the evidence as deterministic stub evidence")
def core_api_identifies_evidence_as_stub(slice_context: SliceContext) -> None:
    assert slice_context.response_body is not None
    assert "deterministic stub" in str(slice_context.response_body["caveat"]).lower()


@then("evidence viewing is blocked by Workspace authorization")
def evidence_viewing_is_blocked_by_workspace_authorization(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 403
    assert slice_context.response_body is not None
    detail = slice_context.response_body["detail"]
    assert isinstance(detail, dict)
    assert detail["code"] == "workspace_access_denied"


def _request_analysis_evidence(slice_context: SliceContext, user_id: UUID) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.analysis_run_id is not None

    response = slice_context.client.get(
        f"/v1/analysis-runs/{slice_context.analysis_run_id}/evidence"
        f"?workspace_id={slice_context.workspace_id}",
        headers={"x-hivesight-dev-user-id": str(user_id)},
    )
    slice_context.response_status_code = response.status_code
    slice_context.response_body = response.json()
