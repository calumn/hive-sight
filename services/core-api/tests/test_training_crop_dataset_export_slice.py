from datetime import UTC, date, datetime
from uuid import UUID

from fastapi.testclient import TestClient
from hive_configuration_test_support import configure_hive

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

USER_ID = UUID("00000000-0000-0000-0000-000000000101")


def test_completed_training_crop_can_be_assigned_to_dataset_item_with_snapshot() -> None:
    state = _build_state()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, crop = _create_completed_training_crop(client)

        response = _assign_crop(
            client,
            workspace_id,
            crop["training_crop_id"],
            dataset_role="training",
            assignment_note="Good small crop for first bee detector training.",
        )
        duplicate = _assign_crop(
            client,
            workspace_id,
            crop["training_crop_id"],
            dataset_role="validation",
        )

        assert response.status_code == 201
        body = response.json()
        assert body["source_evidence_type"] == "training_crop"
        assert body["training_crop_id"] == crop["training_crop_id"]
        assert body["labelling_session_id"] is None
        assert body["dataset_role"] == "training"
        assert body["benchmark_protected"] is False
        assert body["crop_x"] == crop["crop_x"]
        assert body["crop_width"] == crop["crop_width"]
        assert body["curriculum_stage"] == "small_crop"
        assert body["permission_status"] == "workspace_data_use_agreement_accepted"
        assert body["provenance"]["workspace_id"] == workspace_id
        assert body["provenance"]["training_crop_id"] == crop["training_crop_id"]
        assert len(body["reviewed_annotation_ids"]) == 1
        assert len(body["reviewed_ellipse_snapshots"]) == 1
        assert body["reviewed_ellipse_snapshots"][0]["annotation_type"] == "complete_visible_bee"
        assert body["reviewed_ellipse_snapshots"][0]["center_x"] == 300
        assert duplicate.status_code == 409
        assert duplicate.json()["detail"]["code"] == "dataset_item_already_assigned"
    finally:
        app.dependency_overrides.clear()


def test_training_crop_dataset_item_assignment_enforces_review_and_exclusion_rules() -> None:
    state = _build_state()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, inspection_photo_id = _upload_photo(client)
        pending_crop = _create_crop(client, workspace_id, inspection_photo_id, crop_x=100).json()
        no_bees_crop = _create_crop(client, workspace_id, inspection_photo_id, crop_x=760).json()
        excluded_crop = _create_crop(client, workspace_id, inspection_photo_id, crop_x=100, crop_y=520).json()

        no_bees_complete = client.patch(
            f"/v1/training-crops/{no_bees_crop['training_crop_id']}",
            json={
                "workspace_id": workspace_id,
                "visible_bee_status": "no_visible_bees",
                "review_status": "review_complete",
            },
            headers=_headers(),
        )
        excluded = client.patch(
            f"/v1/training-crops/{excluded_crop['training_crop_id']}",
            json={
                "workspace_id": workspace_id,
                "review_status": "excluded",
                "exclusion_reason": "unsuitable_crop",
            },
            headers=_headers(),
        )

        pending_assignment = _assign_crop(
            client,
            workspace_id,
            pending_crop["training_crop_id"],
            dataset_role="training",
        )
        no_bees_training = _assign_crop(
            client,
            workspace_id,
            no_bees_crop["training_crop_id"],
            dataset_role="training",
        )
        no_bees_excluded = _assign_crop(
            client,
            workspace_id,
            no_bees_crop["training_crop_id"],
            dataset_role="excluded",
            exclusion_reason="unsuitable_crop",
            assignment_note="No visible bees are not background training samples yet.",
        )
        excluded_training = _assign_crop(
            client,
            workspace_id,
            excluded_crop["training_crop_id"],
            dataset_role="training",
        )

        assert no_bees_complete.status_code == 200
        assert excluded.status_code == 200
        assert pending_assignment.status_code == 409
        assert pending_assignment.json()["detail"]["code"] == "training_crop_review_required"
        assert no_bees_training.status_code == 409
        assert no_bees_training.json()["detail"]["code"] == "no_visible_bees_requires_excluded_role"
        assert no_bees_excluded.status_code == 201
        assert no_bees_excluded.json()["dataset_role"] == "excluded"
        assert no_bees_excluded.json()["reviewed_ellipse_snapshots"] == []
        assert excluded_training.status_code == 409
        assert (
            excluded_training.json()["detail"]["code"]
            == "training_crop_excluded_requires_excluded_role"
        )
    finally:
        app.dependency_overrides.clear()


