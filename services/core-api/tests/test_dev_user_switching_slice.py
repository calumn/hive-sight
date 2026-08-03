from uuid import UUID

from fastapi.testclient import TestClient

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.dev_users import DEFAULT_DEV_USER_ID, DEV_USERS
from hive_sight_core_api.main import app


def test_dev_users_are_listed_with_stable_workspace_context_when_enabled() -> None:
    state = build_dev_state(dev_users_enabled=True)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        response = client.get("/v1/dev/users")

        assert response.status_code == 200
        dev_users = response.json()["dev_users"]
        assert [dev_user["dev_user_code"] for dev_user in dev_users] == [
            seed.code for seed in DEV_USERS
        ]
        default_user = next(dev_user for dev_user in dev_users if dev_user["is_default"])
        assert default_user["user_id"] == str(DEFAULT_DEV_USER_ID)
        assert default_user["dataset_curator_capability"] is True
        assert default_user["reviewer_capability"] is True
    finally:
        app.dependency_overrides.clear()


def test_dev_session_rejects_unknown_user_when_dev_users_are_enabled() -> None:
    state = build_dev_state(dev_users_enabled=True)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        response = client.get(
            "/v1/dev/session",
            headers={
                "x-hivesight-dev-user-id": "00000000-0000-0000-0000-000000009999"
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "not_authenticated"
    finally:
        app.dependency_overrides.clear()


def test_seeded_dev_users_have_separate_default_workspaces() -> None:
    state = build_dev_state(dev_users_enabled=True)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        owner_a = _session(client, UUID("00000000-0000-0000-0000-000000000102"))
        owner_b = _session(client, UUID("00000000-0000-0000-0000-000000000103"))

        assert owner_a["workspace_id"] != owner_b["workspace_id"]
        owner_a_apiaries = client.get(
            "/v1/apiaries",
            params={"workspace_id": owner_a["workspace_id"]},
            headers=_headers(UUID(owner_a["user_id"])),
        )
        owner_b_apiaries = client.get(
            "/v1/apiaries",
            params={"workspace_id": owner_b["workspace_id"]},
            headers=_headers(UUID(owner_b["user_id"])),
        )
        owner_b_accessing_owner_a = client.get(
            "/v1/apiaries",
            params={"workspace_id": owner_a["workspace_id"]},
            headers=_headers(UUID(owner_b["user_id"])),
        )

        assert owner_a_apiaries.status_code == 200
        assert [apiary["name"] for apiary in owner_a_apiaries.json()["apiaries"]] == [
            "Owner A Apiary"
        ]
        assert owner_b_apiaries.status_code == 200
        assert [apiary["name"] for apiary in owner_b_apiaries.json()["apiaries"]] == [
            "Owner B Apiary"
        ]
        assert owner_b_accessing_owner_a.status_code == 403
        assert owner_b_accessing_owner_a.json()["detail"]["code"] == "workspace_access_denied"
    finally:
        app.dependency_overrides.clear()


def test_dev_user_endpoint_is_unavailable_when_disabled() -> None:
    state = build_dev_state(dev_users_enabled=False)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        response = client.get("/v1/dev/users")

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "dev_users_disabled"
    finally:
        app.dependency_overrides.clear()


def _session(client: TestClient, user_id: UUID):
    response = client.get("/v1/dev/session", headers=_headers(user_id))
    assert response.status_code == 200
    return response.json()


def _headers(user_id: UUID) -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(user_id)}
