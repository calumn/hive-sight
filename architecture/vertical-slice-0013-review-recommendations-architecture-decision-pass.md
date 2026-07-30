# Vertical Slice 0013: Review Recommendations Architecture Decision Pass

Status: implemented.

## Purpose

Close the external review loop before returning to product/model feature slices.

This is an architectural planning slice. Its deliverable is not new user-facing functionality; it is a documented decision pass over all five Claude review recommendations so HiveSight has an explicit answer for each one:

- implement now
- convert into a remediation slice
- convert into a future functional slice
- park with a revisit trigger
- close as no longer needed

The slice should leave the project with a clear next delivery path and no review recommendation sitting only in chat history.

## Source Inputs

- `architecture/review-remediation-2026-07-30.md`
- `architecture/review-remediation-0001-extract-domain-rules-out-of-dev-store.md`
- `architecture/parking-lot.md`
- `architecture/codebase-design.md`
- `architecture/domain-model.md`
- `architecture/adr/0001-service-oriented-architecture.md`
- `requirements/model-requirements.md`
- `requirements/ai-assisted-annotation-and-model-training-baseline.md`
- `requirements/bee-annotation-repository-and-curriculum-training-baseline.md`
- `requirements/ai-sdlc-observations.md`
- `reports/slice-verification/latest.md`

## User Path

Given the team has paused functional slices to handle review feedback
When the team completes the architecture decision pass
Then each external review recommendation has a documented outcome
And any follow-on work is either promoted into a slice/remediation item or parked with a revisit trigger
And the next product/model slice can start without hidden review debt.

## Preconditions

- Review Remediation 0001 has been implemented and verified.
- The skills remediation has been implemented and verified.
- `architecture/parking-lot.md` exists and is the canonical place for deferred but important work.
- No new product capability is expected from this slice.
- Decisions that affect architecture direction should be recorded in ADRs or remediation docs, not only in the slice document.

## Locked Decisions From Grilling

- Keep the Analysis Service as a separate service boundary.
- Preserve the async/event/queue architecture shape for Analysis Service integration, but use an in-memory queue adapter before choosing durable queue technology.
- Analysis Service integration does not block the YOLO OBB Training Baseline, but the integration direction must be recorded before model work deepens.
- Persistence is the most urgent load-bearing architecture decision before the training baseline.
- Before real persistence is implemented, classify the domain model into stable records, version/history-sensitive records, and volatile/deferred records.
- Persist one narrow path first: the Bee Annotation Repository path needed to feed training.
- Use Postgres for durable product and model-governance metadata.
- Keep image bytes outside Postgres; Postgres stores metadata, object keys, provenance, status, and relationships.
- Keep the in-memory adapter for fast unit/workflow tests, but move API/BDD/browser acceptance to Postgres-backed persistence once Slice 0014 lands.
- Include database migrations from day one, with local reset/seed commands.
- Persist deterministic dev personas and Internal Capabilities as seed data in Slice 0014, but keep the dev persona switcher UI as its own slice.
- Do not choose production auth provider, object storage provider, durable queue technology, or deployment platform yet; park them with explicit triggers.
- Standardize on Playwright specs plus generated verification reports for UI acceptance for now; keep UI-level Gherkin parked.
- Correct Varroa traceability wording inside Slice 0013 where docs imply implemented capability has outrun evidence.
- Make Slice 0014 Postgres-backed Bee Annotation Repository persistence a prerequisite for Slice 0015 YOLO OBB Training Baseline.
- Keep Training Run and Model Candidate tables out of Slice 0014; add them in Slice 0015 with the training baseline workflow.
- Keep Slice 0014 Core API-owned only; Analysis Service storage ownership is decided during a later Analysis Service integration slice.
- Preserve local network/mobile UI testing when Postgres is introduced.
- Production deployment remains out of scope until after persistence and model-baseline decisions.
- Create ADRs only for accepted architecture decisions, not deferred choices.
- Slice 0013 should create:
  - `architecture/adr/0003-postgres-for-durable-product-and-model-governance-metadata.md`
  - `architecture/adr/0004-keep-analysis-service-separate-and-integrate-through-async-workflow.md`
  - `architecture/current-system-architecture.md`
  - `architecture/proposed-system-architecture.md`
  - `architecture/postgres-persistence-design.md`
- Current and proposed architecture snapshots should include Mermaid diagrams and honest known-gaps sections.
- `architecture/postgres-persistence-design.md` should include a proposed Mermaid ER diagram for the Slice 0014 schema.
- `architecture/system-context.md` should remain high-level, with a short cross-reference to the new architecture snapshots.
- Slice 0013 should not add runtime tests, but should run the existing verification suite for the current code tranche.

