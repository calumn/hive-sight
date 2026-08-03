# AI-Assisted Annotation And Model Training Baseline

## Purpose

HiveSight's product viability depends on whether the system can reliably identify bees and likely Varroa mites in real inspection photos. Before building a real recognition model, the project needs a practical way to create, review, split, train from, and evaluate labelled image data.

This baseline defines the initial requirements for AI-assisted annotation, reviewed dataset creation, dataset role assignment, model training, model evaluation, and model candidate selection. It complements `requirements/model-requirements.md` and is refined by `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`; it does not replace the beekeeper-facing product specification.

## Core Principle

The project may use AI to accelerate annotation, but AI-generated labels are never trusted ground truth by themselves.

The intended bootstrap loop is:

```text
original inspection photo
-> Candidate Annotations
-> human review and correction
-> reviewed annotations
-> dataset role assignment
-> dataset version
-> training / validation / benchmark evaluation
-> model candidate comparison
-> approved model version
```

The same visual UI components may be reused across annotation labelling, reviewer workflows, and product correction workflows. The data provenance and dataset-governance records must remain separate.

After the Grounding DINO pre-labelling spike, the intended bee bootstrap path is to build a HiveSight-owned trainable Bee Localisation Model from reviewed HiveSight data. Grounding DINO is retired from the active solution by ADR 0005.

## Terminology

**Candidate Annotation**:
A proposed Annotation awaiting human review. It may come from a model candidate, imported public dataset, previous draft, or future helper.

**Draft Annotation**:
A historical or implementation-facing term for a proposed Annotation before human review. Prefer Candidate Annotation in new product, architecture, and API language.

**Reviewed Annotation**:
An Annotation that has a human Review Decision accepting it for its current annotation type and geometry. A Reviewed Annotation is review evidence, but it still requires Dataset Role assignment before it is part of training, validation, or benchmark data.

**Annotation Source**:
The provenance of an Annotation or Candidate Annotation, such as `human_from_scratch`, `model_candidate`, `imported_public_dataset`, `user_correction`, or `reviewer_correction`.

**Review Method**:
How reviewed annotation evidence was produced, such as `human_from_scratch`, `human_reviewed_candidate`, or `imported_reviewed`.

**Dataset Item**:
A reviewed image/annotation unit that has been assigned a Dataset Role and may be included in a Dataset Version.

**Dataset Selection Method**:
Why an item was selected for a dataset: `human_selected` means selection before the curator sees upstream model suggestions, while `upstream_model_selected` means a model influenced selection. This is distinct from Annotation Source and Review Method.

**Sampling Purpose**:
The statistical purpose of Varroa review selection: `model_curation` builds representative model evidence, while `inspection_rate_estimation` supports a future stated rate estimate. It is distinct from Dataset Role.

**Sampling Method**:
How a Varroa review was selected within its Sampling Purpose. The first model-curation methods are `stratified_random` and `curator_targeted` for deliberately added difficult examples.

**Training Run**:
A recorded execution that trains or fine-tunes one model candidate using one or more Dataset Versions and training settings.

**Model Candidate**:
A model version or pipeline version under evaluation before it is approved for user-facing analysis.

**Bee Localisation Model**:
The model purpose that finds visible bees and estimates body geometry. The first HiveSight Bee Detector baseline implements this purpose only.

**Bee Orientation Model**:
The model purpose that resolves a localised bee's directed centre-to-head orientation from its visual evidence.

**Varroa Detector**:
The model purpose that identifies likely visible Varroa evidence on a bee-relative crop, normally normalized to head direction.

**Dataset Curator**:
A registered User with internal dataset/model governance capability who can perform dataset labelling, annotation review, dataset role assignment, and model-governance work.

**Internal Capability**:
An authorization grant separate from ordinary Workspace Membership, used for internal workflows such as annotation review, dataset curation, model review, and model approval.

## Workflow Requirements

### AIA-001 AI-Assisted Annotation Bootstrap

The system should support creating Candidate Annotations for original inspection photos using an AI-assisted pre-labelling mechanism.

