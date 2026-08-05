from datetime import UTC, date, datetime, timedelta
from io import BytesIO
from pathlib import Path
import json
import threading
import time
from uuid import UUID

from fastapi.testclient import TestClient
from hive_configuration_test_support import configure_hive
from PIL import Image

from hive_sight_core_api.bee_detector_training_workflow import (
    BeeDetectorTrainingWorkflow,
    TrainingAdapterResult,
)
from hive_sight_core_api.dependencies import (
    build_dev_state,
    get_bee_detector_training_workflow,
    get_dev_state,
)
from hive_sight_core_api.main import app

CURATOR_ID = UUID("00000000-0000-0000-0000-000000000101")
ORDINARY_USER_ID = UUID("00000000-0000-0000-0000-000000000999")


def test_dataset_curator_creates_dataset_version_and_fake_training_run(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id = _workspace(client)
        _create_reviewed_crop_item(client, workspace_id, "training", 10, 10)
        _create_reviewed_crop_item(client, workspace_id, "validation", 260, 10)

        readiness = client.get(
            f"/v1/model-training/readiness?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert readiness.status_code == 200
        assert readiness.json()["adapter_type"] == "fake"
        assert readiness.json()["eligible_to_create_dataset_version"] is True
        assert readiness.json()["database_purpose"] == "dev"

        dataset_version_response = client.post(
            "/v1/model-training/dataset-versions",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        )
        assert dataset_version_response.status_code == 201
        dataset_version = dataset_version_response.json()
        assert dataset_version["human_readable_id"] == "HS-DV-000001"
        assert dataset_version["training_item_count"] == 1
        assert dataset_version["validation_item_count"] == 1
        assert dataset_version["purpose"] == "marked_bee_detection_orientation"
        assert dataset_version["model_purpose"] == "marked_bee"
        assert dataset_version["export_format"] == "marked_bee_dataset_v1"
        assert dataset_version["protected_benchmark_dataset_item_ids"] == []
        assert dataset_version["report_artifact_id"] is not None
        assert dataset_version["preview_artifact_ids"]
        assert any(warning["code"] == "NO_BENCHMARK_ITEMS" for warning in dataset_version["warnings"])
        package_dir = (
            state.model_artifact_root
            / "dataset-versions"
            / f"dataset-version-{dataset_version['dataset_version_id']}"
        )
        dataset_yaml = (package_dir / "data.yaml").read_text(encoding="utf-8")
        assert f"path: {package_dir.resolve()}" in dataset_yaml
        assert (package_dir / "images" / "train").is_dir()
        assert (package_dir / "images" / "val").is_dir()

        blocked_training = client.post(
            "/v1/model-training/training-runs",
            json={
                "workspace_id": workspace_id,
                "dataset_version_id": dataset_version["dataset_version_id"],
            },
            headers=_headers(),
        )
        assert blocked_training.status_code == 409
        assert (
            blocked_training.json()["detail"]["code"]
            == "high_severity_warnings_require_acknowledgement"
        )

        training_response = client.post(
            "/v1/model-training/training-runs",
            json={
                "workspace_id": workspace_id,
                "dataset_version_id": dataset_version["dataset_version_id"],
                "acknowledge_high_severity_warnings": True,
                "epochs": 1,
                "image_size": 640,
                "batch_size": 1,
                "random_seed": 7,
            },
            headers=_headers(),
        )
        assert training_response.status_code == 202
        queued_run = training_response.json()
        assert queued_run["human_readable_id"] == "HS-TR-000001"
        assert queued_run["status"] == "queued"
        assert queued_run["last_heartbeat_at"] is not None
        training_run = _wait_for_training_run_status(
            client,
            workspace_id,
            queued_run["training_run_id"],
            "completed",
        )
        assert training_run["status"] == "completed"
        assert training_run["adapter_type"] == "fake"
        assert training_run["model_purpose"] == "bee_detector"
        assert training_run["phase"] == "completed"
        assert training_run["last_heartbeat_at"] is not None
        assert training_run["last_activity_message"] == "Training completed and Model Candidate created."
        assert training_run["latest_log_excerpt"] is not None
        assert training_run["model_candidate_id"] is not None
        assert training_run["report_artifact_id"] is not None

        candidates = client.get(
            f"/v1/model-training/model-candidates?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert candidates.status_code == 200
        candidate = candidates.json()["model_candidates"][0]
        assert candidate["human_readable_id"] == "HS-MC-000001"
        assert candidate["promotion_status"] == "not_evaluated"
        assert candidate["not_user_facing_reason"] == "baseline_training_only"

        report = client.get(
            f"/v1/model-training/artifacts/{training_run['report_artifact_id']}?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert report.status_code == 200
        assert "Bee Localisation only" in report.text
    finally:
        app.dependency_overrides.clear()


def test_dataset_curator_creates_marked_bee_dataset_version_and_orientation_baseline(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id = _workspace(client)
        _create_reviewed_crop_item(client, workspace_id, "training", 10, 10)
        _create_reviewed_crop_item(client, workspace_id, "validation", 260, 10)

        dataset_version_response = client.post(
            "/v1/model-training/dataset-versions",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        )
        assert dataset_version_response.status_code == 201
        dataset_version = dataset_version_response.json()
        assert dataset_version["purpose"] == "marked_bee_detection_orientation"
        assert dataset_version["model_purpose"] == "marked_bee"
        assert dataset_version["export_format"] == "marked_bee_dataset_v1"

        readiness = client.get(
            "/v1/model-training/readiness"
            f"?workspace_id={workspace_id}&model_purpose=bee_orientation"
            f"&dataset_version_id={dataset_version['dataset_version_id']}",
            headers=_headers(),
        )
        assert readiness.status_code == 200
        assert readiness.json()["model_purpose"] == "bee_orientation"
        assert readiness.json()["eligible_training_source_bee_count"] == 1
        assert readiness.json()["eligible_validation_source_bee_count"] == 1
        assert readiness.json()["generated_training_example_count"] == 2
        assert readiness.json()["generated_validation_example_count"] == 2
        assert readiness.json()["eligible_to_start_training"] is True

        training_response = client.post(
            "/v1/model-training/training-runs",
            json={
                "workspace_id": workspace_id,
                "dataset_version_id": dataset_version["dataset_version_id"],
                "model_purpose": "bee_orientation",
                "acknowledge_high_severity_warnings": True,
            },
            headers=_headers(),
        )
        assert training_response.status_code == 202
        training_run = _wait_for_training_run_status(
            client,
            workspace_id,
            training_response.json()["training_run_id"],
            "completed",
        )

        assert training_run["model_purpose"] == "bee_orientation"
        assert training_run["model_family"] == "bee_orientation_binary_classifier"
        assert training_run["metrics_summary"]["predictive_training_performed"] is False
        assert training_run["metrics_summary"]["generated_training_example_count"] == 2
        assert training_run["metrics_summary"]["generated_validation_example_count"] == 2
        assert "accuracy" not in training_run["metrics_summary"]
        assert training_run["model_candidate_id"] is not None

        candidates = client.get(
            f"/v1/model-training/model-candidates?workspace_id={workspace_id}",
            headers=_headers(),
        )
        orientation_candidate = [
            candidate
            for candidate in candidates.json()["model_candidates"]
            if candidate["model_candidate_id"] == training_run["model_candidate_id"]
        ][0]
        assert orientation_candidate["model_purpose"] == "bee_orientation"
        assert orientation_candidate["model_family"] == "bee_orientation_binary_classifier"
        assert orientation_candidate["not_user_facing_reason"] == "baseline_training_only"

        report = client.get(
            f"/v1/model-training/artifacts/{training_run['report_artifact_id']}?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert report.status_code == 200
        assert "No predictive model training was performed" in report.text
        assert "head_up" in report.text
        assert "head_down" in report.text

        run_dir = (
            state.model_artifact_root
            / "training-runs"
            / f"training-run-{training_run['training_run_id']}"
        )
        package_dir = run_dir / "bee-orientation-package"
        assert (package_dir / "manifest.json").exists()
        assert (package_dir / "labels.jsonl").exists()
        assert (package_dir / "exclusions.jsonl").exists()
        labels = [
            json.loads(line)
            for line in (package_dir / "labels.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        assert {label["label"] for label in labels} == {"head_up", "head_down"}
        assert {label["augmentation"] for label in labels} == {"none", "rotate_180"}
        assert all(label["image_sha256"] for label in labels)
        assert list((package_dir / "images" / "train").glob("*.png"))
        manifest = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["image_size"] == 224
        assert manifest["ellipse_margin_ratio"] == 0.2
        assert manifest["package_hash"]
    finally:
        app.dependency_overrides.clear()


def test_orientation_readiness_excludes_unreliable_partial_and_benchmark_evidence(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id = _workspace(client)
        _create_reviewed_crop_item(client, workspace_id, "training", 10, 10)
        _create_reviewed_crop_item(client, workspace_id, "validation", 260, 10)
        _create_reviewed_crop_item(
            client,
            workspace_id,
            "training",
            10,
            260,
            orientation_reliability="unreliable",
        )
        _create_reviewed_crop_item(
            client,
            workspace_id,
            "validation",
            260,
            260,
            annotation_type="partial_visible_bee",
        )
        _create_reviewed_crop_item(client, workspace_id, "benchmark", 420, 10)

        dataset_version = client.post(
            "/v1/model-training/dataset-versions",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        ).json()
        readiness = client.get(
            "/v1/model-training/readiness"
            f"?workspace_id={workspace_id}&model_purpose=bee_orientation"
            f"&dataset_version_id={dataset_version['dataset_version_id']}",
            headers=_headers(),
        )

        assert readiness.status_code == 200
        body = readiness.json()
        assert body["eligible_training_source_bee_count"] == 1
        assert body["eligible_validation_source_bee_count"] == 1
        assert body["protected_benchmark_source_bee_count"] == 1
        assert body["excluded_unreliable_orientation_count"] == 1
        assert body["excluded_partial_visible_bee_count"] == 1
        assert body["eligible_to_start_training"] is True
    finally:
        app.dependency_overrides.clear()


def test_orientation_readiness_blocks_missing_source_image_bytes(tmp_path: Path) -> None:
    state = _build_state(tmp_path)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id = _workspace(client)
        _create_reviewed_crop_item(client, workspace_id, "training", 10, 10)
        _create_reviewed_crop_item(client, workspace_id, "validation", 260, 10)
        dataset_version = client.post(
            "/v1/model-training/dataset-versions",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        ).json()
        state.object_storage.objects.clear()

        readiness = client.get(
            "/v1/model-training/readiness"
            f"?workspace_id={workspace_id}&model_purpose=bee_orientation"
            f"&dataset_version_id={dataset_version['dataset_version_id']}",
            headers=_headers(),
        )
        body = readiness.json()

        assert readiness.status_code == 200
        assert body["eligible_to_start_training"] is False
        assert any(
            warning["code"] == "SOURCE_IMAGE_BYTES_MISSING"
            for warning in body["warnings"]
        )
    finally:
        app.dependency_overrides.clear()


def test_bee_training_readiness_and_start_use_one_shared_dataset_version(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_bee_detector_training_workflow] = lambda: BeeDetectorTrainingWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        artifact_root=state.model_artifact_root,
        adapter=AvailableRealishTrainingAdapter(),
        orientation_adapter=AvailableRealishOrientationAdapter(),
        persistence_backend="postgres",
        database_purpose="dev",
        clock=state.store.clock,
    )
    client = TestClient(app)
    try:
        workspace_id = _workspace(client)
        for offset in range(4):
            _create_reviewed_crop_item(client, workspace_id, "training", 10 + offset, 10)
            _create_reviewed_crop_item(client, workspace_id, "validation", 260 + offset, 10)
        dataset_version = client.post(
            "/v1/model-training/dataset-versions",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        ).json()

        readiness = client.get(
            "/v1/model-training/bee-training/readiness"
            f"?workspace_id={workspace_id}&dataset_version_id={dataset_version['dataset_version_id']}",
            headers=_headers(),
        )
        assert readiness.status_code == 200
        assert readiness.json()["eligible_to_start_bee_training"] is True
        assert readiness.json()["bee_localisation"]["adapter_type"] == "ultralytics_yolo_obb"
        assert readiness.json()["bee_orientation"]["adapter_type"] == "torchvision_orientation_classifier"

        start_response = client.post(
            "/v1/model-training/bee-training/runs",
            json={
                "workspace_id": workspace_id,
                "dataset_version_id": dataset_version["dataset_version_id"],
                "acknowledge_high_severity_warnings": True,
            },
            headers=_headers(),
        )
        assert start_response.status_code == 202
        localisation_run_id = start_response.json()["bee_localisation_training_run"][
            "training_run_id"
        ]
        localisation_run = _wait_for_training_run_status(
            client,
            workspace_id,
            localisation_run_id,
            "completed",
        )
        assert localisation_run["dataset_version_id"] == dataset_version["dataset_version_id"]
        orientation_run = _wait_for_training_run_purpose_status(
            client,
            workspace_id,
            "bee_orientation",
            "completed",
        )
        assert orientation_run["dataset_version_id"] == dataset_version["dataset_version_id"]
        assert orientation_run["adapter_type"] == "torchvision_orientation_classifier"
        assert orientation_run["metrics_summary"]["predictive_training_performed"] is True
        assert orientation_run["metrics_summary"]["metric_scope"] == "training_run_validation_not_benchmark"
        assert "validation_accuracy" in orientation_run["metrics_summary"]
        assert "confusion_matrix" in orientation_run["metrics_summary"]
    finally:
        app.dependency_overrides.clear()


def test_real_orientation_training_requires_four_reliable_bees_per_split(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_bee_detector_training_workflow] = lambda: BeeDetectorTrainingWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        artifact_root=state.model_artifact_root,
        adapter=AvailableRealishTrainingAdapter(),
        orientation_adapter=AvailableRealishOrientationAdapter(),
        persistence_backend="postgres",
        database_purpose="dev",
        clock=state.store.clock,
    )
    client = TestClient(app)
    try:
        workspace_id = _workspace(client)
        _create_reviewed_crop_item(client, workspace_id, "training", 10, 10)
        _create_reviewed_crop_item(client, workspace_id, "validation", 260, 10)
        dataset_version = client.post(
            "/v1/model-training/dataset-versions",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        ).json()

        readiness = client.get(
            "/v1/model-training/bee-training/readiness"
            f"?workspace_id={workspace_id}&dataset_version_id={dataset_version['dataset_version_id']}",
            headers=_headers(),
        )
        assert readiness.status_code == 200
        assert readiness.json()["eligible_to_start_bee_training"] is False
        assert readiness.json()["bee_orientation"]["eligible_to_start_training"] is False
        assert any(
            "at least 4 reliable complete visible bees" in warning["message"]
            for warning in readiness.json()["bee_orientation"]["warnings"]
        )
    finally:
        app.dependency_overrides.clear()


def test_directed_ellipse_cleanup_removes_local_dataset_model_evidence_and_reopens_crops(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id = _workspace(client)
        training_crop_id = _create_reviewed_crop_item(client, workspace_id, "training", 10, 10)
        _create_reviewed_crop_item(client, workspace_id, "validation", 260, 10)
        dataset_version_response = client.post(
            "/v1/model-training/dataset-versions",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        )
        assert dataset_version_response.status_code == 201
        dataset_version = dataset_version_response.json()
        package_dir = (
            state.model_artifact_root
            / "dataset-versions"
            / f"dataset-version-{dataset_version['dataset_version_id']}"
        )
        assert package_dir.exists()
        training_response = client.post(
            "/v1/model-training/training-runs",
            json={
                "workspace_id": workspace_id,
                "dataset_version_id": dataset_version["dataset_version_id"],
                "acknowledge_high_severity_warnings": True,
            },
            headers=_headers(),
        )
        assert training_response.status_code == 202
        training_run = _wait_for_training_run_status(
            client,
            workspace_id,
            training_response.json()["training_run_id"],
            "completed",
        )
        run_dir = (
            state.model_artifact_root
            / "training-runs"
            / f"training-run-{training_run['training_run_id']}"
        )
        assert run_dir.exists()

        missing_confirmation = client.post(
            "/v1/dev/directed-ellipse-orientation-cleanup",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        )
        assert missing_confirmation.status_code == 422
        assert (
            missing_confirmation.json()["detail"]["code"]
            == "directed_ellipse_cleanup_confirmation_required"
        )

        cleanup = client.post(
            "/v1/dev/directed-ellipse-orientation-cleanup",
            json={
                "workspace_id": workspace_id,
                "reason": "Slice test reset.",
                "confirm_remove_dataset_and_model_evidence": True,
            },
            headers=_headers(),
        )

        assert cleanup.status_code == 200
        body = cleanup.json()
        assert body["dataset_items_removed"] == 2
        assert body["dataset_versions_removed"] == 1
        assert body["training_runs_removed"] == 1
        assert body["model_candidates_removed"] == 1
        assert body["artifacts_removed"] > 0
        assert body["training_crops_reopened"] == 2
        assert body["training_crop_ellipses_preserved"] == 2
        assert body["inspection_photos_preserved"] == 2
        assert state.store.dataset_items == {}
        assert state.store.dataset_versions == {}
        assert state.store.training_runs == {}
        assert state.store.model_candidates == {}
        assert state.store.artifacts == {}
        assert not package_dir.exists()
        assert not run_dir.exists()
        assert state.store.training_crops[UUID(training_crop_id)].review_status == "review_pending"
        assert len(state.store.training_crop_ellipses) == 2
        evidence = client.get(
            f"/v1/training-crops/{training_crop_id}/evidence?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert evidence.status_code == 200
        assert evidence.json()["training_crop"]["review_status"] == "review_pending"
    finally:
        app.dependency_overrides.clear()


def test_model_training_requires_dataset_curator_capability(tmp_path: Path) -> None:
    state = _build_state(tmp_path)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        state.store.dataset_curator_user_ids.clear()
        workspace_id = client.get(
            "/v1/dev/session",
            headers={"x-hivesight-dev-user-id": str(ORDINARY_USER_ID)},
        ).json()["workspace_id"]
        client.post(
            "/v1/workspace-data-use-agreements/acceptances",
            json={"workspace_id": workspace_id, "terms_version": "2026-07-31"},
            headers={"x-hivesight-dev-user-id": str(ORDINARY_USER_ID)},
        )
        response = client.get(
            f"/v1/model-training/readiness?workspace_id={workspace_id}",
            headers={"x-hivesight-dev-user-id": str(ORDINARY_USER_ID)},
        )
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "dataset_curator_access_required"
    finally:
        app.dependency_overrides.clear()


def test_unavailable_real_training_adapter_blocks_training_run_start(tmp_path: Path) -> None:
    state = _build_state(tmp_path)
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_bee_detector_training_workflow] = lambda: BeeDetectorTrainingWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        artifact_root=state.model_artifact_root,
        adapter=UnavailableRealTrainingAdapter(),
        persistence_backend="postgres",
        database_purpose="dev",
        clock=state.store.clock,
    )
    client = TestClient(app)
    try:
        workspace_id = _workspace(client)
        _create_reviewed_crop_item(client, workspace_id, "training", 10, 10)
        _create_reviewed_crop_item(client, workspace_id, "validation", 260, 10)

        readiness = client.get(
            f"/v1/model-training/readiness?workspace_id={workspace_id}",
            headers=_headers(),
        )
        dataset_version_response = client.post(
            "/v1/model-training/dataset-versions",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        )
        training_response = client.post(
            "/v1/model-training/training-runs",
            json={
                "workspace_id": workspace_id,
                "dataset_version_id": dataset_version_response.json()["dataset_version_id"],
                "acknowledge_high_severity_warnings": True,
            },
            headers=_headers(),
        )

        assert readiness.status_code == 200
        assert readiness.json()["adapter_type"] == "ultralytics_yolo_obb"
        assert readiness.json()["real_adapter_available"] is False
        assert readiness.json()["eligible_to_start_training"] is False
        assert training_response.status_code == 409
        assert training_response.json()["detail"]["code"] == "real_adapter_unavailable"
        assert state.store.list_training_runs(UUID(workspace_id)) == []
    finally:
        app.dependency_overrides.clear()


def test_artifact_serving_uses_known_artifact_ids(tmp_path: Path) -> None:
    state = _build_state(tmp_path)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id = _workspace(client)
        response = client.get(
            f"/v1/model-training/artifacts/00000000-0000-0000-0000-000000009999?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "artifact_not_found"
    finally:
        app.dependency_overrides.clear()


def test_dataset_curator_evaluates_model_candidate_against_protected_benchmark(
    tmp_path: Path,
) -> None:
    state = _build_state(tmp_path)
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id = _workspace(client)
        _create_reviewed_crop_item(client, workspace_id, "training", 10, 10)
        _create_reviewed_crop_item(client, workspace_id, "validation", 260, 10)
        _create_reviewed_crop_item(client, workspace_id, "benchmark", 10, 260)
        dataset_version = client.post(
            "/v1/model-training/dataset-versions",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        ).json()
        training_response = client.post(
            "/v1/model-training/training-runs",
            json={
                "workspace_id": workspace_id,
                "dataset_version_id": dataset_version["dataset_version_id"],
                "acknowledge_high_severity_warnings": True,
            },
            headers=_headers(),
        )
        training_run = _wait_for_training_run_status(
            client,
            workspace_id,
            training_response.json()["training_run_id"],
            "completed",
        )

        readiness = client.get(
            "/v1/model-training/model-candidates/"
            f"{training_run['model_candidate_id']}/benchmark-readiness?workspace_id={workspace_id}",
            headers=_headers(),
        )
        start_response = client.post(
            "/v1/model-training/benchmark-evaluations",
            json={
                "workspace_id": workspace_id,
                "model_candidate_id": training_run["model_candidate_id"],
            },
            headers=_headers(),
        )
        evaluation = _wait_for_benchmark_evaluation_status(
            client,
            workspace_id,
            start_response.json()["benchmark_evaluation_id"],
            "completed",
        )

        assert readiness.status_code == 200
        assert readiness.json()["benchmark_item_count"] == 1
        assert readiness.json()["eligible_to_start_evaluation"] is True
        assert any(
            warning["code"] == "SMALL_BENCHMARK_SET"
            for warning in readiness.json()["warnings"]
        )
        assert start_response.status_code == 202
        assert evaluation["human_readable_id"] == "HS-BE-000001"
        assert evaluation["status"] == "completed"
        assert evaluation["benchmark_scope"] == "training_crop_benchmark_only"
        assert evaluation["metrics_summary"]["benchmark_item_count"] == 1
        assert evaluation["metrics_summary"]["recall"] == 1
        assert evaluation["metrics_summary"]["precision"] == 0.5
        assert len(evaluation["item_results"]) == 1
        assert evaluation["raw_prediction_artifact_id"] is not None
        assert evaluation["report_artifact_id"] is not None

        report = client.get(
            f"/v1/model-training/artifacts/{evaluation['report_artifact_id']}?workspace_id={workspace_id}",
            headers=_headers(),
        )
        raw_predictions = client.get(
            "/v1/model-training/artifacts/"
            f"{evaluation['raw_prediction_artifact_id']}?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert report.status_code == 200
        assert "Training Crop benchmark only" in report.text
        assert "not beekeeper-facing inspection output" in report.text
        assert raw_predictions.status_code == 200
        assert raw_predictions.json()["predictions"][0]["predictions"]
    finally:
        app.dependency_overrides.clear()


def test_benchmark_evaluation_requires_dataset_curator_capability(tmp_path: Path) -> None:
    state = _build_state(tmp_path)
    state.store.dataset_curator_user_ids.clear()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        workspace_id = client.get(
            "/v1/dev/session",
            headers={"x-hivesight-dev-user-id": str(ORDINARY_USER_ID)},
        ).json()["workspace_id"]
        client.post(
            "/v1/workspace-data-use-agreements/acceptances",
            json={"workspace_id": workspace_id, "terms_version": "2026-07-31"},
            headers={"x-hivesight-dev-user-id": str(ORDINARY_USER_ID)},
        )
        response = client.post(
            "/v1/model-training/benchmark-evaluations",
            json={
                "workspace_id": workspace_id,
                "model_candidate_id": "00000000-0000-0000-0000-000000009999",
            },
            headers={"x-hivesight-dev-user-id": str(ORDINARY_USER_ID)},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "dataset_curator_access_required"
    finally:
        app.dependency_overrides.clear()


def test_dataset_curator_can_cancel_active_training_run(tmp_path: Path) -> None:
    state = _build_state(tmp_path)
    adapter = BlockingTrainingAdapter()
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_bee_detector_training_workflow] = lambda: BeeDetectorTrainingWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        artifact_root=state.model_artifact_root,
        adapter=adapter,
        persistence_backend="in_memory",
        database_purpose="dev",
        clock=state.store.clock,
    )
    client = TestClient(app)
    try:
        workspace_id, dataset_version_id = _dataset_version_with_minimum_items(client)
        start_response = client.post(
            "/v1/model-training/training-runs",
            json={
                "workspace_id": workspace_id,
                "dataset_version_id": dataset_version_id,
                "acknowledge_high_severity_warnings": True,
            },
            headers=_headers(),
        )
        assert start_response.status_code == 202
        training_run_id = start_response.json()["training_run_id"]
        adapter.started.wait(timeout=2)

        cancel_response = client.post(
            f"/v1/model-training/training-runs/{training_run_id}/cancel",
            json={"workspace_id": workspace_id, "reason": "Local smoke run is taking too long."},
            headers=_headers(),
        )
        adapter.release()
        cancelled = _wait_for_training_run_status(client, workspace_id, training_run_id, "cancelled")

        assert cancel_response.status_code == 200
        assert cancel_response.json()["status"] == "cancelling"
        assert cancelled["model_candidate_id"] is None
        assert cancelled["cancel_reason"] == "Local smoke run is taking too long."
        assert state.store.active_training_run(UUID(workspace_id)) is None
    finally:
        adapter.release()
        app.dependency_overrides.clear()


def test_dataset_curator_can_abandon_stale_training_run(tmp_path: Path) -> None:
    clock = MutableClock(datetime(2026, 7, 31, 12, 0, tzinfo=UTC))
    state = _build_state(tmp_path, clock=clock)
    adapter = BlockingTrainingAdapter()
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_bee_detector_training_workflow] = lambda: BeeDetectorTrainingWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        artifact_root=state.model_artifact_root,
        adapter=adapter,
        persistence_backend="in_memory",
        database_purpose="dev",
        clock=state.store.clock,
        stale_after_seconds=60,
    )
    client = TestClient(app)
    try:
        workspace_id, dataset_version_id = _dataset_version_with_minimum_items(client)
        start_response = client.post(
            "/v1/model-training/training-runs",
            json={
                "workspace_id": workspace_id,
                "dataset_version_id": dataset_version_id,
                "acknowledge_high_severity_warnings": True,
            },
            headers=_headers(),
        )
        training_run_id = start_response.json()["training_run_id"]
        adapter.started.wait(timeout=2)

        too_early = client.post(
            f"/v1/model-training/training-runs/{training_run_id}/abandon",
            json={"workspace_id": workspace_id, "reason": "No worker exists."},
            headers=_headers(),
        )
        clock.advance(seconds=120)
        stale_detail = client.get(
            f"/v1/model-training/training-runs/{training_run_id}?workspace_id={workspace_id}",
            headers=_headers(),
        )
        abandon_response = client.post(
            f"/v1/model-training/training-runs/{training_run_id}/abandon",
            json={"workspace_id": workspace_id, "reason": "No heartbeat after local restart."},
            headers=_headers(),
        )
        adapter.release()

        assert too_early.status_code == 409
        assert too_early.json()["detail"]["code"] == "training_run_not_stale"
        assert stale_detail.status_code == 200
        assert stale_detail.json()["is_stale"] is True
        assert abandon_response.status_code == 200
        assert abandon_response.json()["status"] == "abandoned"
        assert abandon_response.json()["abandon_reason"] == "No heartbeat after local restart."
        assert state.store.active_training_run(UUID(workspace_id)) is None
    finally:
        adapter.release()
        app.dependency_overrides.clear()


def test_dataset_curator_can_force_abandon_cancelling_training_run(tmp_path: Path) -> None:
    state = _build_state(tmp_path)
    adapter = BlockingTrainingAdapter()
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_bee_detector_training_workflow] = lambda: BeeDetectorTrainingWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        artifact_root=state.model_artifact_root,
        adapter=adapter,
        persistence_backend="in_memory",
        database_purpose="dev",
        clock=state.store.clock,
    )
    client = TestClient(app)
    try:
        workspace_id, dataset_version_id = _dataset_version_with_minimum_items(client)
        start_response = client.post(
            "/v1/model-training/training-runs",
            json={
                "workspace_id": workspace_id,
                "dataset_version_id": dataset_version_id,
                "acknowledge_high_severity_warnings": True,
            },
            headers=_headers(),
        )
        training_run_id = start_response.json()["training_run_id"]
        adapter.started.wait(timeout=2)

        cancel_response = client.post(
            f"/v1/model-training/training-runs/{training_run_id}/cancel",
            json={"workspace_id": workspace_id, "reason": "Real adapter did not stop promptly."},
            headers=_headers(),
        )
        abandon_response = client.post(
            f"/v1/model-training/training-runs/{training_run_id}/abandon",
            json={
                "workspace_id": workspace_id,
                "reason": "Clear cancelling local run so the next baseline can start.",
                "force": True,
            },
            headers=_headers(),
        )
        adapter.release()

        assert cancel_response.status_code == 200
        assert cancel_response.json()["status"] == "cancelling"
        assert abandon_response.status_code == 200
        assert abandon_response.json()["status"] == "abandoned"
        assert abandon_response.json()["model_candidate_id"] is None
        assert state.store.active_training_run(UUID(workspace_id)) is None
    finally:
        adapter.release()
        app.dependency_overrides.clear()


def test_dataset_curator_can_delete_unevidenced_active_training_run(tmp_path: Path) -> None:
    state = _build_state(tmp_path)
    adapter = BlockingTrainingAdapter()
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_bee_detector_training_workflow] = lambda: BeeDetectorTrainingWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        artifact_root=state.model_artifact_root,
        adapter=adapter,
        persistence_backend="in_memory",
        database_purpose="dev",
        clock=state.store.clock,
    )
    client = TestClient(app)
    try:
        workspace_id, dataset_version_id = _dataset_version_with_minimum_items(client)
        start_response = client.post(
            "/v1/model-training/training-runs",
            json={
                "workspace_id": workspace_id,
                "dataset_version_id": dataset_version_id,
                "acknowledge_high_severity_warnings": True,
            },
            headers=_headers(),
        )
        training_run_id = start_response.json()["training_run_id"]
        adapter.started.wait(timeout=2)

        delete_response = client.request(
            "DELETE",
            f"/v1/model-training/training-runs/{training_run_id}",
            json={
                "workspace_id": workspace_id,
                "reason": "Delete orphaned local run before any candidate exists.",
                "confirm_no_candidate_or_required_artifacts": True,
            },
            headers=_headers(),
        )
        adapter.release()
        detail = client.get(
            f"/v1/model-training/training-runs/{training_run_id}?workspace_id={workspace_id}",
            headers=_headers(),
        )

        assert delete_response.status_code == 200
        assert delete_response.json()["deleted"] is True
        assert detail.status_code == 404
        assert state.store.active_training_run(UUID(workspace_id)) is None
    finally:
        adapter.release()
        app.dependency_overrides.clear()


class UnavailableRealTrainingAdapter:
    adapter_type = "ultralytics_yolo_obb"

    def check_available(self) -> bool:
        return False

    def run_training(self, **kwargs) -> TrainingAdapterResult:
        raise AssertionError("Unavailable adapter should not be asked to run training.")


class AvailableRealishTrainingAdapter:
    adapter_type = "ultralytics_yolo_obb"

    def check_available(self) -> bool:
        return True

    def run_training(
        self,
        *,
        training_run,
        run_dir: Path,
        dataset_package_dir: Path,
    ) -> TrainingAdapterResult:
        _ = dataset_package_dir
        weights_path = run_dir / "weights" / "best.pt"
        weights_path.parent.mkdir(parents=True, exist_ok=True)
        weights_path.write_text("realish Bee Localisation weights\n", encoding="utf-8")
        log_path = run_dir / "training.log"
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write("Realish Bee Localisation adapter completed.\n")
        return TrainingAdapterResult(
            metrics={"metric_scope": "realish_localisation"},
            model_artifact_path=weights_path,
            log_path=log_path,
            base_weights_source="realish_test",
        )


class AvailableRealishOrientationAdapter:
    adapter_type = "torchvision_orientation_classifier"

    def check_available(self) -> bool:
        return True

    def run_training(
        self,
        *,
        training_run,
        run_dir: Path,
        dataset_package_dir: Path,
        package_result: dict[str, object],
    ) -> TrainingAdapterResult:
        assert (dataset_package_dir / "labels.jsonl").exists()
        weights_path = run_dir / "weights" / "orientation-classifier.pt"
        weights_path.parent.mkdir(parents=True, exist_ok=True)
        weights_path.write_text("realish Bee Orientation weights\n", encoding="utf-8")
        log_path = run_dir / "training.log"
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write("Realish Bee Orientation adapter completed.\n")
        return TrainingAdapterResult(
            metrics={
                "predictive_training_performed": True,
                "metric_scope": "training_run_validation_not_benchmark",
                "architecture": "mobilenet_v3_small",
                "device": "cpu",
                "validation_accuracy": 1.0,
                "confusion_matrix": {
                    "head_up": {"head_up": 4, "head_down": 0},
                    "head_down": {"head_up": 0, "head_down": 4},
                },
                "package_hash": package_result["package_hash"],
            },
            model_artifact_path=weights_path,
            log_path=log_path,
            base_weights_source="torchvision_random_initialisation",
        )


class BlockingTrainingAdapter:
    adapter_type = "fake"

    def __init__(self) -> None:
        self.started = threading.Event()
        self._released = threading.Event()

    def check_available(self) -> bool:
        return True

    def release(self) -> None:
        self._released.set()

    def run_training(
        self,
        *,
        training_run,
        run_dir: Path,
        dataset_package_dir: Path,
    ) -> TrainingAdapterResult:
        _ = dataset_package_dir
        self.started.set()
        self._released.wait(timeout=5)
        weights_path = run_dir / "weights" / "best.pt"
        weights_path.parent.mkdir(parents=True, exist_ok=True)
        weights_path.write_text("blocking fake weights\n", encoding="utf-8")
        log_path = run_dir / "training.log"
        log_path.write_text("Blocking fake adapter released.\n", encoding="utf-8")
        return TrainingAdapterResult(
            metrics={"metric_scope": "blocking_fake"},
            model_artifact_path=weights_path,
            log_path=log_path,
            base_weights_source="blocking_fake_generated",
        )


class MutableClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value

    def advance(self, *, seconds: int) -> None:
        self.value = self.value.replace() + timedelta(seconds=seconds)


def _build_state(tmp_path: Path, clock=None):
    return build_dev_state(
        id_values=[UUID(f"00000000-0000-0000-0000-000000015{i:03d}") for i in range(1, 240)],
        clock=clock or (lambda: datetime(2026, 7, 31, 12, 0, tzinfo=UTC)),
        dataset_export_root=tmp_path / "exports",
        model_artifact_root=tmp_path / "model-runs",
    )


def _dataset_version_with_minimum_items(client: TestClient) -> tuple[str, str]:
    workspace_id = _workspace(client)
    _create_reviewed_crop_item(client, workspace_id, "training", 10, 10)
    _create_reviewed_crop_item(client, workspace_id, "validation", 260, 10)
    response = client.post(
        "/v1/model-training/dataset-versions",
        json={"workspace_id": workspace_id},
        headers=_headers(),
    )
    assert response.status_code == 201
    return workspace_id, response.json()["dataset_version_id"]


def _workspace(client: TestClient) -> str:
    workspace_id = client.get("/v1/dev/session", headers=_headers()).json()["workspace_id"]
    client.post(
        "/v1/workspace-data-use-agreements/acceptances",
        json={"workspace_id": workspace_id, "terms_version": "2026-07-31"},
        headers=_headers(),
    )
    return workspace_id


def _create_reviewed_crop_item(
    client: TestClient,
    workspace_id: str,
    dataset_role: str,
    crop_x: int,
    crop_y: int,
    *,
    annotation_type: str = "complete_visible_bee",
    orientation_reliability: str = "reliable",
) -> str:
    apiary_id = client.post(
        "/v1/apiaries",
        json={"workspace_id": workspace_id, "name": f"Apiary {dataset_role}"},
        headers=_headers(),
    ).json()["apiary_id"]
    hive_id = client.post(
        "/v1/hives",
        json={"apiary_id": apiary_id, "name": f"Hive {dataset_role}"},
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
        content=_source_png(),
        headers={
            **_headers(),
            "content-type": "image/png",
            "x-hivesight-filename": f"{dataset_role}.png",
        },
    )
    inspection_photo_id = intake.json()["inspection_photo"]["inspection_photo_id"]
    crop = client.post(
        "/v1/training-crops",
        json={
            "workspace_id": workspace_id,
            "inspection_photo_id": inspection_photo_id,
            "crop_x": crop_x,
            "crop_y": crop_y,
            "crop_width": 200,
            "crop_height": 200,
            "source_image_width_px": 640,
            "source_image_height_px": 480,
        },
        headers=_headers(),
    ).json()
    ellipse = client.post(
        f"/v1/training-crops/{crop['training_crop_id']}/bee-ellipses",
        json={
            "workspace_id": workspace_id,
            "annotation_type": annotation_type,
            "center_x": crop_x + 80,
            "center_y": crop_y + 80,
            "radius_x": 24,
            "radius_y": 12,
            "rotation_degrees": 15,
            "orientation_reliability": orientation_reliability,
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
    assignment = client.post(
        f"/v1/training-crops/{crop['training_crop_id']}/dataset-item",
        json={
            "workspace_id": workspace_id,
            "dataset_role": dataset_role,
            "source_group_key": f"{dataset_role}-group",
        },
        headers=_headers(),
    )
    assert assignment.status_code == 201
    return crop["training_crop_id"]


def _headers() -> dict[str, str]:
    return {"x-hivesight-dev-user-id": str(CURATOR_ID)}


def _wait_for_training_run_status(
    client: TestClient,
    workspace_id: str,
    training_run_id: str,
    expected_status: str,
) -> dict:
    for _ in range(50):
        response = client.get(
            f"/v1/model-training/training-runs/{training_run_id}?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert response.status_code == 200
        body = response.json()
        if body["status"] == expected_status:
            return body
        time.sleep(0.02)
    raise AssertionError(f"Training Run did not reach {expected_status}.")


def _wait_for_training_run_purpose_status(
    client: TestClient,
    workspace_id: str,
    model_purpose: str,
    expected_status: str,
) -> dict:
    for _ in range(100):
        response = client.get(
            f"/v1/model-training/training-runs?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert response.status_code == 200
        for run in response.json()["training_runs"]:
            if run["model_purpose"] == model_purpose and run["status"] == expected_status:
                return run
        time.sleep(0.03)
    raise AssertionError(f"{model_purpose} Training Run did not reach {expected_status}.")


def _wait_for_benchmark_evaluation_status(
    client: TestClient,
    workspace_id: str,
    benchmark_evaluation_id: str,
    expected_status: str,
) -> dict:
    for _ in range(50):
        response = client.get(
            "/v1/model-training/benchmark-evaluations/"
            f"{benchmark_evaluation_id}?workspace_id={workspace_id}",
            headers=_headers(),
        )
        assert response.status_code == 200
        body = response.json()
        if body["status"] == expected_status:
            return body
        time.sleep(0.02)
    raise AssertionError(f"Benchmark Evaluation did not reach {expected_status}.")


def _source_png() -> bytes:
    image = Image.new("RGB", (640, 480), color=(240, 220, 180))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
