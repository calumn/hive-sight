from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from hive_sight_core_api.models import LikelyVarroaDetectionResponse
from hive_sight_core_api.varroa_review_workflow import (
    DeterministicStubVarroaDetectorAdapter,
    VarroaDetectorFailure,
    VarroaDetectorRequest,
)

LOCAL_COMMAND_CONTRACT_VERSION = "varroa_detector_command_v1"
DEFAULT_VARROA_DETECTOR_TIMEOUT_SECONDS = 5


@dataclass
class LocalCommandVarroaDetectorAdapter:
    command: list[str]
    model_reference: str
    timeout_seconds: int = DEFAULT_VARROA_DETECTOR_TIMEOUT_SECONDS
    adapter_type: str = "local_command"
    adapter_version: str = "local_command_varroa_detector_pending_validation"
    command_contract_version: str = LOCAL_COMMAND_CONTRACT_VERSION
    last_validation_error: str | None = field(default=None, init=False)

    def detect(self, request: VarroaDetectorRequest) -> list[LikelyVarroaDetectionResponse]:
        if not self.command or not _is_runnable(self.command[0]):
            self.last_validation_error = "command_not_available"
            raise VarroaDetectorFailure(
                code="varroa_detector_command_unavailable",
                message="The configured Varroa Detector command is unavailable.",
                raw_error_payload='{"code": "command_not_available"}',
            )

        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as image_file:
            image_file.write(request.head_up_normalized_image_bytes)
            image_file.flush()
            payload = {
                "contract_version": LOCAL_COMMAND_CONTRACT_VERSION,
                "workspace_id": str(request.workspace_id),
                "inspection_photo_id": str(request.inspection_photo_id),
                "training_crop_id": str(request.training_crop_id),
                "bee_annotation_id": str(request.bee_annotation_id),
                "head_up_normalized_image_path": image_file.name,
                "image_width_px": request.image_width_px,
                "image_height_px": request.image_height_px,
                "transform_version": request.transform_version,
                "transform_metadata": request.transform_metadata,
                "source_geometry_snapshot": request.source_geometry_snapshot,
            }
            try:
                completed = subprocess.run(
                    self.command,
                    input=json.dumps(payload),
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                self.last_validation_error = "timeout"
                raise VarroaDetectorFailure(
                    code="adapter_timeout",
                    message="The configured Varroa Detector timed out.",
                    raw_error_payload=_sanitize(error.stderr),
                ) from error
            except OSError as error:
                self.last_validation_error = "command_not_available"
                raise VarroaDetectorFailure(
                    code="varroa_detector_command_unavailable",
                    message="The configured Varroa Detector command is unavailable.",
                    raw_error_payload=_sanitize(str(error)),
                ) from error

        if completed.returncode != 0:
            self.last_validation_error = "non_zero_exit"
            raise VarroaDetectorFailure(
                code="varroa_detector_command_failed",
                message="The configured Varroa Detector command failed.",
                raw_error_payload=_sanitize(completed.stderr or completed.stdout),
            )
        try:
            response = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            self.last_validation_error = "invalid_json"
            raise VarroaDetectorFailure(
                code="varroa_detector_invalid_json",
                message="The configured Varroa Detector returned invalid JSON.",
                raw_error_payload=_sanitize(completed.stdout),
            ) from error

        if response.get("contract_version") != LOCAL_COMMAND_CONTRACT_VERSION:
            self.last_validation_error = "contract_version_mismatch"
            raise VarroaDetectorFailure(
                code="varroa_detector_contract_error",
                message="The Varroa Detector response contract version is missing or unsupported.",
                raw_error_payload=_sanitize(completed.stdout),
            )
        if response.get("status") != "completed":
            self.last_validation_error = str(response.get("failure_code") or "detector_failed")
            raise VarroaDetectorFailure(
                code=str(response.get("failure_code") or "varroa_detector_failed"),
                message=str(response.get("failure_message") or "The Varroa Detector did not complete."),
                raw_error_payload=_sanitize(completed.stdout),
            )
        if not response.get("model_reference"):
            self.last_validation_error = "missing_model_reference"
            raise VarroaDetectorFailure(
                code="varroa_detector_missing_provenance",
                message="The Varroa Detector response did not include model provenance.",
                raw_error_payload=_sanitize(completed.stdout),
            )
        self.adapter_version = str(response.get("adapter_version") or self.adapter_version)
        self.model_reference = str(response["model_reference"])
        try:
            detections = [
                LikelyVarroaDetectionResponse.model_validate(detection)
                for detection in response.get("detections", [])
            ]
        except ValidationError as error:
            self.last_validation_error = "invalid_detection"
            raise VarroaDetectorFailure(
                code="varroa_detector_invalid_detection",
                message="The Varroa Detector returned an invalid detection.",
                raw_error_payload=_sanitize(completed.stdout),
            ) from error
        self.last_validation_error = None
        return detections

    def readiness(self) -> tuple[bool, str | None]:
        if not self.command or not _is_runnable(self.command[0]):
            return False, "command_not_available"
        return True, None


def build_varroa_detector_adapter(
    *,
    adapter_name: str,
    command: str | None,
    model_reference: str | None,
) -> DeterministicStubVarroaDetectorAdapter | LocalCommandVarroaDetectorAdapter:
    if adapter_name == "deterministic_stub":
        return DeterministicStubVarroaDetectorAdapter()
    if adapter_name == "local_command":
        return LocalCommandVarroaDetectorAdapter(
            command=shlex.split(command or ""),
            model_reference=model_reference or "local_command_varroa_detector",
        )
    raise ValueError(f"Unknown HiveSight Varroa Detector adapter: {adapter_name}")


def _is_runnable(command: str) -> bool:
    if not command:
        return False
    if os.path.sep in command:
        return Path(command).is_file() and os.access(command, os.X_OK)
    from shutil import which

    return which(command) is not None


def _sanitize(value: object) -> str | None:
    if value is None:
        return None
    return str(value)[:2000]