## Review Recommendations Covered

### R-001: Extract Domain Logic Out Of `dev_store.py`

Current state:

Review Remediation 0001 partially actioned this recommendation. Hive Configuration, Inspection gating, Training Crop rules, and Training Crop Dataset Item assignment now live in explicit workflows. Residual debt remains around export/package construction, authorization policy, and real persistence.

Slice 0013 decision required:

- Decide whether the remaining R-001 debt blocks the next functional/model slice.
- Decide whether to define a second remediation slice for export/package workflow extraction before persistence.
- Decide whether authorization policy extraction waits for real auth or gets a dev-only policy seam first.
- Decide whether formal repository protocols should be added before choosing real persistence.

Expected output:

- Update `architecture/review-remediation-2026-07-30.md` R-001 status and recommended next action.
- Add or update parked/remediation items for residual R-001 debt.

Locked decision:

R-001 remains partially actioned. Residual export/package construction and authorization-policy debt does not block Slice 0014 Postgres persistence. Export/package workflow extraction should be revisited after persistence and before or during Slice 0015 if it becomes load-bearing. Authorization policy extraction waits for real auth or a dev persona/capability slice.

### R-002: Decide Analysis Service Integration Direction

Current state:

The Analysis Service exists and is tested, but Core API still uses in-process stub analysis. This is a structural risk before real model training/inference work deepens.

Slice 0013 decision required:

- Choose one direction:
  - keep Analysis Service as a separate service and wire Core API to it through an owned contract
  - fold stub analysis back into Core API until real model runtime work justifies a separate service
  - keep the current split temporarily, but park it with a concrete trigger
- Decide whether this needs an ADR.
- Decide whether Slice 0015 YOLO OBB Training Baseline should proceed before or after this integration decision is implemented.

Expected output:

- ADR or explicit architecture note recording the chosen Analysis Service direction.
- Follow-on slice/remediation document if implementation is needed.

Locked decision:

R-002 is actioned as an architecture decision by ADR 0004. Analysis Service stays separate and will integrate through an async workflow shape. The next implementation should start with an in-memory queue adapter and owned contracts before choosing durable queue technology.

### R-003: Resolve UI-Level Gherkin Commitment

Current state:

API-level acceptance uses Gherkin and pytest-bdd. UI acceptance uses Playwright specs directly. `PARK-0001` already captures UI-level Gherkin as deferred.

Slice 0013 decision required:

- Decide whether UI-level Gherkin is:
  - required soon
  - optional later
  - explicitly dropped in favour of Playwright specs plus reports
- Decide what trigger promotes `PARK-0001`.
- Decide whether existing slice docs that mention UI-level Gherkin need wording updates.

Expected output:

- Update `PARK-0001` with a sharper status/trigger, or close it.
- Update delivery/testing docs if the standard changes.

Locked decision:

R-003 is actioned as a delivery-standard decision. UI acceptance remains Playwright specs plus generated verification reports for now. UI-level Gherkin remains parked as a future option, not a near-term promise.

### R-004: Revisit Load-Bearing Architecture Decisions

Current state:

The project still has no real persistence, queue, object storage provider, production auth provider, deployment platform, or Analysis Store decision. That was acceptable for early slices but is becoming load-bearing as model training and dataset export work grows.

Slice 0013 decision required:

- Decide which architecture decisions must be made before the next tranche.
- At minimum, explicitly triage:
  - persistence technology
  - object storage provider
  - queue or async boundary
  - auth provider and role/capability model
  - Analysis Store ownership
  - deployment target
  - upload/format limits and storage lifecycle
- Decide whether to create one broad ADR or several small ADRs.
- Decide which decisions block Slice 0015 and which can wait.

Expected output:

- ADR(s) or a decision matrix with status for each load-bearing decision.
- Parking-lot updates for any decision not made now.
- Follow-on slice/remediation docs for decisions that require implementation.

Locked decision:

R-004 is partially actioned by Slice 0013. Postgres is accepted for durable product and model-governance metadata. Object storage provider, durable queue technology, production auth provider, deployment target, Analysis Store ownership, and production upload/storage lifecycle remain deferred with explicit triggers.

### Dev Persona Switcher

Current state:

HiveSight uses dev authentication via `x-hivesight-dev-user-id`. This is acceptable for local development, but the UI does not yet make it easy to switch between seeded Users and Internal Capabilities when exercising role-specific behaviours.

