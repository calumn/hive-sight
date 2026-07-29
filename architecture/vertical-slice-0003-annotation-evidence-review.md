# Vertical Slice 0003: Annotation Evidence Review

## Purpose

Prove that a completed stub Analysis Result can expose structured Annotation evidence for one Inspection Photo, and that the Beekeeper can review that evidence as an overlay on the original photo through the Web UI.

This slice establishes the reusable annotation data shape needed for Tagged Photo rendering, later User Correction workflows, and eventual model-improvement review. It deliberately starts with deterministic bee annotations before real bee detection or real Varroa detection, so HiveSight can prove the evidence-review path without implying real AI-assisted Varroa accuracy. Slice 3 is bees-only: it does not render even stubbed Varroa markers.

## Source Inputs

- `CONTEXT.md`: Inspection Photo, Analysis Result, Complete Visible Bee, Partial Visible Bee, Likely Varroa Detection, Tagged Photo, Annotation, User Correction, Review Decision, Workspace Data Use Agreement, Model Version, Dataset Role.
- `requirements/requirements.md`: FR-006, FR-007, FR-009, FR-010, FR-012, FR-013, FR-014, FR-016, FR-017, FR-019, NFR-001, NFR-002, NFR-005.
- `requirements/product-spec.md`: "Beekeeper optionally views all detected bees", "System stores original photos and reusable annotation data", "System re-renders tagged photos from stored annotations", and "User photos are not automatically trusted training data" scenarios.
- `requirements/acceptance-criteria.md`: Bee Counting, Photo And Annotation Storage, Web UI, Ownership And Permissions, Workspace Data Use Agreement And Model Improvement.
- `requirements/model-requirements.md`: MR-013 User Corrections As Review Candidates, MR-014 Human Review Decisions, MR-016 Dataset Provenance, MR-017 Dataset Roles, MR-019 Workspace Data Use Agreement Traceability.
- `requirements/decision-log.md`: Tagged Image Evidence And Correction Loop; User Corrections Require Review Before Dataset Use; Workspace Data Use Agreement Required For Upload And Analysis; Service-Oriented Architecture For V1.
- `architecture/adr/0001-service-oriented-architecture.md`: Core API owns beekeeper-facing product workflow and authorization; model training and evaluation workflow is separate from V1 runtime services.
- `architecture/codebase-design.md`: `InspectionPhotoAccess`, `AnalysisRequestWorkflow`, `AnalysisJobRunner`, `ModelRuntime`, and `CoreApiClient` are the relevant seams.
- `architecture/vertical-slice-0001-photo-intake.md`: successful photo intake preserves an original Inspection Photo reference and creates a queued Analysis Run.
- `architecture/vertical-slice-0002-analysis-handoff.md`: successful stub processing completes an Analysis Run and exposes an Analysis Result through the Core API.

## User Path

Given a User is logged in with an active owner Workspace Membership
And the Workspace has accepted the current Workspace Data Use Agreement
And the User acting as the primary Beekeeper has uploaded an Inspection Photo
And the Inspection Photo has a completed stub Analysis Result
And the stub Analysis Result contains deterministic bee Annotations
When the Beekeeper opens the analysis evidence view
Then the original Inspection Photo is shown
And the system renders Annotation overlays on the photo
And the Beekeeper can inspect how the visible bee count was derived
And the visible bee counts match the rendered bee Annotations
And the Web UI clearly communicates that the overlays are deterministic stub evidence, not real AI-assisted Varroa analysis

## Preconditions

- Vertical Slice 0001 is implemented and demoable.
- Vertical Slice 0002 is implemented and demoable.
- Development authentication remains represented by the dev-only auth header.
- Workspace access and Workspace Data Use Agreement gates from earlier slices still apply before exposing the original photo, Analysis Result, or Annotations.
- An Inspection Photo has an original object reference available through the Core API storage seam.
- The Analysis Result is still produced by a deterministic stub Model Runtime.
- The Analysis Service remains private. The Web UI must not call it directly.
- This slice may use local/dev object viewing through the Core API rather than production signed view URLs.
- Evidence viewing uses the same beekeeper-facing authorization path as photo upload and result viewing. No reviewer, admin, or model-governance role is introduced in this slice.

## End-To-End Behaviour

