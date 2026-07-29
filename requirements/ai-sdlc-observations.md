# AI-SDLC Observations

This document records how AI contributes to the requirements phase and later SDLC phases.

## Observation Log

### 2026-07-28 Requirements Scope Clarification

Human input clarified that HiveSight is primarily focused on detecting Varroa mites rather than general hive telemetry.

Captured product concepts:

- Submit photos of a frame or frames.
- Submit multiple photos of the same frame.
- Count visible bees.
- Detect Varroa mites on bees.
- Estimate an infection rate.
- Provide a web UI first.
- Consider Android and Apple apps later.
- Add lightweight apiary management.
- Define apiaries and hives.
- Associate photos with an inspection event for an individual hive.

AI contribution:

- Structured the input into initial vision, stakeholder, requirement, and acceptance-criteria documents.
- Identified early open questions around image grouping, infection-rate calculation, manual correction, confidence, and validation evidence.

Subsequent human decisions resolved:

- Version one targets hobbyist or small-scale beekeepers.
- The headline metric uses likely Varroa detections associated with complete visible bees per 100 estimated complete visible bees.
- Manual correction of false positives and missed likely Varroa detections is in scope.
- Version one stores original photos plus reusable annotation data.

## Risks Noted

- AI may overstate detection reliability before field validation exists.
- Infection-rate estimates may be misleading if image quality, frame coverage, or bee visibility is poor.
- Multiple photos of the same frame could double-count bees or mites unless the data model handles grouping carefully.
- Requirements may accidentally imply medical or treatment advice unless language is carefully scoped.

### 2026-07-28 Requirements Grilling Baseline

Human-confirmed decisions:

- Version one is for hobbyist or small-scale beekeepers.
- The system should present AI-assisted visual estimates, not diagnoses, treatment recommendations, or official infestation measurements.
- The version-one workflow should be apiary, hive, inspection event, photos, then analysis review.
- Frame-level modelling should stay light, using optional frame labels rather than a heavy frame-management model.
- The output should include tagged-up photos showing potentially infected bees.
- The output may optionally show all other detected bees.
- Users should be able to correct false Varroa tags and mark missed likely Varroa.
- The main first metric should be mites per 100 complete visible bees in uploaded photos.
- Version one should store original photos plus reusable annotation data and render tagged images from that data.

AI contribution:

- Used a grilling-style interview to resolve high-impact product decisions one at a time.
- Converted confirmed decisions into requirement, acceptance-criteria, decision-log, and spec updates.

Human judgment still required:

- Define model performance expectations.
- Define photo quality guidance.
- Decide whether corrected annotations become training data, evaluation data, or both.

### 2026-07-28 Model Requirements Grilling Baseline

Human-confirmed decisions:

- The first model task is object detection on inspection photos.
- The model requirements should define a logical two-stage pipeline: bee detection first, Varroa detection second.
- The implementation may use one model or multiple models.
- Bee annotations should use bounding boxes where practical.
- Varroa annotations should use point markers or small bounding boxes.
- Segmentation masks are deferred for version one.
- The model should distinguish complete visible bees, partial visible bees, and uncertain bees.
- The headline denominator should use complete visible bees.
- Partial visible bees should be reported separately.
- Varroa detections should be associated with complete bees, partial bees, or an unassociated visible Varroa state.
- Partial or unassociated Varroa should be reported as additional evidence rather than silently folded into the headline metric.
- Public or externally sourced images may be used for bootstrapping if provenance, licence, and permission are recorded.
- User corrections are review candidates, not automatic training data.
- Training, validation, benchmark, and excluded dataset roles should be separate.
- Model promotion requires documented benchmark evaluation and human approval.
- Numeric promotion thresholds are deferred until baseline data exists.
- Low-quality photos should produce warnings and may be downgraded or excluded.
- Privacy, consent, provenance, and metadata minimisation are required for training data.

AI contribution:

- Structured the model lifecycle concerns into a separate model requirements baseline.
- Identified governance requirements around ground truth, dataset roles, release gates, and consent.

Human judgment still required:

- Select the first annotation tool.
- Decide what public datasets are usable.
- Define first benchmark size and review process.
- Choose the first model or service for prototyping.
