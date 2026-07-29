# Requirements Skill Map

## Purpose

This document defines the skills needed during the requirements phase of the HiveSight project.

The project has two linked goals:

1. Build a Varroa-focused beehive inspection and monitoring system.
2. Study how AI affects the software development lifecycle, from requirements gathering through production operation.

The requirements phase should produce both product requirements and evidence about how AI contributed to discovering, structuring, validating, and managing those requirements.

## Requirements Phase Outcomes

By the end of the requirements phase, the project should have:

- A clear product vision.
- A stakeholder map.
- A set of stakeholder needs.
- Functional requirements.
- Non-functional requirements.
- Constraints and assumptions.
- Acceptance criteria.
- A requirements traceability structure.
- A decision log.
- A record of AI involvement in the requirements process.

## Skill 1: Requirements Interviewer

Purpose: Elicit real needs from stakeholders and separate problems, goals, constraints, and proposed solutions.

Activities:

- Prepare interview questions.
- Identify what decision or operational problem each stakeholder is trying to solve.
- Ask follow-up questions when answers are vague.
- Distinguish stated wants from underlying needs.
- Capture context, assumptions, constraints, and unresolved questions.
- Summarise interviews for stakeholder confirmation.

Outputs:

- Interview notes.
- Confirmed stakeholder needs.
- Open questions.
- Assumptions.
- Candidate requirements.

## Skill 2: Stakeholder Mapper

Purpose: Identify who affects, uses, maintains, funds, regulates, or benefits from the system.

Activities:

- Identify stakeholder groups.
- Describe each stakeholder's goals and concerns.
- Map stakeholders to use cases and decisions.
- Identify conflicts between stakeholder needs.
- Identify missing voices.

Outputs:

- Stakeholder list.
- Stakeholder map.
- Personas or role descriptions.
- Stakeholder concerns and success criteria.

## Skill 3: Requirement Writer

Purpose: Convert raw needs into clear, atomic, testable requirements.

Activities:

- Assign each requirement a unique ID.
- Write one requirement per statement.
- Avoid ambiguous terms unless quantified.
- Separate functional requirements from non-functional requirements.
- Record source, priority, rationale, and verification method.
- Avoid embedding design choices unless they are genuine constraints.

Suggested requirement format:

```text
ID:
Title:
Statement:
Type:
Source:
Priority:
Rationale:
Verification method:
Acceptance criteria:
Status:
```

## Skill 4: Acceptance Criteria Designer

Purpose: Define what must be true for a requirement to be considered satisfied.

Activities:

- Translate requirements into observable outcomes.
- Define measurable thresholds where possible.
- Include normal, edge, and failure conditions.
- Connect acceptance criteria to future tests.
- Identify criteria that need field validation.

Outputs:

- Acceptance criteria.
- Testable scenarios.
- Verification notes.
- Field validation needs.

## Skill 5: Traceability Manager

Purpose: Maintain links between needs, requirements, design, implementation, tests, and production evidence.

Activities:

- Link each requirement to a stakeholder need or project objective.
- Link each requirement to acceptance criteria.
- Later link each requirement to architecture, code, tests, and production monitoring.
- Identify orphan requirements with no source.
- Identify stakeholder needs with no requirement coverage.
- Support impact analysis when requirements change.

Default traceability model:

```text
Project Objective
-> Stakeholder Need
-> Requirement
-> Acceptance Criteria
-> Design Decision
-> Implementation
-> Test
-> Production Evidence
```

## Skill 6: Requirements Reviewer

Purpose: Check requirement quality before the project treats requirements as a baseline.

Review requirements for:

- Ambiguity.
- Duplicates.
- Compound statements.
- Missing source.
- Missing acceptance criteria.
- Missing verification method.
- Hidden design assumptions.
- Conflicts with other requirements.
- Unrealistic or untestable claims.

## Skill 7: AI-SDLC Observer

Purpose: Capture evidence about how AI affects the requirements phase.

Activities:

- Record where AI was used.
- Record what AI generated.
- Record what humans accepted, rejected, or corrected.
- Identify AI assumptions.
- Identify hallucinations or unsupported claims.
- Track time saved or new work introduced.
- Capture lessons for later SDLC phases.

## Initial HiveSight Requirement Categories

- Apiary management.
- Hive management.
- Inspection events.
- Frame photo upload.
- Multiple photos per frame.
- Bee counting.
- Varroa detection.
- Infection-rate estimation.
- AI confidence and explainability.
- Web UI.
- Future mobile applications.
- Data storage.
- Traceability.
- Production evidence capture.

## Open Questions

- Who is the primary user for the first version?
- Is the first version a prototype, field trial, or production-ready system?
- How should the system group multiple photos of the same frame?
- Should the user be able to manually correct bee counts or Varroa detections?
- What image quality standards are needed?
- What counts as enough evidence that Varroa detection is useful?
- What counts as success for the product?
- What counts as success for the AI-SDLC experiment?