Rationale: Manually drawing every bee and Varroa label from scratch is too slow for building the first useful dataset.

### AIA-002 Human Review Required

Candidate Annotations shall require human review, correction, or rejection before they become Reviewed Annotations.

Rationale: AI-assisted pre-labelling accelerates data creation but must not become ground truth without human judgement.

### AIA-003 Original Images Remain The Training Input

Training, validation, and benchmark workflows shall use original images plus structured annotation data, not images with visual overlays burned into the pixels.

Rationale: Overlay-rendered images are for human review. Training on overlay pixels would teach the model the wrong signal.

### AIA-004 Annotation Corrections

The annotation workflow should let a reviewer approve, reject, mark uncertain, exclude, add, remove, and adjust annotation geometry before data is eligible for dataset use.

For each reviewed Bee Annotation, the workflow shall also record Orientation Reliability as `reliable` or `unreliable`, independently of whether the bee itself is a complete or partial visible bee.

Rationale: A useful bootstrap workflow must fix both false positives and missed objects, not only approve existing draft boxes.

### AIA-005 Bee-First Bootstrap

The first AI-assisted annotation workflow should focus on bee localisation before Bee Orientation and Varroa identification.

Rationale: Bee localisation is the denominator and the immediate first model viability question. Directed reviewed ellipses then supply the evidence needed for orientation learning, while Varroa detection can build on normalized bee crops without conflating the three tasks.

The first baseline should label complete visible bees and partial visible bees. `uncertain_bee` remains required by the model requirements, but may be deferred from the first implementation slice if needed.

### AIA-006 Distinct Labelling And Product Feedback Workflows

The system shall distinguish internal dataset-labelling workflows from beekeeper product feedback workflows, even if they reuse UI components.

Rationale: Initial dataset creation and real-user correction feedback have different actors, incentives, provenance, and statistical meaning.

### AIA-007 Provenance Required

Every Candidate Annotation, Reviewed Annotation, Dataset Item, Dataset Version, Training Run, Model Candidate, and Benchmark Evaluation shall preserve provenance sufficient to explain where it came from and how it was used.

Varroa Dataset Items shall additionally preserve Dataset Selection Method, and Varroa benchmark reports shall show its distribution.

Rationale: Model quality claims are only meaningful when data lineage is traceable.

### AIA-007A Dataset Actor And Authorization

Dataset labelling, dataset role assignment, Training Run review, Model Candidate review, and model approval shall be performed by registered Users with explicit internal capabilities.

Rationale: The project needs one auditable identity model while keeping dataset/model governance permissions separate from ordinary beekeeper Workspace Membership.

### AIA-007B Workspace Ownership Is Not Dataset Authority

Workspace ownership shall not automatically grant dataset/model governance capability.

Rationale: A beekeeper may own inspection data without being authorized to curate benchmark data, approve Dataset Versions, or promote model candidates.

### AIA-007C Contributor Contribution Permission

Where a Dataset Item contains an identified external contributor's image, annotation, or review work, HiveSight shall retain a separate active Contributor Contribution Permission for that contribution as well as the Workspace Data Use Agreement for the underlying workspace evidence.

Contributor permission shall follow these rules:

