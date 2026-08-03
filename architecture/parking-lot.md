# Parking Lot

This document captures important work that is not in the current slice or remediation pass, but should not be forgotten.

Use this when something is out of scope now but expected later. Prefer ADRs or the decision log for settled decisions, and remediation trackers for known active problems.

## Status Values

- `parked`: deliberately deferred.
- `promoted`: moved into an active slice, remediation, ADR, or implementation plan.
- `closed`: no longer needed.
- `superseded`: replaced by another parked item or decision.

## PARK-0001: UI-Level Gherkin Harness

Status: promoted
Date parked: 2026-07-30
Source: Slice 0003.5, Slice 0009.5, skills remediation
Area: testing

Context:

API acceptance currently uses Gherkin and pytest-bdd. UI acceptance currently uses Playwright specs directly.

Why parked:

Slice 0013 grilling decided that UI acceptance should remain Playwright specs plus generated verification reports for now. UI-level Gherkin remains a future option, not a near-term promise.

Revisit trigger:

When Playwright specs and generated verification reports stop being readable enough as executable behaviour documentation, or before a major cross-role UI workflow where Gherkin would materially improve acceptance review.

Suggested owner or area:

Delivery test automation and acceptance BDD.

## PARK-0002: Security Threat-Modelling Skill

Status: promoted
Date parked: 2026-07-30
Source: HiveSight review, skills remediation grilling
Area: security

Context:

The unused upload-url endpoint showed that explicit security review has practical value for HiveSight.

Why parked:

The immediate unsafe route was removed. Creating the security skill now would widen the skills remediation beyond the agreed immediate set.

Revisit trigger:

Before production auth, object storage, signed upload URLs, shared/multi-user access, role security, external APIs, or non-local deployment work.

Suggested owner or area:

Security and architecture.

## PARK-0003: API Contract Governance Skill

Status: promoted
Date parked: 2026-07-30
Source: skills remediation grilling
Area: contracts

Context:

HiveSight has REST contracts, event schemas, and typed web clients, but no skill for versioning or compatibility governance.

Why parked:

Review Remediation 0001 should preserve public contracts. Contract governance becomes more urgent when contracts start changing across service boundaries.

Revisit trigger:

Before implementing Analysis Service integration, public API versioning, event schema evolution, generated-client work, or Core API to Analysis Service job/result contracts.

Suggested owner or area:

API and contract governance.

## PARK-0004: Release And Operations Readiness Skill

Status: promoted
Date parked: 2026-07-30
Source: skills remediation grilling
Area: operations

Context:

The skills library has observability guidance but no release, rollback, runbook, or incident-response skill.

Why parked:

HiveSight does not yet have a real deployment target. Adding this skill before deployment decisions would mostly create abstract process.

Revisit trigger:

When HiveSight chooses a deployment target or prepares an externally accessible environment; before external users, production auth, signed upload URLs, durable object storage commitments, or exposing anything outside local/LAN development.

Suggested owner or area:

Operations and release readiness.

## PARK-0005: Varroa Traceability Correction

Status: closed
Date parked: 2026-07-30
Source: HiveSight review
Area: requirements and domain model

Context:

Varroa detection remains the product goal, but delivered slices have intentionally focused on bee annotation and dataset foundations. Some traceability wording may imply Varroa Annotation is more operationalized than it is.

Why parked:

Slice 0013 corrected the traceability status: Varroa detection remains the product/model goal, but implemented slices currently cover bee annotation, dataset foundations, and bee-detector training preparation rather than real Varroa detection.

Revisit trigger:

Closed by Slice 0013. Future Varroa-specific functional slices should still be planned from current requirements and model requirements before implementation.

Suggested owner or area:

Requirements, domain model, and model governance.

## PARK-0006: YOLO OBB Training Baseline

Status: parked
Date parked: 2026-07-30
Source: Slice renumbering after external review remediation
Area: model training

Context:

`architecture/vertical-slice-0015-yolo-obb-training-baseline.md` defines the first repeatable HiveSight Bee Detector training baseline using reviewed crop-level oriented bee ellipses exported to YOLO OBB labels.

Why parked:

The review recommendations architecture decision pass must run first, and Slice 0014 must introduce Postgres-backed Bee Annotation Repository metadata persistence before training-run and model-candidate evidence becomes meaningful.

Revisit trigger:

Slice 0013 closeout decision: `go after Slice 0014`. Revisit after Slice 0014 Postgres-backed Bee Annotation Repository persistence is complete.

Promotion note:

Promoted into active planning as `architecture/vertical-slice-0015-yolo-obb-training-baseline.md` after Slice 0014 live Postgres closeout passed. Slice 0015 planning now also retires Grounding DINO from the active solution and adds a project-owned Bee Detector training baseline.

Suggested owner or area:

Model governance and architecture.

## PARK-0007: Dev User Switcher

Status: promoted
Date parked: 2026-07-30
Source: Slice 0013 grilling
Area: developer experience, UI acceptance, authorization simulation

Context:

HiveSight currently uses dev authentication through `x-hivesight-dev-user-id`. Before real authentication is selected, the UI should make it easy to exercise behaviours as different seeded development Users, each with stable identity, its own Workspace, Workspace Membership, and Internal Capabilities.

Why parked:

This is useful and likely important for acceptance testing, but it should not be bundled into Postgres persistence. It touches UI ergonomics, seeded dev users, capability simulation, and test setup rather than durable schema design.

Revisit trigger:

Slice 0013 closeout decision: keep this after Slice 0014 unless role-specific UI acceptance becomes the immediate next workflow. Revisit before the next role-specific UI acceptance flow.

Promotion note:

Promoted into `architecture/vertical-slice-0018-dev-user-and-role-switching.md` after role-specific dataset-governance, reviewer, contributor, and future authentication discussions made the single hard-coded dev User too limiting for planning, acceptance testing, and manual QA.

Suggested owner or area:

Web UI, Core API dev session, and test automation.

## PARK-0008: Dataset Item Audit Events

