# Skills Remediation: 2026-07-30 Review

## Purpose

Capture the remediation plan from the external review of the personal SDLC skills library before changing the skills themselves.

The goal is not just to tidy the skills. The more important goal is to make the skills better at preventing drift across the software development lifecycle: vision, requirements, product specification, domain model, ADRs, vertical slices, implementation, tests, verification reports, and AI-SDLC observations.

## Source Inputs

- `/Users/calumnobles/Library/Application Support/Claude/local-agent-mode-sessions/d0655ebb-fa4f-4952-98d6-be6be63ef5b6/735d7aa0-a1d5-4bab-9628-53c087a8c8c3/local_4d71f726-6550-447c-9083-d4cff14f1d94/outputs/skills-review.md`
- Current skills library: `/Users/calumnobles/.agents/skills`
- `requirements/ai-sdlc-observations.md`
- `architecture/review-remediation-2026-07-30.md`
- `architecture/review-remediation-0001-extract-domain-rules-out-of-dev-store.md`

## Review Summary

The skills library is structurally strong:

- Naming taxonomy is consistent.
- Skill-to-skill references mostly resolve correctly.
- Several delivery and architecture skills contain concrete, reusable workflow guidance.
- Review checklists are a useful recurring pattern.

The review also found drift:

- Generic `sdlc-*` skills contain HiveSight/BeehiveMonitor-specific defaults.
- The project name appears inconsistently as both BeehiveMonitor and HiveSight.
- `SKILLS_INDEX.md` is stale and omits newer delivery skills.
- `sdlc-requirements-to-spec` still contains borrowed issue-tracker instructions and a dangling `/setup-matt-pocock-skills` reference.
- The skill library does not structurally force SDLC closeout, which contributed to `requirements/ai-sdlc-observations.md` going stale.
- There is no full-chain traceability audit skill.
- Some later SDLC concerns have no skill coverage yet: threat modelling, persistence/schema design, API contract governance, release readiness, and skill-library review.

## Remediation Principles

- Keep generic skills generic.
- Put HiveSight-specific defaults in a `hivesight-*` skill if they are worth preserving.
- Prefer small closeout steps embedded in existing frequently used skills over standalone skills that must be remembered manually.
- Add new skills only where they represent a repeatable SDLC activity, not a one-off cleanup.
- Keep skills concise and progressively disclosed; do not turn every skill into a large process manual.
- Update `SKILLS_INDEX.md` whenever skills are added, renamed, deleted, or materially re-scoped.
- Treat parked work as governed work: if something is important but not in the current slice, put it somewhere reviewable with a revisit trigger.

## Remediation Work Items

### SR-001: Remove Project-Specific Defaults From Generic Delivery Skills

Status: completed 2026-07-30

Problem:

The following generic `sdlc-delivery-*` skills contain BeehiveMonitor/HiveSight-specific guidance:

- `sdlc-delivery-dependency-injection`
- `sdlc-delivery-python-service-style`
- `sdlc-delivery-typescript-web-style`
- `sdlc-delivery-tdd`

This makes the reusable skills less portable and preserves the old BeehiveMonitor name.

Action:

- Remove the `BeehiveMonitor Defaults` sections from the generic skills.
- Remove direct references to HiveSight-specific modules from generic skill bodies.
- Keep only generic SDLC delivery guidance in these skills.

Acceptance criteria:

- [x] `rg "BeehiveMonitor|HiveSight" /Users/calumnobles/.agents/skills/sdlc-*` no longer finds project-specific defaults in generic skills.
- [x] Removed guidance is either discarded as obsolete or moved into a `hivesight-*` skill.

### SR-002: Create A HiveSight-Specific Skill For Project Defaults

Status: completed 2026-07-30

Problem:

Some removed guidance may still be useful while working on HiveSight, but it does not belong in generic `sdlc-*` skills.

Action:

Create a project-specific skill:

`hivesight-project-delivery-context`

Suggested trigger:

Use when working specifically inside the HiveSight project and needing project-specific delivery defaults, known seams, service boundaries, verification commands, domain vocabulary, or local workflow conventions.

