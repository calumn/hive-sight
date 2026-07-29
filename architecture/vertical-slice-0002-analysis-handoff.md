# Vertical Slice 0002: Analysis Handoff And Stub Result

## Purpose

Prove that an accepted Inspection Photo can move from queued analysis to a completed stub Analysis Result through the private Analysis Service, while the Beekeeper sees status and result evidence only through the Web UI and Core API.

This slice proves the runtime handoff and status projection before real Varroa inference. The deterministic stub result must be visibly marked as a stub so HiveSight does not imply a real AI-assisted Varroa estimate yet.

## Source Inputs

- `CONTEXT.md`: Inspection Photo, Analysis Result, Complete Visible Bee, Partial Visible Bee, Likely Varroa Detection, Tagged Photo, Model Version, Workspace Data Use Agreement.
- `requirements/requirements.md`: FR-006, FR-007, FR-009, FR-010, FR-013, FR-014, FR-016, FR-017, NFR-001, NFR-002, NFR-005.
- `requirements/product-spec.md`: "System estimates visible bees in each photo", "System detects likely Varroa mites on bees", "Beekeeper reviews likely infected bees on a tagged photo", and "System stores original photos and reusable annotation data" scenarios.
- `requirements/acceptance-criteria.md`: Bee Counting, Varroa Detection, Visible Varroa Estimate, Photo And Annotation Storage, Web UI, Ownership And Permissions.
- `requirements/decision-log.md`: Varroa Detection Is The Primary Product Focus; AI Estimate Boundary; Tagged Image Evidence And Correction Loop; Initial Metric Is Mites Per 100 Visible Bees; Service-Oriented Architecture For V1.
- `architecture/adr/0001-service-oriented-architecture.md`: Analysis Service is private; analysis is asynchronous; frontend reads analysis status and results through the Core API.
- `architecture/codebase-design.md`: `AnalysisRequestWorkflow`, `AnalysisJobRunner`, `ModelRuntime`, and `CoreApiClient` are the relevant seams.
- `architecture/vertical-slice-0001-photo-intake.md`: successful photo intake creates a queued `AnalysisRun`.

## User Path

Given a User is logged in with an active owner Workspace Membership
And the Workspace has accepted the current Workspace Data Use Agreement
And the User acting as the primary Beekeeper has uploaded an Inspection Photo
And the Inspection Photo has a queued Analysis Run
When the queued analysis is processed by the private Analysis Service using the deterministic stub Model Runtime
Then the Analysis Run is marked completed
And a stub Analysis Result is stored or projected for that Inspection Photo
And the Beekeeper can see the completed status, model version, count fields, and a clear stub-result caveat in the Web UI

## Preconditions

- Vertical Slice 0001 is implemented and demoable.
- Development authentication remains represented by the dev-only auth header.
- Workspace access and Workspace Data Use Agreement gates from Slice 0001 still apply before any new analysis can be requested or processed.
- An accepted Inspection Photo has an original object reference available to the Analysis Service request.
- The Analysis Service remains private. The Web UI must not call it directly.
- The first model implementation remains a deterministic stub adapter, not a real Varroa model.
- Local development may use a dev-only "process queued analysis" action instead of real queue infrastructure, but this action must preserve the target queue/worker seam.

## End-To-End Behaviour

The Beekeeper follows the Slice 0001 path to accept terms, create Apiary/Hive/Inspection records, and upload one Inspection Photo. The Core API records a queued Analysis Run and exposes that status to the Web UI.

For this slice, the Web UI offers a dev/demo action to process the queued Analysis Run. That action calls the Core API, not the Analysis Service. The Core API verifies the authenticated User still has Workspace access, verifies the Analysis Run belongs to an Inspection Photo in that Workspace, and hands the queued work to a replaceable analysis execution seam.

In local development, that seam calls or invokes the private Analysis Service using the existing `AnalysisJobRunner` and deterministic `ModelRuntime`. The Analysis Service returns a completed stub result with a traceable `model_version`, complete visible bee count, partial visible bee count, likely Varroa detection count, optional tagged image reference, and completion time.

The Core API records or projects the completed Analysis Result against the Inspection Photo and updates the Analysis Run status to `completed`. The Web UI refreshes through `CoreApiClient` and shows that analysis has completed, along with the model version, count fields, and wording that this is a deterministic stub result rather than a real Varroa estimate.

If processing fails, the Core API marks or returns the Analysis Run as failed with a stable user-safe error code. The Web UI shows the failed state without implying that the photo was analysed successfully.

## Layers Touched

- Web UI: Adds analysis status refresh/display after upload, a dev/demo action to process queued analysis, completed and failed states, count fields, model version, and stub-result caveat.
- Core API: Adds an authorized endpoint or workflow action for processing a queued Analysis Run in development, a result/status projection endpoint, and storage or in-memory records for completed Analysis Results.
- Analysis Service: Uses `AnalysisJobRunner` and deterministic `ModelRuntime` to complete one analysis job with stub counts and model-version traceability.
- Storage: Uses existing local/dev object reference from Slice 0001. Tagged image storage is not required; `tagged_image_object_key` may remain `null`.
- Queue or async boundary: Uses a replaceable in-memory/dev queue or dev worker action to simulate consuming one queued analysis item. Real queue infrastructure remains out of scope.
- Contracts: Introduces or tightens Core API response shapes for Analysis Run detail and Analysis Result projection. May add an internal Analysis Service client contract matching `/v1/jobs`.
- Observability: Adds test-visible or structured evidence for queued analysis processing, completed stub result, failed processing, and model version used.

