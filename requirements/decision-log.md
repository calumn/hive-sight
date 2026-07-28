# Decision Log

## 2026-07-28 Varroa Detection Is The Primary Product Focus

Decision: BeehiveMonitor will focus primarily on Varroa mite detection from hive inspection photos.

Rationale: The user clarified that the core value is detecting Varroa mites, counting bees, and estimating infection rate from submitted frame photos.

Implications:

- Image upload and analysis are central capabilities.
- Apiary and hive management should support inspection context rather than become a full beekeeping management suite.
- Requirements should prioritise inspection events, photo association, bee counting, Varroa detection, and infection-rate estimation.

## 2026-07-28 Web UI First, Mobile Later

Decision: The first version should likely be a web UI, with Android and Apple apps considered later.

Rationale: A web UI supports faster initial validation. Mobile apps are likely useful for field capture but can follow once core workflows and APIs are clearer.

Implications:

- The data model and backend should not be tightly coupled to the web UI.
- Future mobile workflows should be considered when designing photo capture and upload.

## 2026-07-28 Lightweight Apiary Management

Decision: The system should include lightweight apiary management: apiaries, hives, inspections, and photo associations.

Rationale: Varroa analysis needs to be tied to a specific hive and inspection event.

Implications:

- The first data model should include apiary, hive, inspection event, photo, and analysis result entities.
- Full beekeeping operations management is not assumed for the first version.

## 2026-07-28 Version-One User Is Hobbyist Or Small-Scale Beekeeper

Decision: Version one will target hobbyist or small-scale beekeepers managing their own apiaries and hives.

Rationale: This keeps the first version focused on a practical inspection-support workflow rather than a professional, advisory, research, or regulatory workflow.

Implications:

- The product should optimise for low-friction recording and review.
- The language should support beekeeper decision-making without claiming clinical or official authority.
- The first requirements baseline does not assume multi-tenant commercial operations, formal advisory reporting, or regulated diagnostic use.

## 2026-07-28 AI Estimate Boundary

Decision: Varroa outputs will be presented as AI-assisted visual estimates, not diagnoses, treatment recommendations, or official infestation measurements.

Rationale: Version one has not established field validation, accuracy thresholds, or treatment protocols.

Implications:

- UI copy must avoid diagnostic and prescriptive claims.
- Results should include confidence, caveats, and visible evidence.
- Acceptance criteria should verify that result wording preserves this boundary.

## 2026-07-28 Tagged Image Evidence And Correction Loop

Decision: Analysis output will include tagged-up photos showing likely Varroa detections, with optional display of all detected bees and lightweight user correction.

Rationale: Tagged photos give the beekeeper an empirical sense of model accuracy, and corrections create useful evidence for future model evaluation.

Implications:

- The system should store original images and structured annotation data.
- The first correction tools should cover false Varroa detections and missed likely Varroa locations.
- Version one should not attempt to become a full annotation studio.

## 2026-07-28 Initial Metric Is Mites Per 100 Visible Bees

Decision: The first Varroa metric will be likely Varroa detections associated with complete visible bees per 100 estimated complete visible bees in uploaded photos.

Rationale: This is understandable and aligned with the image evidence the system actually has.

Implications:

- The system must clearly say the estimate is based only on visible bees in uploaded photos.
- The metric should not be presented as a whole-hive infestation rate.
- Multiple photos of the same frame require careful caveats or grouping to avoid misleading aggregation.
- Partial visible bees and unassociated visible Varroa should be reported as additional evidence rather than silently included in the headline metric.

## 2026-07-28 Model Requirements Are Separate From Product Requirements

Decision: AI model training, dataset, evaluation, privacy, consent, and release-gate requirements will live in a separate `model-requirements.md` document.

Rationale: Product requirements define what the beekeeper-facing system must do. Model requirements define what evidence and governance are needed before trusting the AI capability.

Implications:

- The product requirements can reference model capability without carrying all training and evaluation detail.
- Model provenance, annotation quality, benchmark separation, and promotion gates remain explicit and auditable.
- Future architecture and implementation work should treat model lifecycle as a first-class concern.

## 2026-07-28 Logical Two-Stage Model Pipeline

Decision: The model requirements will define a logical two-stage pipeline: detect bees first, then detect Varroa on or near detected bees.

Rationale: Bee detection and Varroa detection have different difficulty, metrics, and failure modes.

Implications:

- The implementation may still use one model or multiple models.
- Evaluation must measure bee detection and Varroa detection separately.
- The denominator for the headline estimate should use complete visible bees, while partial bees are tracked separately.

## 2026-07-28 User Corrections Require Review Before Dataset Use

Decision: User corrections will be stored as review candidates, not automatically used as training data.

Rationale: Corrections are valuable evidence but may be wrong, uncertain, accidental, or based on unsuitable images.

Implications:

- A human reviewer can approve, reject, mark uncertain, exclude, or assign corrected annotations to training, validation, or benchmark roles.
- User-submitted photos and corrections require explicit consent before model-improvement use.
- Benchmark data should remain protected from training and routine threshold tuning.
