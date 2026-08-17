from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app


FEATURE = "../../../acceptance/features/varroa/hive-frame-slot-inspection-photo-context.feature"
USER_ID = UUID("00000000-0000-0000-0000-000000000101")

scenarios(FEATURE)


@dataclass
class SliceContext:
    client: TestClient
    workspace_id: str | None = None
    apiary_id: str | None = None
    hive_id: str | None = None
    inspection_id: str | None = None
    observations: list[dict[str, object]] = field(default_factory=list)
    selected_observation: dict[str, object] | None = None
    response: object | None = None
    side_a_photo: dict[str, object] | None = None
    side_b_photo: dict[str, object] | None = None


@pytest.fixture
def slice_context(tmp_path: Path) -> SliceContext:
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    app.dependency_overrides[get_dev_state] = lambda: state
    context = SliceContext(client=TestClient(app))
    try:
        yield context
    finally:
        app.dependency_overrides.clear()


def _headers() -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(USER_ID)}


def _bootstrap_hive(context: SliceContext, brood_slot_count: int) -> None:
    session = context.client.get("/v1/dev/session", headers=_headers())
    assert session.status_code == 200
    context.workspace_id = session.json()["workspace_id"]
    accepted = context.client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": context.workspace_id, "terms_version": "2026-08-17"},
        headers=_headers(),
    )
    assert accepted.status_code == 200
    apiary = context.client.post(
        "/v1/apiaries",
        json={"workspace_id": context.workspace_id, "name": "Home apiary"},
        headers=_headers(),
    )
    assert apiary.status_code == 201
    context.apiary_id = apiary.json()["apiary_id"]
    hive = context.client.post(
        "/v1/hives",
        json={"apiary_id": context.apiary_id, "name": "Hive A"},
        headers=_headers(),
    )
    assert hive.status_code == 201
    context.hive_id = hive.json()["hive_id"]
    _configure_hive(context, brood_slot_count)


def _configure_hive(context: SliceContext, brood_slot_count: int) -> None:
    assert context.workspace_id and context.hive_id
    response = context.client.put(
        f"/v1/hives/{context.hive_id}/configuration",
        json={
            "workspace_id": context.workspace_id,
            "frame_standard_id": "british_national_deep_brood",
            "brood_slot_count": brood_slot_count,
        },
        headers=_headers(),
    )
    assert response.status_code == 200


def _create_inspection(context: SliceContext) -> None:
    assert context.hive_id
    response = context.client.post(
        "/v1/inspections",
        json={
            "hive_id": context.hive_id,
            "inspection_date": str(date(2026, 8, 17)),
            "intent": "varroa_assessment",
        },
        headers=_headers(),
    )
    assert response.status_code == 201
    context.inspection_id = response.json()["inspection_id"]
    _refresh_observations(context)


def _refresh_observations(context: SliceContext) -> None:
    assert context.workspace_id and context.inspection_id
    response = context.client.get(
        f"/v1/inspections/{context.inspection_id}/frame-observations"
        f"?workspace_id={context.workspace_id}",
        headers=_headers(),
    )
    assert response.status_code == 200
    context.observations = response.json()["observations"]


def _observation_for_slot(context: SliceContext, slot_number: int) -> dict[str, object]:
    for observation in context.observations:
        slot = observation["hive_frame_slot"]
        if slot["slot_number"] == slot_number:
            return observation
    raise AssertionError(f"Expected brood slot {slot_number}.")


def _patch_observation(
    context: SliceContext,
    observation: dict[str, object],
    *,
    observation_status: str,
    continuity_status: str | None = None,
) -> dict[str, object]:
    assert context.workspace_id
    response = context.client.patch(
        f"/v1/inspection-frame-observations/{observation['inspection_frame_observation_id']}",
        json={
            "workspace_id": context.workspace_id,
            "observation_status": observation_status,
            "continuity_status": continuity_status,
        },
        headers=_headers(),
    )
    context.response = response
    assert response.status_code == 200
    updated = response.json()
    _refresh_observations(context)
    context.selected_observation = updated
    return updated


def _attach_photo(
    context: SliceContext,
    observation: dict[str, object],
    frame_side: str,
    filename: str,
) -> object:
    assert context.workspace_id and context.inspection_id
    response = context.client.post(
        f"/v1/inspection-photos/intake?workspace_id={context.workspace_id}"
        f"&inspection_id={context.inspection_id}"
        f"&inspection_frame_observation_id={observation['inspection_frame_observation_id']}"
        f"&frame_side={frame_side}",
        content=b"fake-image-bytes",
        headers={
            **_headers(),
            "content-type": "image/jpeg",
            "x-hivesight-filename": filename,
        },
    )
    context.response = response
    return response


@given("a Beekeeper has configured a hive with 10 active brood Hive Frame Slots")
def configured_hive_with_ten_slots(slice_context: SliceContext) -> None:
    _bootstrap_hive(slice_context, brood_slot_count=10)