The Beekeeper follows the Slice 0001 and Slice 0002 path: accept the Workspace Data Use Agreement, create Apiary/Hive/Inspection records, upload one Inspection Photo, and process the queued Analysis Run into a completed deterministic stub Analysis Result.

The deterministic stub result now includes structured Annotation data for visible bees. At minimum, it returns a small stable set of `complete_visible_bee` and `partial_visible_bee` annotations in normalized image coordinates, along with the source image dimensions used by the model runtime. The Slice 2 deterministic count values may be revised so the complete visible bee count and partial visible bee count match the rendered annotations. For Slice 3, `likely_varroa_detections` is `0`.

The deterministic Annotations originate in the private Analysis Service stub runtime, not in the Core API. The Core API stores or projects them as first-class Annotation records associated with the Workspace, Inspection Photo, and Analysis Result. The first implementation may still use the in-memory/dev store, but the domain shape should not treat annotations as an opaque blob inside the Analysis Result.

The Core API exposes an authorized analysis evidence response keyed by `analysis_run_id`, for example `GET /v1/analysis-runs/{analysis_run_id}/evidence?workspace_id=...`. The response includes the Analysis Result summary, a Core API-controlled `view_url` for the original Inspection Photo, and the structured Annotations. The image bytes are loaded separately through an authenticated Core API image route that applies the same User, Workspace Membership, Workspace ownership, and Workspace Data Use Agreement checks. Short-lived signed storage URLs remain a future target, not part of this slice.

The Web UI fetches evidence only through `CoreApiClient`. It renders the original Inspection Photo and overlays the stub bee annotations in a Tagged Photo-style view at display time. The original Inspection Photo remains unchanged and no flattened tagged image file is generated. Complete visible bees and partial visible bees are visually distinguishable and visible by default, with no overlay toggles in this slice. The UI includes a small legend/caveat and keeps the Slice 2 boundary: this is deterministic stub evidence and must not be presented as a real Varroa estimate, diagnosis, or treatment recommendation. The rendering must be responsive enough that the image and overlays stay aligned on desktop and mobile.

This slice also prepares the data shape for future User Correction and admin/reviewer workflows. It does not yet let a Beekeeper correct an annotation, does not let an admin make Review Decisions, and does not assign any Dataset Role.

## Layers Touched

- Web UI: Adds an analysis evidence panel that displays the original Inspection Photo with overlay markers for deterministic bee Annotations, including distinguishable complete and partial visible bee styles, a small legend/caveat, and responsive rendering. Both annotation types are visible by default; overlay toggles are not added.
- Core API: Adds or extends an authorized analysis evidence endpoint keyed by `analysis_run_id`. It returns the original photo `view_url`, completed Analysis Result summary, and first-class structured Annotations for the owning Workspace. It also provides an authenticated Core API image view route for local/dev photo display if one does not already exist.
- Analysis Service: Extends the deterministic `ModelRuntime` or job result contract to return stable bee Annotation records alongside Slice 2 count fields. The stub counts are internally consistent with the returned Annotations.
- Storage: Reuses the original Inspection Photo object reference from Slice 1. Production signed view URLs remain out of scope; a Core API proxied local/dev image view is sufficient for this slice.
- Queue or async boundary: Reuses the Slice 2 dev processing path. No real queue infrastructure is added.
- Contracts: Introduces the first explicit Annotation contract for evidence rendering, using normalized image coordinates and source/provenance fields.
- Observability: Adds test-visible or structured evidence for returning annotation evidence, blocking cross-Workspace evidence access, and identifying the stub model/source that produced the Annotations.

## Test Seams

- Seam: `ModelRuntime`
- Behaviour verified: deterministic stub analysis returns stable bee Annotation records with normalized coordinates, source image dimensions, annotation type, confidence, and model/source traceability. It returns no Varroa annotations and keeps `likely_varroa_detections` at `0`.
- Test style: Analysis Service module tests with deterministic runtime and fixed expected annotation payloads.

- Seam: `AnalysisJobRunner`
- Behaviour verified: analysis job output carries Annotation data through the private Analysis Service result contract without losing Slice 2 count fields or model version.
- Test style: Analysis Service job-runner tests using the deterministic Model Runtime.

