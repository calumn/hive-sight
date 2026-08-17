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

Implementation traceability note: some domain concepts are future-state concepts. As of Slice 0015 planning, the implemented path is bee annotation, dataset foundations, Hive Configuration metadata, Postgres-backed repository metadata, and preparation for a Bee Detector baseline. Real Varroa detection, Varroa Annotation review, Visible Varroa Rate calculation, user-facing Model Versions, and Benchmark Evaluations are modelled concepts, not completed runtime behaviour.

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
- **Model Governance**: annotations, corrections, workspace data-use agreements, deletion requests, reviewed data, dataset items, dataset roles, training runs, model candidates, model versions, benchmark evaluations, and release approval.

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
- may have internal capabilities for dataset/model governance workflows
- acts in a workspace through one workspace membership
- may create inspections, upload inspection photos, review tagged photos, and create user corrections when authorized through a workspace membership

Rules:

- User is the identity/authentication concept.
- User is not the ownership boundary for apiaries, hives, inspections, photos, or analysis results.
- Version one registration creates a default workspace and an owner workspace membership for the user.
- Dataset/model governance actors reuse User identity rather than a separate login system.

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
- Workspace Membership roles do not automatically grant internal dataset/model governance capabilities.

### Internal Capability

An authorization grant for internal dataset/model governance workflows.

Essential fields:

- id
- user id
- capability
- status
- granted at
- revoked at

Capabilities:

- `annotation_reviewer`
- `dataset_curator`
- `model_reviewer`
- `model_approver`

Relationships:

- belongs to one user

Rules:

- Internal capabilities are separate from Workspace Membership roles.
- Workspace ownership does not grant dataset curation, benchmark curation, model review, or model approval.
- Internal capabilities preserve one auditable User identity across product, dataset, and model-governance workflows.

### Dataset Curator

The internal actor/persona for dataset labelling and model-governance preparation.

Notes:

- Dataset Curator is not a separate login identity.
- A Dataset Curator is a User with the relevant internal capability.
- Use Dataset Curator when the actor is labelling data, assigning Dataset Roles, curating Dataset Versions, or preparing model-governance evidence.
- Use Beekeeper when the actor is doing ordinary inspection-support work in a Workspace.

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
- has many hive configurations over time
- has one active hive configuration at a time
- has many inspections

### Hive Configuration

The equipment context for a Hive that may help interpret inspection photos and model performance.

Essential fields:

- id
- hive id
- hive type
- box/use
- optional frame standard id
- status
- effective from
- effective to
- created at

Initial hive types may include:

- `british_national`
- `wbc`
- `smith`
- `british_commercial`
- `langstroth`
- `other`
- `unknown`

Initial box/use values may include:

- `brood`
- `super`
- `extra_deep`
- `other`
- `unknown`

Relationships:

- belongs to one hive
- may reference one frame standard

Rules:

- Hive Configuration is model context and provenance.
- A Hive may start with `unknown` equipment context and be refined later.
- Inspection creation requires an active Hive Configuration.
- Hive Configuration is effective-dated history, not a mutable single current record.
- At most one Hive Configuration may be active for a Hive at a time.
- Replacing a Hive Configuration supersedes the previous active configuration and records its `effective_to`.
- Training data should preserve whatever Hive Configuration was known when the source image was captured. If capture-time configuration cannot be resolved, Dataset Item provenance may fall back to assignment-time configuration and must record that fallback.
- Detailed Hive Component or Box configuration is deferred; for Slice 0014, `box/use` remains on Hive Configuration and is snapshotted into Dataset Item provenance.

### Frame Standard

A reusable description of expected physical frame dimensions.

Essential fields:

- id
- display name
- hive type
- frame use
- top bar length
- bottom bar length
- side bar height
- measurement unit
- source or notes

Rules:

- Frame Standard describes expected equipment dimensions; it does not prove the photo has been calibrated to physical scale.
- Frame Standard may later support model bias analysis, crop calibration, quality checks, and frame-region guidance.

### Inspection

A dated review of one hive.

Essential fields:

- id
- workspace id
- hive id
- optional created by user id
- inspection date
- intent
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

Rules:

- Every Inspection has one explicit intent.
- Initial intents are `training_data_collection` and `varroa_assessment`.
- Dataset labelling workflows and beekeeper-facing Varroa assessment workflows must not be mixed inside the same Inspection.

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

### Source Rights Record

The recorded lawful-use basis for one or more Source Images. It is distinct from Annotation Source and records the rights to use the underlying image evidence.

Essential fields:

- id
- rights basis
- source organisation or repository
- source reference
- licence or terms version
- allowed-use summary
- permitted use scopes
- attribution requirement
- attribution text
- restriction review
- status
- reviewed by user id
- reviewed at
- recorded by user id
- recorded at

Statuses:

- `pending_review`
- `approved`
- `rejected`
- `superseded`
- `invalidated`

Rules:

- Recognised rights bases include `workspace_data_use_agreement`, `contributor_contribution_permission`, `public_or_open_licence`, and `other_approved_basis`.
- A public/open rights record must identify a source reference and licence or terms version and be explicitly approved by a Dataset Curator before its Source Images become Dataset Items.
- Public/open evidence is local research and model development evidence only unless the approved Source Rights Record explicitly permits a broader use scope.
- Imported annotation provenance does not establish rights to the underlying image and is stored separately.
- A Source Rights Record remains immutable once a Dataset Version includes a referenced Source Image; later corrections create a superseding rights record.
- If a rights basis is later found invalid, revoked, or incompatible with HiveSight's use, the record becomes `invalidated` and triggers the quarantine and replacement path defined by ADR 0009.
- Required attribution is carried into every relevant Dataset Version, derived export, Benchmark Evaluation report, and released Model Version documentation.
- An unlisted use scope is not permitted.

### Source Image

The underlying original image evidence record used by inspection, dataset, and model-governance workflows.

Essential fields:

- id
- human-readable id
- workspace id
- source type
- original file reference or object key
- original filename
- media type
- file size
- source image width
- source image height
- content hash
- content hash algorithm
- source group key
- provenance summary
- permission status
- source rights record id
- metadata status
- metadata checked at
- status
- rights-impact reason
- created at

Source types:

- `inspection_photo`

Future source types:

- `project_import`
- `public_dataset`
- `external_annotation_import`

Statuses:

- `accepted`
- `rejected`
- `archived`

Rules:

- Source Image is image-only for now.
- In Slice 0014, every Source Image is also an Inspection Photo because only the `inspection_photo` source type is implemented.
- Later, not every Source Image will be an Inspection Photo.
- `workspace_id` is required for `inspection_photo` Source Images; future public/imported source ownership may differ.
- Accepted Source Images require dimensions, `content_hash`, and `content_hash_algorithm`.
- Source Image has its own provenance and permission status, separate from Dataset Item permission snapshots.
- Every Source Image used for model data has a Source Rights Record. The rights basis may be a Workspace Data Use Agreement, Contributor Contribution Permission, public/open licence, or another explicitly approved basis.
- Public/open Source Images record their source organisation or repository, source reference, licence or terms version, allowed-use basis, attribution requirement, and restriction review. Imported annotation provenance remains distinct from source-image rights.
- Source Image may exist without dataset eligibility, but Dataset Item creation requires eligible permission.
- Raw EXIF or image metadata should not be stored in Postgres by default because image metadata may contain personally identifiable information, location, device, or private apiary signals.
- `metadata_status` records minimisation/check status only.
- `source_group_key` is a broad manual grouping hook for likely related images, such as the same physical frame, near-duplicate photo burst, same imported source unit, or same frame side.

