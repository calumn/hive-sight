# Model Requirements

This document captures requirements for the AI model and dataset side of HiveSight.

The product requirements define what the beekeeper-facing system should do. This document defines what evidence, data controls, annotations, evaluation, and release gates are needed before the model side of that capability can be trusted.

AI-assisted annotation, initial dataset bootstrap, dataset split governance, training runs, and model candidate selection are detailed in `requirements/ai-assisted-annotation-and-model-training-baseline.md` and `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`.

## Scope

The first model capability is object detection on hive inspection photos.

The logical model pipeline has two stages:

1. Detect visible bees.
2. Detect likely visible Varroa mites on or near detected bees.

The implementation may use one model or multiple models. The requirements should preserve the logical separation between bee detection and Varroa detection so each can be measured, improved, and governed independently.

Implementation traceability note: as of Slice 0015 planning, HiveSight has implemented bee annotation, dataset foundations, Hive Configuration context, and Postgres-backed repository metadata for a future Bee Detector baseline. The first model-training baseline is Bee Detector only. The Varroa detection requirements remain product/model requirements, not implemented runtime capability.

Grounding DINO was tried as a local pre-labelling adapter and retired by ADR 0005 after poor brood-frame bee localisation results. The active model direction is a HiveSight-owned Bee Detector trained from reviewed HiveSight annotation evidence, with YOLO OBB as the first replaceable implementation candidate.

## Model Objectives

### MR-001 Bee Detection

The model pipeline shall detect visible bees in inspection photos.

Rationale: Bee detection provides the denominator for the first Varroa estimate and the visual evidence for the detected-bee overlay.

### MR-002 Varroa Detection

The model pipeline shall detect likely visible Varroa mites on or near bees in inspection photos.

Rationale: Varroa detection is the core model task supporting the product.

### MR-003 Detection Association

The model pipeline should associate each likely Varroa detection with the most likely host bee when visually possible.

Rationale: Association helps distinguish mites on complete bees, mites on partial bees, and visible mites that cannot be reliably linked to a bee.

## Bee Visibility Classes

The dataset and model outputs should distinguish:

- `complete_visible_bee`: enough of the bee is visible to count confidently as one bee.
- `partial_visible_bee`: a bee is visible but occluded, cropped, overlapped, or only partly in frame.
- `uncertain_bee`: possible bee, but not reliable enough for confident counting.

### MR-004 Complete Bee Denominator

The headline Varroa estimate shall use complete visible bees as the primary denominator.

Rationale: Counting partial bees as full bees could inflate the denominator and understate possible Varroa presence.

### MR-005 Partial Bee Reporting

The system should report partial visible bees separately from complete visible bees.

Rationale: Partial bees are useful evidence but should not silently distort the headline metric.

## Varroa Association Classes

The dataset and model outputs should distinguish:

- `associated_with_complete_bee`
- `associated_with_partial_bee`
- `unassociated_visible_varroa`

### MR-006 Headline Varroa Numerator

The headline Varroa estimate should use likely Varroa detections associated with complete visible bees.

Rationale: This keeps the numerator and denominator aligned.

### MR-007 Additional Varroa Evidence

Likely Varroa detections associated with partial bees or unassociated visible Varroa should be reported as additional evidence rather than silently folded into the headline estimate.

Rationale: The system should not pretend that ambiguous image evidence is cleaner than it is.

## Annotation Requirements

### MR-008 Bee Annotation Shape

Visible bees shall be reviewed as oriented bee ellipses in the canonical annotation model.

Ellipse orientation shall represent the directed long-axis alignment of the visible bee body. `rotation_degrees` points from the ellipse center toward the bee's head along the major axis; the opposite end is the tail.

Rationale: Bees are elongated and appear at many rotations. Directed oriented ellipses better express human-reviewed bee evidence than axis-aligned rectangles, and preserve head/tail orientation that may strengthen later Varroa detection because likely mite location can be bee-orientation dependent.

### MR-008A Bee Annotation Export Shape

The project may export canonical oriented bee ellipses into model-specific training shapes such as oriented bounding boxes.

Rationale: The first trainable detector baseline is expected to use YOLO OBB, which consumes oriented bounding boxes. That export format should not replace the canonical reviewed annotation shape.

### MR-009 Varroa Annotation Shape

Visible Varroa mites should be labelled with point markers or tight bounding boxes.

Rationale: Varroa mites are small, and point or small-box labels may be more practical and consistent than detailed masks.

### MR-010 Segmentation Deferred

Segmentation masks are not required for the first model baseline.

Rationale: Masks are expensive to create and are not needed for the first tagged-photo and counting workflows.

### MR-011 Uncertainty Flags

Annotations should support uncertainty flags such as `uncertain`, `occluded`, `poor_image_quality`, and `disputed`.

Rationale: Varroa and bee labels may be visually ambiguous, especially in dense or low-quality images.

## Ground Truth And Review

