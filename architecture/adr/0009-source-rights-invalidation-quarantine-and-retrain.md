# ADR 0009: Source Rights Invalidation Quarantine And Retrain

Status: accepted

## Context

Public, open, imported, or otherwise externally sourced evidence may rely on a Source Rights Record rather than a Contributor Contribution Permission. A licence or other rights basis can later be found invalid, revoked, or incompatible with HiveSight's intended use. Treating this as a contributor withdrawal would misstate the cause, but leaving dependent model artifacts available would retain the same practical risk.

## Decision

When a Source Rights Record is invalidated, HiveSight shall:

1. Exclude every affected Dataset Item from future exports, Dataset Versions, Training Runs, Benchmark Evaluations, and promotion.
2. Preserve immutable historical manifests and run records for audit and provenance, recording `source_rights_invalidation` as the cause.
3. Quarantine dependent Dataset Versions, Model Candidates, and Model Versions so they cannot support new analysis or promotion.
4. Train and evaluate any replacement from a new Dataset Version that excludes the invalidated evidence before future model use resumes.
5. Follow the applicable removal, attribution, or retention obligation for the source rights basis.

Public/open evidence is treated as local research and model development evidence only unless the approved Source Rights Record explicitly permits a broader use scope.

## Consequences

- Source Rights Records require curator review before public/open images become Dataset Items.
- Required attribution flows into relevant Dataset Versions, exports, evaluation reports, and released model documentation.
- Source Rights Records and Contributor Contribution Permissions use explicit, closed Permitted Use Scopes; an unlisted use is not permitted.
- Dataset lineage must identify every dependent Dataset Version, Training Run, Model Candidate, and Model Version.
- This operational response is intentionally equivalent to ADR 0008's quarantine-and-retrain approach, while preserving the distinct legal and provenance reason.
- Formal licence compatibility for sharing, publication, commercial use, model-output obligations, and user-facing deployment remains parked in PARK-0035.
