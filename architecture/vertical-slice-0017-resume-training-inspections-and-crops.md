# Vertical Slice 0017: Resume Training Inspections And Crops

Status: scope locked after grilling.

## Purpose

Make crop-level bee annotation safe to pause and resume across sessions.

When a Dataset Curator opens HiveSight with the Postgres-backed stack, selects an existing Hive, and has previous Training Data Collection work, the UI should list resumable training-data Inspections for that Hive, let the curator reopen one, reload its uploaded photos, and reload saved Training Crops and Oriented Bee Ellipses so annotation can continue without recreating records.

This slice protects the practical workflow of spending hours circling bees: once a crop or ellipse has been saved, the user should be able to come back tomorrow and continue from that saved state through the UI.

## Source Inputs

- `CONTEXT.md`: Workspace, User, Apiary, Hive, Hive Configuration, Inspection, Inspection Intent, Training Data Collection, Inspection Photo, Training Crop, Oriented Bee Ellipse, Dataset Curator.
- `architecture/vertical-slice-0008-inspection-intent-and-multi-photo-intake.md`: Inspections have explicit intent and can contain multiple photos.
- `architecture/vertical-slice-0009-training-crop-ellipse-annotation.md`: Training Crops and Oriented Bee Ellipses are saved as source-image pixel coordinates.
- `architecture/vertical-slice-0014-postgres-backed-bee-annotation-repository-persistence.md`: Postgres-backed Core API metadata persistence exists.
- `architecture/vertical-slice-0016-workspace-resume-and-apiary-hive-selection.md`: Workspace, Apiary, Hive, and Hive Configuration resume now exists; Inspection resume was deliberately parked.
- `architecture/parking-lot.md#park-0017-inspection-list-and-resume-for-selected-hive`: promoted into this slice.
- User feedback after trying crop annotation: crop annotation may take multiple sessions, so saved work must be discoverable and resumable before significant manual annotation effort.

## User Path

Given a Dataset Curator has opened HiveSight with the Postgres-backed stack
And the selected Hive has one or more Training Data Collection Inspections
And at least one Inspection has uploaded photos, saved Training Crops, and saved Oriented Bee Ellipses
When the Dataset Curator selects or reloads that Hive
Then HiveSight lists existing Training Data Collection Inspections for the Hive
And the Dataset Curator can select an Inspection to resume
And HiveSight reloads that Inspection's photos
And selecting a photo reloads its saved Training Crops
And selecting a crop reloads its saved Oriented Bee Ellipses and review state.

## Preconditions

- Dev authentication continues to use `x-hivesight-dev-user-id`.
- User has an active Workspace Membership for the selected Hive's Workspace.
- User has Dataset Curator capability to work in the Training Crop UI.
- Workspace Data Use Agreement remains required before upload and dataset-curation actions. Listing existing setup and Inspections may load before acceptance, but editing/creating annotation evidence remains gated by existing workflow rules.
- Hive Configuration remains mandatory before creating a new Inspection.
- Postgres-backed persistence is required for the full resume promise across process restarts. The in-memory dev stack may still resume only within the same running process.
- This slice assumes saved Training Crops and Oriented Bee Ellipses are already durable through Slice 0014's Postgres-backed repository path.

## End-To-End Behaviour

When the UI has a selected Hive, it loads existing Inspections for that Hive.

The Core API exposes a narrow Inspection read endpoint:

- `GET /v1/hives/{hive_id}/inspections?workspace_id=...&intent=training_data_collection`

The endpoint returns Inspections belonging to the selected Hive and Workspace. It enforces Workspace access. A missing Hive returns `404 hive_not_found`. A Hive in another Workspace returns `403 workspace_access_denied`. The response is ordered newest Inspection first by `inspection_date`, then id as a deterministic fallback. This slice does not attempt to infer "most recently active annotation work" from crop, ellipse, dataset, or upload timestamps.

The UI shows a `Resume Training Inspection` selector near the existing Inspection creation controls. The selector shows only Training Data Collection Inspections in this slice. If Training Data Collection Inspections exist, the newest Inspection is auto-selected by default and the selection is visible and changeable. The User does not need an extra resume button. The current create Inspection form stays in place below the resume selector.