Suggested contents:

- Canonical project name: HiveSight.
- Key service boundaries: Web UI, Core API, Analysis Service.
- Current dev auth shape: `x-hivesight-dev-user-id`.
- Existing important seams: `CoreApiClient`, `InspectionPhotoAccess`, analysis workflows, dataset labelling workflows, dataset/export workflows, model runtime/pre-labeller adapters.
- Verification command: `pnpm verify:slice`.
- Reminder that generic `sdlc-*` skills should still be used for reusable method guidance.
- Reminder to update `requirements/ai-sdlc-observations.md` at slice/remediation closeout.

Acceptance criteria:

- [x] A `hivesight-*` skill exists for project-specific delivery context.
- [x] Generic skills no longer need HiveSight-specific defaults to remain useful.
- [x] `SKILLS_INDEX.md` lists the new `hivesight-*` skill.

### SR-003: Update `SKILLS_INDEX.md`

Status: completed 2026-07-30

Problem:

The index lists 16 current skills while 18 skill folders exist. It omits:

- `sdlc-delivery-acceptance-bdd`
- `sdlc-delivery-test-automation-reporting`

Action:

- Add the missing skills to the Current Skills section.
- Add any newly created `hivesight-*` skill.
- Expand Suggested Future Skills with the gaps identified in this review.

Suggested future skills:

- `sdlc-governance-traceability-audit`
- `sdlc-security-threat-model`
- `sdlc-architecture-persistence-design`
- `sdlc-contract-api-governance`
- `sdlc-operations-release-readiness`
- `sdlc-skills-library-review`

Acceptance criteria:

- [x] Every immediate child skill folder under `/Users/calumnobles/.agents/skills` is listed in `SKILLS_INDEX.md`.
- [x] Suggested Future Skills reflects the known SDLC coverage gaps.

### SR-004: Repair `sdlc-requirements-to-spec`

Status: completed 2026-07-30

Problem:

`sdlc-requirements-to-spec` still assumes an issue tracker, a `ready-for-agent` label, and a `/setup-matt-pocock-skills` command. HiveSight and the rest of the skill library use local markdown artifacts by default.

Action:

- Change the default output target to local project docs.
- Remove the `/setup-matt-pocock-skills` instruction.
- Keep issue tracker publication as an optional path only when the user explicitly asks for it or the project clearly uses one.
- Align language with `sdlc-delivery-vertical-slice-planning`: publish local artifacts unless the user explicitly asks for issue tracker tickets.

Acceptance criteria:

- [x] The skill no longer references `/setup-matt-pocock-skills`.
- [x] The skill no longer requires an issue tracker or `ready-for-agent` label by default.
- [x] The skill clearly supports local markdown requirements/spec artifacts.

### SR-005: Embed SDLC Closeout Into Existing Skills

Status: completed 2026-07-30

Problem:

The AI-SDLC observation log drifted because updating it was not built into the skills used during architecture and delivery.

Action:

Add a concise closeout instruction to frequently used SDLC skills:

- `sdlc-delivery-vertical-slice-planning`
- `sdlc-architecture-adr`
- `sdlc-architecture-domain-model`
- `sdlc-architecture-codebase-design`
- `sdlc-delivery-test-automation-reporting`

Suggested closeout language:

At completion, check whether this work changes the project’s traceability chain or AI-SDLC learning record. If it does, update or recommend updating:

- requirements/product spec
- domain model
- ADRs
- vertical slice docs
- acceptance tests
- verification report
- `requirements/ai-sdlc-observations.md`

Acceptance criteria:

- [x] The closeout step is present in the targeted skills and the implementation-oriented delivery skills.
- [x] The closeout step is concise enough not to bloat normal skill use.
- [x] It asks the agent to update the relevant artifact directly when the user has asked for implementation, rather than merely suggesting it at the end.

### SR-006: Define Full-Chain Traceability Audit Skill

Status: completed 2026-07-30

Problem:

Existing traceability ideas focus too narrowly on requirements. The drift that actually occurred crossed the whole chain: vision claims, requirements, domain model traceability, slices, code, tests, verification reports, and AI-SDLC observations.

