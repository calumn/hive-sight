from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from hive_sight_core_api.analysis_processing_workflow import AnalysisProcessingWorkflow
from hive_sight_core_api.analysis_request_workflow import AnalysisRequestWorkflow
from hive_sight_core_api.bee_detector_training_workflow import BeeDetectorTrainingWorkflow
from hive_sight_core_api.dataset_labelling_workflow import DatasetLabellingWorkflow
from hive_sight_core_api.dataset_role_assignment_workflow import DatasetRoleAssignmentWorkflow
from hive_sight_core_api.dependencies import (
    DevStateDep,
    get_analysis_processing_workflow,
    get_analysis_request_workflow,
    get_bee_detector_training_workflow,
    get_dataset_labelling_workflow,
    get_dataset_role_assignment_workflow,
    get_hive_configuration_workflow,
    get_inspection_photo_access,
    get_settings,
    get_training_crop_dataset_item_workflow,
    get_training_crop_workflow,
)
from hive_sight_core_api.dev_store import DomainError, UserContext
from hive_sight_core_api.hive_configuration_workflow import HiveConfigurationWorkflow
from hive_sight_core_api.inspection_photo_access import InspectionPhotoAccess
from hive_sight_core_api.models import (
    AnalysisEvidenceResponse,
    AnalysisRunDetailResponse,
    AnalysisRunRequest,
    AnalysisRunResponse,
    ApiaryCreateRequest,
    ApiaryListResponse,
    ApiaryResponse,
    DatasetItemCreateRequest,
    DatasetItemResponse,
    DatasetVersionCreateRequest,
    DatasetVersionListResponse,
    DatasetVersionResponse,
    DatasetLabellingEvidenceResponse,
    DatasetLabellingSessionResponse,
    DevSessionResponse,
    ErrorResponse,
    FrameStandardResponse,
    HealthResponse,
    HiveConfigurationResponse,
    HiveConfigurationUpsertRequest,
    HiveCreateRequest,
    HiveListResponse,
    HiveResponse,
    InspectionCreateRequest,
    InspectionIntentUpdateRequest,
    InspectionPhotoListResponse,
    InspectionResponse,
    ModelCandidateListResponse,
    ModelCandidateResponse,
    ModelTrainingReadinessResponse,
    OrientedBeeEllipseCreateRequest,
    OrientedBeeEllipseResponse,
    OrientedBeeEllipseUpdateRequest,
    PhotoIntakeResponse,
    PhysicalYoloObbExportRequest,
    PhysicalYoloObbExportResponse,
    ProcessAnalysisRunRequest,
    ReviewDecisionCreateRequest,
    ReviewDecisionResponse,
    StartDatasetLabellingRequest,
    TrainingCropCreateRequest,
    TrainingCropDatasetItemCreateRequest,
    TrainingCropEvidenceResponse,
    TrainingCropListResponse,
    TrainingCropResponse,
    TrainingCropUpdateRequest,
    TrainingRunListResponse,
    TrainingRunResponse,
    TrainingRunStartRequest,
    UpdateDatasetLabellingSessionRequest,
    WorkspaceDataUseAgreementAcceptanceRequest,
    WorkspaceDataUseAgreementAcceptanceResponse,
    YoloObbExportRequest,
    YoloObbExportResponse,
)
from hive_sight_core_api.training_crop_dataset_item_workflow import (
    TrainingCropDatasetItemWorkflow,
)
from hive_sight_core_api.training_crop_workflow import TrainingCropWorkflow

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
BeeDetectorTrainingWorkflowDep = Annotated[
    BeeDetectorTrainingWorkflow,
    Depends(get_bee_detector_training_workflow),
]
DevUserIdHeader = Annotated[str | None, Header(alias="x-hivesight-dev-user-id")]


def get_dev_user_context(x_hivesight_dev_user_id: DevUserIdHeader = None) -> UserContext:
    if x_hivesight_dev_user_id is None:
        raise DomainError(
            "not_authenticated",
            "Sign in before using Workspace inspection workflows.",
            401,
        )
    try:
        return UserContext(user_id=UUID(x_hivesight_dev_user_id))
    except ValueError as exc:
        raise DomainError(
            "not_authenticated",
            "The dev authentication header was not a valid User id.",
            401,
        ) from exc


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


@app.post("/v1/inspection-photos/intake", response_model=PhotoIntakeResponse, status_code=202)
async def accept_inspection_photo(
    workspace_id: UUID,
    inspection_id: UUID,
    request: Request,
    user: AuthenticatedUserDep,
    photo_access: InspectionPhotoAccessDep,
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
) -> ModelTrainingReadinessResponse:
    return workflow.readiness(user=user, workspace_id=workspace_id)


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
