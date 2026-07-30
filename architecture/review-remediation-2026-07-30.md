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

Status: actioned as architecture decision by Slice 0013

Problem:

The Analysis Service is tested but not called by the Core API. Core API still runs in-process stub analysis, and the two services duplicate fixture-style analysis behaviour.

Recommended next action:

ADR 0004 accepts keeping the Analysis Service separate and integrating it through an async workflow shape. The first implementation should use an in-memory queue adapter and owned request/result contracts before choosing durable queue technology.

### R-003: Resolve UI-Level Gherkin Commitment

Status: actioned as delivery-standard decision by Slice 0013

Problem:

Several slice documents state that UI-level Gherkin should be introduced soon, but browser acceptance tests currently use Playwright specs directly.

Recommended next action:

Keep API-level acceptance in Gherkin/pytest-bdd. Keep UI acceptance in Playwright specs plus generated verification reports for now. UI-level Gherkin remains parked as a future option in `PARK-0001`.

### R-004: Revisit Load-Bearing Architecture Decisions

Status: partially actioned by Slice 0013

Problem:

Several architecture questions remain open after twelve slices: auth provider, queue technology, database choice, Analysis Store separation, S3 provider, upload/format limits, and deployment platform.

Recommended next action:

ADR 0003 accepts Postgres for durable product and model-governance metadata. Slice 0014 is the next persistence implementation slice. Object storage provider, durable queue technology, production auth provider, deployment platform, Analysis Store ownership, and production storage lifecycle remain parked with explicit triggers.

### R-005: Correct Varroa Traceability Claims

Status: actioned as traceability correction by Slice 0013

Problem:

Varroa detection is still the product goal, but delivered slices have intentionally focused on bee annotation and training-data foundations. Any docs that imply Varroa Annotation is operationalized should be adjusted to distinguish “modelled concept” from “implemented behaviour”.

Recommended next action:

Requirements and domain docs now distinguish the Varroa product/model goal from implemented bee-annotation and bee-detector training foundations. Varroa-specific functional/model slices should still be planned deliberately before implementation resumes in that area.

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

Slice 0013 verification:

- Core API tests: `83 passed, 1 xfailed`
- Analysis Service tests: `2 passed`
- Web TypeScript check: passed
- Playwright browser acceptance tests: `10 passed`
- `pnpm verify:slice`: passed
