# Model Requirements

This document captures requirements for the AI model and dataset side of HiveSight.

The product requirements define what the beekeeper-facing system should do. This document defines what evidence, data controls, annotations, evaluation, and release gates are needed before the model side of that capability can be trusted.

AI-assisted annotation, initial dataset bootstrap, dataset split governance, training runs, and model candidate selection are detailed in `requirements/ai-assisted-annotation-and-model-training-baseline.md` and `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`.

## Scope

The first implemented model capability is object detection on hive inspection photos. The target product capability is a staged bee-and-Varroa pipeline.

The logical model pipeline has three stages:

1. **Bee Localisation**: detect visible bees and estimate their body geometry and major axis.
2. **Bee Orientation**: determine which end of each localised bee is its head.
3. **Varroa Detection**: detect likely visible Varroa mites on or near the head-normalised bee crop.

These are separate logical model purposes. The implementation may initially use separate models, or later combine compatible capabilities, but it must preserve their independent inputs, outputs, provenance, evaluation, and governance. A model that supplies only a body axis has not supplied Bee Orientation.

Implementation traceability note: as of Slice 0015 planning, HiveSight has implemented bee annotation, dataset foundations, Hive Configuration context, and Postgres-backed repository metadata for a future Bee Localisation baseline. The first model-training baseline is Bee Localisation only. Bee Orientation and Varroa Detection remain product/model requirements, not implemented runtime capabilities.

Grounding DINO was tried as a local pre-labelling adapter and retired by ADR 0005 after poor brood-frame bee localisation results. The active model direction is a HiveSight-owned Bee Detector trained from reviewed HiveSight annotation evidence, with YOLO OBB as the first replaceable Bee Localisation implementation candidate.

## Model Objectives

### MR-001 Bee Localisation

The Bee Localisation Model shall detect visible bees in inspection photos and estimate their body geometry.

Rationale: Bee localisation provides the denominator for the first Varroa estimate, the visual evidence for the detected-bee overlay, and the source crop for later orientation and Varroa stages.

### MR-001A Bee Head Direction

The Bee Orientation Model shall determine directed centre-to-head orientation for each localised bee when the visible evidence is sufficient. It shall be allowed to report that orientation is unreliable for an occluded or partial bee. For the first head-normalized Varroa training and benchmark corpora, bees with unreliable orientation shall be excluded while remaining eligible for Bee Localisation evidence and supplementary Varroa evidence.

Rationale: A body axis alone is ambiguous by 180 degrees. Consistent head direction permits a bee-relative crop to be normalized before Varroa detection, which may strengthen learning and inference because likely mite location is anatomy-dependent.

### MR-002 Varroa Detection

The Varroa Detector shall detect likely visible Varroa mites on or near bees from bee-relative crops normalized to head direction when reliable orientation is available. Each positive result shall include explicit reviewed or predicted mite location, using a point marker or tight bounding box. In the first live pipeline, a localised bee with unreliable orientation shall be recorded as `not_assessed_orientation_unreliable`; the Varroa Detector shall not run on a guessed rotation.

The first Varroa baseline shall use high-resolution, standard axis-aligned YOLO detection on normalized bee crops. Oriented mite boxes and segmentation are deferred.

Rationale: Varroa detection is the core model task supporting the product.

### MR-003 Detection Association

The model pipeline should associate each likely Varroa detection with the most likely host bee and its localisation/orientation evidence when visually possible.

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

Rationale: The first trainable detector baseline is expected to use YOLO OBB, which consumes oriented bounding boxes. That export format should not replace the canonical reviewed annotation shape or be treated as an export of biological head/tail direction.

### MR-008B Orientation Reliability

Every reviewed Bee Annotation shall record Orientation Reliability as `reliable` or `unreliable`. It shall be distinct from bee-presence confidence and review status.

Existing Bee Annotations created before Orientation Reliability is implemented shall be returned for one-time human reliability review before entering a Bee Orientation or head-normalized Varroa Dataset Version.

Rationale: A visible bee can be correctly localised while its head direction remains unknowable. The distinction preserves honest orientation training evidence and supplies the first Varroa corpus inclusion rule.

### MR-009 Varroa Annotation Shape

Visible Varroa mites shall be labelled and returned as point markers or tight bounding boxes; a bee-level presence/absence result alone is insufficient for the first Varroa capability.

Rationale: Varroa mites are small, and point or small-box labels may be more practical and consistent than detailed masks.

### MR-009A Varroa Review Outcome

