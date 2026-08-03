from datetime import UTC, date, datetime
from uuid import UUID

from fastapi.testclient import TestClient
from hive_configuration_test_support import configure_hive

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

CURATOR_ID = UUID("00000000-0000-0000-0000-000000000104")
REVIEWER_1_ID = UUID("00000000-0000-0000-0000-000000000105")
REVIEWER_2_ID = UUID("00000000-0000-0000-0000-000000000106")
BASIC_OWNER_ID = UUID("00000000-0000-0000-0000-000000000109")


def test_curator_requests_review_and_eligible_reviewer_sees_safe_queue_evidence() -> None:
    state = build_dev_state(
        dev_users_enabled=True,
        id_values=[UUID(f"00000000-0000-0000-0000-{index:012d}") for index in range(19001, 19030)],
        clock=lambda: datetime(2026, 8, 3, 10, 0, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        crop = _completed_training_crop(client)

        request_response = client.post(
            "/v1/review-queue/items",
            json={
                "workspace_id": crop["workspace_id"],
                "training_crop_id": crop["training_crop_id"],
                "request_notes": "Please check the bee outlines.",
            },
            headers=_headers(CURATOR_ID),
        )
        reviewer_work = client.get("/v1/review-queue/work", headers=_headers(REVIEWER_1_ID))
        requester_work = client.get("/v1/review-queue/work", headers=_headers(CURATOR_ID))
        basic_owner_work = client.get("/v1/review-queue/work", headers=_headers(BASIC_OWNER_ID))

        assert request_response.status_code == 201
        item = request_response.json()
        assert item["human_readable_id"] == "HS-RQ-000001"
        assert item["status"] == "available"
        assert item["request_notes"] == "Please check the bee outlines."

        assert reviewer_work.status_code == 200
        queued_item = reviewer_work.json()["review_queue_items"][0]
        snapshot = queued_item["evidence_snapshot"]
        assert queued_item["human_readable_id"] == "HS-RQ-000001"
        assert snapshot["safe_source_label"].startswith("Training Crop ")
        assert snapshot["reviewed_ellipse_count"] == 2
        assert snapshot["complete_visible_bee_count"] == 1
        assert snapshot["partial_visible_bee_count"] == 1
        assert "requester" not in queued_item
        assert "original" not in queued_item
        assert "filename" not in snapshot
        assert "apiary" not in snapshot
        assert "hive" not in snapshot
        assert "workspace" not in snapshot

        assert requester_work.status_code == 403
        assert requester_work.json()["detail"]["code"] == "reviewer_access_required"
        assert basic_owner_work.status_code == 403
        assert basic_owner_work.json()["detail"]["code"] == "reviewer_access_required"
    finally:
        app.dependency_overrides.clear()


def test_first_reviewer_completion_closes_queue_item_for_everyone() -> None:
    state = build_dev_state(
        dev_users_enabled=True,
        id_values=[UUID(f"00000000-0000-0000-0000-{index:012d}") for index in range(19031, 19070)],
        clock=lambda: datetime(2026, 8, 3, 11, 0, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        crop = _completed_training_crop(client)
        item = _request_review(client, crop)

        missing_notes = client.post(
            f"/v1/review-queue/items/{item['review_queue_item_id']}/outcomes",
            json={"review_outcome": "changes_requested"},
            headers=_headers(REVIEWER_1_ID),
        )
        completion = client.post(
            f"/v1/review-queue/items/{item['review_queue_item_id']}/outcomes",
            json={"review_outcome": "approved"},
            headers=_headers(REVIEWER_1_ID),
        )
        second_completion = client.post(
            f"/v1/review-queue/items/{item['review_queue_item_id']}/outcomes",
            json={"review_outcome": "approved"},
            headers=_headers(REVIEWER_2_ID),
        )
        reviewer_2_work = client.get("/v1/review-queue/work", headers=_headers(REVIEWER_2_ID))
        reviewer_1_history = client.get("/v1/review-queue/history", headers=_headers(REVIEWER_1_ID))
        requested = client.get(
            "/v1/review-queue/requested",
            params={"workspace_id": crop["workspace_id"]},
            headers=_headers(CURATOR_ID),
        )

        assert missing_notes.status_code == 422
        assert missing_notes.json()["detail"]["code"] == "review_notes_required"
        assert completion.status_code == 201
        assert completion.json()["status"] == "completed"
        assert completion.json()["completed_outcome"] == "approved"
        assert second_completion.status_code == 409
        assert second_completion.json()["detail"]["code"] == "review_queue_item_already_completed"
        assert reviewer_2_work.status_code == 200
        assert reviewer_2_work.json()["review_queue_items"] == []
        assert reviewer_1_history.status_code == 200
        assert reviewer_1_history.json()["review_queue_items"][0]["human_readable_id"] == "HS-RQ-000001"
        assert requested.status_code == 200
        requested_item = requested.json()["review_queue_items"][0]
        assert requested_item["completed_reviewer_display_identity"] == "REVIEWER-1"
    finally:
        app.dependency_overrides.clear()


def test_curator_can_cancel_available_item_and_request_again() -> None:
    state = build_dev_state(
        dev_users_enabled=True,
        id_values=[UUID(f"00000000-0000-0000-0000-{index:012d}") for index in range(19071, 19110)],
        clock=lambda: datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        crop = _completed_training_crop(client)
        item = _request_review(client, crop)

        duplicate = client.post(
            "/v1/review-queue/items",
            json={
                "workspace_id": crop["workspace_id"],
                "training_crop_id": crop["training_crop_id"],
            },
            headers=_headers(CURATOR_ID),
        )
        edit_while_available = client.patch(
            f"/v1/training-crops/{crop['training_crop_id']}",
            json={"workspace_id": crop["workspace_id"], "review_status": "review_pending"},
            headers=_headers(CURATOR_ID),
        )
        reviewer_cancel = client.post(
            f"/v1/review-queue/items/{item['review_queue_item_id']}/cancel",
            json={"cancellation_notes": "Reviewer should not cancel."},
            headers=_headers(REVIEWER_1_ID),
        )
        cancelled = client.post(
            f"/v1/review-queue/items/{item['review_queue_item_id']}/cancel",
            json={"cancellation_notes": "Need to adjust the crop first."},
            headers=_headers(CURATOR_ID),
        )
        edit_after_cancel = client.patch(
            f"/v1/training-crops/{crop['training_crop_id']}",
            json={"workspace_id": crop["workspace_id"], "review_status": "review_pending"},
            headers=_headers(CURATOR_ID),
        )
        recompleted = client.patch(
            f"/v1/training-crops/{crop['training_crop_id']}",
            json={
                "workspace_id": crop["workspace_id"],
                "visible_bee_status": "has_visible_bees",
                "review_status": "review_complete",
            },
            headers=_headers(CURATOR_ID),
        )
        second_item = client.post(
            "/v1/review-queue/items",
            json={
                "workspace_id": crop["workspace_id"],
                "training_crop_id": crop["training_crop_id"],
            },
            headers=_headers(CURATOR_ID),
        )

        assert duplicate.status_code == 409
        assert duplicate.json()["detail"]["code"] == "review_queue_item_already_available"
        assert edit_while_available.status_code == 409
        assert edit_while_available.json()["detail"]["code"] == "training_crop_review_request_active"
        assert reviewer_cancel.status_code == 403
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "cancelled"
        assert edit_after_cancel.status_code == 200
        assert recompleted.status_code == 200
        assert second_item.status_code == 201
        assert second_item.json()["human_readable_id"] == "HS-RQ-000002"
    finally:
        app.dependency_overrides.clear()


def _completed_training_crop(client: TestClient) -> dict[str, object]:
    workspace_id = client.get("/v1/dev/session", headers=_headers(CURATOR_ID)).json()["workspace_id"]
    apiaries = client.get(
        "/v1/apiaries",
        params={"workspace_id": workspace_id},
        headers=_headers(CURATOR_ID),
    ).json()["apiaries"]
    hives = client.get(
        f"/v1/apiaries/{apiaries[0]['apiary_id']}/hives",
        params={"workspace_id": workspace_id},
        headers=_headers(CURATOR_ID),
    ).json()["hives"]
    configure_hive(
        client,
        workspace_id=workspace_id,
        hive_id=hives[0]["hive_id"],
        headers=_headers(CURATOR_ID),
    )
    inspection = client.post(
        "/v1/inspections",
        json={
            "hive_id": hives[0]["hive_id"],
            "inspection_date": str(date(2026, 8, 3)),
            "intent": "training_data_collection",
        },
        headers=_headers(CURATOR_ID),
    ).json()
    intake = client.post(
        f"/v1/inspection-photos/intake?workspace_id={workspace_id}&inspection_id={inspection['inspection_id']}",
        content=_minimal_png(),
        headers={
            **_headers(CURATOR_ID),
            "content-type": "image/png",
            "x-hivesight-filename": "private-frame-name.png",
        },
    ).json()
    photo_id = intake["inspection_photo"]["inspection_photo_id"]
    crop = client.post(
        "/v1/training-crops",
        json={
            "workspace_id": workspace_id,
            "inspection_photo_id": photo_id,
            "crop_x": 10,
            "crop_y": 20,
            "crop_width": 100,
            "crop_height": 120,
            "source_image_width_px": 1600,
            "source_image_height_px": 1200,
        },
        headers=_headers(CURATOR_ID),
    ).json()
    for annotation_type, center_x in (
        ("complete_visible_bee", 50),
        ("partial_visible_bee", 12),
    ):
        response = client.post(
            f"/v1/training-crops/{crop['training_crop_id']}/bee-ellipses",
            json={
                "workspace_id": workspace_id,
                "annotation_type": annotation_type,
                "center_x": center_x,
                "center_y": 70,
                "radius_x": 20,
                "radius_y": 12,
                "rotation_degrees": 15,
            },
            headers=_headers(CURATOR_ID),
        )
        assert response.status_code == 201
    completed = client.patch(
        f"/v1/training-crops/{crop['training_crop_id']}",
        json={
            "workspace_id": workspace_id,
            "visible_bee_status": "has_visible_bees",
            "review_status": "review_complete",
        },
        headers=_headers(CURATOR_ID),
    )
    assert completed.status_code == 200
    return completed.json()


def _request_review(client: TestClient, crop: dict[str, object]) -> dict[str, object]:
    response = client.post(
        "/v1/review-queue/items",
        json={
            "workspace_id": crop["workspace_id"],
            "training_crop_id": crop["training_crop_id"],
        },
        headers=_headers(CURATOR_ID),
    )
    assert response.status_code == 201
    return response.json()


def _headers(user_id: UUID) -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(user_id)}


def _minimal_png() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
        b"\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01"
        b"\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
    )
