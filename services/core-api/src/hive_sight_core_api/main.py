from typing import Annotated
from uuid import UUID

from fastapi import BackgroundTasks, Depends, FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from hive_sight_core_api.advisor_treatment_recommendation_workflow import (
    AdvisorTreatmentRecommendationWorkflow,
)
from hive_sight_core_api.advisor_varroa_context_workflow import AdvisorVarroaContextWorkflow
from hive_sight_core_api.analysis_processing_workflow import AnalysisProcessingWorkflow
from hive_sight_core_api.analysis_request_workflow import AnalysisRequestWorkflow
from hive_sight_core_api.bee_detector_benchmark_evaluation_workflow import (
    BeeDetectorBenchmarkEvaluationWorkflow,
)
from hive_sight_core_api.bee_detector_candidate_annotation_workflow import (
    BeeDetectorCandidateAnnotationWorkflow,
)
from hive_sight_core_api.bee_detector_training_workflow import BeeDetectorTrainingWorkflow
from hive_sight_core_api.bee_orientation_benchmark_evaluation_workflow import (
    BeeOrientationBenchmarkEvaluationWorkflow,
)
from hive_sight_core_api.dataset_labelling_workflow import DatasetLabellingWorkflow
from hive_sight_core_api.dataset_repository_workflow import DatasetRepositoryWorkflow
from hive_sight_core_api.dataset_role_assignment_workflow import DatasetRoleAssignmentWorkflow
from hive_sight_core_api.dependencies import (
    DevStateDep,
    build_configured_varroa_detector_adapter,
    get_advisor_treatment_recommendation_workflow,
    get_advisor_varroa_context_workflow,
    get_analysis_processing_workflow,
    get_analysis_request_workflow,
    get_bee_detector_benchmark_evaluation_workflow,
    get_bee_detector_candidate_annotation_workflow,
    get_bee_detector_training_workflow,
    get_bee_orientation_benchmark_evaluation_workflow,
    get_dataset_labelling_workflow,
    get_dataset_repository_workflow,
    get_dataset_role_assignment_workflow,
    get_directed_ellipse_cleanup_workflow,
    get_frame_level_varroa_result_workflow,
    get_hive_configuration_workflow,
    get_inspection_photo_access,
    get_review_queue_workflow,
    get_settings,
    get_training_crop_dataset_item_workflow,
    get_training_crop_workflow,
    get_varroa_photo_analysis_workflow,
    get_varroa_review_workflow,
)
from hive_sight_core_api.dev_store import DomainError, UserContext
from hive_sight_core_api.dev_users import DEV_USER_IDS
from hive_sight_core_api.directed_ellipse_cleanup_workflow import DirectedEllipseCleanupWorkflow
from hive_sight_core_api.frame_level_varroa_result_workflow import FrameLevelVarroaResultWorkflow
from hive_sight_core_api.hive_configuration_workflow import HiveConfigurationWorkflow
from hive_sight_core_api.inspection_photo_access import InspectionPhotoAccess
from hive_sight_core_api.models import (
    AdvisorTreatmentRecommendationCreateRequest,
    AdvisorVarroaContextRequest,
    AdvisorVarroaContextResponse,
    AnalysisEvidenceResponse,
    AnalysisRunDetailListResponse,
    AnalysisRunDetailResponse,
    AnalysisRunRequest,
    AnalysisRunResponse,
    ApiaryCreateRequest,
    ApiaryListResponse,
    ApiaryResponse,
    BeeAnnotationProposalListResponse,
    BeeAnnotationProposalRequest,
    BeeTrainingReadinessResponse,
    BeeTrainingStartRequest,
    BeeTrainingStartResponse,
    BenchmarkEvaluationCancelRequest,
    BenchmarkEvaluationListResponse,
    BenchmarkEvaluationReadinessResponse,
    BenchmarkEvaluationResponse,
    BenchmarkEvaluationStartRequest,
    DatasetItemCreateRequest,
    DatasetItemResponse,
    DatasetLabellingEvidenceResponse,
    DatasetLabellingSessionResponse,
    DatasetRepositoryItemDetail,
    DatasetRepositoryItemListResponse,
    DatasetRepositorySummaryResponse,
    DatasetRole,
    DatasetVersionCreateRequest,
    DatasetVersionListResponse,
    DatasetVersionResponse,
    DevSessionResponse,
    DevUserListResponse,
    DirectedEllipseLocalCleanupRequest,
    DirectedEllipseLocalCleanupResponse,
    ErrorResponse,
    FrameLevelVarroaResultSummaryResponse,
    FrameMiteCountRequest,
    FrameMiteCountResponse,
    FrameSide,
    FrameStandardResponse,
    HeadUpNormalizedBeeCropPreviewResponse,
    HealthResponse,
    HiveConfigurationResponse,
    HiveConfigurationUpsertRequest,
    HiveCreateRequest,
    HiveFrameSlotListResponse,
    HiveListResponse,
    HiveResponse,
    HiveTreatmentCourseListResponse,
    HiveTreatmentCourseResponse,
    InspectionCreateRequest,
    InspectionFrameObservationListResponse,
    InspectionFrameObservationResponse,
    InspectionFrameObservationUpdateRequest,
    InspectionIntent,
    InspectionIntentUpdateRequest,
    InspectionListResponse,
    InspectionPhotoListResponse,
    InspectionResponse,
    ModelCandidateListResponse,
    ModelCandidateResponse,
    ModelTrainingReadinessResponse,
    OrientationBenchmarkReadinessResponse,
    OrientedBeeEllipseCreateRequest,
    OrientedBeeEllipseResponse,
    OrientedBeeEllipseUpdateRequest,
    PhotoIntakeResponse,
    PhysicalYoloObbExportRequest,
    PhysicalYoloObbExportResponse,
    ProcessAnalysisRunRequest,
    ReviewDecisionCreateRequest,
    ReviewDecisionResponse,
    ReviewQueueItemCancelRequest,
    ReviewQueueItemCreateRequest,
    ReviewQueueItemListResponse,
    ReviewQueueItemResponse,
    ReviewQueueOutcomeCreateRequest,
    StartDatasetLabellingRequest,
    TrainingCropCreateRequest,
    TrainingCropDatasetItemCreateRequest,
    TrainingCropEvidenceResponse,
    TrainingCropListResponse,
    TrainingCropResponse,
    TrainingCropUpdateRequest,
    TrainingRunAbandonRequest,
    TrainingRunCancelRequest,
    TrainingRunDeleteRequest,
    TrainingRunDeleteResponse,
    TrainingRunListResponse,
    TrainingRunResponse,
    TrainingRunStartRequest,
    TreatmentEvidenceChainDetailResponse,
    TreatmentEvidenceChainListResponse,
    TreatmentRecommendationDecisionRequest,
    TreatmentRecommendationListResponse,
    TreatmentRecommendationResponse,
    UpdateDatasetLabellingSessionRequest,
    VarroaDetectorPreviewRequest,
    VarroaDetectorPreviewResponse,
    VarroaDetectorReadinessResponse,
    VarroaPhotoAnalysisCreateRequest,
    VarroaPhotoAnalysisBatchResponse,
    VarroaPhotoAnalysisReviewRequest,
    VarroaPhotoAnalysisRunListResponse,
    VarroaPhotoAnalysisRunResponse,
    VarroaReviewCandidateListResponse,
    VarroaReviewOutcomeCreateRequest,
    VarroaReviewOutcomeResponse,
    WorkspaceDataUseAgreementAcceptanceRequest,
    WorkspaceDataUseAgreementAcceptanceResponse,
    YoloObbExportRequest,
    YoloObbExportResponse,
)
from hive_sight_core_api.review_queue_workflow import ReviewQueueWorkflow
from hive_sight_core_api.training_crop_dataset_item_workflow import (
    TrainingCropDatasetItemWorkflow,
)
from hive_sight_core_api.training_crop_workflow import TrainingCropWorkflow
from hive_sight_core_api.varroa_review_workflow import VarroaReviewWorkflow
from hive_sight_core_api.varroa_photo_analysis_workflow import VarroaPhotoAnalysisWorkflow

