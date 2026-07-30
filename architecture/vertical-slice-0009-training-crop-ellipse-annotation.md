# Vertical Slice 0009: Training Crop Ellipse Annotation

## Purpose

Allow a Dataset Curator to create a small Training Crop from a training-data collection Inspection Photo and review visible bees using oriented ellipses.

This slice proves the core annotation mechanic needed before HiveSight can build its own bee detector: human-reviewed, crop-level, oriented bee evidence.

## Source Inputs

- `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`
- `requirements/model-requirements.md`
- `architecture/domain-model.md`
- `architecture/adr/0002-oriented-ellipse-canonical-bee-annotations.md`
- `architecture/vertical-slice-0008-inspection-intent-and-multi-photo-intake.md`
- `architecture/vertical-slice-0012-hive-configuration-and-frame-standard-metadata.md`

## User Path

Given a Dataset Curator has access to a training-data collection Inspection Photo
When the Dataset Curator creates a Training Crop and marks visible bees with oriented ellipses
Then the crop stores reviewed bee annotation evidence
And the crop can be marked review complete or excluded
And the reviewed crop is not automatically assigned to training, validation, or benchmark data.

## Preconditions

- User is logged in.
- User has active Workspace Membership for the source Inspection Photo's Workspace.
- User has dataset curator capability.
- Workspace Data Use Agreement is accepted.
- Source Inspection has intent `training_data_collection`.
- Source Inspection Photo has been uploaded and is viewable.

## End-To-End Behaviour

The Dataset Curator opens a training-data collection photo, selects a rectangular crop region, and saves it as a Training Crop. The first crop-selection gesture is click/tap to create a fixed 640 x 640 pixel crop centred on the selected point, clamped to the source-image edges. If the source image is smaller, the crop uses the largest square that fits.

Before any ellipse exists, the Dataset Curator can adjust crop bounds using nudge controls and numeric width/height inputs. Crop bounds are locked after the first ellipse exists.

The Dataset Curator can create an oriented bee ellipse by clicking/tapping inside the crop. A default ellipse is created at that point with `radius_x = 40`, `radius_y = 20`, and `rotation_degrees = 0`. The curator can move, resize, rotate, and delete ellipses before crop completion. Each ellipse is classified as `complete_visible_bee` or `partial_visible_bee`.

When the crop has valid annotation geometry and a consistent visible bee status, the Dataset Curator can mark the crop `review_complete`. If the crop is unsuitable, the Dataset Curator can mark it `excluded` with a reason or note. Terminal crops are locked in this slice; there is no reopen workflow. A review-complete crop is eligible for later Bee Annotation Repository and Dataset Role assignment, but Slice 9 does not assign dataset use.

## Layers Touched

- Web UI: add a focused Training Crop and oriented ellipse annotation surface.
- Core API: add Training Crop creation/read/update and crop-level bee annotation endpoints.
- Analysis Service: not touched.
- Storage: in-memory dev store for Training Crops and crop annotations.
- Queue or async boundary: not touched.
- Contracts: Training Crop, oriented ellipse geometry, crop review status.
- Observability: standard API errors for intent mismatch, authorization failure, invalid geometry, and invalid crop bounds.

## Test Seams

- Seam: Core API
- Behaviour verified: Training Crop can be created only from a training-data collection Inspection Photo.
- Test style: API tests and API-level BDD.

- Seam: Core API
- Behaviour verified: oriented bee ellipse geometry is persisted, validated, updated, and deleted.
- Test style: API tests.

- Seam: Core API
- Behaviour verified: crop review completion requires valid crop and annotation state; excluded crop records unsuitable status.
- Test style: API tests and API-level BDD.

- Seam: Web UI
- Behaviour verified: Dataset Curator can create a crop, add at least one rotated ellipse, edit it, and mark the crop complete.
- Test style: Playwright browser acceptance.

## Data Shape

Minimum Training Crop fields:

- training crop id
- workspace id
- inspection photo id
- crop x
- crop y
- crop width
- crop height
- coordinate space
- source image width px
- source image height px
- crop image width px
- crop image height px
- curriculum stage
- review status
- visible bee status
- optional exclusion reason
- optional notes
- created by user id
- created at
- updated at

Initial curriculum stage:

- `small_crop`

Future curriculum stages remain documented but do not need full UI controls in this slice:

- `medium_crop`
- `large_crop`
- `full_frame_region`
- `full_frame_side`

Minimum oriented bee ellipse fields:

- annotation id
- workspace id
- inspection photo id
- training crop id
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

