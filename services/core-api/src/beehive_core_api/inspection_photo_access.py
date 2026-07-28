from dataclasses import dataclass
from uuid import UUID

from beehive_core_api.models import UploadUrlResponse


@dataclass(frozen=True)
class InspectionPhotoAccess:
    object_storage_endpoint: str
    object_storage_bucket: str
    upload_url_expires_in_seconds: int = 900

    def create_upload_access(self, inspection_photo_id: UUID) -> UploadUrlResponse:
        object_key = f"inspection-photos/{inspection_photo_id}/original.jpg"

        return UploadUrlResponse(
            inspection_photo_id=inspection_photo_id,
            upload_url=f"{self.object_storage_endpoint}/{self.object_storage_bucket}/{object_key}",
            object_key=object_key,
            expires_in_seconds=self.upload_url_expires_in_seconds,
        )

