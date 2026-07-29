# Domain Model

## Purpose

This document defines the HiveSight domain model in technology-neutral terms. It should guide architecture, schema design, API design, acceptance tests, and traceability without choosing a framework, database, storage provider, or model implementation.

The canonical project vocabulary lives in `CONTEXT.md`. This document uses that vocabulary and adds relationships, lifecycle states, invariants, and unresolved architecture questions.

A visual version of the model is maintained in `architecture/domain-model-diagram.md`.

## Scope

Version one is a web-first inspection support system for hobbyist and small-scale beekeepers.

In scope:

- workspace-owned apiaries, hives, inspections, and inspection photos
- registered user with a default workspace and owner workspace membership
- beekeeper as the primary product persona in version one
- optional frame labels within an inspection
- AI-assisted analysis of inspection photos
- tagged photo review
- lightweight user corrections
- workspace-level data-use agreement for upload, analysis, and model-improvement terms
- explicit privacy/deletion gap capture
- model version, dataset version, benchmark, and review concepts needed for model governance

Out of scope:

- multi-user collaboration
- workspace invitations
- advisor or organisation-level permissions
- native mobile apps
- full commercial apiary management
- full frame inventory management
- treatment recommendations
- official Varroa diagnosis or certification
- automatic use of user-submitted photos or corrections as training data without accepted workspace data-use terms and review

## Context Boundaries

HiveSight currently has one product context with two closely related subdomains:

- **Inspection Support**: apiaries, hives, inspections, photos, analysis output, and tagged review.
- **Model Governance**: annotations, corrections, workspace data-use agreements, deletion requests, reviewed data, dataset roles, model versions, benchmark evaluations, and release approval.

These subdomains share inspection photos and annotations, but their responsibilities differ:

- Inspection Support helps the beekeeper understand an inspection.
- Model Governance controls whether evidence may influence model improvement or model release decisions.

## Core Entities

### Workspace

The version-one ownership boundary.

Essential fields:

- id
- display name
- status
- created at

Relationships:

- has many workspace memberships
- owns many apiaries
- owns all downstream hives, inspections, photos, analysis results, annotations, corrections, workspace data-use agreements, and deletion requests through that boundary

Notes:

- Version one creates one default workspace during user registration.
- Version one supports one active/default workspace in the UI.
- Future collaboration should use workspace memberships rather than bypassing the workspace boundary.

### User

A registered login identity.

Essential fields:

- id
- display name
- contact identifier
- status
- registered at

Relationships:

- has many workspace memberships over time
- acts in a workspace through one workspace membership
- may create inspections, upload inspection photos, review tagged photos, and create user corrections when authorized through a workspace membership

Rules:

- User is the identity/authentication concept.
- User is not the ownership boundary for apiaries, hives, inspections, photos, or analysis results.
- Version one registration creates a default workspace and an owner workspace membership for the user.

### Workspace Membership

The relationship that grants a user access to a workspace.

Essential fields:

- id
- user id
- workspace id
- role
- status
- created at

Version-one roles:

- `owner`

Future roles:

- `member`
- `inspector`
- `advisor`
- `reviewer`

Relationships:

- belongs to one user
- belongs to one workspace

Rules:

- Version one only supports `owner`.
- Version one creates one owner membership for the registered user and default workspace.
- Future multi-user collaboration, invitations, and workspace switching should extend this concept.

### Beekeeper

The product persona for a person doing beekeeping work.

Notes:

- Beekeeper is not a persisted entity in version one.
- In version one, the registered user with the owner workspace membership acts as the primary beekeeper.
- Use Beekeeper in requirements, scenarios, and UI language when describing beekeeping work.
- Use User when describing registration, authentication, login identity, or authorization.
- A workspace may later have multiple users acting as beekeepers, advisors, reviewers, or admins.
- Beekeeper is an actor/persona, not the ownership container.

### Apiary

A beekeeper-defined grouping or location containing hives.

Essential fields:

- id
- workspace id
- name
- optional location label
- optional notes
- status
- created at
- archived at

Relationships:

- belongs to one workspace
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
- workspace id
- hive id
- optional created by user id
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
- workspace id
- inspection id
- optional frame label id
- original file reference
- original filename
- media type
- file size
- upload status
- image quality status
- uploaded at
- uploaded by user id

Relationships:

- belongs to one inspection
- may reference one frame label
- may have many analysis results over time
- may have many annotations through analysis results
- may have many user corrections
- inherits data-use eligibility from the workspace data-use agreement

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
- workspace id
- created by user id
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
- A user correction is not training, validation, or benchmark data until the Workspace Data Use Agreement and review decisions allow it.

### Review Decision

A human decision about a prediction, correction, annotation, dataset item, or model release.

Essential fields:

- id
- reviewer id
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
- In version one, the reviewer may be the same person as the beekeeper/workspace owner.

### Workspace Data Use Agreement

A workspace-level acceptance of the service's data-use terms.

Essential fields:

- id
- workspace id
- status
- terms version
- accepted at
- withdrawn at
- accepted by user id
- withdrawn by user id

Statuses:

- `not_accepted`
- `accepted`
- `withdrawn`

Rules:

- Version one requires the workspace owner to accept the agreement before upload and analysis features can be used.
- If the agreement is withdrawn or not accepted, new upload and analysis are disabled.
- Existing inspection history may remain viewable unless a deletion process applies.
- Withdrawal stops future model-improvement use from the point of withdrawal, subject to the data-use terms.
- The treatment of previously uploaded photos, existing dataset versions, and already-trained model artifacts is an explicit policy/legal gap.

### Data Deletion Request

A request to delete or purge workspace-held data.

Essential fields:

- id
- workspace id
- requester id
- status
- requested at
- completed at
- notes

Statuses:

- `requested`
- `in_review`
- `completed`
- `rejected`
- `partially_completed`

Rules:

- The operational workflow is deferred.
- Uploaded photos and metadata should be treated as potentially personally identifiable or sensitive.
- The project must decide how deletion interacts with existing dataset versions and already-trained model artifacts before production use.

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

- Workspace owns many apiaries.
- User has many workspace memberships.
- Workspace has many workspace memberships.
- Workspace membership belongs to one user and one workspace.
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
- Workspace data-use agreement belongs to one workspace and is accepted by an owner user in version one.
- Data deletion request belongs to one workspace.
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

### Workspace Data Use Agreement

- `not_accepted`
- `accepted`
- `withdrawn`

### Workspace Membership

- `active`
- `revoked`
- `invited`

### Data Deletion Request

- `requested`
- `in_review`
- `completed`
- `rejected`
- `partially_completed`

### Model Version

- `draft`
- `benchmark_pending`
- `approved_for_user_facing_analysis`
- `retired`
- `rejected`

## Invariants

- Every workspace membership belongs to exactly one user and one workspace.
- Version one creates one default workspace and one owner workspace membership when a user registers.
- Version one exposes one active/default workspace per user in the UI.
- Every apiary belongs to exactly one workspace.
- Every hive belongs to exactly one apiary.
- Every inspection belongs to exactly one hive.
- Every inspection photo belongs to exactly one inspection.
- Every accepted inspection photo has a preserved original file reference.
- Every analysis result belongs to exactly one inspection photo.
- Every analysis result records the model version that produced it.
- Every annotation belongs to exactly one analysis result and one inspection photo.
- Every user correction belongs to exactly one inspection photo.
- Every user correction records the user who created it once authentication exists.
- A user correction is never ground truth without review.
- A user correction is never training, validation, or benchmark data without an active workspace data-use agreement and review.
- A user must be registered, logged in, and authorized through an active workspace membership before uploading inspection photos.
- A workspace without an accepted workspace data-use agreement must not upload new photos or receive new analysis.
- Workspace data-use agreement withdrawal disables new upload and analysis.
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

## Ownership, Data Use, And Privacy Boundaries

Version one uses workspace ownership as the access boundary.

The model must preserve:

- user identity for registration, authentication, and authorization
- workspace membership as the relationship between users and workspaces
- workspace ownership for apiaries, hives, inspections, photos, analysis results, annotations, corrections, workspace data-use agreements, and data deletion requests
- an active workspace data-use agreement before upload and analysis features are used
- metadata minimisation before training, evaluation, sharing, or publication
- data-use withdrawal handling for future model-improvement use
- the explicit gap around prior uploads, existing dataset versions, already-trained model artifacts, and deletion/purge rights

Deferred privacy decisions:

- exact future roles and permissions for invited workspace members
- exact wording and versioning of workspace data-use terms
- whether withdrawal affects only future model-improvement use or also previously uploaded photos
- whether and how users can purge workspace-held data
- whether already-trained model artifacts can or must be affected by later withdrawal or deletion requests
- what regulatory obligations apply to inspection photos and metadata

## Traceability

- `User`, `Workspace`, and `Workspace Membership` support registration, authorization, and FR-017.
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
- `Workspace Data Use Agreement` supports FR-016, FR-019, and MR-019 to MR-023 as revised by the domain decision.
- `Data Deletion Request` captures the deferred deletion/privacy gap.
- Upload status supports FR-018 and NFR-006.
- `Model Version` supports MR-028.
- `Dataset Version` supports MR-017 and MR-029.
- `Benchmark Evaluation` supports MR-030 and MR-031.

## Open Architecture Questions

- What exact registration and default workspace creation flow should version one use?
- What future workspace roles and invitation lifecycle are needed after version one?
- Should inspection summaries be stored snapshots, calculated on demand, or both?
- Should photo analysis run synchronously for a prototype or always as a background job?
- Where should original inspection photos be stored?
- What initial image formats and upload size limits should be configured?
- What should the workspace data-use agreement say, and how should accepted terms versions be tracked?
- How should workspace data-use withdrawal affect previously uploaded photos, existing dataset versions, and already-trained model artifacts?
- What data deletion or purge workflow is required before production use?
- Are uploaded photos and inspection metadata legally or operationally personally identifiable or sensitive in the target markets?
- Should frame labels affect v1 aggregation, or only provide warning context?
- How should duplicate or near-duplicate inspection photos be detected?
- What is the first model integration style: local model, hosted model service, or manual/mock analysis?
- What annotation or review interface should be used for first ground-truth creation?
- Should review decisions happen in the beekeeper UI, a reviewer/admin UI, or external tooling?
- Should older photos be re-analysed by newer model versions, and how should superseded results be shown?
