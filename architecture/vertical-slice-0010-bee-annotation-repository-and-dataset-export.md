# Vertical Slice 0010: Bee Annotation Repository And Dataset Export

## Purpose

Allow a Dataset Curator to turn a completed Training Crop into a Dataset Item in the Bee Annotation Repository and export assigned Dataset Items as a first YOLO OBB-compatible manifest.

This slice proves the bridge from human-reviewed crop evidence to model-training input while preserving the domain boundary: oriented bee ellipses remain the canonical reviewed evidence; YOLO OBB labels are a derived export format.

## Source Inputs

- `CONTEXT.md`
- `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`
- `requirements/model-requirements.md`
- `architecture/domain-model.md`
- `architecture/adr/0002-oriented-ellipse-canonical-bee-annotations.md`
- `architecture/vertical-slice-0006-dataset-role-assignment.md`
- `architecture/vertical-slice-0009-training-crop-ellipse-annotation.md`
- `architecture/vertical-slice-0009.5-ellipse-annotation-usability-controls.md`

## User Path

Given a Dataset Curator has a `review_complete` Training Crop with reviewed oriented bee ellipses
When the Dataset Curator assigns that crop to a Dataset Role
Then HiveSight creates a Dataset Item in the Bee Annotation Repository with provenance back to the original Inspection Photo
And the Dataset Curator can export eligible Dataset Items as a YOLO OBB manifest.

## Preconditions

- User is logged in.
- User has active Workspace Membership for the source Training Crop's Workspace.
- User has dataset curator capability.
- Workspace Data Use Agreement is accepted.
- Source Inspection has intent `training_data_collection`.
- Source Training Crop has not already been assigned to any Dataset Role in this slice.

## End-To-End Behaviour

The Dataset Curator opens a completed Training Crop and chooses a Dataset Role for it:

- `training`
- `validation`
- `benchmark`
- `excluded`

HiveSight creates a Dataset Item that belongs to the Bee Annotation Repository. `DatasetItem` is the concrete system record in this slice; Bee Annotation Repository is the conceptual collection of reviewed bee annotation evidence.

The Dataset Item snapshots the crop-level reviewed evidence needed for dataset governance:

- Training Crop identity and bounds
- source Inspection Photo identity
- source Workspace, Apiary, Hive, and Inspection path where available
- Curriculum Stage
- reviewed oriented bee ellipses
- Dataset Role
- assignment note
- optional exclusion reason
- assigning Dataset Curator
- assignment timestamp

The Dataset Item keeps a snapshot of canonical ellipse geometry in source-image pixel coordinates. It also references the source Training Crop. Snapshotting is required so future Training Crop correction, reopening, or supersession cannot silently change evidence that was previously approved for dataset use.

Assignment eligibility rules:

- `review_complete` plus `has_visible_bees` plus at least one ellipse can be assigned to `training`, `validation`, `benchmark`, or `excluded`.
- `review_complete` plus `no_visible_bees` can be assigned only to `excluded` in this slice.
- Training Crops already marked `excluded` can be assigned only to `excluded`.
- `review_pending` Training Crops cannot be assigned.
- A Training Crop may have only one Dataset Item in this slice, including `excluded`. Supersession is deferred.

The Dataset Curator can request a synchronous workspace-wide YOLO OBB manifest export for Dataset Items assigned to `training` and `validation`. The export contains:

- a manifest describing the export, source counts, class mapping, and caveats
- one image manifest entry per exported Training Crop
- one label entry per oriented bee ellipse projected to a YOLO OBB line
- train and validation manifest sections

Benchmark items are deliberately excluded from train/validation label output in this slice. The manifest reports benchmark item ids/counts as protected evidence. Excluded items are retained as governance evidence and reported with exclusion reasons, but are not exported for training.

The export is a model-specific projection. It must be traceable back to Dataset Item ids and source Training Crop ids. Slice 10 returns a manifest/API response only; physical cropped image files, text label files, and zip packaging are deferred.

## Layers Touched

- Web UI: add Dataset Role assignment and export summary controls to the Training Crop workflow.
- Core API: extend Dataset Item assignment for Training Crops and add a YOLO OBB manifest export endpoint.
- Analysis Service: not touched.
- Storage: in-memory dev store for Bee Annotation Repository items and export artifacts.
- Queue or async boundary: not touched; export is generated synchronously for the small dev dataset.
- Contracts: Dataset Item sourced from Training Crop, crop Dataset Role assignment, YOLO OBB export manifest.
- Observability: standard API errors for authorization failure, invalid crop state, duplicate assignment, benchmark leakage prevention, and export eligibility failures.

## Test Seams

- Seam: Core API
- Behaviour verified: only eligible completed Training Crops can become Dataset Items for the requested Dataset Role.
- Test style: API tests and API-level BDD.

- Seam: Core API
- Behaviour verified: Dataset Role assignment creates a Dataset Item with crop, photo, annotation snapshot, role, curator, and provenance fields.
- Test style: API tests.

- Seam: Core API
- Behaviour verified: duplicate Dataset Role assignment is blocked for the same Training Crop in this slice.
- Test style: API tests.

- Seam: Core API
- Behaviour verified: YOLO OBB manifest export projects oriented bee ellipses into crop-relative four-corner label rows and excludes benchmark/excluded items from train/validation output.
- Test style: API tests.

- Seam: Web UI
- Behaviour verified: Dataset Curator can assign one completed Training Crop to a selected Dataset Role and request a workspace-wide export summary.
- Test style: Playwright browser acceptance.

- Seam: Web TypeScript
- Behaviour verified: repository and export client contracts remain type-safe.
- Test style: `pnpm --filter @hive-sight/web check`.

## Data Shape

