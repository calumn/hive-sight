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

The team wants UI-level Gherkin in the next few slices, but building a UI BDD harness would widen the current skills remediation and Review Remediation 0001 work.

Revisit trigger:

Before the next major UI workflow, or when acceptance reporting needs user-readable UI scenarios.

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

Before auth, object storage, signed upload URLs, role security, external APIs, or production deployment work.

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

Before Analysis Service integration, public API versioning, event schema evolution, or generated-client work.

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

When HiveSight chooses a deployment target or prepares an externally accessible environment.

Suggested owner or area:

Operations and release readiness.

## PARK-0005: Varroa Traceability Correction

Status: parked
Date parked: 2026-07-30
Source: HiveSight review
Area: requirements and domain model

Context:

Varroa detection remains the product goal, but delivered slices have intentionally focused on bee annotation and dataset foundations. Some traceability wording may imply Varroa Annotation is more operationalized than it is.

Why parked:

The current pause is focused on skills remediation and dev-store architecture remediation.

Revisit trigger:

Before starting Varroa-specific functional slices or updating model requirements for Varroa detection.

Suggested owner or area:

Requirements, domain model, and model governance.