### Inspection Photo

The beekeeper/product-facing role a Source Image plays when it is attached to an Inspection.

Essential fields:

- id
- workspace id
- source image id
- inspection id
- optional frame label id
- upload status
- image quality status
- uploaded at
- uploaded by user id

Relationships:

- references one source image
- belongs to one inspection
- may reference one frame label
- may have many analysis results over time
- may have many annotations through analysis results
- may have many user corrections
- inherits data-use eligibility from the workspace data-use agreement

Rules:

- Accepted original photos are preserved.
- Product workflows and UI language should continue to use Inspection Photo.
- In Slice 0014, every persisted Source Image is an Inspection Photo source image.
- Tagged photos are rendered views, not replacements for the original.

### Training Crop

A bounded image region derived from a Source Image for focused dataset annotation.

Essential fields:

- id
- human-readable id
- workspace id
- source image id
- optional inspection photo id
- crop bounds in source-image coordinates
- crop image dimensions
- curriculum stage
- created by user id
- review status
- created at

Curriculum stages:

- `small_crop`
- `medium_crop`
- `large_crop`
- `full_frame_region`
- `full_frame_side`

Relationships:

- belongs to one source image
- may reference one inspection photo when the source type is `inspection_photo`
- may have many bee annotations
- may become a dataset item after complete review and dataset role assignment

Rules:

- A Training Crop preserves provenance back to the original Source Image and, when applicable, its Inspection Photo context.
- A Training Crop is a review unit, not a replacement for the original photo.
- Before a Training Crop becomes dataset-eligible, a Dataset Curator should mark all visible bees in the crop or explicitly exclude the crop.
- A Training Crop is mutable during review.
- Once a Dataset Item has been assigned from a Training Crop, the Training Crop is locked for mutations that would affect evidence. Future corrections require a supersession/reopening workflow.

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
- optional analysis result id
- optional training crop id
- photo id
- source
- geometry
- visibility class
- orientation reliability
- Varroa review suitability
- suspected visible Varroa cue
- confidence
- review status

Visibility classes:

- `complete_visible_bee`
- `partial_visible_bee`
- `uncertain_bee`

Annotation sources:

- `human_from_scratch`
- `model_candidate`
- `imported_public_dataset`
- `user_corrected`
- `reviewer_corrected`
- `unknown_legacy`

Review methods:

- `human_from_scratch`
- `human_reviewed_candidate`
- `imported_reviewed`

Rules:

- The canonical reviewed geometry for bee annotations is an oriented bee ellipse.
- Oriented Bee Ellipse rotation is directed: `rotation_degrees` points from the ellipse center toward the bee's head along the major axis; the opposite end is the tail.
- Reviewed Bee Annotations record Orientation Reliability as `reliable` or `unreliable`, independently of their visibility class, bee-presence confidence, and review status. New Oriented Bee Ellipses default to `reliable`; the annotator changes them to `unreliable` when head/tail direction is doubtful.
- Existing local test Bee Annotations without Orientation Reliability may be normalized to `reliable` without a separate defaulted-provenance flag. Future annotation evidence missing Orientation Reliability is excluded from Bee Orientation or Head-Up Normalized Varroa exports until normalized or corrected.
- Bee Annotations may carry lightweight Varroa review triage cues set during bee annotation: Varroa Review Suitability (`unassessed`, `appears_assessable`, or `body_occluded_or_hard_to_assess`) and a boolean Suspected Visible Varroa Cue. These cues are not Varroa Review Outcomes, do not create positive or negative Varroa evidence, and do not override first-corpus eligibility rules.
- New Bee Annotations default Varroa Review Suitability to `unassessed` and Suspected Visible Varroa Cue to false. Existing local test Bee Annotations may be normalized to those defaults without a separate defaulted-provenance flag.
- Varroa review triage cues retain last-updated provenance, such as the user and timestamp that set the cue. Full cue history is not required.
- Candidate Annotations are not ground truth until human reviewed.
- Reviewed Annotations still require Dataset Role assignment before dataset use.
- Model-specific exports may project oriented ellipses into other shapes such as YOLO OBB labels.
- Bee annotation geometry remains mutable during Training Crop review and is locked once a Dataset Item snapshots it.
- `partial_visible_bee` requires enough visible body to draw a meaningful ellipse. Ambiguous fragments should be uncertain or excluded rather than guessed into training evidence.

### Candidate Annotation

A proposed Annotation awaiting human review.

Essential fields:

- id
- workspace id
- source image id
- optional inspection photo id
- optional training crop id
- annotation type
- proposed geometry
- annotation source
- optional proposing model candidate id
- confidence
- status
- created at

Sources:

- `model_candidate`
- `imported_public_dataset`
- `human_from_scratch`
- `unknown_legacy`

Rules:

- Candidate Annotations are untrusted proposed evidence.
- Candidate Annotations may accelerate review but must not enter Dataset Versions until human reviewed.
- Grounding DINO is retired from the active solution and should not be modelled as an active Candidate Annotation source.
- Imported public dataset annotations may enter as Candidate Annotations only; they become reviewed evidence only after HiveSight review.
- Candidate Annotation is independent of any one model run or model family.

### Head-Up Normalized Bee Crop

A derived bee-relative image and coordinate frame rotated so the bee's head is at the top.

Essential source inputs:

- source image bytes
- inspection photo id
- training crop id
- bee annotation id
- bee annotation geometry snapshot
- transform version

Rules:

- It is derived from the source image, Training Crop, and a Bee Annotation; it is not a standalone persisted entity in Slice 0025.
- It may be generated on demand for Varroa Review and later materialized inside a Varroa Dataset Version export artifact.
- Marker coordinates recorded during Varroa Review are relative to this normalized coordinate frame, not the browser display pixels.
- The transform metadata must be sufficient to regenerate the review image and understand the marker coordinate frame.

### Varroa Review

A human review of visible Varroa evidence on one bee-relative crop.

Essential fields:

- id
- workspace id
- inspection photo id
- training crop id
- bee annotation id
- transform metadata
- bee annotation geometry snapshot used for the transform
- sampling purpose
- dataset selection method
- sampling stratum summary
- review outcome
- source
- review method
- review strength
- created by user id
- created at
- updated by user id
- updated at
- optional notes
- optional independent second reviewer id
- optional adjudicator id, distinct from both original reviewer ids
- optional adjudication reference
- optional adjudication rationale

Review outcomes:

- `visible_varroa_present`
- `no_visible_varroa`
- `not_determined`

Rules:

- Slice 0025 creates one current editable Varroa Review per Workspace and Bee Annotation. Later immutable revision/history records are a separate design.
- A Varroa Review is created only when the curator saves an actual outcome. `Not reviewed` is derived from the absence of a current Varroa Review row, not stored as an outcome.
- `visible_varroa_present` requires one or more Varroa Markers.
- `no_visible_varroa` is an active human negative judgement, not merely the absence of a Varroa Annotation.
- `not_determined` requires a note in Slice 0025 and must not be exported as a negative Varroa training or benchmark example.
- `no_visible_varroa` and `not_determined` require zero Varroa Markers.
- Slice 0025 Varroa Reviews are Dataset Curator-only, Training Data Collection-only, and limited to completed non-excluded Training Crops.
- Slice 0025 eligible bees must be `complete_visible_bee` with reliable Orientation Reliability and available source image bytes. Partial visible bees and unreliable-orientation bees may be shown as ineligible/deferred but cannot receive a Slice 0025 Varroa Review Outcome.
- Varroa Review Suitability and Suspected Visible Varroa Cue may prioritise or warn in the UI, but they do not preselect or save a Varroa Review Outcome.
- Slice 0025 review provenance is `model_curation`, `human_selected`, `single_curator_review`, and `human_from_scratch`. This describes the Varroa review itself; the source Bee Annotation's own provenance remains separately visible.
- A Varroa Review is potential future model-curation evidence. It is not automatically a Dataset Item, Dataset Role assignment, benchmark label, Gold-Standard Full-Frame Corpus item, inspection-rate sample, or user-facing Varroa Assessment result.
- `model_curation` and `inspection_rate_estimation` are distinct Sampling Purposes even when they share the same review UI; only the former is eligible for a model Dataset Item by default.
- Slice 0025 uses manual human selection from the selected Training Crop and records `human_selected`. Later sampling-plan slices may add `stratified_random`, `curator_targeted`, or upstream-model-selected queues.
- An early baseline benchmark may use one active curator review only when its report states that limitation. A Model Candidate cannot be considered for user-facing Varroa Assessment until benchmark Varroa Review Outcomes have Blind Independent Review: the second reviewer cannot see the first outcome or Varroa marker positions. Disagreements require Third-Party Adjudication by a reviewer distinct from both originals, who first records a fresh blind review and only then sees anonymised prior reviews to document the final outcome.
- A disagreement that remains unresolved, including a three-way conflict, has the canonical outcome `not_determined` and is excluded from Varroa training and benchmark evidence.
- Training and validation Varroa evidence may use one active reviewed outcome when its review provenance remains available; the stronger Blind Independent Review and Third-Party Adjudication path is the user-facing benchmark promotion gate.
- A non-blocking quality audit periodically selects a stratified-random sample of training and validation Varroa Reviews for Blind Independent Review. Its selection and review provenance, agreement, disagreement, and unresolved outcomes remain distinct from protected benchmark evidence and are reported by Annotation Source, including human-from-scratch and AI-assisted-reviewed evidence.
- A concerning quality-audit result requires a documented Dataset Curator Audit Disposition and a warning on every affected Dataset Version. It does not automatically block dataset use while numerical escalation thresholds remain deferred.

### Varroa Marker

Structured marker data identifying a visible Varroa mite in one Head-Up Normalized Bee Crop.

Essential fields:

- id
- Varroa Review id
- marker type
- normalized x coordinate
- normalized y coordinate
- created at

Marker types:

- `point`

Rules:

- Varroa Markers belong to a Varroa Review, not directly to a Bee Annotation.
- Slice 0025 supports multiple point markers per positive Varroa Review.
- Normalized coordinates are stored in the inclusive range `0 <= x <= 1` and `0 <= y <= 1`, rounded to a stable precision such as four decimal places.
- Slice 0025 does not require per-marker notes, marker dragging, tight boxes, segmentation masks, or body-mask containment validation.

### Varroa Corpus Curation Decision

A Dataset Curator's current decision about whether one Varroa Review Outcome may contribute to the first Varroa Detection model-curation corpus.

Essential fields:

- id
- workspace id
- Varroa Review id
- decision
- target class
- reason
- eligibility snapshot
- source context snapshot
- created by user id
- created at
- updated by user id
- updated at

Decisions:

- `included`
- `excluded`
- `deferred`

Rules:

- The future Varroa Corpus Governance candidate records one current Varroa Corpus Curation Decision per Workspace and Varroa Review Outcome.
- The curation decision does not mutate the original Varroa Review Outcome or its Varroa Markers.
- `included` requires a determinate Varroa Review Outcome: `visible_varroa_present` with one or more markers, or `no_visible_varroa` with zero markers.
- `not_determined` is deferred by default and cannot be included as positive or negative model-curation evidence.
- A saved Varroa Review whose source Training Crop, Bee Annotation geometry, annotation type, Orientation Reliability, or Head-Up Normalized Bee Crop transform no longer matches the current source evidence is stale and cannot be included until rechecked.
- Negative outcomes from bees marked `body_occluded_or_hard_to_assess` default to deferred because they are weak negative evidence. A positive outcome from a hard-to-assess bee may be included with the warning preserved.
- Varroa Corpus Governance is model-curation evidence only. It is not a Dataset Version, benchmark-strength evidence, Gold-Standard Full-Frame Corpus membership, Inspection-Rate Sample, Visible Varroa Rate, Varroa Assessment, or treatment trigger.

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
- Candidate Annotations are not ground truth until human reviewed.
- Reviewed Annotations still require Dataset Role assignment before dataset use.
- A legacy or model-produced Varroa Annotation is evidence of a positive marker candidate. A Varroa Review carries the explicit positive, negative, or not-determined judgement for the bee-relative crop, and its Varroa Markers carry human-reviewed point evidence in normalized bee-crop coordinates.

### Frame Mite Count

A transient, model-assisted count of likely visible Varroa detections across eligible bee annotations for one photographed frame.

Essential fields:

- workspace id
- inspection id
- hive id
- inspection photo id
- inspection date
- source image filename
- model purpose
- adapter type
- adapter version
- model reference
- completed Training Crop count
- unfinished Training Crop count
- excluded Training Crop count
- eligible bee count
- processed bee count
- bees with likely Varroa count
- likely Varroa detection count
- not-assessed bee count
- failed bee count
- model determinate coverage percent
- per-bee result summaries
- caveats

Rules:

- Slice 0028 Frame Mite Counts are run on demand and are not persisted as durable result history.
- A Frame Mite Count belongs to one selected Inspection Photo, not a whole Inspection.
- It runs the configured Varroa Detector over eligible complete reliable bee annotations from completed, non-excluded Training Crops.
- It counts bee annotations, not deduplicated physical bees across overlapping Training Crops.
- Partial visible bees, unreliable-orientation bees, unfinished crops, excluded crops, transform failures, and adapter failures are disclosed separately and are not negative Varroa results.
- A detector result with zero detections is a completed model inference with `0 likely detections`; it is not a human `no_visible_varroa` review outcome.
- A Frame Mite Count does not create, update, or approve Varroa Review Outcomes, Varroa Markers, Dataset Items, Dataset Versions, or Varroa Corpus Curation Decisions.
- It is model-assisted frame evidence only. It is not a Visible Varroa Rate, Varroa Assessment, Treatment Recommendation, HiveSight Advisor context, Advisor trigger, or whole-colony measurement.

### Varroa Photo Analysis

A persisted, model-assisted evidence run for one Inspection Photo.

Essential fields:

- id
- workspace id
- inspection id
- inspection photo id
- status: `running`, `completed`, `partial`, `failed`, or `no_usable_bees`
- review status: `unreviewed`, `accepted`, `rejected`, `inconclusive`, or `needs_expert_review`
- review note
- total detected bees
- eligible bees
- analysed bees
- failed bees
- mites found
- bees with likely visible Varroa
- mite ratio basis
- adapter type
- adapter version
- model reference
- command contract version
- started at
- completed at
- caveat
- Advisor evidence eligibility
- per-bee Photo Analysis results

Rules:

- A Varroa Photo Analysis belongs to one Inspection Photo, not a whole Inspection or Hive.
- A photo has at most one active or produced current-model analysis. Completed, partial, and no-usable-bees results are not rerun; a failed run may be retried. Model-version reanalysis is a separate future workflow that creates a new immutable evidence run.
- Job status and human review status are separate fields.
- Product analysis is independent of Training Crops and Training Crop Bee Annotations.
- Each Inspection Photo Bee Evidence record is a child of the analysis and also retains the Inspection Photo id and source geometry for evidence display and integrity checking.
- `partial` means every eligible bee was attempted, but one or more bee detector calls failed.
- `no_usable_bees` means analysis ran but no bees were eligible for Varroa evaluation.
- A failed or aborted analysis is not a partial result and cannot be accepted.
- Per-bee analysis records preserve detector status, detections, failure details, and structured adapter/model provenance.
- Raw detector request payloads are not stored by default. Capped sanitized raw response or error payload may be retained only for failed or invalid adapter calls.
- A zero-mite model result is not automatically accepted and is not a human `no_visible_varroa` judgement.
- Slice 0035 derives current Advisor evidence eligibility from review status plus the frozen Product Photo Analysis confidence-policy outcome: accepted deterministic development evidence can become `development_integration_only`, while accepted non-stub evidence can become `product_candidate` only when the policy status allows it.
- `needs_expert_review`, `inconclusive`, `rejected`, and `unreviewed` are not Advisor-eligible.

### Advisor Treatment Advice Attempt

A Beekeeper's attempt to obtain HiveSight Advisor treatment advice for one Hive evidence context.

Essential fields:

- id
- treatment evidence chain id
- workspace id
- apiary id
- hive id
- inspection id
- inspection photo id
- concern
- state
- blocked reasons
- adapter type
- adapter version
- created by user id
- created at

Version-one states:

- `blocked_not_ready`
- `advisor_request_failed`
- `recommendation_pending`
- `recommendation_accepted`
- `recommendation_declined`

Rules:

- An Advisor Treatment Advice Attempt is not a Treatment Recommendation unless HiveSight Advisor returns usable advice.
- Blocked and failed attempts remain visible in chain history without creating treatment history.
- Training Data Collection evidence is not product-eligible for Advisor treatment advice; tests may inject synthetic ready context through a controlled seam.
- Production-like configuration must not allow deterministic stub advice to become beekeeper treatment history.

### Advisor Varroa Context Snapshot

The immutable Slice 0029 Advisor Varroa context captured when a Beekeeper asks for treatment advice.

Essential fields:

- id
- treatment evidence chain id
- workspace id
- apiary id
- hive id
- inspection id
- inspection photo id
- context contract version
- full context payload
- context summary
- created by user id
- created at

Rules:

- The snapshot is created only for an Advisor treatment advice attempt, not every transient context read.
- It stores what HiveSight knew at the time advice was requested or blocked.
- Later evidence, model changes, treatment history, or context-builder changes do not rewrite the snapshot.

### Treatment Evidence Chain

The explicit audit handle connecting source Varroa evidence, Advisor context, Advisor request and response, Beekeeper decision, and any resulting treatment course.

Essential fields:

- id
- workspace id
- apiary id
- hive id
- inspection id
- inspection photo id
- concern
- state
- created by user id
- created at
- updated at

Rules:

- A Treatment Evidence Chain can end at a blocked attempt, failed Advisor request, pending recommendation, declined recommendation, accepted recommendation, or planned Hive Treatment Course.
- Chain-history list views show summaries by default.
- Single-chain detail may expose full raw context, request, and response payload snapshots for audit.
- Advisor learning, retrieval, RAG, export, anonymisation, retention, and minimisation are later governance concerns, not implicit uses of chain records.

### Treatment Recommendation

An advisory suggestion returned by HiveSight Advisor for a Hive health concern.

Essential fields:

- id
- treatment evidence chain id
- Advisor treatment request snapshot id
- workspace id
- apiary id
- hive id
- concern
- status
- raw Advisor response payload
- recommendation text
- grounding status
- citations
- adapter type
- adapter version
- Advisor response contract version
- response received at
- decision by user id
- decision at
- decision note

Version-one statuses:

- `pending`
- `accepted`
- `declined`
- `superseded`

Rules:

- A Treatment Recommendation is a suggested treatment plan requiring Beekeeper decision, not applied treatment.
- Accept and decline are current decision fields in the first slice; immutable decision history is deferred.
- Accepting a recommendation is idempotent and creates at most one planned Hive Treatment Course.
- Declining is idempotent for already declined recommendations, but cannot reverse acceptance.
- Advisor citations are stored as structured data as well as inside the raw response payload.

### Hive Treatment Course

A Beekeeper-owned planned or actual treatment course for one Hive.

Essential fields:

- id
- treatment evidence chain id, nullable for manual courses
- source treatment recommendation id, nullable
- workspace id
- apiary id
- hive id
- purpose
- status
- planned course snapshot
- accepted by user id
- accepted at
- acceptance note
- created by user id
- created at

Version-one Advisor-created status:

- `planned`

Rules:

- A Hive Treatment Course created from an accepted Treatment Recommendation is separate from the recommendation.
- A planned course does not imply treatment has been applied.
- Slice 0029.5 does not edit planned courses, schedule reminders, record dated Treatment Applications, mark completion, or record outcomes.
- Manual Hive Treatment Course entry without Advisor provenance is a separate roadmap item.
- A new Advisor recommendation request is blocked while the Hive already has an open planned Varroa treatment course.

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

### Inspection Recovery Review

A distinct, named, saveable, and resumable human review session that recovers or corrects a model-only inspection result.

Essential fields:

- id
- inspection id
- original model-only result id
- original photo-evidence snapshot reference
- original model candidate/version references
- recovery-review provenance on every resulting annotation and Varroa decision
- optional superseded recovery review id
- optional superseded human-reviewed result id
- created by user id
- status
- started at
- last saved at
- completed at
- optional notes
- review completion
- determinate Varroa coverage
- result evidence breakdown: positive, active negative, not-determined, and unassessed complete visible-bee counts

Statuses:

- `in_progress`
- `completed`
- `abandoned`

Rules:

- The review is linked to, and does not change, the original model-only result.
- The review uses a fixed snapshot of the original model-only result and its photo evidence. Newer models are not run or substituted during recovery.
- Every annotation and Varroa decision produced or amended in the review retains its recovery-review provenance and is reported as AI-assisted-reviewed, never human-from-scratch, because the original model output was visible.
- If the Workspace Data Use Agreement is withdrawn but the inspection remains retained, the Workspace owner may still complete the review for inspection support. Its evidence is ineligible for model improvement until an active agreement exists and a Dataset Curator independently reviews it and assigns a Dataset Role.
- Recovery evidence created during withdrawal remains product-only after later agreement acceptance. The Workspace owner must make a separate explicit dataset-contribution decision before independent Dataset Curator review and Dataset Role assignment may make it eligible for model improvement.
- Model promotion does not automatically reanalyse historical Inspection Photos. A future explicit Historical Reanalysis creates a new model-only result and never alters earlier model-only or human-reviewed results.
- In the first release, a review may be opened only for a model-only result whose user-facing Varroa estimate is suppressed for inadequate coverage.
- In the first release, only the Workspace owner may create, resume, or complete a review.
- The Workspace owner may complete a review at any coverage level after explicit confirmation, including when the resulting headline rate remains suppressed.
- A completed review and its Human-Reviewed Inspection Result are immutable. A later correction starts a new linked recovery review and result revision, which records what it supersedes.
- The latest completed Human-Reviewed Inspection Result is the inspection's current result by default. The original model-only result and earlier human-reviewed revisions remain available as labelled comparison history.
- The reviewer may resolve previously unassessed complete visible bees and correct any model-produced bee, orientation, or Varroa decision.
- A completed review produces a separately provenanced Human-Reviewed Inspection Result with its own Review Completion and Determinate Varroa Coverage calculations.
- The original model-only result and every Human-Reviewed Inspection Result expose a Result Evidence Breakdown with positive, active negative, `not_determined`, and unassessed complete visible-bee counts.
- `not_determined` counts toward Review Completion but not Determinate Varroa Coverage and cannot support a headline Visible Varroa Rate.
- Review evidence is product feedback only until a Dataset Curator independently reviews it and assigns a Dataset Role.

### Dataset Contribution Decision

An explicit Workspace owner decision allowing one completed Human-Reviewed Inspection Result revision to be considered for model-data curation.

Essential fields:

- id
- workspace id
- human-reviewed inspection result revision id
- current Workspace Data Use Agreement id and terms version
- decided by user id
- decided at
- status

Statuses:

- `contributed`
- `withdrawn`

Rules:

- A decision applies to exactly one named result revision and is never a workspace-wide opt-in.
- It does not itself assign a Dataset Role or make evidence training-ready; independent Dataset Curator review and Dataset Role assignment remain required.
- It can be created only while a Workspace Data Use Agreement is active.

### Contribution Bundle

A named, immutable collection of one contributor's identified images, annotations, or reviews that share one intended model-data permission boundary.

Essential fields:

- id
- human-readable id
- workspace id
- contributor user id
- contributor pseudonym snapshot
- name
- contribution subject references
- created at

Rules:

- A bundle belongs to exactly one contributor in one workspace.
- A Dataset Curator creates the bundle and assigns its annotation tasks. The Workspace owner may offer their own evidence but does not obtain dataset-governance authority through ownership alone.
- A contributor is a registered User and can view their own bundles through their own identity.
- A contributor may use a pseudonym. HiveSight retains only the minimum contact/authentication data needed to manage contributor access and requests; provenance and curator-facing views use the internal contributor id and pseudonym rather than a required real name.
- Contributor registration does not grant Workspace Membership, Workspace ownership, or dataset/model-governance capability.
- Contributor access is limited to explicitly assigned annotation tasks and Contribution Bundles; it does not expose the wider Workspace, unassigned inspections, or other contributors' evidence.
- The contributor can view a read-only Contribution Usage Record for each bundle: accepted terms, permission and deletion status, and linked Dataset Versions, Training Runs, and model-artifact outcomes. It does not reveal other contributors' evidence or the wider Workspace.
- A contributor may create more than one bundle.
- Once a Contributor Contribution Permission is accepted, the bundle's subject list is immutable. Additional work requires a new bundle.
- In the first release, withdrawal applies to the complete bundle. Finer withdrawal boundaries require separate bundles before permission acceptance.
- Every Dataset Item derived from a bundled contribution retains the bundle reference.

### Contributor Contribution Permission

A registered contributor's explicit permission for one named, immutable Contribution Bundle of their identified image, annotation, or review work to support model-data curation. It is separate from Workspace ownership, Workspace Membership, Dataset Curator capability, and the Workspace Data Use Agreement.

Essential fields:

- id
- contributor user id
- workspace id
- contribution bundle id
- terms version
- permitted use scopes
- terms reacceptance required at
- status
- offered at
- accepted at
- withdrawn at

Statuses:

- `not_accepted`
- `offered`
- `accepted`
- `withdrawn`

Rules:

- A permission covers exactly one named, immutable Contribution Bundle; it is not a grant over the whole workspace.
- Permitted Use Scopes are an explicit, closed list. An unlisted use is not permitted.
- The first contributor terms offer `model_development` and `evaluation` only. `user_facing_deployment`, `sharing_or_publication`, and `commercial_use` require separate explicit opt-in.
- Before acceptance, the contributor sees only a non-sensitive bundle summary and the applicable terms. Assigned images and annotation tasks become visible only after explicit acceptance of that named bundle and terms version.
- A material terms change requires fresh acceptance before the bundle can appear in a new Dataset Version, Training Run, Benchmark Evaluation, or promotion. Historical lineage remains available for audit.
- Re-acceptance after withdrawal creates a new permission record for future use only. It never automatically unquarantines prior Dataset Versions or model artifacts.
- Every Dataset Item derived from the bundle retains the permission and bundle references.
- A contributor may withdraw their own permission without becoming a Workspace owner or Dataset Curator.
- The contributor can withdraw permission through their own registered HiveSight identity.
- Withdrawal applies to the complete Contribution Bundle in the first release.
- Withdrawal or a contributor deletion request immediately revokes access to every unfinished task in the bundle. HiveSight retains only the minimal audit record needed to explain the request and affected lineage.
- A Dataset Item is eligible for future model use only while the Workspace Data Use Agreement and every applicable Contributor Contribution Permission are active.
- Withdrawal follows ADR 0008 for every Dataset Item and derived artifact that depends on the permission.

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
- Review approval does not by itself assign training, validation, or benchmark use.

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
- Contribution Withdrawal stops future reliance on affected training evidence, including its use through affected Dataset Versions, Model Candidates, and Model Versions. Historical lineage is retained for audit; source-image and annotation erasure follows the applicable deletion process.

### Data Deletion Request

A tracked request to delete or purge workspace-held data or a contributor's own Contribution Bundle. A contributor's request automatically triggers Contribution Withdrawal, which immediately stops future model use.

Essential fields:

- id
- workspace id
- requester id
- request scope
- optional contribution bundle id
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
- A contributor may request deletion only for their own Contribution Bundle through their registered HiveSight identity.
- Starting a contributor deletion request automatically withdraws the bundle's Contributor Contribution Permission before erasure processing begins.
- A contributor's deletion request does not grant permission to delete another contributor's data or the wider workspace.
- A request records source-image, annotation, derived-artifact, and retention-handling outcomes separately from Contribution Withdrawal.
- Uploaded photos and metadata should be treated as potentially personally identifiable or sensitive.
- The exact contents and retention period of the minimal audit record, deletion/purge timing, legal-retention exceptions, and material-terms-change classification remain to be decided before production use; PARK-0011 tracks this policy work.

### Dataset Item

A reviewed image-and-annotation unit assigned to a dataset role.