Selecting an Inspection:

- sets the active Inspection in the UI;
- reloads the Inspection's photos through the existing `GET /v1/inspections/{inspection_id}/photos` path;
- clears current selected file, analysis evidence, labelling evidence, model-training panel state, and any crop editor state that belongs to the previously selected Inspection;
- keeps Apiary, Hive, and Hive Configuration selection unchanged.
- scrolls the page down to the Training Crop panel after photos have loaded and the crop panel is available.

For a resumed Training Data Collection Inspection, the Training Crop panel renders whenever the active Inspection has intent `training_data_collection` and has photos, even when no upload was just accepted in the current browser session. The crop panel is no longer coupled only to the upload success state.

If the selected Inspection has uploaded photos, the existing Training Crop panel uses those photos. Its existing photo selector chooses the first uploaded photo deterministically by default and lets the User switch photos. A photo with no crops is a normal ready-to-crop state, not a warning. Selecting a photo loads saved Training Crops through the existing `GET /v1/inspection-photos/{inspection_photo_id}/training-crops` path. All saved crops are shown, including `review_complete` and `excluded` crops, with status visible. Selecting a saved crop reloads Training Crop evidence through the existing crop evidence endpoint, including Oriented Bee Ellipses and review status. If the saved crop has ellipses, the UI auto-selects the most recently saved ellipse so the geometry controls immediately show persisted annotation data.

Creating a new Training Data Collection Inspection remains explicit. When the User creates a new Inspection, the UI selects the newly created Inspection, refreshes the Training Inspection list, and clears the old Inspection's photo, crop, ellipse, evidence, and model-training state.

Varroa Assessment Inspections are not part of the resume selector in this slice. They can still be created and used through the existing explicit path, but the primary resume workflow is for Training Data Collection because that is where long-running crop annotation lives.

Saved-work boundaries must be clear in implementation and closeout:

- `Save crop` persists a Training Crop.
- Clicking inside a saved crop persists a new Oriented Bee Ellipse.
- Nudge, resize, rotate, type change, and delete actions persist immediately.
- Complete or exclude persists immediately.
- A draft crop overlay is not durable until `Save crop`.

This slice supports same-process resume in the in-memory dev stack, but the across-session/restart promise applies only to the Postgres-backed stack. Real annotation work should use `pnpm dev:all:yolo-training`. The final implementation summary must remind the User of that command.

The UI should make saved state legible:

- Inspection selector label includes date and intent.
- Photo list shows uploaded photos for the selected Inspection.
- Training Crop list shows saved crop count and per-crop status.
- Selected crop shows saved ellipse count and geometry.
- Locked completed/excluded crops remain locked as today.

The slice does not need full routes/pages. It can remain on the current one-page working surface.

## Layers Touched

- Web UI: Add `Resume Training Inspection` list/select controls for the selected Hive; auto-select newest Training Data Collection Inspection; reload photos and Training Crop panel state when the selected Inspection changes; select newly created Inspections; render the Training Crop panel for resumed Training Data Collection Inspections with photos; auto-scroll to the crop panel after resume.
- Core API: Add a read endpoint for Inspections by Hive and optional intent.
- Analysis Service: Not touched.
- Storage: Reuse existing Inspection records in in-memory and Postgres-backed stores. No new table is expected.
- Queue or async boundary: Not touched.
- Contracts: Add an Inspection list response shape. Reuse existing Inspection and Inspection Photo shapes.
- Observability: Keep existing request logging and domain error shape.

## Test Seams

- Seam: Core API Hive Inspection read side
- Behaviour verified: a User can list only Inspections for a Hive in their Workspace; filtering to `training_data_collection` excludes Varroa Assessment Inspections.
- Test style: Core API request tests using in-memory store.

- Seam: Web Inspection resume state
- Behaviour verified: existing Training Data Collection Inspection is shown and can be selected without creating a new Inspection.
- Test style: Playwright browser acceptance.

- Seam: Web crop resume state
- Behaviour verified: after reload/reopen, the selected Inspection's photos, saved Training Crops, and saved Oriented Bee Ellipses reappear.
- Test style: Playwright browser acceptance using the Postgres-backed or same-process persisted test server path, plus live Postgres verification for restart-survival.

