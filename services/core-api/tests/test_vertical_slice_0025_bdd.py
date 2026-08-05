from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when
from test_vertical_slice_0025_varroa_review_slice import (
    CURATOR_ID,
    _complete_crop,
    _completed_crop_with_two_bees,
    _headers,
)

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

FEATURES_DIR = Path(__file__).parent / "features"

scenarios(str(FEATURES_DIR / "vertical_slice_0025_varroa_review_outcome_labelling.feature"))


@dataclass
class SliceContext:
    client: TestClient
    workspace_id: str | None = None
    crop_id: str | None = None
    bee_annotation_id: str | None = None
    second_bee_annotation_id: str | None = None
    response: object | None = None


@pytest.fixture
def slice_context(tmp_path: Path) -> SliceContext:
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    try:
        yield SliceContext(client=TestClient(app))
    finally:
        app.dependency_overrides.clear()


@given("a Training Crop has an editable visible bee ellipse")
def editable_visible_bee(slice_context: SliceContext) -> None:
    (
        slice_context.workspace_id,
        slice_context.crop_id,
        slice_context.bee_annotation_id,
        _,
    ) = _completed_crop_with_two_bees(slice_context.client, complete_crop=False)


@given("a completed Training Crop contains a reliable complete visible bee ellipse")
@given("a Head-Up Normalized Bee Crop is open for Varroa review")
def completed_crop_with_eligible_bee(slice_context: SliceContext) -> None:
    (
        slice_context.workspace_id,
        slice_context.crop_id,
        slice_context.bee_annotation_id,
        slice_context.second_bee_annotation_id,
    ) = _completed_crop_with_two_bees(slice_context.client)


@given("a Training Crop contains a partial visible bee or an unreliable-orientation bee")
def crop_with_ineligible_bee(slice_context: SliceContext) -> None:
    (
        slice_context.workspace_id,
        slice_context.crop_id,
        _,
        slice_context.bee_annotation_id,
    ) = _completed_crop_with_two_bees(
        slice_context.client,
        second_annotation_type="partial_visible_bee",
    )


