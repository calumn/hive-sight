from datetime import UTC, date, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from hive_sight_core_api.dependencies import build_dev_state, get_dev_state
from hive_sight_core_api.main import app

CURATOR_USER_ID = UUID("00000000-0000-0000-0000-000000000101")
NON_CURATOR_USER_ID = UUID("00000000-0000-0000-0000-000000000202")


def test_dataset_curator_starts_labelling_session_without_analysis_result() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000001001"),
            UUID("00000000-0000-0000-0000-000000001002"),
            UUID("00000000-0000-0000-0000-000000001003"),
            UUID("00000000-0000-0000-0000-000000001004"),
            UUID("00000000-0000-0000-0000-000000001005"),
            UUID("00000000-0000-0000-0000-000000001006"),
            UUID("00000000-0000-0000-0000-000000001007"),
            UUID("00000000-0000-0000-0000-000000001008"),
        ],
        clock=lambda: datetime(2026, 7, 29, 15, 0, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, inspection_photo_id = _upload_inspection_photo(client)

        response = client.post(
            "/v1/dataset-labelling-sessions",
            json={"workspace_id": workspace_id, "inspection_photo_id": inspection_photo_id},
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["workspace_id"] == workspace_id
        assert body["inspection_photo_id"] == inspection_photo_id
        assert body["status"] == "draft_ready"
        assert body["image_quality_status"] == "unassessed"
        assert body["source_group_key"] is None
        assert body["prelabeler_run"]["prelabeler_name"] == "deterministic-bee-prelabeler"
        assert body["prelabeler_run"]["status"] == "succeeded"
        assert len(state.store.annotations) == 2
        assert len(state.store.analysis_results) == 0
    finally:
        app.dependency_overrides.clear()


def test_start_labelling_is_idempotent_and_projects_draft_annotations() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000001011"),
            UUID("00000000-0000-0000-0000-000000001012"),
            UUID("00000000-0000-0000-0000-000000001013"),
            UUID("00000000-0000-0000-0000-000000001014"),
            UUID("00000000-0000-0000-0000-000000001015"),
            UUID("00000000-0000-0000-0000-000000001016"),
            UUID("00000000-0000-0000-0000-000000001017"),
            UUID("00000000-0000-0000-0000-000000001018"),
        ],
        clock=lambda: datetime(2026, 7, 29, 15, 10, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, inspection_photo_id = _upload_inspection_photo(client)

        first = _start_labelling(client, workspace_id, inspection_photo_id)
        second = _start_labelling(client, workspace_id, inspection_photo_id)
        evidence = client.get(
            f"/v1/dataset-labelling-sessions/{first['labelling_session_id']}/evidence"
            f"?workspace_id={workspace_id}",
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )

        assert second["labelling_session_id"] == first["labelling_session_id"]
        assert len(state.store.dataset_labelling_sessions) == 1
        assert len(state.store.annotations) == 2
        assert evidence.status_code == 200
        evidence_body = evidence.json()
        annotations = evidence_body["draft_annotations"]
        assert [annotation["annotation_type"] for annotation in annotations] == [
            "complete_visible_bee",
            "partial_visible_bee",
        ]
        assert all(annotation["workflow_type"] == "dataset_labelling" for annotation in annotations)
        assert all(annotation["labelling_session_id"] == first["labelling_session_id"] for annotation in annotations)
        assert all(annotation["analysis_result_id"] is None for annotation in annotations)
        assert all(0 <= annotation["x"] <= 1 for annotation in annotations)
        assert all(0 < annotation["width"] <= 1 for annotation in annotations)
        assert evidence_body["reviewed_annotations"] == []
    finally:
        app.dependency_overrides.clear()


def test_dataset_labelling_metadata_and_review_projection() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000001021"),
            UUID("00000000-0000-0000-0000-000000001022"),
            UUID("00000000-0000-0000-0000-000000001023"),
            UUID("00000000-0000-0000-0000-000000001024"),
            UUID("00000000-0000-0000-0000-000000001025"),
            UUID("00000000-0000-0000-0000-000000001026"),
            UUID("00000000-0000-0000-0000-000000001027"),
            UUID("00000000-0000-0000-0000-000000001028"),
            UUID("00000000-0000-0000-0000-000000001029"),
            UUID("00000000-0000-0000-0000-000000001030"),
        ],
        clock=lambda: datetime(2026, 7, 29, 15, 20, tzinfo=UTC),
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, inspection_photo_id = _upload_inspection_photo(client)
        session = _start_labelling(client, workspace_id, inspection_photo_id)
        evidence = _get_labelling_evidence(client, workspace_id, session["labelling_session_id"])
        complete_annotation_id = evidence["draft_annotations"][0]["annotation_id"]
        partial_annotation_id = evidence["draft_annotations"][1]["annotation_id"]

        metadata_response = client.patch(
            f"/v1/dataset-labelling-sessions/{session['labelling_session_id']}",
            json={
                "workspace_id": workspace_id,
                "source_group_key": "frame-a-side-1",
                "image_quality_status": "exclude",
            },
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )
        complete_review = _approve_annotation(client, workspace_id, complete_annotation_id)
        partial_review = _approve_annotation(client, workspace_id, partial_annotation_id)
        reviewed_evidence = _get_labelling_evidence(
            client, workspace_id, session["labelling_session_id"]
        )

        assert metadata_response.status_code == 200
        metadata = metadata_response.json()
        assert metadata["source_group_key"] == "frame-a-side-1"
        assert metadata["image_quality_status"] == "exclude"
        assert complete_review["decision"] == "approved"
        assert partial_review["decision"] == "approved"
        assert reviewed_evidence["labelling_session"]["status"] == "review_in_progress"
        assert reviewed_evidence["labelling_session"]["source_group_key"] == "frame-a-side-1"
        assert reviewed_evidence["labelling_session"]["image_quality_status"] == "exclude"
        assert [annotation["annotation_id"] for annotation in reviewed_evidence["reviewed_annotations"]] == [
            complete_annotation_id,
            partial_annotation_id,
        ]
        assert "dataset_role" not in reviewed_evidence
    finally:
        app.dependency_overrides.clear()


def test_dataset_curator_capability_is_required_for_labelling() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000001031"),
            UUID("00000000-0000-0000-0000-000000001032"),
            UUID("00000000-0000-0000-0000-000000001033"),
            UUID("00000000-0000-0000-0000-000000001034"),
            UUID("00000000-0000-0000-0000-000000001035"),
        ],
    )
    state.store.dataset_curator_user_ids.clear()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, inspection_photo_id = _upload_inspection_photo(client)

        response = client.post(
            "/v1/dataset-labelling-sessions",
            json={"workspace_id": workspace_id, "inspection_photo_id": inspection_photo_id},
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "dataset_curator_access_required"
    finally:
        app.dependency_overrides.clear()


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


def _start_labelling(
    client: TestClient,
    workspace_id: str,
    inspection_photo_id: str,
) -> dict[str, object]:
    response = client.post(
        "/v1/dataset-labelling-sessions",
        json={"workspace_id": workspace_id, "inspection_photo_id": inspection_photo_id},
        headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
    )
    assert response.status_code in {200, 201}
    return response.json()


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


def _approve_annotation(
    client: TestClient,
    workspace_id: str,
    annotation_id: str,
) -> dict[str, object]:
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
    return response.json()
