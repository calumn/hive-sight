from dataclasses import replace
from datetime import UTC, date, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from hive_configuration_test_support import configure_hive

from hive_sight_core_api.dataset_labelling_workflow import PrelabellingRequest
from hive_sight_core_api.dependencies import (
    build_bee_prelabeler,
    build_dev_state,
    get_dataset_labelling_workflow,
    get_dev_state,
)
from hive_sight_core_api.grounding_dino_prelabeler import (
    GroundingDinoBeePrelabeler,
    GroundingDinoDetection,
    TransformersGroundingDinoRunner,
    UnavailableGroundingDinoRunner,
)
from hive_sight_core_api.main import app
from hive_sight_core_api.settings import Settings

CURATOR_USER_ID = UUID("00000000-0000-0000-0000-000000000101")


class FakeGroundingDinoRunner:
    def detect(
        self,
        request: PrelabellingRequest,
        prompt_text: str,
        box_threshold: float,
        text_threshold: float,
    ) -> list[GroundingDinoDetection]:
        return [
            GroundingDinoDetection(
                label="honey bee",
                score=0.86,
                x_min_px=160,
                y_min_px=120,
                x_max_px=460,
                y_max_px=370,
            ),
            GroundingDinoDetection(
                label="partial honey bee",
                score=0.71,
                x_min_px=900,
                y_min_px=700,
                x_max_px=1200,
                y_max_px=940,
            ),
            GroundingDinoDetection(
                label="hive tool",
                score=0.93,
                x_min_px=10,
                y_min_px=10,
                x_max_px=50,
                y_max_px=50,
            ),
            GroundingDinoDetection(
                label="honey bee",
                score=0.91,
                x_min_px=0,
                y_min_px=0,
                x_max_px=1500,
                y_max_px=1100,
            ),
        ]


def test_grounding_dino_adapter_maps_fake_runner_output_to_bee_draft_annotations() -> None:
    prelabeler = GroundingDinoBeePrelabeler(
        runner=FakeGroundingDinoRunner(),
        model_id="grounding-dino-test-model",
        checkpoint_id="local/test-checkpoint.pth",
        prompt_text="honey bee . partial honey bee",
        box_threshold=0.35,
        text_threshold=0.25,
    )

    result = prelabeler.create_draft_annotations(
        PrelabellingRequest(
            inspection_photo_id=UUID("00000000-0000-0000-0000-000000007001"),
            original_object_key="inspection-photos/frame-1.jpg",
            image_bytes=b"not-needed-by-fake-runner",
            source_image_width_px=1600,
            source_image_height_px=1200,
        )
    )

    assert result.provider == "grounding_dino"
    assert result.adapter_version == "0.1.0"
    assert result.model_id == "grounding-dino-test-model"
    assert result.checkpoint_id == "local/test-checkpoint.pth"
    assert result.prompt_text == "honey bee . partial honey bee"
    assert result.box_threshold == 0.35
    assert result.text_threshold == 0.25
    assert result.runtime_mode == "local"
    assert [annotation.annotation_type for annotation in result.annotations] == [
        "complete_visible_bee",
        "partial_visible_bee",
    ]
    assert [annotation.source for annotation in result.annotations] == ["ai_assisted_draft"] * 2
    assert [annotation.coordinate_space for annotation in result.annotations] == ["normalized"] * 2
    assert result.annotations[0].x == pytest.approx(0.1)
    assert result.annotations[0].width == pytest.approx(0.1875)
    assert result.annotations[1].confidence == pytest.approx(0.71)


def test_prelabeler_provider_settings_select_deterministic_or_grounding_dino() -> None:
    settings = _settings()

    deterministic = build_bee_prelabeler(settings)
    grounding_dino = build_bee_prelabeler(
        replace(settings, prelabeler="grounding_dino", grounding_dino_checkpoint="local/model.pth")
    )

    assert deterministic.provider == "deterministic"
    assert grounding_dino.provider == "grounding_dino"
    assert grounding_dino.model_id == "grounding-dino-test-model"
    assert grounding_dino.checkpoint_id == "local/model.pth"


def test_unknown_prelabeler_provider_fails_dependency_creation() -> None:
    with pytest.raises(ValueError, match="Unknown HiveSight pre-labeller provider"):
        build_bee_prelabeler(replace(_settings(), prelabeler="mystery_helper"))


def test_real_transformers_runner_requires_image_bytes() -> None:
    runner = TransformersGroundingDinoRunner(
        model_id="IDEA-Research/grounding-dino-tiny",
        local_files_only=True,
    )

    with pytest.raises(RuntimeError, match="Inspection Photo bytes are not available"):
        runner.detect(
            request=PrelabellingRequest(
                inspection_photo_id=UUID("00000000-0000-0000-0000-000000007001"),
                original_object_key="inspection-photos/frame-1.jpg",
                image_bytes=None,
                source_image_width_px=1600,
                source_image_height_px=1200,
            ),
            prompt_text="honey bee . partial honey bee",
            box_threshold=0.35,
            text_threshold=0.25,
        )


