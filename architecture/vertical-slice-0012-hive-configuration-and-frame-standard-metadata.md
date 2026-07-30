# Vertical Slice 0012: Hive Configuration And Frame Standard Metadata

## Purpose

Capture the equipment context for a Hive so inspection photos, Training Crops, Dataset Items, and physical dataset exports can be traced against likely hive and frame dimensions.

This slice gives HiveSight the first explicit source-context signal for model bias analysis. If reviewed bee training data mostly comes from one hive type, frame standard, brood-box setup, or equipment pattern, HiveSight should be able to see that before training and evaluation claims become misleading.

## Source Inputs

- `CONTEXT.md`
- `architecture/domain-model.md`
- `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`
- `requirements/model-requirements.md`
- `architecture/vertical-slice-0008-inspection-intent-and-multi-photo-intake.md`
- `architecture/vertical-slice-0009-training-crop-ellipse-annotation.md`
- `architecture/vertical-slice-0010-bee-annotation-repository-and-dataset-export.md`
- `architecture/vertical-slice-0011-physical-dataset-export-package.md`
- `architecture/vertical-slice-0013-yolo-obb-training-baseline.md`

## User Path

Given a Beekeeper has created a Hive
When the Beekeeper records the Hive Configuration
Then HiveSight stores the hive type, frame use, and selected Frame Standard for that Hive
And HiveSight allows Inspections to be created for that Hive
And Dataset Curators can see that equipment context in training-data provenance.

## Preconditions

- User is logged in.
- User has active Workspace Membership for the Hive's Workspace.
- Apiary and Hive already exist.
- Workspace Data Use Agreement is not required merely to record Hive Configuration.
- Workspace Data Use Agreement is still required for photo upload, dataset curation, and dataset export workflows.
- A Hive must have Hive Configuration before any Inspection can be created for it.

## End-To-End Behaviour

The Beekeeper creates a Hive with its required current Hive Configuration in the UI. The Core API keeps Hive creation and Hive Configuration upsert as separate operations, but Inspection creation is blocked until the Hive has a current Hive Configuration.

Hive Configuration records:

- hive type
- frame use
- selected Frame Standard
- optional free-text notes, required for `other`
- status
- effective-from date
- actor and timestamp

The first implementation treats Hive Configuration as the current equipment context for the Hive. Updating the configuration replaces the current value rather than creating a full history. Historical equipment configuration and inspection-time snapshots are deferred, but the model keeps enough shape to add them later.

The UI uses the term Hive Configuration end to end. Known Frame Standard selection is authoritative: selecting a known Frame Standard determines hive type and frame use, with no manual override in this slice. The Beekeeper can choose `unknown` or `other` when their equipment is not listed. `unknown` does not require notes. `other` requires notes.

When a known Frame Standard is selected, the UI shows read-only frame dimensions in millimetres. Unknown and other configurations show no dimensions.

Hive Configuration is mandatory, but `unknown` remains a valid explicit configuration. Later Dataset Version or Training Run reports must count and flag unknown Hive Configuration, but Slice 12 does not block dataset export or training preparation solely because equipment context is `unknown`.

The Core API exposes the known Frame Standard catalogue and supports create/update/read of the current Hive Configuration for a Hive. Hive Configuration is workspace-owned through the Hive -> Apiary -> Workspace path.

Dataset Item provenance snapshots the current Hive Configuration at Dataset Item creation time. Physical dataset export manifests use the Dataset Item provenance snapshot rather than looking up live Hive Configuration. This prevents a later Hive Configuration correction from silently rewriting already-curated dataset evidence.

Inspection creation requires current Hive Configuration but does not snapshot it in Slice 12. Inspection-time configuration snapshots are a future persistence/history concern.

Frame dimensions are traceability metadata only in this slice. The model pipeline does not use frame dimensions for calibration, scaling, crop generation, thresholding, or training decisions yet.

## Starter Frame Standard Catalogue

Slice 12 includes a small maintained starter catalogue. These are metadata values for traceability and bias analysis, not a complete equipment inventory.

Initial entries:

- `british_national_shallow_super`
- `british_national_deep_brood`
- `british_national_extra_deep_14x12`
- `wbc_shallow_super`
- `wbc_deep_brood`
- `wbc_extra_deep_14x12`
- `smith_shallow_super`
- `smith_deep_brood`
- `british_commercial_shallow_super`
- `british_commercial_deep_brood`
- `langstroth_shallow_super`
- `langstroth_deep_brood`
- `unknown`
- `other`

