import json
from datetime import UTC, date, datetime
from io import BytesIO
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from PIL import Image

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

USER_ID = UUID("00000000-0000-0000-0000-000000000101")


def test_frame_standard_catalogue_splits_british_national_and_wbc_metadata() -> None:
    state = build_dev_state()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        response = client.get("/v1/frame-standards", headers=_headers())

        assert response.status_code == 200
        standards = {standard["frame_standard_id"]: standard for standard in response.json()}
        assert standards["british_national_deep_brood"]["hive_type"] == "british_national"
        assert standards["british_national_deep_brood"]["side_bar_height_mm"] == 216
        assert standards["wbc_deep_brood"]["hive_type"] == "wbc"
        assert standards["unknown"]["status"] == "unknown"
        assert standards["unknown"]["top_bar_length_mm"] is None
        assert standards["other"]["status"] == "other"
    finally:
        app.dependency_overrides.clear()


def test_inspection_creation_requires_hive_configuration() -> None:
    state = _build_state()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, hive_id = _create_hive_without_configuration(client)

        blocked = client.post(
            "/v1/inspections",
            json={
                "hive_id": hive_id,
                "inspection_date": str(date(2026, 7, 30)),
                "intent": "training_data_collection",
            },
            headers=_headers(),
        )
        configured = _configure_hive(client, workspace_id, hive_id)
        accepted = client.post(
            "/v1/inspections",
            json={
                "hive_id": hive_id,
                "inspection_date": str(date(2026, 7, 30)),
                "intent": "training_data_collection",
            },
            headers=_headers(),
        )

        assert blocked.status_code == 409
        assert blocked.json()["detail"]["code"] == "hive_configuration_required"
        assert configured["hive_type"] == "british_national"
        assert configured["frame_use"] == "deep_brood"
        assert accepted.status_code == 201
    finally:
        app.dependency_overrides.clear()


def test_other_frame_standard_requires_notes_but_unknown_does_not() -> None:
    state = _build_state()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, hive_id = _create_hive_without_configuration(client)

        other_without_notes = _configure_hive(
            client,
            workspace_id,
            hive_id,
            frame_standard_id="other",
            expect_status=422,
        )
        unknown_without_notes = _configure_hive(
            client,
            workspace_id,
            hive_id,
            frame_standard_id="unknown",
        )
        other_with_notes = _configure_hive(
            client,
            workspace_id,
            hive_id,
            frame_standard_id="other",
            notes="Prototype hive equipment; dimensions to be measured.",
        )

        assert other_without_notes["detail"]["code"] == "hive_configuration_notes_required"
        assert unknown_without_notes["frame_standard_id"] == "unknown"
        assert unknown_without_notes["hive_type"] == "unknown"
        assert other_with_notes["frame_standard_id"] == "other"
        assert other_with_notes["notes"] == "Prototype hive equipment; dimensions to be measured."
    finally:
        app.dependency_overrides.clear()


def test_dataset_item_and_physical_export_manifest_keep_hive_configuration_snapshot(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, hive_id = _create_hive_without_configuration(client)
        _configure_hive(client, workspace_id, hive_id, frame_standard_id="british_national_deep_brood")
        inspection_id = _create_inspection(client, hive_id)
        inspection_photo_id = _upload_photo(client, workspace_id, inspection_id)
        training_crop_id = _create_completed_crop(client, workspace_id, inspection_photo_id)

        dataset_item_response = client.post(
            f"/v1/training-crops/{training_crop_id}/dataset-item",
            json={"workspace_id": workspace_id, "dataset_role": "training"},
            headers=_headers(),
        )
        assert dataset_item_response.status_code == 201
        dataset_item = dataset_item_response.json()
        snapshot = dataset_item["provenance"]["hive_configuration"]
        assert snapshot["frame_standard_id"] == "british_national_deep_brood"
        assert snapshot["side_bar_height_mm"] == 216

        _configure_hive(client, workspace_id, hive_id, frame_standard_id="langstroth_deep_brood")
        export_response = client.post(
            "/v1/dataset-exports/yolo-obb/package",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        )

        assert export_response.status_code == 201
        manifest_path = Path(export_response.json()["manifest_path"])
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        exported_snapshot = manifest["exported_items"][0]["provenance"]["hive_configuration"]
        assert exported_snapshot["frame_standard_id"] == "british_national_deep_brood"
        assert exported_snapshot["frame_standard_display_name"] == "British National deep brood"
    finally:
        app.dependency_overrides.clear()


def _build_state(tmp_path: Path | None = None):
    return build_dev_state(
        dataset_export_root=tmp_path,
        id_values=[UUID(f"00000000-0000-0000-0000-{index:012d}") for index in range(12001, 12040)],
        clock=lambda: datetime(2026, 7, 30, 10, 0, tzinfo=UTC),
    )


def _headers() -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(USER_ID)}