Essential fields:

- id
- human-readable id
- workspace id
- source image id
- optional inspection photo id
- training crop id
- reviewed annotation references
- dataset role
- optional curriculum stage
- provenance
- dataset selection method
- permission status
- contributor contribution permission and bundle references
- source rights record snapshot
- permitted use scope snapshot
- eligibility-impact reason
- source group key
- hive configuration snapshot
- hive configuration resolution
- exclusion reason
- status
- supersedes dataset item id
- superseded by dataset item id
- created at

Dataset roles:

- `training`
- `validation`
- `benchmark`
- `excluded`

Rules:

- A Dataset Item requires reviewed annotation evidence.
- Dataset Items are immutable after assignment.
- Later corrections use supersession or withdrawal rather than in-place mutation.
- Initial statuses are `active`, `superseded`, `withdrawn`, and `rights_invalidated`.
- Benchmark Dataset Items must not be used for training or routine tuning.
- Benchmark Dataset Items are selected from a predeclared sampling plan and frozen before an evaluated Model Candidate is run. They must not be added because of that candidate's results.
- Benchmark Dataset Items require a `source_group_key`.
- Dataset Role assignment must hard-block benchmark leakage conflicts for the same Source Image or same `source_group_key` across benchmark versus training/validation.
- Training and validation may share a `source_group_key` in Slice 0014, but exports or reports must flag that as a leakage warning.
- Duplicate or near-duplicate frame photos must be handled before serious benchmark claims.
- Dataset Items snapshot the approved Source Rights Record, Workspace Data Use Agreement eligibility where applicable, and every applicable Contributor Contribution Permission at assignment time.
- A Dataset Item may be used only for a scope allowed by its Source Rights Record and every applicable Contributor Contribution Permission.
- Varroa Dataset Items record Dataset Selection Method as `human_selected` or `upstream_model_selected`. `human_selected` requires selection before upstream model suggestions are seen; any model-influenced selection is `upstream_model_selected`. Benchmark Evaluations report the distribution.
- Contribution Withdrawal transitions affected Dataset Items to `withdrawn` and excludes them from all future exports, Dataset Versions, Training Runs, Benchmark Evaluations, and promotion.
- Source Rights Invalidation transitions affected Dataset Items to `rights_invalidated` and applies the same exclusion to future exports, Dataset Versions, Training Runs, Benchmark Evaluations, and promotion.
- Model-specific training files are derived artifacts, not the canonical Dataset Item evidence.

### Dataset Version

A frozen, named version of reviewed data used for a Training Run or protected Benchmark Evaluation.

Essential fields:

- id
- human-readable id
- workspace id
- purpose
- model purpose
- status
- export format
- selection criteria
- manifest hash
- included dataset item snapshots
- excluded dataset items and reasons
- protected benchmark dataset item ids
- source group distribution
- hive configuration distribution
- curriculum stage distribution
- annotation class counts
- annotation source counts
- review method counts
- warning summary
- rights-impact summary
- required attribution summary
- permitted use scope summary
- audit dispositions
- created by user id
- created at

Statuses:

- `active`
- `obsolete`
- `quarantined`

Rules:

- A Dataset Version is explicit and durable.
- A Dataset Version freezes the evidence and explanatory metadata used at creation time.
- A benchmark Dataset Version or selection snapshot freezes the predeclared sampling plan, selection methods, strata, and included items before the evaluated Model Candidate is run.
- Only active, reviewed Dataset Items may be included.
- Candidate Annotations that have not been reviewed are excluded from Dataset Versions.
- Dataset Versions used by Training Runs are immutable. Changed evidence or changed selection criteria require a new Dataset Version.
- Benchmark Dataset Items may be recorded as protected metadata, but must not be exported into trainer-facing training or validation data.
- A Dataset Version may be marked obsolete as metadata, but its frozen manifest must not be changed.
- A Dataset Version reports the intersection of its included Dataset Items' Permitted Use Scopes and identifies incompatible or excluded evidence.
- A Contribution Withdrawal or Source Rights Invalidation affecting any included Dataset Item transitions the Dataset Version to `quarantined`; its immutable manifest remains available only for audit and it cannot support a new Training Run, Benchmark Evaluation, or promotion.
- Model-specific export packages are physical artifacts derived from a Dataset Version, not the Dataset Version itself.

### Training Run

A recorded execution that trains or fine-tunes a model candidate.

Essential fields:

- id
- human-readable id
- workspace id
- dataset version id
- model purpose
- model family
- adapter type
- training settings summary
- base weights and source
- random seed
- database purpose
- artifact manifest reference
- code or artifact reference
- git commit sha and dirty status
- environment summary
- status
- phase
- started at
- completed at
- failure code
- failure message
- outcome summary
- optional retry-of training run id
- rights-impact summary
- required attribution summary

Rules:

- Training Runs must not use benchmark Dataset Items.
- Training Runs should be repeatable enough to compare candidates.
- The first Bee Localisation baseline is expected to use YOLO OBB as a model-specific export from reviewed oriented bee ellipses.
- YOLO OBB body-axis geometry is not Bee Orientation evidence; a future Bee Orientation Model must establish directed centre-to-head orientation independently.
- Slice 0015 Training Runs create non-user-facing Model Candidates only.
- Failed Training Runs do not create Model Candidates.
- Training Runs are immutable once terminal except for derived artifact availability.
- One queued/running local Training Run may exist at a time in Slice 0015.
- Real YOLO training should not run against the disposable test database by default.
- A terminal Training Run remains immutable after Contribution Withdrawal or Source Rights Invalidation, but its rights-impact summary identifies the affected evidence and its resulting model artifact cannot be used for new analysis or promotion.

### Model Candidate

A model or model pipeline version under evaluation before user-facing approval.

Essential fields:

- id
- human-readable id
- display name
- workspace id
- model purpose
- model family or service
- training run id
- adapter type
- artifact reference
- status
- promotion status
- scope-compatibility report
- not user-facing reason
- created at

Statuses:

- `created`
- `failed`
- `withdrawn`
- `quarantined`

Promotion statuses:

- `not_evaluated`
- `benchmark_pending`
- `approved_for_user_facing_analysis`
- `rejected`

Rules:

- A Model Candidate has one Model Purpose: Bee Localisation, Bee Orientation, or Varroa Detection. The existing Slice 0015 persisted/API value `bee_detector` means Bee Localisation and remains in place until a deliberate contract-evolution slice changes it.
- A Model Candidate becomes user-facing only after a Benchmark Evaluation for that Model Purpose and human approval of the relevant pipeline.
- User-facing deployment, sharing/publication, and commercial release each hard-block unless every Dataset Item used to train the candidate permits the relevant scope. The scope-compatibility report identifies the supporting Dataset Versions and any excluded or incompatible evidence.
- The Slice 0015 HiveSight Bee Detector baseline creates Bee Localisation Model Candidates with `promotion_status=not_evaluated`.
- A Model Candidate is not a Model Version.
- Fake-adapter Model Candidates must remain visibly fake/test-only and ineligible for real promotion.
- A Model Candidate affected by Contribution Withdrawal must be marked `withdrawn` and cannot be promoted or used for new analysis. A replacement requires a new Training Run using a Dataset Version that excludes the withdrawn contribution.
- A Model Candidate affected by Source Rights Invalidation must be marked `quarantined` and cannot be promoted or used for new analysis. A replacement requires a new Training Run using a Dataset Version that excludes the invalidated evidence.

