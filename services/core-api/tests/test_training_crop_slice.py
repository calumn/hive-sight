from datetime import UTC, date, datetime
from uuid import UUID

from fastapi.testclient import TestClient
from hive_configuration_test_support import configure_hive

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

USER_ID = UUID("00000000-0000-0000-0000-000000000101")


def test_training_crop_requires_training_data_collection_photo() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000009001"),
            UUID("00000000-0000-0000-0000-000000009002"),
            UUID("00000000-0000-0000-0000-000000009003"),
        ],
        clock=lambda: datetime(2026, 7, 30, 9, 0, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, inspection_photo_id = _upload_photo(client, "varroa_assessment")

        response = _create_crop(client, workspace_id, inspection_photo_id)

        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "inspection_intent_not_for_training_crop"
    finally:
        app.dependency_overrides.clear()


def test_training_crop_creation_lists_multiple_crops_for_one_photo() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000009011"),
            UUID("00000000-0000-0000-0000-000000009012"),
            UUID("00000000-0000-0000-0000-000000009013"),
            UUID("00000000-0000-0000-0000-000000009014"),
            UUID("00000000-0000-0000-0000-000000009015"),
        ],
        clock=lambda: datetime(2026, 7, 30, 9, 5, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, inspection_photo_id = _upload_photo(client, "training_data_collection")

        first = _create_crop(client, workspace_id, inspection_photo_id, crop_x=100, crop_y=120)
        second = _create_crop(client, workspace_id, inspection_photo_id, crop_x=760, crop_y=120)
        listing = client.get(
            f"/v1/inspection-photos/{inspection_photo_id}/training-crops"
            f"?workspace_id={workspace_id}",
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )

        assert first.status_code == 201
        assert second.status_code == 201
        assert listing.status_code == 200
        body = listing.json()
        assert [crop["crop_x"] for crop in body["training_crops"]] == [100, 760]
        assert all(crop["review_status"] == "review_pending" for crop in body["training_crops"])
        assert all(crop["visible_bee_status"] == "unassessed" for crop in body["training_crops"])
    finally:
        app.dependency_overrides.clear()


def test_crop_bounds_are_validated_and_lock_after_first_ellipse() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000009021"),
            UUID("00000000-0000-0000-0000-000000009022"),
            UUID("00000000-0000-0000-0000-000000009023"),
            UUID("00000000-0000-0000-0000-000000009024"),
            UUID("00000000-0000-0000-0000-000000009025"),
        ],
        clock=lambda: datetime(2026, 7, 30, 9, 10, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, inspection_photo_id = _upload_photo(client, "training_data_collection")
        invalid = _create_crop(
            client,
            workspace_id,
            inspection_photo_id,
            crop_x=1500,
            crop_y=100,
            crop_width=640,
            crop_height=640,
        )
        crop = _create_crop(client, workspace_id, inspection_photo_id).json()
        moved = client.patch(
            f"/v1/training-crops/{crop['training_crop_id']}",
            json={"workspace_id": workspace_id, "crop_x": 120, "crop_y": 140},
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )
        ellipse = _create_ellipse(client, workspace_id, crop["training_crop_id"])
        locked = client.patch(
            f"/v1/training-crops/{crop['training_crop_id']}",
            json={"workspace_id": workspace_id, "crop_x": 160},
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )

        assert invalid.status_code == 422
        assert invalid.json()["detail"]["code"] == "invalid_crop_bounds"
        assert moved.status_code == 200
        assert moved.json()["crop_x"] == 120
        assert moved.json()["crop_y"] == 140
        assert ellipse.status_code == 201
        assert locked.status_code == 409
        assert locked.json()["detail"]["code"] == "crop_bounds_locked"
    finally:
        app.dependency_overrides.clear()


def test_complete_ellipse_is_persisted_normalized_and_validated_inside_crop() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000009031"),
            UUID("00000000-0000-0000-0000-000000009032"),
            UUID("00000000-0000-0000-0000-000000009033"),
            UUID("00000000-0000-0000-0000-000000009034"),
            UUID("00000000-0000-0000-0000-000000009035"),
        ],
        clock=lambda: datetime(2026, 7, 30, 9, 15, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, inspection_photo_id = _upload_photo(client, "training_data_collection")
        crop = _create_crop(client, workspace_id, inspection_photo_id).json()

        outside = _create_ellipse(
            client,
            workspace_id,
            crop["training_crop_id"],
            center_x=105,
            center_y=105,
            radius_x=40,
            radius_y=20,
        )
        created = _create_ellipse(
            client,
            workspace_id,
            crop["training_crop_id"],
            center_x=320,
            center_y=320,
            radius_x=40,
            radius_y=20,
            rotation_degrees=-10,
        )
        updated = client.patch(
            f"/v1/training-crop-bee-ellipses/{created.json()['annotation_id']}",
            json={
                "workspace_id": workspace_id,
                "annotation_type": "partial_visible_bee",
                "rotation_degrees": 365,
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )
        evidence = client.get(
            f"/v1/training-crops/{crop['training_crop_id']}/evidence?workspace_id={workspace_id}",
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )

        assert outside.status_code == 422
        assert outside.json()["detail"]["code"] == "ellipse_outside_crop_bounds"
        assert created.status_code == 201
        assert created.json()["rotation_degrees"] == 350
        assert updated.status_code == 200
        assert updated.json()["annotation_type"] == "partial_visible_bee"
        assert updated.json()["rotation_degrees"] == 5
        assert evidence.status_code == 200
        assert len(evidence.json()["bee_ellipses"]) == 1
    finally:
        app.dependency_overrides.clear()


def test_partial_visible_bee_ellipse_can_cross_crop_boundary() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000009061"),
            UUID("00000000-0000-0000-0000-000000009062"),
            UUID("00000000-0000-0000-0000-000000009063"),
            UUID("00000000-0000-0000-0000-000000009064"),
            UUID("00000000-0000-0000-0000-000000009065"),
        ],
        clock=lambda: datetime(2026, 7, 30, 9, 17, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, inspection_photo_id = _upload_photo(client, "training_data_collection")
        crop = _create_crop(client, workspace_id, inspection_photo_id).json()

        partial = _create_ellipse(
            client,
            workspace_id,
            crop["training_crop_id"],
            annotation_type="partial_visible_bee",
            center_x=105,
            center_y=320,
            radius_x=40,
            radius_y=20,
        )
        complete = _create_ellipse(
            client,
            workspace_id,
            crop["training_crop_id"],
            center_x=105,
            center_y=320,
            radius_x=40,
            radius_y=20,
        )
        outside_partial = _create_ellipse(
            client,
            workspace_id,
            crop["training_crop_id"],
            annotation_type="partial_visible_bee",
            center_x=20,
            center_y=320,
            radius_x=40,
            radius_y=20,
        )

        assert partial.status_code == 201
        assert partial.json()["annotation_type"] == "partial_visible_bee"
        assert complete.status_code == 422
        assert complete.json()["detail"]["code"] == "ellipse_outside_crop_bounds"
        assert outside_partial.status_code == 422
        assert outside_partial.json()["detail"]["code"] == "ellipse_outside_crop_bounds"
    finally:
        app.dependency_overrides.clear()


def test_crop_review_completion_and_zero_bee_rules() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000009041"),
            UUID("00000000-0000-0000-0000-000000009042"),
            UUID("00000000-0000-0000-0000-000000009043"),
            UUID("00000000-0000-0000-0000-000000009044"),
            UUID("00000000-0000-0000-0000-000000009045"),
            UUID("00000000-0000-0000-0000-000000009046"),
        ],
        clock=lambda: datetime(2026, 7, 30, 9, 20, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, inspection_photo_id = _upload_photo(client, "training_data_collection")
        bee_crop = _create_crop(client, workspace_id, inspection_photo_id, crop_x=100).json()
        empty_crop = _create_crop(client, workspace_id, inspection_photo_id, crop_x=800).json()
        pending_empty_crop = _create_crop(
            client,
            workspace_id,
            inspection_photo_id,
            crop_x=800,
            crop_y=500,
        ).json()

        invalid_complete = client.patch(
            f"/v1/training-crops/{bee_crop['training_crop_id']}",
            json={
                "workspace_id": workspace_id,
                "visible_bee_status": "has_visible_bees",
                "review_status": "review_complete",
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )
        _create_ellipse(client, workspace_id, bee_crop["training_crop_id"], center_x=300)
        valid_complete = client.patch(
            f"/v1/training-crops/{bee_crop['training_crop_id']}",
            json={
                "workspace_id": workspace_id,
                "visible_bee_status": "has_visible_bees",
                "review_status": "review_complete",
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )
        zero_bee_complete = client.patch(
            f"/v1/training-crops/{empty_crop['training_crop_id']}",
            json={
                "workspace_id": workspace_id,
                "visible_bee_status": "no_visible_bees",
                "review_status": "review_complete",
                "notes": "Reviewed crop contains no visible bees.",
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )
        pending_no_bees = client.patch(
            f"/v1/training-crops/{pending_empty_crop['training_crop_id']}",
            json={
                "workspace_id": workspace_id,
                "visible_bee_status": "no_visible_bees",
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )
        no_bees_with_ellipse = _create_ellipse(
            client,
            workspace_id,
            pending_empty_crop["training_crop_id"],
            center_x=900,
            center_y=700,
        )
        terminal_locked = _create_ellipse(
            client,
            workspace_id,
            valid_complete.json()["training_crop_id"],
            center_x=360,
        )

        assert invalid_complete.status_code == 409
        assert invalid_complete.json()["detail"]["code"] == "visible_bees_require_ellipse"
        assert valid_complete.status_code == 200
        assert valid_complete.json()["review_status"] == "review_complete"
        assert zero_bee_complete.status_code == 200
        assert zero_bee_complete.json()["visible_bee_status"] == "no_visible_bees"
        assert pending_no_bees.status_code == 200
        assert no_bees_with_ellipse.status_code == 409
        assert no_bees_with_ellipse.json()["detail"]["code"] == "no_visible_bees_conflicts_with_ellipses"
        assert terminal_locked.status_code == 409
        assert terminal_locked.json()["detail"]["code"] == "training_crop_locked"
    finally:
        app.dependency_overrides.clear()


def test_completed_crop_can_be_reopened_for_additional_annotation() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000009071"),
            UUID("00000000-0000-0000-0000-000000009072"),
            UUID("00000000-0000-0000-0000-000000009073"),
            UUID("00000000-0000-0000-0000-000000009074"),
            UUID("00000000-0000-0000-0000-000000009075"),
            UUID("00000000-0000-0000-0000-000000009076"),
        ],
        clock=lambda: datetime(2026, 7, 30, 9, 22, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, inspection_photo_id = _upload_photo(client, "training_data_collection")
        crop = _create_crop(client, workspace_id, inspection_photo_id).json()
        _create_ellipse(client, workspace_id, crop["training_crop_id"], center_x=300)
        completed = client.patch(
            f"/v1/training-crops/{crop['training_crop_id']}",
            json={
                "workspace_id": workspace_id,
                "visible_bee_status": "has_visible_bees",
                "review_status": "review_complete",
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )
        locked = _create_ellipse(client, workspace_id, crop["training_crop_id"], center_x=360)
        reopened = client.patch(
            f"/v1/training-crops/{crop['training_crop_id']}",
            json={
                "workspace_id": workspace_id,
                "review_status": "review_pending",
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )
        additional = _create_ellipse(
            client,
            workspace_id,
            crop["training_crop_id"],
            annotation_type="partial_visible_bee",
            center_x=105,
            center_y=320,
        )

        assert completed.status_code == 200
        assert completed.json()["review_status"] == "review_complete"
        assert locked.status_code == 409
        assert locked.json()["detail"]["code"] == "training_crop_locked"
        assert reopened.status_code == 200
        assert reopened.json()["review_status"] == "review_pending"
        assert reopened.json()["exclusion_reason"] is None
        assert additional.status_code == 201
    finally:
        app.dependency_overrides.clear()


def test_excluded_crop_records_reason_and_is_locked() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000009051"),
            UUID("00000000-0000-0000-0000-000000009052"),
            UUID("00000000-0000-0000-0000-000000009053"),
            UUID("00000000-0000-0000-0000-000000009054"),
        ],
        clock=lambda: datetime(2026, 7, 30, 9, 25, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, inspection_photo_id = _upload_photo(client, "training_data_collection")
        crop = _create_crop(client, workspace_id, inspection_photo_id).json()

        excluded = client.patch(
            f"/v1/training-crops/{crop['training_crop_id']}",
            json={
                "workspace_id": workspace_id,
                "review_status": "excluded",
                "exclusion_reason": "unsuitable_crop",
                "notes": "Crop is too cluttered for early annotation.",
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )
        locked = client.patch(
            f"/v1/training-crops/{crop['training_crop_id']}",
            json={"workspace_id": workspace_id, "notes": "Try reopening."},
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )

        assert excluded.status_code == 200
        assert excluded.json()["review_status"] == "excluded"
        assert excluded.json()["exclusion_reason"] == "unsuitable_crop"
        assert locked.status_code == 409
        assert locked.json()["detail"]["code"] == "training_crop_locked"
    finally:
        app.dependency_overrides.clear()


def _upload_photo(client: TestClient, intent: str) -> tuple[str, str]:
    workspace_id = client.get(
        "/v1/dev/session",
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    ).json()["workspace_id"]
    client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": workspace_id, "terms_version": "2026-07-30"},
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    )
    apiary_id = client.post(
        "/v1/apiaries",
        json={"workspace_id": workspace_id, "name": "Home apiary"},
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    ).json()["apiary_id"]
    hive_id = client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": "Hive A"},
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    ).json()["hive_id"]
    configure_hive(client, workspace_id=workspace_id, hive_id=hive_id, user_id=USER_ID)
    inspection_id = client.post(
        "/v1/inspections",
        json={
            "hive_id": hive_id,
            "inspection_date": str(date(2026, 7, 30)),
            "intent": intent,
        },
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    ).json()["inspection_id"]
    intake = client.post(
        f"/v1/inspection-photos/intake?workspace_id={workspace_id}&inspection_id={inspection_id}",
        content=_minimal_png(width=1600, height=1200),
        headers={
            "content-type": "image/png",
            "x-hivesight-dev-user-id": str(USER_ID),
            "x-hivesight-filename": "frame.png",
        },
    )
    assert intake.status_code == 202
    return workspace_id, intake.json()["inspection_photo"]["inspection_photo_id"]


def _create_crop(
    client: TestClient,
    workspace_id: str,
    inspection_photo_id: str,
    crop_x: int = 100,
    crop_y: int = 100,
    crop_width: int = 640,
    crop_height: int = 640,
) -> object:
    return client.post(
        "/v1/training-crops",
        json={
            "workspace_id": workspace_id,
            "inspection_photo_id": inspection_photo_id,
            "crop_x": crop_x,
            "crop_y": crop_y,
            "crop_width": crop_width,
            "crop_height": crop_height,
            "source_image_width_px": 1600,
            "source_image_height_px": 1200,
        },
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    )


def _create_ellipse(
    client: TestClient,
    workspace_id: str,
    training_crop_id: str,
    annotation_type: str = "complete_visible_bee",
    center_x: float = 300,
    center_y: float = 300,
    radius_x: float = 40,
    radius_y: float = 20,
    rotation_degrees: float = 0,
) -> object:
    return client.post(
        f"/v1/training-crops/{training_crop_id}/bee-ellipses",
        json={
            "workspace_id": workspace_id,
            "annotation_type": annotation_type,
            "center_x": center_x,
            "center_y": center_y,
            "radius_x": radius_x,
            "radius_y": radius_y,
            "rotation_degrees": rotation_degrees,
        },
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    )


def _minimal_png(width: int, height: int) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        + width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + b"\x08\x02\x00\x00\x00"
    )
