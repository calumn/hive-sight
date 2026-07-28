from fastapi.testclient import TestClient

from beehive_analysis_service.main import app


def test_healthz_returns_analysis_service_boundary() -> None:
    client = TestClient(app)

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "service": "analysis-service",
        "status": "ok",
        "boundary": "private service",
    }

