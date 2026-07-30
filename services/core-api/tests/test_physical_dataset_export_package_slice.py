from datetime import UTC, date, datetime
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from PIL import Image

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

USER_ID = UUID("00000000-0000-0000-0000-000000000101")


def test_physical_yolo_obb_package_writes_crop_images_labels_and_manifest(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)
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
        _assign_crop(
            client,
            workspace_id,
            validation_crop["training_crop_id"],
            dataset_role="validation",
        )
        benchmark_item = _assign_crop(
            client,
            workspace_id,
            benchmark_crop["training_crop_id"],
            dataset_role="benchmark",
        ).json()
        excluded_item = _assign_crop(
            client,
            workspace_id,
            excluded_crop["training_crop_id"],
            dataset_role="excluded",
            exclusion_reason="duplicate_or_near_duplicate",
        ).json()

        response = client.post(
            "/v1/dataset-exports/yolo-obb/package",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        )

        assert response.status_code == 201
        body = response.json()
        package_path = Path(body["package_path"])
        assert package_path.exists()
        assert package_path.parent == tmp_path
        assert body["training_item_count"] == 1
        assert body["validation_item_count"] == 1
        assert body["benchmark_item_count"] == 1
        assert body["excluded_item_count"] == 1
        assert body["protected_benchmark_dataset_item_ids"] == [benchmark_item["dataset_item_id"]]
        assert [item["dataset_item_id"] for item in body["excluded_dataset_items"]] == [
            excluded_item["dataset_item_id"]
        ]

        generated_files = body["generated_files"]
        relative_paths = {file["relative_path"] for file in generated_files}
        assert "manifest.json" in relative_paths
        assert "dataset.yaml" in relative_paths
        assert not any("benchmark" in relative_path for relative_path in relative_paths)
        assert not any("excluded" in relative_path for relative_path in relative_paths)

        training_image = _single_generated_file(generated_files, file_kind="image", split="train")
        training_label = _single_generated_file(generated_files, file_kind="label", split="train")
        assert training_image["relative_path"].startswith("images/train/bee-crop-000001-")
        assert training_image["relative_path"].endswith(".png")
        assert training_label["relative_path"].startswith("labels/train/bee-crop-000001-")
        assert training_label["relative_path"].endswith(".txt")
        assert training_image["export_filename_stem"] == training_label["export_filename_stem"]
        assert training_image["dataset_item_id"] == training_item["dataset_item_id"]

        crop_path = package_path / training_image["relative_path"]
        label_path = package_path / training_label["relative_path"]
        with Image.open(crop_path) as crop_image:
            assert crop_image.size == (640, 640)
            assert crop_image.format == "PNG"
        assert label_path.read_text(encoding="utf-8") == (
            "0 0.250000 0.281250 0.375000 0.281250 "
            "0.375000 0.343750 0.250000 0.343750\n"
        )

        dataset_yaml = (package_path / "dataset.yaml").read_text(encoding="utf-8")
        assert "path: ." in dataset_yaml
        assert "train: images/train" in dataset_yaml
        assert "val: images/val" in dataset_yaml
        assert "0: complete_visible_bee" in dataset_yaml
        assert "1: partial_visible_bee" in dataset_yaml

        manifest = json.loads((package_path / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["export_format"] == "yolo_obb"
        assert manifest["exported_items"][0]["dataset_item_id"] == training_item["dataset_item_id"]
        assert manifest["exported_items"][0]["original_filename"] == "frame.png"
        assert manifest["exported_items"][0]["label_rows"] == [
            "0 0.250000 0.281250 0.375000 0.281250 "
            "0.375000 0.343750 0.250000 0.343750"
        ]
        assert manifest["protected_benchmark_dataset_item_ids"] == [benchmark_item["dataset_item_id"]]
        assert [item["dataset_item_id"] for item in manifest["excluded_dataset_items"]] == [
            excluded_item["dataset_item_id"]
        ]

        for generated_file in generated_files:
            file_path = package_path / generated_file["relative_path"]
            file_bytes = file_path.read_bytes()
            assert generated_file["size_bytes"] == len(file_bytes)
            assert generated_file["sha256"] == sha256(file_bytes).hexdigest()
    finally:
        app.dependency_overrides.clear()


def test_physical_yolo_obb_package_blocks_empty_and_cleans_failed_exports(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id = client.get("/v1/dev/session", headers=_headers()).json()["workspace_id"]
        client.post(
            "/v1/workspace-data-use-agreements/acceptances",
            json={"workspace_id": workspace_id, "terms_version": "2026-07-30"},
            headers=_headers(),
        )
        empty_response = client.post(
            "/v1/dataset-exports/yolo-obb/package",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        )
        assert empty_response.status_code == 409
        assert empty_response.json()["detail"]["code"] == "no_dataset_items_for_physical_export"

        workspace_id, crop = _create_completed_training_crop(
            client,
            crop_x=100,
            image_bytes=b"not-a-readable-image",
        )
        _assign_crop(
            client,
            workspace_id,
            crop["training_crop_id"],
            dataset_role="training",
        )
        failed_response = client.post(
            "/v1/dataset-exports/yolo-obb/package",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        )

        assert failed_response.status_code == 409
        assert failed_response.json()["detail"]["code"] == "source_image_unreadable"
        assert list(tmp_path.glob("dataset-export-*")) == []
    finally:
        app.dependency_overrides.clear()


def _build_state(tmp_path: Path):
    return build_dev_state(
        id_values=[
            UUID(f"00000000-0000-0000-0000-000000012{i:03d}") for i in range(1, 120)
        ],
        clock=lambda: datetime(2026, 7, 30, 16, 0, tzinfo=UTC),
        dataset_export_root=tmp_path,
    )


def _create_completed_training_crop(
    client: TestClient,
    crop_x: int = 100,
    crop_y: int = 100,
    image_bytes: bytes | None = None,
) -> tuple[str, dict[str, object]]:
    workspace_id, inspection_photo_id = _upload_photo(client, image_bytes=image_bytes)
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


def _upload_photo(client: TestClient, image_bytes: bytes | None = None) -> tuple[str, str]:
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
        content=image_bytes or _source_png(),
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
    assignment_note: str | None = None,
    exclusion_reason: str | None = None,
) -> object:
    return client.post(
        f"/v1/training-crops/{training_crop_id}/dataset-item",
        json={
            "workspace_id": workspace_id,
            "dataset_role": dataset_role,
            "assignment_note": assignment_note,
            "exclusion_reason": exclusion_reason,
        },
        headers=_headers(),
    )


def _single_generated_file(
    generated_files: list[dict[str, object]],
    file_kind: str,
    split: str,
) -> dict[str, object]:
    matches = [
        generated_file
        for generated_file in generated_files
        if generated_file["file_kind"] == file_kind and generated_file["split"] == split
    ]
    assert len(matches) == 1
    return matches[0]


def _headers() -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(USER_ID)}


def _source_png() -> bytes:
    image = Image.new("RGB", (1600, 1200), color=(220, 180, 90))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
