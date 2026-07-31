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

### 2026-07-30 Slice 0013 Review Recommendations Architecture Decision Pass

Human-confirmed decisions:

- Keep the Analysis Service separate and integrate it later through an async workflow shape.
- Use Postgres for durable Core API product and model-governance metadata.
- Keep image bytes, dataset package files, and future model artifacts outside Postgres.
- Move API-level BDD and browser acceptance to the Postgres-backed path once Slice 0014 lands, while preserving in-memory adapters for fast workflow tests.
- Keep UI acceptance in Playwright specs plus generated verification reports for now; UI-level Gherkin is parked.
- Treat Varroa detection as the product/model goal, but do not imply it is implemented while current slices prove bee annotation and Bee Detector foundations.
- Make Slice 0014 Postgres-backed Bee Annotation Repository persistence the next build slice.
- Make Slice 0015 YOLO OBB Training Baseline `go after Slice 0014`.

AI contribution:

- Created ADR 0003 for Postgres metadata persistence.
- Created ADR 0004 for the Analysis Service async integration direction.
- Added current and proposed system architecture snapshots with diagrams and known gaps.
- Added the Postgres persistence design for the narrow Slice 0014 schema.
- Updated parking-lot and remediation docs so review recommendations are no longer only in chat history.
- Added traceability notes where Varroa requirements could otherwise be mistaken for implemented capability.

Human judgment still required:

- Implement Slice 0014 and verify the first durable persistence path.
- Choose durable queue, production auth, object-storage provider, deployment platform, and Analysis Store ownership when their parked triggers arrive.
- Revisit the dev persona switcher before the next role-specific UI acceptance flow.
- Revisit Varroa-specific slices only after the bee-detector and dataset foundations are sufficiently real.

### 2026-07-31 Slice 0013.5 Domain Model Persistence Stability Gate

Human-confirmed decisions:

- Add `Source Image` as canonical domain language.
- Keep `Inspection Photo` as the product-facing term; an Inspection Photo is the role a Source Image plays when attached to an Inspection.
- Persist `source_images` and `inspection_photos` separately from Slice 0014.
- Implement only `inspection_photo` Source Images in Slice 0014, while preserving the ability to add public/imported/bootstrap Source Images later.
- Source Image owns image/file evidence, dimensions, content hash, provenance, permission status, metadata minimisation status, lifecycle status, and object key.
- Training Crop points directly to Source Image and may also reference Inspection Photo when applicable.
- Hive Configuration is effective-dated history with one active configuration per Hive.
- Dataset Item snapshots capture-time Hive Configuration when resolvable, otherwise assignment-time fallback, otherwise unknown.
- Add one broad `source_group_key`; benchmark Dataset Items require it.
- Hard-block benchmark leakage conflicts by same Source Image or same `source_group_key`; allow training/validation sharing with warning.
- Dataset Items are immutable after assignment and use supersession/withdrawal rather than in-place mutation.
- Source Image, Training Crop, and Dataset Item receive stable immutable human-readable ids.
- Source Image records metadata minimisation status only; raw EXIF/image metadata must not be stored in Postgres.
- Slice 0014 persists a narrow Oriented Bee Ellipse table, not a generic annotation table.

AI contribution:

- Identified persistence edges that could distort the first durable schema.
- Used the grilling workflow to resolve each high-impact modelling decision one at a time.
- Updated glossary, domain model, domain diagram, Postgres persistence design, Slice 0013.5, Slice 0014, and parking-lot artifacts.

Human judgment still required:

- Implement Slice 0014 using the Source Image-aware schema.
- Revisit full Dataset Item audit events before supersession workflow, Dataset Versions, Training Runs, or audit/reporting requirements.
- Revisit Dataset Versions before Slice 0015 training implementation.
- Revisit detailed Hive Component or Box configuration before supporting mixed brood/super workflows or detailed equipment statistics.
- Revisit consent withdrawal and deletion enforcement before hosted/user-submitted model improvement or deletion/purge workflows.
- Revisit stricter split leakage policy before serious benchmark claims or model promotion.

### 2026-07-31 Slice 0014 Postgres-Backed Bee Annotation Repository Persistence

Human-confirmed decisions:

- Use a narrow first durable Postgres schema for Bee Annotation Repository metadata.
- Keep image bytes outside Postgres and store object keys plus minimised source-image metadata only.
- Keep in-memory adapters for fast tests and make Postgres mode opt-in for local development.
- Require `source_group_key` for benchmark Dataset Items across both labelling-session and Training Crop assignment paths.

AI contribution:

- Added SQL migrations and database reset/seed commands.
- Added a Postgres-backed write-through Core API store adapter for the selected persistence path.
- Added `source_images` and `inspection_photos` as separate persisted records with dimensions, content hash, permission/minimisation status, and object keys.
- Added stable human-readable id generation shape for Source Images, Training Crops, and Dataset Items.
- Updated benchmark leakage/domain rules and the small UI affordance needed for benchmark source-group capture.
- Added migration contract tests and an opt-in real Postgres restart integration test.
- Verified the full non-Docker slice suite with `pnpm verify:slice`.

Closeout verification:

- Docker was available for local Postgres verification.
- `pnpm db:reset` rebuilt and seeded the local Postgres schema.
- `HIVESIGHT_TEST_DATABASE_URL=postgresql://hive_sight:hive_sight@localhost:5432/hive_sight_core services/core-api/.venv/bin/python -m pytest services/core-api/tests/test_postgres_persistence_slice.py -p no:cacheprovider` passed with `2 passed`.
- Slice 0014 is now acceptance-closed for the live Postgres restart path.

Human judgment still required:

- Decide whether the repo-local migration runner is sufficient for the next few slices or whether to move to Alembic before schema churn increases.
- Revisit Dataset Versions before Slice 0015 training implementation.
- Revisit training-versus-validation leakage warnings before serious model quality claims.

### 2026-07-31 Slice 0015 YOLO OBB Training Baseline Planning

Human-confirmed direction:

- Proceed toward the first HiveSight Bee Detector training baseline using YOLO OBB.
- Keep bee detection and Varroa mite detection as separate logical model stages.
- Do not use generative AI as the planned baseline approach.
- Use reviewed Training Crops with canonical Oriented Bee Ellipses as the training evidence.
- Treat Candidate Annotations as useful acceleration only after human governance.

AI contribution:

- Reshaped Slice 0015 around a repeatable local Bee Detector training pipeline rather than a vague "train a model" milestone.
- Added automation-bias controls to the slice plan: the baseline report must distinguish human-from-scratch and AI-assisted-reviewed evidence, and warn when blind-review comparison evidence is absent.
- Added benchmark realism controls: benchmark data must remain protected from training and the report must warn if benchmark evidence is empty or easy-only.
- Added the future Varroa training dependency risk to the parking lot so mite training is not built solely from Bee Detector-found bees by accident.

Human judgment still required:

- Implement the Slice 0015 planning decisions after the follow-up grilling pass.
- Keep Varroa training source independence parked until before the first Varroa-specific slice.

### 2026-07-31 Slice 0015 Grilling Closeout

Human-confirmed decisions:

- Slice 0015 will implement durable Dataset Versions, not just export manifests.
- Dataset Versions freeze active reviewed Training Crop evidence, protected benchmark metadata, exclusions, selection criteria, review provenance, Hive Configuration context, source group context, and manifest hashes.
- Unreviewed Candidate Annotations are excluded from Dataset Versions.
- Grounding DINO is retired from the active solution and recorded in ADR 0005.
- The active model direction is a HiveSight-owned Bee Detector, with YOLO OBB as the first replaceable implementation candidate.
- YOLO training is opt-in. Normal app startup and fast tests use a fake adapter and do not require YOLO dependencies or network access.
- Real YOLO setup/training should have memorable commands rather than long environment-variable incantations.
- Real-adapter QA is a separate verification lane, distinct from the default CI/fast test lane.
- Local Postgres should separate dev, test, and QA databases so automated tests do not wipe curator or QA model evidence.
- Training artifacts live outside Postgres under a configurable artifact root; Postgres stores metadata, relative paths, hashes, status, settings, warnings, and provenance.
- Reports must distinguish hard failures from governance warnings, use stable warning codes, and avoid raw personal/location metadata.
- Model Candidates created by Slice 0015 are Bee Detector candidates only, not user-facing Model Versions and not Varroa assessment capability.
- Public dataset annotation import is deferred to Slice 0015.1.
- Full-frame/tiling export is parked for a later model-data slice.

AI contribution:

- Used the grilling workflow to resolve implementation-affecting edge cases one at a time.
- Identified database purpose separation as a safety prerequisite for model-training work.
- Proposed the Candidate Annotation domain language to replace "AI guess" and Grounding DINO-specific pre-labelling language.
- Separated fake-adapter verification, real-adapter QA, and production-readiness claims.
- Added artifact-serving and report-safety guardrails before local model artifacts become part of the workflow.

Human judgment still required:

- During implementation, decide whether local database purpose separation remains small enough to stay in Slice 0015 or should be split into Slice 0014.6.
- Choose the exact pinned Ultralytics dependency version.
- Decide whether the first real-adapter QA command can be fully automated in Slice 0015 or should be a command plus manual QA script.