def test_grounding_dino_failure_records_prelabel_failed_evidence_without_fallback() -> None:
    state = _build_state()

    def workflow_override():
        return get_dataset_labelling_workflow_with_prelabeler(
            state=state,
            prelabeler=GroundingDinoBeePrelabeler(
                runner=UnavailableGroundingDinoRunner(checkpoint_id=None),
                model_id="grounding-dino-test-model",
                checkpoint_id=None,
            ),
        )

    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_dataset_labelling_workflow] = workflow_override
    client = TestClient(app)

    try:
        workspace_id, inspection_photo_id = _upload_inspection_photo(client)

        response = client.post(
            "/v1/dataset-labelling-sessions",
            json={"workspace_id": workspace_id, "inspection_photo_id": inspection_photo_id},
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )
        body = response.json()
        evidence = client.get(
            f"/v1/dataset-labelling-sessions/{body['labelling_session_id']}/evidence"
            f"?workspace_id={workspace_id}",
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        ).json()

        assert response.status_code == 201
        assert body["status"] == "prelabel_failed"
        assert body["prelabeler_run"]["provider"] == "grounding_dino"
        assert body["prelabeler_run"]["status"] == "failed"
        assert body["prelabeler_run"]["error_code"] == "prelabeler_unavailable"
        assert body["prelabeler_run"]["suggestion_count"] == 0
        assert len(state.store.annotations) == 0
        assert evidence["labelling_session"]["status"] == "prelabel_failed"
        assert evidence["draft_annotations"] == []
        assert evidence["dataset_item"] is None
    finally:
        app.dependency_overrides.clear()


def test_grounding_dino_success_projects_provenance_without_dataset_item_assignment() -> None:
    state = _build_state()

    def workflow_override():
        return get_dataset_labelling_workflow_with_prelabeler(
            state=state,
            prelabeler=GroundingDinoBeePrelabeler(
                runner=FakeGroundingDinoRunner(),
                model_id="grounding-dino-test-model",
                checkpoint_id="local/test-checkpoint.pth",
            ),
        )

    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_dataset_labelling_workflow] = workflow_override
    client = TestClient(app)

    try:
        workspace_id, inspection_photo_id = _upload_inspection_photo(client)

        response = client.post(
            "/v1/dataset-labelling-sessions",
            json={"workspace_id": workspace_id, "inspection_photo_id": inspection_photo_id},
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        )
        body = response.json()
        evidence = client.get(
            f"/v1/dataset-labelling-sessions/{body['labelling_session_id']}/evidence"
            f"?workspace_id={workspace_id}",
            headers={"x-hivesight-dev-user-id": str(CURATOR_USER_ID)},
        ).json()

        assert response.status_code == 201
        assert body["status"] == "draft_ready"
        assert body["prelabeler_run"]["provider"] == "grounding_dino"
        assert body["prelabeler_run"]["model_id"] == "grounding-dino-test-model"
        assert body["prelabeler_run"]["checkpoint_id"] == "local/test-checkpoint.pth"
        assert body["prelabeler_run"]["suggestion_count"] == 2
        assert [annotation["annotation_type"] for annotation in evidence["draft_annotations"]] == [
            "complete_visible_bee",
            "partial_visible_bee",
        ]
        assert evidence["dataset_item"] is None
        assert len(state.store.dataset_items) == 0
    finally:
        app.dependency_overrides.clear()


def get_dataset_labelling_workflow_with_prelabeler(state, prelabeler):
    from hive_sight_core_api.dataset_labelling_workflow import DatasetLabellingWorkflow

    return DatasetLabellingWorkflow(
        store=state.store,
        prelabeler=prelabeler,
        clock=state.store.clock,
    )


def _settings() -> Settings:
    return Settings(
        allowed_origins=["http://localhost:5173"],
        database_url="postgresql://test",
        redis_url="redis://test",
        object_storage_endpoint="http://localhost:9000",
        object_storage_bucket="hive-sight-test",
        prelabeler="deterministic",
        grounding_dino_model_id="grounding-dino-test-model",
        grounding_dino_checkpoint="",
        grounding_dino_prompt="honey bee . partial honey bee",
        grounding_dino_box_threshold=0.35,
        grounding_dino_text_threshold=0.25,
        grounding_dino_max_box_area_ratio=0.04,
        grounding_dino_device="auto",
        grounding_dino_local_files_only=False,
    )


def _build_state():
    return build_dev_state(
        id_values=[
            UUID("00000000-0000-0000-0000-000000007001"),
            UUID("00000000-0000-0000-0000-000000007002"),
            UUID("00000000-0000-0000-0000-000000007003"),
            UUID("00000000-0000-0000-0000-000000007004"),
            UUID("00000000-0000-0000-0000-000000007005"),
            UUID("00000000-0000-0000-0000-000000007006"),
            UUID("00000000-0000-0000-0000-000000007007"),
            UUID("00000000-0000-0000-0000-000000007008"),
        ],
        clock=lambda: datetime(2026, 7, 29, 17, 0, tzinfo=UTC),
    )


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
    configure_hive(client, workspace_id=workspace_id, hive_id=hive_id, user_id=CURATOR_USER_ID)
    inspection_id = client.post(
        "/v1/inspections",
        json={
            "hive_id": hive_id,
            "inspection_date": str(date(2026, 7, 29)),
            "intent": "training_data_collection",
        },
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
