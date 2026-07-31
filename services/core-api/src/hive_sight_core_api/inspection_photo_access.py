from dataclasses import dataclass, field
from hashlib import sha256
from io import BytesIO
from struct import unpack
from uuid import UUID, uuid4

from hive_sight_core_api.analysis_request_workflow import AnalysisRequestWorkflow
from hive_sight_core_api.dev_store import (
    DomainError,
    InMemoryObjectStorage,
    InMemoryProductDataStore,
    UploadPolicy,
    UserContext,
)
from hive_sight_core_api.models import AnalysisRunRequest, PhotoIntakeResponse


@dataclass(frozen=True)
class InspectionPhotoAccess:
    object_storage_endpoint: str
    object_storage_bucket: str
    store: InMemoryProductDataStore | None = None
    object_storage: InMemoryObjectStorage | None = None
    analysis_workflow: AnalysisRequestWorkflow | None = None
    upload_policy: UploadPolicy = field(default_factory=UploadPolicy)
    def accept_photo_for_analysis(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_id: UUID,
        filename: str,
        content_type: str,
        body: bytes,
    ) -> PhotoIntakeResponse:
        if self.store is None or self.object_storage is None or self.analysis_workflow is None:
            raise DomainError(
                "upload_storage_failed",
                "Inspection photo intake is not configured.",
                500,
            )

        self.store.require_workspace_access(user, workspace_id)
        self.store.require_data_use_agreement(workspace_id)
        inspection = self.store.require_inspection(workspace_id, inspection_id)
        self._validate_upload(content_type=content_type, size_bytes=len(body))
        source_width_px, source_height_px = _read_image_dimensions(body)

        inspection_photo_id = uuid4()
        object_key = self._object_key(
            workspace_id=workspace_id,
            inspection_id=inspection.inspection_id,
            inspection_photo_id=inspection_photo_id,
            filename=filename,
        )
        self.object_storage.put_object(object_key, body)
        inspection_photo = self.store.record_inspection_photo(
            inspection_photo_id=inspection_photo_id,
            workspace_id=workspace_id,
            inspection_id=inspection.inspection_id,
            original_object_key=object_key,
            filename=filename,
            content_type=content_type,
            size_bytes=len(body),
            uploaded_by_user_id=user.user_id,
            source_image_width_px=source_width_px,
            source_image_height_px=source_height_px,
            content_hash=sha256(body).hexdigest(),
            content_hash_algorithm="sha256",
        )
        analysis_run = self.analysis_workflow.request_analysis(
            AnalysisRunRequest(
                workspace_id=workspace_id,
                inspection_photo_id=inspection_photo.inspection_photo_id,
                original_object_key=inspection_photo.original_object_key,
            )
        )
        return PhotoIntakeResponse(inspection_photo=inspection_photo, analysis_run=analysis_run)

    def _validate_upload(self, content_type: str, size_bytes: int) -> None:
        if content_type not in self.upload_policy.allowed_content_types:
            raise DomainError(
                "unsupported_content_type",
                "Upload an inspection photo as JPEG, PNG, or WebP.",
                415,
            )
        if size_bytes > self.upload_policy.max_size_bytes:
            raise DomainError(
                "file_too_large",
                "The inspection photo is larger than the configured upload limit.",
                413,
            )

    def _object_key(
        self,
        workspace_id: UUID,
        inspection_id: UUID,
        inspection_photo_id: UUID,
        filename: str,
    ) -> str:
        extension = "jpg"
        if "." in filename:
            extension = filename.rsplit(".", maxsplit=1)[-1].lower()
        return (
            f"workspaces/{workspace_id}/inspections/{inspection_id}/"
            f"inspection-photos/{inspection_photo_id}/original.{extension}"
        )


def _read_image_dimensions(body: bytes) -> tuple[int, int]:
    if body.startswith(b"\x89PNG\r\n\x1a\n") and len(body) >= 24:
        return unpack(">II", body[16:24])
    try:
        from PIL import Image

        with Image.open(BytesIO(body)) as image:
            return image.width, image.height
    except (ImportError, OSError, ValueError):
        return 1, 1