Action:

Create a reusable skill:

`sdlc-governance-traceability-audit`

Use when auditing a project for drift across SDLC artifacts and implementation evidence.

The skill should inspect:

- vision and goals
- requirements and product specs
- Gherkin/acceptance criteria
- domain model and glossary
- ADRs
- vertical slices/remediation slices
- source code
- API contracts/events
- unit/API/BDD/browser tests
- verification reports
- AI-SDLC observations or learning logs

It should flag:

- claims without implemented/tested evidence
- implemented behaviour not reflected in requirements/docs
- old names or terminology drift
- duplicate or contradictory artifacts
- open questions that have become load-bearing
- deferred promises repeatedly carried forward without decision

Acceptance criteria:

- [x] Skill exists with clear trigger language.
- [x] Skill produces findings ordered by severity.
- [x] Skill distinguishes "fix now", "document as debt", and "needs human decision".
- [x] Skill encourages updating existing artifacts, not just producing a separate report.

### SR-012: Establish A Parking Lot Pattern

Status: completed 2026-07-30

Problem:

During slice planning, grilling, implementation, and review, the team repeatedly parks useful future work. Today those parked items can end up scattered across chat history, Open Questions, Out Of Scope sections, review notes, and slice docs. That makes them easy to forget and hard to review when planning the next slice or remediation tranche.

Action:

Create one canonical project artifact:

`architecture/parking-lot.md`

Use it for important "not now, but not forgotten" items.

Each parked item should include:

- id
- date parked
- source
- area
- short title
- context
- why parked
- revisit trigger
- suggested owner or owning area
- status: `parked`, `promoted`, `closed`, or `superseded`

Suggested initial entries:

- UI-level Gherkin harness.
- Security threat-modelling skill before auth/storage/signed URLs.
- API contract governance skill before Analysis Service integration or public API/event versioning.
- Release readiness skill before deployment target selection.
- Varroa traceability correction before Varroa-specific functional slices.

Skill updates:

- `sdlc-delivery-vertical-slice-planning` should review relevant parked items before defining a new slice.
- Grilling workflows should capture "parked, not forgotten" items explicitly.
- Closeout steps should add newly parked items and update any resolved parked items.
- `sdlc-governance-traceability-audit` should flag stale parked items or parked items whose revisit trigger has occurred.

Policy:

Nothing should be marked merely Out Of Scope if it is important and expected later. It should either:

- become a parked item with a revisit trigger
- become a decision-log/ADR entry if the direction is settled
- become a remediation tracker item if it is a known active problem
- be explicitly closed as "won't do"

Acceptance criteria:

- [x] `architecture/parking-lot.md` exists.
- [x] Parked items use a consistent structure.
- [x] Existing known parked items from the skills review and HiveSight review are captured.
- [x] Slice planning skills instruct agents to review relevant parked items before defining a new slice.
- [x] Closeout guidance instructs agents to add/update parked items.
- [x] Traceability-audit guidance includes stale parked items and triggered revisit conditions.

### SR-007: Add Security Threat-Modelling Skill

Status: parked in `architecture/parking-lot.md` as PARK-0002; create before auth, object storage, signed upload URLs, role security, or production deployment work.

Problem:

Security currently appears only as checklist guidance inside broader architecture skills. The upload-url finding shows that HiveSight already benefits from explicit threat modelling.

Action:

Create:

`sdlc-security-threat-model`

Use when reviewing or designing auth, uploads, signed URLs, access control, privacy, consent, object storage, model/data pipelines, external APIs, or trust boundaries.

Acceptance criteria:

- [ ] Skill covers assets, actors, trust boundaries, abuse cases, mitigations, and test evidence.
- [ ] Skill supports lightweight threat modelling suitable for early-stage projects.

### SR-008: Add Persistence Design Skill

Status: completed 2026-07-30

Problem:

No current skill forces a deliberate transition from in-memory store to real persistence. This gap contributed to `dev_store.py` becoming the de facto domain owner.

Action:

Create:

`sdlc-architecture-persistence-design`

