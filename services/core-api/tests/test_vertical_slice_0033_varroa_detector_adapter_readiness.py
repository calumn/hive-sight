import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from test_vertical_slice_0025_varroa_review_slice import _completed_crop_with_two_bees, _headers

from hive_sight_core_api.dependencies import (
    build_dev_state,
    get_dev_state,
    get_settings,
    get_varroa_review_workflow,
)
from hive_sight_core_api.main import app
from hive_sight_core_api.varroa_detector_adapters import (
    LOCAL_COMMAND_CONTRACT_VERSION,
    LocalCommandVarroaDetectorAdapter,
)
from hive_sight_core_api.varroa_review_workflow import VarroaDetectorFailure, VarroaReviewWorkflow


def test_local_command_adapter_uses_versioned_stdin_stdout_contract(tmp_path: Path):
    command = _write_command(
        tmp_path,
        """
import json
import sys

request = json.loads(sys.stdin.read())
assert request["contract_version"] == "varroa_detector_command_v1"
assert request["head_up_normalized_image_path"]
print(json.dumps({
    "contract_version": "varroa_detector_command_v1",
    "status": "completed",
    "adapter_version": "fake-command-v1",
    "model_reference": "fake-model",
    "answer_id": "answer-123",
    "detections": [{
        "detection_id": "mite-1",
        "x": 0.5,
        "y": 0.4,
        "width": 0.06,
        "height": 0.05,
        "confidence": 0.88,
        "coordinate_space": "head_up_normalized_crop",
        "source": "local_command"
    }]
}))
""",
    )
    adapter = LocalCommandVarroaDetectorAdapter(
        command=[sys.executable, str(command)],
        model_reference="fake-model",
        timeout_seconds=2,
    )
    request = _detector_request()

    detections = adapter.detect(request)

    assert adapter.adapter_type == "local_command"
    assert adapter.command_contract_version == LOCAL_COMMAND_CONTRACT_VERSION
    assert adapter.adapter_version == "fake-command-v1"
    assert adapter.model_reference == "fake-model"
    assert len(detections) == 1
    assert detections[0].source == "local_command"


def test_local_command_adapter_rejects_missing_contract_version(tmp_path: Path):
    command = _write_command(
        tmp_path,
        """
import json
print(json.dumps({"status": "completed", "detections": []}))
""",
    )
    adapter = LocalCommandVarroaDetectorAdapter(
        command=[sys.executable, str(command)],
        model_reference="fake-model",
        timeout_seconds=2,
    )

    try:
        adapter.detect(_detector_request())
    except VarroaDetectorFailure as error:
        assert error.code == "varroa_detector_contract_error"
    else:
        raise AssertionError("Missing contract version should fail the detector call.")


def test_local_command_adapter_rejects_invalid_detection_coordinates(tmp_path: Path):
    command = _write_command(
        tmp_path,
        """
import json
print(json.dumps({
    "contract_version": "varroa_detector_command_v1",
    "status": "completed",
    "adapter_version": "fake-command-v1",
    "model_reference": "fake-model",
    "detections": [{
        "detection_id": "bad-mite",
        "x": 1.5,
        "y": 0.4,
        "width": 0.06,
        "height": 0.05,
        "confidence": 0.88,
        "coordinate_space": "head_up_normalized_crop",
        "source": "local_command"
    }]
}))
""",
    )
    adapter = LocalCommandVarroaDetectorAdapter(
        command=[sys.executable, str(command)],
        model_reference="fake-model",
        timeout_seconds=2,
    )

    try:
        adapter.detect(_detector_request())
    except VarroaDetectorFailure as error:
        assert error.code == "varroa_detector_invalid_detection"
        assert error.raw_error_payload is not None
    else:
        raise AssertionError("Invalid detections should fail the whole bee detector call.")


def test_readiness_exposes_sanitized_adapter_status(monkeypatch, tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    missing_command = tmp_path / "missing-varroa-detector"
    monkeypatch.setenv("HIVESIGHT_VARROA_DETECTOR_ADAPTER", "local_command")
    monkeypatch.setenv("HIVESIGHT_VARROA_DETECTOR_COMMAND", str(missing_command))
    monkeypatch.setenv("HIVESIGHT_VARROA_DETECTOR_MODEL_REFERENCE", "fake-model")
    get_settings.cache_clear()
    app.dependency_overrides[get_dev_state] = lambda: state
    client = TestClient(app)
    try:
        response = client.get("/v1/model-runtime/varroa-detector/readiness", headers=_headers())

        assert response.status_code == 200
        body = response.json()
        assert body["adapter_type"] == "local_command"
        assert body["available"] is False
        assert body["replaceable_non_stub_adapter"] is True
        assert str(missing_command) not in json.dumps(body)
        assert "command_not_available" in body["unavailable_reason"]
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()


def test_configured_unavailable_local_command_does_not_fall_back_to_stub(monkeypatch, tmp_path: Path):
    state = build_dev_state(dataset_export_root=tmp_path / "exports")
    missing_command = tmp_path / "missing-varroa-detector"
    monkeypatch.setenv("HIVESIGHT_VARROA_DETECTOR_ADAPTER", "local_command")
    monkeypatch.setenv("HIVESIGHT_VARROA_DETECTOR_COMMAND", str(missing_command))
    monkeypatch.setenv("HIVESIGHT_VARROA_DETECTOR_MODEL_REFERENCE", "fake-model")
    get_settings.cache_clear()
    app.dependency_overrides[get_dev_state] = lambda: state
    app.dependency_overrides[get_varroa_review_workflow] = lambda: VarroaReviewWorkflow(
        store=state.store,
        image_loader=state.object_storage.get_object,
        varroa_detector_adapter=LocalCommandVarroaDetectorAdapter(
            command=[str(missing_command)],
            model_reference="fake-model",
            timeout_seconds=1,
        ),
    )
    client = TestClient(app)
    try:
        workspace_id, crop_id, bee_annotation_id, _ = _completed_crop_with_two_bees(client)
        response = client.post(
            f"/v1/training-crops/{crop_id}/varroa-review-candidates/"
            f"{bee_annotation_id}/detector-preview",
            json={"workspace_id": workspace_id},
            headers=_headers(),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "failed"
        assert body["adapter_type"] == "local_command"
        assert body["failure_code"] == "varroa_detector_command_unavailable"
        assert body["detections"] == []
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()


def _write_command(tmp_path: Path, body: str) -> Path:
    command = tmp_path / "fake_varroa_detector.py"
    command.write_text(body.strip() + "\n", encoding="utf-8")
    return command


def _detector_request():
    from hive_sight_core_api.varroa_review_workflow import VarroaDetectorRequest

    return VarroaDetectorRequest(
        workspace_id="00000000-0000-0000-0000-000000000001",
        inspection_photo_id="00000000-0000-0000-0000-000000000002",
        training_crop_id="00000000-0000-0000-0000-000000000003",
        bee_annotation_id="00000000-0000-0000-0000-000000000004",
        head_up_normalized_image_bytes=_minimal_png(),
        image_width_px=1,
        image_height_px=1,
        transform_version="head_up_normalized_bee_crop_v1",
        transform_metadata={},
        source_geometry_snapshot={},
    )


def _minimal_png() -> bytes:
    return (
        b"\\x89PNG\\r\\n\\x1a\\n"
        b"\\x00\\x00\\x00\\rIHDR"
        b"\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x01\\x08\\x02\\x00\\x00\\x00"
        b"\\x90wS\\xde"
        b"\\x00\\x00\\x00\\x00IEND\\xaeB`\\x82"
    )