- Seam: Core API analysis processing workflow
- Behaviour verified: completed stub results store or project first-class Annotation records against the correct Workspace, Analysis Result, and Inspection Photo. The count fields match the stored bee Annotations.
- Test style: Core API workflow tests with in-memory product data, deterministic IDs, deterministic clock, and fake analysis executor.

- Seam: Core API evidence route boundary
- Behaviour verified: authorized Users can fetch analysis evidence by `analysis_run_id` for their Workspace; unauthorized Users cannot fetch another Workspace's photo, result, or Annotations. Evidence viewing still requires an accepted Workspace Data Use Agreement.
- Test style: FastAPI integration tests through public Core API endpoints with dependency overrides.

- Seam: API-level BDD acceptance
- Behaviour verified: the Core API returns original-photo evidence and structured bee Annotations for a completed stub Analysis Result, and rejects cross-Workspace evidence access.
- Test style: pytest-bdd feature scenarios aimed at the Core API, not the Web UI.

- Seam: `CoreApiClient`
- Behaviour verified: web code parses the analysis evidence response, including original photo `view_url`, Analysis Result summary, Annotation overlays, source image dimensions, confidence values, and caveat.
- Test style: TypeScript unit tests with mocked fetch or in-memory client responses.

- Seam: Web UI evidence panel
- Behaviour verified: the Beekeeper can see the original photo, complete visible bee overlays, partial visible bee overlays, small legend/caveat, and responsive overlay alignment. Confidence may be available in quiet detail, but is not emphasized as calibrated accuracy.
- Test style: component test and browser-level visual check where feasible. Repeatable browser acceptance execution is handled by `architecture/vertical-slice-0003-5-web-acceptance-test-harness.md`.

## Data Shape

Minimum additions or tightened records:

- Annotation: `annotation_id`, `workspace_id`, `inspection_photo_id`, `analysis_result_id`, `annotation_type`, `x`, `y`, `width`, `height`, `coordinate_space`, `source_image_width_px`, `source_image_height_px`, `confidence`, `source`, `created_at`.
- Annotation type: `complete_visible_bee`, `partial_visible_bee`. `likely_varroa_detection` remains allowed by the domain language but is not produced or rendered in this slice.
- Coordinate space: `normalized`, with `x`, `y`, `width`, and `height` expressed relative to the source image dimensions from `0.0` to `1.0`.
- Analysis Result: existing Slice 2 fields plus first-class Annotation records for projection. The deterministic stub count fields match the returned/stored bee Annotations, and `likely_varroa_detections` is `0`.
- Inspection Photo evidence view: `inspection_photo_id`, `filename`, `content_type`, `view_url`, `width`, `height`.

Minimum API shapes:

- Analysis evidence request: `workspace_id`, `analysis_run_id`.
- Analysis evidence response: `analysis_run_id`, `analysis_result_id`, `inspection_photo`, `analysis_result`, `annotations`, `result_kind`, `model_version`, `caveat`.
- Inspection Photo image view request: `workspace_id`, `inspection_photo_id`; the route returns image bytes only after Core API authorization.
- Blocked response codes: `not_authenticated`, `workspace_access_denied`, `data_use_agreement_required`, `analysis_run_not_found`, `analysis_result_not_found`, `analysis_result_not_completed`, `photo_view_unavailable`.

## Out Of Scope

- Real bee detection, real Varroa detection, confidence calibration, or model artifact loading.
- Likely Varroa overlay rendering, including deterministic placeholders.
- User Correction creation from the Beekeeper UI.
- Admin or reviewer UI.
- Reviewer role, reviewer permissions, or internal admin capability.
- Review Decisions, Dataset Role assignment, Dataset Version creation, model training, benchmark evaluation, or model promotion.
- Automatic use of user-submitted photos, model Annotations, or User Corrections as training data.
- Full annotation-studio behaviour such as drawing, resizing, deleting, bulk editing, keyboard labelling, or consensus review.
- Overlay toggles, class filters, zoom, pan, or annotation editing controls.
- Flattened tagged image generation or storage.
- Visible Varroa Rate calculation across one or more photos.
- Real queue infrastructure, retries, dead-letter handling, backoff, worker deployment, or distributed locking.
- Durable database persistence if the in-memory slice store is still the fastest local proving path.
- Short-lived signed storage view URLs.
- Production registration/login, production auth provider integration, or service-to-service credential hardening.

## Acceptance Criteria

