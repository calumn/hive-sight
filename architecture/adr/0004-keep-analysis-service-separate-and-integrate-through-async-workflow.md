# Keep Analysis Service Separate And Integrate Through Async Workflow

Status: accepted

## Context

HiveSight's service-oriented architecture has always separated the Web App, Core API, and Analysis Service. The Analysis Service is tested, but the current product workflow still uses in-process Core API stub analysis. That split is acceptable for early delivery, but it becomes confusing before real model inference and training work deepen.

The project needs a clear direction before adding a real detector baseline, Analysis Service job contracts, or durable queue technology.

## Decision

HiveSight will keep the Analysis Service as a separate private service.

The Core API will integrate with it through an asynchronous workflow shape:

- Core API owns product workflow, Workspace authorization, upload eligibility, user-facing analysis status, and result projection.
- Core API publishes or records analysis requests through an owned queue adapter seam.
- Analysis Service owns model runtime execution, analysis job processing, detailed model output normalization, and model-runtime traceability.
- The first integration implementation should use an in-memory queue adapter and explicit request/result contracts before choosing durable queue technology.
- Browser and mobile clients continue to call only the Core API, not the Analysis Service.

## Considered Options

- **Fold analysis back into Core API**: simpler locally, but blurs product workflow, model runtime, and future scaling concerns.
- **Keep services separate with synchronous HTTP calls only**: clearer than in-process analysis, but a poor fit for long-running image analysis and future batch/model workloads.
- **Keep services separate with async workflow**: preserves the intended service boundary while allowing a simple local adapter before durable queue selection.

## Rationale

Image analysis is naturally asynchronous. Keeping a private Analysis Service lets model runtime dependencies, model artifacts, and eventual resource needs evolve separately from the product-facing API.

Using an in-memory queue adapter first avoids choosing Redis, RabbitMQ, cloud queues, or another durable queue before HiveSight has enough integration evidence. The important near-term decision is the boundary shape, not the vendor.

## Consequences

- Core API route handlers must not learn Analysis Service internals.
- Analysis request/result contracts become important and should trigger API contract governance before implementation.
- Durable queue technology remains parked until the in-memory adapter and service contract prove the workflow shape.
- Analysis Store ownership remains deferred. Slice 0014 persistence is Core API-owned only.
- Slice 0015 YOLO OBB Training Baseline is not blocked by implementing this integration, but the direction is now recorded before model work deepens.

