from datetime import UTC, date, datetime
from io import BytesIO
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from hive_configuration_test_support import configure_hive
from PIL import Image

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.dev_store import WorkspaceMembershipRecord
from hive_sight_core_api.main import app

CURATOR_ID = UUID("00000000-0000-0000-0000-000000000101")
OTHER_CURATOR_ID = UUID("00000000-0000-0000-0000-000000000202")
ORDINARY_USER_ID = UUID("00000000-0000-0000-0000-000000000999")


def test_dataset_repository_lists_cross_inspection_items_and_dataset_version_membership(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id = _workspace(client, CURATOR_ID)
        training_item = _create_reviewed_crop_item(
            client,
            workspace_id,
            dataset_role="training",
            crop_x=10,
            crop_y=10,
            filename="training-frame.png",
            inspection_date=date(2026, 8, 1),
        )
        validation_item = _create_reviewed_crop_item(
            client,
            workspace_id,
            dataset_role="validation",
            crop_x=260,
            crop_y=10,
            filename="validation-frame.png",
            inspection_date=date(2026, 8, 2),
        )
        _create_reviewed_crop_item(
            client,
            workspace_id,
            dataset_role="benchmark",
            crop_x=10,
            crop_y=260,
            filename="benchmark-frame.png",
            inspection_date=date(2026, 8, 3),
            source_group_key="protected-benchmark-frame",
        )

        dataset_version = client.post(
            "/v1/model-training/dataset-versions",
            json={"workspace_id": workspace_id},
            headers=_headers(CURATOR_ID),
        )
        assert dataset_version.status_code == 201

        listing = client.get(
            f"/v1/dataset-repository/items?workspace_id={workspace_id}",
            headers=_headers(CURATOR_ID),
        )
        assert listing.status_code == 200
        body = listing.json()
        assert body["summary"]["role_counts"]["training"] == 1
        assert body["summary"]["role_counts"]["validation"] == 1
        assert body["summary"]["role_counts"]["benchmark"] == 1
        assert body["summary"]["annotation_class_counts"]["complete_visible_bee"] == 3
        assert body["summary"]["new_since_latest_dataset_version_count"] == 0
        assert body["summary"]["persistence_backend"] == "in_memory"
        assert len(body["summary"]["inspection_distribution"]) == 3
        assert [item["dataset_role"] for item in body["items"]] == [
            "training",
            "validation",
            "benchmark",
        ]
        assert body["items"][0]["source_filename"] == "training-frame.png"
        assert body["items"][0]["latest_dataset_version_membership"]["membership"] == "training"
        assert body["items"][1]["latest_dataset_version_membership"]["membership"] == "validation"
        assert body["items"][2]["latest_dataset_version_membership"]["membership"] == "protected_benchmark"
        assert body["items"][2]["benchmark_protected"] is True

        detail = client.get(
            f"/v1/dataset-repository/items/{training_item}?workspace_id={workspace_id}",
            headers=_headers(CURATOR_ID),
        )
        assert detail.status_code == 200
        detail_body = detail.json()
        assert detail_body["human_readable_id"] == "HS-DI-000001"
        assert detail_body["complete_visible_bee_count"] == 1
        assert detail_body["partial_visible_bee_count"] == 0
        assert detail_body["preview_status"] == "available"
        assert detail_body["preview_url"].startswith("/v1/inspection-photos/")
        assert detail_body["dataset_version_memberships"][0]["membership"] == "training"
        assert detail_body["reviewed_ellipse_snapshots"][0]["annotation_type"] == "complete_visible_bee"

        validation_listing = client.get(
            f"/v1/dataset-repository/items?workspace_id={workspace_id}&dataset_role=validation",
            headers=_headers(CURATOR_ID),
        )
        assert validation_listing.status_code == 200
        assert [item["dataset_item_id"] for item in validation_listing.json()["items"]] == [
            validation_item
        ]
    finally:
        app.dependency_overrides.clear()


def test_dataset_repository_blocks_cross_workspace_and_non_curator_access(tmp_path: Path) -> None:
    state = _build_state(tmp_path)
    state.store.dataset_curator_user_ids.add(OTHER_CURATOR_ID)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_a = _workspace(client, CURATOR_ID)
        workspace_b = _workspace(client, OTHER_CURATOR_ID)
        item_a = _create_reviewed_crop_item(client, workspace_a, "training", 10, 10, "a.png")
        item_b = _create_reviewed_crop_item(client, workspace_b, "training", 10, 10, "b.png", OTHER_CURATOR_ID)
        state.store.memberships.append(
            WorkspaceMembershipRecord(user_id=ORDINARY_USER_ID, workspace_id=UUID(workspace_a))
        )

        listing = client.get(
            f"/v1/dataset-repository/items?workspace_id={workspace_a}",
            headers=_headers(CURATOR_ID),
        )
        assert listing.status_code == 200
        assert [item["dataset_item_id"] for item in listing.json()["items"]] == [item_a]
        assert item_b not in [item["dataset_item_id"] for item in listing.json()["items"]]

        cross_workspace_detail = client.get(
            f"/v1/dataset-repository/items/{item_b}?workspace_id={workspace_a}",
            headers=_headers(CURATOR_ID),
        )
        assert cross_workspace_detail.status_code == 404
        assert cross_workspace_detail.json()["detail"]["code"] == "dataset_item_not_found"

        blocked = client.get(
            f"/v1/dataset-repository/items?workspace_id={workspace_a}",
            headers=_headers(ORDINARY_USER_ID),
        )
        assert blocked.status_code == 403
        assert blocked.json()["detail"]["code"] == "dataset_curator_access_required"
    finally:
        app.dependency_overrides.clear()


def _build_state(tmp_path: Path):
    return build_dev_state(
        id_values=[UUID(f"00000000-0000-0000-0000-000000153{i:03d}") for i in range(1, 260)],
        clock=lambda: datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
        dataset_export_root=tmp_path / "exports",
        model_artifact_root=tmp_path / "model-runs",
    )


def _workspace(client: TestClient, user_id: UUID) -> str:
    workspace_id = client.get("/v1/dev/session", headers=_headers(user_id)).json()["workspace_id"]
    response = client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": workspace_id, "terms_version": "2026-08-01"},
        headers=_headers(user_id),
    )
    assert response.status_code == 200
    return workspace_id


