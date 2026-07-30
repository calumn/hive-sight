from datetime import UTC, date, datetime
from uuid import UUID

import pytest

from hive_sight_core_api.dependencies import build_dev_state
from hive_sight_core_api.dev_store import DomainError, UserContext
from hive_sight_core_api.hive_configuration_workflow import HiveConfigurationWorkflow
from hive_sight_core_api.models import (
    ApiaryResponse,
    HiveConfigurationUpsertRequest,
    HiveResponse,
    InspectionIntent,
)

USER_ID = UUID("00000000-0000-0000-0000-000000000101")


def test_workflow_requires_notes_for_other_frame_standard() -> None:
    state = _state()
    workflow = HiveConfigurationWorkflow(store=state.store)
    user = UserContext(user_id=USER_ID)
    hive = _hive(state.store.ensure_dev_session(USER_ID).workspace_id)
    state.store.apiaries[hive.apiary_id] = ApiaryResponse(
        apiary_id=hive.apiary_id,
        workspace_id=hive.workspace_id,
        name="Home apiary",
    )
    state.store.hives[hive.hive_id] = hive

    with pytest.raises(DomainError) as exc:
        workflow.upsert_hive_configuration(
            user=user,
            hive_id=hive.hive_id,
            request=HiveConfigurationUpsertRequest(
                workspace_id=hive.workspace_id,
                frame_standard_id="other",
            ),
        )

    assert exc.value.code == "hive_configuration_notes_required"


def test_workflow_blocks_inspection_until_hive_is_configured() -> None:
    state = _state()
    workflow = HiveConfigurationWorkflow(store=state.store)
    user = UserContext(user_id=USER_ID)
    hive = _hive(state.store.ensure_dev_session(USER_ID).workspace_id)
    state.store.apiaries[hive.apiary_id] = ApiaryResponse(
        apiary_id=hive.apiary_id,
        workspace_id=hive.workspace_id,
        name="Home apiary",
    )
    state.store.hives[hive.hive_id] = hive

    with pytest.raises(DomainError) as exc:
        workflow.create_inspection(
            user=user,
            hive_id=hive.hive_id,
            inspection_date=date(2026, 7, 30),
            intent=InspectionIntent.training_data_collection,
        )

    assert exc.value.code == "hive_configuration_required"

    workflow.upsert_hive_configuration(
        user=user,
        hive_id=hive.hive_id,
        request=HiveConfigurationUpsertRequest(
            workspace_id=hive.workspace_id,
            frame_standard_id="british_national_deep_brood",
        ),
    )
    inspection = workflow.create_inspection(
        user=user,
        hive_id=hive.hive_id,
        inspection_date=date(2026, 7, 30),
        intent=InspectionIntent.training_data_collection,
    )

    assert inspection.hive_id == hive.hive_id
    assert inspection.intent == InspectionIntent.training_data_collection


def _state():
    return build_dev_state(
        id_values=[UUID(f"00000000-0000-0000-0000-{index:012d}") for index in range(20001, 20010)],
        clock=lambda: datetime(2026, 7, 30, 15, 0, tzinfo=UTC),
    )


def _hive(workspace_id: UUID) -> HiveResponse:
    return HiveResponse(
        hive_id=UUID("00000000-0000-0000-0000-000000020099"),
        apiary_id=UUID("00000000-0000-0000-0000-000000020098"),
        workspace_id=workspace_id,
        name="Hive A",
    )
