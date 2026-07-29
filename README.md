# HiveSight

HiveSight is a Varroa-focused inspection support system for hobbyist and small-scale beekeepers. The registered product domain is hive-sight.com.

The first codebase follows [ADR-0001](architecture/adr/0001-service-oriented-architecture.md): a service-oriented monorepo with a TypeScript web app, Python Core API, private Python Analysis Service, asynchronous analysis boundary, and S3-compatible object storage.

## Structure

- `apps/web`: V1 web interface.
- `services/core-api`: protected product-facing API for Workspaces, apiaries, hives, inspections, photos, upload flows, and user-facing analysis status.
- `services/analysis-service`: private analysis runtime boundary for image-analysis jobs, detections, tagged outputs, and model-version traceability.
- `contracts`: shared API/event contract notes and schemas.
- `infra`: local development infrastructure notes.
- `architecture`: architecture decisions and diagrams.
- `requirements`: requirements and product specification artifacts.

## Local Start

Install dependencies for each surface, then run them in separate terminals:

```sh
docker compose up -d
cd services/core-api && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]" && uvicorn hive_sight_core_api.main:app --reload --port 8000
cd services/analysis-service && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]" && uvicorn hive_sight_analysis_service.main:app --reload --port 8100
pnpm install
pnpm dev:web
```

The first implementation is deliberately a scaffold. It proves the service boundaries before adding persistence, authentication, queues, object-storage signing, and model inference.