Use when choosing or designing database/storage persistence, schema boundaries, migrations, repositories, transaction boundaries, audit/history, and retention.

Acceptance criteria:

- [x] Skill helps decide what belongs in schema, repository, workflow, and domain policy.
- [x] Skill includes migration and test strategy guidance.
- [x] Skill addresses traceability/audit data explicitly.

### SR-009: Add API Contract Governance Skill

Status: parked in `architecture/parking-lot.md` as PARK-0003; create before Analysis Service integration or public API/event versioning work.

Problem:

The repo has contracts, events, and typed clients, but no skill governs versioning, compatibility, or contract drift.

Action:

Create:

`sdlc-contract-api-governance`

Use when changing REST APIs, event schemas, shared contracts, generated clients, versioning rules, compatibility expectations, or deprecation policy.

Acceptance criteria:

- [ ] Skill covers backward compatibility, schema evolution, versioning, contract tests, and consumer impact.
- [ ] Skill encourages explicit changelog or ADR entries when contracts change materially.

### SR-010: Add Release And Operations Readiness Skill

Status: parked in `architecture/parking-lot.md` as PARK-0004; create once HiveSight has a real deployment target.

Problem:

The library has observability guidance, but not the larger release/operations loop.

Action:

Create:

`sdlc-operations-release-readiness`

Use when preparing deployment, release notes, rollout/rollback, environment config, smoke tests, incident response, and production readiness.

Acceptance criteria:

- [ ] Skill covers release gates, rollback, smoke tests, monitoring, runbooks, and incident follow-up.
- [ ] Skill can be deferred until HiveSight has a real deployment target.

### SR-011: Add Skills Library Review Skill

Status: completed 2026-07-30

Problem:

The skill library itself drifted. A periodic skill-library review would catch stale indexes, broken references, naming drift, project-specific leakage, duplicate scope, and missing metadata.

Action:

Create:

`sdlc-skills-library-review`

Use when auditing or maintaining the personal skills library.

Acceptance criteria:

- [x] Skill checks every skill folder against the index.
- [x] Skill checks cross-references resolve.
- [x] Skill checks generic skills do not contain project-specific defaults.
- [x] Skill checks descriptions are trigger-accurate.
- [x] Skill checks `agents/openai.yaml` metadata if present.

## Recommended Implementation Order

1. SR-001: Remove project-specific defaults from generic skills.
2. SR-002: Create `hivesight-project-delivery-context`.
3. SR-003: Update `SKILLS_INDEX.md`.
4. SR-004: Repair `sdlc-requirements-to-spec`.
5. SR-005: Embed closeout steps in existing high-use SDLC skills.
6. SR-012: Establish `architecture/parking-lot.md` and skill guidance for parked items.
7. SR-006: Create `sdlc-governance-traceability-audit`.
8. SR-008: Create `sdlc-architecture-persistence-design`.
9. SR-011: Create `sdlc-skills-library-review`.
10. Defer SR-007, SR-009, and SR-010 unless their trigger conditions arrive sooner.

## Verification Plan

Implementation verification completed on 2026-07-30:

- Skill validator passed for every immediate skill folder under `/Users/calumnobles/.agents/skills`.
- Stale-name scan found no `BeehiveMonitor`, `setup-matt-pocock-skills`, `ready-for-agent`, dangling `code-review`, `HiveSight-style`, or unresolved placeholder markers.
- Generic `sdlc-*` skills no longer contain HiveSight-specific project defaults.
- `SKILLS_INDEX.md` lists the active skill folders and the deferred future-skill gaps.
- `architecture/parking-lot.md` captures deferred-but-important work with revisit triggers.

## Out Of Scope

- Publishing skills to a remote repository.
- Creating plugin packaging around the skills.
- Rewriting every existing skill.
- Adding heavyweight process documentation to every skill.
- Solving HiveSight architecture remediation directly.

## Open Questions

- Resolved: create `hivesight-project-delivery-context` immediately.
- Resolved: create `sdlc-governance-traceability-audit` in this remediation pass.
- Resolved: do not implement UI-level Gherkin now; park it with an explicit revisit trigger.