Slice 0013 decision required:

- Decide where the dev persona switcher lands in the next delivery order.
- Keep it explicitly dev-only and separate from production authentication.
- Do not bundle it into the Postgres persistence slice unless Slice 0013 explicitly changes that decision.

Expected output:

- Update `PARK-0007` with a promoted slice number or a sharper revisit trigger.
- Decide whether the dev persona switcher happens before Slice 0014 persistence, after Slice 0014 persistence, or before the next role-specific UI acceptance flow.

Locked decision:

The dev persona switcher is a separate dev-only slice, not bundled into persistence. Slice 0014 should persist deterministic dev persona seed records and Internal Capabilities, but the UI selector remains parked until Slice 0013 closeout confirms whether it happens before or after persistence.

### R-005: Correct Varroa Traceability Claims

Current state:

Varroa detection remains the product goal. Implemented slices have focused mostly on bee annotation, dataset foundations, and bee-detector training preparation. Some docs may imply Varroa annotation is more operationalized than it is.

Slice 0013 decision required:

- Audit requirements, model requirements, domain model, and slice docs for Varroa claims.
- Decide which wording changes are factual corrections rather than scope changes.
- Decide when Varroa-specific annotation/model slices should resume.

Expected output:

- Correct misleading docs directly where wording has outrun implementation evidence.
- Keep valid future intent, but clearly distinguish modelled future capability from implemented behaviour.
- Update or close `PARK-0005`.

Locked decision:

R-005 is actioned if Slice 0013 corrects traceability wording so docs distinguish the Varroa product goal from implemented bee-annotation and bee-detector training foundations. Varroa detection remains future product/model scope, not open review-remediation debt.

## Recommendation Decision Matrix

| Item | Decision | Status After Slice 0013 | Follow-On |
| --- | --- | --- | --- |
| R-001 Domain logic in `dev_store.py` | Review Remediation 0001 handled the highest-risk rule clusters; remaining export/auth/persistence debt does not block Slice 0014. | Partially actioned | Revisit export/package extraction after Slice 0014 and before/during Slice 0015 if needed. |
| R-002 Analysis Service integration | Keep Analysis Service separate; integrate via async workflow shape with in-memory queue adapter first. | Actioned as architecture decision by ADR 0004 | Later Analysis Service integration slice; API contract governance trigger applies. |
| R-003 UI-level Gherkin | UI acceptance remains Playwright specs plus generated verification reports for now. | Actioned as decision; future capability parked | `PARK-0001` remains parked with sharper trigger. |
| R-004 Load-bearing architecture decisions | Choose Postgres now; defer auth provider, object storage provider, durable queue, deployment, and Analysis Store ownership. | Partially actioned by ADR 0003 and architecture snapshots | Slice 0014 Postgres persistence; parked triggers for the rest. |
| R-005 Varroa traceability | Correct wording that implies Varroa detection is implemented; keep Varroa as future product/model goal. | Actioned | `PARK-0005` closed. |
| Dev Persona Switcher | Persist dev persona seed records in Slice 0014; UI switcher remains separate dev-only slice. | Parked | `PARK-0007`; revisit before the next role-specific UI acceptance flow. |
| Slice 0015 YOLO OBB Training Baseline | Go after Slice 0014 Postgres persistence. | Parked pending Slice 0014 | `PARK-0006`. |

## Required Slice 0013 Artifacts

- ADR 0003: Postgres for durable product and model-governance metadata.
- ADR 0004: keep Analysis Service separate and integrate through async workflow.
- Current System Architecture snapshot with Mermaid diagrams and known gaps.
- Proposed System Architecture snapshot with Mermaid diagrams and known gaps.
- Postgres Persistence Design with persisted aggregate list, migration/test/seed strategy, and Mermaid ER diagram.
- Updated review-remediation tracker.
- Updated parking lot.
- Updated Varroa traceability wording.
- Updated Slice 0014 and Slice 0015 planning docs.
- Updated AI-SDLC observations.

## End-To-End Behaviour

The team reviews the five recommendations against current docs, code, tests, and verification evidence.

For each recommendation, the team records:

- current status
- decision
- rationale
- artifact updated
- follow-on owner or slice
- revisit trigger, if deferred

The slice ends when the architecture backlog is explicit enough to choose the next delivery item without rediscovering the same review concerns.

## Layers Touched

