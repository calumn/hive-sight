from pytest_bdd import given, scenarios, then, when
from test_vertical_slice_0025_bdd import (
    SliceContext,
    _candidate_for_selected_bee,
    _candidates,
    _save_outcome,
    completed_crop_with_eligible_bee,
    slice_context,
)

scenarios("../../../acceptance/features/varroa/visible-varroa-review-outcome.feature")


@given("a Dataset Curator has opened an eligible bee for Varroa review")
def opened_eligible_bee_for_varroa_review(slice_context: SliceContext) -> None:
    completed_crop_with_eligible_bee(slice_context)


@when("the Dataset Curator records visible Varroa with two mite markers")
def record_visible_varroa_with_two_mite_markers(slice_context: SliceContext) -> None:
    _save_outcome(
        slice_context,
        "visible_varroa_present",
        [{"x": 0.25, "y": 0.4}, {"x": 0.65, "y": 0.7}],
    )


@then("HiveSight preserves a visible-Varroa review outcome for that bee")
def visible_varroa_outcome_is_preserved(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    assert slice_context.response.status_code == 200
    assert slice_context.response.json()["outcome"] == "visible_varroa_present"


@then("HiveSight preserves two mite markers for that bee")
def two_mite_markers_are_preserved(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    assert len(slice_context.response.json()["markers"]) == 2


@then("HiveSight reports one visible-Varroa bee and two visible Varroa markers")
def visible_varroa_summary_reports_one_bee_and_two_markers(slice_context: SliceContext) -> None:
    summary = _candidates(slice_context)["summary"]
    assert summary["visible_varroa_bee_count"] == 1
    assert summary["total_marker_count"] == 2


@then("HiveSight shows the saved markers when the review is reopened")
def saved_markers_are_visible_when_reopened(slice_context: SliceContext) -> None:
    candidate = _candidate_for_selected_bee(slice_context)
    assert candidate["review_outcome"]["outcome"] == "visible_varroa_present"
    assert len(candidate["review_outcome"]["markers"]) == 2
