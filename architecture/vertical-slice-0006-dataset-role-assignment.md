# Vertical Slice 0006: Dataset Role Assignment

## Purpose

Prove that HiveSight can take reviewed dataset-labelling evidence from Slice 5 and explicitly assign it to a Dataset Role, creating a traceable Dataset Item without creating a Dataset Version, export, Training Run, Model Candidate, Benchmark Evaluation, or approved Model Version.

This slice closes the gap between "human-reviewed annotation evidence exists" and "this reviewed photo/annotation unit is allowed to participate in a future dataset split."

## Source Inputs

- `CONTEXT.md`: Dataset Curator, Internal Capability, Reviewed Annotation, Dataset Item, Dataset Role, Dataset Version, Training Run, Model Candidate, Benchmark Evaluation.
- `requirements/ai-assisted-annotation-and-model-training-baseline.md`: Dataset Role assignment, dataset split separation, protected benchmark, duplicate and near-duplicate handling, dataset exclusion reasons, lightweight image quality status.
- `requirements/product-spec.md`: "Reviewed annotations are assigned to dataset roles" and "Benchmark data is protected from model training".
- `architecture/domain-model.md`: Dataset Item, Dataset Role, Dataset Curator, Internal Capability, Review Decision, Dataset Version, Training Run, Model Candidate.
- `architecture/vertical-slice-0005-ai-assisted-bee-annotation-bootstrap.md`: reviewed dataset-labelling annotations, `source_group_key`, image quality status, and the decision to defer Dataset Role assignment.

## User Path

Given a Dataset Curator has reviewed bee Draft Annotations in a Dataset Labelling Session
And the labelling session has optional source grouping and image quality metadata
When the Dataset Curator assigns a Dataset Role to the reviewed photo/annotation evidence
Then the Core API creates a Dataset Item for that Inspection Photo and labelling session
And the Dataset Item records its role as `training`, `validation`, `benchmark`, or `excluded`
And the Dataset Item preserves source grouping, image quality, reviewer provenance, and assignment provenance
And no Dataset Version, export, Training Run, Model Candidate, Benchmark Evaluation, or model promotion is created

## Preconditions

- Vertical Slice 0005 is implemented and demoable.
- The caller is a registered User with internal `dataset_curator` capability.
- Workspace ownership alone is not enough to assign Dataset Roles.
- The Workspace has accepted the Workspace Data Use Agreement.
- The Dataset Labelling Session belongs to the caller's Workspace.
- The Dataset Labelling Session has at least one Reviewed Annotation projected from an approved Review Decision.
- Dataset Role assignment is initially photo/session-level, not per-annotation.
- `source_group_key` remains optional, but must be preserved when present.
- `image_quality_status = exclude` does not automatically create Dataset Role `excluded`; the curator still makes an explicit Dataset Role assignment.

## End-To-End Behaviour

The Dataset Curator opens the internal dataset-labelling evidence created in Slice 5. The page shows the reviewed annotations, current labelling session metadata, and a Dataset Role assignment control.

For Slice 6, allowed Dataset Roles are:

- `training`
- `validation`
- `benchmark`
- `excluded`

The Dataset Curator selects one role and optionally enters an assignment note. If the role is `excluded`, the curator must select an exclusion reason from a small controlled list. If the role is not `excluded`, exclusion reason is absent.

The Core API creates a Dataset Item scoped to the Workspace, Inspection Photo, and Dataset Labelling Session. The Dataset Item records who assigned it, when it was assigned, the selected Dataset Role, optional note, exclusion reason where applicable, the current `source_group_key`, the current `image_quality_status`, and the Reviewed Annotation ids that were eligible at assignment time.

Dataset Item creation is append-only for Slice 6. Reassigning the same labelling session to a different role is out of scope; the implementation may reject a second assignment for the same labelling session with `dataset_item_already_assigned`.