Status: parked
Date parked: 2026-07-31
Source: Slice 0013.5 domain model persistence stability grilling
Area: model governance, persistence

Context:

Slice 0013.5 decided that Dataset Items are immutable after assignment and include actor, timestamp, permission snapshot, provenance snapshot, status, and supersession fields. A dedicated `dataset_item_events` or audit-event table is useful later, but not needed for the first durable repository slice.

Why parked:

Adding an event table now would widen Slice 0014 beyond the narrow persistence path needed before the first model baseline.

Revisit trigger:

Before implementing Dataset Item supersession workflow, Dataset Versions, Training Runs, benchmark governance, consent withdrawal enforcement, or any external audit/reporting requirement.

Suggested owner or area:

Model governance and persistence.

## PARK-0009: Dataset Versions

Status: parked
Date parked: 2026-07-31
Source: Slice 0013.5 domain model persistence stability grilling
Area: model training, model governance

Context:

Slice 0014 persists Dataset Items, but not Dataset Versions. Dataset Versions become load-bearing when a Training Run or Benchmark Evaluation consumes a frozen set of Dataset Items.

Why parked:

Persisting Dataset Versions belongs with the YOLO OBB Training Baseline or a nearby model-training slice, not the first repository persistence slice.

Promotion note:

Promoted into Slice 0015 planning. Dataset Versions are now planned as durable first-class records that freeze active reviewed Dataset Items, protected benchmark metadata, exclusions, selection criteria, and report/preview artifacts before a Training Run consumes them.

Revisit trigger:

Before Slice 0015 training implementation creates Training Runs or Benchmark Evaluations.

Suggested owner or area:

Model training and model governance.

## PARK-0010: Hive Component Or Box Configuration

Status: parked
Date parked: 2026-07-31
Source: Slice 0013.5 domain model persistence stability grilling
Area: domain model, hive equipment

Context:

Slice 0013.5 kept one active Hive Configuration per Hive for now, with `box_use` on Hive Configuration. A real hive may have brood boxes and supers at the same time, and future statistics may need more precise component-level equipment modelling.

Why parked:

Detailed Hive Component or Box modelling would widen the persistence slice into full hive equipment inventory, which the project has deliberately deferred.

Revisit trigger:

Before supporting inspections that mix brood and super material in the same hive workflow, frame-level calibration, detailed equipment statistics, or multi-box hive modelling.

Suggested owner or area:

Domain model and product requirements.

## PARK-0011: Consent Withdrawal And Deletion Enforcement

Status: parked
Date parked: 2026-07-31
Source: Slice 0013.5 domain model persistence stability grilling
Area: privacy, model governance

Context:

The accepted Contribution Withdrawal policy immediately excludes affected Dataset Items from future exports, Dataset Versions, Training Runs, Benchmark Evaluations, and promotion; preserves historical audit lineage; quarantines affected Dataset Versions and model artifacts; and requires a replacement trained without the contribution before future use resumes.

Why parked:

The policy is now decided, but durable propagation, artifact quarantine, replacement training, deletion/erasure handling, and operational reporting still need implementation. Formal privacy/policy review must define the exact contents and retention period of the minimal audit record preserved after contributor deletion, including any legal-retention exception, and how a contributor-terms change is classified as material.

Revisit trigger:

Before user-submitted data is used for model improvement beyond local/project-owned development, before hosted training/sharing/publication, or before implementing deletion/purge workflows.

Suggested owner or area:

Privacy, product policy, and model governance.

## PARK-0012: Stricter Dataset Split Leakage Policy

Status: parked
Date parked: 2026-07-31
Source: Slice 0013.5 domain model persistence stability grilling
Area: model evaluation, dataset governance

Context:

Slice 0014 will hard-block benchmark conflicts for the same Source Image or same `source_group_key`. Same Hive, same Inspection, and training-versus-validation leakage are documented risks but not hard-blocked in the first durable schema.

Why parked:

The first seed dataset is small, and overly strict split rules could make early learning awkward. The benchmark protection hook is enough for the first local repository persistence slice.

Revisit trigger:

Before serious benchmark claims, protected benchmark reporting, model promotion, or publication of model-quality metrics.

Suggested owner or area:

Model evaluation and dataset governance.

## PARK-0013: Varroa Training Source Independence

Status: parked
Date parked: 2026-07-31
Source: Slice 0015 planning feedback
Area: model training, model evaluation, dataset governance

Context:

Bee Localisation, Bee Orientation, and Varroa Detection are separate logical model purposes. The accepted policy requires Varroa training and benchmark datasets to include human-selected bee crops independent of upstream model output. Otherwise the Varroa Detector may never learn from missed populations such as shadowed, occluded, dense, or unusual-angle bees.

Each Varroa Dataset Item will record Dataset Selection Method as `human_selected` or `upstream_model_selected`. `human_selected` requires blind selection before upstream model suggestions are seen; any model-influenced selection is `upstream_model_selected`. Benchmark reports will show the mix. No numeric quota has yet been set.

Model curation defaults to `stratified_random` sampling across available Hive, frame, bee-density, lighting, and image-quality strata, with deliberately difficult examples added as `curator_targeted`. Reports will retain both method and stratum distributions.

Why parked:

Slice 0015 trains only the HiveSight Bee Detector. Varroa mite annotation, independent human crop selection, mite detector training, and bee-to-mite association are out of scope for the first YOLO OBB Bee Localisation baseline.

Revisit trigger:

Before the first Varroa detector training slice, before creating a mite benchmark Dataset Version, or before implementing the human-selected crop collection workflow required by the accepted policy.

Suggested owner or area:

Model governance, dataset curation, and architecture ADR review.

## PARK-0014: Public Dataset Candidate Annotation Import

Status: parked
Date parked: 2026-07-31
Source: Slice 0015 grilling
Area: model training, dataset bootstrap, provenance

Context:

The user has a public USDA-ARS Tucson annotated hive-frame dataset available locally, with PNG images and XML annotations. These annotations may help bootstrap HiveSight's Bee Detector, but they must be treated as Candidate Annotations requiring HiveSight human review before becoming trusted training evidence.