def _create_hive_without_configuration(client: TestClient) -> tuple[str, str]:
    workspace_id = client.get("/v1/dev/session", headers=_headers()).json()["workspace_id"]
    terms = client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": workspace_id, "terms_version": "2026-07-30"},
        headers=_headers(),
    )
    assert terms.status_code == 200
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
    return workspace_id, hive_id


def _configure_hive(
    client: TestClient,
    workspace_id: str,
    hive_id: str,
    frame_standard_id: str = "british_national_deep_brood",
    notes: str | None = None,
    expect_status: int = 200,
) -> dict[str, object]:
    response = client.put(
        f"/v1/hives/{hive_id}/configuration",
        json={
            "workspace_id": workspace_id,
            "frame_standard_id": frame_standard_id,
            "notes": notes,
        },
        headers=_headers(),
    )
    assert response.status_code == expect_status
    return response.json()


def _create_inspection(client: TestClient, hive_id: str) -> str:
    response = client.post(
        "/v1/inspections",
        json={
            "hive_id": hive_id,
            "inspection_date": str(date(2026, 7, 30)),
            "intent": "training_data_collection",
        },
        headers=_headers(),
    )
    assert response.status_code == 201
    return response.json()["inspection_id"]


def _upload_photo(client: TestClient, workspace_id: str, inspection_id: str) -> str:
    response = client.post(
        f"/v1/inspection-photos/intake?workspace_id={workspace_id}&inspection_id={inspection_id}",
        content=_source_png(),
        headers={
            **_headers(),
            "content-type": "image/png",
            "x-hivesight-filename": "configured-frame.png",
        },
    )
    assert response.status_code == 202
    return response.json()["inspection_photo"]["inspection_photo_id"]


def _create_completed_crop(client: TestClient, workspace_id: str, inspection_photo_id: str) -> str:
    crop = client.post(
        "/v1/training-crops",
        json={
            "workspace_id": workspace_id,
            "inspection_photo_id": inspection_photo_id,
            "crop_x": 100,
            "crop_y": 100,
            "crop_width": 640,
            "crop_height": 640,
            "source_image_width_px": 1600,
            "source_image_height_px": 1200,
        },
        headers=_headers(),
    )
    assert crop.status_code == 201
    training_crop_id = crop.json()["training_crop_id"]
    ellipse = client.post(
        f"/v1/training-crops/{training_crop_id}/bee-ellipses",
        json={
            "workspace_id": workspace_id,
            "annotation_type": "complete_visible_bee",
            "center_x": 260,
            "center_y": 280,
            "radius_x": 60,
            "radius_y": 40,
            "rotation_degrees": 12,
        },
        headers=_headers(),
    )
    assert ellipse.status_code == 201
    completed = client.patch(
        f"/v1/training-crops/{training_crop_id}",
        json={
            "workspace_id": workspace_id,
            "visible_bee_status": "has_visible_bees",
            "review_status": "review_complete",
        },
        headers=_headers(),
    )
    assert completed.status_code == 200
    return training_crop_id


def _source_png() -> bytes:
    image = Image.new("RGB", (1600, 1200), color=(230, 190, 80))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
