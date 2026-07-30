# Vertical Slice 0005: AI-Assisted Bee Annotation Bootstrap

## Purpose

Prove that HiveSight can start an internal dataset-labelling workflow for one project-owned Inspection Photo, create AI-assisted Draft Annotations for complete and partial visible bees through a replaceable pre-labelling seam, require a Dataset Curator to review those suggestions, and project approved suggestions as Reviewed Annotations without assigning them to training, validation, benchmark, or model use.

This is the first model-readiness slice. It deliberately builds the smallest useful labelling loop before choosing a real model family, dataset export format, training workflow, or benchmark process.

## Source Inputs

- `CONTEXT.md`: Inspection Photo, Annotation, Draft Annotation, Reviewed Annotation, Annotation Source, Review Decision, Workspace Data Use Agreement, Dataset Curator, Internal Capability, Dataset Role, Dataset Item, Dataset Version, Training Run, Model Candidate, Benchmark Evaluation.
- `requirements/ai-assisted-annotation-and-model-training-baseline.md`: AI-assisted annotation bootstrap, human review required, bee-first bootstrap, distinct labelling and product feedback workflows, provenance required, Dataset Curator authorization, and Dataset Role separation.
- `requirements/product-spec.md`: "Reviewer creates reviewed bee annotations from AI-assisted draft annotations" and the documented gap for `uncertain_bee`.
- `requirements/decision-log.md`: AI-Assisted Annotation Is The Initial Dataset Bootstrap Path; User Corrections Require Review Before Dataset Use; Workspace Data Use Agreement Required For Upload And Analysis.
- `architecture/domain-model.md`: Internal Capability, Dataset Curator, Draft Annotation, Reviewed Annotation, Annotation Source, Review Decision, Dataset Item, Dataset Role, Dataset Version, Training Run, and Model Candidate.
- `architecture/adr/0001-service-oriented-architecture.md`: Core API owns product workflow and authorization; model training and evaluation remain separate from V1 runtime services.
- `architecture/vertical-slice-0004-annotation-review-decision.md`: Review Decisions are append-only evidence, `approved` does not mean dataset-approved, and reviewer capability is separate from Workspace Membership.

## User Path

Given a project-owned Inspection Photo exists in a Workspace with an accepted Workspace Data Use Agreement
And a registered User has the internal `dataset_curator` capability
When the Dataset Curator starts AI-assisted dataset labelling for that photo
Then the system creates or returns the one active Dataset Labelling Session for that photo
And the system creates bee-only Draft Annotations from a deterministic image-dimension-aware pre-labelling seam
And the Web UI shows those annotations as machine suggestions on the original photo
And the Dataset Curator can optionally record source grouping and image quality metadata for the labelling session
When the Dataset Curator approves at least one complete visible bee and one partial visible bee suggestion
Then the Core API records Review Decisions against those Draft Annotations
And the evidence projection shows them as Reviewed Annotations for the `dataset_labelling` workflow
And no Dataset Role, Dataset Item, Dataset Version, Training Run, Model Candidate, or Benchmark Evaluation is created

## Preconditions

- Vertical Slices 0001, 0002, 0003, 0003.5, and 0004 are implemented and demoable.
- Development authentication remains represented by the dev-only auth header.
- The selected Inspection Photo belongs to the caller's Workspace.
- The Workspace has accepted the current Workspace Data Use Agreement.
- The caller is a registered User with the internal `dataset_curator` capability.
- Workspace ownership alone is not enough to start dataset labelling or review dataset-labelling Draft Annotations.
- Dataset labelling can start from any uploaded Inspection Photo that passes ownership and data-use gates. A product Analysis Result is not required.
- The first workflow is bee-only: `complete_visible_bee` and `partial_visible_bee`.
- `uncertain_bee` remains required by the baseline but is recorded as a deliberate gap for this slice.
- The pre-labelling mechanism is a deterministic stub behind an explicit interface. It must be easy to replace with a hosted labelling tool, general vision model, local detector, or trained HiveSight model later.
- The deterministic pre-labeller should derive normalized boxes from source image dimensions, not from fixed fixture-specific pixel coordinates.

## End-To-End Behaviour

The Beekeeper completes the existing inspection-photo intake path and uploads a project-owned Inspection Photo. A Dataset Curator then opens a minimal internal dataset-labelling surface and starts labelling for that photo.

The Core API creates a Dataset Labelling Session for the photo and calls a pre-labelling seam. Starting labelling is idempotent for Slice 5: if a session already exists for the photo, the Core API returns that session rather than creating another one.

