from collections import Counter, defaultdict
from collections.abc import Callable
from uuid import UUID

from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    AnnotationType,
    DatasetRepositoryItemDetail,
    DatasetRepositoryItemListEntry,
    DatasetRepositoryItemListResponse,
    DatasetRepositoryLatestVersionSummary,
    DatasetRepositorySummaryResponse,
    DatasetRepositoryWarningResponse,
    DatasetRole,
    DatasetVersionMembershipResponse,
    DatasetVersionResponse,
    InspectionIntent,
)


class DatasetRepositoryWorkflow:
    def __init__(
        self,
        *,
        store: InMemoryProductDataStore,
        image_loader: Callable[[str], bytes | None],
        persistence_backend: str,
        database_purpose: str,
    ) -> None:
        self.store = store
        self.image_loader = image_loader
        self.persistence_backend = persistence_backend
        self.database_purpose = database_purpose

    def summary(self, *, user: UserContext, workspace_id: UUID) -> DatasetRepositorySummaryResponse:
        self._require_curator(user=user, workspace_id=workspace_id)
        items = self._active_items(workspace_id)
        entries = self._entries(workspace_id=workspace_id, items=items)
        return self._summary(workspace_id=workspace_id, entries=entries)

    def list_items(
        self,
        *,
        user: UserContext,
        workspace_id: UUID,
        dataset_role: DatasetRole | None = None,
    ) -> DatasetRepositoryItemListResponse:
        self._require_curator(user=user, workspace_id=workspace_id)
        items = self._active_items(workspace_id)
        entries = self._entries(workspace_id=workspace_id, items=items)
        if dataset_role is not None:
            entries = [entry for entry in entries if entry.dataset_role == dataset_role]
        entries = sorted(
            entries,
            key=lambda entry: (_role_order(entry.dataset_role), -entry.assigned_at.timestamp()),
        )
        return DatasetRepositoryItemListResponse(
            summary=self._summary(workspace_id=workspace_id, entries=self._entries(workspace_id=workspace_id, items=items)),
            items=entries,
        )

    def detail(
        self,
        *,
        user: UserContext,
        workspace_id: UUID,
        dataset_item_id: UUID,
    ) -> DatasetRepositoryItemDetail:
        self._require_curator(user=user, workspace_id=workspace_id)
        item = self.store.dataset_items.get(dataset_item_id)
        if item is None or item.workspace_id != workspace_id:
            raise DomainError("dataset_item_not_found", "Dataset Item not found.", 404)
        entry = self._entry(workspace_id=workspace_id, item=item, human_readable_id=self._human_id(item))
        return DatasetRepositoryItemDetail(
            **entry.model_dump(),
            reviewed_ellipse_snapshots=item.reviewed_ellipse_snapshots,
            provenance=item.provenance,
            permission_status=item.permission_status,
            preview_url=entry.thumbnail_url,
        )

    def _require_curator(self, *, user: UserContext, workspace_id: UUID) -> None:
        self.store.require_workspace_access(user, workspace_id)
        self.store.require_dataset_curator_capability(user)
        self.store.require_data_use_agreement(workspace_id)

    def _active_items(self, workspace_id: UUID):
        return [
            item
            for item in self.store.dataset_items.values()
            if item.workspace_id == workspace_id
        ]

    def _entries(self, *, workspace_id: UUID, items) -> list[DatasetRepositoryItemListEntry]:
        return [
            self._entry(workspace_id=workspace_id, item=item, human_readable_id=self._human_id(item))
            for item in items
        ]

    def _entry(self, *, workspace_id: UUID, item, human_readable_id: str) -> DatasetRepositoryItemListEntry:
        photo = self.store.inspection_photos.get(item.inspection_photo_id)
        inspection = self.store.inspections.get(photo.inspection_id) if photo else None
        hive = self.store.hives.get(inspection.hive_id) if inspection else None
        apiary = self.store.apiaries.get(hive.apiary_id) if hive else None
        hive_snapshot = item.provenance.hive_configuration if item.provenance else None
        memberships = self._memberships(workspace_id=workspace_id, dataset_item_id=item.dataset_item_id)
        latest = self._latest_membership(memberships)
        thumbnail_url = (
            f"/v1/inspection-photos/{item.inspection_photo_id}/content?workspace_id={workspace_id}"
            if photo is not None
            else None
        )
        preview_status = "available" if photo and self.image_loader(photo.original_object_key) is not None else "unavailable"
        source_counts = Counter(ellipse.source for ellipse in item.reviewed_ellipse_snapshots)
        review_counts = Counter(
            str(ellipse.review_method or ("human_from_scratch" if ellipse.source == "human_from_scratch" else ellipse.source))
            for ellipse in item.reviewed_ellipse_snapshots
        )
        complete_count = sum(
            1
            for ellipse in item.reviewed_ellipse_snapshots
            if ellipse.annotation_type == AnnotationType.complete_visible_bee
        )
        partial_count = sum(
            1
            for ellipse in item.reviewed_ellipse_snapshots
            if ellipse.annotation_type == AnnotationType.partial_visible_bee
        )
        return DatasetRepositoryItemListEntry(
            dataset_item_id=item.dataset_item_id,
            human_readable_id=human_readable_id,
            workspace_id=item.workspace_id,
            dataset_role=item.dataset_role,
            source_evidence_type=item.source_evidence_type,
            inspection_id=inspection.inspection_id if inspection else None,
            inspection_date=inspection.inspection_date if inspection else None,
            inspection_intent=inspection.intent if inspection else None,
            inspection_photo_id=item.inspection_photo_id,
            source_image_id=item.inspection_photo_id,
            source_filename=photo.filename if photo else None,
            apiary_id=apiary.apiary_id if apiary else None,
            apiary_name=apiary.name if apiary else None,
            hive_id=hive.hive_id if hive else None,
            hive_name=hive.name if hive else None,
            hive_configuration_summary=hive_snapshot.frame_standard_display_name if hive_snapshot else None,
            training_crop_id=item.training_crop_id,
            crop_x=item.crop_x,
            crop_y=item.crop_y,
            crop_width=item.crop_width,
            crop_height=item.crop_height,
            crop_image_width_px=item.crop_image_width_px,
            crop_image_height_px=item.crop_image_height_px,
            curriculum_stage=item.curriculum_stage,
            complete_visible_bee_count=complete_count,
            partial_visible_bee_count=partial_count,
            annotation_source_counts=dict(source_counts),
            review_method_counts=dict(review_counts),
            source_group_key=item.source_group_key,
            image_quality_status=item.image_quality_status,
            assigned_by_user_id=item.assigned_by_user_id,
            assigned_at=item.assigned_at,
            assignment_note=item.assignment_note,
            exclusion_reason=item.exclusion_reason,
            benchmark_protected=item.benchmark_protected,
            export_eligibility=self._export_eligibility(item, preview_status),
            latest_dataset_version_membership=latest,
            dataset_version_memberships=memberships,
            is_new_since_latest_dataset_version=latest is None or latest.membership == "not_in_version",
            preview_status=preview_status,
            thumbnail_url=thumbnail_url,
        )

    def _summary(
        self,
        *,
        workspace_id: UUID,
        entries: list[DatasetRepositoryItemListEntry],
    ) -> DatasetRepositorySummaryResponse:
        role_counts = Counter(str(entry.dataset_role) for entry in entries)
        class_counts: Counter[str] = Counter()
        source_counts: Counter[str] = Counter()
        review_counts: Counter[str] = Counter()
        curriculum_counts = Counter(entry.curriculum_stage or "unknown" for entry in entries)
        quality_counts = Counter(str(entry.image_quality_status) for entry in entries)
        hive_config_counts = Counter(entry.hive_configuration_summary or "unknown" for entry in entries)
        source_group_counts = Counter(entry.source_group_key or "unknown" for entry in entries)
        inspection_counts = Counter(
            str(entry.inspection_id) if entry.inspection_id else "unknown" for entry in entries
        )
        intent_counts = Counter(
            str(entry.inspection_intent) if entry.inspection_intent else "unknown" for entry in entries
        )
        hive_counts = Counter(str(entry.hive_id) if entry.hive_id else "unknown" for entry in entries)
        source_image_counts = Counter(str(entry.source_image_id) for entry in entries)

        for entry in entries:
            class_counts["complete_visible_bee"] += entry.complete_visible_bee_count
            class_counts["partial_visible_bee"] += entry.partial_visible_bee_count
            source_counts.update(entry.annotation_source_counts)
            review_counts.update(entry.review_method_counts)

        latest_version = self._latest_dataset_version(workspace_id)
        return DatasetRepositorySummaryResponse(
            workspace_id=workspace_id,
            dataset_item_count=len(entries),
            active_dataset_item_count=len(entries),
            unassigned_completed_crop_count=self._unassigned_completed_crop_count(workspace_id),
            new_since_latest_dataset_version_count=sum(
                1 for entry in entries if entry.is_new_since_latest_dataset_version
            ),
            role_counts={role.value: role_counts[role.value] for role in DatasetRole},
            annotation_class_counts=dict(class_counts),
            annotation_source_counts=dict(source_counts),
            review_method_counts=dict(review_counts),
            curriculum_stage_distribution=dict(curriculum_counts),
            image_quality_distribution=dict(quality_counts),
            hive_configuration_distribution=dict(hive_config_counts),
            source_group_distribution=dict(source_group_counts),
            inspection_distribution=dict(inspection_counts),
            inspection_intent_distribution=dict(intent_counts),
            hive_distribution=dict(hive_counts),
            source_image_distribution=dict(source_image_counts),
            latest_dataset_version=(
                DatasetRepositoryLatestVersionSummary(
                    dataset_version_id=latest_version.dataset_version_id,
                    human_readable_id=latest_version.human_readable_id,
                    status=latest_version.status,
                    created_at=latest_version.created_at,
                    training_item_count=latest_version.training_item_count,
                    validation_item_count=latest_version.validation_item_count,
                    benchmark_item_count=latest_version.benchmark_item_count,
                    excluded_item_count=latest_version.excluded_item_count,
                )
                if latest_version
                else None
            ),
            persistence_backend=self.persistence_backend,
            database_purpose=self.database_purpose,
            warnings=self._warnings(entries),
        )

    def _memberships(
        self,
        *,
        workspace_id: UUID,
        dataset_item_id: UUID,
    ) -> list[DatasetVersionMembershipResponse]:
        memberships: list[DatasetVersionMembershipResponse] = []
        for version in self.store.list_dataset_versions(workspace_id):
            memberships.append(
                DatasetVersionMembershipResponse(
                    dataset_version_id=version.dataset_version_id,
                    human_readable_id=version.human_readable_id,
                    purpose=version.purpose,
                    status=version.status,
                    membership=_membership_for_version(version, dataset_item_id),
                    excluded_reason=_excluded_reason_for_version(version, dataset_item_id),
                    created_at=version.created_at,
                )
            )
        return memberships

    def _latest_membership(
        self,
        memberships: list[DatasetVersionMembershipResponse],
    ) -> DatasetVersionMembershipResponse | None:
        if not memberships:
            return None
        return memberships[0]

    def _latest_dataset_version(self, workspace_id: UUID) -> DatasetVersionResponse | None:
        return next(iter(self.store.list_dataset_versions(workspace_id)), None)

    def _unassigned_completed_crop_count(self, workspace_id: UUID) -> int:
        assigned_crop_ids = {
            item.training_crop_id
            for item in self.store.dataset_items.values()
            if item.workspace_id == workspace_id and item.training_crop_id is not None
        }
        return sum(
            1
            for crop in self.store.training_crops.values()
            if crop.workspace_id == workspace_id
            and crop.review_status == "review_complete"
            and crop.training_crop_id not in assigned_crop_ids
        )

    def _human_id(self, item) -> str:
        ordered_ids = [
            candidate.dataset_item_id
            for candidate in sorted(
                self.store.dataset_items.values(),
                key=lambda candidate: (candidate.assigned_at, str(candidate.dataset_item_id)),
            )
        ]
        try:
            index = ordered_ids.index(item.dataset_item_id) + 1
        except ValueError:
            index = 0
        return f"HS-DI-{index:06d}" if index else str(item.dataset_item_id)

    def _export_eligibility(self, item, preview_status: str) -> str:
        if preview_status != "available":
            return "not_exportable_image_unavailable"
        if item.dataset_role == DatasetRole.training:
            return "eligible_for_training_export"
        if item.dataset_role == DatasetRole.validation:
            return "validation_export"
        if item.dataset_role == DatasetRole.benchmark:
            return "protected_benchmark"
        return "excluded"

    def _warnings(
        self,
        entries: list[DatasetRepositoryItemListEntry],
    ) -> list[DatasetRepositoryWarningResponse]:
        warnings: list[DatasetRepositoryWarningResponse] = []
        if not any(entry.dataset_role == DatasetRole.benchmark for entry in entries):
            warnings.append(_warning("NO_BENCHMARK_ITEMS", "No benchmark Dataset Items yet."))
        if sum(1 for entry in entries if entry.dataset_role == DatasetRole.validation) < 2:
            warnings.append(_warning("SMALL_VALIDATION_SET", "Validation set is small."))
        for code, label, values in (
            ("ONE_INSPECTION", "Inspection", [entry.inspection_id for entry in entries if entry.inspection_id]),
            ("ONE_HIVE", "Hive", [entry.hive_id for entry in entries if entry.hive_id]),
            ("ONE_SOURCE_IMAGE", "Source Image", [entry.source_image_id for entry in entries]),
        ):
            if entries and len(set(values)) == 1:
                warnings.append(_warning(code, f"All Dataset Items come from one {label}."))
        if any(entry.inspection_intent != InspectionIntent.training_data_collection for entry in entries):
            warnings.append(
                _warning(
                    "NON_TRAINING_INSPECTION_INTENT",
                    "Active Dataset Items include non-Training Data Collection Inspection Intent.",
                )
            )
        if any(entry.preview_status != "available" for entry in entries):
            warnings.append(_warning("IMAGE_PREVIEW_UNAVAILABLE", "Some Dataset Item previews are unavailable."))
        warnings.extend(_leakage_warnings(entries))
        return warnings


