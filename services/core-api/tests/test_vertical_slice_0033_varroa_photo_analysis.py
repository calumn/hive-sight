from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from test_vertical_slice_0025_varroa_review_slice import (
    _complete_crop,
    _completed_crop_with_two_bees,
    _headers,
)
from test_vertical_slice_0028_frame_mite_count import _patch_ellipse

from hive_sight_core_api.dependencies import (
    build_dev_state,
    get_dev_state,
    get_varroa_photo_analysis_workflow,
)
from hive_sight_core_api.models import InspectionIntent
from hive_sight_core_api.main import app
from hive_sight_core_api.varroa_photo_analysis_workflow import VarroaPhotoAnalysisWorkflow
from hive_sight_core_api.varroa_review_workflow import (
    VarroaDetectorAdapter,
    VarroaDetectorFailure,
    VarroaDetectorRequest,
)


def test_varroa_photo_analysis_persists_run_and_per_bee_evidence(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    adapter = FailFirstThenDetectAdapter()
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_varroa_photo_analysis_workflow] = lambda: VarroaPhotoAnalysisWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        varroa_detector_adapter=adapter,
    )
    client = TestClient(app)
    try:
        workspace_id, crop_id, _, _ = _completed_crop_with_two_bees(client)
        inspection_photo_id = _inspection_photo_id_for_crop(state, crop_id)

        response = _run_photo_analysis(client, workspace_id, inspection_photo_id)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "partial"
        assert body["review_status"] == "unreviewed"
        assert body["eligible_bees"] == 2
        assert body["analysed_bees"] == 1
        assert body["failed_bees"] == 1
        assert body["mites_found"] == 1
        assert body["mite_ratio_basis"] == "analysed_eligible_bees"
        assert body["adapter_type"] == "local_command"
        assert body["adapter_version"] == "fake_local_command_v1"
        assert body["model_reference"] == "fake-varroa-model"
        assert body["command_contract_version"] == "varroa_detector_command_v1"
        assert body["advisor_evidence_eligible"] is False
        assert "incomplete" in body["caveat"]
        assert [result["bee_annotation_id"] for result in body["bee_results"]] == [None, None]
        assert all(result["training_crop_id"] is None for result in body["bee_results"])
        assert all(result["inspection_photo_id"] == inspection_photo_id for result in body["bee_results"])
        assert body["bee_results"][0]["status"] == "failed"
        assert body["bee_results"][0]["raw_error_payload"] is not None
        assert body["bee_results"][1]["status"] == "completed"
        assert body["bee_results"][1]["raw_error_payload"] is None

        listed = client.get(
            f"/v1/inspection-photos/{inspection_photo_id}/varroa-photo-analyses"
            f"?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert listed.status_code == 200
        assert [run["photo_analysis_run_id"] for run in listed.json()["runs"]] == [
            body["photo_analysis_run_id"]
        ]
    finally:
        app.dependency_overrides.clear()


def test_product_photo_analysis_does_not_require_a_training_crop(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, _, _ = _completed_crop_with_two_bees(client)
        inspection_photo_id = _inspection_photo_id_for_crop(state, crop_id)
        response = _run_photo_analysis(client, workspace_id, inspection_photo_id)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"
        assert body["eligible_bees"] == 2
        assert body["analysed_bees"] == 2
        assert body["bees_with_likely_varroa"] == 2
        assert body["bee_results"][0]["training_crop_id"] is None
        assert body["bee_results"][0]["inspection_photo_id"] == inspection_photo_id
        image = client.get(
            "/v1/varroa-photo-analyses/"
            f"{body['photo_analysis_run_id']}/bee-results/"
            f"{body['bee_results'][0]['photo_analysis_bee_result_id']}/head-up-image"
            f"?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert image.status_code == 200
        assert image.headers["content-type"] == "image/png"
        assert image.content.startswith(b"\x89PNG")
    finally:
        app.dependency_overrides.clear()


def test_batch_analysis_skips_a_photo_with_a_produced_result(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, _, _ = _completed_crop_with_two_bees(client)
        inspection_photo_id = _inspection_photo_id_for_crop(state, crop_id)
        first = _run_photo_analysis(client, workspace_id, inspection_photo_id)
        inspection_id = first.json()["inspection_id"]
        state.store.inspections[UUID(inspection_id)] = state.store.inspections[
            UUID(inspection_id)
        ].model_copy(update={"intent": InspectionIntent.varroa_assessment})

        batch = client.post(
            f"/v1/inspections/{inspection_id}/varroa-photo-analyses/batch",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        )

        assert batch.status_code == 201
        assert batch.json()["status"] == "completed"
        assert batch.json()["attempted_photo_ids"] == []
        assert batch.json()["skipped_photo_ids"] == [inspection_photo_id]
    finally:
        app.dependency_overrides.clear()


def test_produced_photo_analysis_cannot_be_started_again(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, _, _ = _completed_crop_with_two_bees(client)
        inspection_photo_id = _inspection_photo_id_for_crop(state, crop_id)

        first = _run_photo_analysis(client, workspace_id, inspection_photo_id)
        second = _run_photo_analysis(client, workspace_id, inspection_photo_id)

        assert first.status_code == 200
        assert second.status_code == 409
        assert second.json()["detail"]["code"] == "photo_analysis_already_produced"
        listed = client.get(
            f"/v1/inspection-photos/{inspection_photo_id}/varroa-photo-analyses"
            f"?workspace_id={workspace_id}",
            headers=_headers(),
        ).json()
        assert len(listed["runs"]) == 1
    finally:
        app.dependency_overrides.clear()


def test_no_usable_bees_photo_analysis_cannot_be_accepted(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, _, _ = _completed_crop_with_two_bees(client)
        inspection_photo_id = _inspection_photo_id_for_crop(state, crop_id)
        app.dependency_overrides[get_varroa_photo_analysis_workflow] = lambda: VarroaPhotoAnalysisWorkflow(
            store=state.store,
            image_loader=state.object_storage.get_object,
            product_candidate_geometries=(),
        )

        created = _run_photo_analysis(client, workspace_id, inspection_photo_id)
        accepted = _review_photo_analysis(
            client,
            workspace_id,
            created.json()["photo_analysis_run_id"],
            "accepted",
        )
        rejected = _review_photo_analysis(
            client,
            workspace_id,
            created.json()["photo_analysis_run_id"],
            "rejected",
            "No usable bees in the photo.",
        )

        assert created.status_code == 200
        assert created.json()["status"] == "no_usable_bees"
        assert created.json()["analysed_bees"] == 0
        assert accepted.status_code == 409
        assert accepted.json()["detail"]["code"] == "photo_analysis_not_acceptable"
        assert rejected.status_code == 200
        assert rejected.json()["review_status"] == "rejected"
        assert rejected.json()["advisor_evidence_eligible"] is False
    finally:
        app.dependency_overrides.clear()


def test_only_accepted_photo_analysis_is_advisor_eligible(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, _, _ = _completed_crop_with_two_bees(client)
        inspection_photo_id = _inspection_photo_id_for_crop(state, crop_id)
        created = _run_photo_analysis(client, workspace_id, inspection_photo_id).json()

        needs_review = _review_photo_analysis(
            client,
            workspace_id,
            created["photo_analysis_run_id"],
            "needs_expert_review",
            "I doubt this result.",
        )
        accepted = _review_photo_analysis(
            client,
            workspace_id,
            created["photo_analysis_run_id"],
            "accepted",
            "Good enough to use.",
        )

        assert created["status"] == "completed"
        assert created["advisor_evidence_eligible"] is False
        assert needs_review.status_code == 200
        assert needs_review.json()["advisor_evidence_eligible"] is False
        assert accepted.status_code == 200
        assert accepted.json()["review_status"] == "accepted"
        assert accepted.json()["advisor_evidence_eligible"] is True
    finally:
        app.dependency_overrides.clear()


def test_non_accepted_photo_analysis_review_requires_a_note(tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id, crop_id, _, _ = _completed_crop_with_two_bees(client)
        inspection_photo_id = _inspection_photo_id_for_crop(state, crop_id)
        created = _run_photo_analysis(client, workspace_id, inspection_photo_id).json()

        response = _review_photo_analysis(
            client, workspace_id, created["photo_analysis_run_id"], "needs_expert_review"
        )

        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "photo_analysis_review_note_required"
    finally:
        app.dependency_overrides.clear()


def _run_photo_analysis(client: TestClient, workspace_id: str, inspection_photo_id: str):
    started = client.post(
        f"/v1/inspection-photos/{inspection_photo_id}/varroa-photo-analyses",
        json={"workspace_id": workspace_id},
        headers=_headers(),
    )
    if started.status_code != 202:
        return started
    completed = client.get(
        f"/v1/inspection-photos/{inspection_photo_id}/varroa-photo-analyses"
        f"?workspace_id={workspace_id}",
        headers=_headers(),
    )
    return _CompletedRunResponse(completed.json()["runs"][-1])


class _CompletedRunResponse:
    status_code = 200

    def __init__(self, payload: dict):
        self._payload = payload

    def json(self) -> dict:
        return self._payload


def _review_photo_analysis(
    client: TestClient,
    workspace_id: str,
    photo_analysis_run_id: str,
    review_status: str,
    review_note: str | None = None,
):
    return client.patch(
        f"/v1/varroa-photo-analyses/{photo_analysis_run_id}/review",
        json={
            "workspace_id": workspace_id,
            "review_status": review_status,
            "review_note": review_note,
        },
        headers=_headers(),
    )


def _inspection_photo_id_for_crop(state, crop_id: str) -> str:
    return str(state.store.training_crops[UUID(crop_id)].inspection_photo_id)


@dataclass
class FailFirstThenDetectAdapter(VarroaDetectorAdapter):
    adapter_type: str = "local_command"
    adapter_version: str = "fake_local_command_v1"
    model_reference: str = "fake-varroa-model"
    command_contract_version: str = "varroa_detector_command_v1"

    def __post_init__(self) -> None:
        self.call_count = 0

    def detect(self, request: VarroaDetectorRequest):
        self.call_count += 1
        if self.call_count == 1:
            raise VarroaDetectorFailure(
                code="adapter_timeout",
                message="The configured Varroa Detector timed out.",
                raw_error_payload='{"code": "adapter_timeout"}',
            )
        return [
            {
                "detection_id": "fake-detection-1",
                "x": 0.5,
                "y": 0.5,
                "width": 0.08,
                "height": 0.06,
                "confidence": 0.91,
                "coordinate_space": "head_up_normalized_crop",
                "source": "fake_local_command",
            }
        ]