Why parked:

Slice 0015 already includes Dataset Versions, YOLO OBB export, Training Runs, Model Candidates, reporting, local database purpose separation, and Grounding DINO retirement. Public XML import has separate parsing, provenance, licensing, source-group, and review-quality questions.

Revisit trigger:

After `Slice 0015.1: Training Run Progress And Recovery` closes, reconsider as a later public dataset import slice before relying only on hand-created HiveSight crops for early Bee Detector growth.

Suggested owner or area:

Dataset curation and model governance.

## PARK-0015: Full-Frame And Tiled YOLO Export

Status: parked
Date parked: 2026-07-31
Source: Slice 0015 grilling
Area: model data pipeline

Context:

Slice 0015 trains from reviewed Training Crops only. Scaling toward dense full-frame brood photos may require full-frame annotations, tiling, different preview/quality checks, and stronger leakage controls.

Why parked:

The first Bee Detector baseline should prove the reproducible governed training pipeline on small crops before widening to full-frame export complexity.

Revisit trigger:

Before training from full-frame regions or full frame sides, before using large dense brood-frame photos as trainer-facing input, or before evaluating whether crop-trained models transfer to real inspection photos.

Suggested owner or area:

Model training, dataset export, and annotation UI.

## PARK-0016: Modern Candidate Annotation Review Workflow

Status: parked
Date parked: 2026-07-31
Source: Slice 0016 grilling
Area: dataset curation, annotation review, model governance

Context:

Slice 0016 hides the older Dataset Labelling Session UI from the normal Training Data Collection path because the current YOLO OBB training-data workflow uses Training Crops, Oriented Bee Ellipses, Dataset Role assignment, Dataset Versions, and Bee Detector Training Runs.

The older Dataset Labelling backend and tests remain for historical/API continuity, but the product language has moved toward Candidate Annotation rather than Draft Annotation or pre-labelling.

Why parked:

Redesigning Dataset Labelling into a modern Candidate Annotation Review workflow would widen Slice 0016 beyond Workspace resume and Apiary/Hive selection.

Revisit trigger:

Before reintroducing model-proposed annotations into the normal UI, before using a trained HiveSight Bee Detector to propose Candidate Annotations, or before importing public dataset annotations for human review.

Suggested owner or area:

Dataset curation, annotation UI, and model governance.

## PARK-0017: Inspection List And Resume For Selected Hive

Status: parked
Date parked: 2026-07-31
Source: Slice 0016 grilling
Area: inspection workflow, UI usability

Context:

Slice 0016 resumes Workspace, Apiary, Hive, and Hive Configuration context, but it does not list or resume existing Inspections for the selected Hive.

Why parked:

Inspection resume introduces another selection layer across inspection date, intent, photo list, and incomplete annotation/model-training work. The immediate usability goal is to stop recreating Apiary and Hive records.

Promotion note:

Promoted into `architecture/vertical-slice-0017-resume-training-inspections-and-crops.md` after crop annotation usability feedback made multi-session annotation safety urgent.

Revisit trigger:

Slice 0017 now addresses the Training Data Collection resume path. Any remaining broader Inspection history work should be revisited when Varroa Assessment history, edit/archive flows, or full multi-page navigation become necessary.

Suggested owner or area:

Web UI, Core API inspection read side, and browser acceptance.

## PARK-0018: Hive Setup Edit And Rename Workflow

Status: parked
Date parked: 2026-07-31
Source: Slice 0016 grilling
Area: hive equipment, UI usability, provenance

Context:

Slice 0016 keeps Hive creation and initial Hive Configuration combined, and displays existing Hive Configuration without making edit a first-class flow. It also does not support Apiary/Hive rename.

Why parked:

Changing Hive Configuration is domain-significant because Dataset Items snapshot Hive Configuration for provenance. Rename/edit flows introduce update endpoints, validation, audit questions, and UI states that are not needed to unblock first training-data collection.

Revisit trigger:

When persisted setup mistakes become annoying, before broader hive-equipment management, or before users outside the developer workflow need to maintain Apiary/Hive records.

Suggested owner or area:

Product workflow, hive equipment domain model, and UI usability.

## PARK-0019: Unsaved Annotation Edit Warning

Status: parked
Date parked: 2026-07-31
Source: Slice 0016 grilling
Area: annotation UI, user experience

Context:

Slice 0016 clears downstream state aggressively when Apiary or Hive selection changes. Current annotation actions are mostly saved immediately through API calls, but richer local draft editing may later create unsaved work that should warn before context changes.

Why parked:

Defining dirty-state semantics for crop drafts, ellipse edits, pending file input, and future richer editors would widen Slice 0016 beyond context selection.

Revisit trigger:

Before introducing richer local-only annotation drafts, bulk editing, keyboard-heavy editing, or multi-step unsaved annotation workflows.

Suggested owner or area:

Annotation UI and interaction design.

## PARK-0020: Resume Most Recently Active Annotation Work

Status: parked
Date parked: 2026-07-31
Source: Slice 0017 grilling
Area: annotation UI, inspection resume

Context:

Slice 0017 selects the newest Training Data Collection Inspection by `inspection_date`, then id. A more helpful future behaviour may resume the most recently active annotation work by looking across uploads, Training Crops, Oriented Bee Ellipses, Dataset Item assignments, and possibly future draft/edit records.

Why parked:

Activity-derived resume needs a consistent updated-at/read-model story across several entities. Slice 0017 is focused on making saved work reachable before real annotation sessions begin.

Revisit trigger:

When a Hive has enough concurrent or long-running Training Data Collection Inspections that newest-by-date no longer puts the Dataset Curator near the work they expect.

Suggested owner or area:

Web UI, Core API read model, and annotation workflow.

## PARK-0021: Visible Last-Saved Annotation Status

Status: parked
Date parked: 2026-07-31
Source: Slice 0017 grilling
Area: annotation UI, user trust

Context:

