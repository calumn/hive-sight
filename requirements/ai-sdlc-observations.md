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

### 2026-08-02 Slice 0015.35 Directed Bee Ellipse Orientation Planning

Human input changed Oriented Bee Ellipse semantics from undirected body-axis alignment to directed center-to-head orientation.

Key decisions:

- `rotation_degrees` now points from ellipse center toward the bee's head along the major axis.
- The opposite end of the same axis is the tail.
- No separate head marker is required in the data model; the ellipse itself carries direction.
- The UI must make head/tail direction visible and provide a flip head/tail control.
- The rationale is future Varroa detection: likely mite location may be bee-orientation dependent, so preserving head direction may strengthen later Varroa training and inference.
- Existing early local downstream dataset/model evidence should be removed and rebuilt rather than migrated.
- Uploaded photos, Training Crops, and existing ellipses should be preserved as review starting points.
- No persistent "head direction review needed" status is needed for the current seven-crop one-user cleanup.
- Candidate Annotation geometry from YOLO OBB is not trusted as biological head direction; human review decides final directed orientation.

Follow-up:

- Implement Slice 0015.35 before relying on model-candidate evaluation or Varroa-direction-dependent evidence.
- PARK-0028 records that future real hive inspections need automated bee head-direction prediction, not just human-reviewed directed ellipses, before the Varroa Detector can rely on consistently oriented bee crops without human intervention.

### 2026-08-02 Three-Stage Model Pipeline Decision

Human-confirmed direction:

- Treat Bee Localisation, Bee Orientation, and Varroa Detection as distinct logical Model Purposes.
- The current YOLO OBB HiveSight Bee Detector is Bee Localisation only. Its oriented geometry must not be interpreted as biological head/tail prediction.
- Use directed reviewed ellipses as future orientation-training evidence.
- Use a binary head/tail classifier on body-axis-normalized bee crops as the first Bee Orientation baseline, while retaining keypoint/pose and multi-head alternatives if benchmark evidence later shows it is inadequate.
- Give Varroa Detection a bee-relative, head-normalized crop whenever orientation is reliable. Exclude unreliable-orientation bees from the first head-normalized Varroa training and benchmark corpora, while retaining them for Bee Localisation evidence and supplementary Varroa evidence.
- Record Orientation Reliability explicitly as reviewed evidence (`reliable` or `unreliable`), separate from bee-presence confidence and review status.
- Return the current seven manually directed crops for one-time Orientation Reliability review before they enter an orientation or head-normalized Varroa dataset.
- Train and benchmark the first Bee Orientation Model only on reliably oriented complete visible bees; retain reliably oriented partial bees for a later separately reported evaluation.
- Require the first Varroa capability to return a visible mite point or tight bounding box on the normalized bee crop, rather than only a bee-level presence/absence result.
- Use high-resolution, standard axis-aligned YOLO detection for the first Varroa baseline; defer oriented mite boxes and segmentation.
- Require human-selected bee crops in Varroa training and benchmark data, independent of Bee Localisation and Bee Orientation outputs, so the downstream model does not inherit upstream blind spots by construction.
- Record Dataset Selection Method for Varroa Dataset Items and report the mix in benchmark results. `human_selected` requires blind selection before upstream suggestions are seen; any model-influenced selection is `upstream_model_selected`. Defer a numerical quota until there is enough data to justify one.
- In the first live pipeline, record `not_assessed_orientation_unreliable` for a localised bee whose head direction is not reliable; do not run Varroa detection on a guessed rotation.
- Use a CAPTCHA-like Varroa curation workflow: every bee-relative crop is actively marked `visible_varroa_present`, `no_visible_varroa`, or `not_determined`. Only the first two outcomes are positive/negative training or benchmark evidence; silence is never a negative label.
- Keep `model_curation` sampling distinct from future `inspection_rate_estimation` sampling. They may share review UI, but only the latter supports a future rate estimate with its own sampling-plan metadata; PARK-0030 tracks that design.
- Default model curation to stratified-random sampling across available Hive, frame, bee-density, lighting, and image-quality strata, while retaining deliberately difficult curator-targeted examples as a separately reported method.
- Freeze benchmark evidence from a predeclared sampling plan before running the evaluated candidate; do not add examples because that candidate succeeded or failed on them.
- Permit one active curator review for early baseline benchmark Varroa evidence only when the report states that limitation. Require Blind Independent Review, with the second reviewer unable to see the first outcome or marker positions, and Third-Party Adjudication by a reviewer distinct from both originals who first records a fresh blind review before seeing anonymised prior reviews, before a candidate can be considered for user-facing Varroa Assessment. An unresolved disagreement, including a three-way conflict, becomes `not_determined` and remains outside Varroa training and benchmark evidence.
- Require Varroa Benchmark Evaluations to report outcome agreement, one-to-one matched marker-location agreement in bee-relative coordinates, unmatched-marker counts, adjudication and unresolved-disagreement counts, and items lacking independent second review; defer numerical thresholds until project evidence can support them.
- Reserve Blind Independent Review and Third-Party Adjudication for protected benchmark Varroa evidence used in user-facing promotion; allow training and validation evidence to use one active reviewed outcome with retained provenance.
- Periodically select a stratified-random, non-blocking quality-audit sample of training and validation Varroa Reviews for Blind Independent Review, and report its agreement, disagreement, and unresolved outcomes separately from benchmark evidence and by Annotation Source, including human-from-scratch and AI-assisted-reviewed evidence; defer audit sample size and escalation thresholds until enough project review volume exists.
- When a quality audit is concerning, require a documented Dataset Curator Audit Disposition and a warning on every affected Dataset Version rather than an automatic threshold-based block.
- Require the Model Approver to explicitly acknowledge an affected Dataset Version's Audit Disposition before user-facing Varroa promotion.
- Require a protected End-to-End Pipeline Evaluation on a separate full-frame selection snapshot whose predeclared plan and source groups are frozen before candidate selection or tuning, and which is source-group-disjoint from training, validation, and the individual Bee Localisation, Bee Orientation, and Varroa Detection benchmarks, before user-facing Varroa promotion.
- Require the end-to-end full-frame evidence to include every visible reviewed bee, its Orientation Reliability, and the relevant Varroa Review Outcome, so coverage has an honest denominator.
- Require the End-to-End Pipeline Evaluation to report localised-bee to Varroa-Assessment coverage, `not_assessed_orientation_unreliable` coverage, and losses at every stage.
- Break end-to-end coverage and errors down by Hive Configuration, bee-density, lighting, and image quality, while marking sparse groups as non-interpretable.
- Report end-to-end coverage and losses separately for complete and partial visible bees, while retaining complete visible bees as the initial user-facing Varroa-estimate denominator.
- Require a user-facing coverage warning whenever any complete visible bee was not assessed for Varroa; never present the headline rate alone in that case.
- Once an evidence-based coverage threshold is established, suppress rather than merely warn on a user-facing headline estimate below that threshold.
- Give an inadequate-coverage result a full inspection review/correction route through an Inspection Recovery Review: a distinct, named, saveable, and resumable session linked to a fixed snapshot of the original model-only result and photo evidence; do not rerun or substitute newer models during recovery. The route remains available for retained inspection history after data-use withdrawal, but its evidence is ineligible for model improvement without an active agreement and independent curation. Every recovery annotation and Varroa decision retains its provenance and is reported as AI-assisted-reviewed, never human-from-scratch. Model promotion never automatically reanalyses historic Inspection Photos; PARK-0034 records the future explicit reanalysis workflow. In the first release recovery is available only for suppressed model-only results, not every completed inspection, and only the Workspace owner may create, resume, or complete it; PARK-0033 records the broader workflow. The owner can complete it at any coverage level after explicit confirmation. A completed review and result are immutable; a later correction starts a new linked review and result revision. The latest completed human-reviewed result becomes the inspection's current result by default, while the original model-only result and earlier human-reviewed revisions remain available as labelled comparison history. It can resolve previously unassessed complete visible bees and correct any model-produced bee, orientation, or Varroa decision. Preserve the immutable original model-only result and calculate/show a separately provenanced human-reviewed inspection result alongside it. Show a Result Evidence Breakdown for both results: positive, active negative, `not_determined`, and unassessed complete visible-bee counts, plus Review Completion and Determinate Varroa Coverage. `not_determined` counts only toward Review Completion and cannot support a headline rate; retain suppression when an evidence-based determinate-coverage threshold is still not met. Keep the feedback product-only until a Dataset Curator independently reviews it and assigns a Dataset Role.
- Recovery evidence created while the Workspace Data Use Agreement is withdrawn remains product-only after later agreement acceptance. Model use requires a separate explicit Workspace owner dataset-contribution decision, followed by independent Dataset Curator review and Dataset Role assignment.
- The Dataset Contribution Decision applies to exactly one named completed Human-Reviewed Inspection Result revision; it is not a workspace-wide opt-in or Dataset Role assignment.
- Adopted strict Contribution Withdrawal: immediately exclude affected Dataset Items from future exports, Dataset Versions, Training Runs, Benchmark Evaluations, and promotion; preserve historical audit lineage; quarantine affected Dataset Versions and model artifacts; and retrain a replacement without the contribution before future model use resumes. Raw source erasure follows the deletion process.
- Distinguish a Contributor Contribution Permission from the Workspace Data Use Agreement: external contributors control permission for their identified image, annotation, or review work without gaining Workspace ownership or dataset-curation authority. A Dataset Item needs both the workspace agreement and every applicable contributor permission for future model use.
- Make the contributor consent boundary a named, immutable Contribution Bundle rather than a separate acceptance per frame; retain the bundle reference on every included Dataset Item so withdrawal remains exact.
- Make whole-bundle withdrawal the first supported contributor control. Finer withdrawal boundaries require separate Contribution Bundles before acceptance.
- Require external contributors to use their own registered HiveSight identity to view bundles and withdraw permission, without granting them Workspace Membership or dataset/model-governance capability.
- Restrict contributor access to explicitly assigned annotation tasks and Contribution Bundles; do not expose the wider workspace, unassigned inspections, or other contributors' evidence.
- Make Dataset Curators responsible for creating Contribution Bundles and assigning annotation tasks. A Workspace owner can offer their own evidence but does not gain dataset-governance authority through ownership.
- Require explicit acceptance of a named Contribution Bundle and its terms version before showing assigned images or annotation tasks; before that, show only a non-sensitive bundle summary.
- Treat a material contributor-terms change as a forward-use gate: fresh acceptance is required before the bundle can enter a new Dataset Version, Training Run, Benchmark Evaluation, or promotion, while historical lineage remains auditable.
- Let a contributor request deletion of their own Contribution Bundle. Starting that request automatically withdraws permission and stops future model use; deletion then follows its own tracked erasure and retention workflow.
- Give contributors a read-only Contribution Usage Record for each bundle: accepted terms, permission/deletion status, and linked Dataset Versions, Training Runs, and model-artifact outcomes, without exposing other contributors' evidence or the wider workspace.
- Permit pseudonymous contributor identities. Keep only the minimum contact/authentication data needed for control, and use an internal contributor id plus selected pseudonym in provenance and curator-facing views rather than a required real name.
- Revoke access to every unfinished task immediately when a contributor withdraws permission or starts deletion; retain only the minimal audit record needed to explain the request and affected lineage.
- Treat re-acceptance after withdrawal as a new forward-looking permission record; do not automatically unquarantine prior Dataset Versions or model artifacts.
- Park the exact contents and retention period of the minimal audit record after contributor deletion, legal-retention exceptions, and material-terms-change classification in PARK-0011 for formal privacy/policy review; the immediate withdrawal and access-revocation safety behaviour remains decided.
- Distinguish public/open source rights from contributor permission: record a Source Rights Record with licence provenance and restrictions, and keep imported annotation provenance separate from the right to use the underlying image.
- Require a Dataset Curator to explicitly approve a public/open Source Rights Record before related images can become Dataset Items.
- Carry required public/open-source attribution into relevant Dataset Versions, exports, evaluation reports, and released model documentation.
- Require every Source Rights Record and Contributor Contribution Permission to declare a closed set of Permitted Use Scopes, such as development, evaluation, user-facing deployment, sharing/publication, and commercial use; unlisted use is not permitted.
- Set the initial contributor offer to model development and evaluation only; user-facing deployment, sharing/publication, and commercial use require separate explicit opt-in.
- Hard-block user-facing model promotion unless every Dataset Item used for training permits `user_facing_deployment`, retaining a scope-compatibility report in the promotion record.
- Apply the same hard-block and scope-compatibility report to sharing/publication and commercial model release, using the relevant permitted-use scope.
- Park detailed public-source licence compatibility, including non-commercial, share-alike, redistribution, attribution, and model-output obligations, in PARK-0035. Public/open evidence remains local research and model development only unless its reviewed rights record explicitly permits broader use.
- Adopt Source Rights Invalidation as a distinct cause with the same protective operation as Contribution Withdrawal: exclude affected future use, quarantine dependent dataset/model artifacts, retain audit lineage, and retrain a clean replacement; ADR 0009 records the decision.
- Update Slice 0015.4 benchmark evaluation readiness to block withdrawn, rights-invalidated, scope-incompatible, or quarantined evidence, because benchmark evaluation itself is a governed `evaluation` use.
- Scope Slice 0015.4 to the first Bee Localisation Benchmark Evaluation proof point: use the protected benchmark Dataset Items already frozen in the candidate's Training Run Dataset Version, fixed recorded evaluation settings, fake adapter in fast tests, opt-in real YOLO QA, high-severity leakage acknowledgement, and `ellipse_match_v1` as a replaceable first matcher. Park a separate benchmark Dataset Version lifecycle and precise rotated geometry scoring.
- Grill Slice 0015.4 into an implementation-ready shape: multiple first-class Benchmark Evaluations per Model Candidate, latest completed summary plus full run history, cooperative cancellation without deletion, no Candidate Annotation writes from evaluation, raw predictions preserved only as derived JSON artifacts, fixed provisional `SMALL_BENCHMARK_SET` cutoff below 20 items, Training Crop benchmark only, Dataset Curator-only UI, API-level BDD scenarios, live Postgres closeout, local one-model-job-at-a-time lock, `pnpm dev:all:yolo` / `pnpm dev:lan:yolo` aliases, and `pnpm model:qa:bee:evaluate` as the explicit real-adapter QA command.

