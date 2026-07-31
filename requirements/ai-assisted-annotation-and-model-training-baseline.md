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

After the Grounding DINO pre-labelling spike, the intended bee bootstrap path is to build a HiveSight-owned trainable Bee Detector from reviewed HiveSight data. Grounding DINO is retired from the active solution by ADR 0005.

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

**Training Run**:
A recorded execution that trains or fine-tunes one model candidate using one or more Dataset Versions and training settings.

**Model Candidate**:
A model version or pipeline version under evaluation before it is approved for user-facing analysis.

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

Rationale: A useful bootstrap workflow must fix both false positives and missed objects, not only approve existing draft boxes.

### AIA-005 Bee-First Bootstrap

The first AI-assisted annotation workflow should focus on bee identification before Varroa identification.

Rationale: Bee detection is the denominator and is the more immediate first model viability question. Varroa detection can build on the bee-detection dataset and workflow.

The first baseline should label complete visible bees and partial visible bees. `uncertain_bee` remains required by the model requirements, but may be deferred from the first implementation slice if needed.

### AIA-006 Distinct Labelling And Product Feedback Workflows

The system shall distinguish internal dataset-labelling workflows from beekeeper product feedback workflows, even if they reuse UI components.

Rationale: Initial dataset creation and real-user correction feedback have different actors, incentives, provenance, and statistical meaning.

### AIA-007 Provenance Required

Every Candidate Annotation, Reviewed Annotation, Dataset Item, Dataset Version, Training Run, Model Candidate, and Benchmark Evaluation shall preserve provenance sufficient to explain where it came from and how it was used.

Rationale: Model quality claims are only meaningful when data lineage is traceable.

### AIA-007A Dataset Actor And Authorization

Dataset labelling, dataset role assignment, Training Run review, Model Candidate review, and model approval shall be performed by registered Users with explicit internal capabilities.

Rationale: The project needs one auditable identity model while keeping dataset/model governance permissions separate from ordinary beekeeper Workspace Membership.

### AIA-007B Workspace Ownership Is Not Dataset Authority

Workspace ownership shall not automatically grant dataset/model governance capability.

Rationale: A beekeeper may own inspection data without being authorized to curate benchmark data, approve Dataset Versions, or promote model candidates.

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

Benchmark Dataset Items shall not be used for model training, routine tuning, prompt iteration, threshold adjustment, or pre-labelling quality optimisation.

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

Rationale: YOLO OBB expects oriented bounding boxes. HiveSight should support that format without making it the canonical reviewed annotation shape.

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

### AIA-017 Separate Bee And Varroa Evaluation

Bee detection and Varroa detection shall be evaluated separately.

Rationale: The two tasks have different difficulty, data density, metrics, and product consequences.

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

Rationale: User-facing estimates require evidence from protected data.

### AIA-021 Metrics Must Be Task-Specific

Evaluation shall report task-specific metrics rather than a single generic accuracy number.

Initial bee metrics may include:

- complete visible bee detection precision
- complete visible bee detection recall
- partial visible bee detection precision
- partial visible bee detection recall
- complete visible bee count error
- performance by image-quality bucket

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
- Early benchmark items may have one human review, while stricter second-review/adjudication remains open for serious benchmark claims.
- HiveSight's canonical annotation storage starts as internal normalized JSON. YOLO OBB is the first selected derived export format for the Bee Detector baseline.
- Dataset Role assignment is a separate curation step after annotation review.
- Reviewers should visibly know when annotations are Candidate Annotations.
- Benchmark items may originate from Candidate Annotations if human reviewed and provenance is preserved.
- `uncertain_bee` remains a required concept, but may be deferred from the first implementation slice. The gap should be recorded with an acceptance scenario and later executable pending coverage.
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
- Should a second human review be required for benchmark items?
- How should the project handle Varroa labels if the first slice is bee-only?
- What cost/privacy constraints apply if a hosted AI or annotation service is used for pre-labelling?
- What blind-review sample size is enough to measure automation bias?
- What independent sampling rule should be used before the first Varroa Detector training slice?
