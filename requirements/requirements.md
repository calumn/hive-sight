# Requirements

This document captures early candidate requirements. Requirement IDs are provisional until the first baseline.

Detailed AI model, dataset, training, evaluation, and release-gate requirements are captured separately in `model-requirements.md`.

## Functional Requirements

### FR-001 Apiary Management

The system shall allow a user to define an apiary.

Rationale: Photos and inspections need to be organised by real-world apiary location or grouping.

### FR-002 Hive Management

The system shall allow a user to define hives within an apiary.

Rationale: Varroa assessment is meaningful at hive level, not only at account or apiary level.

### FR-003 Inspection Events

The system shall allow a user to create an inspection event for an individual hive.

Rationale: Photos, observations, and Varroa analysis need to be associated with a specific inspection.

### FR-004 Photo Association

The system shall allow a user to associate one or more photos with a hive inspection event.

Rationale: A single frame may have multiple photos, and one inspection may cover multiple frames.

### FR-005 Multiple Photos Per Frame

The system should support optional frame labels so multiple photos can be marked as belonging to the same frame without requiring heavy frame management in version one.

Rationale: Varroa detection may benefit from additional image coverage, but the first version should avoid slowing the product with complex frame modelling.

### FR-006 Bee Counting

The system shall estimate the number of complete visible bees in each submitted photo and report partial visible bees separately where possible.

Rationale: Complete visible bee count is needed for the headline Varroa estimate. Partial bees are useful evidence but should not silently distort the denominator.

### FR-007 Varroa Detection

The system shall detect likely visible Varroa mites on bees in submitted photos.

Rationale: Varroa detection is the core purpose of the system.

### FR-008 Infection-Rate Estimate

The system shall calculate an estimated visible Varroa rate as likely Varroa detections associated with complete visible bees per 100 estimated complete visible bees in the submitted photo set.

Rationale: The user needs a summary measure that can support decision-making without implying a whole-hive infestation rate.

### FR-009 Result Review

The system should present image-level and inspection-level analysis results in a way that allows the user to understand what was counted or detected.

Rationale: AI image analysis requires transparency to support user trust and correction.

### FR-010 Tagged Photo Output

The system shall present a tagged-up version of each analysed photo showing likely Varroa detections on bees.

Rationale: The user needs visual evidence behind the estimate to judge whether the model appears accurate.

### FR-011 Optional Bee Detection Overlay

The system should allow the user to view other detected bees in the image in addition to likely infected bees.

Rationale: Showing the denominator visually gives the user an empirical sense of how the bee count was derived.

### FR-012 Human Correction Loop

The system shall allow a user to mark a likely Varroa tag as incorrect and mark a missed likely Varroa location.

Rationale: Lightweight corrections provide trust, reviewability, and future model-evaluation evidence without requiring a full annotation studio.

### FR-013 Photo And Annotation Storage

The system shall store original photos, analysis results, and reusable annotation data.

Rationale: Original images and structured annotations are needed for auditability, re-rendering tagged images, and later model evaluation.

### FR-016 User Data Consent For Model Improvement

The system shall not automatically use uploaded photos or user corrections as model training data without explicit consent and review.

Rationale: Analysis use, correction review, and model-improvement use are separate concerns with different trust and privacy implications.

### FR-014 Web UI

The system shall provide a web user interface for the first version.

Rationale: A web UI is the most practical initial interface for rapid development and validation.

### FR-015 Future Mobile Apps

The system should be designed so Android and Apple applications can be added later.

Rationale: Mobile capture is likely valuable during real hive inspections.

## Non-Functional Requirements

### NFR-001 Traceability

The project shall maintain traceability from stakeholder needs to requirements, design decisions, implementation, tests, and production evidence.

Rationale: The project is also an AI-SDLC study.

### NFR-002 Explainability

The system should communicate uncertainty, confidence, and limitations for AI-generated Varroa analysis.

Rationale: Incorrect Varroa assessment could mislead treatment decisions.

### NFR-005 Claim Boundary

The system shall present Varroa analysis as an AI-assisted visual estimate, not as a diagnosis, treatment recommendation, or official infestation measurement.

Rationale: Version one is decision support and model-learning evidence, not a validated diagnostic product.

### NFR-003 Data Organisation

The system shall preserve relationships between apiaries, hives, inspections, frames, photos, and analysis results.

Rationale: Historical inspection context is central to the product.

### NFR-004 Extensibility

The system should separate core data and analysis capabilities from UI-specific implementation choices.

Rationale: Future web, Android, and Apple clients should be able to share the same underlying data and analysis services.

## Open Requirements Questions

- Should infection rate be calculated per image, per frame, per inspection, or all three?
- What wording should be used consistently for "mites per 100 visible bees"?
- What image formats and maximum upload sizes should be supported?
- What level of model confidence is needed before a detection is shown to the user?
- Should the system support offline capture later?
- What field evidence is needed to validate the Varroa detection approach?
- What user consent language is needed before photos or corrections can be used for model improvement?