AI contribution:

- Distinguished the stable three-capability product architecture from the still-reversible choice of whether those capabilities are delivered by two, three, or combined model artifacts.
- Identified that each Model Purpose requires independent provenance, metrics, benchmark evidence, and promotion evidence.
- Updated Slice 0015.4 to evaluate Bee Localisation only, preventing an early YOLO benchmark report from implying coverage of orientation or Varroa detection.

Human judgment still required:

- Define the benchmark or operational failure that would justify replacing the first binary head/tail classifier.

### 2026-08-03 Roadmap Capture

Human-confirmed direction:

- Add a lightweight roadmap document under `requirements` so potential future slices are visible outside individual slice docs and the parking lot.
- Group future work by business, technical, governance, and quality concerns rather than treating slice numbers as a fixed plan.

AI contribution:

- Consolidated parked and emerging work into `requirements/roadmap.md`, including Bee Localisation, Bee Orientation, Varroa Detection, statistical inference, product workflow, data governance, platform, and testing candidates.

Human judgment still required:

- Choose the next active slice from the roadmap before implementation.

### 2026-08-03 Dev User And Auth Boundary Direction

Human-confirmed direction:

- Tackle role-sensitive local workflows before real registration and external login.
- Avoid rolling HiveSight-owned passwords or account recovery.
- Treat Google or Apple login as future delegated authentication options, while HiveSight keeps ownership of Workspace Membership, internal capabilities, Contributor Access Scope, and authorization decisions.

