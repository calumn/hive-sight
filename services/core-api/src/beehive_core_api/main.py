from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from beehive_core_api.analysis_request_workflow import AnalysisRequestWorkflow
from beehive_core_api.dependencies import (
    get_analysis_request_workflow,
    get_inspection_photo_access,
    get_settings,
)
from beehive_core_api.inspection_photo_access import InspectionPhotoAccess
from beehive_core_api.models import (
    AnalysisRunRequest,
    AnalysisRunResponse,
    HealthResponse,
    UploadUrlResponse,
)

settings = get_settings()

app = FastAPI(
    title="BeehiveMonitor Core API",
    version="0.1.0",
    description="Protected product-facing API for BeehiveMonitor.",
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


@app.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    return HealthResponse(
        service="core-api",
        status="ok",
        boundary="internet-reachable protected API",
    )


@app.get("/v1/inspection-photos/{inspection_photo_id}/upload-url", response_model=UploadUrlResponse)
def create_upload_url(
    inspection_photo_id: UUID,
    photo_access: InspectionPhotoAccessDep,
) -> UploadUrlResponse:
    return photo_access.create_upload_access(inspection_photo_id)


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

