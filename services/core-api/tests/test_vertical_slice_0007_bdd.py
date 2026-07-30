from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from hive_configuration_test_support import configure_hive
from pytest_bdd import given, scenarios, then, when

from hive_sight_core_api.dataset_labelling_workflow import (
    DatasetLabellingWorkflow,
    PrelabellingRequest,
)
from hive_sight_core_api.dependencies import (
    build_dev_state,
    get_dataset_labelling_workflow,
    get_dev_state,
)
from hive_sight_core_api.dev_store import DevState
from hive_sight_core_api.grounding_dino_prelabeler import (
    GroundingDinoBeePrelabeler,
    GroundingDinoDetection,
    UnavailableGroundingDinoRunner,
)
from hive_sight_core_api.main import app

FEATURES_DIR = Path(__file__).parent / "features"
CURATOR_USER_ID = UUID("00000000-0000-0000-0000-000000000101")

scenarios(str(FEATURES_DIR / "vertical_slice_0007_grounding_dino_pre_labelling_adapter.feature"))


@dataclass
class SliceContext:
    client: TestClient
    state: DevState
    workspace_id: str | None = None
    inspection_photo_id: str | None = None
    labelling_session_id: str | None = None
    evidence: dict[str, object] | None = None


class FakeGroundingDinoRunner:
    def detect(
        self,
        request: PrelabellingRequest,
        prompt_text: str,
        box_threshold: float,
        text_threshold: float,
    ) -> list[GroundingDinoDetection]:
        return [
            GroundingDinoDetection(
                label="honey bee",
                score=0.88,
                x_min_px=160,
                y_min_px=120,
                x_max_px=460,
                y_max_px=370,
            )
        ]