A visible "last saved" status for crops and ellipses would help the Dataset Curator trust that long annotation work is safe. Current crop and ellipse actions persist immediately, and Slice 0017 makes saved work visible after reload/restart.

Why parked:

A reliable last-saved display should be based on a consistent updated-at policy across Training Crops, Oriented Bee Ellipses, Dataset Items, and future richer draft edits. That would widen the resume slice.

Revisit trigger:

Before adding richer local-only editing, keyboard-heavy annotation, multi-step draft workflows, or whenever users need stronger save confirmation than seeing the saved crop/ellipse reappear.

Suggested owner or area:

Annotation UI and product workflow.

## PARK-0022: Inspection-Level Annotation Complete Workflow

Status: parked
Date parked: 2026-07-31
Source: Slice 0017 grilling
Area: annotation workflow, dataset curation

Context:

Slice 0017 deliberately does not define when a Training Data Collection Inspection is "annotation complete." Possible meanings include every uploaded photo reviewed, every intended crop completed or excluded, every visible bee circled, every crop dataset-assigned, or some future quality threshold.

Why parked:

The product semantics are not clear enough yet. The immediate need is pause/resume safety for saved crops and ellipses.

Revisit trigger:

After enough real annotation sessions exist to define what "done" means, or before reporting dataset readiness at Inspection level.

Suggested owner or area:

Dataset curation, product requirements, and annotation workflow.

## PARK-0023: Persistence Mode Warning In The UI

Status: parked
Date parked: 2026-07-31
Source: Slice 0017 grilling
Area: developer experience, data safety

Context:

Real annotation work should use the Postgres-backed stack (`pnpm dev:all:yolo-training`). The in-memory stack can only resume while the process stays alive. Slice 0017 requires clear closeout/docs reminders, but does not add an in-app persistence-mode warning.

Why parked:

An in-app banner needs a broader UX decision about showing technical runtime status to the user. The practical minimum for Slice 0017 is explicit documentation and closeout guidance.

Revisit trigger:

Before non-developer annotation sessions, before handing the tool to another curator, or if any annotation work is lost because the wrong local stack was used.

Suggested owner or area:

Developer experience, Web UI, and data safety.

## PARK-0024: Durable Candidate Annotation Audit History

Status: parked
Date parked: 2026-07-31
Source: Slice 0015.2 grilling
Area: model governance, annotation workflow

Context:

Slice 0015.2 keeps model-generated Candidate Annotations transient and persists only accepted or edited proposals as reviewed Oriented Bee Ellipses with model-candidate provenance. Rejected suggestions are not durably recorded.

Why parked:

A full Candidate Annotation audit ledger would widen the crop pre-labelling slice into durable proposal lifecycle design, rejection history, blind-review comparison support, and active-learning evidence. The immediate learning goal is whether a completed Model Candidate can help annotate new crops under human review.

Revisit trigger:

Before blind-review comparison, model-assisted benchmark governance, active-learning workflows, persisted rejection analytics, or any workflow that needs to prove which model suggestions were rejected rather than simply absent from reviewed evidence.

Suggested owner or area:

Model governance, annotation workflow, and persistence design.

## PARK-0025: Bee Detector Complete/Partial Classification Reliability

Status: parked
Date parked: 2026-07-31
Source: Slice 0015.2 grilling
Area: model quality, Varroa pipeline

Context:

Slice 0015.2 treats YOLO OBB Model Candidate output primarily as bee geometry suggestions. Suggested annotations default to `complete_visible_bee`, while the curator can accept as `partial_visible_bee`. The raw model-proposed class is retained as provenance, but the model is not trusted to distinguish complete and partial bees.

Why parked:

Complete visible bees and partial visible bees may have different downstream behaviour for Varroa denominator logic, Varroa crop generation, benchmark reporting, and user-facing analysis. The current seed dataset is too small to rely on model classification quality.

Revisit trigger:

Before using Bee Detector outputs for Varroa denominator logic, Varroa crop generation, model-quality benchmark reporting, or user-facing analysis.

Suggested owner or area:

Bee Detector evaluation, Varroa Detector planning, and model governance.

## PARK-0026: Dataset Item Reassignment And Supersession UI

Status: parked
Date parked: 2026-08-01
Source: Slice 0015.3 grilling
Area: dataset governance, annotation repository, UI usability

Context:

Slice 0015.3 introduces a read-only Bee Annotation Repository page. The browser will make it obvious when a Dataset Item appears to have the wrong Dataset Role, note, or dataset eligibility state, but changing that evidence is not a simple edit. Dataset Items are immutable once assigned; correction should use a deliberate supersession workflow, especially once Dataset Versions and Training Runs may have consumed the original item.

Why parked:

Adding reassignment, supersession, deletion, or bulk actions would turn the repository browser into a write-side governance workflow. That would widen Slice 0015.3 beyond visibility and could undermine Dataset Version traceability.

Revisit trigger:

When curator review of the Bee Annotation Repository shows real assignment mistakes that need correction, before supporting dataset-quality cleanup at scale, or before allowing external/non-developer curators to maintain Dataset Items.

Suggested owner or area:

Dataset governance, persistence design, and Web UI.

## PARK-0027: Legacy Ellipse Head Direction Review

Status: superseded
Date parked: 2026-08-02
Source: Slice 0015.35 Directed Bee Ellipse Orientation planning
Area: annotation quality, model governance, Varroa pipeline

Context:

ADR 0006 changes Oriented Bee Ellipse rotation semantics from undirected body-axis alignment to directed center-to-head orientation. Existing reviewed ellipses created before this decision may have useful body-axis geometry but ambiguous head/tail direction.

Why superseded:

Slice 0015.35 now includes a one-time local cleanup instead of parking a legacy-review workflow: remove stale Dataset Items, Dataset Versions, Training Runs, Model Candidates, and derived artifacts, while preserving photos, Training Crops, and ellipses for manual review and fresh Dataset Role assignment.

Revisit trigger:

Before using pre-Slice-0015.35 Dataset Items for Varroa-direction-dependent training, before creating a benchmark claim that relies on bee head/tail direction, or when enough legacy annotated crops exist that manual re-review becomes necessary.

