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
        assert body["analysis_result"]["complete_visible_bee_count"] == 3
        assert body["analysis_result"]["partial_visible_bee_count"] == 1
        assert body["analysis_result"]["likely_varroa_detections"] == 0
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


def test_analysis_evidence_returns_original_photo_reference_and_bee_annotations() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000000031"),
            UUID("00000000-0000-0000-0000-000000000032"),
            UUID("00000000-0000-0000-0000-000000000033"),
            UUID("00000000-0000-0000-0000-000000000034"),
            UUID("00000000-0000-0000-0000-000000000035"),
            UUID("00000000-0000-0000-0000-000000000036"),
            UUID("00000000-0000-0000-0000-000000000037"),
            UUID("00000000-0000-0000-0000-000000000038"),
            UUID("00000000-0000-0000-0000-000000000039"),
            UUID("00000000-0000-0000-0000-000000000040"),
        ],
        clock=lambda: datetime(2026, 7, 29, 12, 0, tzinfo=UTC),
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

        response = client.get(
            f"/v1/analysis-runs/{analysis_run_id}/evidence?workspace_id={workspace_id}",
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["analysis_run_id"] == analysis_run_id
        assert body["analysis_result"]["complete_visible_bee_count"] == 3
        assert body["analysis_result"]["partial_visible_bee_count"] == 1
        assert body["analysis_result"]["likely_varroa_detections"] == 0
        assert body["inspection_photo"]["filename"] == "frame-1.jpg"
        assert body["inspection_photo"]["view_url"].startswith("/v1/inspection-photos/")
        assert body["caveat"].startswith("Deterministic stub")
        assert [annotation["annotation_type"] for annotation in body["annotations"]] == [
            "complete_visible_bee",
            "complete_visible_bee",
            "complete_visible_bee",
            "partial_visible_bee",
        ]
        assert len(state.store.annotations) == 4
        assert body["annotations"][0]["coordinate_space"] == "normalized"
        assert body["annotations"][0]["source_image_width_px"] == 1600
        assert body["annotations"][0]["source_image_height_px"] == 1200
        assert body["annotations"][0]["confidence"] == 0.92
    finally:
        app.dependency_overrides.clear()


def test_reviewer_records_review_decision_and_evidence_projects_latest_state() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000000061"),
            UUID("00000000-0000-0000-0000-000000000062"),
            UUID("00000000-0000-0000-0000-000000000063"),
            UUID("00000000-0000-0000-0000-000000000064"),
            UUID("00000000-0000-0000-0000-000000000065"),
            UUID("00000000-0000-0000-0000-000000000066"),
            UUID("00000000-0000-0000-0000-000000000067"),
            UUID("00000000-0000-0000-0000-000000000068"),
            UUID("00000000-0000-0000-0000-000000000069"),
            UUID("00000000-0000-0000-0000-000000000070"),
            UUID("00000000-0000-0000-0000-000000000071"),
            UUID("00000000-0000-0000-0000-000000000072"),
        ],
        clock=lambda: datetime(2026, 7, 29, 12, 30, tzinfo=UTC),
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
        evidence = client.get(
            f"/v1/analysis-runs/{analysis_run_id}/evidence?workspace_id={workspace_id}",
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        ).json()
        annotation_id = evidence["annotations"][0]["annotation_id"]

        approved_response = client.post(
            "/v1/review-decisions",
            json={
                "workspace_id": workspace_id,
                "subject_type": "annotation",
                "subject_id": annotation_id,
                "decision": "approved",
                "notes": "Accepted as a complete visible bee.",
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )
        rejected_response = client.post(
            "/v1/review-decisions",
            json={
                "workspace_id": workspace_id,
                "subject_type": "annotation",
                "subject_id": annotation_id,
                "decision": "rejected",
                "notes": "Changed after closer review.",
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )
        reviewed_evidence_response = client.get(
            f"/v1/analysis-runs/{analysis_run_id}/evidence?workspace_id={workspace_id}",
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )

        assert approved_response.status_code == 201
        assert rejected_response.status_code == 201
        assert len(state.store.review_decisions) == 2
        approved = approved_response.json()
        assert approved["reviewer_id"] == str(USER_ID)
        assert approved["subject_type"] == "annotation"
        assert approved["subject_id"] == annotation_id
        assert approved["decision"] == "approved"
        assert approved["notes"] == "Accepted as a complete visible bee."
        reviewed_evidence = reviewed_evidence_response.json()
        reviewed_annotation = reviewed_evidence["annotations"][0]
        assert reviewed_annotation["latest_review_decision"]["decision"] == "rejected"
        assert reviewed_annotation["latest_review_decision"]["notes"] == "Changed after closer review."
    finally:
        app.dependency_overrides.clear()


def test_review_decision_requires_internal_reviewer_capability() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000000081"),
            UUID("00000000-0000-0000-0000-000000000082"),
            UUID("00000000-0000-0000-0000-000000000083"),
            UUID("00000000-0000-0000-0000-000000000084"),
            UUID("00000000-0000-0000-0000-000000000085"),
            UUID("00000000-0000-0000-0000-000000000086"),
            UUID("00000000-0000-0000-0000-000000000087"),
            UUID("00000000-0000-0000-0000-000000000088"),
            UUID("00000000-0000-0000-0000-000000000089"),
            UUID("00000000-0000-0000-0000-000000000090"),
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
        evidence = client.get(
            f"/v1/analysis-runs/{analysis_run_id}/evidence?workspace_id={workspace_id}",
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        ).json()
        annotation_id = evidence["annotations"][0]["annotation_id"]

        response = client.post(
            "/v1/review-decisions",
            json={
                "workspace_id": workspace_id,
                "subject_type": "annotation",
                "subject_id": annotation_id,
                "decision": "approved",
            },
            headers={"x-hivesight-dev-user-id": str(OTHER_USER_ID)},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "workspace_access_denied"
    finally:
        app.dependency_overrides.clear()


def test_review_decision_rejects_non_reviewer_with_workspace_access() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000000091"),
            UUID("00000000-0000-0000-0000-000000000092"),
            UUID("00000000-0000-0000-0000-000000000093"),
            UUID("00000000-0000-0000-0000-000000000094"),
            UUID("00000000-0000-0000-0000-000000000095"),
            UUID("00000000-0000-0000-0000-000000000096"),
            UUID("00000000-0000-0000-0000-000000000097"),
            UUID("00000000-0000-0000-0000-000000000098"),
            UUID("00000000-0000-0000-0000-000000000099"),
            UUID("00000000-0000-0000-0000-000000000100"),
        ],
    )
    state.store.reviewer_user_ids.clear()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, analysis_run_id = _create_queued_analysis_run(client)
        client.post(
            f"/v1/analysis-runs/{analysis_run_id}/process",
            json={"workspace_id": workspace_id},
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )
        evidence = client.get(
            f"/v1/analysis-runs/{analysis_run_id}/evidence?workspace_id={workspace_id}",
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        ).json()
        annotation_id = evidence["annotations"][0]["annotation_id"]

        response = client.post(
            "/v1/review-decisions",
            json={
                "workspace_id": workspace_id,
                "subject_type": "annotation",
                "subject_id": annotation_id,
                "decision": "approved",
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "reviewer_access_required"
    finally:
        app.dependency_overrides.clear()


def test_review_decision_requires_accepted_workspace_data_use_agreement() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000000111"),
            UUID("00000000-0000-0000-0000-000000000112"),
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
            "/v1/review-decisions",
            json={
                "workspace_id": workspace_id,
                "subject_type": "annotation",
                "subject_id": "00000000-0000-0000-0000-000000000999",
                "decision": "approved",
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "data_use_agreement_required"
    finally:
        app.dependency_overrides.clear()


def test_review_decision_rejects_missing_annotation_and_long_notes() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000000121"),
            UUID("00000000-0000-0000-0000-000000000122"),
        ],
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

        missing_response = client.post(
            "/v1/review-decisions",
            json={
                "workspace_id": workspace_id,
                "subject_type": "annotation",
                "subject_id": "00000000-0000-0000-0000-000000000999",
                "decision": "approved",
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )
        long_notes_response = client.post(
            "/v1/review-decisions",
            json={
                "workspace_id": workspace_id,
                "subject_type": "annotation",
                "subject_id": "00000000-0000-0000-0000-000000000999",
                "decision": "approved",
                "notes": "x" * 501,
            },
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )

        assert missing_response.status_code == 404
        assert missing_response.json()["detail"]["code"] == "annotation_not_found"
        assert long_notes_response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_analysis_evidence_is_not_visible_across_workspaces() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000000041"),
            UUID("00000000-0000-0000-0000-000000000042"),
            UUID("00000000-0000-0000-0000-000000000043"),
            UUID("00000000-0000-0000-0000-000000000044"),
            UUID("00000000-0000-0000-0000-000000000045"),
            UUID("00000000-0000-0000-0000-000000000046"),
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

        response = client.get(
            f"/v1/analysis-runs/{analysis_run_id}/evidence?workspace_id={workspace_id}",
            headers={"x-hivesight-dev-user-id": str(OTHER_USER_ID)},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "workspace_access_denied"
    finally:
        app.dependency_overrides.clear()


def test_original_photo_content_requires_workspace_access() -> None:
    state = build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000000051"),
            UUID("00000000-0000-0000-0000-000000000052"),
            UUID("00000000-0000-0000-0000-000000000053"),
            UUID("00000000-0000-0000-0000-000000000054"),
            UUID("00000000-0000-0000-0000-000000000055"),
            UUID("00000000-0000-0000-0000-000000000056"),
        ],
    )
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id, analysis_run_id = _create_queued_analysis_run(client)
        analysis_run = state.store.get_analysis_run(UUID(analysis_run_id))
        assert analysis_run is not None

        visible = client.get(
            f"/v1/inspection-photos/{analysis_run.inspection_photo_id}/content"
            f"?workspace_id={workspace_id}",
            headers={"x-hivesight-dev-user-id": str(USER_ID)},
        )
        blocked = client.get(
            f"/v1/inspection-photos/{analysis_run.inspection_photo_id}/content"
            f"?workspace_id={workspace_id}",
            headers={"x-hivesight-dev-user-id": str(OTHER_USER_ID)},
        )

        assert visible.status_code == 200
        assert visible.content == b"fake-image-bytes"
        assert visible.headers["content-type"] == "image/jpeg"
        assert blocked.status_code == 403
        assert blocked.json()["detail"]["code"] == "workspace_access_denied"
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