- Each Contributor Contribution Permission records an explicit, closed set of Permitted Use Scopes, such as model development, evaluation, user-facing deployment, sharing/publication, and commercial use. An unlisted scope is not permitted.
- The first contributor terms offer model development and evaluation only. User-facing deployment, sharing/publication, and commercial use require separate explicit opt-in.
- One permission covers one named, immutable Contribution Bundle, such as a contributor's named set of reviewed frames. Every included Dataset Item retains the bundle reference.
- A Dataset Curator creates Contribution Bundles and assigns their annotation tasks. The Workspace owner may offer their own evidence for curation but does not gain contributor-task or dataset-governance authority through ownership alone.
- Before acceptance, HiveSight shows the contributor only a non-sensitive bundle summary and the applicable terms. Assigned images and annotation tasks are not visible until the contributor explicitly accepts that named bundle and terms version.
- A material change to contributor terms requires fresh acceptance before the bundle can appear in any new Dataset Version, Training Run, Benchmark Evaluation, or promotion. Historical lineage remains available for audit.
- Re-acceptance after withdrawal creates a new permission record for future use only and never automatically unquarantines prior Dataset Versions or model artifacts.
- Each contributor has a registered, pseudonymous HiveSight identity through which they can view their own bundles, withdraw permission, request deletion, and view a read-only Contribution Usage Record showing accepted terms, current status, and linked Dataset Versions, Training Runs, and model-artifact outcomes.
- HiveSight retains only the minimum contact/authentication data necessary for the contributor control path. Contribution provenance and curator-facing views use the internal contributor id and selected pseudonym, not a required real name.
- Contributor views do not reveal other contributors' evidence or the wider Workspace. Registration does not grant Workspace Membership or dataset/model-governance capability.
- Contributor access is limited to explicitly assigned annotation tasks and Contribution Bundles, never the wider Workspace, unassigned inspections, or other contributors' evidence.
- Withdrawal or a contributor deletion request immediately revokes access to every unfinished task in the bundle. HiveSight retains only the minimal audit record of unfinished work needed to explain the request and affected lineage.
- In the first release, withdrawal applies to the complete bundle. Contributors create separate bundles before acceptance when they need finer withdrawal boundaries.
- A contributor may withdraw their own permission without becoming a Workspace owner or dataset curator.

Rationale: A helper needs meaningful control over their own contribution without controlling the beekeeper's workspace or other contributors' evidence.

### AIA-007D Source Rights And Licence Provenance

HiveSight shall record a Source Rights Record for every Source Image used for model data. Public or open-source evidence shall identify its source organisation or repository, source reference, licence or terms version, allowed-use basis, attribution requirement, and any restriction review. A Dataset Curator shall explicitly review and approve the Source Rights Record before a related image can become a Dataset Item. Required attribution shall be carried into every relevant Dataset Version, derived export, evaluation report, and released model documentation. This route is separate from a Contributor Contribution Permission. Imported annotation provenance shall remain separate from the rights record for the underlying image.

Rationale: A public/open licence, a Workspace Data Use Agreement, and a contributor's permission are distinct rights routes and must not be represented as the same thing.

Public/open evidence is permitted for local research and model development only unless its reviewed Source Rights Record explicitly permits a broader scope. Formal licence-compatibility review for sharing, publication, commercial use, model-output obligations, or user-facing deployment is parked in PARK-0035.

## Dataset Requirements

### AIA-008 Dataset Role Assignment

Reviewed Annotations shall not enter model training, validation, or benchmark evaluation until they are assigned an explicit Dataset Role.

Allowed Dataset Roles:

- `training`
- `validation`
- `benchmark`
- `excluded`

Rationale: Review approval and dataset eligibility are separate decisions.

### AIA-009 Dataset Split Separation

Training, validation, and benchmark Dataset Items shall be kept logically separate.

Rationale: The project needs a training set for learning, a validation set for development/tuning, and a protected benchmark set for honest evaluation.

For the first implementation, Dataset Role assignment may happen at photo/Dataset Item level. Before serious benchmark claims, the project must address frame-level, near-duplicate, inspection-level, hive-level, or source-level leakage.

### AIA-010 Protected Benchmark

Benchmark Dataset Items shall be selected from a predeclared sampling plan and frozen before the evaluated Model Candidate is run against them. They shall not be used for model training, routine tuning, prompt iteration, threshold adjustment, or pre-labelling quality optimisation, and no item may be added because that candidate succeeded or failed on it.

Early baseline benchmark Varroa Review Outcomes may have one active curator review, but reports shall state that limitation. Before a Model Candidate is considered for user-facing Varroa Assessment, benchmark Varroa Review Outcomes require Blind Independent Review: the second reviewer must not see the first outcome or Varroa marker positions. Disagreements require Third-Party Adjudication: a distinct adjudicator first records a fresh blind review, then may inspect anonymised prior reviews to document the final outcome. An unresolved disagreement, including a three-way conflict, becomes `not_determined` and is excluded from Varroa training and benchmark evidence. Training and validation Varroa evidence may use one active reviewed outcome with retained review provenance.