Suggested owner or area:

Dataset curation, annotation UI, and model governance.

## PARK-0028: Automated Bee Head Direction Prediction

Status: parked
Date parked: 2026-08-02
Source: Slice 0015.35 grilling
Area: model capability, Varroa pipeline, inspection automation

Context:

Slice 0015.35 makes reviewed Oriented Bee Ellipses direction-aware by defining `rotation_degrees` as center-to-head orientation. The first implementation keeps head/tail direction under human review. YOLO OBB can propose Bee Localisation geometry and body-axis alignment, but it should not be assumed to predict biologically meaningful head direction reliably.

ADR 0007 defines Bee Orientation as a distinct logical Model Purpose between Bee Localisation and Varroa Detection. The first implementation will be a binary head/tail classifier on body-axis-normalized bee crops; a keypoint/pose or multi-head model remains an alternative if benchmark evidence shows the classifier is inadequate.

For future real hive inspections, HiveSight needs a model pipeline that can identify every visible bee and its correct head/tail orientation without human intervention. This matters because the future Varroa Detector is expected to work on bee-relative crops: each bee image may be extracted, rotated into a consistent head/tail orientation, and then passed into Varroa mite detection. If head direction is wrong, Varroa-location evidence and mite detection quality may degrade.

Why parked:

The current training-data workflow is still building the first governed bee dataset. Predicting head direction may require a different model task or multi-model pipeline, such as bee detection plus keypoint/pose prediction, a head/tail classifier on bee crops, or another specialist orientation model. Designing that before there is enough reviewed directed-ellipse evidence would be premature.

Revisit trigger:

Before the first user-facing Varroa Assessment pipeline, before automated bee crop normalization for Varroa detection, before replacing human-reviewed head direction with model-predicted direction, or when enough directed bee annotations exist to evaluate head-direction prediction.

Suggested owner or area:

Bee Detector model design, Varroa Detector planning, dataset curation, and model evaluation.

## PARK-0029: Orientation Reliability Review And Dataset Gate

Status: parked
Date parked: 2026-08-02
Source: Three-stage model pipeline grilling
Area: annotation workflow, dataset governance, persistence

Context:

ADR 0007 requires reviewed Bee Annotations to carry Orientation Reliability: `reliable` or `unreliable`, independently of bee-presence confidence and review status. Existing directed ellipses do not yet have this field, so their head direction must not be assumed reliable merely because a rotation was recorded.

Why parked:

The current implementation provides directed ellipse review but does not yet persist Orientation Reliability or provide a dedicated review queue. The current early corpus is small enough for a one-time human review when the field is introduced.

Revisit trigger:

Before creating the first Bee Orientation Dataset Version, the first head-normalized Varroa Dataset Version, or any model evaluation that claims head-direction evidence.

Suggested owner or area:

Annotation workflow, dataset governance, and persistence design.

## PARK-0030: Inspection-Rate Sampling Policy

Status: parked
Date parked: 2026-08-02
Source: Three-stage model pipeline grilling
Area: Varroa assessment, statistics, product safety

Context:

HiveSight distinguishes `model_curation` sampling, which builds representative training and benchmark evidence, from `inspection_rate_estimation` sampling, which would support a future beekeeper-facing Visible Varroa Rate with a stated confidence interval and margin of error. Both may use the same CAPTCHA-like Varroa review UI, but their selection rules and evidence claims differ.

Why parked:

The current work establishes model data and does not yet provide a user-facing Varroa assessment. A rate-estimation policy must account for the intended confidence level and margin, finite population size, within-frame clustering, sampling frame, and upstream model uncertainty before any statistically stated product claim is made.

Revisit trigger:

Before the first user-facing Varroa Assessment slice, before displaying a confidence interval, or before presenting a sampled visible Varroa rate as more than uncalibrated evidence.

Suggested owner or area:

Product requirements, statistical design, model evaluation, and beekeeper-facing UX.

## PARK-0031: User-Facing Varroa Coverage Threshold

Status: parked
Date parked: 2026-08-02
Source: Three-stage model pipeline grilling
Area: model evaluation, product safety, beekeeper-facing UX

Context:

HiveSight will always show a coverage warning when one or more complete visible bees are not assessed for Varroa. Once real end-to-end evidence supports a coverage threshold, a headline Visible Varroa Rate below that threshold will be suppressed rather than displayed with a warning alone.

Why parked:

The project does not yet have a representative End-to-End Pipeline Evaluation corpus or evidence to choose a defensible threshold. Selecting one now would be arbitrary.

Revisit trigger:

Before promoting the first user-facing Varroa pipeline, when representative end-to-end coverage data is available, or when defining model promotion thresholds.

Suggested owner or area:

Model evaluation, product requirements, statistical design, and beekeeper-facing UX.

## PARK-0032: Inadequate-Coverage Review Recovery

Status: parked
Date parked: 2026-08-02
Source: Three-stage model pipeline grilling
Area: Varroa assessment UX, review workflow, model governance

Context:

When a user-facing Visible Varroa Rate is suppressed for inadequate coverage, the Workspace owner should be able to open an Inspection Recovery Review: a distinct, named, saveable, and resumable session linked to a fixed snapshot of the original model-only result and its photo evidence. It remains available for retained inspection history after Workspace Data Use Agreement withdrawal, but recovery evidence is ineligible for model improvement without an active agreement and independent curation. Newer models are not run or substituted during recovery. Every annotation and Varroa decision made in recovery retains its recovery-review provenance and is reported as AI-assisted-reviewed, never human-from-scratch, because the original model output was visible. Model promotion never automatically reanalyses historical Inspection Photos; a future explicit Historical Reanalysis creates a new model-only result without changing prior model-only or human-reviewed results. In the first release this route is available only for suppressed model-only results, not every completed inspection, and only the Workspace owner may create, resume, or complete it. The owner may complete it at any coverage level after explicit confirmation, including when the headline rate remains suppressed. A completed review and result are immutable; a later correction creates a new linked review and human-reviewed result revision. The latest completed human-reviewed result becomes the inspection's current result by default, while the original model-only result and earlier human-reviewed revisions remain available as labelled comparison history. The reviewer may resolve previously unassessed complete visible bees and correct any model-produced bee, orientation, or Varroa decision. The original model-only result must remain immutable while the recovery workflow calculates and shows a separately provenanced human-reviewed inspection result alongside it. Both results must show a Result Evidence Breakdown: positive, active negative, `not_determined`, and unassessed complete visible-bee counts, plus Review Completion and Determinate Varroa Coverage. `not_determined` counts only toward Review Completion. The human-reviewed result must remain suppressed when an evidence-based determinate-coverage threshold is still not met. This is product feedback only until a Dataset Curator independently reviews it and assigns a Dataset Role; it is not automatic training-data intake.

