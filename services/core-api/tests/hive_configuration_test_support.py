from uuid import UUID

from fastapi.testclient import TestClient


def configure_hive(
    client: TestClient,
    *,
    workspace_id: str,
    hive_id: str,
    user_id: UUID | None = None,
    headers: dict[str, str] | None = None,
    frame_standard_id: str = "british_national_deep_brood",
    notes: str | None = None,
) -> dict[str, object]:
    if headers is None:
        assert user_id is not None
        headers = {"x-hivesight-dev-user-id": str(user_id)}
    response = client.put(
        f"/v1/hives/{hive_id}/configuration",
        json={
            "workspace_id": workspace_id,
            "frame_standard_id": frame_standard_id,
            "notes": notes,
        },
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()
