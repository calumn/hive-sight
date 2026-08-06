from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from hive_configuration_test_support import configure_hive
from test_vertical_slice_0025_varroa_review_slice import (
    _complete_crop,
    _completed_crop_with_two_bees,
    _headers,
)
from test_vertical_slice_0026_photo_visible_varroa_summary import _save_outcome
from test_vertical_slice_0028_frame_mite_count import _patch_ellipse

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app


def test_hivesight_assembles_available_advisor_varroa_context_for_one_photo(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, first_bee_id, second_bee_id = _completed_crop_with_two_bees(client)
        inspection_photo_id = _inspection_photo_id_for_crop(state, crop_id)
        inspection = _inspection_for_photo(state, inspection_photo_id)
        _save_outcome(
            client,
            workspace_id,
            crop_id,
            first_bee_id,
            "visible_varroa_present",
            [{"x": 0.25, "y": 0.35}],
        )
        _save_outcome(client, workspace_id, crop_id, second_bee_id, "no_visible_varroa", [])

        response = _assemble_context(client, inspection.hive_id, inspection_photo_id)

        assert response.status_code == 200
        body = response.json()
        assert body["contract_version"] == "advisor_varroa_context_v1"
        assert body["status"] == "available"
        assert body["workspace_id"] == workspace_id
        assert body["hive_id"] == str(inspection.hive_id)
        assert body["apiary_id"] == str(state.store.hives[inspection.hive_id].apiary_id)
        assert body["inspection_id"] == str(inspection.inspection_id)
        assert body["inspection_photo_id"] == inspection_photo_id
        assert body["inspection_date"] == "2026-08-05"
        assert body["jurisdiction_id"] is None
        assert body["varroa_evidence"]["source_intent"] == "training_data_collection"
        assert body["varroa_evidence"]["evidence_readiness"] == "integration_test_only"
        frame_count = body["varroa_evidence"]["frame_mite_count"]
        assert frame_count["status"] == "completed"
        assert frame_count["processed_bee_count"] == 2
        assert frame_count["likely_visible_varroa_detection_count"] == 2
        assert frame_count["bees_with_likely_varroa_count"] == 2
        assert frame_count["adapter_type"] == "deterministic_stub"
        assert "bee_results" not in frame_count
        photo_evidence = body["varroa_evidence"]["photo_visible_varroa_evidence"]
        assert photo_evidence["visible_varroa_bee_count"] == 1
        assert photo_evidence["visible_mite_marker_count"] == 1
        assert photo_evidence["active_negative_bee_count"] == 1
        assert body["treatment_history"] == {
            "status": "not_modelled",
            "recent_treatment_count": None,
            "courses": [],
        }
        assert body["advisor_required_situational_inputs"]["status"] == "not_modelled"
        assert body["advisor_request_readiness"]["can_request_advice"] is False
        assert body["advisor_request_readiness"]["blocking_reasons"] == [
            "jurisdiction_not_provided",
            "source_intent_not_varroa_assessment",
            "treatment_history_not_modelled",
            "advisor_required_situational_inputs_not_modelled",
        ]
        assert "not treatment advice" in body["not_advice_reason"]
    finally:
        app.dependency_overrides.clear()


def test_advisor_context_is_not_available_when_no_frame_evidence_can_be_counted(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, first_bee_id, _ = _completed_crop_with_two_bees(
            client,
            second_annotation_type="partial_visible_bee",
            complete_crop=False,
        )
        _patch_ellipse(client, workspace_id, first_bee_id, annotation_type="partial_visible_bee")
        completed = _complete_crop(client, workspace_id, crop_id)
        assert completed.status_code == 200
        inspection_photo_id = _inspection_photo_id_for_crop(state, crop_id)
        inspection = _inspection_for_photo(state, inspection_photo_id)

        response = _assemble_context(client, inspection.hive_id, inspection_photo_id)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "not_available"
        assert body["workspace_id"] == workspace_id
        assert body["inspection_photo_id"] == inspection_photo_id
        assert body["varroa_evidence"]["frame_mite_count"]["status"] == "not_available"
        assert body["varroa_evidence"]["frame_mite_count"]["not_assessed_reasons"] == {
            "partial_visible_bee": 2
        }
        assert "frame_mite_count_not_available" in body["advisor_request_readiness"][
            "blocking_reasons"
        ]
        assert "not treatment advice" in body["not_advice_reason"]
    finally:
        app.dependency_overrides.clear()


def test_advisor_context_rejects_photo_from_a_different_hive(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, _, _ = _completed_crop_with_two_bees(client)
        inspection_photo_id = _inspection_photo_id_for_crop(state, crop_id)
        other_hive_id = _create_other_hive(client, workspace_id)

        response = _assemble_context(client, UUID(other_hive_id), inspection_photo_id)

        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "photo_hive_mismatch"
        assert "frame_mite_count" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_jurisdiction_is_optional_for_context_but_blocks_advice_readiness(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        _, crop_id, _, _ = _completed_crop_with_two_bees(client)
        inspection_photo_id = _inspection_photo_id_for_crop(state, crop_id)
        inspection = _inspection_for_photo(state, inspection_photo_id)

        without_jurisdiction = _assemble_context(client, inspection.hive_id, inspection_photo_id)
        with_jurisdiction = _assemble_context(
            client,
            inspection.hive_id,
            inspection_photo_id,
            jurisdiction_id="uk-england",
        )

        assert without_jurisdiction.status_code == 200
        assert "jurisdiction_not_provided" in without_jurisdiction.json()[
            "advisor_request_readiness"
        ]["blocking_reasons"]
        assert with_jurisdiction.status_code == 200
        assert with_jurisdiction.json()["jurisdiction_id"] == "uk-england"
        assert "jurisdiction_not_provided" not in with_jurisdiction.json()[
            "advisor_request_readiness"
        ]["blocking_reasons"]
        assert with_jurisdiction.json()["advisor_request_readiness"]["can_request_advice"] is False
    finally:
        app.dependency_overrides.clear()


def _assemble_context(
    client: TestClient,
    hive_id: UUID,
    inspection_photo_id: str,
    *,
    jurisdiction_id: str | None = None,
):
    return client.post(
        f"/v1/hives/{hive_id}/advisor-varroa-context",
        json={"inspection_photo_id": inspection_photo_id, "jurisdiction_id": jurisdiction_id},
        headers=_headers(),
    )


def _inspection_photo_id_for_crop(state, crop_id: str) -> str:
    return str(state.store.training_crops[UUID(crop_id)].inspection_photo_id)


def _inspection_for_photo(state, inspection_photo_id: str):
    photo = state.store.inspection_photos[UUID(inspection_photo_id)]
    return state.store.inspections[photo.inspection_id]


def _create_other_hive(client: TestClient, workspace_id: str) -> str:
    apiary_id = client.post(
        "/v1/apiaries",
        json={"workspace_id": workspace_id, "name": "Other Advisor Context Apiary"},
        headers=_headers(),
    ).json()["apiary_id"]
    hive_id = client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": "Other Advisor Context Hive"},
        headers=_headers(),
    ).json()["hive_id"]
    configure_hive(client, workspace_id=workspace_id, hive_id=hive_id, headers=_headers())
    return hive_id
