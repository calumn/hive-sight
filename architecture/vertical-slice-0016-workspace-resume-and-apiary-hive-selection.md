# Vertical Slice 0016: Workspace Resume And Apiary/Hive Selection

Status: planned after Slice 0015 YOLO OBB Training Baseline.

## Purpose

Make the HiveSight web UI usable for repeated training-data collection now that product metadata can persist.

When a User opens HiveSight, the UI should resume the current Workspace context, show existing Apiaries and Hives, select sensible defaults, and let the Dataset Curator continue creating Training Crops without recreating Apiary and Hive records every session.

This slice also removes a confusing product cue from the normal YOLO training-data workflow: `Start Dataset Labelling` should no longer appear as the primary path when the Inspection Intent is Training Data Collection. The intended current path for YOLO training data is Training Crops, Oriented Bee Ellipses, Dataset Role assignment, Dataset Version creation, and Bee Detector training.

## Source Inputs

- `CONTEXT.md`: Workspace, User, Apiary, Hive, Hive Configuration, Inspection Intent, Training Data Collection, Dataset Curator, Training Crop, Oriented Bee Ellipse, Dataset Role, Dataset Version, Training Run, HiveSight Bee Detector, YOLO OBB.
- `architecture/adr/0001-service-oriented-architecture.md`: Core API owns Workspace authorization and beekeeper-facing product workflow.
- `architecture/adr/0003-postgres-for-durable-product-and-model-governance-metadata.md`: Postgres is the first durable metadata store for Core API product data and model-governance metadata.
- `architecture/vertical-slice-0012-hive-configuration-and-frame-standard-metadata.md`: Hive Configuration is mandatory before creating an Inspection.
- `architecture/vertical-slice-0014-postgres-backed-bee-annotation-repository-persistence.md`: durable metadata path exists.
- `architecture/vertical-slice-0015-yolo-obb-training-baseline.md`: reviewed Training Crops feed Dataset Versions and YOLO OBB Bee Detector training.
- User feedback after Slice 0015: repeated Apiary/Hive creation is now friction, and the old Dataset Labelling panel is confusing during Training Data Collection.

## User Path

Given a User opens HiveSight as the dev-authenticated User
And the User has an active owner Workspace Membership
And the Workspace may already contain Apiaries, Hives, and Hive Configurations
When the web UI loads the Workspace
Then HiveSight lists existing Apiaries and selects the first Apiary by default
And HiveSight lists Hives for the selected Apiary and selects the first Hive by default
And HiveSight loads the selected Hive's current Hive Configuration when one exists
And creating a new Apiary or Hive selects the newly created record
And the User can continue creating Training Data Collection Inspections without recreating existing records.

Given the User creates or selects a Training Data Collection Inspection
When the training-data UI is shown
Then the primary annotation path is Training Crops and Oriented Bee Ellipses
And the legacy Dataset Labelling panel is hidden from the normal training-data collection flow.

## Preconditions

- Dev authentication continues to use `x-hivesight-dev-user-id`.
- The current development User and Workspace continue to be created or resolved by `/v1/dev/session`.
- Workspace Data Use Agreement acceptance remains required before upload, dataset curation, and model-training workflows.
- Hive Configuration remains mandatory before creating an Inspection for a Hive.
- Postgres-backed metadata should preserve Apiaries, Hives, and Hive Configurations across server restarts when the stack is run with `HIVESIGHT_PERSISTENCE_BACKEND=postgres`.
- The UI remains a one-page working surface for this slice. Full routing/navigation is deferred.
- Basic Workspace structure can be loaded before Workspace Data Use Agreement acceptance. Upload, dataset curation, analysis, and model-training actions remain gated by the Workspace Data Use Agreement.
- `pnpm dev:all` remains the fast in-memory default. This slice must also be verified against the Postgres-backed path, but it does not make Postgres the default for all local development.
- Slice 0016 implementation and live QA should start from a deliberately clean local development Postgres database by running `pnpm db:reset:dev`. This is an explicit implementation/QA action, not automatic app startup behaviour.

## End-To-End Behaviour

On load, the Web UI fetches the dev session and Workspace state. It then loads the Apiaries available in the current Workspace before requiring Workspace Data Use Agreement acceptance.

The Core API exposes separate list endpoints for this slice:

- `GET /v1/apiaries?workspace_id=...`
- `GET /v1/apiaries/{apiary_id}/hives?workspace_id=...`