Initial crop review statuses:

- `review_pending`
- `review_complete`
- `excluded`

Initial visible bee statuses:

- `unassessed`
- `has_visible_bees`
- `no_visible_bees`

Initial exclusion reasons:

- `poor_image_quality`
- `no_visible_bees`
- `ambiguous_subject`
- `unsuitable_crop`
- `duplicate_or_near_duplicate`
- `other`

Geometry rules:

- Crop bounds and ellipse geometry are stored as source-image pixel coordinates.
- Browser UI may derive crop-relative coordinates for rendering.
- Ellipse rotation is degrees clockwise from the positive x-axis, normalized to `0 <= rotation_degrees < 360`.
- Ellipse movement uses 5 px nudge increments.
- Ellipse radius controls use 5 px increments.
- Ellipse rotation controls use 5 degree increments.
- Ellipses must stay inside the crop bounds.
- `partial_visible_bee` and `complete_visible_bee` ellipses may touch the crop edge.
- `visible_bee_status = has_visible_bees` requires at least one ellipse before `review_complete`.
- `visible_bee_status = no_visible_bees` cannot retain bee ellipses.
- A zero-bee reviewed crop is represented as `review_complete` plus `no_visible_bees`, not `excluded`.

## Hive And Frame Context Boundary

Training Crop provenance must preserve the path back to:

`Training Crop -> Inspection Photo -> Inspection -> Hive -> Apiary -> Workspace`

Hive Configuration and Frame Standard metadata are relevant model context, especially for bias analysis and future frame-size calibration. They are deliberately deferred to Slice 0012. Slice 9 must not depend on knowing the hive type, brood-box type, or frame dimensions.

## Out Of Scope

- Hive Configuration and Frame Standard implementation.
- Physical image calibration from pixels to millimetres.
- Automatic frame detection or frame boundary snapping.
- Automatic pre-labelling with the HiveSight Bee Detector.
- YOLO OBB export.
- Dataset Version creation.
- Dataset Role assignment.
- Benchmark evaluation.
- Varroa mite annotation.
- Segmentation masks.
- Full annotation workforce management.

## Acceptance Criteria

- [ ] A Training Crop can be created only from an existing Inspection Photo.
- [ ] The source Inspection must have intent `training_data_collection`.
- [ ] Workspace access, accepted Workspace Data Use Agreement, and dataset curator capability are enforced.
- [ ] A Training Crop records bounds in source-photo coordinates.
- [ ] A click/tap creates a 640 x 640 px crop centred on the selected point and clamped to source-image edges.
- [ ] Multiple Training Crops can be created from one Inspection Photo.
- [ ] Invalid crop bounds are rejected.
- [ ] The UI renders the Training Crop annotation surface from the original photo evidence.
- [ ] The UI lets the Dataset Curator choose any uploaded photo from the training-data collection Inspection.
- [ ] Crop bounds can be adjusted with nudge controls and numeric width/height inputs before annotation.
- [ ] Crop bounds are locked after the first ellipse exists.
- [ ] A Dataset Curator can create an oriented bee ellipse.
- [ ] A Dataset Curator can edit, rotate, and delete an oriented bee ellipse.
- [ ] An oriented bee ellipse records center, radii, rotation, coordinate space, and visibility class.
- [ ] Canonical crop and ellipse coordinates are source-image pixel coordinates.
- [ ] Invalid ellipse geometry is rejected.
- [ ] Ellipses cannot extend outside crop bounds.
- [ ] A crop cannot be marked `review_complete` while it has invalid ellipse geometry.
- [ ] A crop with `visible_bee_status = has_visible_bees` requires at least one ellipse before completion.
- [ ] A crop with `visible_bee_status = no_visible_bees` cannot retain bee ellipses.
- [ ] A zero-bee reviewed crop is allowed as `review_complete` plus `no_visible_bees`.
- [ ] A crop can be marked `excluded` without becoming dataset-eligible.
- [ ] `review_complete` and `excluded` crops are locked with no reopen workflow.
- [ ] A review-complete crop is eligible for later Dataset Role assignment but is not automatically training data.
- [ ] API-level BDD scenarios cover crop creation, ellipse review, and exclusion.
- [ ] Browser acceptance covers creating a crop and saving at least one rotated ellipse.

## Open Questions

- Should Slice 10 snapshot Training Crop evidence into a repository item, or reference the crop directly?
- What workflow should reopen or supersede a completed crop in a later slice?
- When should `uncertain_bee` become an implemented annotation type?