### Model Version

A named version of the model or model pipeline.

Essential fields:

- id
- name
- version label
- pipeline description
- release status
- scope-compatibility report reference
- created at
- approved at
- retired at

Release statuses:

- `draft`
- `benchmark_pending`
- `approved_for_user_facing_analysis`
- `quarantined`
- `retired`
- `rejected`

Relationships:

- produces many analysis results
- has many benchmark evaluations

Rules:

- A Model Version affected by Contribution Withdrawal or Source Rights Invalidation transitions to `quarantined` and cannot be selected for new analysis. It may be replaced only by a Model Candidate trained and evaluated without the affected evidence.
- A Model Version retains the approved scope-compatibility report for every deployment, sharing/publication, or commercial release action.

### Benchmark Evaluation

A documented evaluation of one Model Candidate, for one Model Purpose, against one protected benchmark dataset version or selection snapshot.

Essential fields:

- id
- model candidate id
- model purpose
- dataset version id
- status
- model-purpose metrics summary
- quality-bucket metrics summary
- review agreement metrics summary
- reviewer decision id
- evaluated at

Rules:

- A user-facing pipeline requires documented benchmark evaluation for each constituent Model Purpose and human approval.
- A user-facing Varroa Assessment pipeline additionally requires its benchmark Varroa Review Outcomes to satisfy Blind Independent Review and Third-Party Adjudication of disagreements.
- A Varroa Benchmark Evaluation reports outcome agreement, one-to-one matched marker-location agreement in bee-relative coordinates, unmatched-marker counts, adjudication and unresolved-disagreement counts, and the number of benchmark items without independent second review.
- When a candidate relies on a Dataset Version with a quality-audit warning, its promotion record includes the Model Approver's explicit acknowledgement of the associated Audit Disposition.
- Fixed numeric promotion thresholds are deferred until baseline data exists.

### End-to-End Pipeline Evaluation

A documented evaluation of the composed Bee Localisation, Bee Orientation, and Varroa Detection pipeline against a separate protected full-frame selection snapshot with complete human-reviewed bee, Orientation Reliability, and relevant Varroa evidence.

Essential fields:

- id
- selected Model Candidate ids by Model Purpose
- protected full-frame benchmark dataset version or selection snapshot
- protected full-frame source group keys
- status
- end-to-end metrics summary
- stage coverage and failure summary
- reviewer decision id
- evaluated at

Rules:

- It complements rather than replaces constituent Model Purpose Benchmark Evaluations.
- A user-facing Varroa Assessment pipeline requires a documented End-to-End Pipeline Evaluation and human approval.
- Its predeclared full-frame selection plan and source groups are frozen before candidate selection or tuning.
- Its full-frame `source_group_key` values are disjoint from training, validation, and constituent Model Purpose benchmark evidence.
- Its full-frame evidence includes all visible Bee Annotations, their Orientation Reliability, and the relevant Varroa Review Outcomes, rather than only bees which reached the model's final stage.
- It reports localised-bee to Varroa-Assessment coverage, the count and proportion recorded as `not_assessed_orientation_unreliable`, and counts and proportions lost at each stage.
- It reports those measures separately for complete and partial visible bees; the initial user-facing Varroa estimate continues to use complete visible bees only.
- A user-facing Varroa estimate displays a coverage warning whenever any complete visible bee was not assessed for Varroa.
- Once an evidence-based coverage threshold is established, coverage below it suppresses the user-facing headline estimate.
- An inadequate-coverage result provides a route to review or correct the inspection. The reviewer may resolve previously unassessed complete visible bees and correct any model-produced bee, orientation, or Varroa decision. The original model-only result remains immutable; the recovery workflow calculates and shows a separate human-reviewed inspection result alongside it with explicit provenance. The human-reviewed result carries its own coverage and remains suppressed when an evidence-based coverage threshold is still not met. Resulting evidence is product feedback only until a Dataset Curator independently reviews it and assigns a Dataset Role. It is never automatic training evidence.
- It breaks coverage and errors down by Hive Configuration, bee-density, lighting, and image-quality strata, with sparse-group warnings.
- Fixed numeric promotion thresholds are deferred until baseline data exists.

### Varroa Sampling Plan

A versioned, predeclared protocol for selecting and interpreting bee-relative Varroa evidence.

Essential fields:

- id and methodology version
- purpose: `model_curation` or `inspection_rate_estimation`
- declared photographed-frame target population and sampling unit
- strata and allocation rule
- selection method and randomization seed or source
- inclusion and exclusion rules
- planned and achieved sample sizes
- stopping rule, if sequential
- estimator and uncertainty method
- operational decision thresholds, if any
- created or approved by and timestamps

Rules:

- A Model-Curation Sample may include both representative probability-selected and curator-targeted positive-enrichment streams; it must preserve which stream selected each item and is not an inspection prevalence sample.
- An Inspection-Rate Sample must retain every selected eligible bee, non-response or exclusion reason, and selection probability needed to reproduce its stated estimate.
- A Sampling Plan cannot be changed after its associated Dataset Version, End-to-End Pipeline Evaluation, or inspection result is frozen; a changed policy creates a new version.
- A sampling plan is scoped to photo-visible evidence and does not make a whole-hive or colony-level claim.

### Gold-Standard Full-Frame Corpus

A protected, methodology-versioned collection of whole-frame source images with full-depth source-frame annotation and review.

Essential fields:

- id and methodology version
- source-image and source-group membership
- source-frame identity and duplicate/overlap disposition
- full in-scope bee reconciliation record
- Orientation Reliability and Varroa Review Outcome coverage
- review and adjudication provenance
- stratum values and exclusions
- protected use designation

Rules:

- Every in-scope visible bee in a corpus frame is reconciled at source-frame level; crop-edge fragments must not be treated as independent physical bees.
- Every eligible complete bee has an explicit Varroa Review Outcome; `not_determined` remains visible and is not treated as a negative.
- The corpus supports end-to-end pipeline evaluation and sampling-plan experiments. It must be source-group disjoint from model development evidence whenever it supports user-facing promotion or estimator calibration.
- It is not a substitute name for a positive-enriched training dataset.

### Field Reference Measurement

An independently recorded hive or colony measurement, such as an alcohol-wash mite count, associated with an inspection for calibration research.

Rules:

- It records collection method, population, timing, sample size, units, and provenance.
- It is related calibration evidence, not the ground truth for photo-visible annotations or a direct replacement for a Visible Varroa Rate.

## Relationship Summary

