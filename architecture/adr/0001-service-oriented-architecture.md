# Service-Oriented Application Architecture

Status: accepted

BeehiveMonitor will start as a service-oriented system in a monorepo, with separately deployable applications and services rather than a single tightly coupled application. The first application boundary is a TypeScript web frontend calling a protected Core API. The Core API owns the beekeeper-facing product workflow: Workspaces, apiaries, hives, inspections, inspection photos, Workspace Data Use Agreement state, and user-facing authorization.

Image analysis will run behind a separate private Analysis Service. The Core API will submit analysis work asynchronously through a queue, and the Analysis Service will own detailed analysis job state, detections, analysis runs, generated tagged outputs, and model-version traceability. The frontend will read analysis status and results through the Core API rather than calling the Analysis Service directly.

Python is the preferred backend language for the Core API and Analysis Service because the project expects close integration with predictive AI, model inference, model evaluation, and likely generative AI-assisted workflows. FastAPI is the preferred starting point for Python APIs. The web frontend will use TypeScript. Service contracts should be explicit, with OpenAPI used for client/API contracts where practical.

The Core API is internet-reachable but protected, not public-open. A logical API Gateway or edge layer will sit in front of it for TLS termination, routing, client checks, rate limiting, request limits, and abuse protection. User-facing operations require user identity and Workspace authorization. Trusted backend integrations may use service-to-service credentials with narrow scopes. Browser and mobile clients must not depend on embedded long-lived secrets.

Original inspection photos, generated tagged images, and later model artifacts will be stored in S3-compatible object storage. The Core API stores metadata and object references, not image bytes as the long-term pattern. Upload and download/view access should use short-lived, single-action, object-scoped URLs after authorization. A local prototype may temporarily proxy uploads or image delivery through the Core API if that accelerates early learning, but the contract must preserve the target signed-URL pattern.

The model training and evaluation workflow is separate from the V1 runtime services. Runtime services handle upload, analysis jobs, inference, results, and review evidence. The offline model-development pipeline curates datasets, trains models, evaluates against protected benchmarks, and promotes model versions. A lightweight Model Registry concept is required from the start so every analysis run can be traced to the model version that produced it.

## Considered Options

- **Single monolith**: simpler to start, but risks coupling product workflow, image processing, storage, model execution, and future client needs too early.
- **Full microservices from every domain concept**: maximizes separation, but would add coordination overhead before the domain and product workflows have stabilized.
- **Service-oriented modular system**: chosen because it gives clear boundaries around frontend, Core API, analysis, storage, and model governance while preserving early delivery speed.

## Consequences

- The first codebase can be a monorepo, but services and apps must remain separately deployable.
- The frontend gets one stable product-facing API boundary even as analysis internals evolve.
- The Analysis Service can scale differently from the Core API and can grow into model-runtime work without exposing model internals to clients.
- Service ownership must be respected even if local development initially uses simpler shared infrastructure.
- Analysis work is asynchronous, so the product must expose job status and delayed results rather than assuming immediate image analysis.
- API contracts, authentication, authorization, and object-storage access patterns must be designed early enough to avoid accidental tight coupling.
- Vendor choices for queue, object storage provider, auth provider, API gateway, database, and deployment platform remain open.

