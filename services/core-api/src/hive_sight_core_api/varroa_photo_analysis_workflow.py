from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from uuid import UUID

from hive_sight_core_api.dev_store import DomainError, InMemoryProductDataStore, UserContext
from hive_sight_core_api.models import (
    LikelyVarroaDetectionResponse,
    TrainingCropReviewStatus,
    VarroaPhotoAnalysisBeeResultResponse,
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
    VarroaReviewWorkflow,
    _ineligibility_reasons,
    _preview_response,
)


@dataclass(frozen=True)
class VarroaPhotoAnalysisWorkflow:
    store: InMemoryProductDataStore
    image_loader: Callable[[str], bytes | None]
    varroa_detector_adapter: VarroaDetectorAdapter = DeterministicStubVarroaDetectorAdapter()

    def run_photo_analysis(
        self,
        user: UserContext,
        workspace_id: UUID,
        inspection_photo_id: UUID,
    ) -> VarroaPhotoAnalysisRunResponse:
        started = perf_counter()
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
        now = self.store.clock()
        run_id = self.store.id_factory()
        helper = VarroaReviewWorkflow(
            store=self.store,
            image_loader=self.image_loader,
            varroa_detector_adapter=self.varroa_detector_adapter,
        )
        crops = [
            crop
            for crop in self.store.list_training_crops_for_photo_id(
                workspace_id=workspace_id,
                inspection_photo_id=inspection_photo_id,
            )
            if crop.review_status == TrainingCropReviewStatus.review_complete
        ]
        total_detected_bees = 0
        eligible_bees = 0
        bee_results: list[VarroaPhotoAnalysisBeeResultResponse] = []

        for crop in crops:
            for ellipse in self.store.get_ellipses_for_training_crop(crop.training_crop_id):
                total_detected_bees += 1
                if _ineligibility_reasons(crop=crop, ellipse=ellipse):
                    continue
                eligible_bees += 1
                head_up_crop = _preview_response(
                    workspace_id=workspace_id,
                    crop=crop,
                    ellipse=ellipse,
                )
                try:
                    image = helper._build_head_up_normalized_crop_image(
                        workspace_id=workspace_id,
                        crop=crop,
                        ellipse=ellipse,
                    )
                    detections = [
                        LikelyVarroaDetectionResponse.model_validate(detection)
                        for detection in self.varroa_detector_adapter.detect(
                            VarroaDetectorRequest(
                                workspace_id=workspace_id,
                                inspection_photo_id=inspection_photo_id,
                                training_crop_id=crop.training_crop_id,
                                bee_annotation_id=ellipse.annotation_id,
                                head_up_normalized_image_bytes=image.body,
                                image_width_px=head_up_crop.image_width_px,
                                image_height_px=head_up_crop.image_height_px,
                                transform_version=head_up_crop.transform_version,
                                transform_metadata=head_up_crop.transform_metadata,
                                source_geometry_snapshot=(
                                    head_up_crop.bee_annotation_geometry_snapshot
                                ),
                            )
                        )
                    ]
                except VarroaDetectorFailure as error:
                    bee_results.append(
                        self._bee_failure(
                            run_id=run_id,
                            crop_id=crop.training_crop_id,
                            bee_annotation_id=ellipse.annotation_id,
                            head_up_crop=head_up_crop,
                            code=error.code,
                            message=error.message,
                            raw_error_payload=error.raw_error_payload,
                        )
                    )
                    continue
                except Exception as error:
                    bee_results.append(
                        self._bee_failure(
                            run_id=run_id,
                            crop_id=crop.training_crop_id,
                            bee_annotation_id=ellipse.annotation_id,
                            head_up_crop=head_up_crop,
                            code="varroa_detector_invalid_response",
                            message=str(error),
                            raw_error_payload=_sanitize_raw_payload(str(error)),
                        )
                    )
                    continue

                bee_results.append(
                    VarroaPhotoAnalysisBeeResultResponse(
                        photo_analysis_bee_result_id=self.store.id_factory(),
                        photo_analysis_run_id=run_id,
                        training_crop_id=crop.training_crop_id,
                        bee_annotation_id=ellipse.annotation_id,
                        status=VarroaPhotoAnalysisBeeStatus.completed,
                        mites_found=len(detections),
                        detections=detections,
                        adapter_type=self.varroa_detector_adapter.adapter_type,
                        adapter_version=self.varroa_detector_adapter.adapter_version,
                        model_reference=self.varroa_detector_adapter.model_reference,
                        command_contract_version=_command_contract_version(
                            self.varroa_detector_adapter
                        ),
                        head_up_normalized_crop=head_up_crop,
                    )
                )

        analysed_bees = sum(
            1 for result in bee_results if result.status == VarroaPhotoAnalysisBeeStatus.completed
        )
        failed_bees = sum(
            1 for result in bee_results if result.status == VarroaPhotoAnalysisBeeStatus.failed
        )
        status = _photo_analysis_status(
            eligible_bees=eligible_bees,
            analysed_bees=analysed_bees,
            failed_bees=failed_bees,
        )
        run = VarroaPhotoAnalysisRunResponse(
            photo_analysis_run_id=run_id,
            workspace_id=workspace_id,
            inspection_id=inspection.inspection_id,
            inspection_photo_id=inspection_photo_id,
            source_image_filename=photo.filename,
            status=status,
            total_detected_bees=total_detected_bees,
            eligible_bees=eligible_bees,
            analysed_bees=analysed_bees,
            failed_bees=failed_bees,
            mites_found=sum(result.mites_found for result in bee_results),
            adapter_type=self.varroa_detector_adapter.adapter_type,
            adapter_version=self.varroa_detector_adapter.adapter_version,
            model_reference=self.varroa_detector_adapter.model_reference,
            command_contract_version=_command_contract_version(self.varroa_detector_adapter),
            started_at=now,
            completed_at=self.store.clock(),
            caveat=_photo_analysis_caveat(status=status, failed_bees=failed_bees),
            advisor_evidence_eligible=False,
            bee_results=bee_results,
        )
        self.store.save_varroa_photo_analysis_run(run)
        for result in bee_results:
            self.store.save_varroa_photo_analysis_bee_result(result)
        _ = started
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
        updated = run.model_copy(
            update={
                "review_status": request.review_status,
                "review_note": _clean_note(request.review_note),
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
        crop_id: UUID,
        bee_annotation_id: UUID,
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