- Workspace owns many apiaries.
- User has many workspace memberships.
- User may have many internal capabilities.
- Workspace has many workspace memberships.
- Workspace membership belongs to one user and one workspace.
- Internal capability belongs to one user.
- Apiary contains many hives.
- Hive has many inspections.
- Inspection contains many inspection photos.
- Inspection may define many frame labels.
- Frame label may group many inspection photos within one inspection.
- Inspection photo may have many analysis results.
- Source image may have many training crops.
- Inspection photo may be referenced by many training crops when the source image is an inspection photo.
- Analysis result belongs to exactly one model version.
- Analysis result has many bee annotations and Varroa annotations.
- Training crop may have many bee annotations.
- Varroa annotation may reference one bee annotation.
- User correction belongs to one inspection photo and may reference one annotation.
- Workspace data-use agreement belongs to one workspace and is accepted by an owner user in version one.
- Source Rights Record is referenced by one or more Source Images.
- Contributor Contribution Permission belongs to one contributor user and one named immutable Contribution Bundle in one workspace.
- Data deletion request belongs to one workspace.
- Review decision applies to one review subject.
- Dataset item references reviewed image and annotation evidence.
- Dataset version contains frozen snapshots of many dataset items.
- Training run uses one Dataset Version containing training, validation, protected benchmark metadata, and exclusions.
- Training run may produce one model candidate.
- Model candidate may become a model version after benchmark evaluation and human approval.
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

### Contributor Contribution Permission

- `not_accepted`
- `offered`
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
- Every internal capability belongs to exactly one user.
- Version one creates one default workspace and one owner workspace membership when a user registers.
- Version one exposes one active/default workspace per user in the UI.
- Every apiary belongs to exactly one workspace.
- Every hive belongs to exactly one apiary.
- Every inspection belongs to exactly one hive.
- Every inspection has exactly one intent.
- An inspection must not mix training data collection and Varroa assessment intents.
- Every inspection photo belongs to exactly one inspection.
- Every training crop belongs to exactly one source image.
- A training crop may reference one inspection photo when the source image is an inspection photo.
- Every accepted inspection photo has a preserved original file reference.
- Every analysis result belongs to exactly one inspection photo.
- Every analysis result records the model version that produced it.
- Every runtime annotation belongs to exactly one analysis result and one inspection photo.
- Every training crop annotation belongs to exactly one training crop and one inspection photo.
- Every user correction belongs to exactly one inspection photo.
- Every user correction records the user who created it once authentication exists.
- A user correction is never ground truth without review.
- A user correction is never training, validation, or benchmark data without an active Workspace Data Use Agreement, any applicable Contributor Contribution Permission, and review.
- A Candidate Annotation is never ground truth without human review.
- A Reviewed Annotation is never training, validation, or benchmark data without Dataset Role assignment.
- A reviewed bee annotation uses an oriented bee ellipse as its canonical geometry.
- YOLO OBB labels are derived training exports, not canonical annotation evidence.
- A Dataset Item must have exactly one Dataset Role.
- Benchmark Dataset Items must not be used for training or routine tuning.
- A Dataset Version includes only active reviewed Dataset Items as training or validation evidence.
- A Dataset Version freezes the metadata needed to explain a Training Run.
- A Dataset Version referenced by a Training Run is immutable.
- Marked oriented-bee Dataset Versions stay in lockstep across Bee Localisation and Bee Orientation; YOLO OBB labels and Head Up / Head Down crops are purpose-specific projections from the same promoted source evidence, not separate source dataset promotions.
- A Training Run creates a Model Candidate, not an approved Model Version.
- Bee Localisation, Bee Orientation, and Varroa Detection are separate Model Purposes.
- Bee Localisation does not establish biological head direction or assess Varroa evidence.
- Bee Orientation does not localise all bees or assess Varroa evidence.
- Varroa Detection consumes traceable bee-localisation and orientation evidence, with an explicit uncertainty/fallback outcome when orientation is not reliable.
- A positive Varroa Detection includes explicit mite location; bee-level presence/absence alone is insufficient for the first Varroa capability.
- In the first live Varroa pipeline, a localised bee with unreliable orientation is recorded as `not_assessed_orientation_unreliable`; it is not a negative Varroa result and the detector does not run on a guessed rotation.
- The first head-normalized Varroa training and benchmark corpora exclude bees with unreliable orientation; those bees remain eligible for Bee Localisation evidence and supplementary Varroa evidence.
- The first Varroa training and benchmark datasets include human-selected bee crops independent of upstream model output; they must not be assembled solely from localised/oriented model proposals.
- The first Bee Orientation training and benchmark corpora include only reliably oriented complete visible bees; reliably oriented partial bees are retained for later separately reported evaluation.
- Workspace ownership does not grant internal dataset/model governance capability.
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
- exact deletion/purge timing and any legal-retention exception for withdrawn source assets and model artifacts
- what regulatory obligations apply to inspection photos and metadata

## Traceability

- `User`, `Workspace`, and `Workspace Membership` support registration, authorization, and FR-017.
- `Internal Capability` and `Dataset Curator` support the AI-assisted annotation baseline's dataset/model governance actor model.
- `Apiary` supports FR-001.
- `Hive` supports FR-002.
- `Inspection` supports FR-003.
- `Inspection Photo` supports FR-004 and FR-013.
- `Training Crop` supports the bee annotation repository and curriculum training baseline.
- `Frame Label` supports FR-005.
- `Bee Annotation` and `Analysis Result` support FR-006 and MR-001.
- Oriented bee ellipse geometry supports MR-008, MR-008A, MR-001A, ADR-0002, and ADR-0006.
- `Varroa Annotation` and `Analysis Result` support FR-007 and MR-002.
- `Inspection Summary` supports FR-008.
- `Tagged Photo` rendering supports FR-009, FR-010, and FR-011.
- `User Correction` and `Review Decision` support FR-012 and MR-013 to MR-014.
- `Workspace Data Use Agreement` and `Contributor Contribution Permission` support FR-016, FR-019, MR-017H, and MR-019 to MR-023 as revised by the domain decision.
- `Data Deletion Request` captures the deferred deletion/privacy gap.
- Upload status supports FR-018 and NFR-006.
- `Model Version` supports MR-028.
- `Dataset Item` supports MR-017, MR-017A, and the AI-assisted annotation baseline.
- `Candidate Annotation` supports AI-assisted annotation while preserving human review as the trust boundary.
- `Dataset Version` supports MR-017, MR-017F, MR-029, and Slice 0015 Training Run governance.
- `Training Run` and `Model Candidate` support MR-029A, MR-029B, the three Model Purposes, and the AI-assisted annotation baseline.
- `Benchmark Evaluation` supports MR-030 and MR-031.

## Open Architecture Questions

- What exact registration and default workspace creation flow should version one use?
- What future workspace roles and invitation lifecycle are needed after version one?
- Should inspection summaries be stored snapshots, calculated on demand, or both?
- Should photo analysis run synchronously for a prototype or always as a background job?
- Where should original inspection photos be stored?
- What initial image formats and upload size limits should be configured?
- What should the workspace data-use agreement say, and how should accepted terms versions be tracked?
- What exact deletion/purge timing and legal-retention exceptions apply to withdrawn source assets and model artifacts?
- What data deletion or purge workflow is required before production use?
- Are uploaded photos and inspection metadata legally or operationally personally identifiable or sensitive in the target markets?
- Should frame labels affect v1 aggregation, or only provide warning context?
- How should duplicate or near-duplicate inspection photos be detected?
- What is the first model integration style: local model, hosted model service, or manual/mock analysis?
- What annotation or review interface should be used for first ground-truth creation?
- Should review decisions happen in the beekeeper UI, a reviewer/admin UI, or external tooling?
- Should older photos be re-analysed by newer model versions, and how should superseded results be shown?
