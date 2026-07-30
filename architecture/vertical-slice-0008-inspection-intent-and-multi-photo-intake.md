# Vertical Slice 0008: Inspection Intent And Multi-Photo Intake

## Purpose

Make Inspection intent explicit and allow one Inspection to hold multiple photos. This separates dataset collection from beekeeper-facing Varroa assessment before the training and model workflows grow more complex.

## Source Inputs

- `requirements/product-spec.md`
- `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`
- `architecture/domain-model.md`
- `architecture/adr/0002-oriented-ellipse-canonical-bee-annotations.md`

## User Outcome

A Beekeeper can create an Inspection with either training data collection intent or Varroa assessment intent, upload multiple photos to that Inspection, and see those photos listed as separate evidence items.

## Thin Slice

- Add Inspection intent to the domain/API model.
- Support initial intent values:
  - `training_data_collection`
  - `varroa_assessment`
- Preserve current single-photo upload behaviour while allowing repeated uploads to the same Inspection.
- Show Inspection intent in the web UI.
- Route training-data collection inspections toward dataset labelling entry points.
- Route Varroa assessment inspections toward analysis/review entry points.

## Acceptance Criteria

- Creating an Inspection requires one valid intent.
- An Inspection cannot be created with mixed intents.
- The UI makes the intent choice explicit at Inspection creation time, with `varroa_assessment` selected by default.
- Inspection intent can be changed only while the Inspection has no photos.
- An Inspection can contain multiple photos.
- Multi-photo support may be repeated single-photo upload to the same Inspection; batch upload is deferred.
- Each uploaded photo remains independently addressable and reviewable.
- The first UI projection is a simple photo list/grid; frame and side grouping are deferred.
- The UI makes the selected intent visible after creation.
- Dataset labelling affordances are available only for training-data collection inspections.
- Training-data collection photos appear as dataset labelling candidates without a separate "send to labelling" step.
- Varroa assessment affordances are available only for Varroa assessment inspections.
- Unknown Inspection intent values are rejected by the API.
- Workspace Data Use Agreement acceptance is required for uploads under both intents.
- The photo list shows basic uploaded-photo evidence only: filename, upload status, size, and upload time.

## Locked Decisions

- Training-data inspections retain Hive, Apiary, Workspace, and source traceability.
- No persistence migration is needed in this slice because the current dev state is in-memory.
- Permanent Bee Annotation Repository storage is deferred. Slice 0008 must not decide durable model-training storage mechanics beyond keeping source Inspection Photo provenance intact.

## Out Of Scope

- Full frame inventory management.
- Enforcing a maximum of 22 photos.
- Batch photo upload.
- Permanent Bee Annotation Repository storage.
- Oriented ellipse annotation UI.
- Model training.
- Varroa analysis quality changes.

## Test Notes

- Add API tests for valid and invalid Inspection intents.
- Add API tests for multiple photo intake on one Inspection.
- Add browser acceptance coverage for creating each intent and uploading multiple photos.
- Add BDD scenarios for intent separation and multi-photo inspection behaviour.