Every Varroa Benchmark Evaluation shall report outcome agreement, marker-location agreement, adjudication and unresolved-disagreement counts, and how many benchmark items lack independent second review. Marker-location agreement uses one-to-one matched markers in bee-relative coordinates normalized to the reviewed bee body; unmatched markers are reported separately. Numerical pass/fail thresholds remain deferred until sufficient project evidence exists.

A separate, non-blocking quality audit shall periodically select a stratified-random sample of training and validation Varroa Reviews for Blind Independent Review. It shall retain selection and review provenance and report agreement, disagreement, and unresolved outcomes separately from protected benchmark evidence and separately by Annotation Source, including human-from-scratch and AI-assisted-reviewed evidence. A concerning audit result requires a documented Dataset Curator Audit Disposition and a warning on every affected Dataset Version; it does not automatically block dataset use while sample size and escalation thresholds remain deferred.

Rationale: Benchmark leakage would make model progress look better than it really is.

### AIA-011 Duplicate And Near-Duplicate Handling

The project shall define how duplicate or near-duplicate inspection photos are detected or grouped before dataset split assignment.

Rationale: Similar images of the same frame can leak information across training, validation, and benchmark splits.

### AIA-012 Dataset Versioning

Any dataset used for a Training Run or Benchmark Evaluation shall be recorded as a Dataset Version.

Rationale: Model comparisons are only meaningful when the exact dataset inputs are known.

Dataset Versions used for Training Runs shall freeze included Dataset Item ids and key explanatory metadata so historical Training Runs do not change when source evidence is later corrected, withdrawn, superseded, or reclassified.

### AIA-013 Dataset Exclusion Reasons

Excluded Dataset Items should record a reason such as poor image quality, ambiguous subject, duplicate image, privacy concern, unsuitable crop, or insufficient review confidence.

Rationale: Exclusion reasons help improve collection guidance and avoid silently discarding hard cases.

### AIA-013A Lightweight Image Quality Status

The first dataset workflow should record a lightweight image quality status such as `usable`, `poor_quality`, or `exclude`.

Rationale: Early model results need to be interpreted against image quality without requiring a full quality taxonomy from day one.

## Model Training Requirements

### AIA-014 First Model Family Decision Required

Before implementing real training, the project shall choose an initial model approach for object detection.

Candidate approaches may include:

- a local open-source object detector trained on reviewed HiveSight data
- a hosted labelling/training platform
- a general-purpose vision model used only for pre-labelling
- a hybrid approach that starts hosted/manual and later moves local

Rationale: Tool choice affects annotation format, dataset export, training workflow, cost, privacy, and repeatability.

Decision: the first bee detector baseline should use oriented object detection, with Ultralytics YOLO OBB nano or small as the first implementation candidate.

Decision update: Grounding DINO is retired from the active solution. YOLO OBB is the first HiveSight-owned Bee Detector baseline implementation candidate, behind a replaceable model-training adapter seam.

### AIA-014A Canonical Bee Geometry

Reviewed bee annotations shall use oriented bee ellipses as the canonical domain geometry.

Rationale: Bees are elongated and appear at many angles on a frame. Oriented ellipses better match human evidence than axis-aligned rectangles.

### AIA-014B Model-Specific Export Projection

The first YOLO OBB training baseline shall consume a model-specific export projection derived from reviewed oriented bee ellipses.

Rationale: YOLO OBB expects oriented bounding boxes. HiveSight should support that format without making it the canonical reviewed annotation shape or assuming it preserves directed head/tail meaning.

### AIA-014D Three Logical Model Purposes

HiveSight shall preserve separate Bee Localisation, Bee Orientation, and Varroa Detection model purposes. The first implementation may use separate model artifacts; a later combined implementation is permitted only if it continues to expose and evaluate each purpose independently.

