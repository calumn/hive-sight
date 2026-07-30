import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from io import BytesIO
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

scenarios(str(FEATURES_DIR / "vertical_slice_0012_hive_configuration_and_frame_standard_metadata.feature"))


@dataclass
class SliceContext:
    client: TestClient
    state: DevState
    export_root: Path
    workspace_id: str | None = None
    hive_id: str | None = None
    inspection_response: dict[str, object] | None = None
    response_status_code: int | None = None
    dataset_item: dict[str, object] | None = None
    export_manifest: dict[str, object] | None = None


@pytest.fixture
def slice_context(tmp_path: Path) -> SliceContext:
    state = build_dev_state(
        dataset_export_root=tmp_path,
        id_values=[UUID(f"00000000-0000-0000-0000-{index:012d}") for index in range(12101, 12150)],
        clock=lambda: datetime(2026, 7, 30, 11, 0, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    try:
        yield SliceContext(client=TestClient(app), state=state, export_root=tmp_path)
    finally:
        app.dependency_overrides.clear()


@given("the User has created a Hive without Hive Configuration")
def user_created_hive_without_configuration(slice_context: SliceContext) -> None:
    workspace_id, hive_id = _create_hive(slice_context)
    slice_context.workspace_id = workspace_id
    slice_context.hive_id = hive_id


@given("the User has created a configured British National deep brood Hive")
def user_created_configured_british_national_hive(slice_context: SliceContext) -> None:
    workspace_id, hive_id = _create_hive(slice_context)
    _configure_hive(slice_context, workspace_id, hive_id, "british_national_deep_brood")
    slice_context.workspace_id = workspace_id
    slice_context.hive_id = hive_id


@given("the User has assigned a reviewed bee Training Crop to the training Dataset")
def user_assigned_reviewed_training_crop(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.hive_id is not None
    inspection_id = _create_inspection(slice_context, "training_data_collection")
    inspection_photo_id = _upload_photo(slice_context, inspection_id)
    training_crop_id = _create_completed_crop(slice_context, inspection_photo_id)
    response = slice_context.client.post(
        f"/v1/training-crops/{training_crop_id}/dataset-item",
        json={"workspace_id": slice_context.workspace_id, "dataset_role": "training"},
        headers=_headers(),
    )
    assert response.status_code == 201
    slice_context.dataset_item = response.json()


@when("the User creates a training data collection Inspection for that Hive")
def user_creates_training_inspection(slice_context: SliceContext) -> None:
    response = _post_inspection(slice_context, "training_data_collection")
    slice_context.response_status_code = response.status_code
    slice_context.inspection_response = response.json()


@when("the User records British National deep brood Hive Configuration")
def user_records_british_national_hive_configuration(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.hive_id is not None
    _configure_hive(
        slice_context,
        slice_context.workspace_id,
        slice_context.hive_id,
        "british_national_deep_brood",
    )


@when("the User later changes the Hive Configuration to Langstroth deep brood")
def user_changes_hive_configuration(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.hive_id is not None
    _configure_hive(slice_context, slice_context.workspace_id, slice_context.hive_id, "langstroth_deep_brood")


@when("the User creates a physical YOLO OBB dataset package")
def user_creates_physical_yolo_package(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    response = slice_context.client.post(
        "/v1/dataset-exports/yolo-obb/package",
        json={"workspace_id": slice_context.workspace_id},
        headers=_headers(),
    )
    assert response.status_code == 201
    manifest_path = Path(response.json()["manifest_path"])
    slice_context.export_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))


@then("the Core API rejects the Inspection because Hive Configuration is required")
def core_api_rejects_inspection_without_configuration(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 409
    assert slice_context.inspection_response is not None
    detail = slice_context.inspection_response["detail"]
    assert isinstance(detail, dict)
    assert detail["code"] == "hive_configuration_required"


@then("the Core API accepts the configured Inspection")
def core_api_accepts_configured_inspection(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 201
    assert slice_context.inspection_response is not None
    assert slice_context.inspection_response["intent"] == "training_data_collection"


@then("the physical export manifest keeps the Dataset Item Hive Configuration snapshot")
def manifest_keeps_hive_configuration_snapshot(slice_context: SliceContext) -> None:
    assert slice_context.dataset_item is not None
    assert slice_context.export_manifest is not None
    original_snapshot = slice_context.dataset_item["provenance"]["hive_configuration"]
    exported_snapshot = slice_context.export_manifest["exported_items"][0]["provenance"][
        "hive_configuration"
    ]
    assert original_snapshot["frame_standard_id"] == "british_national_deep_brood"
    assert exported_snapshot["frame_standard_id"] == "british_national_deep_brood"
    assert exported_snapshot["frame_standard_display_name"] == "British National deep brood"


def _headers() -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(USER_ID)}


def _create_hive(slice_context: SliceContext) -> tuple[str, str]:
    workspace_id = slice_context.client.get("/v1/dev/session", headers=_headers()).json()[
        "workspace_id"
    ]
    terms = slice_context.client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": workspace_id, "terms_version": "2026-07-30"},
        headers=_headers(),
    )
    assert terms.status_code == 200
    apiary_id = slice_context.client.post(
        "/v1/apiaries",
        json={"workspace_id": workspace_id, "name": "Home apiary"},
        headers=_headers(),
    ).json()["apiary_id"]
    hive_id = slice_context.client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": "Hive A"},
        headers=_headers(),
    ).json()["hive_id"]
    return workspace_id, hive_id


def _configure_hive(
    slice_context: SliceContext,
    workspace_id: str,
    hive_id: str,
    frame_standard_id: str,
) -> None:
    response = slice_context.client.put(
        f"/v1/hives/{hive_id}/configuration",
        json={"workspace_id": workspace_id, "frame_standard_id": frame_standard_id},
        headers=_headers(),
    )
    assert response.status_code == 200


def _post_inspection(slice_context: SliceContext, intent: str):
    assert slice_context.hive_id is not None
    return slice_context.client.post(
        "/v1/inspections",
        json={
            "hive_id": slice_context.hive_id,
            "inspection_date": str(date(2026, 7, 30)),
            "intent": intent,
        },
        headers=_headers(),
    )


def _create_inspection(slice_context: SliceContext, intent: str) -> str:
    response = _post_inspection(slice_context, intent)
    assert response.status_code == 201
    return response.json()["inspection_id"]


def _upload_photo(slice_context: SliceContext, inspection_id: str) -> str:
    assert slice_context.workspace_id is not None
    response = slice_context.client.post(
        "/v1/inspection-photos/intake"
        f"?workspace_id={slice_context.workspace_id}&inspection_id={inspection_id}",
        content=_source_png(),
        headers={**_headers(), "content-type": "image/png", "x-hivesight-filename": "frame.png"},
    )
    assert response.status_code == 202
    return response.json()["inspection_photo"]["inspection_photo_id"]


def _create_completed_crop(slice_context: SliceContext, inspection_photo_id: str) -> str:
    assert slice_context.workspace_id is not None
    crop = slice_context.client.post(
        "/v1/training-crops",
        json={
            "workspace_id": slice_context.workspace_id,
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
    ellipse = slice_context.client.post(
        f"/v1/training-crops/{training_crop_id}/bee-ellipses",
        json={
            "workspace_id": slice_context.workspace_id,
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
    completed = slice_context.client.patch(
        f"/v1/training-crops/{training_crop_id}",
        json={
            "workspace_id": slice_context.workspace_id,
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
