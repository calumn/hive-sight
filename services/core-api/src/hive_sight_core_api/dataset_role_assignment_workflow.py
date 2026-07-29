from dataclasses import dataclass
from uuid import UUID

from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    DatasetExclusionReason,
    DatasetItemResponse,
    DatasetRole,
)


@dataclass(frozen=True)
class DatasetRoleAssignmentWorkflow:
    store: InMemoryProductDataStore

    def create_dataset_item(
        self,
        user: UserContext,
        workspace_id: UUID,
        labelling_session_id: UUID,
        dataset_role: DatasetRole,
        assignment_note: str | None,
        exclusion_reason: DatasetExclusionReason | None,
    ) -> DatasetItemResponse:
        self.store.require_labelling_session(
            user=user,
            workspace_id=workspace_id,
            labelling_session_id=labelling_session_id,
        )
        cleaned_note = assignment_note.strip() if assignment_note else None
        cleaned_note = cleaned_note or None
        self._validate_exclusion(
            dataset_role=dataset_role,
            assignment_note=cleaned_note,
            exclusion_reason=exclusion_reason,
        )
        reviewed_annotation_ids = [
            annotation.annotation_id
            for annotation in self.store.get_annotations_for_labelling_session(
                labelling_session_id
            )
            if annotation.latest_review_decision is not None
            and annotation.latest_review_decision.decision == "approved"
        ]
        if not reviewed_annotation_ids:
            raise DomainError(
                "reviewed_annotations_required",
                "Assign Dataset Role after at least one Draft Annotation has been reviewed.",
                409,
            )
        return self.store.record_dataset_item(
            user=user,
            workspace_id=workspace_id,
            labelling_session_id=labelling_session_id,
            dataset_role=dataset_role,
            reviewed_annotation_ids=reviewed_annotation_ids,
            assignment_note=cleaned_note,
            exclusion_reason=exclusion_reason,
        )

    def _validate_exclusion(
        self,
        dataset_role: DatasetRole,
        assignment_note: str | None,
        exclusion_reason: DatasetExclusionReason | None,
    ) -> None:
        if dataset_role == DatasetRole.excluded and exclusion_reason is None:
            raise DomainError(
                "exclusion_reason_required",
                "Excluded Dataset Items require an exclusion reason.",
                422,
            )
        if dataset_role != DatasetRole.excluded and exclusion_reason is not None:
            raise DomainError(
                "exclusion_reason_not_allowed",
                "Only excluded Dataset Items may carry an exclusion reason.",
                422,
            )
        if exclusion_reason == DatasetExclusionReason.other and assignment_note is None:
            raise DomainError(
                "assignment_note_required",
                "The 'other' exclusion reason requires an assignment note.",
                422,
            )
