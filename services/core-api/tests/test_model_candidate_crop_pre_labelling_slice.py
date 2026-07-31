from datetime import date
from io import BytesIO
from pathlib import Path
import time
from uuid import UUID

from fastapi.testclient import TestClient
from hive_configuration_test_support import configure_hive
from PIL import Image

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.dev_store import WorkspaceMembershipRecord
from hive_sight_core_api.main import app

CURATOR_ID = UUID("00000000-0000-0000-0000-000000000101")
ORDINARY_USER_ID = UUID("00000000-0000-0000-0000-000000000999")


def test_dataset_curator_suggests_and_accepts_model_candidate_bee_prelabels(
    tmp_path: Path,
) -> None:
    state = build_dev_state(
        dataset_export_root=tmp_path / "exports",
        model_artifact_root=tmp_path / "model-runs",
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id = _workspace(client)
        _create_reviewed_crop_item(client, workspace_id, "training", 10, 10)
        _create_reviewed_crop_item(client, workspace_id, "validation", 250, 10)
        dataset_version = _create_dataset_version(client, workspace_id)
        training_run = _train_fake_candidate(client, workspace_id, dataset_version["dataset_version_id"])
        crop = _create_editable_crop(client, workspace_id, crop_x=60, crop_y=250)

        proposals = client.post(
            f"/v1/training-crops/{crop['training_crop_id']}/candidate-bee-annotations",
            json={
                "workspace_id": workspace_id,
                "model_candidate_id": training_run["model_candidate_id"],
                "confidence_threshold": 0.1,
            },
            headers=_headers(),
        )

        assert proposals.status_code == 200
        body = proposals.json()
        assert body["model_candidate_id"] == training_run["model_candidate_id"]
        assert len(body["suggestions"]) == 2
        evidence = client.get(
            f"/v1/training-crops/{crop['training_crop_id']}/evidence?workspace_id={workspace_id}",
            headers=_headers(),
        ).json()
        assert evidence["bee_ellipses"] == []

        suggestion = body["suggestions"][0]
        accepted = client.post(
            f"/v1/training-crops/{crop['training_crop_id']}/bee-ellipses",
            json={
                "workspace_id": workspace_id,
                "annotation_type": "partial_visible_bee",
                "center_x": suggestion["center_x"],
                "center_y": suggestion["center_y"],
                "radius_x": suggestion["radius_x"],
                "radius_y": suggestion["radius_y"],
                "rotation_degrees": suggestion["rotation_degrees"],
                "source": "model_candidate",
                "review_method": "human_reviewed_candidate",
                "model_candidate_id": suggestion["model_candidate_id"],
                "candidate_confidence": suggestion["confidence"],
                "candidate_threshold": suggestion["threshold"],
                "raw_model_class": suggestion["raw_model_class"],
                "raw_yolo_obb": suggestion["raw_yolo_obb"],
                "candidate_review_decision": "accepted_with_edits",
            },
            headers=_headers(),
        )

        assert accepted.status_code == 201
        ellipse = accepted.json()
        assert ellipse["source"] == "model_candidate"
        assert ellipse["review_method"] == "human_reviewed_candidate"
        assert ellipse["model_candidate_id"] == training_run["model_candidate_id"]
        assert ellipse["candidate_review_decision"] == "accepted_with_edits"
        assert ellipse["annotation_type"] == "partial_visible_bee"
    finally:
        app.dependency_overrides.clear()


def test_model_candidate_cannot_prelabel_crop_from_its_own_dataset_version(
    tmp_path: Path,
) -> None:
    state = build_dev_state(
        dataset_export_root=tmp_path / "exports",
        model_artifact_root=tmp_path / "model-runs",
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id = _workspace(client)
        training_crop_id = _create_reviewed_crop_item(client, workspace_id, "training", 10, 10)
        _create_reviewed_crop_item(client, workspace_id, "validation", 250, 10)
        dataset_version = _create_dataset_version(client, workspace_id)
        training_run = _train_fake_candidate(client, workspace_id, dataset_version["dataset_version_id"])
        reopened = client.patch(
            f"/v1/training-crops/{training_crop_id}",
            json={"workspace_id": workspace_id, "review_status": "review_pending"},
            headers=_headers(),
        )
        assert reopened.status_code == 200

        response = client.post(
            f"/v1/training-crops/{training_crop_id}/candidate-bee-annotations",
            json={
                "workspace_id": workspace_id,
                "model_candidate_id": training_run["model_candidate_id"],
                "confidence_threshold": 0.1,
            },
            headers=_headers(),
        )

        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "crop_in_candidate_dataset_version"
    finally:
        app.dependency_overrides.clear()


def test_model_candidate_prelabel_requires_dataset_curator(tmp_path: Path) -> None:
    state = build_dev_state(
        dataset_export_root=tmp_path / "exports",
        model_artifact_root=tmp_path / "model-runs",
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id = _workspace(client)
        state.store.memberships.append(
            WorkspaceMembershipRecord(
                user_id=ORDINARY_USER_ID,
                workspace_id=UUID(workspace_id),
            )
        )
        crop = _create_editable_crop(client, workspace_id, crop_x=60, crop_y=250)

        response = client.post(
            f"/v1/training-crops/{crop['training_crop_id']}/candidate-bee-annotations",
            json={"workspace_id": workspace_id, "confidence_threshold": 0.1},
            headers={"x-hivesight-dev-user-id": str(ORDINARY_USER_ID)},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "dataset_curator_access_required"
    finally:
        app.dependency_overrides.clear()


def _workspace(client: TestClient) -> str:
    workspace_id = client.get("/v1/dev/session", headers=_headers()).json()["workspace_id"]
    client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": workspace_id, "terms_version": "2026-07-31"},
        headers=_headers(),
    )
    return workspace_id


def _create_dataset_version(client: TestClient, workspace_id: str) -> dict[str, object]:
    response = client.post(
        "/v1/model-training/dataset-versions",
        json={"workspace_id": workspace_id},
        headers=_headers(),
    )
    assert response.status_code == 201
    return response.json()


def _train_fake_candidate(
    client: TestClient,
    workspace_id: str,
    dataset_version_id: str,
) -> dict[str, object]:
    response = client.post(
        "/v1/model-training/training-runs",
        json={
            "workspace_id": workspace_id,
            "dataset_version_id": dataset_version_id,
            "acknowledge_high_severity_warnings": True,
        },
        headers=_headers(),
    )
    assert response.status_code == 202
    queued = response.json()
    for _ in range(50):
        current = client.get(
            f"/v1/model-training/training-runs/{queued['training_run_id']}?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert current.status_code == 200
        body = current.json()
        if body["status"] == "completed":
            return body
        time.sleep(0.02)
    raise AssertionError("Fake Training Run did not complete.")


def _create_reviewed_crop_item(
    client: TestClient,
    workspace_id: str,
    dataset_role: str,
    crop_x: int,
    crop_y: int,
) -> str:
    crop = _create_editable_crop(client, workspace_id, crop_x=crop_x, crop_y=crop_y)
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
    return crop["training_crop_id"]


def _create_editable_crop(
    client: TestClient,
    workspace_id: str,
    crop_x: int,
    crop_y: int,
) -> dict[str, object]:
    apiary_id = client.post(
        "/v1/apiaries",
        json={"workspace_id": workspace_id, "name": f"Apiary {crop_x}-{crop_y}"},
        headers=_headers(),
    ).json()["apiary_id"]
    hive_id = client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": f"Hive {crop_x}-{crop_y}"},
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
            "x-hivesight-filename": f"crop-{crop_x}-{crop_y}.png",
        },
    )
    assert intake.status_code == 202
    inspection_photo_id = intake.json()["inspection_photo"]["inspection_photo_id"]
    response = client.post(
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
    )
    assert response.status_code == 201
    return response.json()


def _headers() -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(CURATOR_ID)}


def _source_png() -> bytes:
    image = Image.new("RGB", (640, 480), color=(240, 220, 180))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