Benchmark protection starts as a data rule: Dataset Items with role `benchmark` are visibly marked as protected benchmark data and are not included in any training/export/model workflow because those workflows do not exist yet. Future slices must enforce this when exports, Dataset Versions, Training Runs, and model selection are implemented.

## Layers Touched

- Web UI: Adds a Dataset Role assignment panel to the internal dataset-labelling surface. The panel shows reviewed annotation count, source group key, image quality status, role selection, optional note, exclusion reason when needed, and the resulting Dataset Item state.
- Core API: Adds Dataset Item creation, Dataset Curator authorization, Dataset Role validation, exclusion reason validation, duplicate assignment protection, and Dataset Item evidence projection.
- Analysis Service: Not touched.
- Storage: Reuses the current development store and adds minimum Dataset Item records.
- Queue or async boundary: Not touched.
- Contracts: Adds Dataset Item request/response shapes and extends labelling evidence with optional Dataset Item state.
- Observability: Adds test-visible evidence for role assignment, blocked unauthorized assignment, source-group preservation, benchmark protection flag, and no Dataset Version/export/training side effects.
- Verification reporting: `pnpm verify:slice` should include Core API tests, API-level BDD, Web type-check, browser acceptance, and report evidence for Dataset Role assignment.

## Test Seams

- Seam: Dataset Curator authorization
- Behaviour verified: a User with `dataset_curator` can assign a Dataset Role; a Workspace owner without internal capability cannot.
- Test style: FastAPI integration tests with dependency overrides and dev-auth headers.

- Seam: Dataset Item creation
- Behaviour verified: reviewed dataset-labelling evidence creates one Dataset Item with role, assignment provenance, source grouping, image quality, and reviewed annotation ids.
- Test style: Core API workflow/unit tests with deterministic IDs and clock.

- Seam: Dataset Role validation
- Behaviour verified: only `training`, `validation`, `benchmark`, and `excluded` are accepted; `excluded` requires an exclusion reason; non-excluded roles do not carry an exclusion reason.
- Test style: Core API route/workflow tests.

- Seam: Duplicate assignment protection
- Behaviour verified: assigning the same Dataset Labelling Session twice is rejected for Slice 6.
- Test style: Core API route/workflow tests.

- Seam: API-level BDD acceptance
- Behaviour verified: a Dataset Curator assigns reviewed annotations to a Dataset Role; benchmark assignment is visibly protected; unauthorized assignment is blocked.
- Test style: pytest-bdd feature scenarios aimed at the Core API.

- Seam: `CoreApiClient`
- Behaviour verified: Web code can submit Dataset Role assignment and parse Dataset Item projection.
- Test style: TypeScript type-check and client parsing through browser acceptance.

- Seam: Web UI assignment surface
- Behaviour verified: a Dataset Curator can assign a role from reviewed labelling evidence and see the created Dataset Item state.
- Test style: Playwright browser acceptance through the existing harness.

## Data Shape

Minimum additions:

- Dataset Role: `training`, `validation`, `benchmark`, `excluded`.
- Dataset Item: `dataset_item_id`, `workspace_id`, `inspection_photo_id`, `labelling_session_id`, `dataset_role`, `reviewed_annotation_ids`, `source_group_key`, `image_quality_status`, `assigned_by_user_id`, `assigned_at`, `assignment_note`, `exclusion_reason`, `benchmark_protected`.
- Exclusion reason: `poor_image_quality`, `ambiguous_subject`, `duplicate_or_near_duplicate`, `privacy_concern`, `unsuitable_crop`, `insufficient_review_confidence`, `other`.

Minimum API shapes:

- Create Dataset Item request: `workspace_id`, `labelling_session_id`, `dataset_role`, `assignment_note`, `exclusion_reason`.
- Create Dataset Item response: Dataset Item shape above.
- Labelling evidence extension: optional `dataset_item`.
- Blocked response codes: `not_authenticated`, `dataset_curator_access_required`, `workspace_access_denied`, `data_use_agreement_required`, `labelling_session_not_found`, `reviewed_annotations_required`, `invalid_dataset_role`, `exclusion_reason_required`, `exclusion_reason_not_allowed`, `dataset_item_already_assigned`.