- [ ] A completed stub Analysis Result includes structured Annotation records for at least one complete visible bee and one partial visible bee.
- [ ] Annotation records are associated with the owning Workspace, Inspection Photo, and Analysis Result.
- [ ] Annotation records are first-class records in the Core API store abstraction, even if the backing implementation remains in-memory/dev for this slice.
- [ ] Annotation coordinates use a documented normalized coordinate space suitable for rendering over the original photo, and each Annotation preserves the source image dimensions used by the model runtime.
- [ ] The deterministic stub counts match the returned bee Annotations, and `likely_varroa_detections` is `0`.
- [ ] The Analysis Service deterministic `ModelRuntime` produces the stub Annotations; the Core API does not invent model-output Annotations.
- [ ] The Core API exposes an authorized analysis evidence response keyed by `analysis_run_id`, containing the original Inspection Photo `view_url`, Analysis Result summary, model version, result kind, caveat, and Annotations.
- [ ] The Core API image view route returns original photo bytes only after authorization.
- [ ] The Core API verifies User authentication, Workspace Membership, Workspace ownership, and Workspace Data Use Agreement state before exposing photo evidence, image bytes, or Annotations.
- [ ] A User without access to the Workspace cannot view another Workspace's Inspection Photo evidence or Annotations.
- [ ] The Web UI renders the original Inspection Photo with visually distinguishable complete visible bee and partial visible bee overlays, without generating or depending on a flattened tagged image.
- [ ] The Web UI shows both annotation types by default and does not add overlay toggles in this slice.
- [ ] The Web UI includes a small legend/caveat and keeps annotation confidence visually quiet rather than presenting it as calibrated accuracy.
- [ ] The Web UI evidence view is responsive enough for mobile and desktop, with overlays aligned to the displayed image.
- [ ] The Web UI communicates that the overlays are deterministic stub evidence, not real AI-assisted Varroa analysis.
- [ ] Tests cover the Analysis Service annotation-producing seam, the Core API evidence route/workflow seam, API-level BDD acceptance scenarios, and the Web `CoreApiClient` parsing seam.
- [ ] Browser-level acceptance coverage for the Web UI evidence panel is provided by Vertical Slice 0003.5.
- [ ] The implementation preserves the target architecture: Web UI calls Core API; Core API owns product authorization and evidence projection; Analysis Service remains private and owns model-runtime execution.
- [ ] No Annotation, User Correction, or Inspection Photo becomes training, validation, or benchmark data as part of this slice.

## Decisions From Slice Review

- Annotation rendering uses normalized coordinates and preserves the source image dimensions used by the model runtime.
- Evidence viewing is limited to the same beekeeper-facing Workspace authorization path as prior slices. No reviewer, admin, or model-governance role is introduced in Slice 3.
- Slice 3 produces and renders bee Annotations only. It does not produce or render stubbed Varroa markers.
- Browser image rendering is required. API-only evidence is not enough for the slice to be demoable.
- Tagged Photo rendering is performed at display time from the original Inspection Photo plus structured Annotations. The slice does not generate flattened tagged image files.
- Stub Annotations originate in the Analysis Service deterministic Model Runtime and are carried through the Core API.
- Annotations are first-class Core API records, even if the implementation uses the existing in-memory/dev store.
- Complete visible bee and partial visible bee Annotations are both visible by default. Overlay toggles are deferred.
- User Corrections are completely out of scope for Slice 3.
- Active Workspace Data Use Agreement remains required for evidence viewing.
- Slice 4 should separately bottom out the admin/reviewer workflow, including whether a `Reviewer` role belongs inside Workspace Memberships or as a separate internal capability.
- Stub bee counts must match rendered bee Annotations, and likely Varroa detections must be `0`.
- The evidence route is keyed by `analysis_run_id`.
- The evidence response returns a Core API-controlled image `view_url`; the image bytes are loaded separately.
- The image view route requires the same authentication and Workspace authorization checks as the evidence response.
- Annotation confidence is stored but kept visually quiet in the Web UI.
- The evidence view includes a small legend/caveat.
- The evidence view must be responsive enough that overlays remain aligned on mobile and desktop.

## Open Questions

- None for implementation of this slice. The admin/reviewer workflow, durable persistence, signed storage URLs, real queue infrastructure, and real model inference should be treated as future slice or architecture decisions rather than blockers.