## Test Seams

- Seam: `AnalysisRequestWorkflow`
- Behaviour verified: queued Analysis Runs are eligible for processing only when they belong to the authorized Workspace and still satisfy analysis preconditions.
- Test style: Core API workflow tests with in-memory product data, deterministic IDs, deterministic clock, and fake analysis executor.

- Seam: `AnalysisJobRunner`
- Behaviour verified: a job request with an original object reference returns a completed stub Analysis Result with model-version traceability and count fields.
- Test style: Analysis Service module tests using deterministic `ModelRuntime`, deterministic clock, and fixture object references.

- Seam: Analysis execution adapter or service client
- Behaviour verified: Core API can invoke the private Analysis Service contract without the route handler knowing model-runtime details.
- Test style: adapter tests with a fake Analysis Service client and a failure case.

- Seam: Core API route boundary
- Behaviour verified: the Web UI can request processing or refresh status through the Core API; completed and failed results use stable response shapes and user-safe errors.
- Test style: FastAPI integration tests through public Core API endpoints with dependency overrides.

- Seam: `CoreApiClient`
- Behaviour verified: web code parses queued, completed, and failed analysis responses into UI-safe states.
- Test style: TypeScript unit tests with mocked fetch or in-memory client responses.

- Seam: Web UI workflow
- Behaviour verified: after photo intake, the Beekeeper can see queued status, process the stub analysis, and see completed stub result fields and caveat.
- Test style: component or browser-level workflow test where feasible.

## Data Shape

Minimum additions or tightened records:

- Analysis Run: `analysis_run_id`, `workspace_id`, `inspection_photo_id`, `status`, `queued_at`, `started_at`, `completed_at`, `failed_at`, `failure_code`, `failure_message`, `requested_model_version`, `model_version`.
- Analysis Result: `analysis_result_id`, `analysis_run_id`, `inspection_photo_id`, `workspace_id`, `model_version`, `complete_visible_bee_count`, `partial_visible_bee_count`, `likely_varroa_detections`, `tagged_image_object_key`, `result_kind`, `completed_at`.
- Analysis Job Request: `analysis_run_id`, `inspection_photo_id`, `original_object_key`, `requested_model_version`.
- Analysis Job Result: `analysis_run_id`, `inspection_photo_id`, `model_version`, `status`, `complete_visible_bee_count`, `partial_visible_bee_count`, `likely_varroa_detections`, `tagged_image_object_key`, `completed_at`.

Minimum API shapes:

- Process queued analysis request: `workspace_id`, `analysis_run_id`.
- Analysis run detail response: `analysis_run_id`, `inspection_photo_id`, `status`, timestamps, optional `analysis_result`, optional failure.
- Analysis result response: count fields, `model_version`, `result_kind`.
- Blocked or failed response codes: `not_authenticated`, `workspace_access_denied`, `data_use_agreement_required`, `analysis_run_not_found`, `analysis_run_not_queued`, `analysis_processing_failed`, and `analysis_service_unavailable`.

## Out Of Scope

- Real bee detection, real Varroa detection, confidence scoring, and model artifact loading.
- Visible Varroa Rate calculation across one or more photos.
- Tagged Photo rendering or annotation overlay UI.
- User Correction workflow.
- Real queue infrastructure, retries, dead-letter handling, backoff, worker deployment, or distributed locking.
- Durable database persistence if the in-memory slice store is still the fastest local proving path.
- Real object storage downloads by the Analysis Service if a local object reference or fake object retrieval is enough for this slice.
- Production registration/login, production auth provider integration, or service-to-service credential hardening.
- Model governance UI, dataset eligibility review, training, validation, benchmark evaluation, or model promotion.

## Acceptance Criteria

- [ ] A queued Analysis Run created by Slice 0001 can be processed through a Core API action that the Web UI can trigger or refresh from.
- [ ] The Web UI never calls the Analysis Service directly.
- [ ] The Core API verifies User authentication, Workspace Membership, Workspace ownership, and Workspace Data Use Agreement state before processing or exposing an Analysis Result.
- [ ] A User without access to the Workspace cannot process or view another Workspace's Analysis Run or Analysis Result.
- [ ] The Analysis Service completes one job through `AnalysisJobRunner` and deterministic `ModelRuntime`.
- [ ] A completed stub Analysis Result records or projects `model_version`, complete visible bee count, partial visible bee count, likely Varroa detection count, tagged image reference if any, and completion time.
- [ ] The Analysis Run status changes from `queued` to `completed` after successful stub processing.
- [ ] Processing failure returns or records a stable user-safe error code without losing the original Inspection Photo record.
- [ ] The Web UI shows queued, processing, completed, and failed analysis states clearly.
- [ ] The completed UI explicitly communicates that the result is a deterministic stub, not a real AI-assisted Varroa estimate.
- [ ] Tests cover the Analysis Service runner seam, the Core API analysis processing route/workflow seam, and the Web `CoreApiClient` parsing seam.
- [ ] The implementation preserves the target architecture: Web UI calls Core API; Core API owns product authorization and result projection; Analysis Service remains private and owns model-runtime execution.

## Open Questions

- None for implementation of this slice. A real queue, durable persistence, or real model inference should be treated as a future scope decision rather than a blocker.
