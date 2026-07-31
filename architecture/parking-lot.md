# Parking Lot

This document captures important work that is not in the current slice or remediation pass, but should not be forgotten.

Use this when something is out of scope now but expected later. Prefer ADRs or the decision log for settled decisions, and remediation trackers for known active problems.

## Status Values

- `parked`: deliberately deferred.
- `promoted`: moved into an active slice, remediation, ADR, or implementation plan.
- `closed`: no longer needed.
- `superseded`: replaced by another parked item or decision.

## PARK-0001: UI-Level Gherkin Harness

Status: parked
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

Status: parked
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

Status: parked
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

Suggested owner or area:

Model governance and architecture.

## PARK-0007: Dev Persona Switcher

Status: parked
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