settings = get_settings()

app = FastAPI(
    title="HiveSight Core API",
    version="0.1.0",
    description="Protected product-facing API for HiveSight.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


InspectionPhotoAccessDep = Annotated[InspectionPhotoAccess, Depends(get_inspection_photo_access)]
AnalysisRequestWorkflowDep = Annotated[
    AnalysisRequestWorkflow,
    Depends(get_analysis_request_workflow),
]
AdvisorVarroaContextWorkflowDep = Annotated[
    AdvisorVarroaContextWorkflow,
    Depends(get_advisor_varroa_context_workflow),
]
AdvisorTreatmentRecommendationWorkflowDep = Annotated[
    AdvisorTreatmentRecommendationWorkflow,
    Depends(get_advisor_treatment_recommendation_workflow),
]
AnalysisProcessingWorkflowDep = Annotated[
    AnalysisProcessingWorkflow,
    Depends(get_analysis_processing_workflow),
]
DatasetLabellingWorkflowDep = Annotated[
    DatasetLabellingWorkflow,
    Depends(get_dataset_labelling_workflow),
]
DatasetRoleAssignmentWorkflowDep = Annotated[
    DatasetRoleAssignmentWorkflow,
    Depends(get_dataset_role_assignment_workflow),
]
DatasetRepositoryWorkflowDep = Annotated[
    DatasetRepositoryWorkflow,
    Depends(get_dataset_repository_workflow),
]
HiveConfigurationWorkflowDep = Annotated[
    HiveConfigurationWorkflow,
    Depends(get_hive_configuration_workflow),
]
TrainingCropWorkflowDep = Annotated[
    TrainingCropWorkflow,
    Depends(get_training_crop_workflow),
]
TrainingCropDatasetItemWorkflowDep = Annotated[
    TrainingCropDatasetItemWorkflow,
    Depends(get_training_crop_dataset_item_workflow),
]
VarroaReviewWorkflowDep = Annotated[
    VarroaReviewWorkflow,
    Depends(get_varroa_review_workflow),
]
VarroaPhotoAnalysisWorkflowDep = Annotated[
    VarroaPhotoAnalysisWorkflow,
    Depends(get_varroa_photo_analysis_workflow),
]
FrameLevelVarroaResultWorkflowDep = Annotated[
    FrameLevelVarroaResultWorkflow,
    Depends(get_frame_level_varroa_result_workflow),
]
ReviewQueueWorkflowDep = Annotated[
    ReviewQueueWorkflow,
    Depends(get_review_queue_workflow),
]
BeeDetectorTrainingWorkflowDep = Annotated[
    BeeDetectorTrainingWorkflow,
    Depends(get_bee_detector_training_workflow),
]
BeeDetectorBenchmarkEvaluationWorkflowDep = Annotated[
    BeeDetectorBenchmarkEvaluationWorkflow,
    Depends(get_bee_detector_benchmark_evaluation_workflow),
]
BeeOrientationBenchmarkEvaluationWorkflowDep = Annotated[
    BeeOrientationBenchmarkEvaluationWorkflow,
    Depends(get_bee_orientation_benchmark_evaluation_workflow),
]
BeeDetectorCandidateAnnotationWorkflowDep = Annotated[
    BeeDetectorCandidateAnnotationWorkflow,
    Depends(get_bee_detector_candidate_annotation_workflow),
]
DirectedEllipseCleanupWorkflowDep = Annotated[
    DirectedEllipseCleanupWorkflow,
    Depends(get_directed_ellipse_cleanup_workflow),
]
DevUserIdHeader = Annotated[str | None, Header(alias="x-hivesight-dev-user-id")]


def get_dev_user_context(
    state: DevStateDep,
    x_hivesight_dev_user_id: DevUserIdHeader = None,
) -> UserContext:
    if x_hivesight_dev_user_id is None:
        raise DomainError(
            "not_authenticated",
            "Sign in before using Workspace inspection workflows.",
            401,
        )
    try:
        user_id = UUID(x_hivesight_dev_user_id)
    except ValueError as exc:
        raise DomainError(
            "not_authenticated",
            "The dev authentication header was not a valid User id.",
            401,
        ) from exc
    if state.dev_users_enabled and user_id not in DEV_USER_IDS:
        raise DomainError(
            "not_authenticated",
            "The selected development User is not available in this environment.",
            401,
        )
    return UserContext(user_id=user_id)


AuthenticatedUserDep = Annotated[UserContext, Depends(get_dev_user_context)]


@app.exception_handler(DomainError)
def handle_domain_error(_: Request, error: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": ErrorResponse(code=error.code, message=error.message).model_dump()},
    )


@app.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    return HealthResponse(
        service="core-api",
        status="ok",
        boundary="internet-reachable protected API",
        persistence_backend=settings.persistence_backend,
        database_purpose=settings.database_purpose,
    )


@app.get("/v1/dev/session", response_model=DevSessionResponse)
def get_dev_session(user: AuthenticatedUserDep, state: DevStateDep) -> DevSessionResponse:
    return state.store.ensure_dev_session(user.user_id)


@app.get("/v1/dev/users", response_model=DevUserListResponse)
def list_dev_users(state: DevStateDep) -> DevUserListResponse:
    if not state.dev_users_enabled:
        raise DomainError(
            "dev_users_disabled",
            "Development User switching is not enabled in this environment.",
            404,
        )
    state.store.seed_development_users()
    return DevUserListResponse(dev_users=state.store.list_development_users())


@app.post(
    "/v1/workspace-data-use-agreements/acceptances",
    response_model=WorkspaceDataUseAgreementAcceptanceResponse,
)
def accept_workspace_data_use_agreement(
    request: WorkspaceDataUseAgreementAcceptanceRequest,
    user: AuthenticatedUserDep,
    state: DevStateDep,
) -> WorkspaceDataUseAgreementAcceptanceResponse:
    return state.store.accept_data_use_agreement(
        user=user,
        workspace_id=request.workspace_id,
        terms_version=request.terms_version,
    )


@app.post("/v1/apiaries", response_model=ApiaryResponse, status_code=201)
def create_apiary(
    request: ApiaryCreateRequest,
    user: AuthenticatedUserDep,
    state: DevStateDep,
) -> ApiaryResponse:
    return state.store.create_apiary(user=user, workspace_id=request.workspace_id, name=request.name)


@app.get("/v1/apiaries", response_model=ApiaryListResponse)
def list_apiaries(
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    state: DevStateDep,
) -> ApiaryListResponse:
    return ApiaryListResponse(
        apiaries=state.store.list_apiaries(user=user, workspace_id=workspace_id)
    )


@app.post("/v1/hives", response_model=HiveResponse, status_code=201)
def create_hive(
    request: HiveCreateRequest,
    user: AuthenticatedUserDep,
    state: DevStateDep,
) -> HiveResponse:
    return state.store.create_hive(user=user, apiary_id=request.apiary_id, name=request.name)


@app.get("/v1/apiaries/{apiary_id}/hives", response_model=HiveListResponse)
def list_hives(
    apiary_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    state: DevStateDep,
) -> HiveListResponse:
    return HiveListResponse(
        hives=state.store.list_hives(user=user, workspace_id=workspace_id, apiary_id=apiary_id)
    )


@app.get("/v1/frame-standards", response_model=list[FrameStandardResponse])
def list_frame_standards(
    user: AuthenticatedUserDep,
    workflow: HiveConfigurationWorkflowDep,
) -> list[FrameStandardResponse]:
    _ = user
    return workflow.list_frame_standards()


@app.put("/v1/hives/{hive_id}/configuration", response_model=HiveConfigurationResponse)
def upsert_hive_configuration(
    hive_id: UUID,
    request: HiveConfigurationUpsertRequest,
    user: AuthenticatedUserDep,
    workflow: HiveConfigurationWorkflowDep,
) -> HiveConfigurationResponse:
    return workflow.upsert_hive_configuration(user=user, hive_id=hive_id, request=request)


@app.get("/v1/hives/{hive_id}/configuration", response_model=HiveConfigurationResponse)
def get_hive_configuration(
    hive_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: HiveConfigurationWorkflowDep,
) -> HiveConfigurationResponse:
    return workflow.get_hive_configuration(
        user=user,
        workspace_id=workspace_id,
        hive_id=hive_id,
    )


@app.get("/v1/hives/{hive_id}/frame-slots", response_model=HiveFrameSlotListResponse)
def list_hive_frame_slots(
    hive_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    state: DevStateDep,
) -> HiveFrameSlotListResponse:
    return state.store.list_hive_frame_slots(
        user=user,
        workspace_id=workspace_id,
        hive_id=hive_id,
    )


@app.post("/v1/inspections", response_model=InspectionResponse, status_code=201)
def create_inspection(
    request: InspectionCreateRequest,
    user: AuthenticatedUserDep,
    workflow: HiveConfigurationWorkflowDep,
) -> InspectionResponse:
    return workflow.create_inspection(
        user=user,
        hive_id=request.hive_id,
        inspection_date=request.inspection_date,
        intent=request.intent,
    )


@app.get("/v1/hives/{hive_id}/inspections", response_model=InspectionListResponse)
def list_hive_inspections(
    hive_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    state: DevStateDep,
    intent: InspectionIntent | None = None,
) -> InspectionListResponse:
    return InspectionListResponse(
        inspections=state.store.list_hive_inspections(
            user=user,
            workspace_id=workspace_id,
            hive_id=hive_id,
            intent=intent,
        )
    )


@app.patch("/v1/inspections/{inspection_id}/intent", response_model=InspectionResponse)
def update_inspection_intent(
    inspection_id: UUID,
    request: InspectionIntentUpdateRequest,
    user: AuthenticatedUserDep,
    workflow: HiveConfigurationWorkflowDep,
) -> InspectionResponse:
    return workflow.update_inspection_intent(
        user=user,
        workspace_id=request.workspace_id,
        inspection_id=inspection_id,
        intent=request.intent,
    )


@app.get("/v1/inspections/{inspection_id}/photos", response_model=InspectionPhotoListResponse)
def list_inspection_photos(
    inspection_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    state: DevStateDep,
) -> InspectionPhotoListResponse:
    return state.store.list_inspection_photos(
        user=user,
        workspace_id=workspace_id,
        inspection_id=inspection_id,
    )


@app.get(
    "/v1/inspections/{inspection_id}/frame-observations",
    response_model=InspectionFrameObservationListResponse,
)
def list_inspection_frame_observations(
    inspection_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    state: DevStateDep,
) -> InspectionFrameObservationListResponse:
    return state.store.list_inspection_frame_observations(
        user=user,
        workspace_id=workspace_id,
        inspection_id=inspection_id,
    )


@app.patch(
    "/v1/inspection-frame-observations/{inspection_frame_observation_id}",
    response_model=InspectionFrameObservationResponse,
)
def update_inspection_frame_observation(
    inspection_frame_observation_id: UUID,
    request: InspectionFrameObservationUpdateRequest,
    user: AuthenticatedUserDep,
    state: DevStateDep,
) -> InspectionFrameObservationResponse:
    return state.store.update_inspection_frame_observation(
        user=user,
        workspace_id=request.workspace_id,
        inspection_frame_observation_id=inspection_frame_observation_id,
        observation_status=request.observation_status,
        continuity_status=request.continuity_status,
        notes=request.notes,
    )


@app.post("/v1/inspection-photos/intake", response_model=PhotoIntakeResponse, status_code=202)
async def accept_inspection_photo(
    workspace_id: UUID,
    inspection_id: UUID,
    request: Request,
    user: AuthenticatedUserDep,
    photo_access: InspectionPhotoAccessDep,
    inspection_frame_observation_id: UUID | None = None,
    frame_side: FrameSide | None = None,
    x_hivesight_filename: Annotated[str | None, Header(alias="x-hivesight-filename")] = None,
) -> PhotoIntakeResponse:
    content_type = request.headers.get("content-type", "")
    filename = x_hivesight_filename or "inspection-photo"
    return photo_access.accept_photo_for_analysis(
        user=user,
        workspace_id=workspace_id,
        inspection_id=inspection_id,
        filename=filename,
        content_type=content_type,
        body=await request.body(),
        inspection_frame_observation_id=inspection_frame_observation_id,
        frame_side=frame_side,
    )


@app.post("/v1/analysis-runs", response_model=AnalysisRunResponse, status_code=202)
def request_analysis(
    request: AnalysisRunRequest,
    workflow: AnalysisRequestWorkflowDep,
) -> AnalysisRunResponse:
    return workflow.request_analysis(request)


@app.get("/v1/analysis-runs/{analysis_run_id}", response_model=AnalysisRunResponse)
def get_analysis_run(
    analysis_run_id: UUID,
    workflow: AnalysisRequestWorkflowDep,
) -> AnalysisRunResponse:
    return workflow.get_analysis_status(analysis_run_id)


@app.get("/v1/analysis-runs/{analysis_run_id}/detail", response_model=AnalysisRunDetailResponse)
def get_analysis_run_detail(
    analysis_run_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: AnalysisProcessingWorkflowDep,
) -> AnalysisRunDetailResponse:
    return workflow.get_analysis_run_detail(
        user=user,
        workspace_id=workspace_id,
        analysis_run_id=analysis_run_id,
    )


@app.get(
    "/v1/inspections/{inspection_id}/analysis-runs",
    response_model=AnalysisRunDetailListResponse,
)
def list_inspection_analysis_runs(
    inspection_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: AnalysisProcessingWorkflowDep,
) -> AnalysisRunDetailListResponse:
    return workflow.list_inspection_analysis_runs(
        user=user,
        workspace_id=workspace_id,
        inspection_id=inspection_id,
    )


@app.get(
    "/v1/analysis-runs/{analysis_run_id}/evidence",
    response_model=AnalysisEvidenceResponse,
)
def get_analysis_evidence(
    analysis_run_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: AnalysisProcessingWorkflowDep,
) -> AnalysisEvidenceResponse:
    return workflow.get_analysis_evidence(
        user=user,
        workspace_id=workspace_id,
        analysis_run_id=analysis_run_id,
    )


@app.get("/v1/inspection-photos/{inspection_photo_id}/content")
def get_inspection_photo_content(
    inspection_photo_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    state: DevStateDep,
) -> Response:
    photo = state.store.require_inspection_photo_for_view(
        user=user,
        workspace_id=workspace_id,
        inspection_photo_id=inspection_photo_id,
    )
    body = state.object_storage.get_object(photo.original_object_key)
    if body is None:
        raise DomainError(
            "photo_view_unavailable",
            "The requested Inspection Photo content is not available.",
            404,
        )
    return Response(content=body, media_type=photo.content_type)


@app.post("/v1/review-decisions", response_model=ReviewDecisionResponse, status_code=201)
def create_review_decision(
    request: ReviewDecisionCreateRequest,
    user: AuthenticatedUserDep,
    state: DevStateDep,
) -> ReviewDecisionResponse:
    return state.store.record_review_decision(
        user=user,
        workspace_id=request.workspace_id,
        subject_type=request.subject_type,
        subject_id=request.subject_id,
        decision=request.decision,
        notes=request.notes,
    )


@app.post("/v1/dataset-items", response_model=DatasetItemResponse, status_code=201)
def create_dataset_item(
    request: DatasetItemCreateRequest,
    user: AuthenticatedUserDep,
    workflow: DatasetRoleAssignmentWorkflowDep,
) -> DatasetItemResponse:
    return workflow.create_dataset_item(
        user=user,
        workspace_id=request.workspace_id,
        labelling_session_id=request.labelling_session_id,
        dataset_role=request.dataset_role,
        assignment_note=request.assignment_note,
        exclusion_reason=request.exclusion_reason,
    )


@app.post(
    "/v1/dataset-labelling-sessions",
    response_model=DatasetLabellingSessionResponse,
    status_code=201,
)
def start_dataset_labelling(
    request: StartDatasetLabellingRequest,
    user: AuthenticatedUserDep,
    workflow: DatasetLabellingWorkflowDep,
) -> DatasetLabellingSessionResponse:
    return workflow.start_labelling(
        user=user,
        workspace_id=request.workspace_id,
        inspection_photo_id=request.inspection_photo_id,
    )


@app.post("/v1/training-crops", response_model=TrainingCropResponse, status_code=201)
def create_training_crop(
    request: TrainingCropCreateRequest,
    user: AuthenticatedUserDep,
    workflow: TrainingCropWorkflowDep,
) -> TrainingCropResponse:
    return workflow.create_training_crop(user=user, request=request)


@app.get(
    "/v1/inspection-photos/{inspection_photo_id}/training-crops",
    response_model=TrainingCropListResponse,
)
def list_training_crops_for_photo(
    inspection_photo_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: TrainingCropWorkflowDep,
) -> TrainingCropListResponse:
    return workflow.list_training_crops_for_photo(
        user=user,
        workspace_id=workspace_id,
        inspection_photo_id=inspection_photo_id,
    )


@app.patch("/v1/training-crops/{training_crop_id}", response_model=TrainingCropResponse)
def update_training_crop(
    training_crop_id: UUID,
    request: TrainingCropUpdateRequest,
    user: AuthenticatedUserDep,
    workflow: TrainingCropWorkflowDep,
) -> TrainingCropResponse:
    return workflow.update_training_crop(
        user=user,
        training_crop_id=training_crop_id,
        request=request,
    )


@app.delete("/v1/training-crops/{training_crop_id}", status_code=204)
def delete_training_crop(
    training_crop_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: TrainingCropWorkflowDep,
) -> Response:
    workflow.delete_training_crop(
        user=user,
        workspace_id=workspace_id,
        training_crop_id=training_crop_id,
    )
    return Response(status_code=204)


@app.post(
    "/v1/training-crops/{training_crop_id}/dataset-item",
    response_model=DatasetItemResponse,
    status_code=201,
)
def create_training_crop_dataset_item(
    training_crop_id: UUID,
    request: TrainingCropDatasetItemCreateRequest,
    user: AuthenticatedUserDep,
    workflow: TrainingCropDatasetItemWorkflowDep,
) -> DatasetItemResponse:
    return workflow.create_dataset_item_from_training_crop(
        user=user,
        training_crop_id=training_crop_id,
        request=request,
    )


@app.post(
    "/v1/review-queue/items",
    response_model=ReviewQueueItemResponse,
    status_code=201,
)
def request_training_crop_review(
    request: ReviewQueueItemCreateRequest,
    user: AuthenticatedUserDep,
    workflow: ReviewQueueWorkflowDep,
) -> ReviewQueueItemResponse:
    return workflow.request_training_crop_review(user=user, request=request)


@app.get(
    "/v1/review-queue/work",
    response_model=ReviewQueueItemListResponse,
)
def list_review_work(
    user: AuthenticatedUserDep,
    workflow: ReviewQueueWorkflowDep,
) -> ReviewQueueItemListResponse:
    return workflow.list_available_work(user=user)


@app.get(
    "/v1/review-queue/history",
    response_model=ReviewQueueItemListResponse,
)
def list_review_history(
    user: AuthenticatedUserDep,
    workflow: ReviewQueueWorkflowDep,
) -> ReviewQueueItemListResponse:
    return workflow.list_review_history(user=user)


@app.get(
    "/v1/review-queue/requested",
    response_model=ReviewQueueItemListResponse,
)
def list_requested_reviews(
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: ReviewQueueWorkflowDep,
) -> ReviewQueueItemListResponse:
    return workflow.list_requested_reviews(user=user, workspace_id=workspace_id)


@app.get(
    "/v1/review-queue/items/{review_queue_item_id}",
    response_model=ReviewQueueItemResponse,
)
def get_review_work_item(
    review_queue_item_id: UUID,
    user: AuthenticatedUserDep,
    workflow: ReviewQueueWorkflowDep,
) -> ReviewQueueItemResponse:
    return workflow.get_available_work_item(user=user, review_queue_item_id=review_queue_item_id)


@app.post(
    "/v1/review-queue/items/{review_queue_item_id}/outcomes",
    response_model=ReviewQueueItemResponse,
    status_code=201,
)
def complete_review_work_item(
    review_queue_item_id: UUID,
    request: ReviewQueueOutcomeCreateRequest,
    user: AuthenticatedUserDep,
    workflow: ReviewQueueWorkflowDep,
) -> ReviewQueueItemResponse:
    return workflow.complete_review(
        user=user,
        review_queue_item_id=review_queue_item_id,
        request=request,
    )


@app.post(
    "/v1/review-queue/items/{review_queue_item_id}/cancel",
    response_model=ReviewQueueItemResponse,
)
def cancel_review_work_item(
    review_queue_item_id: UUID,
    request: ReviewQueueItemCancelRequest,
    user: AuthenticatedUserDep,
    workflow: ReviewQueueWorkflowDep,
) -> ReviewQueueItemResponse:
    return workflow.cancel_review(
        user=user,
        review_queue_item_id=review_queue_item_id,
        request=request,
    )


@app.get("/v1/review-queue/items/{review_queue_item_id}/image")
def get_review_work_item_image(
    review_queue_item_id: UUID,
    user: AuthenticatedUserDep,
    workflow: ReviewQueueWorkflowDep,
    state: DevStateDep,
) -> Response:
    photo = workflow.require_image_access(user=user, review_queue_item_id=review_queue_item_id)
    body = state.object_storage.get_object(photo.original_object_key)
    if body is None:
        raise DomainError(
            "photo_view_unavailable",
            "The requested Review Queue image content is not available.",
            404,
        )
    return Response(content=body, media_type=photo.content_type)


@app.get(
    "/v1/dataset-repository/summary",
    response_model=DatasetRepositorySummaryResponse,
)
def get_dataset_repository_summary(
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: DatasetRepositoryWorkflowDep,
) -> DatasetRepositorySummaryResponse:
    return workflow.summary(user=user, workspace_id=workspace_id)


@app.get(
    "/v1/dataset-repository/items",
    response_model=DatasetRepositoryItemListResponse,
)
def list_dataset_repository_items(
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: DatasetRepositoryWorkflowDep,
    dataset_role: DatasetRole | None = None,
) -> DatasetRepositoryItemListResponse:
    return workflow.list_items(
        user=user,
        workspace_id=workspace_id,
        dataset_role=dataset_role,
    )


@app.get(
    "/v1/dataset-repository/items/{dataset_item_id}",
    response_model=DatasetRepositoryItemDetail,
)
def get_dataset_repository_item(
    dataset_item_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: DatasetRepositoryWorkflowDep,
) -> DatasetRepositoryItemDetail:
    return workflow.detail(
        user=user,
        workspace_id=workspace_id,
        dataset_item_id=dataset_item_id,
    )


@app.post(
    "/v1/dataset-exports/yolo-obb",
    response_model=YoloObbExportResponse,
    status_code=201,
)
def create_yolo_obb_export(
    request: YoloObbExportRequest,
    user: AuthenticatedUserDep,
    state: DevStateDep,
) -> YoloObbExportResponse:
    return state.store.create_yolo_obb_export(user=user, workspace_id=request.workspace_id)


@app.post(
    "/v1/dataset-exports/yolo-obb/package",
    response_model=PhysicalYoloObbExportResponse,
    status_code=201,
)
def create_physical_yolo_obb_export_package(
    request: PhysicalYoloObbExportRequest,
    user: AuthenticatedUserDep,
    state: DevStateDep,
) -> PhysicalYoloObbExportResponse:
    return state.store.create_physical_yolo_obb_export_package(
        user=user,
        workspace_id=request.workspace_id,
        image_loader=state.object_storage.get_object,
        export_root=state.dataset_export_root,
    )


@app.get(
    "/v1/model-training/readiness",
    response_model=ModelTrainingReadinessResponse,
)
def get_model_training_readiness(
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorTrainingWorkflowDep,
    model_purpose: str = "bee_detector",
    dataset_version_id: UUID | None = None,
) -> ModelTrainingReadinessResponse:
    return workflow.readiness(
        user=user,
        workspace_id=workspace_id,
        model_purpose=model_purpose,
        dataset_version_id=dataset_version_id,
    )


@app.get(
    "/v1/model-training/bee-training/readiness",
    response_model=BeeTrainingReadinessResponse,
)
def get_bee_training_readiness(
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorTrainingWorkflowDep,
    dataset_version_id: UUID | None = None,
) -> BeeTrainingReadinessResponse:
    return workflow.bee_training_readiness(
        user=user,
        workspace_id=workspace_id,
        dataset_version_id=dataset_version_id,
    )


@app.get(
    "/v1/model-runtime/varroa-detector/readiness",
    response_model=VarroaDetectorReadinessResponse,
)
def get_varroa_detector_readiness(user: AuthenticatedUserDep) -> VarroaDetectorReadinessResponse:
    _ = user
    settings = get_settings()
    adapter = build_configured_varroa_detector_adapter(settings)
    available = True
    unavailable_reason = None
    readiness = getattr(adapter, "readiness", None)
    if callable(readiness):
        available, unavailable_reason = readiness()
    return VarroaDetectorReadinessResponse(
        adapter_type=adapter.adapter_type,
        adapter_version=adapter.adapter_version,
        model_reference=adapter.model_reference,
        available=available,
        unavailable_reason=unavailable_reason,
        database_purpose=settings.database_purpose,
        deterministic_stub_evidence=adapter.adapter_type == "deterministic_stub",
        replaceable_non_stub_adapter=adapter.adapter_type != "deterministic_stub",
        last_validation_error=getattr(adapter, "last_validation_error", None),
    )


@app.post(
    "/v1/model-training/dataset-versions",
    response_model=DatasetVersionResponse,
    status_code=201,
)
def create_model_training_dataset_version(
    request: DatasetVersionCreateRequest,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorTrainingWorkflowDep,
) -> DatasetVersionResponse:
    return workflow.create_dataset_version(
        user=user,
        workspace_id=request.workspace_id,
        purpose=request.purpose,
    )


@app.get(
    "/v1/model-training/dataset-versions",
    response_model=DatasetVersionListResponse,
)
def list_model_training_dataset_versions(
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorTrainingWorkflowDep,
) -> DatasetVersionListResponse:
    return DatasetVersionListResponse(
        dataset_versions=workflow.list_dataset_versions(
            user=user,
            workspace_id=workspace_id,
        )
    )


@app.get(
    "/v1/model-training/dataset-versions/{dataset_version_id}",
    response_model=DatasetVersionResponse,
)
def get_model_training_dataset_version(
    dataset_version_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorTrainingWorkflowDep,
) -> DatasetVersionResponse:
    return workflow.get_dataset_version(
        user=user,
        workspace_id=workspace_id,
        dataset_version_id=dataset_version_id,
    )


@app.post(
    "/v1/model-training/training-runs",
    response_model=TrainingRunResponse,
    status_code=202,
)
def start_model_training_run(
    request: TrainingRunStartRequest,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorTrainingWorkflowDep,
) -> TrainingRunResponse:
    return workflow.start_training_run(user=user, request=request)


@app.post(
    "/v1/model-training/bee-training/runs",
    response_model=BeeTrainingStartResponse,
    status_code=202,
)
def start_bee_training_run(
    request: BeeTrainingStartRequest,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorTrainingWorkflowDep,
) -> BeeTrainingStartResponse:
    return workflow.start_bee_training(user=user, request=request)


@app.get(
    "/v1/model-training/training-runs",
    response_model=TrainingRunListResponse,
)
def list_model_training_runs(
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorTrainingWorkflowDep,
) -> TrainingRunListResponse:
    return TrainingRunListResponse(
        training_runs=workflow.list_training_runs(user=user, workspace_id=workspace_id)
    )


@app.get(
    "/v1/model-training/training-runs/{training_run_id}",
    response_model=TrainingRunResponse,
)
def get_model_training_run(
    training_run_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorTrainingWorkflowDep,
) -> TrainingRunResponse:
    return workflow.get_training_run(
        user=user,
        workspace_id=workspace_id,
        training_run_id=training_run_id,
    )


@app.post(
    "/v1/model-training/training-runs/{training_run_id}/cancel",
    response_model=TrainingRunResponse,
)
def cancel_model_training_run(
    training_run_id: UUID,
    request: TrainingRunCancelRequest,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorTrainingWorkflowDep,
) -> TrainingRunResponse:
    return workflow.cancel_training_run(
        user=user,
        training_run_id=training_run_id,
        request=request,
    )


@app.post(
    "/v1/model-training/training-runs/{training_run_id}/abandon",
    response_model=TrainingRunResponse,
)
def abandon_model_training_run(
    training_run_id: UUID,
    request: TrainingRunAbandonRequest,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorTrainingWorkflowDep,
) -> TrainingRunResponse:
    return workflow.abandon_training_run(
        user=user,
        training_run_id=training_run_id,
        request=request,
    )


@app.delete(
    "/v1/model-training/training-runs/{training_run_id}",
    response_model=TrainingRunDeleteResponse,
)
def delete_model_training_run(
    training_run_id: UUID,
    request: TrainingRunDeleteRequest,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorTrainingWorkflowDep,
) -> TrainingRunDeleteResponse:
    return workflow.delete_training_run(
        user=user,
        training_run_id=training_run_id,
        request=request,
    )


@app.get(
    "/v1/model-training/model-candidates",
    response_model=ModelCandidateListResponse,
)
def list_model_candidates(
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorTrainingWorkflowDep,
) -> ModelCandidateListResponse:
    return ModelCandidateListResponse(
        model_candidates=workflow.list_model_candidates(user=user, workspace_id=workspace_id)
    )


@app.post(
    "/v1/dev/directed-ellipse-orientation-cleanup",
    response_model=DirectedEllipseLocalCleanupResponse,
)
def reset_directed_ellipse_local_evidence(
    request: DirectedEllipseLocalCleanupRequest,
    user: AuthenticatedUserDep,
    workflow: DirectedEllipseCleanupWorkflowDep,
) -> DirectedEllipseLocalCleanupResponse:
    return workflow.reset_dataset_and_model_evidence(user=user, request=request)


@app.get(
    "/v1/model-training/model-candidates/{model_candidate_id}",
    response_model=ModelCandidateResponse,
)
def get_model_candidate(
    model_candidate_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorTrainingWorkflowDep,
) -> ModelCandidateResponse:
    return workflow.get_model_candidate(
        user=user,
        workspace_id=workspace_id,
        model_candidate_id=model_candidate_id,
    )


@app.get(
    "/v1/model-training/model-candidates/{model_candidate_id}/benchmark-readiness",
    response_model=BenchmarkEvaluationReadinessResponse,
)
def get_model_candidate_benchmark_readiness(
    model_candidate_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorBenchmarkEvaluationWorkflowDep,
) -> BenchmarkEvaluationReadinessResponse:
    return workflow.readiness(
        user=user,
        workspace_id=workspace_id,
        model_candidate_id=model_candidate_id,
    )


@app.post(
    "/v1/model-training/benchmark-evaluations",
    response_model=BenchmarkEvaluationResponse,
    status_code=202,
)
def start_model_candidate_benchmark_evaluation(
    request: BenchmarkEvaluationStartRequest,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorBenchmarkEvaluationWorkflowDep,
) -> BenchmarkEvaluationResponse:
    return workflow.start_evaluation(user=user, request=request)


@app.get(
    "/v1/model-training/model-candidates/{model_candidate_id}/orientation-benchmark-readiness",
    response_model=OrientationBenchmarkReadinessResponse,
)
def get_orientation_model_candidate_benchmark_readiness(
    model_candidate_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: BeeOrientationBenchmarkEvaluationWorkflowDep,
) -> OrientationBenchmarkReadinessResponse:
    return workflow.readiness(
        user=user,
        workspace_id=workspace_id,
        model_candidate_id=model_candidate_id,
    )


@app.post(
    "/v1/model-training/orientation-benchmark-evaluations",
    response_model=BenchmarkEvaluationResponse,
    status_code=202,
)
def start_orientation_model_candidate_benchmark_evaluation(
    request: BenchmarkEvaluationStartRequest,
    user: AuthenticatedUserDep,
    workflow: BeeOrientationBenchmarkEvaluationWorkflowDep,
) -> BenchmarkEvaluationResponse:
    return workflow.start_evaluation(user=user, request=request)


@app.get(
    "/v1/model-training/benchmark-evaluations",
    response_model=BenchmarkEvaluationListResponse,
)
def list_model_candidate_benchmark_evaluations(
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorBenchmarkEvaluationWorkflowDep,
) -> BenchmarkEvaluationListResponse:
    return BenchmarkEvaluationListResponse(
        benchmark_evaluations=workflow.list_evaluations(
            user=user,
            workspace_id=workspace_id,
        )
    )


@app.get(
    "/v1/model-training/benchmark-evaluations/{benchmark_evaluation_id}",
    response_model=BenchmarkEvaluationResponse,
)
def get_model_candidate_benchmark_evaluation(
    benchmark_evaluation_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorBenchmarkEvaluationWorkflowDep,
) -> BenchmarkEvaluationResponse:
    return workflow.get_evaluation(
        user=user,
        workspace_id=workspace_id,
        benchmark_evaluation_id=benchmark_evaluation_id,
    )


@app.post(
    "/v1/model-training/benchmark-evaluations/{benchmark_evaluation_id}/cancel",
    response_model=BenchmarkEvaluationResponse,
)
def cancel_model_candidate_benchmark_evaluation(
    benchmark_evaluation_id: UUID,
    request: BenchmarkEvaluationCancelRequest,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorBenchmarkEvaluationWorkflowDep,
) -> BenchmarkEvaluationResponse:
    return workflow.cancel_evaluation(
        user=user,
        benchmark_evaluation_id=benchmark_evaluation_id,
        request=request,
    )


@app.get("/v1/model-training/artifacts/{artifact_id}")
def get_model_training_artifact(
    artifact_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorTrainingWorkflowDep,
) -> Response:
    artifact, body = workflow.get_artifact(
        user=user,
        workspace_id=workspace_id,
        artifact_id=artifact_id,
    )
    return Response(content=body, media_type=artifact.content_type)


@app.get(
    "/v1/training-crops/{training_crop_id}/evidence",
    response_model=TrainingCropEvidenceResponse,
)
def get_training_crop_evidence(
    training_crop_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: TrainingCropWorkflowDep,
) -> TrainingCropEvidenceResponse:
    return workflow.get_training_crop_evidence(
        user=user,
        workspace_id=workspace_id,
        training_crop_id=training_crop_id,
    )


@app.get(
    "/v1/training-crops/{training_crop_id}/varroa-review-candidates",
    response_model=VarroaReviewCandidateListResponse,
)
def list_varroa_review_candidates(
    training_crop_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: VarroaReviewWorkflowDep,
) -> VarroaReviewCandidateListResponse:
    return workflow.list_candidates(
        user=user,
        workspace_id=workspace_id,
        training_crop_id=training_crop_id,
    )


@app.get(
    "/v1/training-crops/{training_crop_id}/varroa-review-candidates/{bee_annotation_id}/head-up-normalized-preview",
    response_model=HeadUpNormalizedBeeCropPreviewResponse,
)
def get_head_up_normalized_preview(
    training_crop_id: UUID,
    bee_annotation_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: VarroaReviewWorkflowDep,
) -> HeadUpNormalizedBeeCropPreviewResponse:
    return workflow.get_preview_metadata(
        user=user,
        workspace_id=workspace_id,
        training_crop_id=training_crop_id,
        bee_annotation_id=bee_annotation_id,
    )


@app.get(
    "/v1/training-crops/{training_crop_id}/varroa-review-candidates/{bee_annotation_id}/head-up-normalized-image",
)
def get_head_up_normalized_image(
    training_crop_id: UUID,
    bee_annotation_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: VarroaReviewWorkflowDep,
) -> Response:
    image = workflow.get_preview_image(
        user=user,
        workspace_id=workspace_id,
        training_crop_id=training_crop_id,
        bee_annotation_id=bee_annotation_id,
    )
    return Response(content=image.body, media_type=image.content_type)


@app.put(
    "/v1/training-crops/{training_crop_id}/varroa-review-candidates/{bee_annotation_id}/outcome",
    response_model=VarroaReviewOutcomeResponse,
)
def save_varroa_review_outcome(
    training_crop_id: UUID,
    bee_annotation_id: UUID,
    request: VarroaReviewOutcomeCreateRequest,
    user: AuthenticatedUserDep,
    workflow: VarroaReviewWorkflowDep,
) -> VarroaReviewOutcomeResponse:
    return workflow.save_outcome(
        user=user,
        training_crop_id=training_crop_id,
        bee_annotation_id=bee_annotation_id,
        request=request,
    )


@app.post(
    "/v1/training-crops/{training_crop_id}/varroa-review-candidates/{bee_annotation_id}/detector-preview",
    response_model=VarroaDetectorPreviewResponse,
)
def preview_varroa_detector_detections(
    training_crop_id: UUID,
    bee_annotation_id: UUID,
    request: VarroaDetectorPreviewRequest,
    user: AuthenticatedUserDep,
    workflow: VarroaReviewWorkflowDep,
) -> VarroaDetectorPreviewResponse:
    return workflow.preview_varroa_detections(
        user=user,
        workspace_id=request.workspace_id,
        training_crop_id=training_crop_id,
        bee_annotation_id=bee_annotation_id,
    )


@app.post(
    "/v1/inspection-photos/{inspection_photo_id}/frame-mite-count",
    response_model=FrameMiteCountResponse,
)
def count_frame_mites(
    inspection_photo_id: UUID,
    request: FrameMiteCountRequest,
    user: AuthenticatedUserDep,
    workflow: VarroaReviewWorkflowDep,
) -> FrameMiteCountResponse:
    return workflow.count_frame_mites(
        user=user,
        workspace_id=request.workspace_id,
        inspection_photo_id=inspection_photo_id,
    )


@app.post(
    "/v1/inspection-photos/{inspection_photo_id}/varroa-photo-analyses",
    response_model=VarroaPhotoAnalysisRunResponse,
    status_code=202,
)
def run_varroa_photo_analysis(
    inspection_photo_id: UUID,
    request: VarroaPhotoAnalysisCreateRequest,
    background_tasks: BackgroundTasks,
    user: AuthenticatedUserDep,
    workflow: VarroaPhotoAnalysisWorkflowDep,
) -> VarroaPhotoAnalysisRunResponse:
    run = workflow.enqueue_photo_analysis(
        user=user,
        workspace_id=request.workspace_id,
        inspection_photo_id=inspection_photo_id,
    )
    background_tasks.add_task(
        workflow.process_photo_analysis_run,
        request.workspace_id,
        run.photo_analysis_run_id,
    )
    return run


@app.post(
    "/v1/inspections/{inspection_id}/varroa-photo-analyses/batch",
    response_model=VarroaPhotoAnalysisBatchResponse,
    status_code=201,
)
def run_all_varroa_photo_analyses(
    inspection_id: UUID,
    request: VarroaPhotoAnalysisCreateRequest,
    user: AuthenticatedUserDep,
    workflow: VarroaPhotoAnalysisWorkflowDep,
) -> VarroaPhotoAnalysisBatchResponse:
    return workflow.run_all_photo_analyses(user, request.workspace_id, inspection_id)


@app.get(
    "/v1/inspection-photos/{inspection_photo_id}/varroa-photo-analyses",
    response_model=VarroaPhotoAnalysisRunListResponse,
)
def list_varroa_photo_analyses(
    inspection_photo_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: VarroaPhotoAnalysisWorkflowDep,
) -> VarroaPhotoAnalysisRunListResponse:
    return workflow.list_photo_analyses(
        user=user,
        workspace_id=workspace_id,
        inspection_photo_id=inspection_photo_id,
    )


@app.get(
    "/v1/varroa-photo-analyses/{photo_analysis_run_id}/bee-results/{photo_analysis_bee_result_id}/head-up-image"
)
def get_varroa_photo_analysis_bee_evidence_image(
    photo_analysis_run_id: UUID,
    photo_analysis_bee_result_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: VarroaPhotoAnalysisWorkflowDep,
) -> Response:
    return Response(
        content=workflow.get_bee_evidence_image(
            user=user,
            workspace_id=workspace_id,
            photo_analysis_run_id=photo_analysis_run_id,
            photo_analysis_bee_result_id=photo_analysis_bee_result_id,
        ),
        media_type="image/png",
    )


@app.patch(
    "/v1/varroa-photo-analyses/{photo_analysis_run_id}/review",
    response_model=VarroaPhotoAnalysisRunResponse,
)
def review_varroa_photo_analysis(
    photo_analysis_run_id: UUID,
    request: VarroaPhotoAnalysisReviewRequest,
    user: AuthenticatedUserDep,
    workflow: VarroaPhotoAnalysisWorkflowDep,
) -> VarroaPhotoAnalysisRunResponse:
    return workflow.review_photo_analysis(
        user=user,
        photo_analysis_run_id=photo_analysis_run_id,
        request=request,
    )


@app.post(
    "/v1/hives/{hive_id}/advisor-varroa-context",
    response_model=AdvisorVarroaContextResponse,
)
def assemble_advisor_varroa_context(
    hive_id: UUID,
    request: AdvisorVarroaContextRequest,
    user: AuthenticatedUserDep,
    workflow: AdvisorVarroaContextWorkflowDep,
) -> AdvisorVarroaContextResponse:
    return workflow.assemble_context(
        user=user,
        hive_id=hive_id,
        inspection_photo_id=request.inspection_photo_id,
        jurisdiction_id=request.jurisdiction_id,
    )


@app.post(
    "/v1/hives/{hive_id}/advisor-treatment-recommendations",
    response_model=TreatmentEvidenceChainDetailResponse,
    status_code=201,
)
def request_advisor_treatment_recommendation(
    hive_id: UUID,
    request: AdvisorTreatmentRecommendationCreateRequest,
    user: AuthenticatedUserDep,
    workflow: AdvisorTreatmentRecommendationWorkflowDep,
) -> TreatmentEvidenceChainDetailResponse:
    return workflow.request_treatment_advice(user=user, hive_id=hive_id, request=request)


@app.get(
    "/v1/hives/{hive_id}/treatment-recommendations",
    response_model=TreatmentRecommendationListResponse,
)
def list_treatment_recommendations(
    hive_id: UUID,
    user: AuthenticatedUserDep,
    workflow: AdvisorTreatmentRecommendationWorkflowDep,
) -> TreatmentRecommendationListResponse:
    return workflow.list_treatment_recommendations(user=user, hive_id=hive_id)


@app.post(
    "/v1/treatment-recommendations/{treatment_recommendation_id}/accept",
    response_model=HiveTreatmentCourseResponse,
)
def accept_treatment_recommendation(
    treatment_recommendation_id: UUID,
    request: TreatmentRecommendationDecisionRequest,
    user: AuthenticatedUserDep,
    workflow: AdvisorTreatmentRecommendationWorkflowDep,
) -> HiveTreatmentCourseResponse:
    return workflow.accept_recommendation(
        user=user,
        treatment_recommendation_id=treatment_recommendation_id,
        note=request.note,
    )


@app.post(
    "/v1/treatment-recommendations/{treatment_recommendation_id}/decline",
    response_model=TreatmentRecommendationResponse,
)
def decline_treatment_recommendation(
    treatment_recommendation_id: UUID,
    request: TreatmentRecommendationDecisionRequest,
    user: AuthenticatedUserDep,
    workflow: AdvisorTreatmentRecommendationWorkflowDep,
) -> TreatmentRecommendationResponse:
    return workflow.decline_recommendation(
        user=user,
        treatment_recommendation_id=treatment_recommendation_id,
        note=request.note,
    )


@app.get(
    "/v1/hives/{hive_id}/treatment-courses",
    response_model=HiveTreatmentCourseListResponse,
)
def list_hive_treatment_courses(
    hive_id: UUID,
    user: AuthenticatedUserDep,
    workflow: AdvisorTreatmentRecommendationWorkflowDep,
) -> HiveTreatmentCourseListResponse:
    return workflow.list_treatment_courses(user=user, hive_id=hive_id)


@app.get(
    "/v1/hives/{hive_id}/advisor-treatment-advice-attempts",
    response_model=TreatmentEvidenceChainListResponse,
)
def list_advisor_treatment_advice_attempts(
    hive_id: UUID,
    user: AuthenticatedUserDep,
    workflow: AdvisorTreatmentRecommendationWorkflowDep,
) -> TreatmentEvidenceChainListResponse:
    return workflow.list_advice_attempts(user=user, hive_id=hive_id)


@app.get(
    "/v1/treatment-evidence-chains/{treatment_evidence_chain_id}",
    response_model=TreatmentEvidenceChainDetailResponse,
)
def get_treatment_evidence_chain(
    treatment_evidence_chain_id: UUID,
    user: AuthenticatedUserDep,
    workflow: AdvisorTreatmentRecommendationWorkflowDep,
) -> TreatmentEvidenceChainDetailResponse:
    return workflow.get_treatment_evidence_chain(
        user=user,
        treatment_evidence_chain_id=treatment_evidence_chain_id,
    )


@app.get(
    "/v1/inspection-photos/{inspection_photo_id}/photo-visible-varroa-summary",
    response_model=FrameLevelVarroaResultSummaryResponse,
)
def get_photo_visible_varroa_summary(
    inspection_photo_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: FrameLevelVarroaResultWorkflowDep,
) -> FrameLevelVarroaResultSummaryResponse:
    return workflow.get_photo_visible_summary(
        user=user,
        workspace_id=workspace_id,
        inspection_photo_id=inspection_photo_id,
    )


@app.post(
    "/v1/training-crops/{training_crop_id}/candidate-bee-annotations",
    response_model=BeeAnnotationProposalListResponse,
)
def suggest_training_crop_bee_annotations(
    training_crop_id: UUID,
    request: BeeAnnotationProposalRequest,
    user: AuthenticatedUserDep,
    workflow: BeeDetectorCandidateAnnotationWorkflowDep,
) -> BeeAnnotationProposalListResponse:
    return workflow.suggest_bee_annotations(
        user=user,
        training_crop_id=training_crop_id,
        request=request,
    )


@app.post(
    "/v1/training-crops/{training_crop_id}/bee-ellipses",
    response_model=OrientedBeeEllipseResponse,
    status_code=201,
)
def create_training_crop_ellipse(
    training_crop_id: UUID,
    request: OrientedBeeEllipseCreateRequest,
    user: AuthenticatedUserDep,
    workflow: TrainingCropWorkflowDep,
) -> OrientedBeeEllipseResponse:
    return workflow.create_training_crop_ellipse(
        user=user,
        training_crop_id=training_crop_id,
        request=request,
    )


@app.patch(
    "/v1/training-crop-bee-ellipses/{annotation_id}",
    response_model=OrientedBeeEllipseResponse,
)
def update_training_crop_ellipse(
    annotation_id: UUID,
    request: OrientedBeeEllipseUpdateRequest,
    user: AuthenticatedUserDep,
    workflow: TrainingCropWorkflowDep,
) -> OrientedBeeEllipseResponse:
    return workflow.update_training_crop_ellipse(
        user=user,
        annotation_id=annotation_id,
        request=request,
    )


@app.delete("/v1/training-crop-bee-ellipses/{annotation_id}", status_code=204)
def delete_training_crop_ellipse(
    annotation_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: TrainingCropWorkflowDep,
) -> Response:
    workflow.delete_training_crop_ellipse(
        user=user,
        workspace_id=workspace_id,
        annotation_id=annotation_id,
    )
    return Response(status_code=204)


@app.patch(
    "/v1/dataset-labelling-sessions/{labelling_session_id}",
    response_model=DatasetLabellingSessionResponse,
)
def update_dataset_labelling_session(
    labelling_session_id: UUID,
    request: UpdateDatasetLabellingSessionRequest,
    user: AuthenticatedUserDep,
    workflow: DatasetLabellingWorkflowDep,
) -> DatasetLabellingSessionResponse:
    return workflow.update_session_metadata(
        user=user,
        workspace_id=request.workspace_id,
        labelling_session_id=labelling_session_id,
        source_group_key=request.source_group_key,
        image_quality_status=request.image_quality_status,
    )


@app.get(
    "/v1/dataset-labelling-sessions/{labelling_session_id}/evidence",
    response_model=DatasetLabellingEvidenceResponse,
)
def get_dataset_labelling_evidence(
    labelling_session_id: UUID,
    workspace_id: UUID,
    user: AuthenticatedUserDep,
    workflow: DatasetLabellingWorkflowDep,
) -> DatasetLabellingEvidenceResponse:
    return workflow.get_labelling_evidence(
        user=user,
        workspace_id=workspace_id,
        labelling_session_id=labelling_session_id,
    )


@app.post(
    "/v1/analysis-runs/{analysis_run_id}/process",
    response_model=AnalysisRunDetailResponse,
    status_code=202,
)
def process_analysis_run(
    analysis_run_id: UUID,
    request: ProcessAnalysisRunRequest,
    user: AuthenticatedUserDep,
    workflow: AnalysisProcessingWorkflowDep,
) -> AnalysisRunDetailResponse:
    return workflow.process_queued_analysis(
        user=user,
        workspace_id=request.workspace_id,
        analysis_run_id=analysis_run_id,
    )
