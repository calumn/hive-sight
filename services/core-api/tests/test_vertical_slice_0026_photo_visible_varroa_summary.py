from datetime import date
from io import BytesIO
from uuid import UUID

from fastapi.testclient import TestClient
from hive_configuration_test_support import configure_hive
from PIL import Image

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

CURATOR_ID = UUID("00000000-0000-0000-0000-000000000101")


def test_photo_visible_varroa_summary_aggregates_completed_crops_and_caveats_unfinished(tmp_path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, photo_id, first_crop, second_crop, unfinished_crop = _photo_with_three_crops(client)
        first_positive = _create_ellipse(client, workspace_id, first_crop, 90, "complete_visible_bee")
        first_negative = _create_ellipse(client, workspace_id, first_crop, 160, "complete_visible_bee")
        second_unresolved = _create_ellipse(client, workspace_id, second_crop, 70, "complete_visible_bee")
        second_unreviewed = _create_ellipse(client, workspace_id, second_crop, 125, "complete_visible_bee")
        _create_ellipse(client, workspace_id, second_crop, 170, "partial_visible_bee")
        _create_ellipse(client, workspace_id, unfinished_crop, 110, "complete_visible_bee")
        _complete_crop(client, workspace_id, first_crop)
        _complete_crop(client, workspace_id, second_crop)
        _save_outcome(
            client,
            workspace_id,
            first_crop,
            first_positive,
            "visible_varroa_present",
            [{"x": 0.25, "y": 0.35}, {"x": 0.55, "y": 0.65}],
        )
        _save_outcome(client, workspace_id, first_crop, first_negative, "no_visible_varroa", [])
        _save_outcome(
            client,
            workspace_id,
            second_crop,
            second_unresolved,
            "not_determined",
            [],
            notes="The body is hidden by glare.",
        )

        response = _get_summary(client, workspace_id, photo_id)

        assert response.status_code == 200
        body = response.json()
        assert body["workspace_id"] == workspace_id
        assert body["inspection_photo_id"] == photo_id
        assert body["completed_training_crop_count"] == 2
        assert body["unfinished_training_crop_count"] == 1
        assert body["eligible_complete_bee_count"] == 4
        assert body["reviewed_eligible_bee_count"] == 3
        assert body["determinate_eligible_bee_count"] == 2
        assert body["visible_varroa_bee_count"] == 1
        assert body["active_negative_bee_count"] == 1
        assert body["not_determined_bee_count"] == 1
        assert body["unreviewed_eligible_bee_count"] == 1
        assert body["ineligible_or_not_assessed_bee_count"] == 1
        assert body["visible_mite_marker_count"] == 2
        assert body["review_completion_percent"] == 75.0
        assert body["determinate_varroa_coverage_percent"] == 50.0
        assert body["readiness_state"] == "partial_evidence"
        assert body["advisor_context_available"] is True
        assert "photo-visible evidence" in body["caveats"].lower()
        assert "unfinished crop" in body["caveats"]
        assert "coverage is incomplete" in body["caveats"]
        assert "treatment" not in body["caveats"].lower().replace("not treatment advice", "")
    finally:
        app.dependency_overrides.clear()


def test_photo_visible_varroa_summary_without_determinate_evidence_is_not_advisor_ready(tmp_path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, photo_id, crop_id, _, _ = _photo_with_three_crops(client)
        unresolved = _create_ellipse(client, workspace_id, crop_id, 90, "complete_visible_bee")
        _complete_crop(client, workspace_id, crop_id)
        _save_outcome(
            client,
            workspace_id,
            crop_id,
            unresolved,
            "not_determined",
            [],
            notes="The bee is obscured.",
        )

        response = _get_summary(client, workspace_id, photo_id)

        assert response.status_code == 200
        body = response.json()
        assert body["reviewed_eligible_bee_count"] == 1
        assert body["determinate_eligible_bee_count"] == 0
        assert body["not_determined_bee_count"] == 1
        assert body["advisor_context_available"] is False
        assert body["readiness_state"] == "not_available"
    finally:
        app.dependency_overrides.clear()


def _photo_with_three_crops(client: TestClient) -> tuple[str, str, str, str, str]:
    workspace_id = _workspace(client)
    apiary_id = client.post(
        "/v1/apiaries",
        json={"workspace_id": workspace_id, "name": "Slice 26 Apiary"},
        headers=_headers(),
    ).json()["apiary_id"]
    hive_id = client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": "Slice 26 Hive"},
        headers=_headers(),
    ).json()["hive_id"]
    configure_hive(client, workspace_id=workspace_id, hive_id=hive_id, headers=_headers())
    inspection_id = client.post(
        "/v1/inspections",
        json={
            "hive_id": hive_id,
            "inspection_date": str(date(2026, 8, 5)),
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
            "x-hivesight-filename": "slice-26-varroa-summary.png",
        },
    )
    photo_id = intake.json()["inspection_photo"]["inspection_photo_id"]
    crops = [
        _create_crop(client, workspace_id, photo_id, 0),
        _create_crop(client, workspace_id, photo_id, 220),
        _create_crop(client, workspace_id, photo_id, 420),
    ]
    return workspace_id, photo_id, crops[0], crops[1], crops[2]


def _workspace(client: TestClient) -> str:
    workspace_id = client.get("/v1/dev/session", headers=_headers()).json()["workspace_id"]
    client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": workspace_id, "terms_version": "2026-08-05"},
        headers=_headers(),
    )
    return workspace_id