Authorized empty lists return `200 []`. Unauthorized Workspace access returns `403` using the existing Workspace authorization error shape. A missing Apiary returns `404 apiary_not_found`. An Apiary in another Workspace returns `403`.

If the Workspace has no Apiaries, the UI shows an empty setup-needed state and keeps the create Apiary form available.

If the Workspace has one or more Apiaries, the UI selects the first Apiary by default. The selected Apiary is shown as a compact context summary. If more than one Apiary exists, the UI shows a compact selectable Apiary list. The create Apiary form remains available behind an `Add apiary` action.

Default selection uses stable ordering: creation order oldest first when available, otherwise `name`, then id. Creating a new Apiary selects the newly created Apiary immediately, even if it would not be first under the normal default rule.

When the selected Apiary changes, the UI loads Hives for that Apiary.

If the selected Apiary has no Hives, the UI shows an empty Hive state and keeps the create Hive form available.

If the selected Apiary has one or more Hives, the UI selects the first Hive by default using the same stable-ordering rule and attempts to load the current Hive Configuration. Hives are shown as a selectable list, with the selected Hive highlighted. If a Hive Configuration exists, the UI displays it and allows Inspection creation. If no Hive Configuration exists, the UI treats that as a normal setup-needed state, shows Hive Configuration controls behind `Add hive` or the empty-Hive setup state, and keeps Inspection creation disabled until configuration is recorded. A missing Hive Configuration is not shown as a red error banner.

Creating an Apiary selects the newly created Apiary and aggressively clears any selected Hive, Inspection, selected file, photos, analysis result/evidence, labelling evidence, Training Crop panel state, Dataset Versions, and Training Runs that belonged to the previous selection.

Creating a Hive selects the newly created Hive, records its Hive Configuration from the selected Frame Standard and notes, and clears any selected Inspection and downstream evidence from the previous Hive selection. This slice keeps the current combined create-Hive-and-record-Hive-Configuration flow. Existing Hive Configurations are displayed but not made editable as a first-class edit flow in this slice.

The existing create forms stay on the same page for now, but are secondary controls rather than always-visible setup panels. They should no longer imply that Apiary and Hive creation are mandatory every time the app starts.

The top of the one-page UI should be modestly reorganized into a clearer context-picker surface:

- Workspace gate/status
- selected Apiary summary, optional Apiary list, and add Apiary action
- Hive list, Hive Configuration display/setup, and add Hive action
- Inspection creation controls
- upload, Training Crops, Dataset Version, and Training Run controls

The context rows should show Apiary and Hive names. UUID fragments may remain as secondary debug/status text where useful, but they should not dominate the working UI.

Inspection creation remains explicit. Selecting a Hive does not automatically create an Inspection. The UI default Inspection Intent changes to `training_data_collection` for current development and dataset-building work, while keeping both Intent options visible. The API continues to require explicit intent.

For Training Data Collection Inspections, the visible annotation path focuses on:

- Training Crops
- Oriented Bee Ellipses
- Training Crop review completion
- Dataset Role assignment
- Dataset Version creation
- Bee Detector baseline training

The older Dataset Labelling Session UI remains in code, API history, and existing tests, but is hidden from the normal path for creating YOLO OBB training data. It is hidden, not removed. It may be reintroduced later as a modern Candidate Annotation Review workflow if it is updated to the current domain language and model direction.

## Layers Touched

- Web UI: Add compact Apiary context, Hive list/select controls once records exist, auto-select defaults, load Hive Configuration for selected Hive, reset downstream state when selection changes, keep create forms as secondary add actions, default Inspection Intent to Training Data Collection, and hide legacy Dataset Labelling panel from the normal Training Data Collection workflow.
- Core API: Add separate read endpoints for Workspace Apiaries and Apiary Hives. Reuse the existing current Hive Configuration endpoint.
- Analysis Service: Not touched.
- Storage: Reuse existing Apiary, Hive, and Hive Configuration records in the in-memory and Postgres-backed stores. No new table is expected unless implementation reveals a missing projection.
- Queue or async boundary: Not touched.
- Contracts: Add list response shapes for Apiary list and Hive list. Do not introduce a Workspace resume projection in this slice.
- Observability: Keep existing request logging. Add no new observability requirement unless a new Workspace resume endpoint is introduced.

## Test Seams