Why parked:

User-facing Varroa Assessment, the coverage threshold, and the complete review UX do not yet exist. The current product evidence flow already distinguishes User Corrections and reviewed dataset evidence, but needs a purpose-built recovery journey.

Revisit trigger:

Before the first user-facing Varroa Assessment slice, when implementing coverage suppression, or when adding complete-bee review/correction for model output.

Suggested owner or area:

Varroa assessment UX, review workflow, dataset governance, and acceptance testing.

Recovery evidence created while the Workspace Data Use Agreement is withdrawn remains product-only after later agreement acceptance. Model use requires a separate explicit Workspace owner dataset-contribution decision, followed by independent Dataset Curator review and Dataset Role assignment.

Each Dataset Contribution Decision applies to exactly one named completed Human-Reviewed Inspection Result revision; it is not a workspace-wide opt-in or Dataset Role assignment.

## PARK-0033: General Inspection Review And Correction

Status: parked
Date parked: 2026-08-02
Source: Three-stage model pipeline grilling
Area: inspection UX, review workflow, model governance

Context:

The first Inspection Recovery Review is intentionally available only when a model-only user-facing Varroa result is suppressed for inadequate coverage. A future general review workflow could allow a beekeeper to correct any completed inspection, including results whose coverage was adequate.

Why parked:

The initial recovery workflow solves the safety-critical inadequate-coverage case. A general inspection editor is a larger product and governance decision that should be designed deliberately rather than becoming an accidental extension.

Revisit trigger:

After the first user-facing Varroa Assessment recovery workflow has been demonstrated, or when ordinary completed inspections need user correction.

Suggested owner or area:

Inspection UX, model governance, and acceptance testing.

## PARK-0034: Historical Inspection Reanalysis

Status: parked
Date parked: 2026-08-02
Source: Three-stage model pipeline grilling
Area: inspection history, model lifecycle, provenance

Context:

Model promotion must never automatically reanalyse historical Inspection Photos. A future Workspace owner-initiated Historical Reanalysis should run a selected newer model against an existing photo and create a new model-only result, preserving all prior model-only and human-reviewed results for comparison.

Why parked:

The first user-facing Varroa Assessment and recovery workflow need stable provenance first. Reanalysis needs a deliberate model-selection, queueing, cost, and comparison experience.

Revisit trigger:

After the first promoted user-facing model is available, or when a Workspace owner asks to compare a historic inspection against a newer model.

Suggested owner or area:

Inspection UX, model lifecycle, background jobs, and acceptance testing.

## PARK-0035: Public Source Licence Compatibility Review

Status: parked
Date parked: 2026-08-02
Source: Contributor permission and source-rights grilling
Area: source rights, legal/policy, model governance

Context:

HiveSight records Source Rights Records, curator approval, permitted-use scopes, attribution, and Source Rights Invalidation for public/open evidence. The current approved boundary is local research and model development only unless a rights record explicitly permits broader use.

Why parked:

Detailed compatibility assessment for non-commercial, share-alike, redistribution, attribution, and model-output obligations needs formal legal/policy review. HiveSight must not infer that a public/open image licence permits sharing, publication, commercial use, or user-facing deployment.

Revisit trigger:

Before any public-source evidence supports a shared or published dataset, model release, commercial activity, or user-facing deployment; or before importing a source with non-standard or restrictive terms.

Suggested owner or area:

Legal/policy review, Dataset Curator governance, and model release management.

## PARK-0036: Benchmark Dataset Version Lifecycle

Status: parked
Date parked: 2026-08-03
Source: Slice 0015.4 planning
Area: model evaluation, dataset governance, curator UX

Context:

Slice 0015.4 uses protected benchmark Dataset Items already frozen inside the evaluated Model Candidate's Training Run Dataset Version as the first benchmark selection snapshot. That is enough to produce the first Bee Localisation Benchmark Evaluation report.

Why parked:

A separate benchmark-only Dataset Version lifecycle introduces curation UI, locking rules, source-group governance, report comparison rules, and permission/scope impact handling beyond the first evaluation proof point.

Revisit trigger:

Before comparing multiple Model Candidates against the same named benchmark, before publishing model-quality numbers, before promotion workflow, or when benchmark curation needs its own named lifecycle.

Suggested owner or area:

Dataset governance, model evaluation, and curator UX.

## PARK-0037: Precise Rotated Geometry Evaluation

Status: parked
Date parked: 2026-08-03
Source: Slice 0015.4 planning
Area: model evaluation, geometry, bee localisation metrics

Context:

Slice 0015.4 starts with `ellipse_match_v1`, a simple replaceable matching rule based on center distance plus radius/area overlap approximation. It reports complete and partial visible bee precision/recall separately without claiming precise rotated IoU scoring.

Why parked:

Precise rotated-box or ellipse IoU adds geometry complexity that is not needed for the first benchmark-reporting path. The first slice needs an honest, deterministic comparison rule more than it needs a perfect metric.

Revisit trigger:

Before publishing Bee Localisation quality claims, before model promotion, when two candidate models appear close enough that the approximate matcher may change the decision, or when rotated geometry utilities already exist with focused tests.

Suggested owner or area:

Model evaluation and geometry utilities.