def _create_reviewed_crop_item(
    client: TestClient,
    workspace_id: str,
    dataset_role: str,
    crop_x: int,
    crop_y: int,
    filename: str,
    user_id: UUID = CURATOR_ID,
    inspection_date: date = date(2026, 8, 1),
    source_group_key: str | None = None,
) -> str:
    apiary_id = client.post(
        "/v1/apiaries",
        json={"workspace_id": workspace_id, "name": f"Apiary {filename}"},
        headers=_headers(user_id),
    ).json()["apiary_id"]
    hive_id = client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": f"Hive {filename}"},
        headers=_headers(user_id),
    ).json()["hive_id"]
    configure_hive(client, workspace_id=workspace_id, hive_id=hive_id, headers=_headers(user_id))
    inspection_id = client.post(
        "/v1/inspections",
        json={
            "hive_id": hive_id,
            "inspection_date": str(inspection_date),
            "intent": "training_data_collection",
        },
        headers=_headers(user_id),
    ).json()["inspection_id"]
    intake = client.post(
        f"/v1/inspection-photos/intake?workspace_id={workspace_id}&inspection_id={inspection_id}",
        content=_source_png(),
        headers={
            **_headers(user_id),
            "content-type": "image/png",
            "x-hivesight-filename": filename,
        },
    )
    assert intake.status_code == 202
    inspection_photo_id = intake.json()["inspection_photo"]["inspection_photo_id"]
    crop = client.post(
        "/v1/training-crops",
        json={
            "workspace_id": workspace_id,
            "inspection_photo_id": inspection_photo_id,
            "crop_x": crop_x,
            "crop_y": crop_y,
            "crop_width": 200,
            "crop_height": 200,
            "source_image_width_px": 640,
            "source_image_height_px": 480,
        },
        headers=_headers(user_id),
    ).json()
    ellipse = client.post(
        f"/v1/training-crops/{crop['training_crop_id']}/bee-ellipses",
        json={
            "workspace_id": workspace_id,
            "annotation_type": "complete_visible_bee",
            "center_x": crop_x + 80,
            "center_y": crop_y + 80,
            "radius_x": 24,
            "radius_y": 12,
            "rotation_degrees": 15,
        },
        headers=_headers(user_id),
    )
    assert ellipse.status_code == 201
    completed = client.patch(
        f"/v1/training-crops/{crop['training_crop_id']}",
        json={
            "workspace_id": workspace_id,
            "visible_bee_status": "has_visible_bees",
            "review_status": "review_complete",
        },
        headers=_headers(user_id),
    )
    assert completed.status_code == 200
    assignment = client.post(
        f"/v1/training-crops/{crop['training_crop_id']}/dataset-item",
        json={
            "workspace_id": workspace_id,
            "dataset_role": dataset_role,
            "source_group_key": source_group_key or f"{dataset_role}-{filename}",
        },
        headers=_headers(user_id),
    )
    assert assignment.status_code == 201
    return assignment.json()["dataset_item_id"]


def _headers(user_id: UUID = CURATOR_ID) -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(user_id)}


def _source_png() -> bytes:
    image = Image.new("RGB", (640, 480), color=(240, 220, 180))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