@when("the Dataset Curator marks the bee as body occluded or hard to assess for Varroa review")
def mark_hard_to_assess(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.bee_annotation_id
    slice_context.response = slice_context.client.patch(
        f"/v1/training-crop-bee-ellipses/{slice_context.bee_annotation_id}",
        json={
            "workspace_id": slice_context.workspace_id,
            "varroa_review_suitability": "body_occluded_or_hard_to_assess",
        },
        headers=_headers(),
    )


@when("the Dataset Curator flags suspected visible Varroa on that bee")
def flag_suspected_visible_varroa(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.crop_id and slice_context.bee_annotation_id
    slice_context.response = slice_context.client.patch(
        f"/v1/training-crop-bee-ellipses/{slice_context.bee_annotation_id}",
        json={
            "workspace_id": slice_context.workspace_id,
            "suspected_visible_varroa": True,
        },
        headers=_headers(),
    )
    _complete_crop(slice_context.client, slice_context.workspace_id, slice_context.crop_id)


@when("the Dataset Curator opens that bee for Varroa review")
def open_bee_for_varroa_review(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.crop_id and slice_context.bee_annotation_id
    slice_context.response = slice_context.client.get(
        f"/v1/training-crops/{slice_context.crop_id}/varroa-review-candidates/"
        f"{slice_context.bee_annotation_id}/head-up-normalized-preview"
        f"?workspace_id={slice_context.workspace_id}",
        headers=_headers(),
    )


@when("the Dataset Curator records no visible Varroa")
def record_no_visible_varroa(slice_context: SliceContext) -> None:
    _save_outcome(slice_context, "no_visible_varroa", [])


@when("the Dataset Curator places two mite markers and records visible Varroa present")
def record_visible_varroa(slice_context: SliceContext) -> None:
    _save_outcome(
        slice_context,
        "visible_varroa_present",
        [{"x": 0.25, "y": 0.4}, {"x": 0.65, "y": 0.7}],
    )


@when("the Dataset Curator records not determined with a note")
def record_not_determined(slice_context: SliceContext) -> None:
    _save_outcome(slice_context, "not_determined", [], notes="The body is obscured.")


@when("the Dataset Curator reviews Varroa eligibility for that bee")
def review_ineligible_bee(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.crop_id
    slice_context.response = slice_context.client.get(
        f"/v1/training-crops/{slice_context.crop_id}/varroa-review-candidates"
        f"?workspace_id={slice_context.workspace_id}",
        headers=_headers(),
    )


@when("the Dataset Curator tries to save visible Varroa present without a marker")
def save_positive_without_marker(slice_context: SliceContext) -> None:
    _save_outcome(slice_context, "visible_varroa_present", [])


@when("the Dataset Curator tries to save not determined without a note")
def save_not_determined_without_note(slice_context: SliceContext) -> None:
    _save_outcome(slice_context, "not_determined", [])


@then("HiveSight saves the Varroa review suitability cue for the bee")
def suitability_cue_saved(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    assert slice_context.response.status_code == 200


@then("HiveSight saves the suspected visible Varroa cue for the bee")
def suspected_cue_saved(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    assert slice_context.response.json()["suspected_visible_varroa"] is True


@then("HiveSight records who last updated those cues and when")
def cue_provenance_recorded(slice_context: SliceContext) -> None:
    body = slice_context.response.json()
    assert body["suspected_visible_varroa_updated_by_user_id"] == str(CURATOR_ID)
    assert body["suspected_visible_varroa_updated_at"] is not None


@then("HiveSight does not treat either cue as a Varroa Review Outcome")
def cues_do_not_create_outcome(slice_context: SliceContext) -> None:
    candidates = _candidates(slice_context)
    assert candidates["summary"]["reviewed_bee_count"] == 0


@then("HiveSight shows a Head-Up Normalized Bee Crop for the selected bee")
def preview_shown(slice_context: SliceContext) -> None:
    assert slice_context.response.status_code == 200
    assert slice_context.response.json()["transform_version"] == "head_up_normalized_bee_crop_v1"


@then("HiveSight shows the source Training Crop and bee annotation provenance")
def preview_has_source_provenance(slice_context: SliceContext) -> None:
    body = slice_context.response.json()
    assert body["training_crop_id"] == slice_context.crop_id
    assert body["bee_annotation_geometry_snapshot"]["annotation_id"] == slice_context.bee_annotation_id


@then("HiveSight shows any Varroa triage cues recorded during bee annotation")
def candidates_show_triage_cues(slice_context: SliceContext) -> None:
    candidates = _candidates(slice_context)
    assert "suspected_visible_varroa_cue_count" in candidates["summary"]


@then("HiveSight labels the review purpose as model curation")
def labels_model_curation(slice_context: SliceContext) -> None:
    _save_outcome(slice_context, "no_visible_varroa", [])
    assert slice_context.response.json()["sampling_purpose"] == "model_curation"


@then("HiveSight shows that this is not a Varroa assessment")
def not_varroa_assessment(slice_context: SliceContext) -> None:
    assert _candidates(slice_context)["summary"]["caveat"] == "Model-curation summary only; not a Varroa assessment."


@then("HiveSight saves a Varroa Review Outcome of no_visible_varroa")
def negative_saved(slice_context: SliceContext) -> None:
    assert slice_context.response.status_code == 200
    assert slice_context.response.json()["outcome"] == "no_visible_varroa"


@then("HiveSight records zero Varroa markers")
def zero_markers(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["markers"] == []


@then("HiveSight labels the evidence as an active negative judgement")
def active_negative_labelled(slice_context: SliceContext) -> None:
    assert slice_context.response.json()["review_strength"] == "single_curator_review"


@then("HiveSight saves a Varroa Review Outcome of visible_varroa_present")
def positive_saved(slice_context: SliceContext) -> None:
    assert slice_context.response.status_code == 200
    assert slice_context.response.json()["outcome"] == "visible_varroa_present"


@then("HiveSight records the mite markers in normalized bee-crop coordinates")
def marker_coordinates_saved(slice_context: SliceContext) -> None:
    assert len(slice_context.response.json()["markers"]) == 2


@then("HiveSight reports one visible-Varroa bee and two visible Varroa markers")
def positive_summary(slice_context: SliceContext) -> None:
    summary = _candidates(slice_context)["summary"]
    assert summary["visible_varroa_bee_count"] == 1
    assert summary["total_marker_count"] == 2


@then("HiveSight shows the markers when the review is reopened")
def markers_reopened(slice_context: SliceContext) -> None:
    candidate = _candidate_for_selected_bee(slice_context)
    assert len(candidate["review_outcome"]["markers"]) == 2


@then("HiveSight saves a Varroa Review Outcome of not_determined")
def unresolved_saved(slice_context: SliceContext) -> None:
    assert slice_context.response.status_code == 200
    assert slice_context.response.json()["outcome"] == "not_determined"


@then("HiveSight does not treat the crop as negative training evidence")
def unresolved_not_negative(slice_context: SliceContext) -> None:
    assert _candidates(slice_context)["summary"]["no_visible_varroa_bee_count"] == 0


@then("HiveSight keeps the crop visible as unresolved Varroa evidence")
def unresolved_counted(slice_context: SliceContext) -> None:
    assert _candidates(slice_context)["summary"]["not_determined_bee_count"] == 1


@then("HiveSight explains that the bee is excluded from the first Head-Up Normalized Varroa corpus")
def ineligible_explained(slice_context: SliceContext) -> None:
    candidate = _candidate_for_selected_bee(slice_context)
    assert candidate["eligibility"] == "ineligible"
    assert "partial_visible_bee" in candidate["ineligibility_reasons"]


@then("HiveSight does not allow a Varroa Review Outcome to be saved for that bee in this slice")
def ineligible_save_blocked(slice_context: SliceContext) -> None:
    _save_outcome(slice_context, "no_visible_varroa", [])
    assert slice_context.response.status_code == 409
    assert slice_context.response.json()["detail"]["code"] == "varroa_review_candidate_ineligible"


@then("HiveSight blocks the save and explains that visible Varroa requires marker evidence")
def positive_requires_marker(slice_context: SliceContext) -> None:
    assert slice_context.response.status_code == 422
    assert slice_context.response.json()["detail"]["code"] == "visible_varroa_requires_marker"


@then("HiveSight blocks the save and explains that not determined requires a note")
def not_determined_requires_note(slice_context: SliceContext) -> None:
    assert slice_context.response.status_code == 422
    assert slice_context.response.json()["detail"]["code"] == "not_determined_requires_note"


def _save_outcome(
    slice_context: SliceContext,
    outcome: str,
    markers: list[dict[str, float]],
    *,
    notes: str | None = None,
) -> None:
    assert slice_context.workspace_id and slice_context.crop_id and slice_context.bee_annotation_id
    slice_context.response = slice_context.client.put(
        f"/v1/training-crops/{slice_context.crop_id}/varroa-review-candidates/"
        f"{slice_context.bee_annotation_id}/outcome",
        json={
            "workspace_id": slice_context.workspace_id,
            "outcome": outcome,
            "markers": markers,
            "notes": notes,
        },
        headers=_headers(),
    )


def _candidates(slice_context: SliceContext) -> dict:
    assert slice_context.workspace_id and slice_context.crop_id
    response = slice_context.client.get(
        f"/v1/training-crops/{slice_context.crop_id}/varroa-review-candidates"
        f"?workspace_id={slice_context.workspace_id}",
        headers=_headers(),
    )
    assert response.status_code == 200
    return response.json()


def _candidate_for_selected_bee(slice_context: SliceContext) -> dict:
    candidates = _candidates(slice_context)
    return next(
        candidate
        for candidate in candidates["candidates"]
        if candidate["bee_annotation"]["annotation_id"] == slice_context.bee_annotation_id
    )
