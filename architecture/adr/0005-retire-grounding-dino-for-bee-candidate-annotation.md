# ADR 0005: Retire Grounding DINO For Bee Candidate Annotation

Date: 2026-07-31

## Status

Accepted

## Context

Slice 0007 introduced Grounding DINO as a local pre-labelling adapter so HiveSight could create machine-proposed bee Draft Annotations while preserving human review as the trust boundary.

Real brood-frame trial images showed that Grounding DINO was not useful enough for HiveSight's bee candidate annotation workflow. It produced poor localisation for the dense, rotated, partly occluded bees found on brood-frame photos, and it encouraged continued investment in a helper that cannot learn from HiveSight's reviewed annotation repository.

HiveSight also now has a clearer model direction: build a project-owned Bee Detector from reviewed oriented bee ellipse evidence, with YOLO OBB as the first implementation candidate behind a replaceable adapter seam.

## Decision

Grounding DINO is retired from the active HiveSight solution.

Active setup commands, runtime configuration, adapter registration, tests, and current architecture docs should no longer treat Grounding DINO as a supported pre-labelling path.

The replacement direction is a HiveSight-owned Bee Detector that proposes Candidate Annotations for human review. YOLO OBB is the first selected training baseline for that Bee Detector, but the architecture should preserve a model adapter seam so HiveSight can replace the model family later if the reviewed dataset points elsewhere.

## Consequences

- Historical Slice 0007 documentation can remain as evidence of what was tried.
- Grounding DINO-specific dependencies should be removed if they are not needed by the YOLO training path.
- Active product, requirements, and architecture language should use Candidate Annotation rather than Grounding DINO-specific pre-labelling language.
- Candidate Annotations are never ground truth. They require human review before they can enter Dataset Versions.
- Future model-training work should focus on reviewed HiveSight data rather than continuing to tune Grounding DINO prompts or thresholds.
