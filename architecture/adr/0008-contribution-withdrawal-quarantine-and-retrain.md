# ADR 0008: Contribution Withdrawal Quarantine And Retrain

Status: accepted

## Context

HiveSight accepts contributor-controlled training evidence. A Contributor Contribution Permission is distinct from the Workspace Data Use Agreement: the former belongs to the identified contributor, while the latter governs workspace evidence. A contributor may later withdraw permission for their contribution after it has entered Dataset Versions, Training Runs, Model Candidates, or an approved Model Version. Merely blocking future uploads or exports would leave HiveSight relying on a withdrawn contribution through already-created model artifacts.

## Decision

HiveSight adopts a strict Contribution Withdrawal policy.

1. Withdraw affected Dataset Items immediately from future exports, Dataset Versions, Training Runs, Benchmark Evaluations, and promotion.
2. Preserve immutable historical manifests and run records only for audit and provenance.
3. Quarantine affected Dataset Versions and model artifacts. Affected Model Candidates cannot be promoted or used for new analysis. An affected user-facing Model Version cannot remain in use.
4. Train and evaluate a replacement from a new Dataset Version that excludes the withdrawn contribution before model use resumes.
5. Process source images and annotations through the applicable deletion or erasure workflow, subject to any documented retention requirement.
6. Record each contributor's permission against one named, immutable Contribution Bundle and retain that bundle reference on every affected Dataset Item.
7. In the first release, withdrawal applies to the complete Contribution Bundle. A contributor needs separate bundles before acceptance when they need finer withdrawal boundaries.
8. Contributors use a registered HiveSight identity to view their own bundles and withdraw permission. That identity does not grant Workspace Membership or dataset/model-governance capability.
9. Contributor access is limited to explicitly assigned annotation tasks and Contribution Bundles, never the wider Workspace, unassigned inspections, or other contributors' evidence.
10. A Dataset Curator creates Contribution Bundles and assigns tasks. Workspace ownership permits offering the owner's evidence for curation, not dataset-governance authority.
11. Before acceptance, a contributor sees only a non-sensitive bundle summary and applicable terms. Assigned images and annotation tasks become visible only after explicit acceptance of that named bundle and terms version.
12. A material change to contributor terms requires fresh acceptance before the bundle can appear in a new Dataset Version, Training Run, Benchmark Evaluation, or promotion. Historical lineage remains available for audit.
13. A contributor may request deletion of their own Contribution Bundle through their registered identity. Starting the request automatically withdraws model-use permission; the deletion request then tracks subsequent erasure and retention handling.
14. Contributors can view a read-only Contribution Usage Record for each bundle, showing accepted terms, permission/deletion status, and linked Dataset Versions, Training Runs, and model-artifact outcomes without exposing other contributors' evidence or the wider Workspace.
15. Contributors may use a pseudonymous HiveSight identity. HiveSight retains only the minimum contact/authentication data needed for access and requests; provenance and curator-facing views use the internal id and selected pseudonym, not a required real name.
16. Withdrawal or a contributor deletion request immediately revokes access to every unfinished task in the bundle. Retain only the minimal audit record needed to explain the request and affected lineage.
17. Re-acceptance after withdrawal creates a new permission record for future use only. It never automatically unquarantines prior Dataset Versions or model artifacts.
18. Public/open source evidence relies on its own Source Rights Record, not a fictional Contributor Contribution Permission. Source licence provenance and imported annotation provenance remain separate.
19. A Dataset Curator explicitly approves a public/open Source Rights Record before a related image can become a Dataset Item.

The first contributor terms offer model development and evaluation only. User-facing deployment, sharing/publication, and commercial use require separate explicit opt-in.

User-facing deployment, sharing/publication, and commercial release each hard-block unless every Dataset Item used for training permits the relevant scope; every release record includes a scope-compatibility report.

Source Rights Invalidation is governed separately by ADR 0009 because it has the same operational response but a distinct cause.

This policy is the HiveSight product default. It does not replace project-specific legal advice on lawful basis, erasure, contract terms, or retention obligations.

## Consequences

- Dataset lineage must identify all Dataset Versions, Training Runs, Model Candidates, and Model Versions affected by a withdrawn Dataset Item.
- Quarantine status is an operational state, not deletion: historical evidence remains auditable but cannot support future use.
- Model training must be reproducible from frozen Dataset Version manifests so a clean replacement can be created.
- Contribution withdrawal, deletion, model retirement, and replacement-training flows require dedicated workflows and acceptance coverage before external contributor data is used in a real model.
- The consent screen and contributor terms must state this policy in clear language and make withdrawal at least as easy as contribution.
