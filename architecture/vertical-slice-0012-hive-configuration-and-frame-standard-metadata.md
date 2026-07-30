# Vertical Slice 0012: Hive Configuration And Frame Standard Metadata

## Purpose

Capture the equipment context for a Hive so inspection photos and training data can be traced against likely frame dimensions and hive standards.

This supports later model-quality analysis: if reviewed training data mostly comes from one hive type, frame size, brood-box setup, or beekeeper equipment pattern, HiveSight should be able to see that bias rather than discover it accidentally.

## Source Inputs

- `CONTEXT.md`
- `architecture/domain-model.md`
- `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`
- `architecture/vertical-slice-0009-training-crop-ellipse-annotation.md`
- `architecture/vertical-slice-0010-bee-annotation-repository.md`

## User Path

Given a Beekeeper has created a Hive
When the Beekeeper records the Hive Configuration
Then the Hive stores the hive type, box/use, and expected Frame Standard
And future Inspection Photos and Training Crops retain traceability back to that equipment context.

## Preconditions

- User is logged in.
- User has active Workspace Membership for the Hive's Workspace.
- Apiary and Hive already exist.

## End-To-End Behaviour

The Beekeeper selects or records a Hive Configuration for a Hive. The system stores the selected hive type and box/use, links to a known Frame Standard where possible, and exposes that context alongside inspection and training-data provenance.

The first implementation may allow `unknown` or `other` values so the user is not blocked when their equipment is not in the initial list.

## Layers Touched

- Web UI: add a small Hive Configuration section near Hive setup or Hive detail.
- Core API: add create/update/read Hive Configuration endpoints.
- Analysis Service: not touched.
- Storage: in-memory store for the current dev implementation; durable persistence remains governed by the broader persistence decision.
- Queue or async boundary: not touched.
- Contracts: Hive Configuration and Frame Standard response/request models.
- Observability: standard API errors for invalid workspace access and unknown Frame Standard references.

## Test Seams

- Seam: Core API
- Behaviour verified: Hive Configuration can be recorded only for a Hive in the User's Workspace.
- Test style: API tests.

- Seam: Core API
- Behaviour verified: known Frame Standard metadata is returned with the Hive Configuration.
- Test style: API tests.

- Seam: Web UI
- Behaviour verified: Beekeeper can select a common hive/frame setup and see it preserved.
- Test style: browser acceptance test.

## Data Shape

Minimum Hive Configuration fields:

- hive configuration id
- hive id
- hive type
- box/use
- optional frame standard id
- status
- effective from
- created at

Minimum Frame Standard fields:

- frame standard id
- display name
- hive type
- frame use
- top bar length
- bottom bar length
- side bar height
- measurement unit
- source or notes

Initial frame standards should include a small UK/US-oriented starter set, with exact values verified before implementation:

- British National / WBC shallow super
- British National / WBC deep brood
- British National / WBC extra deep 14x12
- Smith shallow super
- Smith deep brood
- British Commercial shallow super
- British Commercial deep brood
- Langstroth shallow super
- Langstroth deep brood

## Out Of Scope

- Physical image calibration from pixels to millimetres.
- Automatic frame detection.
- Full commercial apiary inventory management.
- Frame-by-frame inventory records.
- Recalculating existing model metrics by Hive Configuration.
- Making Hive Configuration mandatory before photo upload.
- Using frame dimensions directly inside the model pipeline.

## Acceptance Criteria

- [ ] A Hive can have a Hive Configuration.
- [ ] Hive Configuration records hive type and box/use.
- [ ] Hive Configuration can reference a known Frame Standard.
- [ ] `unknown` or `other` equipment context is supported.
- [ ] Workspace access is enforced.
- [ ] Inspection Photo and Training Crop provenance can be traced back to the Hive and its equipment context.
- [ ] The UI shows the selected Hive Configuration.
- [ ] Tests cover API contract and visible UI behaviour.

## Open Questions

- Which hive/frame standards should be included in the first maintained catalogue?
- Should Hive Configuration be editable over time with history, or simply replace the current value in version one?
- Should an Inspection snapshot the Hive Configuration at the time of inspection?
- Should box/use live on the Hive, the Inspection, or the individual photo when a hive contains mixed equipment?
- What source should be used to verify initial frame dimensions before shipping a maintained catalogue?
