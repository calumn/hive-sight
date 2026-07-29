# Vertical Slice 0001: Inspection Photo Intake

## Purpose

Prove that HiveSight can accept an inspection photo only through the authenticated, Workspace-authorized, data-use-gated product path.

This slice ends when a User acting as the primary Beekeeper can see that an Inspection Photo has been accepted for analysis, with an analysis request recorded or stubbed as queued. It deliberately proves intake and gating before real Varroa inference.

## Source Inputs

- `CONTEXT.md`: User, Workspace, Workspace Membership, Beekeeper, Apiary, Hive, Inspection, Inspection Photo, Workspace Data Use Agreement, Analysis Result.
- `requirements/requirements.md`: FR-001, FR-002, FR-003, FR-004, FR-013, FR-016, FR-017, FR-018, FR-020, FR-014.
- `requirements/product-spec.md`: "Beekeeper uploads multiple photos to an inspection" and "Workspace data-use agreement is required for upload and analysis" scenarios.
- `requirements/acceptance-criteria.md`: Photo Upload and Association, Photo And Annotation Storage, Web UI, Ownership And Permissions, Upload And Storage, Workspace Data Use Agreement And Model Improvement.
- `requirements/decision-log.md`: Inspection Photo Upload Preconditions; Service-Oriented Architecture For V1.
- `architecture/adr/0001-service-oriented-architecture.md`: Core API owns product workflow and authorization; Analysis Service is private; photo storage targets short-lived object-scoped URLs.
- `architecture/codebase-design.md`: `InspectionPhotoAccess`, `AnalysisRequestWorkflow`, and `CoreApiClient` are the first relevant seams.

## User Path

Given a person has registered as a User
And the User is logged in
And the User has an active owner Workspace Membership
And the Workspace has accepted the current Workspace Data Use Agreement
And the User is acting as the primary Beekeeper in that Workspace
And the Beekeeper has an Apiary, Hive, and Inspection
When the Beekeeper uploads one inspection photo
Then the photo is associated with the Inspection
And the original photo reference is preserved
And an analysis request is queued or stubbed as queued
And the Beekeeper can see the photo intake status in the Web UI

## Preconditions

- A registered User exists.
- The User is logged in. For this slice, authentication is represented by a clearly dev-only auth header that resolves to an authenticated `UserContext`.
- The User has an active owner Workspace Membership for the Workspace.
- The Workspace owns the Apiary, Hive, Inspection, and Inspection Photo.
- The Workspace has accepted the current Workspace Data Use Agreement through a simple slice-level acceptance action.
- Upload constraints are configurable. The initial policy allows `image/jpeg`, `image/png`, and `image/webp`, with a maximum size of 15 MB per image.
- Object storage uses Core API proxied upload with local/dev storage for this slice, while preserving the future signed-upload-url seam behind `InspectionPhotoAccess`.

## Closed Decisions

- Development auth uses a clearly dev-only auth header, not a hard-coded hidden User and not production registration/login.
- The slice includes minimal create actions for Apiary, Hive, and Inspection rather than relying only on seeded fixtures.
- Storage uses Core API proxied upload with local/dev storage first, behind `InspectionPhotoAccess`.
- Initial upload policy is JPEG, PNG, WebP, max 15 MB, all configurable.
- Upload and intake failures use stable machine-readable error codes: `not_authenticated`, `workspace_access_denied`, `data_use_agreement_required`, `inspection_not_found`, `unsupported_content_type`, `file_too_large`, `upload_storage_failed`, and `analysis_request_failed`.
- The Web UI includes a simple Workspace Data Use Agreement acceptance action, without withdrawal or legal-copy management.
- Successful photo intake automatically creates a queued `AnalysisRun` through `AnalysisRequestWorkflow`.
- The Analysis Service does not execute real analysis in this slice.

## End-To-End Behaviour

The Web UI presents a minimal inspection photo intake workflow. A dev-only auth header represents the logged-in User. The User can accept the Workspace Data Use Agreement, create an Apiary, create a Hive under that Apiary, create an Inspection under that Hive, and select one image file for upload.

The Web UI submits the file to the Core API through a proxied upload/intake endpoint. The Core API checks the dev-authenticated User context, Workspace Membership, Workspace Data Use Agreement status, Inspection ownership, content type, and size.

If any gate fails, the Core API rejects the upload request with a stable error code and user-safe reason. The Web UI shows the blocked state without pretending analysis has started.

If all gates pass, the Core API stores the original file in local/dev storage, creates or records an Inspection Photo with an original object reference, and requests analysis through `AnalysisRequestWorkflow`. Queue publishing remains stubbed, but the workflow creates a queued analysis state that is traceable to the Inspection Photo.

The Web UI shows the Inspection Photo as accepted and shows analysis status as queued. No Varroa count, bee count, tagged photo, or model output is required in this slice.

## Layers Touched

- Web UI: Minimal workflow showing dev-authenticated User context, Workspace Data Use Agreement acceptance, Apiary creation, Hive creation, Inspection creation, file selection, upload blocked/accepted states, and queued analysis status.
- Core API: Minimal create endpoints for Apiary, Hive, and Inspection; Workspace Data Use Agreement acceptance endpoint; proxied upload/intake endpoint enforcing User, Workspace Membership, Workspace Data Use Agreement, Inspection ownership, content type, and size gates.
- Analysis Service: Not touched for real execution. Existing private service can remain a stub.
- Storage: Local/dev storage behind `InspectionPhotoAccess`, with original object reference preserved. Keep the target model of short-lived, object-scoped upload access visible in the module interface for later replacement.
- Queue or async boundary: Stubbed queue publication through `AnalysisRequestWorkflow`, automatically returning analysis status `queued` after successful intake.
- Contracts: Minimal request/response shapes for inspection photo intake, upload access, and analysis request status. Existing event contracts may remain unchanged unless the stubbed request needs a small explicit payload.
- Observability: Core API should emit enough structured log or test-visible event evidence to distinguish blocked upload, accepted photo intake, and queued analysis request.