AI contribution:

- Proposed `Slice 0018: Dev User And Role Switching` as a bridge from the existing `x-hivesight-dev-user-id` seam toward real authentication.
- Parked real external login behind a follow-on Auth Boundary Decision and First External Login Provider slice.
- Refined Slice 0018 after grilling: switch seeded development Users rather than roles; give each seeded User its own Workspace; keep cross-user task access out of scope; use User switching as a logout/login proxy that clears user-scoped UI state; hide impossible product capabilities while showing diagnostic capability status in the Development session panel.

Human judgment still required:

- Decide whether Google is the first real provider and whether Apple is needed for the first external-user release.

### 2026-08-05 Varroa Evidence Methodology

Human-confirmed direction:

- Keep model-corpus construction, full-depth model validation, and production inspection-rate sampling as distinct activities even when they reuse the same Varroa Review Outcome interface.
- Construct a small Gold-Standard Full-Frame Corpus to measure both compounded pipeline error and sampling error before choosing a user-facing sample size or sequential stopping rule.
- Treat paired alcohol-wash or other field measurements as calibration research against a related but different target, not as photo-annotation ground truth or permission to claim colony-level prevalence.

AI contribution:

- Turned the distinction into `requirements/varroa-evidence-methodology.md`, including full-depth annotation/review protocol, representative and positive-enriched curation streams, protected development/locked evaluation sets, repeatable sampling simulations, and reproducibility records.
- Refined product, model, domain, roadmap, decision-log, and parking-lot wording so an eventual rate is frame-scoped, caveated, and never inferred from positive-enriched training balance.

