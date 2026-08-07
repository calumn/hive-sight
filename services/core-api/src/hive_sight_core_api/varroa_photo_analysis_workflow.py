from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    LikelyVarroaDetectionResponse,
    VarroaPhotoAnalysisBeeResultResponse,
    VarroaPhotoAnalysisBatchResponse,
    VarroaPhotoAnalysisBatchStatus,
    VarroaPhotoAnalysisBeeStatus,
    VarroaPhotoAnalysisReviewRequest,
    VarroaPhotoAnalysisReviewStatus,
    VarroaPhotoAnalysisRunListResponse,
    VarroaPhotoAnalysisRunResponse,
    VarroaPhotoAnalysisStatus,
)
from hive_sight_core_api.varroa_review_workflow import (
    DeterministicStubVarroaDetectorAdapter,
    VarroaDetectorAdapter,
    VarroaDetectorFailure,
    VarroaDetectorRequest,
)


@dataclass(frozen=True)
class VarroaPhotoAnalysisWorkflow:
    store: InMemoryProductDataStore
    image_loader: Callable[[str], bytes | None]
    varroa_detector_adapter: VarroaDetectorAdapter = DeterministicStubVarroaDetectorAdapter()
    product_candidate_geometries: tuple[dict[str, float], ...] = (
        {"x": 0.32, "y": 0.5, "width": 0.22, "height": 0.44, "rotation_degrees": 0.0},
        {"x": 0.68, "y": 0.5, "width": 0.22, "height": 0.44, "rotation_degrees": 0.0},
    )

    def run_photo_analysis(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_photo_id: UUID,
    ) -> VarroaPhotoAnalysisRunResponse:
        run = self.enqueue_photo_analysis(user, workspace_id, inspection_photo_id)
        return self.process_photo_analysis_run(workspace_id, run.photo_analysis_run_id)

    def enqueue_photo_analysis(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_photo_id: UUID,
    ) -> VarroaPhotoAnalysisRunResponse:
        self.store.require_workspace_access(user, workspace_id)
        self.store.require_data_use_agreement(workspace_id)
        photo = self.store.get_inspection_photo(inspection_photo_id)
        if photo is None or photo.workspace_id != workspace_id:
            raise DomainError(
                "inspection_photo_not_found",
                "The requested Inspection Photo was not found in this Workspace.",
                404,
            )
        inspection = self.store.require_inspection(workspace_id, photo.inspection_id)
        existing = self.store.list_varroa_photo_analysis_runs_for_photo(
            workspace_id=workspace_id, inspection_photo_id=inspection_photo_id
        )
        if any(run.status in {
            VarroaPhotoAnalysisStatus.running,
            VarroaPhotoAnalysisStatus.completed,
            VarroaPhotoAnalysisStatus.partial,
            VarroaPhotoAnalysisStatus.no_usable_bees,
        } for run in existing):
            raise DomainError(
                "photo_analysis_already_produced",
                "This Inspection Photo already has a produced Photo Analysis.",
                409,
            )
        now = self.store.clock()
        run_id = self.store.id_factory()
        run = VarroaPhotoAnalysisRunResponse(
            photo_analysis_run_id=run_id,
            workspace_id=workspace_id,
            inspection_id=inspection.inspection_id,
            inspection_photo_id=inspection_photo_id,
            source_image_filename=photo.filename,
            status=VarroaPhotoAnalysisStatus.running,
            total_detected_bees=0,
            eligible_bees=0,
            analysed_bees=0,
            failed_bees=0,
            mites_found=0,
            bees_with_likely_varroa=0,
            current_stage="Bee localisation",
            adapter_type=self.varroa_detector_adapter.adapter_type,
            adapter_version=self.varroa_detector_adapter.adapter_version,
            model_reference=self.varroa_detector_adapter.model_reference,
            command_contract_version=_command_contract_version(self.varroa_detector_adapter),
            started_at=now,
            caveat="Development model evidence is being analysed; not treatment advice.",
            advisor_evidence_eligible=False,
        )
        self.store.save_varroa_photo_analysis_run(run)
        return run

    def process_photo_analysis_run(
        self,
        workspace_id: UUID,
        photo_analysis_run_id: UUID,
    ) -> VarroaPhotoAnalysisRunResponse:
        run = self.store.get_varroa_photo_analysis_run(workspace_id, photo_analysis_run_id)
        if run is None:
            raise DomainError(
                "photo_analysis_not_found",
                "The requested Varroa Photo Analysis was not found in this Workspace.",
                404,
            )
        if run.status != VarroaPhotoAnalysisStatus.running:
            return run
        photo = self.store.get_inspection_photo(run.inspection_photo_id)
        if photo is None:
            failed = run.model_copy(
                update={
                    "status": VarroaPhotoAnalysisStatus.failed,
                    "completed_at": self.store.clock(),
                    "failure_code": "inspection_photo_not_found",
                    "failure_message": "The Inspection Photo disappeared before analysis could begin.",
                    "current_stage": None,
                    "caveat": "Photo could not be analysed.",
                }
            )
            return self.store.save_varroa_photo_analysis_run(failed)
        inspection = self.store.require_inspection(workspace_id, photo.inspection_id)
        # An Inspection Photo is product evidence.  It never relies on, or
        # exposes, the separate model-curation Training Crop workflow.
        return self._run_product_photo_analysis(
            workspace_id=workspace_id,
            inspection=inspection,
            photo=photo,
            run_id=run.photo_analysis_run_id,
            now=run.started_at,
        )

    def _run_product_photo_analysis(self, *, workspace_id: UUID, inspection, photo, run_id: UUID, now):
        image = self.image_loader(photo.original_object_key) or b""
        # These source-coordinate candidates stand in for the localisation and
        # orientation adapters.  Their geometry is persisted so a real adapter
        # can replace this seam without changing the product evidence shape.
        candidate_geometries = self.product_candidate_geometries
        results: list[VarroaPhotoAnalysisBeeResultResponse] = []
        for geometry in candidate_geometries:
            try:
                detections = [
                    LikelyVarroaDetectionResponse.model_validate(item)
                    for item in self.varroa_detector_adapter.detect(
                        VarroaDetectorRequest(
                            workspace_id=workspace_id,
                            inspection_photo_id=photo.inspection_photo_id,
                            training_crop_id=None,
                            bee_annotation_id=None,
                            head_up_normalized_image_bytes=image,
                            image_width_px=640,
                            image_height_px=640,
                            transform_version="product_photo_stub_v1",
                            transform_metadata={"head_up": True, "development_model_evidence": True},
                            source_geometry_snapshot=geometry,
                        )
                    )
                ]
                results.append(
                    VarroaPhotoAnalysisBeeResultResponse(
                        photo_analysis_bee_result_id=self.store.id_factory(),
                        photo_analysis_run_id=run_id,
                        inspection_photo_id=photo.inspection_photo_id,
                        source_geometry_snapshot=geometry,
                        status=VarroaPhotoAnalysisBeeStatus.completed,
                        mites_found=len(detections),
                        detections=detections,
                        adapter_type=self.varroa_detector_adapter.adapter_type,
                        adapter_version=self.varroa_detector_adapter.adapter_version,
                        model_reference=self.varroa_detector_adapter.model_reference,
                        command_contract_version=_command_contract_version(self.varroa_detector_adapter),
                    )
                )
            except VarroaDetectorFailure as error:
                results.append(
                    self._bee_failure(
                        run_id=run_id,
                        crop_id=None,
                        bee_annotation_id=None,
                        head_up_crop=None,
                        code=error.code,
                        message=error.message,
                        raw_error_payload=error.raw_error_payload,
                    ).model_copy(
                        update={
                            "inspection_photo_id": photo.inspection_photo_id,
                            "source_geometry_snapshot": geometry,
                        }
                    )
                )
            except Exception as error:
                results.append(
                    self._bee_failure(
                        run_id=run_id,
                        crop_id=None,
                        bee_annotation_id=None,
                        head_up_crop=None,
                        code="varroa_detector_invalid_response",
                        message=str(error),
                        raw_error_payload=_sanitize_raw_payload(str(error)),
                    ).model_copy(
                        update={
                            "inspection_photo_id": photo.inspection_photo_id,
                            "source_geometry_snapshot": geometry,
                        }
                    )
                )
        analysed_bees = sum(result.status == VarroaPhotoAnalysisBeeStatus.completed for result in results)
        failed_bees = sum(result.status == VarroaPhotoAnalysisBeeStatus.failed for result in results)
        status = _photo_analysis_status(
            eligible_bees=len(candidate_geometries),
            analysed_bees=analysed_bees,
            failed_bees=failed_bees,
        )
        run = VarroaPhotoAnalysisRunResponse(
            photo_analysis_run_id=run_id, workspace_id=workspace_id, inspection_id=inspection.inspection_id,
            inspection_photo_id=photo.inspection_photo_id, source_image_filename=photo.filename,
            status=status, total_detected_bees=len(candidate_geometries), eligible_bees=len(candidate_geometries), analysed_bees=analysed_bees,
            failed_bees=failed_bees, mites_found=sum(result.mites_found for result in results),
            bees_with_likely_varroa=sum(result.mites_found > 0 for result in results),
            adapter_type=self.varroa_detector_adapter.adapter_type, adapter_version=self.varroa_detector_adapter.adapter_version,
            model_reference=self.varroa_detector_adapter.model_reference,
            command_contract_version=_command_contract_version(self.varroa_detector_adapter), started_at=now,
            completed_at=self.store.clock(), caveat=_photo_analysis_caveat(status=status, failed_bees=failed_bees),
            advisor_evidence_eligible=False, bee_results=results,
        )
        self.store.save_varroa_photo_analysis_run(run)
        for result in results:
            self.store.save_varroa_photo_analysis_bee_result(result)
        return self.store.get_varroa_photo_analysis_run(workspace_id, run_id) or run

    def list_photo_analyses(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_photo_id: UUID,
    ) -> VarroaPhotoAnalysisRunListResponse:
        self.store.require_workspace_access(user, workspace_id)
        self.store.require_data_use_agreement(workspace_id)
        return VarroaPhotoAnalysisRunListResponse(
            workspace_id=workspace_id,
            inspection_photo_id=inspection_photo_id,
            runs=self.store.list_varroa_photo_analysis_runs_for_photo(
                workspace_id=workspace_id,
                inspection_photo_id=inspection_photo_id,
            ),
        )

    def run_all_photo_analyses(
        self, user: UserContext, workspace_id: UUID, inspection_id: UUID
    ) -> VarroaPhotoAnalysisBatchResponse:
        self.store.require_workspace_access(user, workspace_id)
        self.store.require_data_use_agreement(workspace_id)
        inspection = self.store.require_inspection(workspace_id, inspection_id)
        if inspection.intent.value != "varroa_assessment":
            raise DomainError("inspection_not_varroa_assessment", "Photo analysis is only available for Varroa Assessment Inspections.", 409)
        photos = self.store.list_inspection_photos(user, workspace_id, inspection_id).photos
        attempted: list[UUID] = []
        skipped: list[UUID] = []
        runs: list[VarroaPhotoAnalysisRunResponse] = []
        for photo in photos:
            prior = self.store.list_varroa_photo_analysis_runs_for_photo(workspace_id, photo.inspection_photo_id)
            if any(run.status in {VarroaPhotoAnalysisStatus.completed, VarroaPhotoAnalysisStatus.partial, VarroaPhotoAnalysisStatus.no_usable_bees} for run in prior):
                skipped.append(photo.inspection_photo_id)
                continue
            attempted.append(photo.inspection_photo_id)
            try:
                runs.append(self.run_photo_analysis(user, workspace_id, photo.inspection_photo_id))
            except DomainError:
                continue
        issues = any(run.status in {VarroaPhotoAnalysisStatus.partial, VarroaPhotoAnalysisStatus.failed} for run in runs)
        batch = VarroaPhotoAnalysisBatchResponse(
            photo_analysis_batch_id=self.store.id_factory(), workspace_id=workspace_id,
            inspection_id=inspection_id,
            status=VarroaPhotoAnalysisBatchStatus.completed_with_issues if issues else VarroaPhotoAnalysisBatchStatus.completed,
            attempted_photo_ids=attempted, skipped_photo_ids=skipped, runs=runs,
            started_at=self.store.clock(), completed_at=self.store.clock(),
        )
        return self.store.save_varroa_photo_analysis_batch(batch)

    def review_photo_analysis(
        self,
        user: UserContext,
        photo_analysis_run_id: UUID,
        request: VarroaPhotoAnalysisReviewRequest,
    ) -> VarroaPhotoAnalysisRunResponse:
        self.store.require_workspace_access(user, request.workspace_id)
        self.store.require_data_use_agreement(request.workspace_id)
        run = self.store.get_varroa_photo_analysis_run(
            workspace_id=request.workspace_id,
            photo_analysis_run_id=photo_analysis_run_id,
        )
        if run is None:
            raise DomainError(
                "photo_analysis_not_found",
                "The requested Varroa Photo Analysis was not found in this Workspace.",
                404,
            )
        if request.review_status == VarroaPhotoAnalysisReviewStatus.accepted and run.status in {
            VarroaPhotoAnalysisStatus.failed,
            VarroaPhotoAnalysisStatus.no_usable_bees,
        }:
            raise DomainError(
                "photo_analysis_not_acceptable",
                "This Varroa Photo Analysis cannot be accepted as Advisor evidence.",
                409,
            )
        if (
            request.review_status != VarroaPhotoAnalysisReviewStatus.accepted
            and not _clean_note(request.review_note)
        ):
            raise DomainError(
                "photo_analysis_review_note_required",
                "A note is required when a Photo Analysis is not accepted.",
                422,
            )
        updated = run.model_copy(
            update={
                "review_status": request.review_status,
                "review_note": (
                    None
                    if request.review_status == VarroaPhotoAnalysisReviewStatus.accepted
                    else _clean_note(request.review_note)
                ),
                "advisor_evidence_eligible": (
                    request.review_status == VarroaPhotoAnalysisReviewStatus.accepted
                    and run.status
                    in {VarroaPhotoAnalysisStatus.completed, VarroaPhotoAnalysisStatus.partial}
                ),
            }
        )
        self.store.save_varroa_photo_analysis_run(updated)
        return self.store.get_varroa_photo_analysis_run(
            request.workspace_id,
            photo_analysis_run_id,
        ) or updated

    def _bee_failure(
        self,
        *,
        run_id: UUID,
        crop_id: UUID | None,
        bee_annotation_id: UUID | None,
        head_up_crop,
        code: str,
        message: str,
        raw_error_payload: str | None,
    ) -> VarroaPhotoAnalysisBeeResultResponse:
        return VarroaPhotoAnalysisBeeResultResponse(
            photo_analysis_bee_result_id=self.store.id_factory(),
            photo_analysis_run_id=run_id,
            training_crop_id=crop_id,
            bee_annotation_id=bee_annotation_id,
            status=VarroaPhotoAnalysisBeeStatus.failed,
            mites_found=0,
            adapter_type=self.varroa_detector_adapter.adapter_type,
            adapter_version=self.varroa_detector_adapter.adapter_version,
            model_reference=self.varroa_detector_adapter.model_reference,
            command_contract_version=_command_contract_version(self.varroa_detector_adapter),
            failure_code=code,
            failure_message=message,
            raw_error_payload=_sanitize_raw_payload(raw_error_payload),
            head_up_normalized_crop=head_up_crop,
        )


