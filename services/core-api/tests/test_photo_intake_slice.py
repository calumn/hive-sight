from datetime import UTC, date, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app
from hive_sight_core_api.models import AnalysisRunStatus

USER_ID = UUID("00000000-0000-0000-0000-000000000101")
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000202")


def test_photo_intake_accepts_image_for_authorized_workspace_with_terms() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000000001"),
            UUID("00000000-0000-0000-0000-000000000002"),
            UUID("00000000-0000-0000-0000-000000000003"),
            UUID("00000000-0000-0000-0000-000000000004"),
            UUID("00000000-0000-0000-0000-000000000005"),
        ],
        clock=lambda: datetime(2026, 7, 29, 9, 30, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
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
            json={
                "hive_id": hive_id,
                "inspection_date": str(date(2026, 7, 29)),
                "intent": "varroa_assessment",
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        ).json()["inspection_id"]

        response = client.post(
            f"/v1/inspection-photos/intake?workspace_id={workspace_id}&inspection_id={inspection_id}",
            content=b"fake-image-bytes",
            headers={
                "content-type": "image/jpeg",
                "x-hivesight-dev-user-id": str(USER_ID),
                "x-hivesight-filename": "frame-1.jpg",
            },
        )

        assert response.status_code == 202
        body = response.json()
        assert body["inspection_photo"]["workspace_id"] == workspace_id
        assert body["inspection_photo"]["inspection_id"] == inspection_id
        assert body["inspection_photo"]["filename"] == "frame-1.jpg"
        assert body["inspection_photo"]["content_type"] == "image/jpeg"
        assert body["inspection_photo"]["size_bytes"] == 16
        assert body["inspection_photo"]["upload_status"] == "accepted"
        assert body["analysis_run"]["status"] == AnalysisRunStatus.queued
    finally:
        app.dependency_overrides.clear()


def test_photo_intake_rejects_missing_authentication() -> None:
    state = build_dev_state()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        response = client.post(
            "/v1/inspection-photos/intake"
            "?workspace_id=00000000-0000-0000-0000-000000000001"
            "&inspection_id=00000000-0000-0000-0000-000000000002",
            content=b"fake-image-bytes",
            headers={"content-type": "image/jpeg", "x-hivesight-filename": "frame-1.jpg"},
        )

        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "not_authenticated"
    finally:
        app.dependency_overrides.clear()


def test_photo_intake_rejects_workspace_without_data_use_agreement() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000000011"),
            UUID("00000000-0000-0000-0000-000000000012"),
            UUID("00000000-0000-0000-0000-000000000013"),
        ],
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id = client.get(
            "/v1/dev/session",
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        ).json()["workspace_id"]
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
            json={
                "hive_id": hive_id,
                "inspection_date": str(date(2026, 7, 29)),
                "intent": "varroa_assessment",
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        ).json()["inspection_id"]

        response = client.post(
            f"/v1/inspection-photos/intake?workspace_id={workspace_id}&inspection_id={inspection_id}",
            content=b"fake-image-bytes",
            headers={
                "content-type": "image/jpeg",
                "x-hivesight-dev-user-id": str(USER_ID),
                "x-hivesight-filename": "frame-1.jpg",
            },
        )

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "data_use_agreement_required"
    finally:
        app.dependency_overrides.clear()


def test_photo_intake_rejects_cross_workspace_access() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000000021"),
            UUID("00000000-0000-0000-0000-000000000022"),
        ],
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id = client.get(
            "/v1/dev/session",
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        ).json()["workspace_id"]

        response = client.post(
            "/v1/apiaries",
            json={"workspace_id": workspace_id, "name": "Intrusion"},
            headers={"x-hivesight-dev-user-id": str(OTHER_USER_ID)},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "workspace_access_denied"
    finally:
        app.dependency_overrides.clear()


def test_photo_intake_rejects_unsupported_content_type_and_large_file() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000000031"),
            UUID("00000000-0000-0000-0000-000000000032"),
            UUID("00000000-0000-0000-0000-000000000033"),
        ],
        max_upload_size_bytes=4,
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
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
            json={
                "hive_id": hive_id,
                "inspection_date": str(date(2026, 7, 29)),
                "intent": "varroa_assessment",
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        ).json()["inspection_id"]

        unsupported_response = client.post(
            f"/v1/inspection-photos/intake?workspace_id={workspace_id}&inspection_id={inspection_id}",
            content=b"gif",
            headers={
                "content-type": "image/gif",
                "x-hivesight-dev-user-id": str(USER_ID),
                "x-hivesight-filename": "frame-1.gif",
            },
        )
        large_response = client.post(
            f"/v1/inspection-photos/intake?workspace_id={workspace_id}&inspection_id={inspection_id}",
            content=b"too-large",
            headers={
                "content-type": "image/jpeg",
                "x-hivesight-dev-user-id": str(USER_ID),
                "x-hivesight-filename": "frame-1.jpg",
            },
        )

        assert unsupported_response.status_code == 415
        assert unsupported_response.json()["detail"]["code"] == "unsupported_content_type"
        assert large_response.status_code == 413
        assert large_response.json()["detail"]["code"] == "file_too_large"
    finally:
        app.dependency_overrides.clear()