### MR-012 Human-Reviewed Ground Truth

Ground truth shall require human-reviewed annotations.

Rationale: AI-generated labels and user corrections are useful signals, but they should not become trusted ground truth without review.

### MR-012A Candidate Annotations Are Allowed

The project may use Candidate Annotations to accelerate initial dataset creation.

Rationale: Candidate annotations can make the first bee and Varroa datasets practical to create while keeping human review as the trust boundary.

### MR-012B Candidate Annotations Are Not Ground Truth

Candidate Annotations shall remain distinct from Reviewed Annotations until a human reviewer checks or corrects them.

Rationale: AI assistance should reduce annotation effort without creating circular or unverified labels.

### MR-012C Automation-Bias Warning

Training and evaluation reports shall distinguish human-from-scratch review from human-reviewed candidate annotations.

Rationale: A human approving an existing machine proposal is not equivalent to drawing the annotation blind. Reports should warn when reviewed data lacks human-from-scratch or blind-review comparison evidence.

### MR-013 User Corrections As Review Candidates

User corrections shall be stored as review candidates, not automatically used as training data.

Rationale: User corrections may be correct, uncertain, accidental, or wrong. They require review before use.

### MR-014 Correction Review Outcomes

A reviewer should be able to approve, reject, mark uncertain, exclude, approve for training, or approve for evaluation/benchmark use.

Rationale: Different levels of review confidence are needed for different dataset roles.

Suggested statuses:

- `model_suggested`
- `user_corrected`
- `review_pending`
- `review_approved`
- `training_approved`
- `evaluation_approved`
- `rejected`
- `excluded`

## Dataset Sources And Provenance

### MR-015 Staged Dataset Sources

The project should use a staged dataset source strategy:

- Public or externally sourced images for bootstrapping.
- Project-owned inspection photos for realistic development.
- Future user-submitted photos only with explicit consent.

Rationale: Early public data may help bootstrap the model, but project-owned and consented field data will better match real usage.

### MR-016 Provenance Required

Every image used for training, validation, or evaluation shall have recorded provenance, permission status, and dataset role.

Rationale: Dataset governance depends on knowing where each image came from and how it may be used.

### MR-017 Dataset Roles

Reviewed annotations shall be assigned explicit dataset roles.

Allowed roles:

- `training`
- `validation`
- `benchmark`
- `excluded`

Rationale: Training, tuning, and honest evaluation require separated datasets.

### MR-017A Dataset Items

Dataset use shall be tracked at the Dataset Item level, connecting reviewed image/annotation evidence to one Dataset Role.

Rationale: A reviewed annotation is not automatically training, validation, benchmark, or excluded data.

### MR-017B Dataset Split Leakage Prevention

The project shall guard against duplicate or near-duplicate frame photos crossing training, validation, and benchmark splits.

Rationale: Similar images of the same frame can make model evaluation look better than it really is.

### MR-017C Training Crops

The dataset workflow shall support Training Crops derived from original inspection photos.

Rationale: Small, reviewed crops let the project bootstrap a bee detector before enough fully annotated frame-side photos exist.

### MR-017D Curriculum Stages

Dataset Items may record a Curriculum Stage such as `small_crop`, `medium_crop`, `large_crop`, `full_frame_region`, or `full_frame_side`.

Rationale: The project should be able to grow model difficulty deliberately as the reviewed Bee Annotation Repository expands.

### MR-017E First HiveSight Bee Detector Baseline

The first trainable HiveSight Bee Detector should use oriented object detection, with YOLO OBB nano or small as the first candidate.

Rationale: YOLO OBB gives a practical local baseline for rotated bee-like objects while preserving the option to change model family once better project data exists.

### MR-017F Dataset Version Freezing

Any Dataset Version used by a Training Run shall freeze the included Dataset Item ids and the key metadata needed to reproduce and explain the run.

Rationale: Later Dataset Item withdrawal, supersession, correction, or role changes must not silently change historical training evidence.

### MR-018 Protected Benchmark

The benchmark dataset should be protected from training and routine threshold tuning.

Rationale: Benchmark leakage would compromise the project's ability to measure real model improvement.

### MR-018A Representative Benchmark Sourcing

Benchmark data should include realistic dense, occluded, shadowed, poor-light, and varied source-group examples rather than only easy sparse crops.

Rationale: A model that looks good only on easy curriculum data may fail on real inspection photos.

### MR-018B Varroa Training Source Independence

Before the first Varroa Detector training slice, the project shall decide how mite-training crops are sourced so the Varroa Detector does not inherit Bee Detector blind spots by construction.

Rationale: If all mite-training crops come only from bees found by the Bee Detector, missed bee populations may never reach Varroa training or evaluation.

## Privacy And Consent

### MR-019 Training Consent

Photos uploaded for analysis shall not automatically become training data.

Rationale: Analysis use and model-improvement use are separate user expectations.

### MR-020 Explicit Consent

