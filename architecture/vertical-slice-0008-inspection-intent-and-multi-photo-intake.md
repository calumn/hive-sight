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
- An Inspection can contain multiple photos.
- Each uploaded photo remains independently addressable and reviewable.
- The UI makes the selected intent visible after creation.
- Dataset labelling affordances are available only for training-data collection inspections.
- Varroa assessment affordances are available only for Varroa assessment inspections.

## Out Of Scope

- Full frame inventory management.
- Enforcing a maximum of 22 photos.
- Oriented ellipse annotation UI.
- Model training.
- Varroa analysis quality changes.

## Test Notes

- Add API tests for valid and invalid Inspection intents.
- Add API tests for multiple photo intake on one Inspection.
- Add browser acceptance coverage for creating each intent and uploading multiple photos.
- Add BDD scenarios for intent separation and multi-photo inspection behaviour.
