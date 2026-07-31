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
from hive_sight_core_api.dev_store import InMemoryEventRecorder, InMemoryObjectStorage, UploadPolicy
from hive_sight_core_api.main import app
from hive_sight_core_api.models import (
    ArtifactResponse,
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
    state = _build_postgres_state(database_url)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)

    try:
        workspace_id = client.get("/v1/dev/session", headers=_headers()).json()["workspace_id"]
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
    finally:
        app.dependency_overrides.clear()


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

    artifact = ArtifactResponse(
        artifact_id=weights_artifact_id,
        workspace_id=workspace_id,
        artifact_kind="weights",
        relative_path="training-run-HS-TR-000001/weights/best.pt",
        media_type="application/octet-stream",
        size_bytes=9,
        sha256="fake-sha",
        created_at=now,
    )
    dataset_version = DatasetVersionResponse(
        dataset_version_id=dataset_version_id,
        human_readable_id="HS-DV-000001",
        workspace_id=workspace_id,
        model_purpose="bee_detector",
        export_format="yolo_obb_v1",
        conversion_version="ellipse_to_yolo_obb_v1",
        dataset_role_policy="training_and_validation_only",
        created_by_user_id=USER_ID,
        created_at=now,
        source_dataset_item_ids=[],
        included_dataset_item_ids=[],
        protected_benchmark_dataset_item_ids=[],
        excluded_dataset_items=[],
        training_item_count=1,
        validation_item_count=1,
        benchmark_item_count=0,
        class_map={"0": "complete_visible_bee", "1": "partial_visible_bee"},
        package_artifact_id=weights_artifact_id,
        manifest_artifact_id=weights_artifact_id,
        dataset_yaml_artifact_id=weights_artifact_id,
        report_artifact_id=None,
        preview_artifact_ids=[],
        warnings=[],
        git_commit=None,
        status="created",
        caveat="test dataset version",
    )
    training_run = TrainingRunResponse(
        training_run_id=training_run_id,
        human_readable_id="HS-TR-000001",
        workspace_id=workspace_id,
        dataset_version_id=dataset_version_id,
        model_purpose="bee_detector",
        adapter_type="fake",
        status="completed",
        requested_by_user_id=USER_ID,
        requested_at=now,
        started_at=now,
        completed_at=now,
        failed_at=None,
        failure_code=None,
        failure_message=None,
        epochs=1,
        image_size=640,
        batch_size=1,
        random_seed=7,
        metrics={"precision": 0.1},
        model_candidate_id=model_candidate_id,
        report_artifact_id=None,
        log_artifact_id=None,
        warnings_acknowledged=True,
        caveat="test training run",
    )
    model_candidate = ModelCandidateResponse(
        model_candidate_id=model_candidate_id,
        human_readable_id="HS-MC-000001",
        workspace_id=workspace_id,
        training_run_id=training_run_id,
        dataset_version_id=dataset_version_id,
        model_purpose="bee_detector",
        adapter_type="fake",
        weights_artifact_id=weights_artifact_id,
        metrics={"precision": 0.1},
        promotion_status="not_evaluated",
        not_user_facing_reason="baseline_training_only",
        created_at=now,
    )

    store.save_artifact(artifact)
    store.save_dataset_version(dataset_version)
    store.save_training_run(training_run)
    store.save_model_candidate(model_candidate)

    restarted = _build_postgres_state(database_url).store
    assert restarted.get_dataset_version(dataset_version_id).human_readable_id == "HS-DV-000001"
    assert restarted.get_training_run(training_run_id).status == "completed"
    assert restarted.get_model_candidate(model_candidate_id).human_readable_id == "HS-MC-000001"
    assert restarted.get_artifact(weights_artifact_id).relative_path.endswith("weights/best.pt")

    restarted_state = _build_postgres_state(database_url)
    app.dependency_overrides[get_dev_state] = lambda: restarted_state
    restarted_client = TestClient(app)
    try:
        crops = restarted_client.get(
            f"/v1/inspection-photos/{inspection_photo_id}/training-crops?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert crops.status_code == 200
        assert crops.json()["training_crops"][0]["training_crop_id"] == crop["training_crop_id"]
        export = restarted_client.post(
            "/v1/dataset-exports/yolo-obb",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        )
        assert export.status_code == 201
        assert export.json()["training_item_count"] == 1
    finally:
        app.dependency_overrides.clear()


def _build_postgres_state(database_url: str):
    store = PostgresProductDataStore(
        database_url=database_url,
        id_factory=_id_factory(),
        clock=lambda: datetime(2026, 7, 31, 10, 0, tzinfo=UTC),
    )
    from hive_sight_core_api.dev_store import DevState

    return DevState(
        store=store,
        object_storage=InMemoryObjectStorage(),
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
