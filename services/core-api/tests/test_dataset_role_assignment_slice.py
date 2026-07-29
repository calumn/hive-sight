from datetime import UTC, date, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

CURATOR_USER_ID = UUID("00000000-0000-0000-0000-000000000101")
NON_CURATOR_USER_ID = UUID("00000000-0000-0000-0000-000000000202")


def test_dataset_curator_assigns_reviewed_labelling_session_to_training() -> None:
    state = _build_state()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, labelling_session_id, reviewed_annotation_ids = _create_reviewed_labelling(
            client
        )
        client.patch(
            f"/v1/dataset-labelling-sessions/{labelling_session_id}",
            json={
                "workspace_id": workspace_id,
                "source_group_key": "frame-a-side-1",
                "image_quality_status": "usable",
            },
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )

        response = client.post(
            "/v1/dataset-items",
            json={
                "workspace_id": workspace_id,
                "labelling_session_id": labelling_session_id,
                "dataset_role": "training",
                "assignment_note": "Good enough for the first training pool.",
                "exclusion_reason": None,
            },
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["workspace_id"] == workspace_id
        assert body["labelling_session_id"] == labelling_session_id
        assert body["dataset_role"] == "training"
        assert body["reviewed_annotation_ids"] == reviewed_annotation_ids
        assert body["source_group_key"] == "frame-a-side-1"
        assert body["image_quality_status"] == "usable"
        assert body["assigned_by_user_id"] == str(CURATOR_USER_ID)
        assert body["assignment_note"] == "Good enough for the first training pool."
        assert body["exclusion_reason"] is None
        assert body["benchmark_protected"] is False
        assert len(state.store.dataset_items) == 1
    finally:
        app.dependency_overrides.clear()


def test_benchmark_dataset_item_is_projected_as_protected() -> None:
    state = _build_state()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, labelling_session_id, _ = _create_reviewed_labelling(client)

        response = client.post(
            "/v1/dataset-items",
            json={
                "workspace_id": workspace_id,
                "labelling_session_id": labelling_session_id,
                "dataset_role": "benchmark",
                "assignment_note": "Hold back for honest evaluation.",
                "exclusion_reason": None,
            },
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )
        evidence = client.get(
            f"/v1/dataset-labelling-sessions/{labelling_session_id}/evidence"
            f"?workspace_id={workspace_id}",
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )

        assert response.status_code == 201
        assert response.json()["benchmark_protected"] is True
        assert evidence.status_code == 200
        assert evidence.json()["dataset_item"]["dataset_role"] == "benchmark"
        assert evidence.json()["dataset_item"]["benchmark_protected"] is True
    finally:
        app.dependency_overrides.clear()


def test_dataset_role_assignment_validates_exclusion_reason_and_duplicates() -> None:
    state = _build_state()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, labelling_session_id, _ = _create_reviewed_labelling(client)

        missing_reason = client.post(
            "/v1/dataset-items",
            json={
                "workspace_id": workspace_id,
                "labelling_session_id": labelling_session_id,
                "dataset_role": "excluded",
                "assignment_note": "Bad image.",
                "exclusion_reason": None,
            },
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )
        reason_not_allowed = client.post(
            "/v1/dataset-items",
            json={
                "workspace_id": workspace_id,
                "labelling_session_id": labelling_session_id,
                "dataset_role": "training",
                "assignment_note": "Wrongly carries exclusion reason.",
                "exclusion_reason": "poor_image_quality",
            },
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )
        other_without_note = client.post(
            "/v1/dataset-items",
            json={
                "workspace_id": workspace_id,
                "labelling_session_id": labelling_session_id,
                "dataset_role": "excluded",
                "assignment_note": "",
                "exclusion_reason": "other",
            },
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )
        created = client.post(
            "/v1/dataset-items",
            json={
                "workspace_id": workspace_id,
                "labelling_session_id": labelling_session_id,
                "dataset_role": "excluded",
                "assignment_note": "Other issue noted.",
                "exclusion_reason": "other",
            },
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )
        duplicate = client.post(
            "/v1/dataset-items",
            json={
                "workspace_id": workspace_id,
                "labelling_session_id": labelling_session_id,
                "dataset_role": "validation",
                "assignment_note": None,
                "exclusion_reason": None,
            },
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )

        assert missing_reason.status_code == 422
        assert missing_reason.json()["detail"]["code"] == "exclusion_reason_required"
        assert reason_not_allowed.status_code == 422
        assert reason_not_allowed.json()["detail"]["code"] == "exclusion_reason_not_allowed"
        assert other_without_note.status_code == 422
        assert other_without_note.json()["detail"]["code"] == "assignment_note_required"
        assert created.status_code == 201
        assert created.json()["dataset_role"] == "excluded"
        assert created.json()["exclusion_reason"] == "other"
        assert duplicate.status_code == 409
        assert duplicate.json()["detail"]["code"] == "dataset_item_already_assigned"
    finally:
        app.dependency_overrides.clear()


def test_dataset_role_assignment_requires_curator_and_reviewed_annotations() -> None:
    state = _build_state()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, inspection_photo_id = _upload_inspection_photo(client)
        labelling_session_id = _start_labelling(client, workspace_id, inspection_photo_id)

        no_review_response = client.post(
            "/v1/dataset-items",
            json={
                "workspace_id": workspace_id,
                "labelling_session_id": labelling_session_id,
                "dataset_role": "training",
                "assignment_note": None,
                "exclusion_reason": None,
            },
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )
        state.store.dataset_curator_user_ids.clear()
        no_curator_response = client.post(
            "/v1/dataset-items",
            json={
                "workspace_id": workspace_id,
                "labelling_session_id": labelling_session_id,
                "dataset_role": "training",
                "assignment_note": None,
                "exclusion_reason": None,
            },
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )

        assert no_review_response.status_code == 409
        assert no_review_response.json()["detail"]["code"] == "reviewed_annotations_required"
        assert no_curator_response.status_code == 403
        assert no_curator_response.json()["detail"]["code"] == "dataset_curator_access_required"
    finally:
        app.dependency_overrides.clear()


def _build_state():
    return build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000006001"),
            UUID("00000000-0000-0000-0000-000000006002"),
            UUID("00000000-0000-0000-0000-000000006003"),
            UUID("00000000-0000-0000-0000-000000006004"),
            UUID("00000000-0000-0000-0000-000000006005"),
            UUID("00000000-0000-0000-0000-000000006006"),
            UUID("00000000-0000-0000-0000-000000006007"),
            UUID("00000000-0000-0000-0000-000000006008"),
            UUID("00000000-0000-0000-0000-000000006009"),
            UUID("00000000-0000-0000-0000-000000006010"),
            UUID("00000000-0000-0000-0000-000000006011"),
            UUID("00000000-0000-0000-0000-000000006012"),
        ],
        clock=lambda: datetime(2026, 7, 29, 17, 0, tzinfo=UTC),
    )


