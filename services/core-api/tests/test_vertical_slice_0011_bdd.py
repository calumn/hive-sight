from dataclasses import dataclass
from datetime import UTC, date, datetime
from io import BytesIO
import json
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pytest_bdd import given, scenarios, then, when

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.dev_store import DevState
from hive_sight_core_api.main import app

FEATURES_DIR = Path(__file__).parent / "features"
USER_ID = UUID("00000000-0000-0000-0000-000000000101")

scenarios(str(FEATURES_DIR / "vertical_slice_0011_physical_dataset_export_package.feature"))


@dataclass
class SliceContext:
    client: TestClient
    state: DevState
    export_root: Path
    workspace_id: str | None = None
    response_status_code: int | None = None
    response_body: dict[str, object] | None = None


@pytest.fixture
def slice_context(tmp_path: Path) -> SliceContext:
    state = build_dev_state(
        id_values=[
            UUID(f"00000000-0000-0000-0000-000000013{i:03d}") for i in range(1, 120)
        ],
        clock=lambda: datetime(2026, 7, 30, 17, 0, tzinfo=UTC),
        dataset_export_root=tmp_path,
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    try:
        yield SliceContext(client=TestClient(app), state=state, export_root=tmp_path)
    finally:
        app.dependency_overrides.clear()


@given("the User is logged in with dataset curator capability for physical dataset export")
def user_logged_in(slice_context: SliceContext) -> None:
    workspace_id = slice_context.client.get("/v1/dev/session", headers=_headers()).json()[
        "workspace_id"
    ]
    response = slice_context.client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": workspace_id, "terms_version": "2026-07-30"},
        headers=_headers(),
    )
    assert response.status_code == 200
    slice_context.workspace_id = workspace_id


@given("the Dataset Curator has assigned Training Crops to training and validation roles")
def assigned_training_validation(slice_context: SliceContext) -> None:
    _create_and_assign_crop(slice_context, crop_x=100, crop_y=100, dataset_role="training")
    _create_and_assign_crop(slice_context, crop_x=760, crop_y=100, dataset_role="validation")


@given(
    "the Dataset Curator has assigned Training Crops to training validation benchmark and excluded roles for physical export"
)
def assigned_all_roles(slice_context: SliceContext) -> None:
    _create_and_assign_crop(slice_context, crop_x=100, crop_y=100, dataset_role="training")
    _create_and_assign_crop(slice_context, crop_x=760, crop_y=100, dataset_role="validation")
    _create_and_assign_crop(slice_context, crop_x=100, crop_y=520, dataset_role="benchmark")
    _create_and_assign_crop(
        slice_context,
        crop_x=760,
        crop_y=520,
        dataset_role="excluded",
        exclusion_reason="unsuitable_crop",
    )


