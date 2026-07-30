from datetime import UTC, date, datetime
from uuid import UUID

from fastapi.testclient import TestClient
from hive_configuration_test_support import configure_hive

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

USER_ID = UUID("00000000-0000-0000-0000-000000000101")


def test_inspection_creation_requires_valid_intent() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000008001"),
            UUID("00000000-0000-0000-0000-000000008002"),
            UUID("00000000-0000-0000-0000-000000008003"),
        ],
        clock=lambda: datetime(2026, 7, 29, 18, 0, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, hive_id = _create_hive_context(client)

        missing_intent = client.post(
            "/v1/inspections",
            json={"hive_id": hive_id, "inspection_date": str(date(2026, 7, 29))},
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )
        unknown_intent = client.post(
            "/v1/inspections",
            json={
                "hive_id": hive_id,
                "inspection_date": str(date(2026, 7, 29)),
                "intent": "mixed_workflow",
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )
        valid = client.post(
            "/v1/inspections",
            json={
                "hive_id": hive_id,
                "inspection_date": str(date(2026, 7, 29)),
                "intent": "training_data_collection",
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )

        assert workspace_id
        assert missing_intent.status_code == 422
        assert unknown_intent.status_code == 422
        assert valid.status_code == 201
        assert valid.json()["intent"] == "training_data_collection"
    finally:
        app.dependency_overrides.clear()


def test_inspection_intent_can_change_only_before_photo_upload() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000008011"),
            UUID("00000000-0000-0000-0000-000000008012"),
            UUID("00000000-0000-0000-0000-000000008013"),
            UUID("00000000-0000-0000-0000-000000008014"),
        ],
        clock=lambda: datetime(2026, 7, 29, 18, 5, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, hive_id = _create_hive_context(client, accept_terms=True)
        inspection_id = _create_inspection(client, hive_id, intent="varroa_assessment")

        updated = client.patch(
            f"/v1/inspections/{inspection_id}/intent",
            json={"workspace_id": workspace_id, "intent": "training_data_collection"},
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )
        upload = _upload_photo(client, workspace_id, inspection_id, filename="frame-a.jpg")
        locked = client.patch(
            f"/v1/inspections/{inspection_id}/intent",
            json={"workspace_id": workspace_id, "intent": "varroa_assessment"},
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )

        assert updated.status_code == 200
        assert updated.json()["intent"] == "training_data_collection"
        assert upload.status_code == 202
        assert locked.status_code == 409
        assert locked.json()["detail"]["code"] == "inspection_intent_locked"
    finally:
        app.dependency_overrides.clear()


def test_repeated_photo_uploads_are_listed_for_one_inspection() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000008021"),
            UUID("00000000-0000-0000-0000-000000008022"),
            UUID("00000000-0000-0000-0000-000000008023"),
            UUID("00000000-0000-0000-0000-000000008024"),
        ],
        clock=lambda: datetime(2026, 7, 29, 18, 10, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, hive_id = _create_hive_context(client, accept_terms=True)
        inspection_id = _create_inspection(client, hive_id, intent="varroa_assessment")

        first = _upload_photo(client, workspace_id, inspection_id, filename="frame-a.jpg")
        second = _upload_photo(client, workspace_id, inspection_id, filename="frame-b.jpg")
        listing = client.get(
            f"/v1/inspections/{inspection_id}/photos?workspace_id={workspace_id}",
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )

        assert first.status_code == 202
        assert second.status_code == 202
        assert listing.status_code == 200
        body = listing.json()
        assert body["inspection"]["intent"] == "varroa_assessment"
        assert [photo["filename"] for photo in body["photos"]] == [
            "frame-a.jpg",
            "frame-b.jpg",
        ]
        assert all(photo["upload_status"] == "accepted" for photo in body["photos"])
    finally:
        app.dependency_overrides.clear()


def test_dataset_labelling_requires_training_data_collection_intent() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000008031"),
            UUID("00000000-0000-0000-0000-000000008032"),
            UUID("00000000-0000-0000-0000-000000008033"),
            UUID("00000000-0000-0000-0000-000000008034"),
        ],
        clock=lambda: datetime(2026, 7, 29, 18, 15, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, hive_id = _create_hive_context(client, accept_terms=True)
        inspection_id = _create_inspection(client, hive_id, intent="varroa_assessment")
        intake = _upload_photo(client, workspace_id, inspection_id, filename="assessment.jpg")
        inspection_photo_id = intake.json()["inspection_photo"]["inspection_photo_id"]

        response = client.post(
            "/v1/dataset-labelling-sessions",
            json={"workspace_id": workspace_id, "inspection_photo_id": inspection_photo_id},
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )

        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "inspection_intent_not_for_dataset_labelling"
    finally:
        app.dependency_overrides.clear()


def _create_hive_context(
    client: TestClient,
    accept_terms: bool = False,
) -> tuple[str, str]:
    workspace_id = client.get(
        "/v1/dev/session",
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    ).json()["workspace_id"]
    if accept_terms:
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
    configure_hive(client, workspace_id=workspace_id, hive_id=hive_id, user_id=USER_ID)
    return workspace_id, hive_id


def _create_inspection(client: TestClient, hive_id: str, intent: str) -> str:
    response = client.post(
        "/v1/inspections",
        json={
            "hive_id": hive_id,
            "inspection_date": str(date(2026, 7, 29)),
            "intent": intent,
        },
        headers={"x-hivesight-dev-user-id": str(USER_ID)},
    )
    assert response.status_code == 201
    return response.json()["inspection_id"]


def _upload_photo(
    client: TestClient,
    workspace_id: str,
    inspection_id: str,
    filename: str,
) -> object:
    return client.post(
        f"/v1/inspection-photos/intake?workspace_id={workspace_id}&inspection_id={inspection_id}",
        content=b"fake-image-bytes",
        headers={
            "content-type": "image/jpeg",
            "x-hivesight-dev-user-id": str(USER_ID),
            "x-hivesight-filename": filename,
        },
    )
