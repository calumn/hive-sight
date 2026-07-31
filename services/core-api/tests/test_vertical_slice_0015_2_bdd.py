from dataclasses import dataclass
from pathlib import Path

from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

from test_model_candidate_crop_pre_labelling_slice import (
    _create_dataset_version,
    _create_editable_crop,
    _create_reviewed_crop_item,
    _headers,
    _train_fake_candidate,
    _workspace,
)

FEATURES_DIR = Path(__file__).parent / "features"
scenarios(str(FEATURES_DIR / "vertical_slice_0015_2_model_candidate_crop_pre_labelling.feature"))


@dataclass
class SliceContext:
    client: TestClient
    workspace_id: str
    model_candidate_id: str | None = None
    eligible_crop_id: str | None = None
    included_crop_id: str | None = None
    response_body: dict[str, object] | None = None
    status_code: int | None = None


@given("a completed Bee Detector Model Candidate exists", target_fixture="slice_context")
def completed_model_candidate_exists(tmp_path: Path) -> SliceContext:
    state = build_dev_state(
        dataset_export_root=tmp_path / "exports",
        model_artifact_root=tmp_path / "model-runs",
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    workspace_id = _workspace(client)
    included_crop_id = _create_reviewed_crop_item(client, workspace_id, "training", 10, 10)
    _create_reviewed_crop_item(client, workspace_id, "validation", 250, 10)
    dataset_version = _create_dataset_version(client, workspace_id)
    training_run = _train_fake_candidate(client, workspace_id, dataset_version["dataset_version_id"])
    return SliceContext(
        client=client,
        workspace_id=workspace_id,
        model_candidate_id=str(training_run["model_candidate_id"]),
        included_crop_id=included_crop_id,
    )


@given("an editable Training Crop was not included in that Model Candidate Dataset Version")
def eligible_editable_crop_exists(slice_context: SliceContext) -> None:
    crop = _create_editable_crop(slice_context.client, slice_context.workspace_id, 60, 250)
    slice_context.eligible_crop_id = str(crop["training_crop_id"])


@given("an editable Training Crop was included in that Model Candidate Dataset Version")
def included_editable_crop_exists(slice_context: SliceContext) -> None:
    assert slice_context.included_crop_id is not None
    response = slice_context.client.patch(
        f"/v1/training-crops/{slice_context.included_crop_id}",
        json={"workspace_id": slice_context.workspace_id, "review_status": "review_pending"},
        headers=_headers(),
    )
    assert response.status_code == 200


@when("the Dataset Curator asks the Model Candidate to suggest bees for the crop")
def curator_requests_candidate_suggestions(slice_context: SliceContext) -> None:
    crop_id = slice_context.eligible_crop_id or slice_context.included_crop_id
    assert crop_id is not None
    response = slice_context.client.post(
        f"/v1/training-crops/{crop_id}/candidate-bee-annotations",
        json={
            "workspace_id": slice_context.workspace_id,
            "model_candidate_id": slice_context.model_candidate_id,
            "confidence_threshold": 0.1,
        },
        headers=_headers(),
    )
    slice_context.status_code = response.status_code
    slice_context.response_body = response.json()


@then("the Core API returns transient candidate bee proposals")
def core_api_returns_transient_proposals(slice_context: SliceContext) -> None:
    assert slice_context.status_code == 200
    assert slice_context.response_body is not None
    suggestions = slice_context.response_body["suggestions"]
    assert isinstance(suggestions, list)
    assert len(suggestions) == 2
    evidence = slice_context.client.get(
        f"/v1/training-crops/{slice_context.eligible_crop_id}/evidence?workspace_id={slice_context.workspace_id}",
        headers=_headers(),
    ).json()
    assert evidence["bee_ellipses"] == []


@when("the Dataset Curator accepts a candidate proposal as a reviewed partial bee")
def curator_accepts_candidate_proposal(slice_context: SliceContext) -> None:
    assert slice_context.response_body is not None
    assert slice_context.eligible_crop_id is not None
    suggestion = slice_context.response_body["suggestions"][0]
    response = slice_context.client.post(
        f"/v1/training-crops/{slice_context.eligible_crop_id}/bee-ellipses",
        json={
            "workspace_id": slice_context.workspace_id,
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
    slice_context.status_code = response.status_code
    slice_context.response_body = response.json()


@then("the Training Crop evidence records model-candidate provenance")
def crop_evidence_records_model_candidate_provenance(slice_context: SliceContext) -> None:
    assert slice_context.status_code == 201
    assert slice_context.response_body is not None
    assert slice_context.response_body["source"] == "model_candidate"
    assert slice_context.response_body["review_method"] == "human_reviewed_candidate"
    assert slice_context.response_body["candidate_review_decision"] == "accepted_with_edits"
    app.dependency_overrides.clear()


@then("candidate pre-labelling is blocked by the frozen Dataset Version boundary")
def candidate_pre_labelling_is_blocked(slice_context: SliceContext) -> None:
    assert slice_context.status_code == 409
    assert slice_context.response_body is not None
    assert slice_context.response_body["detail"]["code"] == "crop_in_candidate_dataset_version"
    app.dependency_overrides.clear()