## Out Of Scope

- Dataset Version creation.
- Dataset export, including internal JSON, YOLO, COCO, or external annotation-tool export.
- Training Run creation.
- Model Candidate creation.
- Benchmark Evaluation execution.
- Model promotion.
- Automatic train/validation/benchmark split recommendation.
- Automatic duplicate or near-duplicate detection.
- Enforcing source-group leakage across multiple Dataset Items beyond preserving `source_group_key`.
- Reassigning Dataset Items or maintaining role-assignment history.
- Per-annotation Dataset Role assignment.
- Geometry editing, adding missed bees, deleting false positives, or `uncertain_bee` annotation type support.
- Real pre-labelling helper/model selection. This is expected to be Slice 0007.
- Production auth provider integration or internal capability management UI.

## Acceptance Criteria

- [ ] A Dataset Curator can assign reviewed dataset-labelling evidence to `training`.
- [ ] A Dataset Curator can assign reviewed dataset-labelling evidence to `validation`.
- [ ] A Dataset Curator can assign reviewed dataset-labelling evidence to `benchmark`.
- [ ] A Dataset Curator can assign reviewed dataset-labelling evidence to `excluded` with an exclusion reason.
- [ ] A Workspace owner without `dataset_curator` capability is blocked from Dataset Role assignment.
- [ ] Dataset Role assignment is blocked when the Workspace Data Use Agreement is not accepted.
- [ ] Dataset Role assignment is blocked when the labelling session has no Reviewed Annotations.
- [ ] Dataset Role assignment is blocked for unsupported Dataset Role values.
- [ ] `excluded` requires an exclusion reason.
- [ ] Non-`excluded` roles reject exclusion reason.
- [ ] Assigning the same Dataset Labelling Session twice is rejected for Slice 6.
- [ ] Dataset Item preserves `source_group_key` when present.
- [ ] Dataset Item preserves session-level `image_quality_status`.
- [ ] Dataset Item records reviewed annotation ids that were approved at assignment time.
- [ ] Dataset Item records `assigned_by_user_id`, `assigned_at`, and optional assignment note.
- [ ] Dataset Items with role `benchmark` are marked `benchmark_protected = true`.
- [ ] Dataset Items with role other than `benchmark` are marked `benchmark_protected = false`.
- [ ] Labelling evidence projects the created Dataset Item.
- [ ] Dataset Item creation does not create Dataset Version, export, Training Run, Model Candidate, Benchmark Evaluation, or model promotion records.
- [ ] API-level BDD covers successful Dataset Role assignment and blocked unauthorized assignment.
- [ ] Browser acceptance covers the Dataset Curator happy path.
- [ ] `pnpm verify:slice` includes Slice 6 checks in the generated verification report.

## Decisions For This Slice

- Slice 6 assigns Dataset Roles at photo/labelling-session level, not per annotation.
- Dataset Role assignment creates a Dataset Item.
- Dataset Item creation requires at least one Reviewed Annotation.
- Dataset Item creation is append-only for Slice 6; reassignment is deferred.
- `source_group_key` is preserved for future leakage handling but not automatically enforced yet.
- `image_quality_status = exclude` is metadata and does not replace explicit Dataset Role assignment.
- Benchmark protection begins as a persisted Dataset Item flag; later training/export slices must enforce it.
- Slice 7 should focus on a separate, vaguely real pre-labelling helper before heavy annotation-editor UI.

## Open Questions

- Should Slice 6 require a minimum number of reviewed annotations before assigning `training`, `validation`, or `benchmark`, or is one reviewed annotation enough for the tracer?
- Should assignment notes keep the same 500 character limit as Review Decision notes?
- Should `other` exclusion reason require a note?