## PARK-0038: Full-Frame Bee Localisation Evaluation

Status: parked
Date parked: 2026-08-03
Source: Slice 0015.4 grilling
Area: model evaluation, bee localisation, full-frame benchmark evidence

Context:

Slice 0015.4 evaluates Bee Localisation Model Candidates against Training Crop benchmark Dataset Items. That proves the benchmark workflow and measures crop-level localisation, but it does not answer whether the model can find bees across realistic whole-frame inspection photos.

Why parked:

Full-frame evaluation needs different benchmark evidence, image-scale handling, source-group governance, UI/report caveats, and likely different matching/performance expectations. Adding it now would widen the first benchmark-reporting slice.

Revisit trigger:

After crop-level Benchmark Evaluation is implemented and at least one trained candidate has been measured, before making whole-frame Bee Localisation claims, or before starting the user-facing Varroa Assessment pipeline.

Suggested owner or area:

Model evaluation, dataset governance, and future Varroa Assessment pipeline planning.

## PARK-0039: Assigned Review And Contribution Task Inbox

Status: parked
Date parked: 2026-08-03
Source: Slice 0018 grilling
Area: review workflow, contributor workflow, authorization

Context:

Reviewers and contributors will need to see work assigned to them from another User's Workspace without gaining broad Workspace Membership or visibility into that Workspace. This may become a task or inbox concept rather than a message-queue technology decision.

Why parked:

Slice 0018 establishes development User switching and Workspace separation only. Cross-user work assignment, task visibility, blind-review access, contributor bundles, and adjudication workflow would make the slice too large.

Revisit trigger:

Before Blind Independent Review, Third-Party Adjudication, external contributor annotation, Contribution Bundle tasks, or any workflow where one User needs to work on evidence owned by another User's Workspace.

Suggested owner or area:

Review workflow, contributor workflow, authorization, and product UX.

Promotion note:

Partially promoted into `architecture/vertical-slice-0019-reviewer-work-queue.md` for the shared Reviewer Work Queue path only. The design deliberately favours a common eligible-review pool over named reviewer assignment. Contributor task inboxes, Contribution Bundles, permission acceptance, and contributor withdrawal remain deferred.

## PARK-0040: Reviewer Correction Workflow

Status: parked
Date parked: 2026-08-03
Source: Slice 0019 grilling
Area: review workflow, annotation correction, model governance

Context:

Slice 0019 deliberately keeps queue review completion at task level: `approved`, `changes_requested`, or `not_determined`, with notes. A deeper review workflow will need to let a Reviewer identify which individual annotation is wrong, propose corrected geometry or classification, and retain clear correction provenance without mutating the original annotation evidence.

Why parked:

Adding per-ellipse correction would widen Slice 0019 beyond proving shared review queue work and limited evidence access. It belongs with Blind Independent Review, reviewer correction, adjudication, or Varroa benchmark evidence rather than the first Reviewer Work Queue slice.

Revisit trigger:

Before Blind Independent Review, Third-Party Adjudication, benchmark Varroa review, reviewer-created replacement annotations, or any workflow where `changes_requested` notes are no longer sufficient.

Suggested owner or area:

Review workflow, annotation correction, dataset governance, and future Varroa benchmark governance.

## PARK-0041: Workspace Collaboration And Membership Model

Status: parked
Date parked: 2026-08-03
Source: Slice 0018 grilling
Area: workspace membership, collaboration, authorization

Context:

The stronger expected use case is multiple Users sharing one Workspace, such as a family, bee club, association, or small business managing the same apiaries and hives. A User belonging to multiple Workspaces is not ruled out, but it is not the main near-term assumption.

Why parked:

Slice 0018 gives each seeded development User one default Workspace and avoids Workspace switching. Collaboration affects invitations, access lists, audit trails, default Workspace choice, and the semantics of "who am I acting for?"

Revisit trigger:

Before invitations, shared apiary/hive management, family/business accounts, beekeeper associations, or any workflow where multiple Users act inside one Workspace. Decide then whether one User can belong to multiple Workspaces and how Workspace switching/default Workspace works.

Suggested owner or area:

Product requirements, domain model, authorization, and Web UI.

## PARK-0042: Real Authentication Provider And Session Architecture

Status: parked
Date parked: 2026-08-03
Source: Slice 0018 grilling
Area: authentication, authorization, security

Context:

HiveSight should not roll its own password, account recovery, or social-login implementation. Real authentication should be delegated to an external OpenID Connect identity provider, probably Google first, with Apple or other providers considered later. HiveSight still owns Workspace Membership, Internal Capabilities, Contributor Access Scope, and authorization decisions.

Why parked:

Slice 0018 is a development identity-switching slice, not production authentication. The real authentication choice is long-lived and should produce an ADR before implementation.

Revisit trigger:

Before external users, hosted deployment, Contribution Bundles, shared Workspaces, non-local use, or implementing any real login provider.

Suggested owner or area:

Architecture, security, authentication, and product governance.

## PARK-0043: Review Queue Claiming And Multi-Reviewer Rules

Status: parked
Date parked: 2026-08-03
Source: Slice 0019 grilling
Area: review workflow, queue operations, model governance

Context:

Slice 0019 uses a shared eligible-review pool. It deliberately does not assign items to named Reviewers, does not claim or lease review work, and closes a Review Queue Item after the first eligible Reviewer completion. This is enough to prove limited cross-Workspace review access and task-level outcomes.

Why parked:

Claiming, leases, stale work recovery, required reviewer counts, disagreement handling, and adjudication would widen the first review queue slice. They become important once reviews are no longer simple task-level checks or when several independent outcomes are required before benchmark or model-governance decisions.

Revisit trigger:

Before Blind Independent Review, Third-Party Adjudication, multi-review benchmark governance, reviewer disagreement metrics, or any queue where stale in-flight work can block progress.

Suggested owner or area:

Review workflow, queue operations, authorization, and model governance.

## PARK-0044: Crop Boundary Duplicate Partial Bee Handling