Known starter dimensions are recorded in millimetres with source notes:

| Frame Standard | Hive Type | Frame Use | Top Bar Length | Bottom Bar Length | Side Bar Height |
| --- | --- | --- | ---: | ---: | ---: |
| British National shallow super | `british_national` | `shallow_super` | 432 | 356 | 140 |
| British National deep brood | `british_national` | `deep_brood` | 432 | 356 | 216 |
| British National extra deep 14x12 | `british_national` | `extra_deep_14x12` | 432 | 356 | 305 |
| WBC shallow super | `wbc` | `shallow_super` | 432 | 356 | 140 |
| WBC deep brood | `wbc` | `deep_brood` | 432 | 356 | 216 |
| WBC extra deep 14x12 | `wbc` | `extra_deep_14x12` | 432 | 356 | 305 |
| Smith shallow super | `smith` | `shallow_super` | 394 | 356 | 140 |
| Smith deep brood | `smith` | `deep_brood` | 394 | 356 | 216 |
| British Commercial shallow super | `british_commercial` | `shallow_super` | 432 | 406 | 152 |
| British Commercial deep brood | `british_commercial` | `deep_brood` | 432 | 406 | 254 |
| Langstroth shallow super | `langstroth` | `shallow_super` | 483 | 447 | 137 |
| Langstroth deep brood | `langstroth` | `deep_brood` | 483 | 447 | 232 |

The catalogue source note should explicitly say the initial dimensions are project-maintained starter metadata for dev traceability and must be independently verified before production claims or physical calibration.

## Locked Decisions

- Slice 12 records one current Hive Configuration per Hive.
- Hive Configuration is mandatory before creating any Inspection, for both `training_data_collection` and `varroa_assessment` intents.
- No migration/grandfathering rule is needed because there is no persistence before Slice 12.
- UI captures Hive name and Hive Configuration together; Core API keeps Hive creation and Hive Configuration upsert as separate operations.
- Updating Hive Configuration replaces the current value in this slice.
- Full configuration history is deferred.
- Inspection-time configuration snapshots are deferred.
- Hive Configuration uses the term Hive Configuration end to end in docs, UI, API, tests, and acceptance language.
- `unknown` and `other` are valid Frame Standard choices.
- `other` requires notes. `unknown` does not require notes.
- Known Frame Standard selection determines hive type and frame use in Slice 12, with no manual override.
- The UI shows read-only dimensions for known Frame Standards.
- `unknown` is allowed in Slice 12, but later Dataset Version or Training Run reports must count and flag unknown equipment context.
- Frame use belongs to the Hive Configuration in this slice, not directly to every Inspection Photo.
- Mixed equipment within one Hive is not modelled in this slice.
- Frame dimensions are metadata only. They are not used for pixel-to-mm calibration.
- British National and WBC are separate hive types, even where starter dimensions overlap.
- Dataset Item provenance snapshots current Hive Configuration at Dataset Item creation time.
- Physical dataset export manifests include Hive Configuration metadata from Dataset Item provenance snapshots.
- Physical export API responses remain summary-only; detailed Hive Configuration metadata lives in the Dataset Item provenance and `manifest.json`.
- Training Run and Model Candidate behaviour remains out of scope until Slice 13.

## Layers Touched

- Web UI: capture Hive Configuration during Hive setup and show the current Hive Configuration near Hive context.
- Core API: add Frame Standard catalogue read endpoint, current Hive Configuration create/update/read endpoint, and Inspection creation guard.
- Analysis Service: not touched.
- Storage: in-memory dev store for Frame Standards and current Hive Configurations.
- Queue or async boundary: not touched.
- Contracts: Frame Standard response, Hive Configuration request/response, Inspection creation guard error, provenance/export metadata extension.
- Observability: standard API errors for workspace access failure, missing Hive Configuration, unknown Hive, invalid Frame Standard id, `other` without notes, and invalid enum values.

## Test Seams

- Seam: Core API
- Behaviour verified: User can list starter Frame Standards.
- Test style: API tests.

- Seam: Core API
- Behaviour verified: User can record and retrieve current Hive Configuration for a Hive in their Workspace.
- Test style: API tests and API-level BDD.

