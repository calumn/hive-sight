from fastapi.testclient import TestClient

from beehive_core_api.main import app


def test_healthz_returns_core_api_boundary() -> None:
    client = TestClient(app)

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "service": "core-api",
        "status": "ok",
        "boundary": "internet-reachable protected API",
    }