@given("the Workspace has an accepted Workspace Data Use Agreement")
def workspace_has_terms(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None


@when("the Beekeeper creates a Varroa Assessment Inspection for that hive")
def beekeeper_creates_varroa_inspection(slice_context: SliceContext) -> None:
    _create_inspection(slice_context)


@then("HiveSight shows one pending Inspection Frame Observation for each active brood slot")
def pending_observations_are_shown(slice_context: SliceContext) -> None:
    assert len(slice_context.observations) == 10
    assert {item["observation_status"] for item in slice_context.observations} == {"pending"}
    assert {item["continuity_status"] for item in slice_context.observations} == {"pending"}


@then("HiveSight prevents photos from being attached to those pending observations")
def pending_observations_reject_photos(slice_context: SliceContext) -> None:
    response = _attach_photo(slice_context, slice_context.observations[0], "side_a", "pending.jpg")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "inspection_frame_observation_not_inspected"


@given("a Varroa Assessment Inspection has a pending observation for brood slot 6")
def pending_observation_for_slot_six(slice_context: SliceContext) -> None:
    _bootstrap_hive(slice_context, brood_slot_count=10)
    _create_inspection(slice_context)
    slice_context.selected_observation = _observation_for_slot(slice_context, 6)
    assert slice_context.selected_observation["observation_status"] == "pending"


@when("the Beekeeper marks brood slot 6 inspected")
def beekeeper_marks_slot_six_inspected(slice_context: SliceContext) -> None:
    assert slice_context.selected_observation
    response = slice_context.client.patch(
        f"/v1/inspection-frame-observations/"
        f"{slice_context.selected_observation['inspection_frame_observation_id']}",
        json={
            "workspace_id": slice_context.workspace_id,
            "observation_status": "inspected",
        },
        headers=_headers(),
    )
    slice_context.response = response


@then("HiveSight asks whether the observed frame is continuous with the previous observation")
def continuity_is_required(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    assert slice_context.response.status_code == 422
    assert slice_context.response.json()["detail"]["code"] == "continuity_required_for_inspected"


@when("the Beekeeper records that the observed frame is continuous with the previous observation")
def beekeeper_records_continuity(slice_context: SliceContext) -> None:
    assert slice_context.selected_observation
    slice_context.selected_observation = _patch_observation(
        slice_context,
        slice_context.selected_observation,
        observation_status="inspected",
        continuity_status="continuous_with_previous_observation",
    )


@when("the Beekeeper attaches one side A photo and one side B photo to that observation")
def beekeeper_attaches_both_side_photos(slice_context: SliceContext) -> None:
    assert slice_context.selected_observation
    side_a = _attach_photo(slice_context, slice_context.selected_observation, "side_a", "side-a.jpg")
    assert side_a.status_code == 202
    slice_context.side_a_photo = side_a.json()["inspection_photo"]
    side_b = _attach_photo(slice_context, slice_context.selected_observation, "side_b", "side-b.jpg")
    assert side_b.status_code == 202
    slice_context.side_b_photo = side_b.json()["inspection_photo"]


@then("HiveSight shows both photos under the same Inspection Frame Observation")
def both_photos_share_observation(slice_context: SliceContext) -> None:
    assert slice_context.side_a_photo and slice_context.side_b_photo
    assert (
        slice_context.side_a_photo["inspection_frame_observation_id"]
        == slice_context.side_b_photo["inspection_frame_observation_id"]
    )
    assert (
        slice_context.side_a_photo["inspection_frame_observation_id"]
        == slice_context.selected_observation["inspection_frame_observation_id"]
    )


@then("HiveSight shows side A and side B as separate frame-side evidence")
def side_photos_are_separate(slice_context: SliceContext) -> None:
    assert slice_context.side_a_photo and slice_context.side_b_photo
    assert slice_context.side_a_photo["frame_side"] == "side_a"
    assert slice_context.side_b_photo["frame_side"] == "side_b"


@given("an inspected brood slot observation already has a side A photo and a side B photo")
def inspected_observation_with_both_sides(slice_context: SliceContext) -> None:
    pending_observation_for_slot_six(slice_context)
    assert slice_context.selected_observation
    slice_context.selected_observation = _patch_observation(
        slice_context,
        slice_context.selected_observation,
        observation_status="inspected",
        continuity_status="continuous_with_previous_observation",
    )
    beekeeper_attaches_both_side_photos(slice_context)


@when("the Beekeeper tries to attach another side A photo")
def try_duplicate_side_a(slice_context: SliceContext) -> None:
    assert slice_context.selected_observation
    _attach_photo(slice_context, slice_context.selected_observation, "side_a", "duplicate-a.jpg")


@then("HiveSight rejects the photo")
def photo_is_rejected(slice_context: SliceContext) -> None:
    assert slice_context.response is not None
    assert slice_context.response.status_code == 409


@when("the Beekeeper tries to attach an unknown-side photo")
def try_unknown_side_photo(slice_context: SliceContext) -> None:
    assert slice_context.selected_observation
    _attach_photo(slice_context, slice_context.selected_observation, "unknown", "unknown.jpg")


@given("an inspected brood slot observation has one unknown-side photo")
def inspected_observation_with_unknown_photo(slice_context: SliceContext) -> None:
    pending_observation_for_slot_six(slice_context)
    assert slice_context.selected_observation
    slice_context.selected_observation = _patch_observation(
        slice_context,
        slice_context.selected_observation,
        observation_status="inspected",
        continuity_status="continuous_with_previous_observation",
    )
    response = _attach_photo(slice_context, slice_context.selected_observation, "unknown", "unknown.jpg")
    assert response.status_code == 202


@when("the Beekeeper tries to attach a side A photo")
def try_side_a_after_unknown(slice_context: SliceContext) -> None:
    assert slice_context.selected_observation
    _attach_photo(slice_context, slice_context.selected_observation, "side_a", "side-a.jpg")


@given("a Varroa Assessment Inspection has brood slot observations")
def inspection_has_brood_observations(slice_context: SliceContext) -> None:
    _bootstrap_hive(slice_context, brood_slot_count=10)
    _create_inspection(slice_context)


@when("the Beekeeper marks an active brood slot skipped")
def beekeeper_marks_slot_skipped(slice_context: SliceContext) -> None:
    observation = _observation_for_slot(slice_context, 4)
    slice_context.selected_observation = _patch_observation(
        slice_context,
        observation,
        observation_status="skipped",
    )


@then("HiveSight shows the observation as skipped")
def observation_is_skipped(slice_context: SliceContext) -> None:
    assert slice_context.selected_observation
    assert slice_context.selected_observation["observation_status"] == "skipped"


@then("HiveSight shows frame continuity as not continuous or unknown")
def continuity_is_broken(slice_context: SliceContext) -> None:
    assert slice_context.selected_observation
    assert slice_context.selected_observation["continuity_status"] == "not_continuous_or_unknown"


@then("HiveSight prevents photos from being attached to that observation")
def current_observation_rejects_photos(slice_context: SliceContext) -> None:
    assert slice_context.selected_observation
    response = _attach_photo(slice_context, slice_context.selected_observation, "side_a", "blocked.jpg")
    assert response.status_code == 409


@when("a historical brood slot is inactive for the current hive brood slot count")
def historical_slot_is_inactive(slice_context: SliceContext) -> None:
    assert slice_context.hive_id
    _configure_hive(slice_context, brood_slot_count=12)
    _create_inspection(slice_context)
    _configure_hive(slice_context, brood_slot_count=10)
    _create_inspection(slice_context)
    slice_context.selected_observation = _observation_for_slot(slice_context, 12)


@then("HiveSight shows the observation as inactive")
def observation_is_inactive(slice_context: SliceContext) -> None:
    assert slice_context.selected_observation
    assert slice_context.selected_observation["observation_status"] == "inactive"


@given("a hive has 12 brood Hive Frame Slots with historical observations")
def hive_has_twelve_slots_with_history(slice_context: SliceContext) -> None:
    _bootstrap_hive(slice_context, brood_slot_count=12)
    _create_inspection(slice_context)


@when("the Beekeeper changes the active brood slot count to 10")
def beekeeper_reduces_slot_count(slice_context: SliceContext) -> None:
    _configure_hive(slice_context, brood_slot_count=10)


@then("HiveSight archives brood slots 11 and 12 for future inspections")
def slots_are_archived(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.hive_id
    response = slice_context.client.get(
        f"/v1/hives/{slice_context.hive_id}/frame-slots?workspace_id={slice_context.workspace_id}",
        headers=_headers(),
    )
    assert response.status_code == 200
    slots = response.json()["hive_frame_slots"]
    assert [slot["status"] for slot in slots if slot["slot_number"] in (11, 12)] == [
        "archived",
        "archived",
    ]


@then("HiveSight keeps their historical observations and photos visible")
def historical_observations_stay_visible(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.inspection_id
    _refresh_observations(slice_context)
    assert _observation_for_slot(slice_context, 11)["observation_status"] == "pending"
    assert _observation_for_slot(slice_context, 12)["observation_status"] == "pending"


@when("the Beekeeper changes the active brood slot count back to 12")
def beekeeper_increases_slot_count(slice_context: SliceContext) -> None:
    _configure_hive(slice_context, brood_slot_count=12)


@then("HiveSight reactivates the same brood slots 11 and 12")
def slots_are_reactivated(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.hive_id
    response = slice_context.client.get(
        f"/v1/hives/{slice_context.hive_id}/frame-slots?workspace_id={slice_context.workspace_id}",
        headers=_headers(),
    )
    assert response.status_code == 200
    slots = response.json()["hive_frame_slots"]
    assert [slot["status"] for slot in slots if slot["slot_number"] in (11, 12)] == [
        "active",
        "active",
    ]


@then("new inspections use those same slot identities")
def new_inspections_use_same_slots(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id and slice_context.inspection_id
    previous = {
        item["hive_frame_slot"]["slot_number"]: item["hive_frame_slot"]["hive_frame_slot_id"]
        for item in slice_context.observations
    }
    _create_inspection(slice_context)
    latest = {
        item["hive_frame_slot"]["slot_number"]: item["hive_frame_slot"]["hive_frame_slot_id"]
        for item in slice_context.observations
    }
    assert latest[11] == previous[11]
    assert latest[12] == previous[12]