Rationale: Localising a bee, resolving its head/tail direction, and identifying a tiny mite on a normalized bee crop have different labels, error modes, data density, and evaluation needs.

### AIA-014E Orientation Baseline Deferred

Once sufficient reviewed directed ellipses exist, the first Bee Orientation baseline shall use a binary head/tail classifier on body-axis-normalized crops. A keypoint/pose or multi-head localisation model remains a later alternative if benchmark evidence shows the classifier is inadequate.

Rationale: Standard YOLO OBB geometry can recover a body axis but not reliable biological head direction. The project should not choose an orientation architecture before it has enough directed review evidence to test the choice.

For the first head-normalized Varroa training and benchmark corpora, bees with unreliable orientation are excluded rather than assigned an invented direction. They remain useful Bee Localisation evidence and may retain separately reported Varroa evidence.

In the first live Varroa pipeline, a localised bee with unreliable orientation is recorded as `not_assessed_orientation_unreliable`; the detector does not run on a guessed rotation.

The first Bee Orientation training and benchmark corpora include only reliably oriented `complete_visible_bee` annotations. Reliably oriented partial bees remain retained evidence for a later, separately reported evaluation.

### AIA-014F Varroa Location Evidence

The first Varroa baseline shall use high-resolution, standard axis-aligned YOLO detection on head-normalized bee crops. It shall produce explicit mite locations, not only bee-level presence/absence classifications. Its training evidence shall use reviewed Varroa point markers or tight bounding boxes. Oriented mite boxes and segmentation are deferred.

Its training and benchmark datasets shall include human-selected bee crops independent of upstream model outputs, so the Varroa baseline does not inherit Bee Localisation or Bee Orientation blind spots by construction.

Every bee-relative crop reviewed for Varroa evidence shall record `visible_varroa_present`, `no_visible_varroa`, or `not_determined`. The intended curator workflow is CAPTCHA-like: the curator actively marks each crop as containing one or more visible mites, containing no visible mite, or not determinable. Only the first two outcomes may form positive/negative Varroa training and benchmark evidence.

The same review UI may serve `model_curation` and future `inspection_rate_estimation` sampling, but the selected crop set and its records must preserve the Sampling Purpose. Only model-curation records are eligible for model Dataset Roles unless explicitly reviewed and reassigned later.

The default `model_curation` method shall be `stratified_random` across available Hive, frame, bee-density, lighting, and image-quality strata. Curators may add deliberately difficult examples as `curator_targeted`; Dataset Versions and benchmark reports shall preserve the resulting method and stratum distributions.

Rationale: A visible location is needed for curator review, host-bee association, error analysis, and honest user-facing evidence.

### AIA-014C Curriculum Crop Bootstrap

The first bee training dataset should start from reviewed Training Crops before moving to larger regions and full frame sides.

Initial stages:

- `small_crop`
- `medium_crop`
- `large_crop`
- `full_frame_region`
- `full_frame_side`

Rationale: Small crops with a few bees are faster to review completely and give the first trainable detector a cleaner learning path.

### AIA-015 Training Run Records

Every Training Run shall record the dataset versions, model candidate, training settings, code/artifact reference, start/end time, and outcome.

Rationale: Repeatability and comparison require more than a final model file.

At minimum, a Training Run should record dataset version ids, model family or service, training settings summary, code/artifact reference, random seed where applicable, start/end time, and outcome summary.

For the YOLO OBB baseline, Training Runs should also record model purpose, adapter type, database purpose, base weights, base weight source, artifact manifest, environment summary, git state, warning acknowledgement, metrics, and failure details.

### AIA-016 Model Candidate Records

Every trained or configured candidate model shall be recorded as a Model Candidate before it is eligible for benchmark evaluation or promotion.

Rationale: Candidate tracking keeps experimental models separate from approved user-facing models.

### AIA-017 Separate Localisation, Orientation, And Varroa Evaluation

Bee Localisation, Bee Orientation, and Varroa Detection shall be evaluated separately.

Rationale: The three tasks have different labels, ambiguity, data density, metrics, and product consequences.

