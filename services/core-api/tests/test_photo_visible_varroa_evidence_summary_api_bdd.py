from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when
from test_vertical_slice_0026_photo_visible_varroa_summary import (
    _complete_crop,
    _create_ellipse,
    _get_summary,
    _headers,
    _photo_with_three_crops,
    _save_outcome,
)

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

scenarios("../../../acceptance/features/varroa/photo-visible-varroa-evidence-summary.feature")


@dataclass
class SliceContext:
    client: TestClient
    workspace_id: str | None = None
    photo_id: str | None = None
    first_crop_id: str | None = None
    second_crop_id: str | None = None
    unfinished_crop_id: str | None = None
    response: object | None = None


@pytest.fixture
def slice_context(tmp_path: Path) -> SliceContext:
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    try:
        yield SliceContext(client=TestClient(app))
    finally:
        app.dependency_overrides.clear()


@given("a Training Data Collection Inspection Photo has completed Training Crops")
def photo_has_completed_training_crops(slice_context: SliceContext) -> None:
    (
        slice_context.workspace_id,
        slice_context.photo_id,
        slice_context.first_crop_id,
        slice_context.second_crop_id,
        slice_context.unfinished_crop_id,
    ) = _photo_with_three_crops(slice_context.client)
    assert slice_context.workspace_id and slice_context.first_crop_id and slice_context.second_crop_id