def _create_reviewed_labelling(client: TestClient) -> tuple[str, str, list[str]]:
    workspace_id, inspection_photo_id = _upload_inspection_photo(client)
    labelling_session_id = _start_labelling(client, workspace_id, inspection_photo_id)
    evidence = _get_labelling_evidence(client, workspace_id, labelling_session_id)
    annotation_ids = [
        annotation["annotation_id"] for annotation in evidence["draft_annotations"][:1]
    ]
    for annotation_id in annotation_ids:
        response = client.post(
            "/v1/review-decisions",
            json={
                "workspace_id": workspace_id,
                "subject_type": "annotation",
                "subject_id": annotation_id,
                "decision": "approved",
                "notes": "Accepted for dataset labelling evidence.",
            },
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )
        assert response.status_code == 201
    return workspace_id, labelling_session_id, annotation_ids


def _upload_inspection_photo(client: TestClient) -> tuple[str, str]:
    workspace_id = client.get(
        "/v1/dev/session",
        headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
    ).json()["workspace_id"]
    client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": workspace_id, "terms_version": "2026-07-29"},
        headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
    )
    apiary_id = client.post(
        "/v1/apiaries",
        json={"workspace_id": workspace_id, "name": "Home apiary"},
        headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
    ).json()["apiary_id"]
    hive_id = client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": "Hive A"},
        headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
    ).json()["hive_id"]
    inspection_id = client.post(
        "/v1/inspections",
        json={"hive_id": hive_id, "inspection_date": str(date(2026, 7, 29))},
        headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
    ).json()["inspection_id"]
    intake_response = client.post(
        f"/v1/inspection-photos/intake?workspace_id={workspace_id}&inspection_id={inspection_id}",
        content=b"fake-image-bytes",
        headers={
            "content-type": "image/jpeg",
            "x-hivesight-dev-user-id": str(CURATOR_USER_ID),
            "x-hivesight-filename": "frame-1.jpg",
        },
    )
    assert intake_response.status_code == 202
    return workspace_id, intake_response.json()["inspection_photo"]["inspection_photo_id"]


def _start_labelling(client: TestClient, workspace_id: str, inspection_photo_id: str) -> str:
    response = client.post(
        "/v1/dataset-labelling-sessions",
        json={"workspace_id": workspace_id, "inspection_photo_id": inspection_photo_id},
        headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
    )
    assert response.status_code == 201
    return response.json()["labelling_session_id"]


def _get_labelling_evidence(
    client: TestClient,
    workspace_id: str,
    labelling_session_id: str,
) -> dict[str, object]:
    response = client.get(
        f"/v1/dataset-labelling-sessions/{labelling_session_id}/evidence"
        f"?workspace_id={workspace_id}",
        headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
    )
    assert response.status_code == 200
    return response.json()
