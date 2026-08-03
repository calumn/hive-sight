import importlib.util
import os
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from hive_configuration_test_support import configure_hive

from hive_sight_core_api.db import MIGRATIONS_DIR, reset_database
from hive_sight_core_api.dependencies import get_dev_state
from hive_sight_core_api.dev_store import (
    DomainError,
    FileSystemObjectStorage,
    InMemoryEventRecorder,
    InMemoryObjectStorage,
    UploadPolicy,
    UserContext,
)
from hive_sight_core_api.dev_users import DEV_USERS
from hive_sight_core_api.main import app
from hive_sight_core_api.models import (
    ArtifactResponse,
    BenchmarkEvaluationResponse,
    DatasetVersionResponse,
    ModelCandidateResponse,
    TrainingRunResponse,
)
from hive_sight_core_api.postgres_store import PostgresProductDataStore

USER_ID = UUID("00000000-0000-0000-0000-000000000101")


def test_slice_0014_migration_declares_durable_annotation_repository_shape() -> None:
    migration = (MIGRATIONS_DIR / "0014_postgres_bee_annotation_repository.sql").read_text(
        encoding="utf-8"
    )

    for table_name in [
        "source_images",
        "inspection_photos",
        "training_crops",
        "oriented_bee_ellipses",
        "dataset_items",
        "hive_configurations",
        "repository_records",
    ]:
        assert f"CREATE TABLE IF NOT EXISTS {table_name}" in migration

    assert "human_readable_id text NOT NULL UNIQUE" in migration
    assert "source_image_id uuid NOT NULL REFERENCES source_images(id)" in migration
    assert "content_hash text NOT NULL" in migration
    assert "content_hash_algorithm text NOT NULL" in migration
    assert "metadata_minimisation_status text NOT NULL" in migration
    assert "dataset_role <> 'benchmark' OR source_group_key IS NOT NULL" in migration
    assert "benchmark_source_group_guard" in migration
    assert "raw_exif" not in migration.casefold()


