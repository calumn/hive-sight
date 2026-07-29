from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from hive_sight_core_api.analysis_processing_workflow import AnalysisProcessingWorkflow
from hive_sight_core_api.analysis_request_workflow import AnalysisRequestWorkflow
from hive_sight_core_api.dependencies import (
    DevStateDep,
    get_analysis_processing_workflow,
    get_analysis_request_workflow,
    get_inspection_photo_access,
    get_settings,
)
from hive_sight_core_api.dev_store import DomainError, UserContext
from hive_sight_core_api.inspection_photo_access import InspectionPhotoAccess
from hive_sight_core_api.models import (
    AnalysisEvidenceResponse,
    AnalysisRunDetailResponse,
    AnalysisRunRequest,
    AnalysisRunResponse,
    ApiaryCreateRequest,
    ApiaryResponse,
    DevSessionResponse,
    ErrorResponse,
    HealthResponse,
    HiveCreateRequest,
    HiveResponse,
    InspectionCreateRequest,
    InspectionResponse,
    PhotoIntakeResponse,
    ProcessAnalysisRunRequest,
    ReviewDecisionCreateRequest,
    ReviewDecisionResponse,
    UploadUrlResponse,
    WorkspaceDataUseAgreementAcceptanceRequest,
    WorkspaceDataUseAgreementAcceptanceResponse,
)

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


@app.post("/v1/hives", response_model=HiveResponse, status_code=201)
def create_hive(
    request: HiveCreateRequest,
    user: AuthenticatedUserDep,
    state: DevStateDep,
) -> HiveResponse:
    return state.store.create_hive(user=user, apiary_id=request.apiary_id, name=request.name)


@app.post("/v1/inspections", response_model=InspectionResponse, status_code=201)
def create_inspection(
    request: InspectionCreateRequest,
    user: AuthenticatedUserDep,
    state: DevStateDep,
) -> InspectionResponse:
    return state.store.create_inspection(
        user=user,
        hive_id=request.hive_id,
        inspection_date=request.inspection_date,
    )


@app.get("/v1/inspection-photos/{inspection_photo_id}/upload-url", response_model=UploadUrlResponse)
def create_upload_url(
    inspection_photo_id: UUID,
    photo_access: InspectionPhotoAccessDep,
) -> UploadUrlResponse:
    return photo_access.create_upload_access(inspection_photo_id)


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
