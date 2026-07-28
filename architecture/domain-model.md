# Domain Model

## Purpose

This document defines the BeehiveMonitor domain model in technology-neutral terms. It should guide architecture, schema design, API design, acceptance tests, and traceability without choosing a framework, database, storage provider, or model implementation.

The canonical project vocabulary lives in `CONTEXT.md`. This document uses that vocabulary and adds relationships, lifecycle states, invariants, and unresolved architecture questions.

A visual version of the model is maintained in `architecture/domain-model-diagram.md`.

## Scope

Version one is a web-first inspection support system for hobbyist and small-scale beekeepers.

In scope:

- account-owned apiaries, hives, inspections, and inspection photos
- optional frame labels within an inspection
- AI-assisted analysis of inspection photos
- tagged photo review
- lightweight user corrections
- consent traceability for model improvement
- model version, dataset version, benchmark, and review concepts needed for model governance

Out of scope:

- multi-user collaboration
- advisor or organisation-level permissions
- native mobile apps
- full commercial apiary management
- full frame inventory management
- treatment recommendations
- official Varroa diagnosis or certification
- automatic use of user-submitted photos or corrections as training data

## Context Boundaries

BeehiveMonitor currently has one product context with two closely related subdomains:

- **Inspection Support**: apiaries, hives, inspections, photos, analysis output, and tagged review.
- **Model Governance**: annotations, corrections, consent, reviewed data, dataset roles, model versions, benchmark evaluations, and release approval.

These subdomains share inspection photos and annotations, but their responsibilities differ:

- Inspection Support helps the beekeeper understand an inspection.
- Model Governance controls whether evidence may influence model improvement or model release decisions.

## Core Entities

### Account

The version-one ownership boundary.

Essential fields:

- id
- display name
- status
- created at

Relationships:

- owns many apiaries
- owns all downstream hives, inspections, photos, analysis results, annotations, corrections, and consent records through that boundary

Notes:

- Version one does not model roles, memberships, teams, or advisors.
- Future collaboration should extend this boundary rather than bypass it.

### Apiary

A beekeeper-defined grouping or location containing hives.

Essential fields:

- id
- account id
- name
- optional location label
- optional notes
- status
- created at
- archived at

Relationships:

- belongs to one account
- contains many hives

### Hive

An individual managed hive record inside an apiary.

Essential fields:

- id
- apiary id
- name or code
- optional notes
- status
- created at
- archived at

Relationships:

- belongs to one apiary
- has many inspections

### Inspection

A dated review of one hive.

Essential fields:

- id
- account id
- hive id
- inspection date
- optional notes
- status
- created at
- updated at

Relationships:

- belongs to one hive
- contains many inspection photos
- may define many frame labels
- may have one current inspection summary

Canonical term:

- Use `Inspection`.
- Avoid `Inspection Event` in new architecture docs unless quoting older requirements.

### Frame Label

An optional label that groups photos believed to show the same frame during one inspection.

Essential fields:

- id
- inspection id
- label
- optional notes

Relationships:

- belongs to one inspection
- may be attached to many inspection photos

Rules:

- Frame labels are lightweight grouping hints, not frame inventory records.
- A frame label does not prove that photos are non-overlapping or safe to aggregate without caution.

### Inspection Photo

The original uploaded photo evidence for an inspection.

Essential fields:

- id
- account id
- inspection id
- optional frame label id
- original file reference
- original filename
- media type
- file size
- upload status
- image quality status
- uploaded at

Relationships:

- belongs to one inspection
- may reference one frame label
- may have many analysis results over time
- may have many annotations through analysis results
- may have many user corrections
- may have consent records

Rules:

- Accepted original photos are preserved.
- Tagged photos are rendered views, not replacements for the original.

### Analysis Result

Model output for one inspection photo.

Essential fields:

- id
- photo id
- model version id
- status
- complete visible bee count
- partial visible bee count
- uncertain bee count
- likely Varroa detections associated with complete bees
- likely Varroa detections associated with partial bees
- unassociated visible Varroa detections
- image quality status
- confidence or quality notes
- analysed at

Relationships:

- belongs to one inspection photo
- was produced by one model version
- has many bee annotations
- has many Varroa annotations
- may have many user corrections

Rules:

- Analysis results are not diagnoses.
- Analysis results are traceable to the model version that produced them.
- A newer analysis result may supersede an older one without deleting history.

### Inspection Summary

A derived roll-up across an inspection's analysis results.

Essential fields:

- id
- inspection id
- status
- complete visible bee total
- partial visible bee total
- headline Varroa numerator
- additional Varroa evidence count
- visible Varroa rate
- quality warning status
- generated at