### AIA-018 Baseline Before Optimisation

The first model work should establish a baseline result before heavy optimisation.

Rationale: The project needs to learn whether the approach is viable before investing in extensive tuning.

Fixed numeric success thresholds are deferred until labelled seed data exists. The first baseline is for measurement and viability learning.

## Evaluation Requirements

### AIA-019 Validation During Development

Validation data may be used during model development to compare candidates and tune model settings.

Rationale: Validation feedback is necessary for practical model development, but it is not the final honest exam.

### AIA-020 Benchmark Evaluation For Promotion

A Model Candidate shall pass a documented Benchmark Evaluation before it becomes an approved user-facing Model Version.

Promotion shall hard-block unless every Dataset Item used to train the candidate permits `user_facing_deployment`. Sharing/publication and commercial release shall each hard-block unless every training Dataset Item permits the relevant scope. Each release record shall include a scope-compatibility report that identifies the supporting Dataset Versions and any excluded or incompatible evidence.

Where the candidate relies on a Dataset Version with a quality-audit warning, the Model Approver shall explicitly acknowledge the associated Audit Disposition in the promotion record.

A user-facing Varroa assessment pipeline shall additionally pass a documented End-to-End Pipeline Evaluation on a separate protected full-frame selection snapshot; this complements rather than replaces its constituent model benchmarks. Its predeclared selection plan and source groups must be frozen before candidate selection or tuning. Its `source_group_key` values must be disjoint from training, validation, and component benchmark evidence. Its full-frame evidence must include complete human-reviewed labels for all visible bees, their Orientation Reliability, and the relevant Varroa Review Outcomes. The report shall show localised-bee to Varroa-Assessment coverage, `not_assessed_orientation_unreliable` coverage, and losses at each stage, separately for complete and partial visible bees, and broken down by Hive Configuration, bee-density, lighting, and image-quality strata with sparse-group warnings. The initial user-facing Varroa estimate continues to use complete visible bees only and displays a coverage warning whenever any complete visible bee was not assessed for Varroa. Once an evidence-based coverage threshold is established, coverage below it suppresses the headline estimate.

An inadequate-coverage result shall provide a route for the Workspace owner to open an Inspection Recovery Review: a distinct, named, saveable, and resumable review session linked to a fixed snapshot of the original model-only result and its photo evidence. This inspection-support route remains available after Workspace Data Use Agreement withdrawal when the inspection is retained, but its evidence is ineligible for model improvement without an active agreement and independent curation. Newer models are not run or substituted during recovery. Every resulting annotation and Varroa decision retains recovery-review provenance and is reported as AI-assisted-reviewed, never human-from-scratch, because the original model output was visible. Model promotion never automatically reanalyses historical Inspection Photos; a future explicit Historical Reanalysis creates a new model-only result without altering prior model-only or human-reviewed results. In the first release the recovery review is available only for a suppressed model-only result, not for every completed inspection, and only the Workspace owner may create, resume, or complete it. The owner may complete it at any coverage level after explicit confirmation, including when the headline rate remains suppressed. Once completed, the review and its result are immutable; a later correction creates a new linked review and human-reviewed result revision. The latest completed human-reviewed result becomes the inspection's current result by default, while the original model-only result and earlier human-reviewed revisions remain available as labelled comparison history. The reviewer may resolve previously unassessed complete visible bees and correct any model-produced bee, orientation, or Varroa decision. The original model-only result remains immutable and the recovery workflow calculates and shows a separate human-reviewed inspection result alongside it with explicit provenance. Both results show a Result Evidence Breakdown: positive, active negative, `not_determined`, and unassessed complete visible-bee counts, plus Review Completion and Determinate Varroa Coverage. An explicit `not_determined` outcome counts toward Review Completion but not Determinate Varroa Coverage or a headline rate, and the result remains suppressed when an evidence-based determinate-coverage threshold is still not met. That product feedback remains product feedback only until a Dataset Curator independently reviews it and assigns a Dataset Role; it is never automatic training evidence.

