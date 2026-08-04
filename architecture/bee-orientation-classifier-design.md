# Bee Orientation Classifier Design

Status: planning design

## Purpose

This document defines the first technical design for HiveSight's Bee Orientation Model.

The model purpose is narrow: given one localised bee whose body axis is known, determine whether the bee's head is up in a normalized crop, or whether the crop should be flipped by 180 degrees before Varroa Detection.

This design uses the existing directed Oriented Bee Ellipse evidence. `rotation_degrees` already points from the ellipse centre toward the bee's head. The training-data convention for the orientation model is therefore:

- **Head Up**: the normalized crop has the bee's head at the top of the image.
- **Head Down**: the normalized crop has the bee's tail at the top and must be flipped 180 degrees before Varroa Detection.

The human source evidence is shared with Bee Localisation. A Dataset Curator provides one reviewed training set of marked, oriented bees: source image, Training Crop, Oriented Bee Ellipse geometry, visibility class, source rights, contribution permission, review provenance, Dataset Item, Dataset Role, and Dataset Version membership. Bee Localisation and Bee Orientation then consume different projections of that same governed evidence.

The split is at Model Purpose and derived artifact level, not at source-annotation governance level. YOLO OBB receives a geometry projection for Bee Localisation; the Bee Orientation classifier receives a Head Up / Head Down crop projection from the same reviewed Oriented Bee Ellipse when Orientation Reliability is `reliable`.

A promoted marked-bee Dataset Version must stay in lockstep across Bee Localisation and Bee Orientation. HiveSight should not promote a YOLO source dataset independently from an orientation source dataset when both claim to use the same marked oriented-bee evidence. What may differ are the derived export packages, training adapters, model candidates, benchmark reports, and promotion gates for each Model Purpose.

## Source Inputs

- `CONTEXT.md`: Oriented Bee Ellipse, Orientation Reliability, Model Purpose, Bee Localisation Model, Bee Orientation Model, Varroa Detector.
- `architecture/adr/0006-directed-bee-ellipse-orientation.md`: Oriented Bee Ellipse rotation is directed centre-to-head geometry.
- `architecture/adr/0007-three-stage-bee-localisation-orientation-and-varroa-pipeline.md`: Bee Localisation, Bee Orientation, and Varroa Detection remain separately governed Model Purposes.
- `requirements/model-requirements.md`: MR-001A Bee Head Direction, MR-008B Orientation Reliability, Bee Orientation Metrics.
- `requirements/roadmap.md`: Bee Orientation candidate slices.

## Learning Shape

The first Bee Orientation implementation is a binary image classifier, not a bee detector.

Input:

- one RGB bee-relative crop;
- body axis normalized so the candidate head/tail axis is vertical;
- crop size fixed by the export package, for example 128x128 or 224x224;
- optional margin around the ellipse so head and tail context are not clipped.

Output:

- `head_up_probability`;
- predicted label: `head_up` or `head_down`;
- confidence or uncertainty score;
- optional abstention outcome when the model is below the Orientation Reliability threshold.

The model does not create canonical annotation evidence. It creates Candidate Orientation evidence that must be benchmarked and governed before user-facing use.

## 1. Dataset Builder

The dataset builder exports Bee Orientation examples from reviewed Bee Annotation Repository evidence.

Eligibility:

- source Dataset Item is active and assigned to an eligible Dataset Role;
- bee annotation is `complete_visible_bee` for the first corpus;
- Oriented Bee Ellipse has reviewed Orientation Reliability of `reliable`;
- source image bytes are available;
- source rights and contribution permissions allow the target use;
- benchmark items remain protected and are not mixed into training or validation exports.

Transform:

1. Read the source image and Training Crop provenance.
2. Locate each eligible Oriented Bee Ellipse.
3. Extract a bee-relative crop with margin.
4. Rotate the crop so the stored centre-to-head direction points upward.
5. Resize or pad to the model input size.
6. Emit a `head_up` example.
7. Optionally emit a 180-degree flipped augmentation labelled `head_down`.

Package contents:

- crop image files;
- labels;
- source map linking each example to Dataset Item, Training Crop, Source Image, and ellipse ids;
- transform metadata: crop bounds, margin, source image dimensions, rotation applied, resize/pad policy, augmentation flag;
- manifest with model purpose `bee_orientation`, export version, class map, source rights summary, and excluded-item reasons.

Design guard:

The builder must not infer Orientation Reliability from the presence of `rotation_degrees`. Reliability is a reviewed data-quality field.

## 2. Model Training Adapter

The first training adapter should use a small, replaceable image classifier.

Initial candidates:

- MobileNet-style classifier;
- EfficientNet-lite-style classifier;
- small ResNet-style classifier.

Training inputs:

- shared marked-bee Dataset Version;
- package produced by the dataset builder;
- fixed class map: `0 head_up`, `1 head_down`;
- training settings: image size, batch size, epochs, seed, augmentation settings, base architecture, pretrained weights.

Training outputs:

- Training Run;
- Model Candidate for Model Purpose `bee_orientation`;
- weights or model artifact;
- training logs;
- validation metrics;
- artifact manifest with dataset version ids and package manifest hash.

Adapter seam:

The adapter should follow the existing model-run pattern used by Bee Localisation: fake deterministic adapter for fast tests, optional real local adapter for explicit QA/training commands.

Design guard:

The classifier receives bee crops. It must not be described as finding bees, counting bees, detecting mites, or producing a complete Varroa assessment.

## 3. Benchmark And Evaluation

Bee Orientation Benchmark Evaluation measures head-direction prediction only.

Required metrics:

- head-up/head-down accuracy;
- confusion matrix;
- confidence distribution;
- abstention or unreliable-orientation rate when thresholding is enabled;
- performance by image quality, occlusion, bee size, class, Hive Configuration, Source Image, and source group where enough evidence exists;
- sparse-group warnings.

Optional metrics:

- angular error to the reviewed directed ellipse when the pipeline also emits a direction angle;
- calibration curve for `head_up_probability`;
- separate report for partial visible bees once partial-bee evaluation is deliberately introduced.

Protected benchmark rules:

- benchmark evidence is frozen before evaluating the candidate;
- benchmark source groups must be disjoint from training and validation when that gate exists;
- benchmark report names Model Purpose `bee_orientation`;
- report must not claim Bee Localisation, Varroa Detection, or user-facing Varroa readiness.

Pass/fail thresholds remain deferred until enough benchmark evidence exists.

## 4. Inference Adapter

The inference adapter receives localised bee crops from the pipeline.

Input contract:

- source Inspection Photo or Source Image id;
- localised bee id or Candidate Annotation id;
- localised body geometry from Bee Localisation;
- normalized crop bytes or a request from which the adapter can create them;
- upstream model candidate/version provenance.

Output contract:

- predicted orientation: `head_up` or `head_down`;
- `head_up_probability`;
- confidence;
- threshold decision: `orientation_assessed` or `not_assessed_orientation_unreliable`;
- model candidate/version provenance;
- normalized crop transform metadata.

Inference behaviour:

1. Normalize the localised bee crop onto a vertical body axis.
2. Run the classifier.
3. If confidence is below the configured reliability threshold, record `not_assessed_orientation_unreliable`.
4. If the prediction is `head_down`, rotate the crop 180 degrees.
5. Emit a Head-Up Normalized Bee Crop for Varroa Detection.

Design guard:

The inference adapter may decide not to assess. It must not guess a head direction when reliability is inadequate.

## 5. Pipeline Integration

The first runtime pipeline remains staged:

1. Bee Localisation finds visible bees and body geometry.
2. Bee Orientation converts each localised bee into a reliable Head-Up Normalized Bee Crop or an unassessed orientation outcome.
3. Varroa Detection runs only on Head-Up Normalized Bee Crops whose orientation was assessed.

Pipeline records:

- each localised bee receives a stable pipeline item id;
- each orientation prediction is linked to its localised bee and source image;
- each Varroa prediction is linked to the orientation output and normalized crop;
- bees that do not reach Varroa Detection are counted in coverage as `not_assessed_orientation_unreliable` or another explicit loss category.

Failure and coverage:

- a failed Bee Localisation result prevents downstream orientation for that bee;
- an unreliable orientation suppresses Varroa Detection for that bee;
- a Varroa Detector failure does not rewrite localisation or orientation evidence;
- user-facing Varroa output must report coverage losses by stage.

Design guard:

Combining these stages into one future model remains allowed only if the separate Model Purpose outputs, provenance, metrics, and governance records are preserved.

## 6. Governance Records

Bee Orientation shares the reviewed annotation, source-rights, contribution, Dataset Item, Dataset Role, and Dataset Version governance of the marked oriented-bee source evidence.

Bee Orientation still needs its own derived model-governance records once that shared evidence is exported, trained, benchmarked, or used for inference. Those records must identify Model Purpose `bee_orientation` and must not be treated as interchangeable with Bee Localisation training runs, model candidates, or benchmark evaluations.

Required records:

- shared marked-bee Dataset Version membership;
- Bee Orientation export package derived from that Dataset Version;
- Bee Orientation Training Run;
- Bee Orientation Model Candidate;
- Bee Orientation Benchmark Evaluation;
- Orientation Prediction or orientation stage output;
- Head-Up Normalized Bee Crop provenance;
- orientation threshold settings used for each inference run.

Required provenance:

- source image and crop ids;
- Oriented Bee Ellipse id for training/benchmark examples;
- Orientation Reliability review status;
- Dataset Role and Dataset Version membership;
- source rights and contribution permission summary;
- model candidate/version id;
- transform metadata sufficient to reproduce the normalized crop.

Promotion gates:

- orientation benchmark evidence must be separate from Bee Localisation and Varroa Detection benchmark evidence;
- user-facing Varroa promotion requires orientation benchmark evidence plus End-to-End Pipeline Evaluation;
- unreliable-orientation counts are part of coverage reporting and cannot be hidden behind aggregate accuracy.

## Out Of Scope

- Varroa marker labelling.
- Varroa Detector training.
- User-facing Varroa estimates.
- Pose/keypoint or multi-head model implementation.
- Production model deployment.
- Numeric promotion thresholds.

## Open Questions

- What input crop size and margin should the first dataset builder use?
- Should the first classifier train on both generated `head_up` and generated `head_down` examples, or only on naturally presented crops with controlled augmentation?
- What confidence threshold should produce `not_assessed_orientation_unreliable` in early QA?
- Should Orientation Reliability be reviewed per ellipse before or during Dataset Role assignment?
- Should partial visible bees be excluded entirely from the first orientation package, or exported into a labelled holdout report only?