@when("the Dataset Curator creates a physical YOLO OBB dataset export package")
def create_physical_export(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    response = slice_context.client.post(
        "/v1/dataset-exports/yolo-obb/package",
        json={"workspace_id": slice_context.workspace_id},
        headers=_headers(),
    )
    slice_context.response_status_code = response.status_code
    slice_context.response_body = response.json()


@then("the Core API writes crop images labels manifest and dataset YAML files")
def core_api_writes_files(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 201
    assert slice_context.response_body is not None
    package_path = Path(str(slice_context.response_body["package_path"]))
    assert (package_path / "manifest.json").exists()
    assert (package_path / "dataset.yaml").exists()
    assert len(list((package_path / "images" / "train").glob("*.png"))) == 1
    assert len(list((package_path / "images" / "val").glob("*.png"))) == 1
    assert len(list((package_path / "labels" / "train").glob("*.txt"))) == 1
    assert len(list((package_path / "labels" / "val").glob("*.txt"))) == 1


@then("the package response reports the generated package summary")
def response_reports_summary(slice_context: SliceContext) -> None:
    assert slice_context.response_body is not None
    assert slice_context.response_body["training_item_count"] == 1
    assert slice_context.response_body["validation_item_count"] == 1
    assert str(slice_context.response_body["manifest_path"]).endswith("manifest.json")
    assert str(slice_context.response_body["dataset_yaml_path"]).endswith("dataset.yaml")
    assert len(slice_context.response_body["generated_files"]) == 6


@then("the physical package contains only training and validation files")
def package_contains_only_train_val(slice_context: SliceContext) -> None:
    assert slice_context.response_body is not None
    package_path = Path(str(slice_context.response_body["package_path"]))
    relative_paths = [
        str(path.relative_to(package_path))
        for path in package_path.rglob("*")
        if path.is_file()
    ]
    assert all("/benchmark/" not in path for path in relative_paths)
    assert all("/excluded/" not in path for path in relative_paths)
    assert len([path for path in relative_paths if path.startswith("images/")]) == 2
    assert len([path for path in relative_paths if path.startswith("labels/")]) == 2


@then("the manifest reports benchmark and excluded items as metadata only")
def manifest_reports_protected_metadata(slice_context: SliceContext) -> None:
    assert slice_context.response_body is not None
    assert slice_context.response_body["benchmark_item_count"] == 1
    assert slice_context.response_body["excluded_item_count"] == 1
    package_path = Path(str(slice_context.response_body["package_path"]))
    manifest = json.loads((package_path / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["protected_benchmark_dataset_item_ids"]) == 1
    assert len(manifest["excluded_dataset_items"]) == 1
    assert len(manifest["exported_items"]) == 2


def _create_and_assign_crop(
    slice_context: SliceContext,
    crop_x: int,
    crop_y: int,
    dataset_role: str,
    exclusion_reason: str | None = None,
) -> str:
    assert slice_context.workspace_id is not None
    inspection_photo_id = _upload_photo(slice_context)
    crop = slice_context.client.post(
        "/v1/training-crops",
        json={
            "workspace_id": slice_context.workspace_id,
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
    assert crop.status_code == 201
    training_crop_id = crop.json()["training_crop_id"]
    ellipse = slice_context.client.post(
        f"/v1/training-crops/{training_crop_id}/bee-ellipses",
        json={
            "workspace_id": slice_context.workspace_id,
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
    complete = slice_context.client.patch(
        f"/v1/training-crops/{training_crop_id}",
        json={
            "workspace_id": slice_context.workspace_id,
            "visible_bee_status": "has_visible_bees",
            "review_status": "review_complete",
        },
        headers=_headers(),
    )
    assert complete.status_code == 200
    assignment = slice_context.client.post(
        f"/v1/training-crops/{training_crop_id}/dataset-item",
        json={
            "workspace_id": slice_context.workspace_id,
            "dataset_role": dataset_role,
            "assignment_note": "Assigned by Slice 11 BDD.",
            "exclusion_reason": exclusion_reason,
        },
        headers=_headers(),
    )
    assert assignment.status_code == 201
    return training_crop_id


def _upload_photo(slice_context: SliceContext) -> str:
    assert slice_context.workspace_id is not None
    apiary_id = slice_context.client.post(
        "/v1/apiaries",
        json={"workspace_id": slice_context.workspace_id, "name": "Home apiary"},
        headers=_headers(),
    ).json()["apiary_id"]
    hive_id = slice_context.client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": "Hive A"},
        headers=_headers(),
    ).json()["hive_id"]
    inspection_id = slice_context.client.post(
        "/v1/inspections",
        json={
            "hive_id": hive_id,
            "inspection_date": str(date(2026, 7, 30)),
            "intent": "training_data_collection",
        },
        headers=_headers(),
    ).json()["inspection_id"]
    intake = slice_context.client.post(
        "/v1/inspection-photos/intake"
        f"?workspace_id={slice_context.workspace_id}&inspection_id={inspection_id}",
        content=_source_png(),
        headers={
            **_headers(),
            "content-type": "image/png",
            "x-hivesight-filename": "frame.png",
        },
    )
    assert intake.status_code == 202
    return intake.json()["inspection_photo"]["inspection_photo_id"]


def _headers() -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(USER_ID)}


def _source_png() -> bytes:
    image = Image.new("RGB", (1600, 1200), color=(220, 180, 90))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