- Seam: Core API Workspace read side
- Behaviour verified: a User can list only Apiaries in their Workspace and only Hives under a selected Apiary.
- Test style: Core API request tests using in-memory store; Postgres restart-survival coverage if new persistence read methods are added.

- Seam: Hive Configuration read for selected Hive
- Behaviour verified: selected Hive loads current Hive Configuration when it exists; Inspection creation remains blocked when it does not.
- Test style: Core API request/workflow tests plus browser acceptance.

- Seam: Web Workspace resume state
- Behaviour verified: when existing Apiaries and Hives are present, the UI selects defaults and allows Inspection creation without recreating them.
- Test style: Playwright browser acceptance using persisted or pre-created records.

- Seam: Training Data Collection UI path
- Behaviour verified: Training Crop annotation is the visible primary dataset-building workflow, and the legacy Dataset Labelling panel is hidden from the normal path.
- Test style: Playwright browser acceptance.

- Seam: Postgres-backed restart path
- Behaviour verified: after `pnpm db:reset:dev`, the User can create Apiary, Hive, and Hive Configuration records, restart or reload against Postgres-backed metadata, and see those records listed and selected.
- Test style: live Postgres verification during closeout.

## Data Shape

Minimum read-side data needed by the UI:

- Apiary: `apiary_id`, `workspace_id`, `name`.
- Hive: `hive_id`, `apiary_id`, `workspace_id`, `name`.
- Hive Configuration: existing Slice 0012 shape, including selected Frame Standard details.
- Apiary list response: `apiaries: Apiary[]`.
- Hive list response: `hives: Hive[]`.

Selection state is UI state, not a persisted user preference in this slice. The default selection rule is deterministic: first Apiary by stable ordering, then first Hive by stable ordering. Stable ordering should be creation order if available, otherwise name then id.

## Out Of Scope

- Full multi-page application navigation.
- Persisted per-user "last selected Apiary/Hive" preference.
- Search, filtering, archive/delete, rename, or edit flows for Apiaries and Hives.
- Multiple Workspace selection.
- Real authentication or production role switching.
- Inspection history listing or resume of an existing Inspection.
- Automatically creating an Inspection when a Hive is selected.
- Public dataset import.
- Candidate Annotation review redesign.
- Replacing the legacy Dataset Labelling backend.
- Model Candidate promotion or evaluation.
- Editing existing Hive Configuration.
- Dev User or role selector.
- Unsaved-local-edit warning before changing Apiary or Hive.

## Acceptance Criteria

- [ ] On app load, the UI fetches and displays existing Apiaries for the current Workspace.
- [ ] If one or more Apiaries exist, the UI selects a default Apiary without requiring the User to create another one.
- [ ] Creating a new Apiary selects the newly created Apiary.
- [ ] Selecting an Apiary loads Hives belonging to that Apiary.
- [ ] If one or more Hives exist for the selected Apiary, the UI selects a default Hive without requiring the User to create another one.
- [ ] Creating a new Hive selects the newly created Hive.
- [ ] The UI loads and displays current Hive Configuration for the selected Hive when it exists.
- [ ] Inspection creation remains disabled or blocked until selected Hive Configuration exists.
- [ ] Changing Apiary or Hive clears downstream Inspection/photo/annotation/model-training state that no longer belongs to the selection.
- [ ] For Training Data Collection, the visible primary workflow is Training Crops and Oriented Bee Ellipses.
- [ ] The legacy Dataset Labelling panel is not shown in the normal Training Data Collection path.
- [ ] Browser acceptance proves a User can reload/open the app and continue from existing Apiary/Hive records.
- [ ] Browser acceptance proves creating an additional Apiary or Hive selects the new record.
- [ ] UI labels make Apiary/Hive creation feel like setup/add actions rather than the main workflow once records exist.
- [ ] The UI default Inspection Intent is Training Data Collection, while both Intent options remain visible.
- [ ] Basic Apiary/Hive list loading works before Workspace Data Use Agreement acceptance.
- [ ] Core API tests prove Workspace authorization on Apiary/Hive list endpoints or resume projection.
- [ ] `pnpm verify:slice` passes.
- [ ] Live Postgres verification starts from `pnpm db:reset:dev`, creates Apiary/Hive/Hive Configuration records, restarts or reloads, and proves those records are listed and selected.
- [ ] Final implementation summary reminds the User to run `pnpm db:reset:dev` before their own clean-field manual testing.

## Open Questions

- None. Scope decisions were resolved during grilling.
