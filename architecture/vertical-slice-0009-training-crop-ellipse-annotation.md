# Vertical Slice 0009: Training Crop Ellipse Annotation

## Purpose

Allow a Dataset Curator to create a small Training Crop from an Inspection Photo and review visible bees using oriented ellipses.

## Source Inputs

- `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`
- `requirements/model-requirements.md`
- `architecture/domain-model.md`
- `architecture/adr/0002-oriented-ellipse-canonical-bee-annotations.md`

## User Outcome

A Dataset Curator can select a training-data collection photo, create a crop, draw oriented bee ellipses over complete and partial visible bees, and mark the crop review complete or excluded.

## Thin Slice

- Add Training Crop records tied to an Inspection Photo.
- Persist crop bounds in source-photo coordinates.
- Persist reviewed bee annotations with oriented ellipse geometry.
- Support `complete_visible_bee` and `partial_visible_bee` labels.
- Support crop review statuses:
  - `review_pending`
  - `review_complete`
  - `excluded`
- Add a focused web UI for crop selection and ellipse annotation.

## Acceptance Criteria

- A Training Crop can be created only from an existing Inspection Photo.
- A Training Crop records its source-photo bounds and dimensions.
- A Dataset Curator can create, edit, rotate, and delete an oriented bee ellipse.
- An oriented bee ellipse records center, radii, rotation, coordinate space, and visibility class.
- A crop cannot be marked review complete while it has invalid ellipse geometry.
- A review-complete crop is eligible for later Dataset Role assignment but is not automatically training data.

## Out Of Scope

- Automatic pre-labelling with the HiveSight Bee Detector.
- YOLO OBB export.
- Dataset Version creation.
- Benchmark evaluation.
- Varroa mite annotation.

## Test Notes

- Add API tests for Training Crop creation and validation.
- Add API tests for oriented ellipse annotation persistence.
- Add browser acceptance coverage for drawing and editing at least one oriented ellipse.
- Add BDD scenarios for complete crop review and exclusion.