Status: parked
Date parked: 2026-08-03
Source: Annotation seeding discussion
Area: dataset quality, sampling validity, bee localisation, Varroa denominator logic

Context:

Early Bee Localisation seeding uses manually placed Training Crops within a larger frame photo. When adjacent crops touch or overlap, the same physical bee can appear partly in two crops. The curator may correctly annotate each visible fragment as `partial_visible_bee`, which is useful for teaching the Bee Detector that edge-visible bee fragments are still bees.

Why parked:

This is acceptable for early YOLO OBB seeding, but it is not safe to treat duplicated partial crop-edge annotations as independent bees for counting, infestation-rate estimation, protected benchmark claims, or Varroa sampling. Complete visible bees can support bee-population denominator logic more directly; partial visible bees need source-frame-level reconciliation before they can be interpreted as unique physical bees.

Revisit trigger:

Before using Training Crop evidence for user-facing bee counts, infestation-rate denominators, protected full-frame benchmark evidence, Varroa crop sampling, or any statistically stated claim that depends on unique bee counts across crop boundaries.

Suggested owner or area:

Dataset governance, Bee Localisation evaluation, Varroa sampling design, and future full-frame annotation/reconciliation workflow.

## PARK-0045: Crop Bounds Editing After Save

Status: parked
Date parked: 2026-08-03
Source: Slice 0020 grilling
Area: crop selection, annotation UI, dataset governance

Context:

Slice 0020 keeps Training Crop creation simple: the Dataset Curator can create and delete eligible crops, but does not get a first-class edit/resize/reposition workflow for crop bounds after save.

Why parked:

Changing crop bounds after ellipses, review requests, or Dataset Items exist is not just a UI edit. It raises questions about whether existing bee ellipses remain valid, whether review evidence has been changed, whether Dataset Item snapshots must be invalidated, and whether downstream Dataset Versions or Training Runs have consumed the old crop evidence.

Revisit trigger:

When crop-placement mistakes become common enough that delete-and-recreate is not acceptable, before supporting non-developer curators at scale, or before implementing richer crop drafting with resize handles.

Suggested owner or area:

Training Crop workflow, annotation UI, and dataset governance.

## PARK-0046: Bulk Dataset Role Assignment

Status: parked
Date parked: 2026-08-03
Source: Slice 0020 grilling
Area: dataset governance, curator productivity

Context:

Slice 0020 keeps Dataset Role assignment as an explicit selected-crop governance action. It does not introduce bulk assignment of many completed crops into `training`, `validation`, `benchmark`, or `excluded`.

Why parked:

Bulk assignment is useful, but it can amplify mistakes. It needs clearer guardrails around review strength, source-image leakage, source groups, benchmark protection, and whether all selected crops have comparable annotation quality.

Revisit trigger:

When individual assignment becomes the bottleneck for a real corpus, after Crop Governance has made per-crop status and warnings clear enough to support safe bulk decisions.

Suggested owner or area:

Dataset governance, Repository UX, and acceptance testing.

## PARK-0047: Resume Exact Training Workflow Position

Status: parked
Date parked: 2026-08-03
Source: Slice 0020 grilling
Area: inspection resume, annotation UX

Context:

Slice 0020 derives the initial stage from saved Inspection state, but does not persist the exact stage, selected Source Image, selected Training Crop, zoom, pan, or editor position the Dataset Curator last used.

Why parked:

Persisting exact UI position can become stale and create a second source of truth if it is introduced too early. The current slice focuses on making saved domain records easy to find and safe to work with.

Revisit trigger:

When long annotation sessions routinely span several days or several inspections, and resuming the exact crop/stage becomes more valuable than deriving a sensible starting point.

Suggested owner or area:

Web UI, inspection resume, and annotation productivity.

## PARK-0048: Dedicated Model Governance Page

Status: parked
Date parked: 2026-08-03
Source: Slice 0020 grilling
Area: model governance, Repository UX

Context:

Slice 0020 keeps Dataset Version creation, Bee Detector Training Runs, Model Candidate selection, and Benchmark Evaluation controls in the Repository page. Crop Governance is limited to decisions about the selected Inspection's crops.

Why parked:

The model-governance controls are now substantial enough that they may deserve a separate page, but moving them while also separating the Training Inspection workflow would widen Slice 0020 unnecessarily.

Revisit trigger:

When comparing multiple Model Candidates, managing reusable benchmark sets, promoting candidates, or operating model jobs becomes too crowded for the Repository page.

Suggested owner or area:

Model governance, Repository UX, and operations.

## PARK-0049: Negative Or Background Bee Localisation Dataset Role

Status: parked
Date parked: 2026-08-03
Source: Slice 0020 grilling
Area: dataset governance, bee localisation training

Context:

Slice 0020 treats a completed Training Crop with `no_visible_bees` as ineligible for the positive bee-detector training dataset. Such crops may still be useful as explicit negative or background examples later.

Why parked:

Adding a negative/background role changes dataset export semantics, training configuration, evaluation expectations, and curator guidance. It should be designed deliberately rather than hidden inside workflow separation.

Revisit trigger:

Before training Bee Localisation models with explicit background examples, before false-positive reduction becomes the limiting model-quality problem, or before full-frame/tiled training export.

Suggested owner or area:

Bee Localisation model training, dataset export, and dataset governance.

## PARK-0050: Cross-Inspection Submitted Review Dashboard

Status: parked
Date parked: 2026-08-03
Source: Slice 0020 grilling
Area: review workflow, curator UX

Context:

Slice 0020 may show a selected-Inspection `Waiting for review` filter or section, but it does not add a broader dashboard where a Dataset Curator can see all their submitted crops waiting for review across hives and inspections.

Why parked:

The selected-Inspection governance view is enough for the workflow separation slice. Cross-inspection chasing, reminders, stale-review handling, and reviewer capacity belong with the wider review operations design.

Revisit trigger:

When review wait states span multiple inspections or users need to chase, cancel, or re-route review work across the whole Workspace.

Suggested owner or area:

Review workflow, curator UX, and queue operations.