@pytest.mark.skipif(
    importlib.util.find_spec("psycopg") is None or not os.getenv("HIVESIGHT_TEST_DATABASE_URL"),
    reason="Set HIVESIGHT_TEST_DATABASE_URL and install psycopg to run Postgres persistence integration.",
)
def test_postgres_store_survives_restart_for_training_crop_dataset_item_path() -> None:
    database_url = os.environ["HIVESIGHT_TEST_DATABASE_URL"]
    reset_database(database_url)
    object_storage_root = Path("/tmp/hive-sight-test-object-storage")
    state = _build_postgres_state(database_url, object_storage_root=object_storage_root)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id = client.get("/v1/dev/session", headers=_headers()).json()["workspace_id"]
        terms = client.post(
            "/v1/workspace-data-use-agreements/acceptances",
            json={"workspace_id": workspace_id, "terms_version": "2026-07-31"},
            headers=_headers(),
        )
        assert terms.status_code == 200
        apiary_id = client.post(
            "/v1/apiaries",
            json={"workspace_id": workspace_id, "name": "Persistence apiary"},
            headers=_headers(),
        ).json()["apiary_id"]
        hive_id = client.post(
            "/v1/hives",
            json={"apiary_id": apiary_id, "name": "Hive P"},
            headers=_headers(),
        ).json()["hive_id"]
        configure_hive(client, workspace_id=workspace_id, hive_id=hive_id, headers=_headers())
        inspection_id = client.post(
            "/v1/inspections",
            json={
                "hive_id": hive_id,
                "inspection_date": str(date(2026, 7, 31)),
                "intent": "training_data_collection",
            },
            headers=_headers(),
        ).json()["inspection_id"]
        intake = client.post(
            f"/v1/inspection-photos/intake?workspace_id={workspace_id}&inspection_id={inspection_id}",
            content=_minimal_png(),
            headers={
                **_headers(),
                "content-type": "image/png",
                "x-hivesight-filename": "persistent-frame.png",
            },
        )
        inspection_photo_id = intake.json()["inspection_photo"]["inspection_photo_id"]
        crop = client.post(
            "/v1/training-crops",
            json={
                "workspace_id": workspace_id,
                "inspection_photo_id": inspection_photo_id,
                "crop_x": 10,
                "crop_y": 20,
                "crop_width": 100,
                "crop_height": 120,
                "source_image_width_px": 1600,
                "source_image_height_px": 1200,
            },
            headers=_headers(),
        ).json()
        ellipse = client.post(
            f"/v1/training-crops/{crop['training_crop_id']}/bee-ellipses",
            json={
                "workspace_id": workspace_id,
                "annotation_type": "complete_visible_bee",
                "center_x": 50,
                "center_y": 70,
                "radius_x": 20,
                "radius_y": 12,
                "rotation_degrees": 15,
            },
            headers=_headers(),
        )
        assert ellipse.status_code == 201
        completed = client.patch(
            f"/v1/training-crops/{crop['training_crop_id']}",
            json={
                "workspace_id": workspace_id,
                "visible_bee_status": "has_visible_bees",
                "review_status": "review_complete",
            },
            headers=_headers(),
        )
        assert completed.status_code == 200
        dataset_item = client.post(
            f"/v1/training-crops/{crop['training_crop_id']}/dataset-item",
            json={
                "workspace_id": workspace_id,
                "dataset_role": "training",
                "source_group_key": "post-restart-frame",
            },
            headers=_headers(),
        )
        assert dataset_item.status_code == 201
        dataset_item_id = dataset_item.json()["dataset_item_id"]
        state.store.save_dataset_version(
            DatasetVersionResponse(
                dataset_version_id=UUID("00000000-0000-0000-0000-000000014999"),
                workspace_id=UUID(workspace_id),
                human_readable_id="HS-DV-PERSIST",
                purpose="bee_detector_training_baseline",
                model_purpose="bee_detector",
                status="created",
                export_format="yolo_obb_v1",
                selection_criteria={"dataset_role_policy": "training_and_validation_only"},
                manifest_hash="persistent-manifest-hash",
                included_dataset_item_ids=[UUID(dataset_item_id)],
                training_dataset_item_ids=[UUID(dataset_item_id)],
                validation_dataset_item_ids=[],
                protected_benchmark_dataset_item_ids=[],
                excluded_dataset_items=[],
                training_item_count=1,
                validation_item_count=0,
                benchmark_item_count=0,
                excluded_item_count=0,
                annotation_class_counts={"complete_visible_bee": 1},
                annotation_source_counts={"human_from_scratch": 1},
                review_method_counts={"human_review": 1},
                source_group_distribution={"post-restart-frame": 1},
                hive_configuration_distribution={"British National deep brood": 1},
                curriculum_stage_distribution={"sparse_bees": 1},
                image_quality_distribution={"usable": 1},
                warnings=[],
                preview_artifact_ids=[],
                report_artifact_id=None,
                created_by_user_id=USER_ID,
                created_at=datetime(2026, 7, 31, 10, 0, tzinfo=UTC),
            )
        )
    finally:
        app.dependency_overrides.clear()

    restarted_state = _build_postgres_state(
        database_url,
        object_storage_root=object_storage_root,
    )
    app.dependency_overrides[get_dev_state] = lambda: restarted_state
    restarted_client = TestClient(app)
    try:
        inspections = restarted_client.get(
            f"/v1/hives/{hive_id}/inspections",
            params={"workspace_id": workspace_id, "intent": "training_data_collection"},
            headers=_headers(),
        )
        photos = restarted_client.get(
            f"/v1/inspections/{inspection_id}/photos",
            params={"workspace_id": workspace_id},
            headers=_headers(),
        )
        crops = restarted_client.get(
            f"/v1/inspection-photos/{inspection_photo_id}/training-crops",
            params={"workspace_id": workspace_id},
            headers=_headers(),
        )
        evidence = restarted_client.get(
            f"/v1/training-crops/{crop['training_crop_id']}/evidence",
            params={"workspace_id": workspace_id},
            headers=_headers(),
        )
        content = restarted_client.get(
            f"/v1/inspection-photos/{inspection_photo_id}/content",
            params={"workspace_id": workspace_id},
            headers=_headers(),
        )
        repository = restarted_client.get(
            "/v1/dataset-repository/items",
            params={"workspace_id": workspace_id},
            headers=_headers(),
        )

        assert inspections.status_code == 200
        assert inspections.json()["inspections"][0]["inspection_id"] == inspection_id
        assert photos.status_code == 200
        assert photos.json()["photos"][0]["inspection_photo_id"] == inspection_photo_id
        assert crops.status_code == 200
        assert crops.json()["training_crops"][0]["training_crop_id"] == crop["training_crop_id"]
        assert evidence.status_code == 200
        assert evidence.json()["bee_ellipses"][0]["rotation_degrees"] == 15
        assert content.status_code == 200
        assert content.content == _minimal_png()
        assert repository.status_code == 200
        repository_body = repository.json()
        assert repository_body["summary"]["latest_dataset_version"]["human_readable_id"] == "HS-DV-PERSIST"
        assert repository_body["items"][0]["dataset_item_id"] == dataset_item_id
        assert repository_body["items"][0]["latest_dataset_version_membership"]["membership"] == "training"

        cleanup = restarted_client.post(
            "/v1/dev/directed-ellipse-orientation-cleanup",
            json={
                "workspace_id": workspace_id,
                "reason": "Postgres directed ellipse cleanup test.",
                "confirm_remove_dataset_and_model_evidence": True,
            },
            headers=_headers(),
        )
        assert cleanup.status_code == 200
        assert cleanup.json()["dataset_items_removed"] == 1
        assert cleanup.json()["dataset_versions_removed"] == 1
        assert cleanup.json()["training_crops_reopened"] == 1
        assert cleanup.json()["training_crop_ellipses_preserved"] == 1
    finally:
        app.dependency_overrides.clear()

    cleaned_state = _build_postgres_state(
        database_url,
        object_storage_root=object_storage_root,
    )
    app.dependency_overrides[get_dev_state] = lambda: cleaned_state
    cleaned_client = TestClient(app)
    try:
        cleaned_evidence = cleaned_client.get(
            f"/v1/training-crops/{crop['training_crop_id']}/evidence",
            params={"workspace_id": workspace_id},
            headers=_headers(),
        )
        cleaned_repository = cleaned_client.get(
            "/v1/dataset-repository/items",
            params={"workspace_id": workspace_id},
            headers=_headers(),
        )
        assert cleaned_evidence.status_code == 200
        assert cleaned_evidence.json()["training_crop"]["review_status"] == "review_pending"
        assert cleaned_evidence.json()["bee_ellipses"][0]["rotation_degrees"] == 15
        assert cleaned_repository.status_code == 200
        assert cleaned_repository.json()["summary"]["dataset_item_count"] == 0

        recompleted = cleaned_client.patch(
            f"/v1/training-crops/{crop['training_crop_id']}",
            json={
                "workspace_id": workspace_id,
                "visible_bee_status": "has_visible_bees",
                "review_status": "review_complete",
            },
            headers=_headers(),
        )
        reassignment = cleaned_client.post(
            f"/v1/training-crops/{crop['training_crop_id']}/dataset-item",
            json={
                "workspace_id": workspace_id,
                "dataset_role": "validation",
                "source_group_key": "post-cleanup-frame",
            },
            headers=_headers(),
        )
        assert recompleted.status_code == 200
        assert reassignment.status_code == 201
        assert reassignment.json()["reviewed_ellipse_snapshots"][0]["rotation_degrees"] == 15
    finally:
        app.dependency_overrides.clear()