def test_yolo_obb_manifest_exports_training_and_validation_without_benchmark_leakage() -> None:
    state = _build_state()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, training_crop = _create_completed_training_crop(client, crop_x=100)
        _, validation_crop = _create_completed_training_crop(client, crop_x=760)
        _, benchmark_crop = _create_completed_training_crop(client, crop_x=100, crop_y=520)
        _, excluded_crop = _create_completed_training_crop(client, crop_x=760, crop_y=520)

        training_item = _assign_crop(
            client,
            workspace_id,
            training_crop["training_crop_id"],
            dataset_role="training",
        ).json()
        validation_item = _assign_crop(
            client,
            workspace_id,
            validation_crop["training_crop_id"],
            dataset_role="validation",
        ).json()
        benchmark_item = _assign_crop(
            client,
            workspace_id,
            benchmark_crop["training_crop_id"],
            dataset_role="benchmark",
            source_group_key="benchmark-frame-001",
        ).json()
        excluded_item = _assign_crop(
            client,
            workspace_id,
            excluded_crop["training_crop_id"],
            dataset_role="excluded",
            exclusion_reason="duplicate_or_near_duplicate",
            assignment_note="Duplicate source group.",
        ).json()

        response = client.post(
            "/v1/dataset-exports/yolo-obb",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        )

        assert response.status_code == 201
        body = response.json()
        assert body["export_format"] == "yolo_obb"
        assert body["label_convention"] == "class x1 y1 x2 y2 x3 y3 x4 y4"
        assert body["coordinate_basis"] == "crop-relative normalized corner points"
        assert body["class_map"] == {"0": "complete_visible_bee", "1": "partial_visible_bee"}
        assert body["training_item_count"] == 1
        assert body["validation_item_count"] == 1
        assert body["benchmark_item_count"] == 1
        assert body["included_dataset_item_ids"] == [
            training_item["dataset_item_id"],
            validation_item["dataset_item_id"],
        ]
        assert body["protected_benchmark_dataset_item_ids"] == [benchmark_item["dataset_item_id"]]
        assert [item["dataset_item_id"] for item in body["excluded_dataset_items"]] == [
            excluded_item["dataset_item_id"]
        ]
        assert len(body["image_entries"]) == 2
        assert len(body["label_entries"]) == 2
        first_label = body["label_entries"][0]
        assert first_label["dataset_item_id"] == training_item["dataset_item_id"]
        assert first_label["split"] == "training"
        assert first_label["class_id"] == 0
        assert first_label["label"] == (
            "0 0.250000 0.281250 0.375000 0.281250 "
            "0.375000 0.343750 0.250000 0.343750"
        )
        assert "derived model-training projections" in body["caveat"]
    finally:
        app.dependency_overrides.clear()


def _build_state():
    return build_dev_state(
        id_values=[
            UUID(f"00000000-0000-0000-0000-000000010{i:03d}") for i in range(1, 80)
        ],
        clock=lambda: datetime(2026, 7, 30, 14, 0, tzinfo=UTC),
    )


def _create_completed_training_crop(
    client: TestClient,
    crop_x: int = 100,
    crop_y: int = 100,
) -> tuple[str, dict[str, object]]:
    workspace_id, inspection_photo_id = _upload_photo(client)
    crop = _create_crop(client, workspace_id, inspection_photo_id, crop_x=crop_x, crop_y=crop_y).json()
    ellipse = client.post(
        f"/v1/training-crops/{crop['training_crop_id']}/bee-ellipses",
        json={
            "workspace_id": workspace_id,
            "annotation_type": "complete_visible_bee",
            "center_x": crop_x + 200,
            "center_y": crop_y + 200,
            "radius_x": 40,
            "radius_y": 20,
            "rotation_degrees": 0,
        },
        headers=_headers(),
    )
    assert ellipse.status_code == 201
    complete = client.patch(
        f"/v1/training-crops/{crop['training_crop_id']}",
        json={
            "workspace_id": workspace_id,
            "visible_bee_status": "has_visible_bees",
            "review_status": "review_complete",
        },
        headers=_headers(),
    )
    assert complete.status_code == 200
    return workspace_id, complete.json()


def _upload_photo(client: TestClient) -> tuple[str, str]:
    workspace_id = client.get("/v1/dev/session", headers=_headers()).json()["workspace_id"]
    client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": workspace_id, "terms_version": "2026-07-30"},
        headers=_headers(),
    )
    apiary_id = client.post(
        "/v1/apiaries",
        json={"workspace_id": workspace_id, "name": "Home apiary"},
        headers=_headers(),
    ).json()["apiary_id"]
    hive_id = client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": "Hive A"},
        headers=_headers(),
    ).json()["hive_id"]
    configure_hive(client, workspace_id=workspace_id, hive_id=hive_id, headers=_headers())
    inspection_id = client.post(
        "/v1/inspections",
        json={
            "hive_id": hive_id,
            "inspection_date": str(date(2026, 7, 30)),
            "intent": "training_data_collection",
        },
        headers=_headers(),
    ).json()["inspection_id"]
    intake = client.post(
        f"/v1/inspection-photos/intake?workspace_id={workspace_id}&inspection_id={inspection_id}",
        content=_minimal_png(),
        headers={
            **_headers(),
            "content-type": "image/png",
            "x-hivesight-filename": "frame.png",
        },
    )
    assert intake.status_code == 202
    return workspace_id, intake.json()["inspection_photo"]["inspection_photo_id"]


def _create_crop(
    client: TestClient,
    workspace_id: str,
    inspection_photo_id: str,
    crop_x: int,
    crop_y: int = 100,
) -> object:
    return client.post(
        "/v1/training-crops",
        json={
            "workspace_id": workspace_id,
            "inspection_photo_id": inspection_photo_id,
            "crop_x": crop_x,
            "crop_y": crop_y,
            "crop_width": 640,
            "crop_height": 640,
            "source_image_width_px": 1600,
            "source_image_height_px": 1200,
        },
        headers=_headers(),
    )


def _assign_crop(
    client: TestClient,
    workspace_id: str,
    training_crop_id: str,
    dataset_role: str,
    source_group_key: str | None = None,
    assignment_note: str | None = None,
    exclusion_reason: str | None = None,
) -> object:
    return client.post(
        f"/v1/training-crops/{training_crop_id}/dataset-item",
        json={
            "workspace_id": workspace_id,
            "dataset_role": dataset_role,
            "source_group_key": source_group_key,
            "assignment_note": assignment_note,
            "exclusion_reason": exclusion_reason,
        },
        headers=_headers(),
    )


def _headers() -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(USER_ID)}


def _minimal_png() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x06@\x00\x00\x04\xb0\x08\x02\x00\x00\x00"
        b"\x3b\x7f\x5b\x4b"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