Future user-submitted photos and corrections shall require explicit consent before they can be used for model improvement.

Rationale: Uploaded images may contain metadata, location signals, private apiary details, or user records.

### MR-021 Consent Tracking

Workspace Data Use Agreement status, accepted terms version, and withdrawal status shall be tracked at the Workspace level and must be traceable to photos and corrections through Workspace ownership.

Rationale: Version one treats consent as a Workspace-level condition of using upload and analysis features. Dataset eligibility still needs to be traceable for each photo and correction through its owning Workspace.

The policy for withdrawal, prior uploads, dataset versions, already-trained model artifacts, and purge rights remains unresolved and must not be hidden behind the initial consent flow.

### MR-022 Consent Withdrawal

The system should support withdrawal of consent for future training use.

Rationale: Users should retain control over whether their data contributes to model improvement.

### MR-023 Metadata Minimisation

Images used for training, evaluation, sharing, or publication should be stripped of unnecessary metadata.

Rationale: Image metadata may contain location, device, or other private information.

## Image Quality

### MR-024 Image Quality Status

The model pipeline shall record image quality status for each analysed photo.

Suggested quality issues:

- too blurry
- too dark
- overexposed
- bees too small
- frame too distant
- severe occlusion
- no clear bees or frame context
- duplicate or near-duplicate photo
- too few complete visible bees

Rationale: Low-quality images can make counts and Varroa estimates misleading.

### MR-025 Quality Warnings

The system shall show quality warnings when image evidence is weak.

Rationale: The user should understand when the model result may be unreliable.

### MR-026 Estimate Downgrade Or Exclusion

Low-quality or unsuitable photos may be downgraded or excluded from inspection-level estimates.

Rationale: The system should avoid presenting confident-looking rates from weak evidence.

## Model Evaluation Metrics

### MR-027 Separate Bee And Varroa Metrics

The project shall evaluate bee detection and Varroa detection separately.

Rationale: A single accuracy number would hide important differences between denominator quality and mite detection quality.

### Bee Detection Metrics

Suggested bee metrics:

- complete visible bee count error
- partial visible bee count error
- bee detection precision and recall when reviewed boxes are available
- performance by image-quality bucket

### Varroa Detection Metrics

Suggested Varroa metrics:

- Varroa detection precision
- Varroa detection recall
- false positives per image
- false negatives per image
- association accuracy against complete, partial, and unassociated states
- performance by image-quality bucket

### Product Review Metrics

Suggested product-review metrics:

- percentage of model Varroa tags rejected by users or reviewers
- percentage of missed Varroa markers added by users or reviewers
- number of inspections where low-quality evidence prevented a confident estimate

## Model Versioning And Release Gates

### MR-028 Model Version Records

Every model used for user-facing analysis shall have a recorded model version.

Rationale: Results, corrections, and evaluations need to be traceable to the model that produced them.

### MR-029 Dataset Version Records

Every benchmark evaluation shall record the dataset version used.

Rationale: Model comparisons are only meaningful when the evaluation data is known.

### MR-029A Training Run Records

Every model training or fine-tuning execution shall record the Dataset Versions, model candidate, training settings, code/artifact reference, and outcome.

Rationale: Model candidates must be reproducible and comparable.

At minimum, a Training Run should record model purpose, model family, adapter type, dataset version, settings, base weights, random seed, artifact manifest, environment summary, git state, database purpose, warnings, metrics, and failure details.

### MR-029B Model Candidate Records

Trained or configured models shall be tracked as Model Candidates until they pass benchmark evaluation and human promotion approval.

Rationale: Experimental candidates must remain distinct from approved user-facing Model Versions.

### MR-030 Benchmark Evaluation Before Promotion

A model version shall pass a documented benchmark evaluation before it is promoted for user-facing Varroa estimates.

Rationale: No model should silently move into product use without evidence.

### MR-031 Human Approval Before Promotion

A human reviewer shall approve a model version before it is used for user-facing Varroa estimates.

Rationale: Release decisions require judgment, especially before numeric performance thresholds are mature.

### MR-032 Numeric Thresholds Deferred

Fixed numeric promotion thresholds are deferred until baseline data exists.

Rationale: Premature thresholds may be arbitrary before the project has representative images and reviewed labels.

## Open Model Questions

- Which public or externally sourced datasets are legally usable for bootstrapping?
- What annotation tool should be used for the first reviewed dataset?
- What minimum image quality guidance should be given to users?
- Should user corrections ever be used for training without a second reviewer, or is one reviewer enough for this project?
- How large should the first protected benchmark set be?
- Should dataset splits happen at photo, frame, inspection, hive, workspace, or source level?
- How should duplicate or near-duplicate frame photos be detected?
- How should model results be compared when a newer model re-analyses older photos?
- Where should consent be captured in the product workflow?
- What blind-review sample size is sufficient to measure automation bias once the workflow exists?
- What independent sampling policy should govern future Varroa Detector training crops?
