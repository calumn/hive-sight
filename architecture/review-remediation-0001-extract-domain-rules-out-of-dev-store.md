# Review Remediation 0001: Extract Domain Rules Out Of Dev Store

## Purpose

Reduce the architectural risk identified in the 2026-07-30 external review: `dev_store.py` is currently acting as both the in-memory persistence adapter and the owner of major HiveSight domain rules.

This remediation makes the codebase safer for real persistence by moving selected business rules out of the in-memory store and into explicit workflow/application modules. After this work, the dev store should be closer to a replaceable repository implementation rather than the central domain brain.

## Source Inputs

- `architecture/review-remediation-2026-07-30.md`
- `architecture/codebase-design.md`
- `architecture/adr/0001-service-oriented-architecture.md`
- `architecture/domain-model.md`
- `requirements/ai-sdlc-observations.md`
- Current `services/core-api/src/hive_sight_core_api/dev_store.py`
- Current Core API workflow modules:
  - `analysis_request_workflow.py`
  - `analysis_processing_workflow.py`
  - `dataset_labelling_workflow.py`
  - `dataset_role_assignment_workflow.py`
  - `inspection_photo_access.py`

## Remediation Path

Given the Core API currently passes all product-slice tests
When the team introduces explicit application services and repository protocols around the busiest domain rules
Then the same API, BDD, and browser acceptance behaviour remains green
And `dev_store.py` no longer owns those domain decisions directly
And future persistence work can target repository methods instead of recreating business behaviour hidden inside the in-memory store.

## Preconditions

- Slice 12 remains the latest implemented functional slice.
- No real persistent database exists yet.
- Existing public API and UI behaviour must remain unchanged.
- Existing BDD scenarios and Playwright acceptance tests must remain green.
- This remediation should not change product capability, only code ownership and test seams.

## Problem Statement

`InMemoryProductDataStore` currently owns too much:

- Workspace authorization checks.
- Workspace Data Use Agreement checks.
- Reviewer and Dataset Curator capability checks.
- Inspection intent policy.
- Dataset Labelling eligibility.
- Training Crop bounds, lock, review, and exclusion rules.
- Oriented bee ellipse validation.
- Dataset Item role-assignment rules.
- YOLO OBB export eligibility and protected benchmark rules.
- Hive Configuration validation and Inspection creation gating.
- Provenance snapshot assembly.
- Physical export package construction.

Some of this belongs in repositories, but much of it is application/domain workflow policy. If real persistence is added now, either the database adapter will inherit business rules it should not own, or every rule will need to be rediscovered and moved under pressure.

## Strategy

Use expand, migrate, contract.

Expand:

- Introduce small `Protocol` interfaces for the repository capabilities needed by workflows.
- Add application services for the highest-value rule clusters.
- Keep `InMemoryProductDataStore` as the concrete repository behind those protocols.
- Preserve old public behaviour while tests move to the new seams.

Migrate:

- Move domain validation and orchestration into workflow/application services.
- Change FastAPI dependencies to inject those workflow/application services.
- Keep store methods as simple data reads/writes wherever practical.

Contract:

- Remove duplicated validation from `dev_store.py` once equivalent workflow tests prove behaviour.
- Rename or split store methods so the remaining API reads like persistence operations rather than use-case operations.

## Thin Remediation Scope

This first remediation slice should not attempt to clean the whole store.

Target rule clusters:

1. Training Crop workflow rules.
2. Dataset Item assignment rules.
3. Hive Configuration and Inspection creation gate.

These clusters are selected because they are recent, high-churn, heavily tested, and directly relevant to the next model-training work.

## End-To-End Behaviour

From the user perspective, nothing changes:

- A Beekeeper still creates Apiary, Hive, Hive Configuration, and Inspection through the existing UI.
- Dataset Curators still create Training Crops, annotate oriented bee ellipses, complete review, assign Dataset Roles, and export YOLO OBB data.
- All existing Core API routes keep their current request and response contracts.
- Existing browser acceptance flows keep passing.

From the code perspective:

- Route handlers call workflow/application services for use cases.
- Workflow/application services enforce domain rules.
- Repository protocols expose persistence-shaped methods.
- In-memory store implements those protocols for now.
- Tests can target workflow/application services directly, with in-memory repositories or focused fakes.

## Proposed Module Shape

### Repository Protocols

Add a small protocol module, for example:

`services/core-api/src/hive_sight_core_api/repositories.py`

Candidate protocols:

- `WorkspaceRepository`
- `HiveRepository`
- `InspectionRepository`
- `InspectionPhotoRepository`
- `TrainingCropRepository`
- `DatasetItemRepository`
- `HiveConfigurationRepository`

Do not create one protocol per helper function. Protocols should be grouped by the aggregate or workflow need.

### Application Services

Add focused services only where behaviour is currently substantial:

- `inspection_workflow.py`
  - create Inspection
  - enforce Hive Configuration requirement
  - update Inspection intent lock rules

- `hive_configuration_workflow.py`
  - list Frame Standards
  - upsert current Hive Configuration
  - enforce `other` notes rule
  - enforce Workspace ownership through Hive

- `training_crop_workflow.py`
  - create Training Crop
  - update Training Crop review state
  - create/update/delete oriented bee ellipses
  - enforce crop bounds, crop locks, zero-bee rules, and ellipse containment

- `dataset_item_workflow.py`
  - assign reviewed Dataset Labelling Session to Dataset Item
  - assign completed Training Crop to Dataset Item
  - enforce Dataset Role/exclusion rules
  - assemble Dataset Item provenance snapshot

The current export code may stay in `dev_store.py` for this first remediation if extracting it would make the slice too wide. If it moves, prefer a separate `dataset_export_workflow.py`.

## Layers Touched

- Web UI: Not touched.
- Core API routes: Updated only to call injected workflow/application services where the selected rules move.
- Core API workflow modules: Add or expand application services for selected rule clusters.
- Storage: In-memory store remains the only concrete repository; its interface becomes more persistence-shaped.
- Queue or async boundary: Not touched.
- Contracts: No public API contract changes.
- Observability: Preserve existing stable `DomainError` codes and messages.

## Dependency Injection Direction

Use FastAPI dependency functions at the HTTP edge:

- build repository-backed workflows from `DevStateDep`
- inject workflows into routes with `Annotated[..., Depends(...)]`
- pass plain `UserContext`, request models, and ids into workflows

Avoid service locators or hidden globals.

Avoid adding protocols unless there is a clear workflow boundary or a near-term persistence adapter need.

## Test Seams

- Seam: `InspectionWorkflow`
- Behaviour verified: Inspection creation requires current Hive Configuration; intent update is locked after photo upload.
- Test style: direct workflow unit tests plus existing API/BDD tests.

- Seam: `HiveConfigurationWorkflow`
- Behaviour verified: Frame Standard catalogue is exposed; `other` requires notes; `unknown` does not; known Frame Standard controls hive type and frame use.
- Test style: direct workflow unit tests plus existing API/BDD tests.

- Seam: `TrainingCropWorkflow`
- Behaviour verified: crop bounds, crop locking, zero-bee completion rules, excluded crop rules, oriented ellipse containment.
- Test style: direct workflow unit tests plus existing API/BDD tests.

- Seam: `DatasetItemWorkflow`
- Behaviour verified: reviewed evidence can become a Dataset Item; Dataset Role and exclusion rules are enforced; provenance snapshots Hive Configuration.
- Test style: direct workflow unit tests plus existing API/BDD tests.

- Seam: Core API
- Behaviour verified: route contracts and stable error codes are unchanged.
- Test style: existing API tests and API-level BDD.

- Seam: Web acceptance
- Behaviour verified: existing user flows still pass after backend ownership changes.
- Test style: existing Playwright suite.

## Data Shape

No public data-shape changes are intended.

Internal protocol method names should favour persistence language:

- `get_workspace(...)`
- `get_hive(...)`
- `save_hive_configuration(...)`
- `get_current_hive_configuration(...)`
- `get_inspection(...)`
- `save_inspection(...)`
- `list_inspection_photos(...)`
- `get_training_crop(...)`
- `save_training_crop(...)`
- `list_training_crop_ellipses(...)`
- `save_dataset_item(...)`

Avoid workflow-shaped repository methods such as:

- `create_training_crop(...)`
- `create_dataset_item_from_training_crop(...)`
- `create_yolo_obb_export(...)`

Those names should belong to workflow/application services.

## Acceptance Criteria

- [x] `dev_store.py` no longer owns Training Crop validation rules directly.
- [x] `dev_store.py` no longer owns Dataset Item assignment validation rules directly for Training Crop assignment.
- [x] `dev_store.py` no longer owns Hive Configuration validation rules directly.
- [x] Inspection creation gating is enforced by an application workflow rather than a store method.
- [x] New workflow/application service tests cover the moved rules directly.
- [x] Existing Core API tests continue to pass without weakening assertions.
- [x] Existing API-level BDD scenarios continue to pass.
- [x] Existing Playwright browser acceptance tests continue to pass.
- [x] Public request/response contracts do not change.
- [x] Stable `DomainError` codes and messages remain unchanged.
- [x] `architecture/review-remediation-2026-07-30.md` marks R-001 as partially actioned with residual debt.
- [x] `requirements/ai-sdlc-observations.md` records the remediation outcome after implementation.
- [x] `pnpm verify:slice` passes.

