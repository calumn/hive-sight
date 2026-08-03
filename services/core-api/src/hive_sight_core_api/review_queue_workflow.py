from dataclasses import dataclass
from uuid import UUID

from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    AnnotationType,
    ReviewQueueEllipseEvidence,
    ReviewQueueEvidenceSnapshot,
    ReviewQueueItemCancelRequest,
    ReviewQueueItemCreateRequest,
    ReviewQueueItemListResponse,
    ReviewQueueItemRecord,
    ReviewQueueItemResponse,
    ReviewQueueItemStatus,
    ReviewQueueOutcomeCreateRequest,
    ReviewQueueOutcomeRecord,
    ReviewQueueOutcomeValue,
    ReviewQueueSubjectType,
    TrainingCropReviewStatus,
    VisibleBeeStatus,
)


@dataclass(frozen=True)
class ReviewQueueWorkflow:
    store: InMemoryProductDataStore

    def request_training_crop_review(
        self,
        user: UserContext,
        request: ReviewQueueItemCreateRequest,
    ) -> ReviewQueueItemResponse:
        crop = self.store.require_training_crop(
            user=user,
            workspace_id=request.workspace_id,
            training_crop_id=request.training_crop_id,
        )
        if crop.review_status != TrainingCropReviewStatus.review_complete:
            raise DomainError(
                "training_crop_review_not_complete",
                "Only completed Training Crops can be requested for review.",
                409,
            )
        if crop.visible_bee_status != VisibleBeeStatus.has_visible_bees:
            raise DomainError(
                "training_crop_has_no_reviewable_bees",
                "Review Queue Items require a completed Training Crop with visible bees.",
                409,
            )
        ellipses = self.store.get_ellipses_for_training_crop(crop.training_crop_id)
        if not ellipses:
            raise DomainError(
                "training_crop_has_no_reviewed_ellipses",
                "Review Queue Items require at least one reviewed bee ellipse.",
                409,
            )
        active = self.store.active_review_queue_item_for_training_crop(crop.training_crop_id)
        if active is not None:
            raise DomainError(
                "review_queue_item_already_available",
                "This Training Crop already has an available Review Queue Item.",
                409,
            )

        requested_at = self.store.clock()
        item = ReviewQueueItemRecord(
            review_queue_item_id=self.store.id_factory(),
            human_readable_id=_human_readable_id("HS-RQ", self.store.list_review_queue_items()),
            workspace_id=request.workspace_id,
            subject_type=ReviewQueueSubjectType.training_crop,
            subject_id=crop.training_crop_id,
            requested_by_user_id=user.user_id,
            original_crop_reviewer_user_id=crop.created_by_user_id,
            status=ReviewQueueItemStatus.available,
            request_notes=_clean_optional_text(request.request_notes),
            requested_at=requested_at,
            evidence_snapshot=ReviewQueueEvidenceSnapshot(
                safe_source_label=f"Training Crop {crop.training_crop_id.hex[:8]}",
                training_crop_id=crop.training_crop_id,
                training_crop_label=f"Training Crop {crop.training_crop_id.hex[:8]}",
                inspection_photo_id=crop.inspection_photo_id,
                image_view_url=(
                    "/v1/review-queue/items/{review_queue_item_id}/image"
                ),
                crop_x=crop.crop_x,
                crop_y=crop.crop_y,
                crop_width=crop.crop_width,
                crop_height=crop.crop_height,
                source_image_width_px=crop.source_image_width_px,
                source_image_height_px=crop.source_image_height_px,
                crop_image_width_px=crop.crop_image_width_px,
                crop_image_height_px=crop.crop_image_height_px,
                reviewed_ellipses=[
                    ReviewQueueEllipseEvidence(
                        annotation_id=ellipse.annotation_id,
                        annotation_type=ellipse.annotation_type,
                        center_x=ellipse.center_x,
                        center_y=ellipse.center_y,
                        radius_x=ellipse.radius_x,
                        radius_y=ellipse.radius_y,
                        rotation_degrees=ellipse.rotation_degrees,
                        coordinate_space=ellipse.coordinate_space,
                        source_image_width_px=ellipse.source_image_width_px,
                        source_image_height_px=ellipse.source_image_height_px,
                    )
                    for ellipse in ellipses
                ],
                reviewed_ellipse_count=len(ellipses),
                complete_visible_bee_count=sum(
                    1 for ellipse in ellipses if ellipse.annotation_type == AnnotationType.complete_visible_bee
                ),
                partial_visible_bee_count=sum(
                    1 for ellipse in ellipses if ellipse.annotation_type == AnnotationType.partial_visible_bee
                ),
                crop_review_status=crop.review_status,
                visible_bee_status=crop.visible_bee_status,
                requested_at=requested_at,
            ),
        )
        item = item.model_copy(
            update={
                "evidence_snapshot": item.evidence_snapshot.model_copy(
                    update={
                        "image_view_url": (
                            f"/v1/review-queue/items/{item.review_queue_item_id}/image"
                        )
                    }
                )
            }
        )
        self.store.save_review_queue_item(item)
        return self.store.review_queue_item_response(item)

    def list_available_work(self, user: UserContext) -> ReviewQueueItemListResponse:
        self.store.require_reviewer_capability(user)
        return ReviewQueueItemListResponse(
            review_queue_items=[
                self.store.review_queue_item_response(item)
                for item in self.store.list_review_queue_items()
                if item.status == ReviewQueueItemStatus.available
                and self._reviewer_is_eligible(user.user_id, item)
            ]
        )

    def get_available_work_item(
        self,
        user: UserContext,
        review_queue_item_id: UUID,
    ) -> ReviewQueueItemResponse:
        item = self._require_item(review_queue_item_id)
        self.store.require_reviewer_capability(user)
        if item.status != ReviewQueueItemStatus.available or not self._reviewer_is_eligible(
            user.user_id,
            item,
        ):
            raise DomainError(
                "review_queue_item_not_available",
                "The requested Review Queue Item is not available to this Reviewer.",
                404,
            )
        return self.store.review_queue_item_response(item)

    def list_review_history(self, user: UserContext) -> ReviewQueueItemListResponse:
        self.store.require_reviewer_capability(user)
        completed_item_ids = {
            outcome.review_queue_item_id
            for outcome in self.store.review_queue_outcomes.values()
            if outcome.reviewer_id == user.user_id
        }
        return ReviewQueueItemListResponse(
            review_queue_items=[
                self.store.review_queue_item_response(item)
                for item in reversed(self.store.list_review_queue_items())
                if item.review_queue_item_id in completed_item_ids
            ]
        )

    def list_requested_reviews(
        self,
        user: UserContext,
        workspace_id: UUID,
    ) -> ReviewQueueItemListResponse:
        self.store.require_workspace_access(user, workspace_id)
        self.store.require_data_use_agreement(workspace_id)
        self.store.require_dataset_curator_capability(user)
        return ReviewQueueItemListResponse(
            review_queue_items=[
                self.store.review_queue_item_response(item, include_reviewer_identity=True)
                for item in reversed(self.store.list_review_queue_items())
                if item.workspace_id == workspace_id and item.requested_by_user_id == user.user_id
            ]
        )

    def complete_review(
        self,
        user: UserContext,
        review_queue_item_id: UUID,
        request: ReviewQueueOutcomeCreateRequest,
    ) -> ReviewQueueItemResponse:
        item = self._require_item(review_queue_item_id)
        self.store.require_reviewer_capability(user)
        if item.status != ReviewQueueItemStatus.available:
            raise DomainError(
                "review_queue_item_already_completed",
                "This Review Queue Item is no longer available.",
                409,
            )
        if not self._reviewer_is_eligible(user.user_id, item):
            raise DomainError(
                "review_queue_item_not_available",
                "The requested Review Queue Item is not available to this Reviewer.",
                404,
            )
        notes = _clean_optional_text(request.review_notes)
        if request.review_outcome in {
            ReviewQueueOutcomeValue.changes_requested,
            ReviewQueueOutcomeValue.not_determined,
        } and notes is None:
            raise DomainError(
                "review_notes_required",
                "Changes-requested and not-determined review outcomes require notes.",
                422,
            )
        completed_at = self.store.clock()
        outcome = ReviewQueueOutcomeRecord(
            review_queue_outcome_id=self.store.id_factory(),
            review_queue_item_id=review_queue_item_id,
            reviewer_id=user.user_id,
            review_outcome=request.review_outcome,
            review_notes=notes,
            created_at=completed_at,
        )
        self.store.save_review_queue_outcome(outcome)
        completed = item.model_copy(
            update={
                "status": ReviewQueueItemStatus.completed,
                "completed_at": completed_at,
                "completed_by_outcome_id": outcome.review_queue_outcome_id,
            }
        )
        self.store.save_review_queue_item(completed)
        return self.store.review_queue_item_response(completed)

    def cancel_review(
        self,
        user: UserContext,
        review_queue_item_id: UUID,
        request: ReviewQueueItemCancelRequest,
    ) -> ReviewQueueItemResponse:
        item = self._require_item(review_queue_item_id)
        self.store.require_workspace_access(user, item.workspace_id)
        self.store.require_data_use_agreement(item.workspace_id)
        self.store.require_dataset_curator_capability(user)
        if item.requested_by_user_id != user.user_id:
            raise DomainError(
                "review_queue_cancel_not_requester",
                "Only the Dataset Curator who requested review can cancel it in this slice.",
                403,
            )
        if item.status != ReviewQueueItemStatus.available:
            raise DomainError(
                "review_queue_item_not_cancellable",
                "Only available Review Queue Items can be cancelled.",
                409,
            )
        notes = _clean_optional_text(request.cancellation_notes)
        if notes is None:
            raise DomainError(
                "review_queue_cancellation_notes_required",
                "Cancellation notes are required.",
                422,
            )
        cancelled = item.model_copy(
            update={
                "status": ReviewQueueItemStatus.cancelled,
                "cancelled_at": self.store.clock(),
                "cancelled_by_user_id": user.user_id,
                "cancellation_notes": notes,
            }
        )
        self.store.save_review_queue_item(cancelled)
        return self.store.review_queue_item_response(cancelled, include_reviewer_identity=True)

    def require_image_access(
        self,
        user: UserContext,
        review_queue_item_id: UUID,
    ):
        item = self._require_item(review_queue_item_id)
        if item.status == ReviewQueueItemStatus.available:
            self.get_available_work_item(user=user, review_queue_item_id=review_queue_item_id)
        else:
            self.store.require_reviewer_capability(user)
            outcome = self.store.review_queue_outcome_for_reviewer(review_queue_item_id, user.user_id)
            if outcome is None:
                raise DomainError(
                    "review_queue_item_not_available",
                    "The requested Review Queue Item is not available to this Reviewer.",
                    404,
                )
        photo = self.store.get_inspection_photo(item.evidence_snapshot.inspection_photo_id)
        if photo is None:
            raise DomainError(
                "inspection_photo_not_found",
                "The queued Inspection Photo was not found.",
                404,
            )
        return photo

    def _require_item(self, review_queue_item_id: UUID) -> ReviewQueueItemRecord:
        item = self.store.get_review_queue_item(review_queue_item_id)
        if item is None:
            raise DomainError(
                "review_queue_item_not_found",
                "The requested Review Queue Item was not found.",
                404,
            )
        return item

    def _reviewer_is_eligible(
        self,
        reviewer_id: UUID,
        item: ReviewQueueItemRecord,
    ) -> bool:
        if reviewer_id == item.requested_by_user_id:
            return False
        if reviewer_id == item.original_crop_reviewer_user_id:
            return False
        return self.store.review_queue_outcome_for_reviewer(
            item.review_queue_item_id,
            reviewer_id,
        ) is None


def _human_readable_id(prefix: str, existing_items: list[ReviewQueueItemRecord]) -> str:
    return f"{prefix}-{len(existing_items) + 1:06d}"


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