@given("eligible complete bees on those crops have Varroa Review Outcomes")
def eligible_bees_have_outcomes(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.first_crop_id and slice_context.second_crop_id
    positive = _create_ellipse(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.first_crop_id,
        80,
        "complete_visible_bee",
    )
    negative = _create_ellipse(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.first_crop_id,
        140,
        "complete_visible_bee",
    )
    unresolved = _create_ellipse(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.second_crop_id,
        80,
        "complete_visible_bee",
    )
    _create_ellipse(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.second_crop_id,
        125,
        "complete_visible_bee",
    )
    _create_ellipse(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.second_crop_id,
        170,
        "partial_visible_bee",
    )
    _complete_crop(slice_context.client, slice_context.workspace_id, slice_context.first_crop_id)
    _complete_crop(slice_context.client, slice_context.workspace_id, slice_context.second_crop_id)
    _save_outcome(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.first_crop_id,
        positive,
        "visible_varroa_present",
        [{"x": 0.25, "y": 0.35}, {"x": 0.55, "y": 0.65}],
    )
    _save_outcome(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.first_crop_id,
        negative,
        "no_visible_varroa",
        [],
    )
    _save_outcome(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.second_crop_id,
        unresolved,
        "not_determined",
        [],
        notes="The body is hidden by glare.",
    )


@given("one reviewed bee has two Varroa markers")
def one_reviewed_bee_has_two_markers(slice_context: SliceContext) -> None:
    photo_has_completed_training_crops(slice_context)
    assert slice_context.workspace_id and slice_context.first_crop_id
    positive = _create_ellipse(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.first_crop_id,
        80,
        "complete_visible_bee",
    )
    negative = _create_ellipse(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.first_crop_id,
        140,
        "complete_visible_bee",
    )
    _complete_crop(slice_context.client, slice_context.workspace_id, slice_context.first_crop_id)
    _save_outcome(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.first_crop_id,
        positive,
        "visible_varroa_present",
        [{"x": 0.25, "y": 0.35}, {"x": 0.55, "y": 0.65}],
    )
    _save_outcome(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.first_crop_id,
        negative,
        "no_visible_varroa",
        [],
    )


@given("another reviewed bee has no visible Varroa")
def another_reviewed_bee_has_no_visible_varroa(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.first_crop_id


@given("a photo has eligible complete bees without determinate Varroa outcomes")
def photo_has_non_determinate_bees(slice_context: SliceContext) -> None:
    photo_has_completed_training_crops(slice_context)
    assert slice_context.workspace_id and slice_context.first_crop_id
    unresolved = _create_ellipse(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.first_crop_id,
        80,
        "complete_visible_bee",
    )
    _create_ellipse(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.first_crop_id,
        140,
        "complete_visible_bee",
    )
    _complete_crop(slice_context.client, slice_context.workspace_id, slice_context.first_crop_id)
    _save_outcome(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.first_crop_id,
        unresolved,
        "not_determined",
        [],
        notes="The body is hidden by glare.",
    )


@given("a photo has partial visible bees or bees with unreliable orientation")
def photo_has_ineligible_bees(slice_context: SliceContext) -> None:
    photo_has_completed_training_crops(slice_context)
    assert slice_context.workspace_id and slice_context.first_crop_id
    _create_ellipse(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.first_crop_id,
        80,
        "complete_visible_bee",
    )
    _create_ellipse(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.first_crop_id,
        140,
        "partial_visible_bee",
    )
    _complete_crop(slice_context.client, slice_context.workspace_id, slice_context.first_crop_id)


@given("a Training Data Collection Inspection Photo has one completed Training Crop")
def photo_has_one_completed_crop(slice_context: SliceContext) -> None:
    (
        slice_context.workspace_id,
        slice_context.photo_id,
        slice_context.first_crop_id,
        slice_context.second_crop_id,
        slice_context.unfinished_crop_id,
    ) = _photo_with_three_crops(slice_context.client)
    assert slice_context.workspace_id and slice_context.first_crop_id
    assert slice_context.second_crop_id
    slice_context.client.delete(
        f"/v1/training-crops/{slice_context.second_crop_id}?workspace_id={slice_context.workspace_id}",
        headers=_headers(),
    )
    _create_ellipse(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.first_crop_id,
        80,
        "complete_visible_bee",
    )
    _complete_crop(slice_context.client, slice_context.workspace_id, slice_context.first_crop_id)


@given("the same photo has one unfinished Training Crop")
def same_photo_has_unfinished_crop(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.unfinished_crop_id
    _create_ellipse(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.unfinished_crop_id,
        80,
        "complete_visible_bee",
    )


@given("a photo has a photo-visible Varroa evidence summary with at least one determinate eligible bee outcome")
def photo_has_advisor_ready_evidence(slice_context: SliceContext) -> None:
    one_reviewed_bee_has_two_markers(slice_context)


@when("the Dataset Curator opens the Varroa Review stage")
@when("HiveSight calculates the photo-visible Varroa evidence summary")
@when("an integration client checks whether Advisor-ready Varroa context exists")
def calculate_summary(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.photo_id
    slice_context.response = _get_summary(
        slice_context.client,
        slice_context.workspace_id,
        slice_context.photo_id,
    )


@then("HiveSight reports reviewed bee count, visible-Varroa bee count, visible mite marker count, active negative count, not-determined count, unreviewed eligible count, and ineligible bee count")
def reports_breakdown(slice_context: SliceContext) -> None:
    body = _body(slice_context)
    assert body["reviewed_eligible_bee_count"] == 3
    assert body["visible_varroa_bee_count"] == 1
    assert body["visible_mite_marker_count"] == 2
    assert body["active_negative_bee_count"] == 1
    assert body["not_determined_bee_count"] == 1
    assert body["unreviewed_eligible_bee_count"] == 1
    assert body["ineligible_or_not_assessed_bee_count"] == 1


@then("HiveSight shows review completion and determinate Varroa coverage")
def shows_coverage(slice_context: SliceContext) -> None:
    body = _body(slice_context)
    assert body["review_completion_percent"] == 75.0
    assert body["determinate_varroa_coverage_percent"] == 50.0


@then("HiveSight labels the result as photo-visible evidence, not a treatment recommendation")
def labels_not_advice(slice_context: SliceContext) -> None:
    caveats = _body(slice_context)["caveats"].lower()
    assert "photo-visible evidence" in caveats
    assert "not treatment advice" in caveats


@then("HiveSight reports one visible-Varroa bee")
def reports_one_positive_bee(slice_context: SliceContext) -> None:
    assert _body(slice_context)["visible_varroa_bee_count"] == 1


@then("HiveSight reports two visible mite markers")
def reports_two_markers(slice_context: SliceContext) -> None:
    assert _body(slice_context)["visible_mite_marker_count"] == 2


@then("HiveSight does not treat marker count and positive bee count as the same measure")
def marker_and_bee_counts_are_distinct(slice_context: SliceContext) -> None:
    body = _body(slice_context)
    assert body["visible_varroa_bee_count"] != body["visible_mite_marker_count"]


@then("HiveSight includes those bees in the eligible denominator")
def includes_non_determinate_in_denominator(slice_context: SliceContext) -> None:
    assert _body(slice_context)["eligible_complete_bee_count"] == 2


@then("HiveSight reports review completion and determinate Varroa coverage below 100%")
def reports_incomplete_coverage(slice_context: SliceContext) -> None:
    body = _body(slice_context)
    assert body["review_completion_percent"] < 100.0
    assert body["determinate_varroa_coverage_percent"] < 100.0


@then("HiveSight shows a coverage warning")
def shows_coverage_warning(slice_context: SliceContext) -> None:
    assert "coverage is incomplete" in _body(slice_context)["caveats"]


@then("HiveSight reports them as ineligible or not assessed for Varroa")
def reports_ineligible(slice_context: SliceContext) -> None:
    assert _body(slice_context)["ineligible_or_not_assessed_bee_count"] == 1


@then("HiveSight excludes them from the eligible complete-bee denominator")
def excludes_ineligible_from_denominator(slice_context: SliceContext) -> None:
    assert _body(slice_context)["eligible_complete_bee_count"] == 1


@then("HiveSight keeps their count visible in the evidence breakdown")
def keeps_ineligible_visible(slice_context: SliceContext) -> None:
    assert "ineligible_or_not_assessed_bee_count" in _body(slice_context)


@then("HiveSight includes the completed crop in the evidence counts")
def includes_completed_crop(slice_context: SliceContext) -> None:
    body = _body(slice_context)
    assert body["completed_training_crop_count"] == 1
    assert body["eligible_complete_bee_count"] == 1


@then("HiveSight excludes the unfinished crop from bee, marker, positive, negative, and coverage counts")
def excludes_unfinished_crop_counts(slice_context: SliceContext) -> None:
    body = _body(slice_context)
    assert body["unfinished_training_crop_count"] == 1
    assert body["eligible_complete_bee_count"] == 1
    assert body["visible_varroa_bee_count"] == 0
    assert body["active_negative_bee_count"] == 0
    assert body["visible_mite_marker_count"] == 0


@then("HiveSight shows that one unfinished crop was not included")
def shows_unfinished_caveat(slice_context: SliceContext) -> None:
    assert "unfinished crop" in _body(slice_context)["caveats"]


@then("HiveSight reports that Varroa evidence context is available with caveats")
def advisor_context_available(slice_context: SliceContext) -> None:
    body = _body(slice_context)
    assert body["advisor_context_available"] is True
    assert body["readiness_state"] in {"partial_evidence", "complete_reviewed_evidence"}
    assert body["caveats"]


@then("HiveSight does not produce a treatment recommendation")
def no_treatment_recommendation(slice_context: SliceContext) -> None:
    assert "treatment_recommendation" not in _body(slice_context)


def _body(slice_context: SliceContext) -> dict[str, object]:
    assert slice_context.response is not None
    assert slice_context.response.status_code == 200
    return slice_context.response.json()