## Out Of Scope

- Introducing a real database.
- Selecting the production persistence technology.
- Rewriting all of `dev_store.py`.
- Changing Core API route paths or public response shapes.
- Changing Web UI behaviour.
- Changing Analysis Service integration.
- Implementing queue technology.
- Implementing production authentication.
- Extracting every possible protocol.
- Refactoring only for file size without moving ownership of meaningful rules.

## Risks

- Over-abstraction: adding too many protocols could make the code harder to understand without moving real behaviour.
- Behaviour drift: moving validation rules could accidentally change stable error codes or edge-case outcomes.
- Half extraction: leaving rules duplicated in both workflows and store would make future changes confusing.
- Slice creep: attempting to solve persistence, auth, queueing, and service integration in the same remediation would make this too large.

## Implementation Notes

- Move one rule cluster at a time.
- Preserve old API tests while adding direct workflow tests.
- Prefer small data-access protocols over a generic repository interface.
- Keep `InMemoryProductDataStore` concrete and boring.
- Use existing `DomainError` semantics rather than introducing a new error hierarchy in this slice.
- Do not change frontend code unless a route dependency change accidentally affects browser acceptance.

## Suggested Build Order

1. Add repository protocols for the selected rule clusters.
2. Add `HiveConfigurationWorkflow` and route dependencies; move Hive Configuration validation.
3. Add `InspectionWorkflow`; move Inspection creation gate and intent lock rule.
4. Add `TrainingCropWorkflow`; move crop and ellipse validation.
5. Add `DatasetItemWorkflow`; move role-assignment validation and provenance assembly.
6. Simplify `InMemoryProductDataStore` methods to persistence operations where the moved workflows now own orchestration.
7. Run full verification and update remediation/AI-SDLC docs.

## Open Questions

- Resolved: physical YOLO OBB export stays in `dev_store.py` for this remediation and remains residual debt.
- Resolved: capability checks remain on `InMemoryProductDataStore` temporarily; extracting authorization policy is deferred until auth becomes real.
- Resolved: no formal `repositories.py` was added yet. The remediation introduced persistence-shaped store methods first because there is still only one concrete adapter.

## Implementation Outcome

Implemented on 2026-07-30.

New application workflow seams:

- `HiveConfigurationWorkflow`
  - owns Frame Standard selection rules, `other` notes validation, Hive Configuration upsert, Hive Configuration lookup, Inspection creation gating, and Inspection intent locking.
- `TrainingCropWorkflow`
  - owns Training Crop bounds validation, editable-state locking, zero-bee review rules, oriented bee ellipse validation, ellipse lifecycle, and Training Crop evidence projection.
- `TrainingCropDatasetItemWorkflow`
  - owns Training Crop to Dataset Item assignment rules, exclusion validation, reviewed ellipse snapshot creation, and Training Crop provenance snapshot assembly.

Store changes:

- Added persistence-shaped methods such as `get_hive`, `get_current_hive_configuration`, `save_hive_configuration`, `save_inspection`, `inspection_has_photos`, `get_inspection_photo`, `list_training_crops_for_photo_id`, `save_training_crop`, `save_training_crop_ellipse`, `get_training_crop_ellipse`, `delete_training_crop_ellipse_record`, and `save_dataset_item`.
- Kept legacy store use-case method names as compatibility wrappers where helpful, but FastAPI routes now call injected workflows for the moved rule clusters.

Verification:

- Focused workflow and related API tests: 20 passed.
- Core API tests: 83 passed, 1 xfailed.
- Ruff: passed.
- `pnpm verify:slice`: passed, including Core API tests, Analysis Service tests, Web TypeScript check, and 10 Playwright browser acceptance tests.

Residual debt:

- Older Dataset Labelling Session to Dataset Item assignment still uses `DatasetRoleAssignmentWorkflow` plus store persistence methods.
- YOLO OBB export and physical package construction remain in `dev_store.py`.
- Workspace authorization, Data Use Agreement, and dataset-curator capability checks remain on the in-memory store until production auth/persistence decisions justify an explicit policy/repository split.
