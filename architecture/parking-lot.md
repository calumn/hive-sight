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

Status: parked
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

## PARK-0007: Dev Persona Switcher

Status: promoted
Date parked: 2026-07-30
Source: Slice 0013 grilling
Area: developer experience, UI acceptance, authorization simulation

Context:

HiveSight currently uses dev authentication through `x-hivesight-dev-user-id`. Before real authentication is selected, the UI should make it easy to exercise behaviours as different seeded Users and Internal Capabilities, such as Beekeeper Owner, Dataset Curator, Reviewer, and a User with no internal capability.

Why parked:

This is useful and likely important for acceptance testing, but it should not be bundled into Postgres persistence. It touches UI ergonomics, seeded dev users, capability simulation, and test setup rather than durable schema design.

Revisit trigger:

Slice 0013 closeout decision: keep this after Slice 0014 unless role-specific UI acceptance becomes the immediate next workflow. Revisit before the next role-specific UI acceptance flow.

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

Slice 0014 snapshots Workspace Data Use Agreement eligibility at Dataset Item assignment time, but does not automatically propagate later consent withdrawal or deletion requests into exports, Training Runs, benchmark records, or already-trained artifacts.

Why parked:

Withdrawal and deletion enforcement require product, policy, legal, and technical decisions. A simple database rule would be misleading.

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

Bee detection and Varroa detection are separate logical model stages. That split helps measure each stage independently, but it does not automatically prevent the mite-training dataset from inheriting Bee Detector blind spots. If mite-training crops are selected only from bees found by the Bee Detector, the Varroa detector may never learn from missed bee populations such as shadowed, occluded, dense, or unusual-angle bees.

Why parked:

Slice 0015 trains only the HiveSight Bee Detector. Varroa mite annotation, mite crops, mite detector training, and bee-to-mite association are out of scope for the first YOLO OBB bee baseline.

Revisit trigger:

Before the first Varroa detector training slice, before creating a mite benchmark Dataset Version, or before using Bee Detector output as the sole source of mite-training crops.

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