Rationale: User-facing estimates require evidence from protected data.

Recovery evidence created while the Workspace Data Use Agreement is withdrawn remains product-only. A later agreement acceptance is prospective and does not itself make that evidence eligible for model improvement; the Workspace owner must make a separate explicit dataset-contribution decision, followed by independent Dataset Curator review and Dataset Role assignment.

Each Dataset Contribution Decision applies to exactly one named completed Human-Reviewed Inspection Result revision, records the owner, decision time, result revision, and current Workspace Data Use Agreement, and is not a workspace-wide opt-in or Dataset Role assignment.

When a contributor withdraws permission for training use, affected Dataset Items are withdrawn from future exports, Dataset Versions, Training Runs, Benchmark Evaluations, and promotion. Historical manifests and run records remain for audit, but affected Dataset Versions and model artifacts are quarantined. A replacement must be trained from a new Dataset Version that excludes the withdrawn contribution before model use resumes.

### AIA-021 Metrics Must Be Task-Specific

Evaluation shall report task-specific metrics rather than a single generic accuracy number.

Initial bee metrics may include:

- complete visible bee detection precision
- complete visible bee detection recall
- partial visible bee detection precision
- partial visible bee detection recall
- complete visible bee count error
- performance by image-quality bucket

Initial orientation metrics may include:

- directed head/tail accuracy
- angular error against human-reviewed direction
- coverage and explicit unreliable-orientation rate
- complete versus partial visible bee performance

Initial Varroa metrics may include:

- likely Varroa detection precision
- likely Varroa detection recall
- false positives per image
- false negatives per image
- association accuracy to complete, partial, or unassociated states
- performance by image-quality bucket

Rationale: A single score would hide the failure modes that matter to the product.

### AIA-022 Human Promotion Decision

A human reviewer shall approve a Model Candidate before it becomes user-facing.

Rationale: Early model promotion needs judgement as well as metrics.

## Statistical And Governance Risks

The requirements shall explicitly guard against:

- using AI-generated draft labels as ground truth without human review
- automation bias from human reviewers approving candidate annotations without enough human-from-scratch or blind-review comparison evidence
- training on benchmark items
- tuning prompts, thresholds, or model settings against benchmark items
- using the same frame or near-duplicate images across train/validation/benchmark splits
- evaluating a model on photos that influenced its training
- treating ordinary beekeeper corrections as trusted labels without review
- hiding low-quality or excluded examples in a way that makes model performance look artificially strong
- using user-submitted photos for model improvement without accepted terms and review

## Initial Dataset Strategy

The first practical dataset target may be small, for example around 100 brood-frame or inspection-frame photos, but the dataset should be treated as a structured seed dataset rather than an informal folder of images.

The first seed dataset should use project-owned photos only. Public or externally sourced images are deferred until licensing, provenance, and domain-match questions are resolved.

The workflow must support incremental dataset build-up. It should work with one photo, then a small seed set, then grow toward the initial target rather than requiring all target photos before tooling can be useful.

For the first bee-detection baseline, the project should aim to know:

- how many photos were reviewed
- how many complete visible bees were labelled
- how many partial visible bees were labelled
- how many photos were excluded and why
- how the dataset was split
- which pre-labelling mechanism was used, if any
- which review method was used
- who reviewed the annotations
- which internal capability authorized the reviewer or Dataset Curator
- which Dataset Version was used for each Training Run
- which Dataset Version was protected as benchmark

## Relationship To Product Feedback

Beekeeper product feedback remains valuable but is not the same as initial dataset labelling.

Product feedback:

- occurs during normal inspection-result review
- is created by a Beekeeper/User
- starts as a User Correction or product Review Decision
- may be noisy or partial
- requires review before dataset use

Dataset labelling:

- occurs in an internal annotation workflow
- is performed by a Dataset Curator or reviewer with internal capability
- may use Candidate Annotations
- aims to produce complete reviewed labels for selected photos
- can be assigned to training, validation, benchmark, or excluded roles

## Decisions From Baseline Review