Every bee-relative crop reviewed for Varroa evidence shall record one Varroa Review Outcome: `visible_varroa_present`, `no_visible_varroa`, or `not_determined`. `visible_varroa_present` requires one or more reviewed Varroa markers; `no_visible_varroa` is an explicit human negative judgement; `not_determined` is excluded from negative training and benchmark evidence.

Rationale: An absent marker is ambiguous. A useful Varroa dataset needs known positives, actively reviewed negatives, and an honest unresolved state.

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

Every image used for training, validation, or evaluation shall have recorded provenance, Source Rights Record, permission status where applicable, explicit Permitted Use Scopes, and dataset role. For public/open evidence, the record shall include source organisation or repository, source reference, licence or terms version, allowed-use basis, attribution requirement, and restriction review, and it shall be explicitly approved by a Dataset Curator before a related image becomes a Dataset Item. Required attribution shall be carried into every relevant Dataset Version, derived export, evaluation report, and released model documentation. An unlisted use scope is not permitted.

Rationale: Dataset governance depends on knowing where each image came from and whether use is authorised by a workspace agreement, contributor permission, public/open licence, or another approved rights basis.

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

### MR-017L Dataset Selection Method

Dataset Items intended for Varroa training or benchmark use shall record Dataset Selection Method as `human_selected` or `upstream_model_selected`. `human_selected` requires selection before the curator sees upstream model suggestions; any model-influenced selection is `upstream_model_selected`. Benchmark reports shall show the resulting distribution.

Rationale: Selection Method makes the independence of the Varroa evidence auditable without conflating crop selection with annotation source or review method.

### MR-017B Dataset Split Leakage Prevention

The project shall guard against duplicate or near-duplicate frame photos crossing training, validation, and benchmark splits.

Rationale: Similar images of the same frame can make model evaluation look better than it really is.

### MR-017C Training Crops

The dataset workflow shall support Training Crops derived from original inspection photos.

Rationale: Small, reviewed crops let the project bootstrap a bee detector before enough fully annotated frame-side photos exist.

### MR-017D Curriculum Stages

Dataset Items may record a Curriculum Stage such as `small_crop`, `medium_crop`, `large_crop`, `full_frame_region`, or `full_frame_side`.

Rationale: The project should be able to grow model difficulty deliberately as the reviewed Bee Annotation Repository expands.

### MR-017E First HiveSight Bee Localisation Baseline

The first trainable HiveSight Bee Detector should implement Bee Localisation using oriented object detection, with YOLO OBB nano or small as the first candidate.

Rationale: YOLO OBB gives a practical local baseline for rotated bee-like objects while preserving the option to change model family once better project data exists.

### MR-017F Dataset Version Freezing

Any Dataset Version used by a Training Run shall freeze the included Dataset Item ids and the key metadata needed to reproduce and explain the run.

Rationale: Later Dataset Item withdrawal, supersession, correction, or role changes must not silently change historical training evidence.

### MR-017G Contribution Withdrawal Enforcement

When a contributor withdraws permission for a training contribution, HiveSight shall immediately prevent the affected Dataset Items from appearing in future exports, Dataset Versions, Training Runs, Benchmark Evaluations, or promotions. It shall preserve historical run lineage but mark every affected Dataset Version, Training Run, Model Candidate, and Model Version as affected by Contribution Withdrawal. Affected candidates shall not be promoted or used for new analysis; any affected user-facing Model Version shall be quarantined and replaced only by a newly trained Model Candidate whose Dataset Version excludes the withdrawn contribution. Source-image and annotation erasure shall be handled through the applicable deletion process.

Rationale: A withdrawal must stop future reliance on the contribution while retaining the minimal audit trail needed to explain earlier work.

### MR-017H Contributor Permission Boundary