@pytest.fixture
def slice_context() -> SliceContext:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000007101"),
            UUID("00000000-0000-0000-0000-000000007102"),
            UUID("00000000-0000-0000-0000-000000007103"),
            UUID("00000000-0000-0000-0000-000000007104"),
            UUID("00000000-0000-0000-0000-000000007105"),
            UUID("00000000-0000-0000-0000-000000007106"),
            UUID("00000000-0000-0000-0000-000000007107"),
            UUID("00000000-0000-0000-0000-000000007108"),
        ],
        clock=lambda: datetime(2026, 7, 29, 17, 30, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    try:
        yield SliceContext(client=TestClient(app), state=state)
    finally:
        app.dependency_overrides.clear()


@given("the User is logged in with dataset curator capability for Grounding DINO labelling")
def user_is_logged_in(slice_context: SliceContext) -> None:
    response = slice_context.client.get(
        "/v1/dev/session",
        headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
    )
    assert response.status_code == 200
    slice_context.workspace_id = response.json()["workspace_id"]


@given(
    "the Workspace has accepted the Workspace Data Use Agreement for Grounding DINO labelling"
)
def workspace_has_accepted_data_use_agreement(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    response = slice_context.client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": slice_context.workspace_id, "terms_version": "2026-07-29"},
        headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
    )
    assert response.status_code == 200


@given("the Beekeeper has uploaded an Inspection Photo for Grounding DINO labelling")
def beekeeper_has_uploaded_photo(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    apiary_id = slice_context.client.post(
        "/v1/apiaries",
        json={"workspace_id": slice_context.workspace_id, "name": "Home apiary"},
        headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
    ).json()["apiary_id"]
    hive_id = slice_context.client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": "Hive A"},
        headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
    ).json()["hive_id"]
    configure_hive(
        slice_context.client,
        workspace_id=slice_context.workspace_id,
        hive_id=hive_id,
        user_id=CURATOR_USER_ID,
    )
    inspection_id = slice_context.client.post(
        "/v1/inspections",
        json={
            "hive_id": hive_id,
            "inspection_date": str(date(2026, 7, 29)),
            "intent": "training_data_collection",
        },
        headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
    ).json()["inspection_id"]
    intake = slice_context.client.post(
        "/v1/inspection-photos/intake"
        f"?workspace_id={slice_context.workspace_id}&inspection_id={inspection_id}",
        content=b"fake-image-bytes",
        headers={
            "content-type": "image/jpeg",
            "x-hivesight-dev-user-id": str(CURATOR_USER_ID),
            "x-hivesight-filename": "frame-1.jpg",
        },
    )
    assert intake.status_code == 202
    slice_context.inspection_photo_id = intake.json()["inspection_photo"][
        "inspection_photo_id"
    ]


@when("the Dataset Curator starts labelling with a fake Grounding DINO helper")
def starts_labelling_with_fake_grounding_dino(slice_context: SliceContext) -> None:
    _override_prelabeler(
        slice_context,
        GroundingDinoBeePrelabeler(
            runner=FakeGroundingDinoRunner(),
            model_id="grounding-dino-bdd-model",
            checkpoint_id="local/bdd-checkpoint.pth",
        ),
    )
    _start_labelling(slice_context)


@when("the Dataset Curator starts labelling with an unavailable Grounding DINO helper")
def starts_labelling_with_unavailable_grounding_dino(slice_context: SliceContext) -> None:
    _override_prelabeler(
        slice_context,
        GroundingDinoBeePrelabeler(
            runner=UnavailableGroundingDinoRunner(checkpoint_id=None),
            model_id="grounding-dino-bdd-model",
            checkpoint_id=None,
        ),
    )
    _start_labelling(slice_context)


@then("the Core API shows Grounding DINO pre-labeller provenance")
def core_api_shows_grounding_dino_provenance(slice_context: SliceContext) -> None:
    evidence = _evidence(slice_context)
    run = evidence["labelling_session"]["prelabeler_run"]
    assert run["provider"] == "grounding_dino"
    assert run["model_id"] == "grounding-dino-bdd-model"
    assert run["checkpoint_id"] == "local/bdd-checkpoint.pth"
    assert run["prompt_text"] == "honey bee . partial honey bee"
    assert run["runtime_mode"] == "local"
    assert run["suggestion_count"] == 1


@then("the helper suggestions remain Draft Annotations requiring review")
def suggestions_remain_draft_annotations(slice_context: SliceContext) -> None:
    evidence = _evidence(slice_context)
    assert len(evidence["draft_annotations"]) == 1
    assert evidence["draft_annotations"][0]["workflow_type"] == "dataset_labelling"
    assert evidence["draft_annotations"][0]["source"] == "ai_assisted_draft"
    assert evidence["reviewed_annotations"] == []


@then("no Dataset Item is assigned by pre-labelling")
def no_dataset_item_assigned(slice_context: SliceContext) -> None:
    evidence = _evidence(slice_context)
    assert evidence["dataset_item"] is None
    assert len(slice_context.state.store.dataset_items) == 0


@then("the Core API records pre-labelling failure evidence")
def core_api_records_failure_evidence(slice_context: SliceContext) -> None:
    evidence = _evidence(slice_context)
    run = evidence["labelling_session"]["prelabeler_run"]
    assert evidence["labelling_session"]["status"] == "prelabel_failed"
    assert run["provider"] == "grounding_dino"
    assert run["status"] == "failed"
    assert run["error_code"] == "prelabeler_unavailable"
    assert run["suggestion_count"] == 0


@then("no Draft Annotations or Dataset Items are created")
def no_drafts_or_dataset_items_created(slice_context: SliceContext) -> None:
    evidence = _evidence(slice_context)
    assert evidence["draft_annotations"] == []
    assert evidence["dataset_item"] is None
    assert len(slice_context.state.store.dataset_items) == 0


def _override_prelabeler(slice_context: SliceContext, prelabeler) -> None:
    app.dependency_overrides[get_dataset_labelling_workflow] = lambda: DatasetLabellingWorkflow(
        store=slice_context.state.store,
        prelabeler=prelabeler,
        clock=slice_context.state.store.clock,
    )


def _start_labelling(slice_context: SliceContext) -> None:
    assert slice_context.workspace_id is not None
    assert slice_context.inspection_photo_id is not None
    response = slice_context.client.post(
        "/v1/dataset-labelling-sessions",
        json={
            "workspace_id": slice_context.workspace_id,
            "inspection_photo_id": slice_context.inspection_photo_id,
        },
        headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
    )
    assert response.status_code == 201
    slice_context.labelling_session_id = response.json()["labelling_session_id"]


def _evidence(slice_context: SliceContext) -> dict[str, object]:
    if slice_context.evidence is not None:
        return slice_context.evidence
    assert slice_context.workspace_id is not None
    assert slice_context.labelling_session_id is not None
    response = slice_context.client.get(
        f"/v1/dataset-labelling-sessions/{slice_context.labelling_session_id}/evidence"
        f"?workspace_id={slice_context.workspace_id}",
        headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
    )
    assert response.status_code == 200
    slice_context.evidence = response.json()
    return slice_context.evidence
