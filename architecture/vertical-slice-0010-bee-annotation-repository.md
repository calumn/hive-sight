# Vertical Slice 0010: Bee Annotation Repository

## Status

Superseded by `architecture/vertical-slice-0010-bee-annotation-repository-and-dataset-export.md`.

This earlier draft intentionally kept YOLO OBB export out of scope. The implemented Slice 0010 combined Bee Annotation Repository assignment with logical YOLO OBB dataset export, and later slices depend on that broader scope. Keep this file only as a historical draft; do not use it for implementation planning.

## Purpose

Turn reviewed Training Crops and oriented bee ellipses into traceable Bee Annotation Repository evidence that can be assigned to dataset roles.

## Source Inputs

- `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`
- `requirements/ai-assisted-annotation-and-model-training-baseline.md`
- `requirements/model-requirements.md`
- `architecture/domain-model.md`

## User Outcome

A Dataset Curator can see reviewed crop-level bee evidence, assign it to training, validation, benchmark, or excluded roles, and create a traceable Dataset Item.

## Thin Slice

- Add Bee Annotation Repository listing for review-complete Training Crops.
- Add Dataset Item creation from a reviewed Training Crop.
- Record Dataset Role assignment separately from crop review completion.
- Preserve provenance from Dataset Item back to Training Crop, Inspection Photo, Inspection, Hive, Apiary, Workspace, reviewer, and source file.
- Support exclusion reasons for unsuitable reviewed crops.

## Acceptance Criteria

- Review-complete Training Crops appear as repository candidates.
- Excluded Training Crops do not appear as dataset-eligible candidates unless explicitly viewed.
- Assigning a Dataset Role creates a Dataset Item.
- Dataset Role assignment records actor and timestamp.
- Benchmark Dataset Items are clearly marked as protected.
- A reviewed crop without Dataset Role assignment is not training, validation, or benchmark data.

## Out Of Scope

- Dataset Version packaging.
- YOLO OBB export files.
- Model training.
- Automated leakage detection beyond recording provenance fields.

## Test Notes

- Add API tests proving review completion and Dataset Role assignment are separate.
- Add API tests for exclusion reasons.
- Add BDD scenarios for repository eligibility and protected benchmark assignment.
- Add browser acceptance coverage for assigning a reviewed crop to a role.