In this slice, the seam is deterministic and returns a small set of bee-only Draft Annotations with normalized geometry, annotation type, optional confidence, source, pre-labeller name, and pre-labeller version. These Draft Annotations are stored using the shared Annotation shape, but they are not product Analysis Result output and are not User Corrections. They belong to the `dataset_labelling` workflow, have `labelling_session_id`, and have no `analysis_result_id`.

The Dataset Labelling Session records lightweight governance metadata:

- `source_group_key`, an optional manual grouping value used to flag photos that may represent the same source frame, near-duplicate sequence, hive/session, or other future leakage-risk group.
- `image_quality_status`, a session-level value of `unassessed`, `usable`, `poor_quality`, or `exclude`, defaulting to `unassessed`.
- `prelabeler_run`, a lightweight run block with adapter name, adapter version, started/finished timestamp, status, and optional error information.

`source_group_key` and `image_quality_status` are metadata only in Slice 5. They do not block annotation review and do not create Dataset Role assignment. In particular, `image_quality_status = exclude` does not mean Dataset Role `excluded`.

If pre-labelling fails, the session should expose a `prelabel_failed` state and error evidence. Starting labelling again returns the existing failed session. Retry behaviour is deferred until a later slice introduces explicit retry semantics.

The Web UI exposes this workflow through a separate internal dataset-labelling route or surface, rather than attaching it to the beekeeper-facing evidence page. The page displays the original Inspection Photo in the browser and renders the draft bee boxes over it. The UI clearly marks them as AI-assisted machine suggestions for dataset labelling. It includes simple controls for optional `source_group_key` and session-level `image_quality_status`. Capability-management UI is not required; the route or controls are simply gated to Users with `dataset_curator`.

The Dataset Curator can select a draft box and record a Review Decision using the same decision values established in Slice 0004:

- `approved`
- `rejected`
- `uncertain`
- `excluded`

For this slice, the happy path must support approving at least one `complete_visible_bee` and at least one `partial_visible_bee`. Rejected, uncertain, and excluded decisions should be accepted by the API if Slice 0004 already supports them, but the first browser happy path only needs to demonstrate approval.

Review Decisions remain append-only. The latest approved Review Decision projects a Draft Annotation as a Reviewed Annotation for the dataset-labelling workflow. That reviewed evidence is still not ground truth for model training until a later Dataset Role assignment slice creates Dataset Items.

The Web UI should keep the product-review and dataset-labelling meanings visually separate. It may reuse overlay, annotation-list, and review-control components, but the surface must not imply that product model output review and dataset bootstrap labelling are the same workflow.

Partial review is allowed. A new session starts as `draft_ready`, the first Review Decision moves it to `review_in_progress`, and Slice 5 does not automatically mark a session as `reviewed` because there is no finish-review action yet.

## Layers Touched

- Web UI: Adds a minimal internal dataset-labelling route or surface that loads one Inspection Photo, starts or opens a Dataset Labelling Session, renders AI-assisted Draft Annotations in the browser, lets a Dataset Curator update optional `source_group_key` and `image_quality_status`, and lets a Dataset Curator approve draft bee annotations. The surface should be usable/readable on mobile, but desktop-class labelling is the Slice 5 target.
- Core API: Adds idempotent Dataset Labelling Session workflow, Dataset Curator authorization checks, pre-labelling adapter seam, pre-labeller run evidence, lightweight source-group and image-quality metadata, draft-annotation storage/projection, and dataset-labelling review projection.
- Analysis Service: Not touched for real inference. The slice uses a deterministic pre-labeller seam owned by the Core API boundary for now; replacing that seam with an Analysis Service or external labelling tool is a later decision.
- Storage: Reuses existing original Inspection Photo storage and the current development metadata store. Adds only the minimum in-memory/dev records needed for labelling sessions and draft annotations unless durable persistence is chosen separately.
- Queue or async boundary: Not touched. Draft generation is synchronous for one photo in this slice.
- Contracts: Adds Dataset Labelling Session, pre-labeller run, session metadata, and Draft Annotation request/response shapes, plus a labelling evidence projection that preserves annotation source and review state.
- Observability: Adds test-visible evidence for labelling-session creation, pre-labeller invocation, pre-labeller failure, Dataset Curator identity, blocked unauthorized attempts, curation metadata, and separation from Dataset Role or training use.
- Verification reporting: Existing `pnpm verify:slice` should include the new Core API, API-level BDD, Web type-check, browser acceptance checks, and governance metadata evidence in the generated verification report.

## Test Seams

- Seam: Dataset Curator authorization
- Behaviour verified: a User with `dataset_curator` capability can start dataset labelling and review draft annotations; a normal Workspace owner without that internal capability cannot.
- Test style: FastAPI integration tests with dependency overrides and dev-auth headers.