HiveSight shall model an external contributor's permission to use their identified image, annotation, or review contribution separately from the Workspace Data Use Agreement. Each permission shall record an explicit, closed set of Permitted Use Scopes, such as model development, evaluation, user-facing deployment, sharing/publication, and commercial use; an unlisted scope is not permitted. The first contributor terms shall offer model development and evaluation only, explicitly excluding user-facing deployment, sharing/publication, and commercial use unless the contributor separately opts into those scopes. A Dataset Curator shall create Contribution Bundles and assign their annotation tasks; the Workspace owner may offer their own evidence but does not obtain dataset-governance authority through ownership alone. Before acceptance, HiveSight shall show a contributor only a non-sensitive bundle summary and the applicable terms, and shall not reveal assigned images or annotation tasks until the contributor explicitly accepts that named bundle and terms version. A material change to contributor terms requires fresh acceptance before the bundle may appear in a new Dataset Version, Training Run, Benchmark Evaluation, or promotion; historical lineage remains available for audit. Re-acceptance after withdrawal creates a new permission record for future use only and never automatically unquarantines prior Dataset Versions or model artifacts. Each contributor shall have a registered, pseudonymous HiveSight identity through which they can view their own bundles, withdraw permission, request deletion, and view a read-only Contribution Usage Record showing accepted terms, status, and linked Dataset Versions, Training Runs, and model-artifact outcomes. HiveSight retains only the minimum contact/authentication data needed for this control path; contribution provenance and curator-facing views use the internal contributor id and selected pseudonym, not a required real name. This identity does not grant Workspace Membership or dataset/model-governance capability, and the usage record does not reveal other contributors' evidence or the wider Workspace. Contributor access shall be limited to explicitly assigned annotation tasks and Contribution Bundles, never the wider Workspace, unassigned inspections, or other contributors' evidence. Withdrawal or a contributor deletion request shall immediately revoke access to every unfinished task in the bundle, while HiveSight retains only the minimal audit record needed to explain the request and affected lineage. One permission shall cover one named, immutable Contribution Bundle, and each included Dataset Item shall retain its bundle reference. In the first release, a withdrawal applies to the whole bundle; contributors must create separate bundles before acceptance when they need finer withdrawal boundaries. A Dataset Item may be eligible for future model use only while the workspace agreement and every applicable Contributor Contribution Permission are active. Withdrawal by one contributor shall affect only the Dataset Items and derived artifacts that depend on that contributor's identified contribution.

Rationale: Workspace ownership and contributor permission are different rights and must not be conflated.

### MR-017I Contributor Erasure Request

A contributor shall be able to request deletion of their own Contribution Bundle through their registered HiveSight identity. Starting that request shall automatically withdraw the bundle's model-use permission immediately; the deletion request then tracks subsequent source-image, annotation, derived-artifact, and retention handling. The contributor may not request deletion of other contributors' data or the wider workspace.

Rationale: Stopping future model use and erasing held contribution data are distinct, user-controlled operations.

### MR-017J Source Rights Invalidation Enforcement

If a Source Rights Record is later found invalid, revoked, or incompatible with HiveSight's intended use, HiveSight shall immediately exclude its affected Dataset Items from future exports, Dataset Versions, Training Runs, Benchmark Evaluations, and promotion. It shall quarantine dependent Dataset Versions and model artifacts, retain historical lineage for audit, and require a replacement trained without the invalidated evidence before future model use resumes. The record shall preserve `source_rights_invalidation` as the distinct cause.

Rationale: A source-licence problem must be as protective in operation as a contributor withdrawal without misrepresenting the reason as consent withdrawal.

### MR-017K User-Facing Deployment Scope Gate

HiveSight shall hard-block promotion of a Model Candidate to user-facing deployment unless every Dataset Item used to train it permits `user_facing_deployment`. Sharing/publication and commercial release shall each hard-block unless every training Dataset Item permits the relevant scope. Each release record shall include a scope-compatibility report identifying its supporting Dataset Versions and any excluded or incompatible evidence.

Rationale: Development permission does not imply permission to deploy a model trained on that evidence.

### MR-018 Protected Benchmark

The benchmark dataset shall be selected from a predeclared sampling plan and frozen before the evaluated Model Candidate is run against it. It shall be protected from training and routine threshold tuning, and no item may be added because that candidate succeeded or failed on it.

Rationale: Benchmark leakage would compromise the project's ability to measure real model improvement.

### MR-018A Representative Benchmark Sourcing

Benchmark data should include realistic dense, occluded, shadowed, poor-light, and varied source-group examples rather than only easy sparse crops.

Rationale: A model that looks good only on easy curriculum data may fail on real inspection photos.

### MR-018B Varroa Training Source Independence

The first Varroa training and benchmark datasets shall include human-selected bee crops, independently of upstream Bee Localisation and Bee Orientation outputs. They shall not be assembled solely from crops found and oriented by upstream models.

Rationale: If all mite-training crops come only from bees found or successfully oriented by upstream models, missed bee populations may never reach Varroa training or evaluation.

### MR-018C Separate Varroa Sampling Policies

HiveSight shall distinguish `model_curation` sampling from `inspection_rate_estimation` sampling, even when both use the same Varroa Review Outcome UI. Model-curation sampling optimizes representative training and benchmark evidence; inspection-rate sampling supports a future statistically stated estimate and must retain its own sampling-plan metadata.

Rationale: A dataset chosen to improve detection quality is not automatically a probability sample suitable for estimating a beekeeper-facing Varroa rate.

### MR-018D Model-Curation Sampling Method

