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

### 2026-07-30 Architecture And Vertical Slice Delivery Baseline

Human-confirmed decisions:

- Use thin, demonstrable vertical slices rather than a large upfront platform build.
- Keep Core API, Web UI, and Analysis Service as separate service boundaries.
- Use API-level BDD scenarios for acceptance behaviour first.
- Add browser acceptance tests once the local web harness was available.
- Treat AI-assisted annotation as human-verified evidence, not automatic ground truth.
- Start bee annotation with rotated ellipses because bee pose matters for training.
- Use YOLO OBB as the first trainable model direction, while keeping model adapters swappable.
- Separate inspection intent between training-data collection and Varroa assessment.
- Require Hive Configuration from Slice 12 onward because frame standards can affect later statistics and bias analysis.

AI contribution:

- Proposed slice boundaries, test seams, and acceptance criteria from evolving product discussions.
- Converted repeated human decisions into architecture notes, BDD scenarios, API tests, and browser acceptance tests.
- Identified where model lifecycle concepts needed dedicated requirements before deeper model work.
- Helped keep domain language stable across requirements, architecture, Python contracts, TypeScript client types, and UI copy.

Human judgment still required:

- Choose real persistence, queue, object-storage, auth, and deployment technologies.
- Decide when the Analysis Service must be wired into the Core API flow rather than remaining a tested but orphaned service.
- Decide whether UI-level Gherkin is still a required delivery standard or should be explicitly dropped.
- Verify starter Hive Configuration frame dimensions before using them for production claims or calibration.

### 2026-07-30 External Review Remediation Pause

Human-confirmed decisions:

- Pause new functional slices until the external review findings have been triaged and actioned.
- Treat the unauthenticated unused upload-url endpoint as a real risk despite being unwired.
- Resolve duplicate slice documentation before building more slices on top of it.
- Resume this AI-SDLC observations log because it is part of the project's stated learning goal.

AI contribution:

- Verified the external findings against the current repository state.
- Removed the dead upload-url route and its misleading test rather than preserving an unsafe future trap.
- Marked the earlier, narrower Slice 0010 document as superseded by the implemented Slice 0010 export specification.
- Added this observation entry to restore the feedback loop between delivery, review, and learning artifacts.

Human judgment still required:

- Decide how far to go before the next functional slice: immediate small fixes only, or a deeper architecture-debt slice.
- Decide whether to extract authorization, validation, and geometry logic out of `dev_store.py` before adding persistence.
- Decide whether to keep Analysis Service separate and wire it, or fold the current stub behaviour back into Core API until model work is real.

### 2026-07-30 Skills Remediation And Parking Lot

Human-confirmed decisions:

- Implement the skills remediation rather than leaving it as a review document.
- Keep generic `sdlc-*` skills reusable by moving HiveSight-specific defaults into a project-specific skill.
- Create an explicit parking-lot artifact for important deferred work.
- Review relevant parked items when planning new slices or remediation tranches.
- Defer security, API contract governance, and release readiness skills until their trigger conditions arrive.

AI contribution:

- Created `hivesight-project-delivery-context`, `sdlc-governance-traceability-audit`, `sdlc-architecture-persistence-design`, and `sdlc-skills-library-review`.
- Removed stale project-specific and borrowed-template guidance from generic skills.
- Embedded concise closeout and parking-lot checks into high-use SDLC skills.
- Added `architecture/parking-lot.md` with initial deferred items and revisit triggers.
- Validated the skills library and updated `architecture/skills-remediation-2026-07-30.md` with completion evidence.

Human judgment still required:

- Revisit UI-level Gherkin before the next major UI workflow.
- Create security, API contract governance, and release readiness skills when the parked triggers occur.
- Use the traceability-audit skill before restarting functional slice delivery.

### 2026-07-30 Review Remediation 0001 Implementation

Human-confirmed decisions:

- Resume implementation after the skills remediation and parking-lot pattern were in place.
- Treat Review Remediation 0001 as a behaviour-preserving refactor, not a functional product slice.
- Keep real persistence out of scope while making future persistence easier.

AI contribution:

- Added direct workflow tests for Hive Configuration/Inspection gating, Training Crop rules, and Training Crop Dataset Item assignment.
- Added `HiveConfigurationWorkflow`, `TrainingCropWorkflow`, and `TrainingCropDatasetItemWorkflow`.
- Rewired Core API routes to call injected workflows for the moved rule clusters.
- Added persistence-shaped methods to `InMemoryProductDataStore` while preserving public API behaviour.
- Verified the remediation with `pnpm verify:slice`.

Human judgment still required:

- Decide the real persistence technology and migration path.
- Decide when Workspace authorization and Data Use Agreement checks should move from dev-store helpers into explicit policy services.
- Extract YOLO OBB export/package construction out of `dev_store.py` before export persistence or long-running package generation becomes load-bearing.