- Seam: Dataset Labelling Session workflow
- Behaviour verified: starting labelling for a valid Inspection Photo creates or returns the existing active Dataset Labelling Session scoped to the Workspace and photo, without requiring a product Analysis Result.
- Test style: Core API workflow/unit tests with deterministic IDs and deterministic clock.

- Seam: Pre-labelling adapter
- Behaviour verified: the deterministic adapter returns bee-only Draft Annotations with complete/partial visible bee labels, normalized image-dimension-aware geometry, optional confidence, source, pre-labeller name, and pre-labeller version.
- Test style: Core API unit tests against the adapter interface and workflow tests using the deterministic adapter.

- Seam: Pre-labeller run evidence
- Behaviour verified: the session records adapter name, adapter version, started/finished time, status, and error evidence when pre-labelling fails; failed sessions are returned rather than silently replaced.
- Test style: Core API workflow/unit tests.

- Seam: Session curation metadata
- Behaviour verified: optional `source_group_key` and `image_quality_status` can be recorded and projected without blocking annotation review or creating Dataset Role assignment.
- Test style: Core API route/workflow tests and TypeScript client tests.

- Seam: Draft Annotation provenance
- Behaviour verified: Draft Annotations record `annotation_source = ai_assisted_draft`, `workflow_type = dataset_labelling`, `labelling_session_id`, no `analysis_result_id`, and do not appear as product Analysis Result output.
- Test style: Core API route/workflow tests.

- Seam: Review Decision projection for dataset labelling
- Behaviour verified: approved Draft Annotations project as Reviewed Annotations for the labelling workflow while retaining draft source and review provenance.
- Test style: Core API workflow/unit tests.

- Seam: API-level BDD acceptance
- Behaviour verified: a Dataset Curator creates AI-assisted Draft Annotations, records curation metadata, and approves bee suggestions; an ordinary Workspace owner is blocked from dataset labelling.
- Test style: pytest-bdd feature scenarios aimed at the Core API, not the Web UI.

- Seam: `CoreApiClient`
- Behaviour verified: Web code can start or load a Dataset Labelling Session, parse Draft Annotations, update `source_group_key` and `image_quality_status`, submit Review Decisions, and parse reviewed-state projection.
- Test style: TypeScript unit tests with mocked fetch responses.

- Seam: Web UI labelling surface
- Behaviour verified: a Dataset Curator can see machine-suggested bee boxes on the original photo, update lightweight session metadata, approve a complete visible bee and a partial visible bee, and see reviewed state update in the browser.
- Test style: Playwright browser acceptance through the existing Slice 0003.5 harness.

## Data Shape

Minimum additions:

- Internal Capability: `dataset_curator`.
- Workflow type: `dataset_labelling`.
- Dataset Labelling Session: `labelling_session_id`, `workspace_id`, `inspection_photo_id`, `created_by_user_id`, `status`, `source_group_key`, `image_quality_status`, `prelabeler_run`, `created_at`, `updated_at`.
- Labelling Session status: `draft_ready`, `review_in_progress`, `prelabel_failed`. `reviewed` is reserved for a later finish-review behaviour.
- Image quality status: `unassessed`, `usable`, `poor_quality`, `exclude`.
- Source group key: optional text, max 100 characters.
- Pre-labeller run: `prelabeler_run_id`, `prelabeler_name`, `prelabeler_version`, `status`, `started_at`, `finished_at`, `error_code`, `error_message`.
- Pre-labeller run status: `succeeded`, `failed`.
- Draft Annotation: `annotation_id`, `labelling_session_id`, `workspace_id`, `inspection_photo_id`, `analysis_result_id`, `annotation_type`, `geometry`, `geometry_unit`, `source_image_width`, `source_image_height`, `annotation_source`, `confidence`, `prelabeler_name`, `prelabeler_version`, `created_at`.
- Annotation type: `complete_visible_bee`, `partial_visible_bee`.
- Annotation Source: `ai_assisted_draft`.
- For dataset-labelling Draft Annotations, `analysis_result_id` is null or absent.
- Review Decision: reuse Slice 0004 shape with `subject_type = annotation`; the subject is a dataset-labelling Draft Annotation.
- Reviewed Annotation projection: Draft Annotation fields plus latest approved Review Decision fields and `workflow_type = dataset_labelling`.

Minimum API shapes:

- Start labelling request: `workspace_id`, `inspection_photo_id`.
- Start labelling response: `labelling_session_id`, `workspace_id`, `inspection_photo_id`, `status`, `source_group_key`, `image_quality_status`, `prelabeler_run`, `draft_annotations`.
- Update session metadata request: `source_group_key`, `image_quality_status`.
- Labelling evidence response: `inspection_photo`, `labelling_session`, `draft_annotations`, `reviewed_annotations`, `latest_review_decisions`.
- Blocked response codes: `not_authenticated`, `dataset_curator_access_required`, `workspace_access_denied`, `data_use_agreement_required`, `inspection_photo_not_found`, `unsupported_annotation_type`, `invalid_review_subject`, `invalid_review_decision`, `invalid_source_group_key`, `invalid_image_quality_status`, `prelabel_failed`.

## Out Of Scope

- Real bee detection, real Varroa detection, confidence calibration, or model artifact loading.
- Hosted AI, hosted labelling platform integration, hosted training, or any external image transfer.
- Metadata minimisation or EXIF-stripping changes beyond the existing local upload path, because this slice does not send images to a hosted service.
- Geometry editing, drawing new annotations, deleting false positives, adding missed bees, keyboard labelling, bulk approval, review queues, assignment, double review, adjudication, or audit dashboards.
- Automatic duplicate or near-duplicate detection, perceptual hashing, source grouping suggestions, or leakage enforcement. Slice 5 only records optional manual `source_group_key` metadata.
- Dataset export of any kind, including internal JSON export, YOLO export, or COCO export. The labelling evidence API response is not a Dataset Version export.
- Retry UI or explicit retry workflow for failed pre-labelling.
- `uncertain_bee` as a separate annotation type. The requirement remains documented and should be covered by a pending/gap scenario.
- Varroa labels, likely Varroa detections, mite-to-bee association, or Visible Varroa Rate.
- Dataset Role assignment, Dataset Item creation, Dataset Version creation, benchmark protection enforcement, Training Run creation, Model Candidate creation, Benchmark Evaluation, or model promotion.
- Treating Reviewed Annotations as training-ready ground truth.
- Production auth provider integration, invitation flow, internal capability management UI, or full admin console.
- Durable database persistence if the in-memory/dev store remains sufficient for the slice.
- UI-level Gherkin. Later Slice 0013 planning parked this as a future option; this slice continues to rely on plain Playwright for browser acceptance.

## Acceptance Criteria

- [ ] A Dataset Curator can start dataset labelling for one project-owned Inspection Photo in a Workspace with an accepted Workspace Data Use Agreement.
- [ ] A Workspace owner without `dataset_curator` internal capability is blocked from starting dataset labelling.
- [ ] Dataset labelling is blocked when the selected Inspection Photo is missing, belongs to another Workspace, or lacks an accepted Workspace Data Use Agreement.
- [ ] Dataset labelling can start from an uploaded Inspection Photo even when no product Analysis Result exists.
- [ ] Starting labelling creates or returns the existing active Dataset Labelling Session scoped to the Workspace and Inspection Photo.
- [ ] A new successful Dataset Labelling Session starts in `draft_ready` status.
- [ ] The deterministic pre-labelling seam creates bee-only Draft Annotations for at least one `complete_visible_bee` and one `partial_visible_bee`.
- [ ] The deterministic pre-labelling seam derives boxes from source image dimensions so suggestions remain inside the rendered image.
- [ ] Draft Annotations record normalized geometry, source image dimensions, optional confidence, `annotation_source = ai_assisted_draft`, pre-labeller name, pre-labeller version, and `workflow_type = dataset_labelling`.
- [ ] Dataset-labelling Draft Annotations have `labelling_session_id` and no `analysis_result_id`.
- [ ] Draft Annotations are not exposed as product Analysis Result output and are not User Corrections.
- [ ] A Dataset Labelling Session records lightweight `prelabeler_run` evidence with adapter name, adapter version, status, timestamps, and error details when relevant.
- [ ] If pre-labelling fails, the session exposes `prelabel_failed` state and is returned by later start attempts rather than being silently replaced.
- [ ] A Dataset Curator can optionally record `source_group_key` on the Dataset Labelling Session.
- [ ] A Dataset Curator can set session-level `image_quality_status` to `unassessed`, `usable`, `poor_quality`, or `exclude`.
- [ ] `source_group_key` and `image_quality_status` do not block annotation review and do not create Dataset Role assignment.
- [ ] The Web UI renders the original Inspection Photo in the browser with AI-assisted draft bee boxes overlaid.
- [ ] The Web UI clearly indicates that the boxes are machine suggestions for dataset labelling.
- [ ] The Web UI exposes dataset labelling through a separate internal route or surface.
- [ ] The Web UI includes simple controls for optional `source_group_key` and session-level `image_quality_status`.
- [ ] A Dataset Curator can approve at least one complete visible bee Draft Annotation and one partial visible bee Draft Annotation.
- [ ] The first Review Decision moves the session to `review_in_progress`.
- [ ] Slice 5 does not automatically mark a session as `reviewed`.
- [ ] Review Decisions are stored as append-only records and do not overwrite the Draft Annotation.
- [ ] Approved Draft Annotations project as Reviewed Annotations for the `dataset_labelling` workflow.
- [ ] Reviewed Annotation projection preserves Draft Annotation provenance and reviewer provenance.
- [ ] Approved Reviewed Annotations are not assigned to training, validation, benchmark, excluded, Dataset Item, Dataset Version, Training Run, Model Candidate, or Benchmark Evaluation records.
- [ ] Product annotation review and dataset-labelling review remain distinct in API contracts, stored provenance, and UI wording.
- [ ] API-level BDD scenarios cover the Dataset Curator happy path, curation metadata, and one blocked unauthorized dataset-labelling attempt.
- [ ] A pending or documented-gap BDD scenario records that `uncertain_bee` annotation type support is required but not implemented in this slice.
- [ ] Browser acceptance covers the Dataset Curator happy path through the existing Playwright harness.
- [ ] Browser acceptance targets a desktop-class labelling workflow; mobile should remain usable/readable but is not optimized in Slice 5.
- [ ] `pnpm verify:slice` includes the Slice 5 checks and governance metadata evidence in the generated verification report.
- [ ] The implementation preserves the target architecture: Web UI calls Core API; Core API owns dataset workflow and authorization; real model training and evaluation remain outside this slice.