def _create_crop(client: TestClient, workspace_id: str, photo_id: str, crop_x: int) -> str:
    response = client.post(
        "/v1/training-crops",
        json={
            "workspace_id": workspace_id,
            "inspection_photo_id": photo_id,
            "crop_x": 0,
            "crop_y": 0,
            "crop_width": 300,
            "crop_height": 240,
            "source_image_width_px": 640,
            "source_image_height_px": 480,
        },
        headers=_headers(),
    )
    assert response.status_code == 201
    return response.json()["training_crop_id"]


def _complete_crop(client: TestClient, workspace_id: str, crop_id: str) -> None:
    response = client.patch(
        f"/v1/training-crops/{crop_id}",
        json={
            "workspace_id": workspace_id,
            "visible_bee_status": "has_visible_bees",
            "review_status": "review_complete",
        },
        headers=_headers(),
    )
    assert response.status_code == 200


def _create_ellipse(
    client: TestClient,
    workspace_id: str,
    crop_id: str,
    center_x: int,
    annotation_type: str,
) -> str:
    response = client.post(
        f"/v1/training-crops/{crop_id}/bee-ellipses",
        json={
            "workspace_id": workspace_id,
            "annotation_type": annotation_type,
            "center_x": center_x,
            "center_y": 100,
            "radius_x": 24,
            "radius_y": 12,
            "rotation_degrees": 0,
            "orientation_reliability": "reliable",
        },
        headers=_headers(),
    )
    assert response.status_code == 201
    return response.json()["annotation_id"]


def _save_outcome(
    client: TestClient,
    workspace_id: str,
    crop_id: str,
    bee_annotation_id: str,
    outcome: str,
    markers: list[dict[str, float]],
    *,
    notes: str | None = None,
) -> None:
    response = client.put(
        f"/v1/training-crops/{crop_id}/varroa-review-candidates/{bee_annotation_id}/outcome",
        json={
            "workspace_id": workspace_id,
            "outcome": outcome,
            "markers": markers,
            "notes": notes,
        },
        headers=_headers(),
    )
    assert response.status_code == 200


def _get_summary(client: TestClient, workspace_id: str, photo_id: str):
    return client.get(
        f"/v1/inspection-photos/{photo_id}/photo-visible-varroa-summary?workspace_id={workspace_id}",
        headers=_headers(),
    )


def _headers() -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(CURATOR_ID)}


def _source_png() -> bytes:
    image = Image.new("RGB", (640, 480), color=(245, 235, 200))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
