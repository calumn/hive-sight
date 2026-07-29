from datetime import UTC, date, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

USER_ID = UUID("00000000-0000-0000-0000-000000000101")
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000202")


def test_process_queued_analysis_completes_stub_result_through_core_api() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000000001"),
            UUID("00000000-0000-0000-0000-000000000002"),
            UUID("00000000-0000-0000-0000-000000000003"),
            UUID("00000000-0000-0000-0000-000000000004"),
            UUID("00000000-0000-0000-0000-000000000005"),
            UUID("00000000-0000-0000-0000-000000000006"),
        ],
        clock=lambda: datetime(2026, 7, 29, 10, 45, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, analysis_run_id = _create_queued_analysis_run(client)

        response = client.post(
            f"/v1/analysis-runs/{analysis_run_id}/process",
            json={"workspace_id": workspace_id},
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )

        assert response.status_code == 202
        body = response.json()
        assert body["workspace_id"] == workspace_id
        assert body["analysis_run_id"] == analysis_run_id
        assert body["status"] == "completed"
        assert body["analysis_result"]["result_kind"] == "deterministic_stub"
        assert body["analysis_result"]["model_version"] == "stub-varroa-detector-0.1.0"
        assert body["analysis_result"]["complete_visible_bee_count"] == 48
        assert body["analysis_result"]["partial_visible_bee_count"] == 3
        assert body["analysis_result"]["likely_varroa_detections"] == 1
        assert "stub" in body["message"].lower()
    finally:
        app.dependency_overrides.clear()


def test_analysis_result_detail_is_not_visible_across_workspaces() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000000011"),
            UUID("00000000-0000-0000-0000-000000000012"),
            UUID("00000000-0000-0000-0000-000000000013"),
            UUID("00000000-0000-0000-0000-000000000014"),
            UUID("00000000-0000-0000-0000-000000000015"),
        ],
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, analysis_run_id = _create_queued_analysis_run(client)

        response = client.post(
            f"/v1/analysis-runs/{analysis_run_id}/process",
            json={"workspace_id": workspace_id},
            headers={"x-hivesight-dev-user-id": str(OTHER_USER_ID)},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "workspace_access_denied"
    finally:
        app.dependency_overrides.clear()


def test_processing_completed_analysis_run_is_rejected_with_stable_code() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000000021"),
            UUID("00000000-0000-0000-0000-000000000022"),
            UUID("00000000-0000-0000-0000-000000000023"),
            UUID("00000000-0000-0000-0000-000000000024"),
            UUID("00000000-0000-0000-0000-000000000025"),
            UUID("00000000-0000-0000-0000-000000000026"),
        ],
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, analysis_run_id = _create_queued_analysis_run(client)
        client.post(
            f"/v1/analysis-runs/{analysis_run_id}/process",
            json={"workspace_id": workspace_id},
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )

        response = client.post(
            f"/v1/analysis-runs/{analysis_run_id}/process",
            json={"workspace_id": workspace_id},
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )

        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "analysis_run_not_queued"
    finally:
        app.dependency_overrides.clear()


def _create_queued_analysis_run(client: TestClient) -> tuple[str, str]:
    workspace_id = client.get(
        "/v1/dev/session",
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    ).json()["workspace_id"]
    client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": workspace_id, "terms_version": "2026-07-29"},
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    )
    apiary_id = client.post(
        "/v1/apiaries",
        json={"workspace_id": workspace_id, "name": "Home apiary"},
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    ).json()["apiary_id"]
    hive_id = client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": "Hive A"},
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    ).json()["hive_id"]
    inspection_id = client.post(
        "/v1/inspections",
        json={"hive_id": hive_id, "inspection_date": str(date(2026, 7, 29))},
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    ).json()["inspection_id"]
    intake = client.post(
        f"/v1/inspection-photos/intake?workspace_id={workspace_id}&inspection_id={inspection_id}",
        content=b"fake-image-bytes",
        headers={
            "content-type": "image/jpeg",
            "x-hivesight-dev-user-id": str(USER_ID),
            "x-hivesight-filename": "frame-1.jpg",
        },
    ).json()
    return workspace_id, intake["analysis_run"]["analysis_run_id"]
