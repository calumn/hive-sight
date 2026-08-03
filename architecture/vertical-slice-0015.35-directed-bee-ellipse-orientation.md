# Vertical Slice 0015.35: Directed Bee Ellipse Orientation

## Purpose

Make reviewed Oriented Bee Ellipses carry bee head/tail direction, not just body-axis alignment, so HiveSight preserves orientation evidence that may strengthen future Varroa detection and bee-relative mite-location modelling.

This slice proves that a Dataset Curator can see which end of an ellipse is the bee's head, flip a backwards ellipse, and have the directed rotation persist into Training Crop evidence and new Dataset Item snapshots.

Because the project is still in early local development and the existing annotated data is small, this slice also includes a one-time local cleanup: remove stale Dataset Items, Dataset Versions, Training Runs, Model Candidates, and derived local training/export artifacts, while preserving uploaded photos, Training Crops, and existing ellipses for manual head/tail re-review.

## Source Inputs

- `CONTEXT.md`: Oriented Bee Ellipse, Training Crop, Dataset Item, Candidate Annotation, HiveSight Bee Detector, Varroa Detector.
- `requirements/model-requirements.md`: MR-008 Bee Annotation Shape, MR-002 Varroa Detection, MR-018B Varroa Training Source Independence, MR-027 Separate Bee And Varroa Metrics.
- `architecture/domain-model.md`: Annotation, Training Crop, Dataset Item, Dataset Version, Model Candidate, Varroa Annotation.
- `architecture/adr/0002-oriented-ellipse-canonical-bee-annotations.md`: oriented ellipses remain canonical bee annotation geometry.
- `architecture/adr/0006-directed-bee-ellipse-orientation.md`: `rotation_degrees` is now directed center-to-head orientation.
- `architecture/vertical-slice-0009-training-crop-ellipse-annotation.md`: original Training Crop ellipse editor.
- `architecture/vertical-slice-0015.2-model-candidate-crop-pre-labelling.md`: model Candidate Annotations can create reviewed ellipses after human review.
- `architecture/vertical-slice-0015.3-dataset-repository-browser.md`: repository detail renders reviewed ellipse snapshots.
- `architecture/parking-lot.md#park-0028-automated-bee-head-direction-prediction`: future model capability for predicting bee head direction without human intervention.

## User Path

Given a Dataset Curator is reviewing a Training Crop with visible bees
When the curator creates or selects an Oriented Bee Ellipse
Then HiveSight shows which end of the ellipse is the bee's head
And the curator can rotate the ellipse until the head end points at the bee's head
And the curator can flip head/tail direction when the ellipse geometry is correct but backwards
And the saved ellipse and any new Dataset Item snapshot preserve that directed orientation.

Given existing local dataset/model evidence was created before directed ellipse semantics
When the Dataset Curator runs the one-time local cleanup
Then HiveSight removes stale dataset/model records and derived artifacts
And keeps uploaded photos, Training Crops, and ellipses available for re-review and fresh Dataset Role assignment.

## Preconditions

- The User has Dataset Curator internal capability.
- The Workspace Data Use Agreement is accepted.
- The selected Inspection has `Training Data Collection` intent.
- The selected Training Crop is editable, reopened, or not yet dataset-assigned.
- Existing Dataset Item immutability rules still apply.
- The local cleanup action is explicitly dev-only and must not be exposed as a production data-management workflow.

## End-To-End Behaviour

The Dataset Curator works in the existing Training Crop editor. Reviewed bee ellipses continue to use center, radii, and `rotation_degrees`, but the UI now renders the major axis as directional: head end and tail end are visually distinguishable.

The curator can use existing rotate controls to align the bee body and a new **Flip head/tail** control to add 180 degrees while preserving center and radii. The resulting `rotation_degrees` is normalized and saved through the existing ellipse update path.

When the crop is completed and assigned to a Dataset Role, the Dataset Item snapshots the reviewed ellipse with the directed rotation. Repository previews should render the head/tail distinction where reviewed ellipse snapshots are displayed, so the curator can visually audit old and new dataset evidence.

Existing Training Crop ellipses keep their stored `rotation_degrees`; no random mutation is performed. Their current angle is simply the starting point for manual review. The one-time local cleanup removes stale downstream dataset/model evidence so those crops can be reviewed again, completed, assigned to new Dataset Items, included in new Dataset Versions, and used for fresh Training Runs.

No persistent "head direction review needed" state is added. This is a one-user, one-time cleanup for the current seven-crop local dataset, not a product workflow.

YOLO OBB Candidate Annotations can still propose geometry, but their rotation is not trusted as biologically meaningful head direction. Human review decides the final directed orientation before an ellipse becomes reviewed evidence.

## Layers Touched

- Web UI: Update Training Crop ellipse overlays, selected ellipse controls, repository crop preview overlays, and user-facing guidance. Add **Flip head/tail** control using an arrow-style head indicator.
- Core API: Reuse existing ellipse create/update/read contracts where possible. Validate and normalize `rotation_degrees` as directed center-to-head orientation. Add or reuse a dev-only reset/cleanup command or endpoint for stale local dataset/model evidence if no suitable command already exists.
- Analysis Service: Not touched.
- Storage: No new ellipse field required if `rotation_degrees` is reused. Postgres persistence must continue to store and reload the directed value. Dev-only cleanup removes stale Dataset Items, Dataset Versions, Training Runs, Model Candidates, and derived dataset/model artifacts while preserving original image objects, Training Crops, and ellipses.
- Queue or async boundary: Not touched.
- Contracts: Clarify existing `rotation_degrees` contract semantics. Add no new API field unless implementation shows the UI cannot render direction cleanly from existing geometry.
- Observability: Existing request logging is enough; no sensitive image metadata should be logged.