@pytest.mark.skipif(
    importlib.util.find_spec("psycopg") is None or not os.getenv("HIVESIGHT_TEST_DATABASE_URL"),
    reason="Set HIVESIGHT_TEST_DATABASE_URL and install psycopg to run Postgres persistence integration.",
)
def test_postgres_store_seeds_development_users_with_separate_workspaces() -> None:
    database_url = os.environ["HIVESIGHT_TEST_DATABASE_URL"]
    reset_database(database_url)

    store = _build_postgres_state(database_url).store
    store.seed_development_users()

    owner_a = DEV_USERS[1]
    owner_b = DEV_USERS[2]
    curator = DEV_USERS[3]
    no_capability = DEV_USERS[-1]

    assert store.ensure_dev_session(owner_a.user_id).workspace_id == owner_a.workspace_id
    assert store.ensure_dev_session(owner_b.user_id).workspace_id == owner_b.workspace_id
    assert store.ensure_dev_session(curator.user_id).dataset_curator_capability is True
    assert store.ensure_dev_session(no_capability.user_id).dataset_curator_capability is False
    assert store.ensure_dev_session(no_capability.user_id).reviewer_capability is False
    assert [
        apiary.name
        for apiary in store.list_apiaries(UserContext(owner_a.user_id), owner_a.workspace_id)
    ] == ["Owner A Apiary"]
    with pytest.raises(DomainError) as error:
        store.list_apiaries(UserContext(owner_b.user_id), owner_a.workspace_id)
    assert error.value.code == "workspace_access_denied"


