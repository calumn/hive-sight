from typing import Annotated

from fastapi import Depends, FastAPI

from beehive_analysis_service.analysis_job_runner import AnalysisJobRunner
from beehive_analysis_service.dependencies import get_analysis_job_runner
from beehive_analysis_service.models import AnalysisJobRequest, AnalysisJobResult, HealthResponse

app = FastAPI(
    title="BeehiveMonitor Analysis Service",
    version="0.1.0",
    description="Private analysis runtime API for BeehiveMonitor.",
)

AnalysisJobRunnerDep = Annotated[AnalysisJobRunner, Depends(get_analysis_job_runner)]


@app.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    return HealthResponse(
        service="analysis-service",
        status="ok",
        boundary="private service",
    )


@app.post("/v1/jobs", response_model=AnalysisJobResult)
def run_analysis_job(
    request: AnalysisJobRequest,
    runner: AnalysisJobRunnerDep,
) -> AnalysisJobResult:
    return runner.run_analysis_job(request)

