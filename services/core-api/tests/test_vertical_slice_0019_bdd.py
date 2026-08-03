from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when
from test_review_queue_slice import (
    CURATOR_ID,
    REVIEWER_1_ID,
    REVIEWER_2_ID,
    _completed_training_crop,
    _headers,
    _request_review,
)

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

FEATURES_DIR = Path(__file__).parent / "features"
scenarios(str(FEATURES_DIR / "vertical_slice_0019_reviewer_work_queue.feature"))


@dataclass
class SliceContext:
    client: TestClient
    crop: dict[str, object] | None = None
    item: dict[str, object] | None = None
    opened_item: dict[str, object] | None = None
    completion: object | None = None
    second_completion: object | None = None
    reviewer_2_work: dict[str, object] | None = None
    cancellation: dict[str, object] | None = None
    second_item: dict[str, object] | None = None


@pytest.fixture
def slice_context() -> SliceContext:
    state = build_dev_state(
        dev_users_enabled=True,
        id_values=[UUID(f"00000000-0000-0000-0000-{index:012d}") for index in range(19111, 19180)],
        clock=lambda: datetime(2026, 8, 3, 13, 0, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    try:
        yield SliceContext(client=TestClient(app))
    finally:
        app.dependency_overrides.clear()


@given("a Dataset Curator has requested review for a completed Training Crop")
def curator_has_requested_review(slice_context: SliceContext) -> None:
    crop = _completed_training_crop(slice_context.client)
    slice_context.crop = crop
    slice_context.item = _request_review(slice_context.client, crop)


@given("two eligible Reviewers can see the same available Review Queue Item")
def two_reviewers_can_see_item(slice_context: SliceContext) -> None:
    curator_has_requested_review(slice_context)
    reviewer_1_work = slice_context.client.get(
        "/v1/review-queue/work",
        headers=_headers(REVIEWER_1_ID),
    )
    reviewer_2_work = slice_context.client.get(
        "/v1/review-queue/work",
        headers=_headers(REVIEWER_2_ID),
    )
    assert reviewer_1_work.status_code == 200
    assert reviewer_2_work.status_code == 200
    assert reviewer_1_work.json()["review_queue_items"][0]["review_queue_item_id"] == slice_context.item["review_queue_item_id"]
    assert reviewer_2_work.json()["review_queue_items"][0]["review_queue_item_id"] == slice_context.item["review_queue_item_id"]


@given("a Dataset Curator has an available Review Queue Item for a Training Crop")
def curator_has_available_item(slice_context: SliceContext) -> None:
    curator_has_requested_review(slice_context)


@when("an eligible Reviewer opens the Review Queue Item")
def reviewer_opens_item(slice_context: SliceContext) -> None:
    assert slice_context.item is not None
    response = slice_context.client.get(
        f"/v1/review-queue/items/{slice_context.item['review_queue_item_id']}",
        headers=_headers(REVIEWER_1_ID),
    )
    assert response.status_code == 200
    slice_context.opened_item = response.json()


@when("one Reviewer completes the Review Queue Item as approved")
def reviewer_completes_item(slice_context: SliceContext) -> None:
    assert slice_context.item is not None
    slice_context.completion = slice_context.client.post(
        f"/v1/review-queue/items/{slice_context.item['review_queue_item_id']}/outcomes",
        json={"review_outcome": "approved"},
        headers=_headers(REVIEWER_1_ID),
    )


@when("the Dataset Curator cancels the Review Queue Item with cancellation notes")
def curator_cancels_item(slice_context: SliceContext) -> None:
    assert slice_context.item is not None
    response = slice_context.client.post(
        f"/v1/review-queue/items/{slice_context.item['review_queue_item_id']}/cancel",
        json={"cancellation_notes": "Need to adjust the crop first."},
        headers=_headers(CURATOR_ID),
    )
    assert response.status_code == 200
    slice_context.cancellation = response.json()


@then("the Reviewer sees the Training Crop image and reviewed bee ellipses")
def reviewer_sees_crop_evidence(slice_context: SliceContext) -> None:
    assert slice_context.opened_item is not None
    snapshot = slice_context.opened_item["evidence_snapshot"]
    assert snapshot["image_view_url"].startswith("/v1/review-queue/items/")
    assert len(snapshot["reviewed_ellipses"]) == 2


@then("the Reviewer sees safe crop metadata")
def reviewer_sees_safe_metadata(slice_context: SliceContext) -> None:
    assert slice_context.opened_item is not None
    snapshot = slice_context.opened_item["evidence_snapshot"]
    assert snapshot["safe_source_label"].startswith("Training Crop ")
    assert snapshot["crop_width"] == 100
    assert snapshot["reviewed_ellipse_count"] == 2
    assert slice_context.opened_item["request_notes"] is None


@then("the Reviewer does not see unsafe Workspace metadata")
def reviewer_does_not_see_unsafe_metadata(slice_context: SliceContext) -> None:
    assert slice_context.opened_item is not None
    snapshot = slice_context.opened_item["evidence_snapshot"]
    assert "filename" not in snapshot
    assert "apiary" not in snapshot
    assert "hive" not in snapshot
    assert "workspace" not in snapshot
    assert "requested_by_user_id" not in slice_context.opened_item
    assert "original_crop_reviewer_user_id" not in slice_context.opened_item


@then("the Review Queue Item is no longer available to any Reviewer")
def item_no_longer_available(slice_context: SliceContext) -> None:
    assert slice_context.item is not None
    assert slice_context.completion is not None
    assert slice_context.completion.status_code == 201
    reviewer_1_work = slice_context.client.get(
        "/v1/review-queue/work",
        headers=_headers(REVIEWER_1_ID),
    )
    reviewer_2_work = slice_context.client.get(
        "/v1/review-queue/work",
        headers=_headers(REVIEWER_2_ID),
    )
    assert reviewer_1_work.json()["review_queue_items"] == []
    assert reviewer_2_work.json()["review_queue_items"] == []


@then("another Reviewer cannot complete the same Review Queue Item")
def another_reviewer_cannot_complete(slice_context: SliceContext) -> None:
    assert slice_context.item is not None
    response = slice_context.client.post(
        f"/v1/review-queue/items/{slice_context.item['review_queue_item_id']}/outcomes",
        json={"review_outcome": "approved"},
        headers=_headers(REVIEWER_2_ID),
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "review_queue_item_already_completed"


@then("the Review Queue Item status becomes cancelled")
def item_is_cancelled(slice_context: SliceContext) -> None:
    assert slice_context.cancellation is not None
    assert slice_context.cancellation["status"] == "cancelled"
    assert slice_context.cancellation["cancellation_notes"] == "Need to adjust the crop first."


@then("the Dataset Curator can request a new review for the Training Crop")
def curator_can_request_new_review(slice_context: SliceContext) -> None:
    assert slice_context.crop is not None
    response = slice_context.client.post(
        "/v1/review-queue/items",
        json={
            "workspace_id": slice_context.crop["workspace_id"],
            "training_crop_id": slice_context.crop["training_crop_id"],
        },
        headers=_headers(CURATOR_ID),
    )
    assert response.status_code == 201
    assert response.json()["human_readable_id"] == "HS-RQ-000002"