Human judgment still required:

- Approve the pilot's frame strata, review-strength progression, operational thresholds to simulate, field-reference protocol, and the evidence bar for showing a sampled result to a beekeeper.

### 2026-08-05 Slice 0023 Real Bee Training Baseline Planning

Human-confirmed direction:

- Move next to real Bee Orientation training before Varroa Detection work, because Varroa Detection depends on reliable Head-Up Normalized Bee Crop evidence.
- Treat Bee Training as the operator workflow: Bee Localisation and Bee Orientation are trained in tandem from one shared Marked-Bee Dataset Version.
- Remove YOLO-named user commands now. Keep internal adapter ids such as `ultralytics_yolo_obb` only where technically accurate.
- Add a real PyTorch/torchvision Bee Orientation adapter that creates a non-user-facing Model Candidate with training-run validation metrics only.
- Keep Bee Orientation benchmark evaluation, orientation inference, Head-Up Normalized Bee Crop generation, and Varroa work out of Slice 0023.
- Require a small but non-trivial real-orientation data gate: at least four eligible reliable complete bees in Training and four in Validation.
- Make the Bee Training local lane explain Docker/Postgres availability problems without resetting or seeding the database.

AI contribution:

- Converted the agreed decisions into `architecture/vertical-slice-0023-real-bee-training-baseline.md` with signed-off Gherkin scenarios.
- Proposed the thin implementation boundary: one UI action or command starts Bee Localisation first, then Bee Orientation, with two separate Training Runs tied to one source Dataset Version and no new parent run entity.

Human judgment still required:

- Confirm implementation priority after Slice 0023 design is committed or proceed directly to building the slice.

### 2026-08-05 Slice 0023 Real Bee Training Baseline Implementation

Human-confirmed direction:

- Proceed with the signed-off Slice 0023 scenarios.
- Keep Bee Training as the operator workflow and remove YOLO-named user commands instead of keeping aliases.

AI contribution:

- Implemented combined Bee Training readiness and start behaviour so Bee Localisation runs first and Bee Orientation follows from the same Marked-Bee Dataset Version.
- Added a real PyTorch/torchvision Bee Orientation adapter that records non-user-facing candidate artifacts, package hash, architecture, device, validation accuracy, and a Head Up / Head Down confusion matrix.
- Updated the Web UI, command surface, docs, roadmap, parking lot, and regression tests to use Bee Training / Bee Localisation product language while retaining internal adapter ids where technically accurate.

Human judgment still required:

- Review the first real orientation training reports once real weekend photos are available.
- Decide later whether benchmark evidence supports the binary orientation classifier or whether a keypoint/pose or multi-head model is needed.

### 2026-08-05 Slice 0024 Bee Orientation Benchmark Evaluation Planning

Human-confirmed direction:

- Make Slice 0024 the Bee Orientation Benchmark Evaluation slice after real Bee Orientation training.
- Evaluate only reliable complete visible bees from protected Benchmark items inside the candidate's own shared Marked-Bee Dataset Version.
- Report excluded unreliable-orientation and partial visible bees, but do not score them in the first orientation benchmark.
- Produce Head Up / Head Down accuracy and confusion matrix evidence only; defer angular error, promotion thresholds, and classifier-sufficiency decisions.
- Allow fake candidates for fast workflow evidence while labelling fake-adapter benchmark output as not real model quality.
- Add a separate Bee Orientation benchmark section inside Model Governance, with modest structure around Model Benchmarking.
- Keep the one-active-model-job guard and avoid adding a reusable Benchmark Dataset Version lifecycle in this slice.

