from dataclasses import dataclass
from datetime import date
from uuid import UUID

from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    FrameStandardResponse,
    FrameStandardStatus,
    HiveConfigurationResponse,
    HiveConfigurationStatus,
    HiveConfigurationUpsertRequest,
    InspectionIntent,
    InspectionResponse,
)


@dataclass(frozen=True)
class HiveConfigurationWorkflow:
    store: InMemoryProductDataStore

    def list_frame_standards(self) -> list[FrameStandardResponse]:
        return self.store.list_frame_standards()

    def upsert_hive_configuration(
        self,
        user: UserContext,
        hive_id: UUID,
        request: HiveConfigurationUpsertRequest,
    ) -> HiveConfigurationResponse:
        hive = self.store.get_hive(hive_id)
        if hive is None or hive.workspace_id != request.workspace_id:
            raise DomainError(
                "hive_not_found",
                "The requested Hive was not found in this Workspace.",
                404,
            )
        self.store.require_workspace_access(user, hive.workspace_id)
        frame_standard = self.store.get_frame_standard(request.frame_standard_id)
        if frame_standard is None:
            raise DomainError(
                "frame_standard_not_found",
                "The requested Frame Standard is not in the HiveSight starter catalogue.",
                422,
            )
        notes = _clean_optional_text(request.notes)
        if frame_standard.status == FrameStandardStatus.other and notes is None:
            raise DomainError(
                "hive_configuration_notes_required",
                "The 'other' Frame Standard requires Hive Configuration notes.",
                422,
            )
        existing = self.store.get_current_hive_configuration(hive_id)
        now = self.store.clock()
        configuration = HiveConfigurationResponse(
            hive_configuration_id=existing.hive_configuration_id if existing else self.store.id_factory(),
            hive_id=hive_id,
            workspace_id=hive.workspace_id,
            hive_type=frame_standard.hive_type,
            frame_use=frame_standard.frame_use,
            frame_standard_id=frame_standard.frame_standard_id,
            frame_standard=frame_standard,
            brood_slot_count=request.brood_slot_count or 10,
            notes=notes,
            status=HiveConfigurationStatus.current,
            effective_from=request.effective_from or now.date(),
            configured_by_user_id=user.user_id,
            configured_at=existing.configured_at if existing else now,
            updated_at=now,
        )
        self.store.save_hive_configuration(configuration)
        return configuration

    def get_hive_configuration(
        self,
        user: UserContext,
        workspace_id: UUID,
        hive_id: UUID,
    ) -> HiveConfigurationResponse:
        hive = self.store.get_hive(hive_id)
        if hive is None or hive.workspace_id != workspace_id:
            raise DomainError(
                "hive_not_found",
                "The requested Hive was not found in this Workspace.",
                404,
            )
        self.store.require_workspace_access(user, workspace_id)
        configuration = self.store.get_current_hive_configuration(hive_id)
        if configuration is None:
            raise DomainError(
                "hive_configuration_required",
                "Record Hive Configuration before using this Hive for Inspections.",
                409,
            )
        return configuration

    def create_inspection(
        self,
        user: UserContext,
        hive_id: UUID,
        inspection_date: date,
        intent: InspectionIntent,
    ) -> InspectionResponse:
        hive = self.store.get_hive(hive_id)
        if hive is None:
            raise DomainError("inspection_not_found", "The requested hive was not found.", 404)
        self.store.require_workspace_access(user, hive.workspace_id)
        if self.store.get_current_hive_configuration(hive_id) is None:
            raise DomainError(
                "hive_configuration_required",
                "Record Hive Configuration before creating an Inspection for this Hive.",
                409,
            )
        if intent == InspectionIntent.training_data_collection:
            self.store.require_dataset_curator_capability(user)
        inspection = InspectionResponse(
            inspection_id=self.store.id_factory(),
            hive_id=hive_id,
            workspace_id=hive.workspace_id,
            inspection_date=inspection_date,
            intent=intent,
        )
        self.store.save_inspection(inspection)
        self.store.initialize_inspection_frame_observations(inspection)
        return inspection

    def update_inspection_intent(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_id: UUID,
        intent: InspectionIntent,
    ) -> InspectionResponse:
        self.store.require_workspace_access(user, workspace_id)
        inspection = self.store.require_inspection(workspace_id, inspection_id)
        if intent == InspectionIntent.training_data_collection:
            self.store.require_dataset_curator_capability(user)
        if self.store.inspection_has_photos(inspection_id):
            raise DomainError(
                "inspection_intent_locked",
                "Inspection intent cannot be changed after photos have been uploaded.",
                409,
            )
        updated = inspection.model_copy(update={"intent": intent})
        self.store.save_inspection(updated)
        return updated


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