- The first AI-assisted annotation/model baseline is bee-only.
- The initial dataset uses project-owned inspection/frame photos only.
- The initial target is about 100 project-owned frame photos, but the workflow must support incremental growth before all 100 exist.
- The first implementation may use deterministic or manually created Candidate Annotations, with a replaceable candidate-generation seam.
- Geometry adjustment, adding missed bees, and removing incorrect boxes are required for the complete workflow, but may be deferred from the first thin implementation slice.
- Initial Dataset Role assignment may happen at photo/Dataset Item level, with duplicate/frame leakage tracked as a follow-on risk before serious benchmark claims.
- Early benchmark Varroa items may have one active human review, but this limitation must be reported. User-facing Varroa Assessment promotion requires Blind Independent Review and Third-Party Adjudication of benchmark disagreements.
- HiveSight's canonical annotation storage starts as internal normalized JSON. YOLO OBB is the first selected derived export format for the Bee Detector baseline.
- Dataset Role assignment is a separate curation step after annotation review.
- Reviewers should visibly know when annotations are Candidate Annotations.
- Benchmark items may originate from Candidate Annotations if human reviewed and provenance is preserved.
- `uncertain_bee` remains a required concept, but may be deferred from the first implementation slice. The gap should be recorded with an acceptance scenario and later executable pending coverage.
- Reviewed directed ellipse orientation is retained as future Bee Orientation training evidence; YOLO OBB output remains Bee Localisation geometry rather than head-direction evidence.
- Orientation Reliability is reviewed evidence with values `reliable` or `unreliable`; it is distinct from bee-presence confidence and review status.
- Existing directed ellipses require a one-time human Orientation Reliability review before they may enter Bee Orientation or head-normalized Varroa Dataset Versions.
- HiveSight's target pipeline has three logical model purposes: Bee Localisation, Bee Orientation, and Varroa Detection. The current YOLO OBB baseline implements Bee Localisation only.
- Dataset-labelling review and product model-output review require separate workflow/provenance types.
- Training Runs record reproducibility metadata including dataset versions, model family/service, settings, code/artifact reference, random seed where applicable, timing, and outcome.
- Metadata minimisation, including EXIF stripping, is required before hosted pre-labelling, hosted training, sharing, or publication.
- Hosted AI, annotation, or training services are allowed only after an explicit tool/privacy/cost decision.
- The first bee baseline measures object detection quality only, not downstream Visible Varroa Rate.
- The first dataset workflow records lightweight image quality status.
- Numeric success thresholds are deferred until labelled seed data exists.
- Complete visible bees and partial visible bees are both included in the first bee baseline.
- External annotation-tool import/export is a first-class requirement after the first tool/model path is chosen.
- Annotation-level review provenance is required where practical.
- Optional review notes with a 500-character maximum apply to dataset annotation review.
- The Dataset Curator is a registered User with internal dataset/model governance capability, not a separate identity system.
- Internal capabilities are separate from ordinary Workspace Membership roles.
- Grounding DINO is retired from the active solution after poor brood-frame bee localisation results.
- The first trainable Bee Detector baseline uses YOLO OBB as a replaceable implementation candidate.
- The first Bee Detector Training Run creates a non-user-facing Model Candidate only; model promotion and product inference are later work.
- Automation-bias risk must be visible in reports when reviewed evidence lacks human-from-scratch or blind-review comparison.

## Open Questions

- Should the first annotation tool be built inside HiveSight or should the project integrate/export to an existing tool first?
- What minimum size should the first bee-detection benchmark set have?
- Should dataset splits happen at photo level, frame label level, inspection level, hive level, or workspace/source level?
- What image metadata must be stripped before training or sharing?
- What quality bar is enough to prove bee-detection viability?
- How should the project handle Varroa labels if the first slice is bee-only?
- What cost/privacy constraints apply if a hosted AI or annotation service is used for pre-labelling?
- What blind-review sample size is enough to measure automation bias?
- What benchmark result or operational failure would justify replacing the first binary head/tail classifier with a keypoint/pose or multi-head orientation model?
