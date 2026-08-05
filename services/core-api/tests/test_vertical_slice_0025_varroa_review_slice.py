from datetime import date
from io import BytesIO
from uuid import UUID

from fastapi.testclient import TestClient
from hive_configuration_test_support import configure_hive
from PIL import Image

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

CURATOR_ID = UUID("00000000-0000-0000-0000-000000000101")


def test_dataset_curator_records_varroa_triage_cues_and_candidates_prioritise_suspected_bees(tmp_path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, first_ellipse_id, second_ellipse_id = _completed_crop_with_two_bees(
            client,
            complete_crop=False,
        )

        cue_update = client.patch(
            f"/v1/training-crop-bee-ellipses/{second_ellipse_id}",
            json={
                "workspace_id": workspace_id,
                "varroa_review_suitability": "body_occluded_or_hard_to_assess",
                "suspected_visible_varroa": True,
            },
            headers=_headers(),
        )
        completed = _complete_crop(client, workspace_id, crop_id)
        candidates = client.get(
            f"/v1/training-crops/{crop_id}/varroa-review-candidates?workspace_id={workspace_id}",
            headers=_headers(),
        )

        assert cue_update.status_code == 200
        assert completed.status_code == 200
        assert cue_update.json()["varroa_review_suitability"] == "body_occluded_or_hard_to_assess"
        assert cue_update.json()["suspected_visible_varroa"] is True
        assert cue_update.json()["varroa_review_suitability_updated_by_user_id"] == str(CURATOR_ID)
        assert candidates.status_code == 200
        body = candidates.json()
        assert body["candidates"][0]["bee_annotation"]["annotation_id"] == second_ellipse_id
        assert body["summary"]["suspected_visible_varroa_cue_count"] == 1
        assert body["summary"]["hard_to_assess_cue_count"] == 1
        assert body["summary"]["caveat"] == "Model-curation summary only; not a Varroa assessment."
        assert first_ellipse_id in [
            candidate["bee_annotation"]["annotation_id"] for candidate in body["candidates"]
        ]
    finally:
        app.dependency_overrides.clear()


def test_dataset_curator_saves_positive_varroa_review_with_marker_and_preview(tmp_path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, ellipse_id, _ = _completed_crop_with_two_bees(client)

        preview = client.get(
            f"/v1/training-crops/{crop_id}/varroa-review-candidates/{ellipse_id}"
            f"/head-up-normalized-preview?workspace_id={workspace_id}",
            headers=_headers(),
        )
        image = client.get(preview.json()["image_url"], headers=_headers())
        saved = client.put(
            f"/v1/training-crops/{crop_id}/varroa-review-candidates/{ellipse_id}/outcome",
            json={
                "workspace_id": workspace_id,
                "outcome": "visible_varroa_present",
                "markers": [{"x": 0.12345, "y": 1}],
            },
            headers=_headers(),
        )
        reopened = client.get(
            f"/v1/training-crops/{crop_id}/varroa-review-candidates?workspace_id={workspace_id}",
            headers=_headers(),
        )

        assert preview.status_code == 200
        assert preview.json()["transform_version"] == "head_up_normalized_bee_crop_v1"
        assert preview.json()["image_width_px"] == 256
        assert image.status_code == 200
        assert image.headers["content-type"] == "image/png"
        assert saved.status_code == 200
        assert saved.json()["outcome"] == "visible_varroa_present"
        assert saved.json()["markers"][0]["x"] == 0.1235
        assert saved.json()["markers"][0]["y"] == 1
        assert saved.json()["sampling_purpose"] == "model_curation"
        assert saved.json()["dataset_selection_method"] == "human_selected"
        assert saved.json()["review_strength"] == "single_curator_review"
        assert saved.json()["annotation_source"] == "human_from_scratch"
        assert reopened.json()["summary"]["visible_varroa_bee_count"] == 1
        assert reopened.json()["summary"]["total_marker_count"] == 1
        reviewed_candidate = next(
            candidate
            for candidate in reopened.json()["candidates"]
            if candidate["bee_annotation"]["annotation_id"] == ellipse_id
        )
        assert reviewed_candidate["review_outcome"]["markers"][0]["x"] == 0.1235
    finally:
        app.dependency_overrides.clear()


def test_varroa_review_blocks_invalid_outcomes_and_ineligible_bees(tmp_path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, complete_ellipse_id, partial_ellipse_id = _completed_crop_with_two_bees(
            client,
            second_annotation_type="partial_visible_bee",
        )

        positive_without_marker = client.put(
            f"/v1/training-crops/{crop_id}/varroa-review-candidates/{complete_ellipse_id}/outcome",
            json={
                "workspace_id": workspace_id,
                "outcome": "visible_varroa_present",
                "markers": [],
            },
            headers=_headers(),
        )
        not_determined_without_note = client.put(
            f"/v1/training-crops/{crop_id}/varroa-review-candidates/{complete_ellipse_id}/outcome",
            json={
                "workspace_id": workspace_id,
                "outcome": "not_determined",
                "markers": [],
            },
            headers=_headers(),
        )
        ineligible = client.put(
            f"/v1/training-crops/{crop_id}/varroa-review-candidates/{partial_ellipse_id}/outcome",
            json={
                "workspace_id": workspace_id,
                "outcome": "no_visible_varroa",
                "markers": [],
            },
            headers=_headers(),
        )

        assert positive_without_marker.status_code == 422
        assert positive_without_marker.json()["detail"]["code"] == "visible_varroa_requires_marker"
        assert not_determined_without_note.status_code == 422
        assert not_determined_without_note.json()["detail"]["code"] == "not_determined_requires_note"
        assert ineligible.status_code == 409
        assert ineligible.json()["detail"]["code"] == "varroa_review_candidate_ineligible"
    finally:
        app.dependency_overrides.clear()


def test_varroa_review_records_active_negative_and_unresolved_outcomes(tmp_path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, first_ellipse_id, second_ellipse_id = _completed_crop_with_two_bees(client)

        negative = client.put(
            f"/v1/training-crops/{crop_id}/varroa-review-candidates/{first_ellipse_id}/outcome",
            json={
                "workspace_id": workspace_id,
                "outcome": "no_visible_varroa",
                "markers": [],
            },
            headers=_headers(),
        )
        unresolved = client.put(
            f"/v1/training-crops/{crop_id}/varroa-review-candidates/{second_ellipse_id}/outcome",
            json={
                "workspace_id": workspace_id,
                "outcome": "not_determined",
                "markers": [],
                "notes": "Wing glare makes the abdomen ambiguous.",
            },
            headers=_headers(),
        )
        candidates = client.get(
            f"/v1/training-crops/{crop_id}/varroa-review-candidates?workspace_id={workspace_id}",
            headers=_headers(),
        ).json()

        assert negative.status_code == 200
        assert negative.json()["outcome"] == "no_visible_varroa"
        assert negative.json()["markers"] == []
        assert unresolved.status_code == 200
        assert unresolved.json()["outcome"] == "not_determined"
        assert unresolved.json()["notes"] == "Wing glare makes the abdomen ambiguous."
        assert candidates["summary"]["reviewed_bee_count"] == 2
        assert candidates["summary"]["no_visible_varroa_bee_count"] == 1
        assert candidates["summary"]["not_determined_bee_count"] == 1
    finally:
        app.dependency_overrides.clear()


def _completed_crop_with_two_bees(
    client: TestClient,
    *,
    second_annotation_type: str = "complete_visible_bee",
    complete_crop: bool = True,
) -> tuple[str, str, str, str]:
    workspace_id = _workspace(client)
    apiary_id = client.post(
        "/v1/apiaries",
        json={"workspace_id": workspace_id, "name": "Varroa Review Apiary"},
        headers=_headers(),
    ).json()["apiary_id"]
    hive_id = client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": "Varroa Review Hive"},
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
            "x-hivesight-filename": "varroa-review.png",
        },
    )
    crop = client.post(
        "/v1/training-crops",
        json={
            "workspace_id": workspace_id,
            "inspection_photo_id": intake.json()["inspection_photo"]["inspection_photo_id"],
            "crop_x": 10,
            "crop_y": 10,
            "crop_width": 300,
            "crop_height": 240,
            "source_image_width_px": 640,
            "source_image_height_px": 480,
        },
        headers=_headers(),
    ).json()
    first = _create_ellipse(client, workspace_id, crop["training_crop_id"], 110, "complete_visible_bee")
    second = _create_ellipse(client, workspace_id, crop["training_crop_id"], 210, second_annotation_type)
    if complete_crop:
        completed = _complete_crop(client, workspace_id, crop["training_crop_id"])
        assert completed.status_code == 200
    return workspace_id, crop["training_crop_id"], first, second


def _complete_crop(client: TestClient, workspace_id: str, training_crop_id: str):
    return client.patch(
        f"/v1/training-crops/{training_crop_id}",
        json={
            "workspace_id": workspace_id,
            "visible_bee_status": "has_visible_bees",
            "review_status": "review_complete",
        },
        headers=_headers(),
    )


def _create_ellipse(
    client: TestClient,
    workspace_id: str,
    training_crop_id: str,
    center_x: int,
    annotation_type: str,
) -> str:
    response = client.post(
        f"/v1/training-crops/{training_crop_id}/bee-ellipses",
        json={
            "workspace_id": workspace_id,
            "annotation_type": annotation_type,
            "center_x": center_x,
            "center_y": 120,
            "radius_x": 28,
            "radius_y": 12,
            "rotation_degrees": 30,
            "orientation_reliability": "reliable",
        },
        headers=_headers(),
    )
    assert response.status_code == 201
    return response.json()["annotation_id"]


def _workspace(client: TestClient) -> str:
    workspace_id = client.get("/v1/dev/session", headers=_headers()).json()["workspace_id"]
    client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": workspace_id, "terms_version": "2026-08-05"},
        headers=_headers(),
    )
    return workspace_id


def _headers() -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(CURATOR_ID)}


def _source_png() -> bytes:
    image = Image.new("RGB", (640, 480), color=(245, 235, 200))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
