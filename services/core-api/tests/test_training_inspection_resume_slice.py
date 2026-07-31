from datetime import date
from uuid import UUID

from fastapi.testclient import TestClient

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

USER_ID = UUID("00000000-0000-0000-0000-000000000101")
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000202")


def test_hive_training_inspection_list_filters_and_orders_newest_first() -> None:
    state = build_dev_state()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id = _workspace_id(client, USER_ID)
        apiary_id = _create_apiary(client, USER_ID, workspace_id, "Resume apiary")
        hive_id = _create_hive(client, USER_ID, apiary_id, "Resume hive")
        _configure_hive(client, USER_ID, workspace_id, hive_id)
        older_training = _create_inspection(
            client,
            USER_ID,
            hive_id,
            date(2026, 7, 29),
            "training_data_collection",
        )
        _create_inspection(client, USER_ID, hive_id, date(2026, 7, 30), "varroa_assessment")
        newer_training = _create_inspection(
            client,
            USER_ID,
            hive_id,
            date(2026, 7, 31),
            "training_data_collection",
        )

        response = client.get(
            f"/v1/hives/{hive_id}/inspections",
            params={"workspace_id": workspace_id, "intent": "training_data_collection"},
            headers=_headers(USER_ID),
        )

        assert response.status_code == 200
        assert [inspection["inspection_id"] for inspection in response.json()["inspections"]] == [
            newer_training,
            older_training,
        ]
        assert {
            inspection["intent"] for inspection in response.json()["inspections"]
        } == {"training_data_collection"}
    finally:
        app.dependency_overrides.clear()


def test_hive_inspection_list_keeps_workspace_boundaries() -> None:
    state = build_dev_state()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id = _workspace_id(client, USER_ID)
        other_workspace_id = _workspace_id(client, OTHER_USER_ID)
        apiary_id = _create_apiary(client, USER_ID, workspace_id, "Private apiary")
        hive_id = _create_hive(client, USER_ID, apiary_id, "Private hive")
        _configure_hive(client, USER_ID, workspace_id, hive_id)

        unauthorized_workspace = client.get(
            f"/v1/hives/{hive_id}/inspections",
            params={"workspace_id": workspace_id, "intent": "training_data_collection"},
            headers=_headers(OTHER_USER_ID),
        )
        cross_workspace_hive = client.get(
            f"/v1/hives/{hive_id}/inspections",
            params={"workspace_id": other_workspace_id, "intent": "training_data_collection"},
            headers=_headers(OTHER_USER_ID),
        )
        missing_hive = client.get(
            "/v1/hives/00000000-0000-0000-0000-000000009999/inspections",
            params={"workspace_id": workspace_id, "intent": "training_data_collection"},
            headers=_headers(USER_ID),
        )

        assert unauthorized_workspace.status_code == 403
        assert unauthorized_workspace.json()["detail"]["code"] == "workspace_access_denied"
        assert cross_workspace_hive.status_code == 403
        assert cross_workspace_hive.json()["detail"]["code"] == "workspace_access_denied"
        assert missing_hive.status_code == 404
        assert missing_hive.json()["detail"]["code"] == "hive_not_found"
    finally:
        app.dependency_overrides.clear()


def _headers(user_id: UUID) -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(user_id)}


def _workspace_id(client: TestClient, user_id: UUID) -> str:
    response = client.get("/v1/dev/session", headers=_headers(user_id))
    assert response.status_code == 200
    return response.json()["workspace_id"]


def _create_apiary(client: TestClient, user_id: UUID, workspace_id: str, name: str) -> str:
    response = client.post(
        "/v1/apiaries",
        json={"workspace_id": workspace_id, "name": name},
        headers=_headers(user_id),
    )
    assert response.status_code == 201
    return response.json()["apiary_id"]


def _create_hive(client: TestClient, user_id: UUID, apiary_id: str, name: str) -> str:
    response = client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": name},
        headers=_headers(user_id),
    )
    assert response.status_code == 201
    return response.json()["hive_id"]


def _configure_hive(client: TestClient, user_id: UUID, workspace_id: str, hive_id: str) -> None:
    response = client.put(
        f"/v1/hives/{hive_id}/configuration",
        json={"workspace_id": workspace_id, "frame_standard_id": "british_national_deep_brood"},
        headers=_headers(user_id),
    )
    assert response.status_code == 200


def _create_inspection(
    client: TestClient,
    user_id: UUID,
    hive_id: str,
    inspection_date: date,
    intent: str,
) -> str:
    response = client.post(
        "/v1/inspections",
        json={
            "hive_id": hive_id,
            "inspection_date": str(inspection_date),
            "intent": intent,
        },
        headers=_headers(user_id),
    )
    assert response.status_code == 201
    return response.json()["inspection_id"]