Relationships:

- belongs to one inspection
- is derived from photo-level analysis results

Rules:

- The summary should be recalculable.
- Aggregation must account for optional frame labels and quality warnings.

### Bee Annotation

Structured marker data identifying a visible bee.

Essential fields:

- id
- analysis result id
- photo id
- source
- geometry
- visibility class
- confidence
- review status

Visibility classes:

- `complete_visible_bee`
- `partial_visible_bee`
- `uncertain_bee`

Sources:

- `model_suggested`
- `user_corrected`
- `reviewed`

### Varroa Annotation

Structured marker data identifying a likely visible Varroa mite.

Essential fields:

- id
- analysis result id
- photo id
- optional bee annotation id
- source
- geometry
- association state
- confidence
- review status

Association states:

- `associated_with_complete_bee`
- `associated_with_partial_bee`
- `unassociated_visible_varroa`

Rules:

- Only likely Varroa detections associated with complete visible bees contribute to the headline numerator.
- Partial or unassociated Varroa detections are additional evidence.

### User Correction

A beekeeper flag about model output.

Essential fields:

- id
- account id
- photo id
- optional analysis result id
- optional annotation id
- correction type
- optional geometry
- notes
- review status
- created at

Version-one correction types:

- `false_positive_varroa`
- `missed_likely_varroa`

Future correction types:

- `incorrect_bee_detection`
- `missed_bee`

Rules:

- A user correction is review evidence, not ground truth.
- A user correction is not training, validation, or benchmark data until consent and review decisions allow it.

### Review Decision

A human decision about a prediction, correction, annotation, dataset item, or model release.

Essential fields:

- id
- reviewer account id
- subject type
- subject id
- decision
- notes
- created at

Decision values:

- `approved`
- `rejected`
- `uncertain`
- `excluded`
- `training_approved`
- `evaluation_approved`

Rules:

- Review decisions must preserve what was reviewed and by whom.
- In version one, the reviewer may be the same person as the beekeeper/account owner.

### Consent Record

Evidence that a photo, inspection, or correction may or may not be considered for model improvement.

Essential fields:

- id
- account id
- subject type
- subject id
- status
- scope
- recorded at
- withdrawn at

Subject types:

- `inspection_photo`
- `inspection`
- `user_correction`

Statuses:

- `not_requested`
- `granted`
- `denied`
- `withdrawn`

Scopes:

- `analysis_only`
- `model_improvement_candidate`
- `training_candidate`
- `evaluation_candidate`

Rules:

- Consent is not assumed to be global.
- Consent is not assumed to be permanent.
- Evidence without consent must not enter model-improvement candidate workflows.

### Model Version

A named version of the model or model pipeline.

Essential fields:

- id
- name
- version label
- pipeline description
- release status
- created at
- approved at
- retired at

Release statuses:

- `draft`
- `benchmark_pending`
- `approved_for_user_facing_analysis`
- `retired`
- `rejected`

Relationships:

- produces many analysis results
- has many benchmark evaluations

### Dataset Version

A named version of reviewed data used for training, validation, benchmark evaluation, or exclusion.

Essential fields:

- id
- name
- version label
- dataset role
- source summary
- created at

Dataset roles:

- `training`
- `validation`
- `benchmark`
- `excluded`

Rules:

- Benchmark datasets must be protected from training and routine threshold tuning.

### Benchmark Evaluation

A documented evaluation of one model version against one protected benchmark dataset version.

Essential fields:

- id
- model version id
- dataset version id
- status
- bee detection metrics summary
- Varroa detection metrics summary
- quality-bucket metrics summary
- reviewer decision id
- evaluated at

Rules:

- A user-facing model version requires documented benchmark evaluation and human approval.
- Fixed numeric promotion thresholds are deferred until baseline data exists.

## Relationship Summary

- Account owns many apiaries.
- Apiary contains many hives.
- Hive has many inspections.
- Inspection contains many inspection photos.
- Inspection may define many frame labels.
- Frame label may group many inspection photos within one inspection.
- Inspection photo may have many analysis results.
- Analysis result belongs to exactly one model version.
- Analysis result has many bee annotations and Varroa annotations.
- Varroa annotation may reference one bee annotation.
- User correction belongs to one inspection photo and may reference one annotation.
- Consent record applies to one inspection, inspection photo, or user correction.
- Review decision applies to one review subject.
- Model version may have many benchmark evaluations.
- Benchmark evaluation uses one dataset version.

## Lifecycle States

