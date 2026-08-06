# Codebase Design

This note applies the `sdlc-architecture-codebase-design` skill to the initial HiveSight scaffold before persistence, queues, storage signing, or model inference are added.

The goal is to avoid a service-oriented codebase made of shallow pass-through files. Each service should grow around deep modules: small interfaces with useful behaviour hidden behind them, tested through those interfaces.

## Current Scaffold Assessment

The current scaffold is deliberately thin:

- the Web App calls the Core API health endpoint
- the Core API exposes stub upload and analysis-run endpoints
- the Analysis Service exposes a stub analysis job endpoint
- event contracts exist for `AnalysisRequested` and `AnalysisCompleted`

This is acceptable as a starting skeleton. It should not become the long-term structure. The next step is to move behaviour out of route handlers and into modules with explicit interfaces.

Slice 0013 accepted Postgres for durable product and model-governance metadata and kept the Analysis Service as a separate async boundary. See `architecture/adr/0003-postgres-for-durable-product-and-model-governance-metadata.md`, `architecture/adr/0004-keep-analysis-service-separate-and-integrate-through-async-workflow.md`, and `architecture/postgres-persistence-design.md`.

## Design Vocabulary

Use these terms consistently in codebase design discussions:

- **Module**: anything with an interface and implementation, from a function to a service package.
- **Interface**: everything a caller must know to use a module correctly, including invariants and errors.
- **Seam**: the place where behaviour can vary without editing the caller.
- **Adapter**: a concrete implementation at a seam, such as a queue adapter, storage adapter, or in-memory test adapter.
- **Depth**: how much useful behaviour sits behind a small interface.

Avoid using `component` or `boundary` when the more precise term is `module`, `interface`, or `seam`.

## Core API Modules

### Current Application Workflow Seams

Review Remediation 0001 moved several recent domain-rule clusters out of the in-memory dev store and into explicit Core API workflows:

- `HiveConfigurationWorkflow`: Frame Standard selection, Hive Configuration validation, Inspection creation gating, and Inspection intent locking.
- `TrainingCropWorkflow`: Training Crop bounds, crop review state, crop locking, oriented bee ellipse validation, and Training Crop evidence projection.
- `TrainingCropDatasetItemWorkflow`: Training Crop Dataset Item assignment, exclusion rules, reviewed ellipse snapshots, and Training Crop provenance snapshot assembly.

`InMemoryProductDataStore` remains the concrete dev repository, but the moved workflows should stay the public application seams for route handlers and direct workflow tests. Do not put these rules back into store adapters when real persistence is introduced.

### Inspection Photo Access

Candidate module:

`InspectionPhotoAccess`

External interface:

```text
create_upload_access(workspace_id, inspection_photo_id, filename, content_type, size_bytes)
create_view_access(workspace_id, inspection_photo_id, rendition)
```

Current implementation note:

Slice 0001 uses the Core API proxied upload path rather than a signed upload-url endpoint. Do not expose a public upload-url route until `create_upload_access(...)` enforces Workspace authorization, Workspace Data Use Agreement status, upload size, content type, object-key scope, expiry, and auditable issued-access metadata behind this module interface.

Behaviour hidden behind the interface:

- Workspace authorization checks
- Workspace Data Use Agreement enforcement
- upload size and content-type validation
- object-key generation
- short-lived upload/view URL creation
- audit metadata for issued access

Dependencies:

- product data store: local-substitutable
- object storage: true external in production, local-substitutable with MinIO in development
- authorization context: in-process initially, later backed by auth provider

Adapter strategy:

- production: S3-compatible storage adapter
- tests: in-memory object-access adapter or MinIO-backed adapter

Design warning:

Do not let route handlers build object keys or sign URLs directly. That would spread storage rules across callers and make the storage seam shallow.

### Analysis Requesting

Candidate module:

`AnalysisRequestWorkflow`

External interface:

```text
request_analysis(workspace_id, inspection_photo_id, requested_model_version=None)
get_analysis_status(workspace_id, analysis_run_id)
```

Behaviour hidden behind the interface:

- Workspace authorization
- photo eligibility checks
- Workspace Data Use Agreement enforcement
- analysis-run creation
- duplicate or re-analysis policy
- event construction
- queue publishing
- user-facing status projection

Dependencies:

- product data store: local-substitutable
- analysis queue: remote but owned once the Analysis Service consumes it
- model registry lookup: local-substitutable initially, possibly remote/owned later

Adapter strategy:

- production: queue adapter publishing `AnalysisRequested`
- tests: in-memory analysis-request adapter that records events

Design warning:

Do not make the Core API route handler know the queue payload shape in detail. The route should call the workflow interface; the workflow owns event construction.

### Bee Detector Training

Candidate module:

`BeeDetectorTrainingWorkflow`

External interface:

```text
get_training_readiness(workspace_id, requested_adapter)
create_dataset_version(workspace_id, selection_criteria)
start_training_run(workspace_id, dataset_version_id, training_settings, warning_acknowledgement)
get_training_run(workspace_id, training_run_id)
get_model_candidate(workspace_id, model_candidate_id)
get_artifact(workspace_id, artifact_id)
```

Behaviour hidden behind the interface:

- Dataset Curator/internal capability authorization
- Dataset Version selection, frozen snapshotting, manifest hashing, and exclusion reasons
- benchmark protection and dataset leakage warnings
- Training Crop image/dimension validation
- oriented ellipse to YOLO OBB projection
- local export package and preview artifact generation
- high-severity warning acknowledgement
- one-active-training-run lock
- model-training adapter selection
- Training Run lifecycle and Model Candidate creation
- artifact record validation and safe artifact serving

Dependencies:

- Postgres-backed product/model governance store
- local filesystem artifact storage
- `BeeDetectorTrainingAdapter`
- authorization/dev-session context

Adapter strategy:

- fast tests: fake `BeeDetectorTrainingAdapter` that writes deterministic fake weights, logs, metrics, report, and artifact manifest
- explicit local real path: Ultralytics YOLO OBB adapter using optional pinned dependencies

Design warning:

Do not make route handlers, UI components, or persistence adapters know YOLO-specific file layout details. YOLO OBB export is a derived projection from canonical Oriented Bee Ellipses. Keep the model-family details inside export/training adapters so HiveSight can change model family later.

Slice 0015 keeps this workflow inside Core API because Dataset Versions, Training Runs, Model Candidates, reports, and artifact metadata are Core API governance records. If training becomes heavy enough to require process isolation, GPU scheduling, or durable job queues, move the adapter execution behind the Analysis Service or a dedicated training worker without changing the public model-training contract.

## Analysis Service Modules

### Analysis Job Runner

Candidate module:

`AnalysisJobRunner`

External interface:

```text
run_analysis_job(analysis_run_id, inspection_photo_id, original_object_key, requested_model_version=None)
```

Behaviour hidden behind the interface:

- source image retrieval
- model-version selection
- bee detection
- Varroa detection
- detection association
- tagged-image rendering
- result persistence
- completion event construction

Dependencies:

- object storage: true external in production, local-substitutable with MinIO in development
- model runtime: in-process for the first stub, later model artifact adapter
- analysis store: local-substitutable
- completion queue/event publisher: remote but owned if events are consumed by Core API

Adapter strategy:

- production: object-storage adapter, model-runtime adapter, analysis-store adapter, event publisher
- tests: in-memory storage/model/store/event adapters

Design warning:

Do not expose bee detection, Varroa detection, rendering, and persistence as separate public service interfaces too early. They can be internal seams inside the Analysis Service until real variation appears.

### Model Runtime

Candidate module:

`ModelRuntime`

External interface:

```text
analyse_photo(image_reference, model_version)
```

Behaviour hidden behind the interface:

- load model artifact
- run the logical bee-detection and Varroa-detection pipeline
- normalize detections into HiveSight annotation terms
- return model-version traceability and quality notes

Dependencies:

- model artifacts: object storage or local filesystem
- predictive AI libraries: in-process

Adapter strategy:

- first implementation: deterministic stub adapter
- later implementation: real inference adapter
- tests: fixture-backed adapter with known detections

Design warning:

One real stub and one future real model adapter justify this seam, but keep the interface small. Avoid leaking framework-specific tensors, model paths, or raw detector outputs to callers.

## Web App Modules

### Core API Client

Candidate module:

`CoreApiClient`

External interface:

```text
get_health()
create_upload_access(...)
request_analysis(...)
get_analysis_run(...)
```

Behaviour hidden behind the interface:

- base URL configuration
- request/response parsing
- auth token attachment once authentication exists
- error normalization for UI workflows

Dependencies:

- Core API: remote but owned

Adapter strategy:

- production: HTTP adapter
- tests: in-memory client adapter

Design warning:

Do not let page components construct URLs, parse response shapes, or know transport details directly. UI code should depend on a small client interface.

## First Seams To Introduce

Introduce seams only when there are at least two adapters or a clear near-term second adapter.

Good early seams:

- object storage access: production S3-compatible adapter plus in-memory/MinIO test adapter
- analysis queue publishing: production Redis/queue adapter plus in-memory test adapter
- model runtime: deterministic stub adapter plus later real inference adapter
- Core API client in the Web App: HTTP adapter plus in-memory test adapter

Seams to defer:

- separate repository interfaces for every domain entity
- separate service clients for internal analysis sub-steps
- plugin-style detector interfaces before the model runtime has real alternatives

## Testing Strategy

The interface is the test surface.

Recommended early test layers:

- Core API route tests for HTTP contract shape.
- `AnalysisRequestWorkflow` tests using in-memory data and queue adapters.
- `InspectionPhotoAccess` tests for authorization, data-use agreement, upload validation, object-key generation, and URL expiry rules.
- `AnalysisJobRunner` tests using fixture images or fake image references and deterministic model-runtime adapters.
- Web App tests around `CoreApiClient` and user-facing workflows once UI workflows become real.
- Playwright browser acceptance tests for implemented Web UI vertical-slice workflows, starting with one reliable Chromium path before adding a browser matrix.
- Slice verification report generation from a repo-level command so service tests, API-level BDD scenarios, Web TypeScript checks, and browser acceptance tests are visible in one human-readable artifact.

Avoid tests that lock onto private helper functions or route-handler internals. If a test has to change when the implementation is reorganized but behaviour is unchanged, it is probably testing past the interface.

Keep client-neutral Gherkin features distinct from API contract tests, lower-level tests, and browser-only visual checks. Where meaningful, one canonical feature can execute through API and browser bindings; Slice 0030 introduces this as a limited pilot while Playwright remains the browser-acceptance default for un-migrated workflows.

## Next Implementation Recommendation

Before adding persistence, queueing, storage signing, or model stubs, create the following internal modules:

- Core API: `inspection_photo_access.py`
- Core API: `analysis_request_workflow.py`
- Core API: `bee_detector_training_workflow.py`
- Core API: `adapters/object_storage.py`
- Core API: `adapters/analysis_queue.py`
- Core API: `adapters/bee_detector_training.py`
- Analysis Service: `analysis_job_runner.py`
- Analysis Service: `model_runtime.py`
- Analysis Service: `adapters/object_storage.py`
- Analysis Service: `adapters/analysis_store.py`
- Web App: `src/coreApiClient.ts`

Keep the interfaces small. Add adapters only when production and test versions both exist or are clearly imminent.