- Web UI: not touched unless testing-standard docs are updated.
- Core API: not touched unless tiny doc-linked code comments or route ownership notes are required.
- Analysis Service: not touched; integration direction is decided, not implemented.
- Storage: not touched; persistence direction is triaged, not implemented.
- Queue or async boundary: not touched; decision status is recorded.
- Contracts: no public contract changes; API contract governance may be promoted or parked.
- Observability: no runtime changes; verification/reporting evidence is reviewed.

## Test Seams

- Seam: Traceability audit
- Behaviour verified: each review recommendation has a current status, decision, rationale, and follow-on action.
- Test style: document review checklist.

- Seam: ADR/architecture docs
- Behaviour verified: any architecture direction chosen in the slice is recorded somewhere more durable than the slice document.
- Test style: artifact inspection.

- Seam: Parking lot
- Behaviour verified: deferred items have owners/areas and revisit triggers.
- Test style: artifact inspection.

- Seam: Verification report
- Behaviour verified: latest verification evidence is referenced honestly and not overstated.
- Test style: report inspection.

## Data Shape

No runtime data shape changes.

Planning artifacts should use this lightweight recommendation decision shape:

- recommendation id
- title
- current status
- decision
- rationale
- artifact updates
- follow-on slice/remediation/parking-lot id
- revisit trigger

Slice 0014 provisional persisted aggregate scope:

- User
- Workspace
- Workspace Membership
- Internal Capability
- Apiary
- Hive
- Hive Configuration
- Inspection
- Inspection Photo metadata and object key
- Training Crop
- Oriented Bee Ellipse
- Dataset Item
- Dataset Item ellipse snapshot
- Dataset Item provenance snapshot

Slice 0014 deliberately excludes:

- Training Run
- Model Candidate
- Model Version
- Benchmark Evaluation
- Analysis Result persistence changes
- image bytes in Postgres

## Out Of Scope

- Implementing Analysis Service integration.
- Implementing real persistence.
- Implementing production authentication.
- Implementing object storage or signed upload URLs.
- Implementing UI-level Gherkin.
- Implementing Varroa detection.
- Changing public API contracts.
- Changing Web UI behaviour.
- Reworking Slice 0015 implementation details beyond deciding whether it is still next.

## Acceptance Criteria

- [x] R-001 has an updated status and residual-debt decision.
- [x] R-002 has an explicit Analysis Service direction, either as an ADR or a documented deferred decision with trigger.
- [x] R-003 has an explicit UI acceptance-testing standard decision and `PARK-0001` is updated or closed.
- [x] R-004 has a triaged decision matrix for persistence, object storage, queue, auth, Analysis Store, deployment, and upload/storage lifecycle.
- [x] R-005 has a completed Varroa traceability audit and any misleading wording is corrected or parked.
- [x] Dev persona switcher ordering is decided before Slice 0014 starts.
- [x] All new deferred work is captured in `architecture/parking-lot.md` with revisit triggers.
- [x] Any material architecture choices are recorded in ADRs or existing architecture docs.
- [x] `architecture/review-remediation-2026-07-30.md` reflects the outcome of this pass.
- [x] `requirements/ai-sdlc-observations.md` records the review closeout outcome.
- [x] The final output names the next recommended build slice.
- [x] Slice 0014 is defined or updated as Postgres-backed Bee Annotation Repository persistence.
- [x] Slice 0015 clearly depends on Slice 0014 and remains parked until Slice 0013 closeout.

## Open Questions

- Resolved: Slice 0015 YOLO OBB Training Baseline depends on Slice 0014 Postgres persistence.
- Resolved: Analysis Service remains separate and is recorded in ADR 0004.
- Resolved: UI acceptance remains Playwright specs plus generated verification reports for now.
- Resolved: Postgres persistence is the most urgent load-bearing architecture decision.
- Resolved: dev persona seed records belong in Slice 0014, but the dev persona switcher UI is a separate parked slice.
- Resolved: Varroa traceability correction is handled inside Slice 0013.
- Resolved: Slice 0015 is `go after Slice 0014`.

## Closeout Decisions

- Next recommended build slice: Vertical Slice 0014, Postgres-Backed Bee Annotation Repository Persistence.
- Slice 0015 YOLO OBB Training Baseline remains parked and should proceed after Slice 0014 unless Slice 0014 uncovers a stronger blocker.
- Dev Persona Switcher remains parked until after Slice 0014, unless the next role-specific UI acceptance flow makes it urgent sooner.
- UI-level Gherkin remains parked as a future option; UI acceptance continues through Playwright specs plus generated verification reports.