def _photo_analysis_status(
    *,
    eligible_bees: int,
    analysed_bees: int,
    failed_bees: int,
) -> VarroaPhotoAnalysisStatus:
    if eligible_bees == 0:
        return VarroaPhotoAnalysisStatus.no_usable_bees
    if analysed_bees == 0 and failed_bees > 0:
        return VarroaPhotoAnalysisStatus.failed
    if failed_bees > 0:
        return VarroaPhotoAnalysisStatus.partial
    return VarroaPhotoAnalysisStatus.completed


def _photo_analysis_caveat(*, status: VarroaPhotoAnalysisStatus, failed_bees: int) -> str:
    caveats = ["Model-assisted photo analysis only; not treatment advice."]
    if status == VarroaPhotoAnalysisStatus.partial:
        caveats.append(
            f"Result is incomplete because {failed_bees} eligible bee detector call(s) failed."
        )
    if status == VarroaPhotoAnalysisStatus.no_usable_bees:
        caveats.append("No usable bees were available for Varroa evaluation.")
    if status == VarroaPhotoAnalysisStatus.failed:
        caveats.append("No usable mite count was produced.")
    return " ".join(caveats)


def _command_contract_version(adapter: VarroaDetectorAdapter) -> str | None:
    return getattr(adapter, "command_contract_version", None)


def _clean_note(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _sanitize_raw_payload(value: str | None) -> str | None:
    if value is None:
        return None
    return value[:2000]
