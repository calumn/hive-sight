from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.dev_store import DevState
from hive_sight_core_api.main import app

FEATURES_DIR = Path(__file__).parent / "features"
USER_ID = UUID("00000000-0000-0000-0000-000000000101")

scenarios(str(FEATURES_DIR / "vertical_slice_0010_bee_annotation_repository_and_dataset_export.feature"))


@dataclass
class SliceContext:
    client: TestClient
    state: DevState
    workspace_id: str | None = None
    training_crop_id: str | None = None
    response_status_code: int | None = None
    response_body: dict[str, object] | None = None


@pytest.fixture
def slice_context() -> SliceContext:
    state = build_dev_state(
        id_values=[
            UUID(f"00000000-0000-0000-0000-000000011{i:03d}") for i in range(1, 100)
        ],
        clock=lambda: datetime(2026, 7, 30, 15, 0, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    try:
        yield SliceContext(client=TestClient(app), state=state)
    finally:
        app.dependency_overrides.clear()


@given("the User is logged in with dataset curator capability for Bee Annotation Repository export")
def user_logged_in(slice_context: SliceContext) -> None:
    workspace_id = slice_context.client.get("/v1/dev/session", headers=_headers()).json()[
        "workspace_id"
    ]
    accept_terms = slice_context.client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": workspace_id, "terms_version": "2026-07-30"},
        headers=_headers(),
    )
    assert accept_terms.status_code == 200
    slice_context.workspace_id = workspace_id


@given("the Dataset Curator has completed a Training Crop with a visible bee ellipse")
def completed_training_crop(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    slice_context.training_crop_id = _create_completed_crop(slice_context, 100, 100)


@given(
    "the Dataset Curator has assigned Training Crops to training validation benchmark and excluded roles"
)
def assigned_training_crops(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    role_to_crop = {
        "training": _create_completed_crop(slice_context, 100, 100),
        "validation": _create_completed_crop(slice_context, 760, 100),
        "benchmark": _create_completed_crop(slice_context, 100, 520),
        "excluded": _create_completed_crop(slice_context, 760, 520),
    }
    for role, training_crop_id in role_to_crop.items():
        response = _assign_crop(
            slice_context,
            training_crop_id,
            role,
            exclusion_reason="unsuitable_crop" if role == "excluded" else None,
        )
        assert response.status_code == 201


@when("the Dataset Curator assigns the Training Crop to training")
def assign_training_crop(slice_context: SliceContext) -> None:
    assert slice_context.training_crop_id is not None
    response = _assign_crop(slice_context, slice_context.training_crop_id, "training")
    slice_context.response_status_code = response.status_code
    slice_context.response_body = response.json()


@when("the Dataset Curator creates a YOLO OBB manifest export")
def create_yolo_export(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    response = slice_context.client.post(
        "/v1/dataset-exports/yolo-obb",
        json={"workspace_id": slice_context.workspace_id},
        headers=_headers(),
    )
    slice_context.response_status_code = response.status_code
    slice_context.response_body = response.json()


@then("the Core API creates a Dataset Item from the Training Crop")
def core_api_creates_dataset_item(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 201
    assert slice_context.response_body is not None
    assert slice_context.response_body["source_evidence_type"] == "training_crop"
    assert slice_context.response_body["training_crop_id"] == slice_context.training_crop_id
    assert slice_context.response_body["dataset_role"] == "training"


@then("the Dataset Item snapshots the reviewed bee ellipse evidence")
def dataset_item_snapshots_ellipse(slice_context: SliceContext) -> None:
    assert slice_context.response_body is not None
    snapshots = slice_context.response_body["reviewed_ellipse_snapshots"]
    assert isinstance(snapshots, list)
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert isinstance(snapshot, dict)
    assert snapshot["annotation_type"] == "complete_visible_bee"
    assert snapshot["coordinate_space"] == "source_image_pixels"


@then("the manifest includes training and validation label rows")
def manifest_includes_train_validation(slice_context: SliceContext) -> None:
    assert slice_context.response_status_code == 201
    assert slice_context.response_body is not None
    assert slice_context.response_body["training_item_count"] == 1
    assert slice_context.response_body["validation_item_count"] == 1
    label_entries = slice_context.response_body["label_entries"]
    assert isinstance(label_entries, list)
    assert [entry["split"] for entry in label_entries] == ["training", "validation"]
    assert all(str(entry["label"]).startswith("0 ") for entry in label_entries)


@then("the manifest reports benchmark and excluded items without exporting them for training")
def manifest_protects_benchmark_and_excluded(slice_context: SliceContext) -> None:
    assert slice_context.response_body is not None
    assert slice_context.response_body["benchmark_item_count"] == 1
    assert len(slice_context.response_body["protected_benchmark_dataset_item_ids"]) == 1
    assert len(slice_context.response_body["excluded_dataset_items"]) == 1
    assert "derived model-training projections" in str(slice_context.response_body["caveat"])


def _create_completed_crop(slice_context: SliceContext, crop_x: int, crop_y: int) -> str:
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
        content=b"fake-image-bytes",
        headers={
            **_headers(),
            "content-type": "image/jpeg",
            "x-hivesight-filename": "frame.jpg",
        },
    )
    assert intake.status_code == 202
    return intake.json()["inspection_photo"]["inspection_photo_id"]


def _assign_crop(
    slice_context: SliceContext,
    training_crop_id: str,
    dataset_role: str,
    exclusion_reason: str | None = None,
) -> object:
    assert slice_context.workspace_id is not None
    return slice_context.client.post(
        f"/v1/training-crops/{training_crop_id}/dataset-item",
        json={
            "workspace_id": slice_context.workspace_id,
            "dataset_role": dataset_role,
            "assignment_note": "Assigned by Slice 10 BDD.",
            "exclusion_reason": exclusion_reason,
        },
        headers=_headers(),
    )


def _headers() -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(USER_ID)}