The default model-curation selection shall be `stratified_random` across available Hive, frame, bee-density, lighting, and image-quality strata. A Dataset Curator may add deliberately difficult examples as `curator_targeted`; Dataset Versions and benchmark reports shall preserve and show the resulting method and stratum distributions.

Rationale: Randomness reduces curator-selection bias, stratification protects coverage of known conditions, and targeted examples prevent rare but operationally important cases being lost.

### MR-018E Benchmark Varroa Review Strength

Early baseline benchmark Varroa Review Outcomes may have one active curator review, provided the benchmark report states that limitation. Before a Model Candidate may be considered for user-facing Varroa Assessment, every benchmark Varroa Review Outcome shall receive Blind Independent Review: the second reviewer shall not see the first outcome or Varroa marker positions. Disagreements shall receive Third-Party Adjudication: a distinct adjudicator shall first record a fresh blind review, then may see anonymised prior reviews to document the final outcome. An unresolved disagreement, including a three-way conflict, shall become `not_determined` and be excluded from Varroa training and benchmark evidence. Training and validation Varroa evidence may use one active reviewed outcome, provided its review provenance is retained.

Rationale: Early learning needs a practical path to usable evidence, while a user-facing health assessment needs stronger protection against reviewer error and automation bias.

### MR-018F Benchmark Review Agreement Reporting

Every Varroa Benchmark Evaluation shall report outcome agreement, marker-location agreement, adjudication and unresolved-disagreement counts, and the count of benchmark items without independent second review. Marker-location agreement shall use one-to-one matched markers in bee-relative coordinates, normalized to the reviewed bee body rather than raw image pixels; unmatched markers shall be reported separately. Numeric promotion thresholds for these measures are deferred until sufficient project evidence exists.

Rationale: Model metrics cannot be interpreted honestly without showing the consistency and completeness of the human benchmark evidence.

### MR-018G Training And Validation Review Audit

HiveSight shall periodically select a stratified-random sample of training and validation Varroa Reviews for Blind Independent Review as a non-blocking quality audit. The audit shall preserve its selection and review provenance and report agreement, disagreement, and unresolved-outcome measures separately from protected benchmark evidence and separately by Annotation Source, including human-from-scratch and AI-assisted-reviewed evidence. A concerning audit result requires a documented Dataset Curator Audit Disposition and a warning on every affected Dataset Version; it does not automatically block dataset use while numerical escalation thresholds remain deferred.

Rationale: One-review training data is practical for growth, but must remain observable for reviewer drift and automation bias.

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

Contributor-level withdrawal and source-rights invalidation are governed by MR-017G to MR-017K and ADR 0008/0009. Workspace-level agreement withdrawal still requires a product workflow, and detailed deletion, purge, retention, and legal-exception policy remains parked in PARK-0011.

### MR-022 Consent Withdrawal

The system should support withdrawal of consent for future training use. When withdrawn evidence has already entered Dataset Versions or model artifacts, HiveSight shall preserve historical lineage for audit, prevent future reliance on affected evidence, and follow the applicable quarantine-and-retrain workflow.

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

### MR-027 Separate Localisation, Orientation, And Varroa Metrics

The project shall evaluate Bee Localisation, Bee Orientation, and Varroa Detection separately.

Rationale: A single accuracy number would hide important differences between denominator quality, head-direction correctness, and mite detection quality.

### Bee Localisation Metrics

Suggested bee metrics:

- complete visible bee count error
- partial visible bee count error
- bee detection precision and recall when reviewed boxes are available
- performance by image-quality bucket

### Bee Orientation Metrics

Suggested orientation metrics:

- directed head/tail accuracy, where a 180-degree reversal is incorrect
- angular error against reviewed centre-to-head orientation
- orientation coverage and unreliable-orientation rate
- performance for complete and partial visible bees separately
- performance by image-quality and occlusion bucket

The first Bee Orientation training and benchmark corpora shall contain only `complete_visible_bee` annotations with reliable orientation. Reliably oriented partial bees remain retained evidence for later, separately reported evaluation.

### Varroa Detection Metrics

Suggested Varroa metrics:

- Varroa detection precision
- Varroa detection recall
- false positives per image
- false negatives per image
- association accuracy against complete, partial, and unassociated states
- performance by image-quality bucket
- performance by orientation-confidence bucket

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

Each Model Candidate used in a user-facing Varroa assessment pipeline shall pass a documented benchmark evaluation for its own Model Purpose before promotion.

Where the candidate relies on a Dataset Version with a quality-audit warning, the Model Approver shall explicitly acknowledge the associated Audit Disposition as part of the promotion record.

Rationale: No model should silently move into product use without evidence.

### MR-030A End-To-End Pipeline Evaluation Before Promotion