## Test Seams

- Seam: `InspectionPhotoAccess`
- Behaviour verified: proxied upload/intake is allowed only when the User is authenticated, the Workspace is authorized, data-use terms are accepted, and file constraints pass.
- Test style: Core API service/module tests with in-memory authorization, data-use, inspection, and storage adapters.

- Seam: `AnalysisRequestWorkflow`
- Behaviour verified: accepted Inspection Photo intake creates a queued analysis request without exposing queue payload construction to route handlers.
- Test style: Workflow test using deterministic IDs, deterministic clock, and in-memory queue/event recorder.

- Seam: Core API route boundary
- Behaviour verified: blocked requests return clear HTTP errors; accepted requests return Inspection Photo and analysis status data.
- Test style: FastAPI integration tests through public HTTP endpoints.

- Seam: `CoreApiClient`
- Behaviour verified: web code parses accepted and blocked intake responses into UI-safe states.
- Test style: TypeScript unit tests or component-level tests using a fake Core API response.

- Seam: Web UI workflow
- Behaviour verified: Beekeeper can follow the visible path from inspection context to accepted photo and queued status.
- Test style: Component or browser-level test once the UI workflow exists.

## Data Shape

Minimum product records or in-memory equivalents:

- User: `user_id`, authentication status.
- Workspace: `workspace_id`, `data_use_agreement_status`, `data_use_agreement_terms_version`.
- Workspace Membership: `user_id`, `workspace_id`, `role`, `status`.
- Apiary: `apiary_id`, `workspace_id`, `name`.
- Hive: `hive_id`, `apiary_id`, `name`.
- Inspection: `inspection_id`, `hive_id`, `inspection_date`.
- Inspection Photo: `inspection_photo_id`, `inspection_id`, `workspace_id`, `original_object_key`, `filename`, `content_type`, `size_bytes`, `upload_status`, `uploaded_by_user_id`, `uploaded_at`.
- Analysis Run: `analysis_run_id`, `inspection_photo_id`, `status`, `queued_at`, `requested_model_version`.

Minimum API shapes:

- Dev auth context: dev-only auth header carrying or resolving to `user_id`.
- Data-use agreement acceptance request: `workspace_id`, `terms_version`.
- Apiary create request/response: `workspace_id`, `name`, returned `apiary_id`.
- Hive create request/response: `apiary_id`, `name`, returned `hive_id`.
- Inspection create request/response: `hive_id`, `inspection_date`, returned `inspection_id`.
- Intake request: `workspace_id`, `inspection_id`, `filename`, `content_type`, `size_bytes`.
- Intake response: `inspection_photo_id`, `upload_status`, `original_object_key`, optional `upload_url`, `analysis_run_id`, `analysis_status`.
- Blocked response: stable error code and user-safe message. Initial codes are `not_authenticated`, `workspace_access_denied`, `data_use_agreement_required`, `inspection_not_found`, `unsupported_content_type`, `file_too_large`, `upload_storage_failed`, and `analysis_request_failed`.

## Out Of Scope

- Real registration, password login, OAuth, or production identity provider integration.
- Multi-user invitations, non-owner roles, workspace switching, advisor access, or organization-level permissions.
- Real S3 signing, MinIO wiring, or direct browser-to-object-storage upload.
- Real queue infrastructure if an in-memory event recorder is enough for the first implementation.
- Real Analysis Service execution.
- Bee counting, Varroa detection, Visible Varroa Rate calculation, tagged photo rendering, and user correction workflows.
- Dataset eligibility review, model training, benchmark evaluation, or model governance UI.
- Deferred guest or trial photo analysis.
- Data Deletion Request implementation.
- Workspace Data Use Agreement withdrawal and legal-copy management.

## Acceptance Criteria

- [ ] A logged-in User with an active owner Workspace Membership and accepted Workspace Data Use Agreement can submit one inspection photo for an existing Workspace-owned Inspection.
- [ ] A person who is not logged in cannot upload an inspection photo.
- [ ] A logged-in User without access to the Workspace cannot upload an inspection photo for that Workspace.
- [ ] A Workspace without an accepted Workspace Data Use Agreement cannot upload an inspection photo or start analysis.
- [ ] The Web UI lets the User accept the current Workspace Data Use Agreement before upload.
- [ ] The Web UI supports minimal Apiary, Hive, and Inspection creation as part of the demoable path.
- [ ] `image/jpeg`, `image/png`, and `image/webp` files up to 15 MB are accepted by the initial configurable upload policy.
- [ ] Unsupported content type and excessive file size are rejected with stable error codes and user-safe messages.
- [ ] An accepted Inspection Photo records its Workspace, Inspection, original object reference, filename, content type, size, upload status, uploader, and upload time.
- [ ] An accepted Inspection Photo triggers an analysis request through `AnalysisRequestWorkflow` and returns status `queued`.
- [ ] The Web UI shows blocked, accepted, and queued states clearly.
- [ ] Tests cover the upload gate at module and Core API route seams.
- [ ] The implementation preserves the target architecture: Web UI calls Core API; Core API owns authorization and data-use gates; Analysis Service remains private.

## Open Questions

- None for implementation of this slice. Further questions should be treated as scope-change proposals rather than blockers.
