# Oriented Ellipse Canonical Bee Annotations

Status: accepted

## Context

HiveSight needs reviewed bee annotations that are useful both for human evidence review and for training the first bee detector. Bees on brood frames are elongated, overlap with comb, and appear at many rotations. The Grounding DINO pre-labelling spike showed that generic open-vocabulary detection is not good enough as the main strategy for dense bee-on-comb detection.

The project needs a canonical annotation shape that reflects what a human reviewer means by "this visible bee" while still allowing export into practical model-training formats.

## Decision

HiveSight will store human-reviewed bee annotations as oriented bee ellipses.

Ellipse rotation represents the visible bee body's undirected long-axis alignment. It does not record head-to-tail direction. For bee detection, an ellipse at `30 degrees` and an ellipse at `210 degrees` describe the same body axis.

The first trainable HiveSight Bee Detector baseline will use YOLO OBB nano or small. Reviewed oriented bee ellipses will be exported into oriented bounding boxes for YOLO OBB training.

The YOLO OBB label is a model-specific projection. It is not the canonical domain truth.

## Considered Options

- Axis-aligned rectangles as canonical geometry.
- Oriented bounding boxes as canonical geometry.
- Segmentation masks as canonical geometry.
- Oriented ellipses as canonical geometry, with model-specific exports.

## Rationale

Oriented ellipses match the visible shape of bees better than axis-aligned rectangles and are faster to create than segmentation masks. They also let the project preserve reviewer intent while exporting to oriented object detection formats for training.

Head-end direction is deliberately not part of the canonical bee annotation at this stage. Asking curators to identify head direction would slow early dataset creation and introduce a noisier label than the first Bee Detector needs.

YOLO OBB is a practical first baseline because it can learn rotated objects, has an accessible local training path, and can be replaced later if the growing dataset shows a better model family is needed.

## Consequences

- The annotation UI must support creating, moving, resizing, and rotating oriented ellipses.
- Annotation guidance must be clear that rotation means body-axis alignment, not anatomical head direction.
- Dataset exports must convert reviewed ellipses into YOLO OBB labels for the first detector baseline.
- Metrics and visual review should be clear about whether they are evaluating canonical ellipses or exported model labels.
- Grounding DINO remains an experimental helper and comparison point, not the primary training strategy.
- Later segmentation, keypoint, or specialist detector approaches remain possible without changing the canonical reviewed evidence already captured.