### Inspection

- `draft`
- `photos_uploaded`
- `analysis_pending`
- `analysis_complete`
- `reviewed`
- `archived`

### Inspection Photo

- `uploaded`
- `rejected_format`
- `rejected_size`
- `analysis_pending`
- `analysis_complete`
- `analysis_failed`
- `excluded_from_summary`

### Analysis Result

- `queued`
- `processing`
- `complete`
- `failed`
- `superseded`

### Annotation Or Correction

- `model_suggested`
- `user_corrected`
- `review_pending`
- `review_approved`
- `training_approved`
- `evaluation_approved`
- `rejected`
- `excluded`

### Consent Record

- `not_requested`
- `granted`
- `denied`
- `withdrawn`

### Model Version

- `draft`
- `benchmark_pending`
- `approved_for_user_facing_analysis`
- `retired`
- `rejected`

## Invariants

- Every apiary belongs to exactly one account.
- Every hive belongs to exactly one apiary.
- Every inspection belongs to exactly one hive.
- Every inspection photo belongs to exactly one inspection.
- Every accepted inspection photo has a preserved original file reference.
- Every analysis result belongs to exactly one inspection photo.
- Every analysis result records the model version that produced it.
- Every annotation belongs to exactly one analysis result and one inspection photo.
- Every user correction belongs to exactly one inspection photo.
- A user correction is never ground truth without review.
- A user correction is never training, validation, or benchmark data without consent and review.
- Evidence without consent must not enter model-improvement candidate workflows.
- Benchmark data must not be used for training or routine threshold tuning.
- The visible Varroa rate must not be presented as diagnosis, treatment advice, official infestation rate, or whole-hive measurement.
- Tagged photos must be renderable from the original inspection photo plus annotation data.

## Derived Values

### Photo-Level Analysis Counts

Derived from annotations for one analysis result:

- complete visible bee count
- partial visible bee count
- uncertain bee count
- likely Varroa detections associated with complete bees
- likely Varroa detections associated with partial bees
- unassociated visible Varroa detections

### Inspection Summary

Derived from selected photo-level analysis results:

```text
visible_varroa_rate =
  likely_varroa_detections_associated_with_complete_bees
  / complete_visible_bees
  * 100
```

The display wording should communicate: likely mites per 100 complete visible bees in uploaded photos.

Partial visible bees, Varroa detections associated with partial bees, and unassociated visible Varroa detections are additional evidence.

## Ownership, Consent, And Privacy Boundaries

Version one uses account ownership as the access boundary.

The model must preserve:

- account ownership for apiaries, hives, inspections, photos, analysis results, annotations, corrections, and consent records
- traceable consent before model-improvement eligibility
- metadata minimisation before training, evaluation, sharing, or publication
- consent withdrawal for future training use

Deferred consent decision:

- consent may be captured at upload time, inspection level, account settings level, or model-review time

## Traceability

- `Account` supports FR-017.
- `Apiary` supports FR-001.
- `Hive` supports FR-002.
- `Inspection` supports FR-003.
- `Inspection Photo` supports FR-004 and FR-013.
- `Frame Label` supports FR-005.
- `Bee Annotation` and `Analysis Result` support FR-006 and MR-001.
- `Varroa Annotation` and `Analysis Result` support FR-007 and MR-002.
- `Inspection Summary` supports FR-008.
- `Tagged Photo` rendering supports FR-009, FR-010, and FR-011.
- `User Correction` and `Review Decision` support FR-012 and MR-013 to MR-014.
- `Consent Record` supports FR-016, FR-019, and MR-019 to MR-023.
- Upload status supports FR-018 and NFR-006.
- `Model Version` supports MR-028.
- `Dataset Version` supports MR-017 and MR-029.
- `Benchmark Evaluation` supports MR-030 and MR-031.

## Open Architecture Questions

- Should inspection summaries be stored snapshots, calculated on demand, or both?
- Should photo analysis run synchronously for a prototype or always as a background job?
- Where should original inspection photos be stored?
- What initial image formats and upload size limits should be configured?
- Where should consent be captured in the user workflow?
- How should consent withdrawal affect existing dataset versions?
- Should frame labels affect v1 aggregation, or only provide warning context?
- How should duplicate or near-duplicate inspection photos be detected?
- What is the first model integration style: local model, hosted model service, or manual/mock analysis?
- What annotation or review interface should be used for first ground-truth creation?
- Should review decisions happen in the beekeeper UI, a reviewer/admin UI, or external tooling?
- Should older photos be re-analysed by newer model versions, and how should superseded results be shown?
