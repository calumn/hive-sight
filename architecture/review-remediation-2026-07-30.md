# Review Remediation: 2026-07-30 External Code And Artifact Review

## Purpose

Capture and track remediation from the external HiveSight review before continuing new functional slices.

The review found that the delivered code and domain vocabulary are strong for this stage, but that several architecture and process debts should be handled deliberately before the project grows further.

## Source

- `/Users/calumnobles/Library/Application Support/Claude/local-agent-mode-sessions/d0655ebb-fa4f-4952-98d6-be6be63ef5b6/735d7aa0-a1d5-4bab-9628-53c087a8c8c3/local_4d71f726-6550-447c-9083-d4cff14f1d94/outputs/hive-sight-review.md`

## Actioned Now

- Removed the unused unauthenticated `GET /v1/inspection-photos/{inspection_photo_id}/upload-url` route.
- Removed the `InspectionPhotoAccess.create_upload_access(...)` implementation that generated unsigned object-storage URLs without Workspace, DUA, content-type, size, or audit checks.
- Removed the unit test that asserted the unsafe upload-url behaviour.
- Marked `architecture/vertical-slice-0010-bee-annotation-repository.md` as superseded by `architecture/vertical-slice-0010-bee-annotation-repository-and-dataset-export.md`.
- Resumed `requirements/ai-sdlc-observations.md` with architecture/delivery and review-remediation entries.
- Updated `architecture/codebase-design.md` to state that any future signed upload-url seam must enforce auth, DUA, validation, expiry, scoping, and audit metadata before it is exposed.

## Remaining Review Backlog

### R-001: Extract Domain Logic Out Of `dev_store.py`

Status: partially actioned by Review Remediation 0001

Problem:

`dev_store.py` is currently the real owner of Workspace authorization checks, Data Use Agreement enforcement, dataset-curator checks, geometry validation, role-assignment rules, export validation, and Hive Configuration rules. The architecture intended the store to be a replaceable persistence adapter, but it has become a deep business module.

Recommended next action:

Review Remediation 0001 moved Hive Configuration/Inspection gating, Training Crop rules, and Training Crop Dataset Item assignment into explicit workflows. Residual debt remains for export/package construction, production authorization policy, and the eventual real persistence adapter.

### R-002: Decide Analysis Service Integration Direction

Status: open

Problem:

The Analysis Service is tested but not called by the Core API. Core API still runs in-process stub analysis, and the two services duplicate fixture-style analysis behaviour.

Recommended next action:

Choose one of two paths before real model work deepens:

- Wire Core API to Analysis Service through an owned request/result contract.
- Or fold the stub behaviour back into Core API until the model runtime warrants a separate service.

### R-003: Resolve UI-Level Gherkin Commitment

Status: open

Problem:

Several slice documents state that UI-level Gherkin should be introduced soon, but browser acceptance tests currently use Playwright specs directly.

Recommended next action:

Either create a UI BDD harness slice or explicitly revise the delivery standard to keep UI acceptance in Playwright while API acceptance remains Gherkin.

### R-004: Revisit Load-Bearing Architecture Decisions

Status: open

Problem:

Several architecture questions remain open after twelve slices: auth provider, queue technology, database choice, Analysis Store separation, S3 provider, upload/format limits, and deployment platform.

Recommended next action:

Run a dedicated architecture decision pass before persistence, queue integration, or production auth work starts.

### R-005: Correct Varroa Traceability Claims

Status: open

Problem:

Varroa detection is still the product goal, but delivered slices have intentionally focused on bee annotation and training-data foundations. Any docs that imply Varroa Annotation is operationalized should be adjusted to distinguish “modelled concept” from “implemented behaviour”.

Recommended next action:

Review `architecture/domain-model.md`, `requirements/model-requirements.md`, and related traceability sections before starting Varroa-specific slices.

## Verification

Initial remediation verification:

- Core API tests: `76 passed, 1 xfailed`
- Ruff: passed

Review Remediation 0001 verification:

- Core API tests: `83 passed, 1 xfailed`
- Analysis Service tests: `2 passed`
- Web TypeScript check: passed
- Playwright browser acceptance tests: `10 passed`
- `pnpm verify:slice`: passed