def _membership_for_version(version: DatasetVersionResponse, dataset_item_id: UUID) -> str:
    if dataset_item_id in version.training_dataset_item_ids:
        return "training"
    if dataset_item_id in version.validation_dataset_item_ids:
        return "validation"
    if dataset_item_id in version.protected_benchmark_dataset_item_ids:
        return "protected_benchmark"
    if any(item.dataset_item_id == dataset_item_id for item in version.excluded_dataset_items):
        return "excluded"
    if dataset_item_id in version.included_dataset_item_ids:
        return "included"
    return "not_in_version"


def _excluded_reason_for_version(version: DatasetVersionResponse, dataset_item_id: UUID) -> str | None:
    for item in version.excluded_dataset_items:
        if item.dataset_item_id == dataset_item_id:
            return item.reason
    return None


def _warning(code: str, message: str) -> DatasetRepositoryWarningResponse:
    return DatasetRepositoryWarningResponse(code=code, severity="warning", message=message)


def _leakage_warnings(
    entries: list[DatasetRepositoryItemListEntry],
) -> list[DatasetRepositoryWarningResponse]:
    warnings: list[DatasetRepositoryWarningResponse] = []
    roles_by_source: dict[UUID, set[DatasetRole]] = defaultdict(set)
    for entry in entries:
        roles_by_source[entry.source_image_id].add(entry.dataset_role)
    if any({DatasetRole.training, DatasetRole.validation}.issubset(roles) for roles in roles_by_source.values()):
        warnings.append(_warning("TRAINING_VALIDATION_SHARE_SOURCE", "Training and validation share a Source Image."))
    if any(
        DatasetRole.benchmark in roles
        and bool({DatasetRole.training, DatasetRole.validation}.intersection(roles))
        for roles in roles_by_source.values()
    ):
        warnings.append(_warning("BENCHMARK_SOURCE_CONFLICT", "Benchmark shares Source Image with train/validation."))
    return warnings


def _role_order(role: DatasetRole) -> int:
    return {
        DatasetRole.training: 0,
        DatasetRole.validation: 1,
        DatasetRole.benchmark: 2,
        DatasetRole.excluded: 3,
    }[role]
