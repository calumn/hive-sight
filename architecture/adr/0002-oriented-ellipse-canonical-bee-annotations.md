# Oriented Ellipse Canonical Bee Annotations

Status: accepted

Supersession note: ADR 0006 changes the rotation semantics from undirected body-axis alignment to directed center-to-head orientation. This ADR still stands for the choice of oriented ellipses as canonical bee annotation geometry.

## Context

HiveSight needs reviewed bee annotations that are useful both for human evidence review and for training the first bee detector. Bees on brood frames are elongated, overlap with comb, and appear at many rotations. The Grounding DINO pre-labelling spike showed that generic open-vocabulary detection is not good enough as the main strategy for dense bee-on-comb detection.

The project needs a canonical annotation shape that reflects what a human reviewer means by "this visible bee" while still allowing export into practical model-training formats.

## Decision

HiveSight will store human-reviewed bee annotations as oriented bee ellipses.

At the time of this ADR, ellipse rotation represented the visible bee body's undirected long-axis alignment. ADR 0006 later superseded that part of the decision: `rotation_degrees` now represents directed center-to-head orientation along the major axis.

The first trainable HiveSight Bee Detector baseline will use YOLO OBB nano or small. Reviewed oriented bee ellipses will be exported into oriented bounding boxes for YOLO OBB training.

The YOLO OBB label is a model-specific projection. It is not the canonical domain truth.

## Considered Options

- Axis-aligned rectangles as canonical geometry.
- Oriented bounding boxes as canonical geometry.
- Segmentation masks as canonical geometry.
- Oriented ellipses as canonical geometry, with model-specific exports.

## Rationale

Oriented ellipses match the visible shape of bees better than axis-aligned rectangles and are faster to create than segmentation masks. They also let the project preserve reviewer intent while exporting to oriented object detection formats for training.

Head-end direction was deliberately not part of the original canonical bee annotation decision. ADR 0006 revisits that trade-off after the project identified likely Varroa-location dependency on bee orientation.

YOLO OBB is a practical first baseline because it can learn rotated objects, has an accessible local training path, and can be replaced later if the growing dataset shows a better model family is needed.

## Consequences

- The annotation UI must support creating, moving, resizing, and rotating oriented ellipses.
- Annotation guidance must follow ADR 0006: rotation now means directed center-to-head orientation.
- Dataset exports must convert reviewed ellipses into YOLO OBB labels for the first detector baseline.
- Metrics and visual review should be clear about whether they are evaluating canonical ellipses or exported model labels.
- Grounding DINO remains an experimental helper and comparison point, not the primary training strategy.
- Later segmentation, keypoint, or specialist detector approaches remain possible without changing the canonical reviewed evidence already captured.