- Seam: Postgres-backed restart path
- Behaviour verified: create Training Data Collection Inspection, upload photo, save crop and ellipse, stop/restart or reload against Postgres, then select the Inspection and continue editing.
- Test style: live Postgres verification during closeout.

## Data Shape

Minimum new response:

- Inspection list response: `inspections: Inspection[]`.

Existing reused shapes:

- Inspection: `inspection_id`, `hive_id`, `workspace_id`, `inspection_date`, `intent`.
- Inspection Photo list: existing `InspectionPhotoListResponse`.
- Training Crop list: existing `TrainingCropListResponse`.
- Training Crop evidence: existing `TrainingCropEvidenceResponse`.

No persisted "last selected Inspection" user preference is added in this slice. Selection is derived deterministically from the current Hive's Training Data Collection Inspection list.

## Out Of Scope

- Full app routing or a dedicated Inspection history page.
- Persisted per-user last selected Inspection preference.
- Resume by most recently updated annotation activity.
- Editing Inspection date or intent.
- Deleting, archiving, or renaming Inspections.
- Listing/resuming Varroa Assessment Inspections as a first-class history workflow.
- Reopening completed or excluded Training Crops.
- Unsaved local draft warning.
- Visible "last saved" timestamps for crops or ellipses.
- Inspection-level annotation complete workflow.
- Saved-work recovered toast/status.
- Bulk crop/ellipse operations.
- Multi-user concurrency or record locking.
- Full offline save/resume behaviour.
- Training-run resume or model-candidate management.
- Candidate Annotation Review redesign.

## Acceptance Criteria

- [ ] Core API exposes `GET /v1/hives/{hive_id}/inspections?workspace_id=...&intent=training_data_collection`.
- [ ] The Inspection list endpoint enforces Workspace access.
- [ ] Missing Hive returns `404 hive_not_found`.
- [ ] Hive in another Workspace returns `403 workspace_access_denied`.
- [ ] The endpoint can filter by `training_data_collection` and excludes Varroa Assessment Inspections from that filtered response.
- [ ] UI loads Training Data Collection Inspections when a Hive is selected.
- [ ] UI shows an empty resume state when the selected Hive has no Training Data Collection Inspections.
- [ ] UI selects the newest existing Training Data Collection Inspection by default when one exists.
- [ ] Creating a new Training Data Collection Inspection selects the newly created Inspection and refreshes the list.
- [ ] Selecting a different Inspection reloads its photo list.
- [ ] Selecting or auto-selecting a resumed Inspection scrolls to the Training Crop panel after photos load.
- [ ] A resumed Training Data Collection Inspection with photos renders the Training Crop panel without requiring a new upload in the current browser session.
- [ ] The first uploaded photo is selected deterministically by default, and the User can choose another photo.
- [ ] A photo with no saved crops is shown as a normal ready-to-crop state.
- [ ] Selecting a photo reloads all saved Training Crops for that photo, including completed and excluded crops.
- [ ] Selecting a saved Training Crop reloads saved Oriented Bee Ellipses.
- [ ] If a resumed crop has ellipses, the UI auto-selects the most recently saved ellipse.
- [ ] After browser reload against a running server, the UI can resume a previously saved crop and ellipse without recreating Apiary, Hive, Inspection, photo, or crop records.
- [ ] Live Postgres verification proves the same resume path after process restart or stack restart.
- [ ] Existing crop edit controls still save each ellipse change immediately.
- [ ] Slice docs and final closeout clearly state that saved crop/ellipse changes persist immediately, but unsaved draft crop overlays do not persist until `Save crop`.
- [ ] Final implementation summary reminds the User that real annotation work should use `pnpm dev:all:yolo-training`.
- [ ] Existing completed/excluded crop lock behaviour remains unchanged.
- [ ] Browser acceptance covers creating a crop and ellipse, reloading/reopening, and continuing from the saved crop.
- [ ] `pnpm verify:slice` passes.

## Open Questions

- None. Scope decisions were resolved during grilling.
