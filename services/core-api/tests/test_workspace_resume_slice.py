from uuid import UUID

from fastapi.testclient import TestClient

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

USER_ID = UUID("00000000-0000-0000-0000-000000000101")
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000202")


def test_workspace_lists_existing_apiaries_and_hives_before_terms_acceptance() -> None:
    state = build_dev_state()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id = _workspace_id(client, USER_ID)
        assert _list_apiaries(client, USER_ID, workspace_id).json() == {"apiaries": []}

        z_apiary_id = _create_apiary(client, USER_ID, workspace_id, "Zulu apiary")
        a_apiary_id = _create_apiary(client, USER_ID, workspace_id, "Alpha apiary")
        _create_hive(client, USER_ID, a_apiary_id, "Hive Z")
        _create_hive(client, USER_ID, a_apiary_id, "Hive A")

        apiary_listing = _list_apiaries(client, USER_ID, workspace_id)
        hive_listing = _list_hives(client, USER_ID, workspace_id, a_apiary_id)
        z_hive_listing = _list_hives(client, USER_ID, workspace_id, z_apiary_id)

        assert apiary_listing.status_code == 200
        assert [apiary["name"] for apiary in apiary_listing.json()["apiaries"]] == [
            "Alpha apiary",
            "Zulu apiary",
        ]
        assert hive_listing.status_code == 200
        assert [hive["name"] for hive in hive_listing.json()["hives"]] == ["Hive A", "Hive Z"]
        assert z_hive_listing.status_code == 200
        assert z_hive_listing.json() == {"hives": []}
    finally:
        app.dependency_overrides.clear()


def test_workspace_list_routes_keep_authorization_and_missing_apiary_boundaries() -> None:
    state = build_dev_state()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id = _workspace_id(client, USER_ID)
        other_workspace_id = _workspace_id(client, OTHER_USER_ID)
        apiary_id = _create_apiary(client, USER_ID, workspace_id, "Private apiary")

        unauthorized_apiaries = _list_apiaries(client, OTHER_USER_ID, workspace_id)
        unauthorized_hives = _list_hives(client, OTHER_USER_ID, other_workspace_id, apiary_id)
        missing_apiary = _list_hives(
            client,
            USER_ID,
            workspace_id,
            "00000000-0000-0000-0000-000000009999",
        )

        assert unauthorized_apiaries.status_code == 403
        assert unauthorized_apiaries.json()["detail"]["code"] == "workspace_access_denied"
        assert unauthorized_hives.status_code == 403
        assert unauthorized_hives.json()["detail"]["code"] == "workspace_access_denied"
        assert missing_apiary.status_code == 404
        assert missing_apiary.json()["detail"]["code"] == "apiary_not_found"
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


def _list_apiaries(client: TestClient, user_id: UUID, workspace_id: str):
    return client.get(
        "/v1/apiaries",
        params={"workspace_id": workspace_id},
        headers=_headers(user_id),
    )


def _list_hives(client: TestClient, user_id: UUID, workspace_id: str, apiary_id: str):
    return client.get(
        f"/v1/apiaries/{apiary_id}/hives",
        params={"workspace_id": workspace_id},
        headers=_headers(user_id),
    )
