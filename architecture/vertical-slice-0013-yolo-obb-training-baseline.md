# Vertical Slice 0013: YOLO OBB Training Baseline

## Purpose

Create the first repeatable HiveSight Bee Detector training baseline using reviewed crop-level oriented bee ellipses exported to YOLO OBB labels.

This slice should follow physical dataset packaging and hive/frame metadata work so the first training run has a real local dataset package and enough source context to interpret early model behaviour.

## Source Inputs

- `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`
- `requirements/model-requirements.md`
- `architecture/adr/0002-oriented-ellipse-canonical-bee-annotations.md`
- `architecture/domain-model.md`
- `architecture/vertical-slice-0011-physical-dataset-export-package.md`
- `architecture/vertical-slice-0012-hive-configuration-and-frame-standard-metadata.md`

## User Outcome

A Dataset Curator or model reviewer can export reviewed bee evidence into a YOLO OBB training dataset, run a small baseline training job, and record the resulting Model Candidate and Training Run.

## Thin Slice

- Use a physical YOLO OBB dataset export package as training input.
- Run a first YOLO OBB nano or small training job when enough local reviewed data exists.
- Record Training Run metadata.
- Record Model Candidate metadata.
- Produce a baseline report that states data volume, model family, training settings, and basic validation metrics.

## Acceptance Criteria

- Exported labels are derived from reviewed oriented bee ellipses.
- The training run records which physical export package was used.
- Benchmark Dataset Items are excluded from training input.
- A Training Run records model family, training settings, source data, start/end time, status, and outcome.
- A Model Candidate is created separately from any approved user-facing Model Version.
- The baseline report does not claim production suitability.

## Out Of Scope

- Varroa mite detection.
- Automatic model promotion.
- Protected benchmark evaluation for release.
- Cloud training infrastructure.
- Production model serving.

## Test Notes

- Add tests proving the training adapter consumes the physical export package shape.
- Add tests proving benchmark items are excluded from training input.
- Add tests for Training Run and Model Candidate records.
- Add a verification report section for model export/training artifacts.