AI contribution:

- Converted the grilling decisions and accepted scenarios into `architecture/vertical-slice-0024-bee-orientation-benchmark-evaluation.md`.
- Updated the roadmap and PARK-0028 so benchmark evaluation is the next planned orientation step while automated inference and Head-Up Normalized Bee Crop generation remain parked.

Human judgment still required:

- Review real Bee Orientation benchmark reports once real protected benchmark evidence exists.
- Later decide whether the binary classifier is sufficient for Varroa work or whether a keypoint/pose or multi-head model is justified.

### 2026-08-05 Slice 0024 Bee Orientation Benchmark Evaluation Implementation

Human-confirmed direction:

- Proceed with the signed-off Slice 0024 scenarios.
- Keep Bee Orientation benchmark evidence purpose-limited: Head Up / Head Down only, no Bee Localisation claim, no Varroa claim, and no user-facing promotion.

AI contribution:

- Added Bee Orientation benchmark readiness and start paths for completed Bee Orientation Model Candidates from the same shared Marked-Bee Dataset Version.
- Recorded eligible reliable complete benchmark bees, excluded unreliable-orientation bees, excluded partial visible bees, accuracy, Head Up / Head Down confusion matrix, raw prediction artifacts, and report artifacts.
- Added the Web UI section, browser acceptance coverage, and `pnpm model:qa:bee:orientation-evaluate` as an append-only real-adapter QA command.

Human judgment still required:

- Review real Bee Orientation benchmark reports once real protected benchmark evidence exists.
- Decide later whether benchmark evidence supports the binary classifier or whether a keypoint/pose or multi-head model is needed before Varroa crop normalization.

### 2026-08-05 Slice 0025 Varroa Review Outcome Labelling Planning

Human-confirmed direction:

- Move from Bee Orientation evidence into the first Varroa curation workflow before training a Varroa Detector.
- Acceptance signoff given for Slice 0025 scenarios.
- Preserve the active-label rule: `no_visible_varroa` is an explicit human judgement, not the absence of marker clicks.
- Name the workflow stage `Varroa Review` and place it after Crop Governance and before Model Governance.
- Scope the slice to Dataset Curators, Training Data Collection inspections, completed Training Crops, and reliable complete visible bees.
- Treat Varroa review suitability and suspected-visible-Varroa as fast annotation-time triage cues, not final Varroa evidence.
- Use on-demand Head-Up Normalized Bee Crop previews as the primary review surface, with source crop context and point markers in normalized coordinates.
- Keep review evidence conservative: `model_curation`, `human_selected`, `single_curator_review`, and `human_from_scratch`.

AI contribution:

- Proposed Slice 0025 as a combined thin slice: generate a Head-Up Normalized Bee Crop preview from reliable complete human-reviewed bee ellipses, then let a Dataset Curator record `visible_varroa_present`, `no_visible_varroa`, or `not_determined` with point-marker evidence for positives.
- Kept automated orientation inference, Varroa Detector training, sampling-plan queues, blind independent review, repository-level queues, Dataset Item promotion, HiveSight Advisor, treatment recommendation, and user-facing Varroa Assessment out of the slice.
- Drafted and revised `architecture/vertical-slice-0025-varroa-review-outcome-labelling.md`, updated the roadmap, and aligned the context/domain-model documents with the new Varroa Review concepts.

Human judgment still required:

- Decide after real use whether triage cues need richer notes/history or whether the lightweight current-value model is enough.
- Decide in a later slice how Varroa Review Outcomes graduate into Dataset Items, benchmark evidence, sampling-plan evidence, or treatment-advisor inputs.

### 2026-08-05 Slice 0025 Varroa Review Outcome Labelling Implementation

Human-confirmed direction:

- Build the signed-off Slice 0025 workflow without adding Varroa Detector training, treatment advice, repository queues, or dataset promotion.

AI contribution:

- Added durable Varroa review cues to Training Crop bee ellipses.
- Added Core API Varroa Review candidate, Head-Up Normalized Bee Crop preview/image, and current outcome endpoints.
- Added current Varroa Review Outcome persistence with point markers, provenance labels, server-side validation, Postgres migration/projection support, focused API tests, executable BDD scenarios, and browser acceptance.
- Added the Web `Varroa Review` workflow stage and user-guide instructions.

