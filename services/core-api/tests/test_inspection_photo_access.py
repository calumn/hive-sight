from uuid import UUID

from beehive_core_api.inspection_photo_access import InspectionPhotoAccess


def test_create_upload_access_returns_scoped_short_lived_upload_url() -> None:
    inspection_photo_id = UUID("00000000-0000-0000-0000-000000000123")
    photo_access = InspectionPhotoAccess(
        object_storage_endpoint="http://localhost:9000",
        object_storage_bucket="beehive-monitor-local",
    )

    response = photo_access.create_upload_access(inspection_photo_id)

    assert response.inspection_photo_id == inspection_photo_id
    assert response.method == "PUT"
    assert response.expires_in_seconds == 900
    assert response.object_key == f"inspection-photos/{inspection_photo_id}/original.jpg"
    assert response.upload_url == (
        "http://localhost:9000/beehive-monitor-local/"
        f"inspection-photos/{inspection_photo_id}/original.jpg"
    )