- Seam: Core API
- Behaviour verified: Inspection creation is blocked until the Hive has current Hive Configuration.
- Test style: API tests and API-level BDD.

- Seam: Core API
- Behaviour verified: Workspace access is enforced through Hive -> Apiary -> Workspace.
- Test style: API tests.

- Seam: Core API
- Behaviour verified: Dataset Item provenance snapshots Hive Configuration metadata at Dataset Item creation and physical export manifest includes that snapshot.
- Test style: API tests.

- Seam: Web UI
- Behaviour verified: Beekeeper can select a common Hive Configuration, see dimensions, and create an Inspection only after configuration exists.
- Test style: Playwright browser acceptance.

- Seam: Web TypeScript
- Behaviour verified: Frame Standard and Hive Configuration client contracts remain type-safe.
- Test style: `pnpm --filter @hive-sight/web check`.

## Data Shape

### Frame Standard

Minimum fields:

- frame standard id
- display name
- hive type
- frame use
- top bar length mm, optional
- bottom bar length mm, optional
- side bar height mm, optional
- measurement unit: `mm`
- source note
- status: `known`, `unknown`, or `other`

Initial hive type values:

- `british_national`
- `wbc`
- `smith`
- `british_commercial`
- `langstroth`
- `unknown`
- `other`

Initial frame use values:

- `shallow_super`
- `deep_brood`
- `extra_deep_14x12`
- `unknown`
- `other`

### Hive Configuration

Minimum fields:

- hive configuration id
- hive id
- workspace id
- hive type
- frame use
- frame standard id, optional
- frame standard, optional expanded response
- notes, optional
- status: `current`
- effective from
- configured by user id
- configured at
- updated at

### Provenance Extension

Dataset Item provenance and physical export manifest metadata should include a snapshot of:

- hive configuration id
- hive type
- frame use
- frame standard id
- frame standard display name
- frame dimensions in millimetres, when known

This metadata is required for Dataset Items created from new Slice 12 data because Inspection creation is blocked until Hive Configuration exists.

## Out Of Scope

- Real persistent database storage.
- Full Hive Configuration history.
- Inspection-time Hive Configuration snapshots.
- Mixed equipment within one Hive or one Inspection.
- Frame-by-frame inventory.
- Frame-side numbering or side A/B tracking.
- Pixel-to-millimetre calibration.
- Automatic frame detection in images.
- Using frame dimensions directly inside the model pipeline.
- Training Run execution.
- Model Candidate creation.
- Benchmark Evaluation execution.
- Production verification of all global hive/frame standards.
- Blocking dataset export or training preparation solely because Hive Configuration is `unknown`.

## Acceptance Criteria

- [x] A User can list starter Frame Standards.
- [x] Starter Frame Standards include the UK/US-oriented entries listed in this slice.
- [x] A Beekeeper can create or update the current Hive Configuration for a Hive.
- [x] Hive Configuration is mandatory before creating any Inspection.
- [x] Hive creation UI captures Hive name and Hive Configuration together.
- [x] Hive Configuration records hive type and frame use.
- [x] Known Frame Standard selection determines hive type and frame use without manual override.
- [x] Hive Configuration can reference a known Frame Standard.
- [x] Hive Configuration supports `unknown` and `other`.
- [x] `other` Frame Standard requires notes.
- [x] `unknown` Frame Standard does not require notes.
- [x] UI shows read-only dimensions for known Frame Standards.
- [x] Workspace access is enforced through Hive -> Apiary -> Workspace.
- [x] Hive Configuration can be retrieved for the current Hive.
- [x] Updating Hive Configuration replaces the current value in this slice.
- [x] Dataset Item provenance snapshots current Hive Configuration metadata at Dataset Item creation.
- [x] Physical dataset export manifest includes Hive Configuration metadata from Dataset Item provenance.
- [x] UI shows the selected Hive Configuration.
- [x] API-level BDD covers mandatory Hive Configuration before Inspection creation.
- [x] API-level BDD covers Hive Configuration snapshot in Dataset Item provenance/export metadata.
- [x] Browser acceptance covers selecting Hive Configuration and confirms Inspection creation is unavailable or blocked until configuration exists.
- [x] `pnpm verify:slice` passes.

Verification report: `reports/slice-verification/latest.md`

## Open Questions

- None. Scope is locked for implementation.