@pytest.mark.skipif(
    importlib.util.find_spec("psycopg") is None or not os.getenv("HIVESIGHT_TEST_DATABASE_URL"),
    reason="Set HIVESIGHT_TEST_DATABASE_URL and install psycopg to run Postgres persistence integration.",
)
def test_postgres_store_survives_restart_for_model_training_records() -> None:
    database_url = os.environ["HIVESIGHT_TEST_DATABASE_URL"]
    reset_database(database_url)
    store = _build_postgres_state(database_url).store
    now = datetime(2026, 7, 31, 10, 0, tzinfo=UTC)
    workspace_id = UUID("00000000-0000-0000-0000-000000000201")
    dataset_version_id = UUID("00000000-0000-0000-0000-000000014001")
    training_run_id = UUID("00000000-0000-0000-0000-000000014002")
    model_candidate_id = UUID("00000000-0000-0000-0000-000000014003")
    weights_artifact_id = UUID("00000000-0000-0000-0000-000000014004")
    benchmark_evaluation_id = UUID("00000000-0000-0000-0000-000000014005")

    artifact = ArtifactResponse(
        artifact_id=weights_artifact_id,
        owner_type="training_run",
        owner_id=training_run_id,
        artifact_type="weights",
        relative_path="training-run-HS-TR-000001/weights/best.pt",
        content_type="application/octet-stream",
        size_bytes=9,
        sha256="fake-sha",
        required_or_diagnostic="required",
        availability_status="available",
        created_at=now,
    )
    dataset_version = DatasetVersionResponse(
        dataset_version_id=dataset_version_id,
        workspace_id=workspace_id,
        human_readable_id="HS-DV-000001",
        purpose="bee_detector_training_baseline",
        model_purpose="bee_detector",
        status="created",
        export_format="yolo_obb_v1",
        selection_criteria={"dataset_role_policy": "training_and_validation_only"},
        manifest_hash="fake-manifest-hash",
        included_dataset_item_ids=[],
        training_dataset_item_ids=[],
        validation_dataset_item_ids=[],
        protected_benchmark_dataset_item_ids=[],
        excluded_dataset_items=[],
        training_item_count=1,
        validation_item_count=1,
        benchmark_item_count=0,
        excluded_item_count=0,
        annotation_class_counts={"complete_visible_bee": 1},
        annotation_source_counts={"human_from_scratch": 1},
        review_method_counts={"human_review": 1},
        source_group_distribution={"post-restart-frame": 1},
        hive_configuration_distribution={},
        curriculum_stage_distribution={"sparse_bees": 1},
        image_quality_distribution={"usable": 1},
        warnings=[],
        preview_artifact_ids=[],
        report_artifact_id=None,
        created_by_user_id=USER_ID,
        created_at=now,
    )
    training_run = TrainingRunResponse(
        training_run_id=training_run_id,
        workspace_id=workspace_id,
        human_readable_id="HS-TR-000001",
        dataset_version_id=dataset_version_id,
        model_purpose="bee_detector",
        model_family="yolo_obb",
        model_size="nano",
        base_weights="yolo11n-obb.pt",
        base_weights_source="ultralytics",
        status="completed",
        phase="completed",
        adapter_type="fake",
        database_purpose="test",
        training_settings={"epochs": 1, "image_size": 640, "batch_size": 1},
        random_seed=7,
        git_commit_sha=None,
        git_dirty_status="clean",
        environment_summary={"fixture": True},
        warning_acknowledgement={"acknowledged": True},
        started_at=now,
        completed_at=now,
        failure_code=None,
        failure_message=None,
        artifact_ids=[weights_artifact_id],
        metrics_summary={"precision": 0.1},
        report_artifact_id=None,
        model_candidate_id=model_candidate_id,
        created_by_user_id=USER_ID,
        created_at=now,
        purpose_notes="test training run",
    )
    model_candidate = ModelCandidateResponse(
        model_candidate_id=model_candidate_id,
        workspace_id=workspace_id,
        human_readable_id="HS-MC-000001",
        display_name="HS-MC-000001 fake YOLO OBB",
        training_run_id=training_run_id,
        model_purpose="bee_detector",
        model_family="yolo_obb",
        adapter_type="fake",
        artifact_id=weights_artifact_id,
        status="created",
        promotion_status="not_evaluated",
        not_user_facing_reason="baseline_training_only",
        created_at=now,
    )
    benchmark_evaluation = BenchmarkEvaluationResponse(
        benchmark_evaluation_id=benchmark_evaluation_id,
        workspace_id=workspace_id,
        human_readable_id="HS-BE-000001",
        model_candidate_id=model_candidate_id,
        model_candidate_human_readable_id="HS-MC-000001",
        training_run_id=training_run_id,
        dataset_version_id=dataset_version_id,
        status="completed",
        phase="completed",
        adapter_type="fake",
        training_adapter_type="fake",
        evaluation_adapter_type="fake",
        database_purpose="test",
        confidence_threshold=0.1,
        match_strategy="ellipse_match_v1",
        benchmark_scope="training_crop_benchmark_only",
        started_at=now,
        completed_at=now,
        last_heartbeat_at=now,
        last_activity_message="Benchmark Evaluation completed.",
        progress_percent=100,
        latest_log_excerpt="Benchmark Evaluation completed.",
        warnings=[],
        metrics_summary={"precision": 0.5, "recall": 1.0},
        item_results=[],
        raw_prediction_artifact_id=None,
        report_artifact_id=None,
        artifact_ids=[],
        created_by_user_id=USER_ID,
        created_at=now,
    )

    store.save_artifact(artifact)
    store.save_dataset_version(dataset_version)
    store.save_training_run(training_run)
    store.save_model_candidate(model_candidate)
    store.save_benchmark_evaluation(benchmark_evaluation)

    restarted = _build_postgres_state(database_url).store
    assert (
        restarted.get_dataset_version(workspace_id, dataset_version_id).human_readable_id
        == "HS-DV-000001"
    )
    assert restarted.get_training_run(workspace_id, training_run_id).status == "completed"
    assert (
        restarted.get_model_candidate(workspace_id, model_candidate_id).human_readable_id
        == "HS-MC-000001"
    )
    assert (
        restarted.get_benchmark_evaluation(workspace_id, benchmark_evaluation_id).human_readable_id
        == "HS-BE-000001"
    )
    assert restarted.get_artifact(weights_artifact_id).relative_path.endswith("weights/best.pt")

def _build_postgres_state(database_url: str, object_storage_root: Path | None = None):
    store = PostgresProductDataStore(
        database_url=database_url,
        id_factory=_id_factory(),
        clock=lambda: datetime(2026, 7, 31, 10, 0, tzinfo=UTC),
    )
    from hive_sight_core_api.dev_store import DevState

    return DevState(
        store=store,
        object_storage=(
            FileSystemObjectStorage(root=object_storage_root)
            if object_storage_root is not None
            else InMemoryObjectStorage()
        ),
        event_recorder=InMemoryEventRecorder(),
        upload_policy=UploadPolicy(),
        dataset_export_root=Path("/tmp/hive-sight-test-exports"),
        model_artifact_root=Path("/tmp/hive-sight-test-model-runs"),
    )


def _id_factory():
    values = [UUID(f"00000000-0000-0000-0000-000000014{i:03d}") for i in range(1, 120)]

    def next_id() -> UUID:
        return values.pop(0)

    return next_id


def _headers() -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(USER_ID)}


def _minimal_png() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x06@\x00\x00\x04\xb0\x08\x02\x00\x00\x00"
        b"\x3b\x7f\x5b\x4b"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
