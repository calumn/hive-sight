from pathlib import Path
import shutil
from uuid import UUID

from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    DirectedEllipseLocalCleanupRequest,
    DirectedEllipseLocalCleanupResponse,
    TrainingCropReviewStatus,
)


class DirectedEllipseCleanupWorkflow:
    """One-time local cleanup for the directed bee ellipse orientation transition."""

    def __init__(
        self,
        *,
        store: InMemoryProductDataStore,
        artifact_root: Path,
        database_purpose: str,
    ) -> None:
        self.store = store
        self.artifact_root = artifact_root
        self.database_purpose = database_purpose

    def reset_dataset_and_model_evidence(
        self,
        *,
        user: UserContext,
        request: DirectedEllipseLocalCleanupRequest,
    ) -> DirectedEllipseLocalCleanupResponse:
        self.store.require_workspace_access(user, request.workspace_id)
        self.store.require_data_use_agreement(request.workspace_id)
        self.store.require_dataset_curator_capability(user)
        if self.database_purpose not in {"dev", "test"}:
            raise DomainError(
                "directed_ellipse_cleanup_local_only",
                "Directed ellipse cleanup is only available for local dev or test databases.",
                409,
            )
        if not request.confirm_remove_dataset_and_model_evidence:
            raise DomainError(
                "directed_ellipse_cleanup_confirmation_required",
                "Confirm removal of local Dataset Items, Dataset Versions, Training Runs, Model Candidates, and model artifacts.",
                422,
            )

        artifact_paths_removed = self._remove_artifact_paths(request.workspace_id)
        training_crops_reopened = self._reopen_reviewed_crops_with_ellipses(request.workspace_id)
        removed = self.store.remove_dataset_and_model_evidence_for_workspace(request.workspace_id)

        return DirectedEllipseLocalCleanupResponse(
            workspace_id=request.workspace_id,
            dataset_items_removed=removed["dataset_items_removed"],
            dataset_versions_removed=removed["dataset_versions_removed"],
            training_runs_removed=removed["training_runs_removed"],
            model_candidates_removed=removed["model_candidates_removed"],
            artifacts_removed=removed["artifacts_removed"],
            artifact_paths_removed=artifact_paths_removed,
            training_crops_reopened=training_crops_reopened,
            training_crop_ellipses_preserved=sum(
                1
                for ellipse in self.store.training_crop_ellipses.values()
                if ellipse.workspace_id == request.workspace_id
            ),
            inspection_photos_preserved=sum(
                1
                for photo in self.store.inspection_photos.values()
                if photo.workspace_id == request.workspace_id
            ),
            caveat=(
                "Local reset removed derived dataset/model evidence only. Uploaded photos, "
                "Training Crops, and bee ellipses were preserved for directed head review."
            ),
        )

    def _reopen_reviewed_crops_with_ellipses(self, workspace_id: UUID) -> int:
        crop_ids_with_ellipses = {
            ellipse.training_crop_id
            for ellipse in self.store.training_crop_ellipses.values()
            if ellipse.workspace_id == workspace_id
        }
        reopened = 0
        for crop in list(self.store.training_crops.values()):
            if crop.workspace_id != workspace_id or crop.training_crop_id not in crop_ids_with_ellipses:
                continue
            if crop.review_status == TrainingCropReviewStatus.review_pending:
                continue
            self.store.save_training_crop(
                crop.model_copy(
                    update={
                        "review_status": TrainingCropReviewStatus.review_pending,
                        "exclusion_reason": None,
                        "updated_at": self.store.clock(),
                    }
                )
            )
            reopened += 1
        return reopened

    def _remove_artifact_paths(self, workspace_id: UUID) -> int:
        removed_paths = 0
        for artifact in list(self.store.artifacts.values()):
            if not self._artifact_belongs_to_workspace(artifact.owner_id, workspace_id):
                continue
            path = self._safe_artifact_path(artifact.relative_path)
            if path is None or not path.exists():
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            removed_paths += 1
        for dataset_version in self.store.list_dataset_versions(workspace_id):
            removed_paths += self._remove_safe_child_dir(
                "dataset-versions",
                f"dataset-version-{dataset_version.dataset_version_id}",
            )
        for training_run in self.store.list_training_runs(workspace_id):
            removed_paths += self._remove_safe_child_dir(
                "training-runs",
                f"training-run-{training_run.training_run_id}",
            )
        return removed_paths

    def _artifact_belongs_to_workspace(self, owner_id: UUID, workspace_id: UUID) -> bool:
        dataset_version = self.store.dataset_versions.get(owner_id)
        if dataset_version is not None:
            return dataset_version.workspace_id == workspace_id
        training_run = self.store.training_runs.get(owner_id)
        if training_run is not None:
            return training_run.workspace_id == workspace_id
        return False

    def _safe_artifact_path(self, relative_path: str) -> Path | None:
        if relative_path.startswith("/") or ".." in Path(relative_path).parts:
            return None
        root = self.artifact_root.resolve()
        path = (root / relative_path).resolve()
        if path == root or root not in path.parents:
            return None
        return path

    def _remove_safe_child_dir(self, parent: str, child: str) -> int:
        root = self.artifact_root.resolve()
        path = (root / parent / child).resolve()
        if root not in path.parents or not path.exists():
            return 0
        shutil.rmtree(path)
        return 1
