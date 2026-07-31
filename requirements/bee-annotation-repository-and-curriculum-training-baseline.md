# Bee Annotation Repository And Curriculum Training Baseline

## Purpose

HiveSight will build its bee detector from a growing repository of human-reviewed bee annotations. The project will start with small, manageable crop images and gradually move toward larger crops, full-frame regions, and whole frame sides as model quality improves.

This baseline refines the AI-assisted annotation strategy after the Grounding DINO spike. Grounding DINO has been retired from the active solution by ADR 0005. The intended path is to train the HiveSight Bee Detector from reviewed HiveSight data.

## Core Principles

- Model suggestions are Candidate Annotations only until human reviewed.
- Human-reviewed annotations are the trusted evidence.
- Canonical bee geometry is an oriented bee ellipse, not an axis-aligned rectangle.
- Dataset Role assignment remains separate from review approval.
- Benchmark data is protected from training, routine tuning, threshold tuning, prompt tuning, and pre-labelling optimisation.
- Training-data collection and beekeeper-facing Varroa assessment are separate Inspection Intents.

## Workflow

```text
source inspection photo
-> training crop selection
-> HiveSight Bee Detector candidate oriented bee ellipses, if a candidate-generation model exists
-> human correction and complete review
-> reviewed oriented bee ellipses
-> Bee Annotation Repository item
-> Dataset Role assignment
-> Dataset Version
-> Training Run
-> Model Candidate
-> Benchmark Evaluation
-> approved Model Version or next training cycle
```

The loop is not circular because model output is never accepted as truth without human review. The model proposes; the Dataset Curator verifies, corrects, adds missed bees, removes false positives, and approves the final evidence.

## Requirements

### BAR-001 Inspection Intent

Each Inspection shall have one explicit Inspection Intent.

Initial intents:

- `training_data_collection`
- `varroa_assessment`

Training-data collection Inspections expose dataset labelling workflows. Varroa-assessment Inspections expose beekeeper-facing analysis workflows. One Inspection must not mix both intents.

### BAR-002 Multi-Photo Inspection

An Inspection shall support multiple Inspection Photos.

Rationale: A brood box can contain 10 or 11 frames, and a beekeeper may photograph both sides of each frame.

### BAR-003 Training Crop

The dataset workflow shall support Training Crops derived from original Inspection Photos.

A Training Crop records:

- source Inspection Photo
- crop bounds in source-image coordinates
- crop image dimensions
- Curriculum Stage
- creator/reviewer provenance

### BAR-004 Curriculum Stages

Training data shall support a curriculum that starts with small manageable crops and grows in difficulty.

Initial Curriculum Stages:

- `small_crop`
- `medium_crop`
- `large_crop`
- `full_frame_region`
- `full_frame_side`

Rationale: Small crops with a few bees are easier to annotate completely and easier for the first model to learn from.

### BAR-005 Oriented Bee Ellipse Is Canonical

The canonical reviewed bee annotation geometry shall be an oriented bee ellipse.

Minimum fields:

- center x
- center y
- radius x
- radius y
- rotation degrees
- coordinate space

Rotation degrees shall describe the undirected long-axis alignment of the visible bee body, not head-to-tail direction.

Rationale: Bees are elongated and appear at many rotations. Oriented ellipses better express human-reviewed bee evidence than axis-aligned rectangles.

### BAR-006 Complete Crop Review

Before a Training Crop can become dataset-eligible, a Dataset Curator shall mark all visible bees in that crop or explicitly mark the crop as incomplete/excluded.

Rationale: For early training, missing bees are as damaging as false positives.

### BAR-007 Bee Annotation Repository

HiveSight shall maintain a Bee Annotation Repository containing reviewed annotation evidence and provenance.

Repository items may initially be crop-level rather than whole-photo-level.

### BAR-008 Initial Model Family

The first trainable HiveSight Bee Detector shall use an oriented object detection approach.

Initial candidate: Ultralytics YOLO OBB nano or small model.

Rationale: YOLO OBB can train on oriented bounding boxes, has a practical training/export path, and is a reasonable first baseline for rotated bee-like objects.

### BAR-009 Ellipse-To-OBB Export

HiveSight shall be able to export reviewed oriented bee ellipses as oriented bounding boxes for the first YOLO OBB training baseline.

The exported model format is not the canonical domain truth. It is a model-specific training projection.

### BAR-010 Trainable Candidate Annotation Model

The HiveSight Bee Detector should become the primary Candidate Annotation helper once the first viable model exists and is approved for that use.

Rationale: A project-owned model can improve with the reviewed annotation repository. Generic pre-labelling helpers cannot learn from HiveSight corrections unless separately fine-tuned.

### BAR-011 Grounding DINO Retirement

Grounding DINO is retired from the active HiveSight solution.

Rationale: Trial use on real brood-frame photos produced poor bee localisation, and continuing to tune it would distract from the project-owned Bee Detector path.

### BAR-012 Rebuild Loop

The project should periodically rebuild the HiveSight Bee Detector from accumulated reviewed repository items.

Every rebuild creates a Training Run and Model Candidate. User-facing use requires benchmark evaluation and human approval.

## Initial Model Decision

The first model baseline should be:

- task: oriented object detection
- implementation candidate: Ultralytics YOLO OBB
- starting size: nano or small
- initial classes:
  - `complete_visible_bee`
  - `partial_visible_bee`
- training data: reviewed crop-level oriented bee ellipses exported as oriented bounding boxes
- candidate output: Candidate Annotations only

## Out Of Scope

- Varroa mite detection training.
- Segmentation masks as the first canonical geometry.
- Full-frame whole-hive performance claims.
- Automatic benchmark promotion.
- Production annotation workforce management.
- Final numeric model success thresholds before seed data exists.

## Open Questions

- What crop dimensions should define `small_crop`, `medium_crop`, and `large_crop`?
- How many reviewed crops are enough for the first YOLO OBB baseline?
- What annotation UI gesture best supports fast oriented ellipse creation and adjustment?