## Test Seams

- Seam: Training Crop workflow rotation normalization
- Behaviour verified: flipping head/tail adds 180 degrees, normalizes the result, and leaves center/radii/type/provenance intact.
- Test style: Core API workflow/unit test.

- Seam: Dataset Item snapshot
- Behaviour verified: Dataset Item creation snapshots the directed `rotation_degrees` from reviewed ellipses and preserves it after reload.
- Test style: Core API test, with live Postgres verification when persistence is touched.

- Seam: Dev-only local cleanup
- Behaviour verified: cleanup removes stale Dataset Items, Dataset Versions, Training Runs, Model Candidates, and derived local artifacts while preserving Source Images, Inspection Photos, Training Crops, and existing ellipses.
- Test style: Core API or command-level regression test; live Postgres verification because local cleanup is persistence-affecting.

- Seam: Training Crop editor UI
- Behaviour verified: selected reviewed ellipse displays a visible head/tail direction and **Flip head/tail** changes the saved orientation.
- Test style: Playwright browser acceptance.

- Seam: Repository preview UI
- Behaviour verified: repository detail preview renders the reviewed ellipse with the same head/tail direction as the Training Crop evidence.
- Test style: Playwright browser acceptance or focused component-level DOM assertion through existing acceptance flow.

- Seam: Candidate Annotation acceptance
- Behaviour verified: accepting a model Candidate Annotation still requires human-reviewed directed orientation; if the proposed ellipse is backwards, the curator can flip it before completion.
- Test style: focused API/UI regression around model-assisted accepted ellipse provenance if the implementation touches that path.

## Data Shape

No new canonical annotation object is required.

Existing Oriented Bee Ellipse fields:

- `center_x`
- `center_y`
- `radius_x`
- `radius_y`
- `rotation_degrees`
- `annotation_type`
- provenance fields

New semantic contract:

- `rotation_degrees` is directed center-to-head orientation along the ellipse major axis.
- tail direction is `rotation_degrees + 180`.
- values should be normalized consistently, preferably into `0 <= rotation_degrees < 360`.
- **Flip head/tail** is product language; implementation may apply it as a 180-degree update to `rotation_degrees`.
- Existing stored rotations are not randomized or mass-mutated. They are the initial directed orientation until the curator reviews and corrects them.

Potential UI-only derived fields:

- `head_end_x`
- `head_end_y`
- `tail_end_x`
- `tail_end_y`

These should be derived for rendering rather than persisted unless a later slice introduces a different annotation geometry.

## Out Of Scope

- Separate head-point annotations.
- Automatic head detection by the Bee Detector.
- Automated head/tail prediction by any model pipeline.
- Varroa annotation, Varroa Detector training, or mite-location labels.
- Persistent legacy head-direction status, warning banners, or a cleanup dashboard.
- Dataset Item supersession for already-assigned evidence.
- Production deletion, consent withdrawal, or data-retention workflow.
- Changing YOLO OBB export format to encode head/tail direction.
- Model Candidate evaluation or promotion.
- Keyboard shortcut for **Flip head/tail**.

## Acceptance Criteria

- [x] `CONTEXT.md`, model requirements, domain model, and ADRs define Oriented Bee Ellipse rotation as directed center-to-head orientation.
- [x] Training Crop editor visually distinguishes ellipse head and tail ends.
- [x] Dataset Curator can flip a selected ellipse's head/tail direction without changing its center, radii, annotation type, or provenance.
- [x] Flipped ellipse rotation is persisted and survives reload.
- [x] One-time dev-only cleanup removes stale Dataset Items, Dataset Versions, Training Runs, Model Candidates, and derived local artifacts while keeping photos, Training Crops, and ellipses.
- [x] Preserved crops can be re-reviewed, completed, and assigned to fresh Dataset Items after cleanup.
- [x] New Dataset Item snapshots include the directed `rotation_degrees` value.
- [x] Bee Annotation Repository detail previews render reviewed ellipse snapshots with visible head/tail direction.
- [x] Existing model-assisted Candidate Annotation acceptance still produces reviewed ellipses with human-review provenance and directed orientation.
- [x] Existing YOLO OBB export and training remain geometrically compatible.
- [x] User guide explains how to orient the ellipse head end toward the bee's head.
- [x] Browser acceptance covers creating or selecting an ellipse and flipping head/tail; API and live Postgres tests cover persisted/reloaded direction.
- [x] `pnpm verify:slice` passes.
- [x] Live Postgres verification proves cleanup and preserved crop/ellipse review evidence behave correctly.

## Open Questions

- Should `rotation_degrees` normalization use `0..360` everywhere, or preserve existing values while interpreting them directionally?
- Should the cleanup command be a CLI-only command, a hidden dev endpoint, or both?

## Parked Follow-Up

- PARK-0028 records the future need for a model pipeline that can identify bees and their correct head/tail orientation without human intervention, so Varroa detection can consume consistently rotated bee crops.