## Decisions For This Slice

- Slice 5 starts the AI-assisted dataset bootstrap path but stops before Dataset Role assignment.
- The actor is a Dataset Curator: a registered User with internal `dataset_curator` capability.
- Workspace ownership does not grant dataset-labelling authority.
- Dataset labelling can start from an uploaded Inspection Photo without a product Analysis Result.
- Slice 5 introduces Dataset Labelling Session as a first-class workflow concept.
- There is one active Dataset Labelling Session per Inspection Photo in Slice 5. Starting labelling is idempotent and returns the existing session.
- Draft Annotations in this slice belong to `workflow_type = dataset_labelling`.
- Draft Annotations reuse the shared Annotation shape, with `labelling_session_id`, `annotation_source`, `workflow_type`, and no `analysis_result_id` preserving separation.
- Reviewed Annotation is a projection of Draft Annotation plus latest approved Review Decision, not a copied second annotation record.
- The first label set is bee-only: `complete_visible_bee` and `partial_visible_bee`.
- The Slice 5 happy path requires at least one approved `complete_visible_bee` and one approved `partial_visible_bee`.
- The pre-labeller is deterministic, image-dimension-aware, and replaceable.
- Draft Annotation confidence is optional provenance only. Slice 5 does not sort, filter, threshold, or decide from confidence.
- The Dataset Labelling Session records optional `source_group_key` and session-level `image_quality_status`.
- `source_group_key` is optional, manually entered, and does not implement automatic duplicate detection.
- `image_quality_status` defaults to `unassessed`, is editable in the UI, and does not block annotation review.
- The Dataset Labelling Session records lightweight `prelabeler_run` evidence.
- Failed pre-labelling creates visible `prelabel_failed` state. Starting labelling again returns the existing failed session until a later explicit retry workflow is defined.
- The first implementation uses browser-rendered overlays on the original image. Overlay pixels are not saved into the image.
- Review approval means "accepted as reviewed annotation evidence for this labelling workflow"; it does not mean "eligible for model training".
- The Slice 5 UI happy path only needs to prove approval, while API tests may cover rejected, uncertain, and excluded values.
- Partial review is allowed. The session moves from `draft_ready` to `review_in_progress` after the first Review Decision; `reviewed` is reserved for a later finish-review behaviour.
- The dataset-labelling UI is a separate internal route or surface gated by `dataset_curator`, not a capability-management UI.
- Desktop-class labelling is the target. Mobile should remain usable/readable but is not optimized in this slice.
- Slice 5 does not introduce real model/tool selection.
- Dataset Role assignment and Dataset Item creation should be defined in the next model-readiness slice.

## Open Questions

- Should the next slice assign Dataset Roles at the whole-photo level first, or should it introduce finer-grained Dataset Items immediately?
- Should the real pre-labelling path first use a hosted vision/labelling service, a local open-source detector, or a general-purpose model used only for suggestions?
- When geometry editing arrives, should it be implemented first as drag handles on existing boxes, add/remove controls, or import/export with an external annotation tool?