Human judgment still required:

- Review the first real curated Varroa outcomes on weekend photo data.

### 2026-08-05 Varroa Corpus Governance Planning, Renumbered To Slice 0030

Human-confirmed direction:

- Preserve corpus governance before Varroa Detector training datasets are frozen.
- Keep Varroa evidence in model-curation space until explicit include, exclude, or defer decisions exist.
- Preserve the boundary between active negative evidence and unresolved `not_determined` evidence.

AI contribution:

- Designed `architecture/vertical-slice-0030-varroa-corpus-governance.md`, renumbered from the original Slice 0026 design after the Varroa-to-Advisor tranche was replanned.
- Added Varroa Corpus Governance and Varroa Corpus Curation Decision to the project language and domain model.
- Promoted the stale-source Varroa review risk from the parking lot into the corpus governance design so source geometry changes block corpus inclusion until rechecked.
- Updated the roadmap to preserve Varroa Corpus Governance as Slice 0030 after frame-level counting and Advisor-context groundwork.

Human judgment still required:

- Review and sign off the Slice 0030 Gherkin before implementation starts.
- Decide in the later corpus-to-dataset slice whether included corpus decisions freeze directly into a Varroa Dataset Version or first become a named draft corpus.

### 2026-08-05 Slice 0026 Frame-Level Varroa Result Summary Planning

Human-confirmed direction:

- The next target is getting HiveSight to the point where it can count mites on a photographed frame, using either a stubbed or real adapter.
- The near-term integration goal is to reach the point where HiveSight can expose treatment-relevant Varroa context to HiveSight Advisor.
- Corpus governance remains important, but it should not block the first frame-counting path.

AI contribution:

- Replanned the Varroa-to-Advisor tranche as Slice 0026 Frame-Level Varroa Result Summary, Slice 0027 Varroa Detector Adapter Seam, Slice 0028 Frame Mite Counting Workflow, and Slice 0029 Advisor Varroa Context API.
- Preserved Varroa Corpus Governance as Slice 0030.
- Designed `architecture/vertical-slice-0026-frame-level-varroa-result-summary.md`.
- Updated `requirements/roadmap.md`, `CONTEXT.md`, and `architecture/domain-model.md` to align the new slice numbering and domain language.

Human judgment still required:

- Review and sign off the Slice 0026 Gherkin before implementation starts.
- Decide whether Slice 0026 summaries are scoped to one Inspection Photo only or also need an Inspection-level roll-up.
- Decide whether Advisor context availability requires complete determinate coverage or can be partial with caveats.

### 2026-08-06 Dual-Seam Acceptance Specification Pilot Planning

Human-confirmed direction:

- Promote Dual-Seam Acceptance Specification Pilot as Slice 0030.
- Keep one client-neutral, capability-organised Gherkin feature as the living acceptance specification; bind it separately to the Core API and Web UI where both seams are meaningful.
- Use `playwright-bdd` for the browser binding while retaining native Playwright execution and reporting.
- Pilot the approach with the accepted Varroa Review scenario that records visible Varroa with two mite markers.
- Preserve Slice 0025 as historical acceptance evidence, keep browser-specific visual regression coverage, and return the previously designed Varroa Corpus Governance work to an unnumbered candidate.

AI contribution:

- Identified that existing API Gherkin and browser acceptance tests are executable but still organised primarily by transient slice history.
- Identified a current API/browser drift in the selected Varroa outcome example: the API Gherkin described two markers while the browser test asserted one.
- Designed `architecture/vertical-slice-0030-dual-seam-acceptance-specification-pilot.md` with formally accepted Gherkin, scoped migration, runner choice, verification boundaries, and follow-on limits.
- Renamed the unbuilt Slice 0030 Varroa Corpus Governance design to `architecture/candidate-varroa-corpus-governance.md` and aligned roadmap, architecture, and testing-policy references.

Human judgment still required:

- Review the Slice 0030 implementation once the API and browser bindings execute the shared feature.
- Decide which capability should migrate next only after the pilot demonstrates its maintenance and reporting cost.
