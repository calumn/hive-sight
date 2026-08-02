# ADR 0006: Directed Bee Ellipse Orientation

Status: accepted

## Context

HiveSight stores reviewed bee annotations as Oriented Bee Ellipses. ADR 0002 originally defined ellipse rotation as undirected body-axis alignment: an ellipse at 30 degrees and one at 210 degrees described the same bee body axis.

That was sufficient for the first Bee Detector baseline, but later Varroa detection may benefit from knowing where the bee's head is. Likely Varroa location can be bee-orientation dependent, and a future Varroa Detector may train more effectively if bee crops can be normalized or interpreted relative to head and tail.

## Decision

HiveSight will treat Oriented Bee Ellipse rotation as directed.

`rotation_degrees` points from the ellipse center toward the bee's head along the major axis. The opposite end of the same axis is the tail.

The annotation does not need a separate head marker. The ellipse itself carries head/tail direction through its rotation semantics, and the UI must make that direction visually obvious.

For the current early local dataset, existing downstream dataset/model evidence should be discarded and rebuilt after manual head/tail review. Existing uploaded photos, Training Crops, and ellipses can be preserved; their stored rotations become the starting point for review, not trusted final head direction.

## Considered Options

- Keep undirected ellipse rotation and defer head/tail evidence.
- Add a separate head-point marker to each bee annotation.
- Treat ellipse rotation as directed and add a flip head/tail control.
- Add a persistent "direction unknown" or "head direction review needed" state for legacy ellipses.

## Rationale

Keeping orientation undirected would preserve the simplest Bee Detector label but discard evidence that may matter for Varroa detection. A separate head marker would add another geometry object and more annotation burden than needed.

Directed ellipse rotation keeps the canonical shape simple while preserving the head/tail semantics needed later. A Dataset Curator can rotate the ellipse until the visible head end points at the bee's head, or flip the direction by 180 degrees when the geometry is correct but reversed.

Because HiveSight is still in one-user local development with a small number of annotated crops, a one-time cleanup is simpler than introducing a legacy direction-review state machine. Stale Dataset Items, Dataset Versions, Training Runs, Model Candidates, and derived artifacts can be removed and recreated after review.

## Consequences

- Existing Training Crop ellipses created before this decision keep their stored `rotation_degrees` as a review starting point. They should be manually checked before being reassigned into new Dataset Items.
- Existing early local Dataset Items, Dataset Versions, Training Runs, Model Candidates, and derived artifacts may be removed and rebuilt rather than migrated.
- The Training Crop UI must render a visible head/tail distinction and provide a flip head/tail control.
- Candidate Annotations from YOLO OBB may propose geometry, but head/tail direction remains human-reviewed unless a future model explicitly proposes reliable direction.
- Dataset Items and Dataset Versions continue to snapshot `rotation_degrees`; the semantic meaning of that value is now directed.
- YOLO OBB export remains geometrically compatible, but YOLO OBB labels should not be treated as preserving head/tail semantics unless a later export format explicitly supports it.