### Dataset Item

Minimum fields:

- dataset item id
- workspace id
- inspection photo id
- training crop id
- crop bounds in source-photo coordinates
- crop image width px
- crop image height px
- curriculum stage
- dataset role
- reviewed ellipse ids
- reviewed ellipse snapshot
- source group key or duplicate group key, optional
- provenance summary
- permission status
- assignment note, optional
- exclusion reason, optional
- assigned by user id
- assigned at
- benchmark protected flag

Initial Dataset Roles:

- `training`
- `validation`
- `benchmark`
- `excluded`

Initial permission status:

- `workspace_data_use_agreement_accepted`

Initial provenance summary must preserve traceability to:

`Dataset Item -> Training Crop -> Inspection Photo -> Inspection -> Hive -> Apiary -> Workspace`

If some upstream display fields are unavailable in the current dev store, the item must still preserve the known ids.

### Reviewed Ellipse Snapshot

Minimum fields:

- annotation id
- annotation type
- center x
- center y
- radius x
- radius y
- rotation degrees
- coordinate space
- source image width px
- source image height px
- source
- created by user id
- created at
- updated at

Supported annotation types:

- `complete_visible_bee`
- `partial_visible_bee`

### YOLO OBB Export

Minimum export fields:

- export id
- workspace id
- export format
- created by user id
- created at
- class map
- included dataset item ids
- excluded dataset item ids with reasons
- protected benchmark dataset item ids
- training item count
- validation item count
- benchmark item count, reported but not exported for training
- image entries
- label entries
- caveat

Initial export format:

- `yolo_obb`

Initial class map:

- `0`: `complete_visible_bee`
- `1`: `partial_visible_bee`

Slice 10 returns this export as a manifest/API response. It does not create physical files or a zip archive.

### YOLO OBB Projection Rule

For each reviewed oriented bee ellipse:

- canonical source: ellipse center, radii, and rotation
- projected model shape: oriented bounding box enclosing the ellipse
- OBB width: `2 * radius_x`
- OBB height: `2 * radius_y`
- OBB rotation: ellipse rotation
- class id: from initial class map
- label convention: `class x1 y1 x2 y2 x3 y3 x4 y4`
- coordinates: four rotated rectangle corner points normalized against the crop image width and height
- coordinate origin: the top-left of the Training Crop, not the original source photo

The Dataset Item snapshot stores source-image pixel geometry for traceability. The export converts source-image pixel geometry to crop-relative pixels, then normalizes by crop width and crop height.

## Out Of Scope

- Real persistent database storage.
- Physical cropped image file generation.
- Production zip packaging and long-running export jobs.
- Dataset Version creation.
- Training Run execution.
- Model Candidate creation.
- Benchmark Evaluation execution.
- Duplicate or near-duplicate image detection.
- Automatic split balancing.
- Hive Configuration and Frame Standard implementation.
- Reopening or superseding completed Training Crops.
- Varroa mite annotation export.
- Segmentation masks.
- User-submitted photo consent withdrawal workflow.

## Acceptance Criteria

- [x] A Dataset Curator can create a Dataset Item from a `review_complete` Training Crop.
- [x] Dataset Item creation requires dataset curator capability.
- [x] Dataset Item creation requires accepted Workspace Data Use Agreement.
- [x] Dataset Item creation requires the source Inspection intent to be `training_data_collection`.
- [x] Dataset Item creation is blocked for `review_pending` Training Crops.
- [x] A Training Crop marked `excluded` can create only an `excluded` Dataset Item.
- [x] A `review_complete` Training Crop with `no_visible_bees` can create only an `excluded` Dataset Item.
- [x] A `review_complete` Training Crop with `has_visible_bees` and at least one ellipse can create a Dataset Item with role `training`, `validation`, `benchmark`, or `excluded`.
- [x] Dataset Item creation records Dataset Role.
- [x] Dataset Item creation records assignment note and optional exclusion reason.
- [x] Dataset Item creation snapshots reviewed oriented bee ellipses.
- [x] Dataset Item creation preserves source Training Crop and Inspection Photo ids.
- [x] Dataset Item provenance is traceable back to Workspace and Hive path where available.
- [x] Duplicate Dataset Role assignment for the same Training Crop is blocked in this slice.
- [x] Benchmark Dataset Items are marked benchmark protected.
- [x] YOLO OBB manifest export is synchronous and workspace-wide.
- [x] YOLO OBB manifest export includes training and validation Dataset Items.
- [x] YOLO OBB manifest export excludes benchmark Dataset Items from train/validation label output.
- [x] YOLO OBB manifest export reports protected benchmark Dataset Item ids/counts.
- [x] YOLO OBB manifest export excludes `excluded` Dataset Items from train/validation label output.
- [x] YOLO OBB manifest export reports excluded Dataset Item ids/reasons.
- [x] YOLO OBB export includes a class map for complete and partial visible bees.
- [x] YOLO OBB export uses `class x1 y1 x2 y2 x3 y3 x4 y4`.
- [x] YOLO OBB export normalizes corner points against the crop image.
- [x] YOLO OBB export includes traceability back to Dataset Item ids and Training Crop ids.
- [x] YOLO OBB export identifies itself as a derived projection, not canonical annotation evidence.
- [x] API-level BDD scenarios cover repository assignment and export leakage prevention.
- [x] Browser acceptance covers assigning one completed Training Crop through UI and viewing a workspace-wide export summary.
- [x] `pnpm verify:slice` passes.

## Open Questions

- Should `no_visible_bees` crops become negative/background training samples in a later slice?
- What supersession workflow should replace or correct a Dataset Item after assignment?
- Should physical cropped image and label files be generated in Slice 11 or as Slice 10.5?