A user-facing Varroa assessment pipeline shall also pass a documented End-to-End Pipeline Evaluation on a separate protected full-frame selection snapshot. This evaluation is additional to, not a replacement for, each constituent Model Purpose's Benchmark Evaluation. Its predeclared selection plan and source groups shall be frozen before candidate selection or tuning. Its `source_group_key` values shall be disjoint from training, validation, and component benchmark evidence. Its full-frame evidence shall contain complete human-reviewed labels for all visible bees, their Orientation Reliability, and the relevant Varroa Review Outcomes. It shall report the count and proportion of localised bees that reached Varroa Assessment, the count and proportion recorded as `not_assessed_orientation_unreliable`, and the count and proportion lost at each stage, separately for complete and partial visible bees, and broken down by Hive Configuration, bee-density, lighting, and image-quality strata with sparse-group warnings. The initial user-facing Varroa estimate continues to use complete visible bees only and shall display a coverage warning whenever any complete visible bee was not assessed for Varroa. Once an evidence-based coverage threshold is established, coverage below that threshold shall suppress the headline estimate.

Rationale: Separate model scores do not reveal compounded failures across localisation, orientation, and Varroa detection in the actual inspection workflow.

### MR-030B Inadequate-Coverage Review Recovery

When a user-facing Varroa headline estimate is suppressed for inadequate coverage, the Workspace owner shall be able to open an Inspection Recovery Review for human review or correction. This remains available for retained inspection history after the Workspace Data Use Agreement is withdrawn, because it is an inspection-support feature. In the first release, the review is available only for a suppressed model-only result, not for every completed inspection, and only the Workspace owner may create, resume, or complete it. It is a distinct, named, saveable, and resumable review session linked to a fixed snapshot of the original model-only result and its photo evidence; newer models shall not be run or substituted during recovery. Every resulting annotation and Varroa decision shall retain its recovery-review provenance and be reported as AI-assisted-reviewed, never as human-from-scratch, because the original model output was visible. Model promotion shall never automatically reanalyse historical Inspection Photos. A future explicit Historical Reanalysis request shall create a new model-only result and never alter prior model-only or human-reviewed results. The owner may complete it at any coverage level after an explicit confirmation, including when its headline rate remains suppressed. Once completed, the review and its result are immutable; a later correction shall create a new linked review and human-reviewed result revision. The latest completed human-reviewed result shall become the inspection's current result by default; the original model-only result and earlier human-reviewed revisions remain available as labelled comparison history. The reviewer shall be able to resolve previously unassessed complete visible bees and correct any model-produced bee, orientation, or Varroa decision. The original model-only result remains immutable; the recovery workflow shall calculate and show a separate human-reviewed inspection result alongside it with explicit provenance. Both results shall show a Result Evidence Breakdown with counts of positive, active negative, `not_determined`, and unassessed complete visible bees, plus Review Completion and Determinate Varroa Coverage. An explicit `not_determined` outcome counts toward Review Completion but not Determinate Varroa Coverage, and shall not support a headline rate. The resulting evidence is product feedback only and remains ineligible for model-improvement use until an active Workspace Data Use Agreement exists and a Dataset Curator independently reviews it and assigns a Dataset Role; it must never become training evidence automatically.

Rationale: Insufficient automated coverage should provide an actionable recovery path, not discard potentially useful inspection evidence.

### MR-030C Recovery Evidence Consent Boundary

Recovery evidence created while the Workspace Data Use Agreement is withdrawn shall remain product-only. A later agreement acceptance is prospective and shall not itself make that evidence eligible for model improvement; the Workspace owner must make a separate explicit dataset-contribution decision, followed by independent Dataset Curator review and Dataset Role assignment.

Rationale: Re-accepting terms must not silently change the permitted use of evidence created during withdrawal.

### MR-030D Per-Revision Dataset Contribution Decision

A Dataset Contribution Decision shall apply to exactly one named completed Human-Reviewed Inspection Result revision. It shall record the Workspace owner, decision time, result revision, and current Workspace Data Use Agreement. It shall not act as a workspace-wide opt-in or itself assign a Dataset Role.

Rationale: The owner needs precise, auditable control over evidence created while consent was withdrawn.

### MR-031 Human Approval Before Promotion

A human reviewer shall approve a model version before it is used for user-facing Varroa estimates.

Rationale: Release decisions require judgment, especially before numeric performance thresholds are mature.

### MR-032 Numeric Thresholds Deferred

Fixed numeric promotion and coverage-suppression thresholds are deferred until baseline data exists.

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
- What fallback is acceptable when a partial or occluded bee cannot be oriented reliably for Varroa detection?
