from datetime import UTC, date, datetime
from io import BytesIO
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from hive_configuration_test_support import configure_hive
from PIL import Image

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

CURATOR_ID = UUID("00000000-0000-0000-0000-000000000101")
ORDINARY_USER_ID = UUID("00000000-0000-0000-0000-000000000999")


def test_dataset_curator_creates_dataset_version_and_fake_training_run(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id = _workspace(client)
        _create_reviewed_crop_item(client, workspace_id, "training", 10, 10)
        _create_reviewed_crop_item(client, workspace_id, "validation", 260, 10)

        readiness = client.get(
            f"/v1/model-training/readiness?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert readiness.status_code == 200
        assert readiness.json()["adapter_type"] == "fake"
        assert readiness.json()["eligible_to_create_dataset_version"] is True
        assert readiness.json()["database_purpose"] == "dev"

        dataset_version_response = client.post(
            "/v1/model-training/dataset-versions",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        )
        assert dataset_version_response.status_code == 201
        dataset_version = dataset_version_response.json()
        assert dataset_version["human_readable_id"] == "HS-DV-000001"
        assert dataset_version["training_item_count"] == 1
        assert dataset_version["validation_item_count"] == 1
        assert dataset_version["export_format"] == "yolo_obb_v1"
        assert dataset_version["protected_benchmark_dataset_item_ids"] == []
        assert dataset_version["report_artifact_id"] is not None
        assert dataset_version["preview_artifact_ids"]
        assert any(warning["code"] == "NO_BENCHMARK_ITEMS" for warning in dataset_version["warnings"])

        blocked_training = client.post(
            "/v1/model-training/training-runs",
            json={
                "workspace_id": workspace_id,
                "dataset_version_id": dataset_version["dataset_version_id"],
            },
            headers=_headers(),
        )
        assert blocked_training.status_code == 409
        assert (
            blocked_training.json()["detail"]["code"]
            == "high_severity_warnings_require_acknowledgement"
        )

        training_response = client.post(
            "/v1/model-training/training-runs",
            json={
                "workspace_id": workspace_id,
                "dataset_version_id": dataset_version["dataset_version_id"],
                "acknowledge_high_severity_warnings": True,
                "epochs": 1,
                "image_size": 640,
                "batch_size": 1,
                "random_seed": 7,
            },
            headers=_headers(),
        )
        assert training_response.status_code == 202
        training_run = training_response.json()
        assert training_run["human_readable_id"] == "HS-TR-000001"
        assert training_run["status"] == "completed"
        assert training_run["adapter_type"] == "fake"
        assert training_run["model_purpose"] == "bee_detector"
        assert training_run["model_candidate_id"] is not None
        assert training_run["report_artifact_id"] is not None

        candidates = client.get(
            f"/v1/model-training/model-candidates?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert candidates.status_code == 200
        candidate = candidates.json()["model_candidates"][0]
        assert candidate["human_readable_id"] == "HS-MC-000001"
        assert candidate["promotion_status"] == "not_evaluated"
        assert candidate["not_user_facing_reason"] == "baseline_training_only"

        report = client.get(
            f"/v1/model-training/artifacts/{training_run['report_artifact_id']}?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert report.status_code == 200
        assert "Bee Detector localisation only" in report.text
    finally:
        app.dependency_overrides.clear()


def test_model_training_requires_dataset_curator_capability(tmp_path: Path) -> None:
    state = _build_state(tmp_path)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        state.store.dataset_curator_user_ids.clear()
        workspace_id = client.get(
            "/v1/dev/session",
            headers={"x-hivesight-dev-user-id": str(ORDINARY_USER_ID)},
        ).json()["workspace_id"]
        client.post(
            "/v1/workspace-data-use-agreements/acceptances",
            json={"workspace_id": workspace_id, "terms_version": "2026-07-31"},
            headers={"x-hivesight-dev-user-id": str(ORDINARY_USER_ID)},
        )
        response = client.get(
            f"/v1/model-training/readiness?workspace_id={workspace_id}",
            headers={"x-hivesight-dev-user-id": str(ORDINARY_USER_ID)},
        )
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "dataset_curator_access_required"
    finally:
        app.dependency_overrides.clear()


def test_artifact_serving_uses_known_artifact_ids(tmp_path: Path) -> None:
    state = _build_state(tmp_path)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id = _workspace(client)
        response = client.get(
            f"/v1/model-training/artifacts/00000000-0000-0000-0000-000000009999?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "artifact_not_found"
    finally:
        app.dependency_overrides.clear()


def _build_state(tmp_path: Path):
    return build_dev_state(
        id_values=[UUID(f"00000000-0000-0000-0000-000000015{i:03d}") for i in range(1, 240)],
        clock=lambda: datetime(2026, 7, 31, 12, 0, tzinfo=UTC),
        dataset_export_root=tmp_path / "exports",
        model_artifact_root=tmp_path / "model-runs",
    )


def _workspace(client: TestClient) -> str:
    workspace_id = client.get("/v1/dev/session", headers=_headers()).json()["workspace_id"]
    client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": workspace_id, "terms_version": "2026-07-31"},
        headers=_headers(),
    )
    return workspace_id


def _create_reviewed_crop_item(
    client: TestClient,
    workspace_id: str,
    dataset_role: str,
    crop_x: int,
    crop_y: int,
) -> None:
    apiary_id = client.post(
        "/v1/apiaries",
        json={"workspace_id": workspace_id, "name": f"Apiary {dataset_role}"},
        headers=_headers(),
    ).json()["apiary_id"]
    hive_id = client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": f"Hive {dataset_role}"},
        headers=_headers(),
    ).json()["hive_id"]
    configure_hive(client, workspace_id=workspace_id, hive_id=hive_id, headers=_headers())
    inspection_id = client.post(
        "/v1/inspections",
        json={
            "hive_id": hive_id,
            "inspection_date": str(date(2026, 7, 31)),
            "intent": "training_data_collection",
        },
        headers=_headers(),
    ).json()["inspection_id"]
    intake = client.post(
        f"/v1/inspection-photos/intake?workspace_id={workspace_id}&inspection_id={inspection_id}",
        content=_source_png(),
        headers={
            **_headers(),
            "content-type": "image/png",
            "x-hivesight-filename": f"{dataset_role}.png",
        },
    )
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
        headers=_headers(),
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
        headers=_headers(),
    )
    assert ellipse.status_code == 201
    completed = client.patch(
        f"/v1/training-crops/{crop['training_crop_id']}",
        json={
            "workspace_id": workspace_id,
            "visible_bee_status": "has_visible_bees",
            "review_status": "review_complete",
        },
        headers=_headers(),
    )
    assert completed.status_code == 200
    assignment = client.post(
        f"/v1/training-crops/{crop['training_crop_id']}/dataset-item",
        json={
            "workspace_id": workspace_id,
            "dataset_role": dataset_role,
            "source_group_key": f"{dataset_role}-group",
        },
        headers=_headers(),
    )
    assert assignment.status_code == 201


def _headers() -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(CURATOR_ID)}


def _source_png() -> bytes:
    image = Image.new("RGB", (640, 480), color=(240, 220, 180))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
