# Vertical Slice 0004: Annotation Review Decision

## Purpose

Prove that HiveSight can route existing Annotation evidence into a human review workflow, record a Review Decision against one Annotation, and show that review state through the Core API and Web UI without turning the reviewed evidence into training, validation, or benchmark data.

This slice closes the admin/reviewer gap deliberately left open by Vertical Slice 0003. It establishes the first thin internal review capability needed before later User Correction workflows and model-improvement pipelines can safely consume reviewed evidence.

Slice 0005 is expected to switch focus toward recognition model, training, dataset, and evaluation concerns. Slice 0004 prepares for that by making review decisions explicit and traceable, but it does not implement model training or dataset assignment.

## Source Inputs

- `CONTEXT.md`: Annotation, Review Decision, User Correction, Workspace Data Use Agreement, Dataset Role, Model Version, Dataset Version, Benchmark Evaluation.
- `requirements/product-spec.md`: "Reviewed corrections become eligible for dataset use" and "User photos are not automatically trusted training data" scenarios.
- `requirements/model-requirements.md`: MR-012 Human-Reviewed Ground Truth, MR-013 User Corrections As Review Candidates, MR-014 Correction Review Outcomes, MR-016 Dataset Provenance, MR-017 Dataset Roles, MR-019 Workspace Data Use Agreement Traceability.
- `requirements/decision-log.md`: User Corrections Require Review Before Dataset Use; Workspace Data Use Agreement Required For Upload And Analysis; Service-Oriented Architecture For V1; User, Workspace Membership, And Beekeeper Language.
- `architecture/domain-model.md`: Review Decision entity and rule that review decisions preserve what was reviewed and by whom.
- `architecture/adr/0001-service-oriented-architecture.md`: Core API owns product workflow and authorization; model training and evaluation remain separate from V1 runtime services.
- `architecture/vertical-slice-0003-annotation-evidence-review.md`: first-class bee Annotations and the explicit decision that Slice 4 should bottom out the admin/reviewer workflow.
- `architecture/vertical-slice-0003-5-web-acceptance-test-harness.md`: browser acceptance harness and slice verification report.

## User Path

Given an Inspection Photo has a completed deterministic stub Analysis Result
And that result has first-class bee Annotations
And an internal Reviewer has access to the review workflow
When the Reviewer opens the annotation review view
And records a Review Decision for one Annotation
Then the Core API stores the Review Decision with reviewer, subject, decision, notes, and timestamp
And the reviewed Annotation is shown with its current review state
And the review evidence remains separate from Dataset Role assignment, Dataset Version creation, model training, benchmark evaluation, or model promotion

## Preconditions

- Vertical Slice 0001 is implemented and demoable.
- Vertical Slice 0002 is implemented and demoable.
- Vertical Slice 0003 is implemented and demoable.
- Vertical Slice 0003.5 is implemented and available for browser acceptance and slice verification.
- Development authentication remains represented by the dev-only auth header.
- The Core API already stores or projects first-class Annotation records associated with Workspace, Inspection Photo, and Analysis Result.
- Review is limited to bee Annotations from deterministic stub output.
- The Reviewer capability may be dev/internal-only for this slice.
- The Workspace Data Use Agreement gate still protects photo evidence and annotations. A Review Decision may be recorded only for evidence belonging to a Workspace with an accepted agreement.
- No production auth provider, invitation flow, or full role-management UI is required.

## End-To-End Behaviour

The Beekeeper completes the existing local workflow: accept the Workspace Data Use Agreement, create Apiary/Hive/Inspection records, upload one Inspection Photo, process the deterministic stub Analysis Run, and produce bee Annotation evidence.

An internal Reviewer opens a review-oriented Web UI surface. The surface can be a simple internal panel rather than a polished admin console. It lists or loads the completed Analysis Result and displays the original Inspection Photo with existing Annotation overlays. The Reviewer can select one Annotation and record a Review Decision.

For this slice, supported Review Decision values are:

- `approved`
- `rejected`
- `uncertain`
- `excluded`

The decision is stored as a separate Review Decision record rather than overwriting the original Annotation. The record preserves the subject type, subject id, reviewer id, decision value, optional notes, and created timestamp. The current review state for an Annotation may be projected from the latest Review Decision.

The Core API owns the review workflow and authorization boundary. The Web UI calls the Core API only. The Analysis Service is not touched because model runtime output has already been produced in earlier slices.

The Web UI shows whether an Annotation is unreviewed or reviewed, and displays the latest decision. The reviewer can refresh or revisit the evidence and still see the recorded decision. Review Decisions are append-only records. If a reviewer changes their mind, a later decision supersedes the earlier decision for latest-state projection; previous decisions are not edited or deleted.

Review Decisions created in this slice do not make the Annotation ground truth, do not assign a Dataset Role, do not create a Dataset Version, and do not trigger model training. They create traceable review evidence that Slice 0005 can use when the project turns toward recognition model and training work.

## Layers Touched

- Web UI: Adds a minimal internal annotation review surface that displays existing evidence, lets a Reviewer select one Annotation, submit a Review Decision and optional notes, and see reviewed/unreviewed state.
- Core API: Adds Review Decision data shape, store operations, internal reviewer authorization seam, review routes, and latest review-state projection for Annotation evidence.
- Analysis Service: Not touched. Existing deterministic Annotations remain the review subjects.
- Storage: Reuses original Inspection Photo viewing and existing in-memory/dev metadata storage unless durable persistence is chosen separately.
- Queue or async boundary: Not touched.
- Contracts: Adds Review Decision request/response contracts and extends annotation evidence projection with latest review state.
- Observability: Adds test-visible evidence for review creation, reviewer identity, blocked unauthorized review attempts, and protected separation from dataset/model-training use.
- Verification reporting: Existing `pnpm verify:slice` should include the new Core API, API-level BDD, Web type-check, and browser acceptance checks.

## Test Seams

- Seam: Review Decision domain/store
- Behaviour verified: a Review Decision can be recorded against an Annotation with reviewer id, subject type, subject id, decision value, optional notes, and timestamp without mutating the original Annotation.
- Test style: Core API workflow/unit tests with deterministic IDs and deterministic clock.

- Seam: Core API reviewer authorization
- Behaviour verified: an internal Reviewer can submit a Review Decision; a normal Beekeeper/User without reviewer capability cannot submit one; cross-Workspace review attempts are blocked.
- Test style: FastAPI integration tests with dependency overrides and dev-auth headers.

- Seam: Core API review route boundary
- Behaviour verified: valid review requests create a Review Decision; invalid decision values, missing annotations, wrong Workspace, missing Workspace Data Use Agreement, or non-reviewer callers return documented blocked responses.
- Test style: FastAPI route tests through public Core API endpoints.

- Seam: API-level BDD acceptance
- Behaviour verified: a Reviewer approves, rejects, marks uncertain, or excludes a bee Annotation, and the Annotation evidence response shows the latest review state.
- Test style: pytest-bdd feature scenarios aimed at the Core API, not the Web UI.

- Seam: `CoreApiClient`
- Behaviour verified: Web code can submit a Review Decision and parse latest review state on Annotation evidence.
- Test style: TypeScript unit tests with mocked fetch responses.

- Seam: Web UI review surface
- Behaviour verified: a Reviewer can see an unreviewed Annotation, submit a Review Decision with optional notes, and see the updated state in the browser.
- Test style: Playwright browser acceptance test through the existing Slice 0003.5 harness.

## Data Shape

Minimum additions:

- Review Decision: `review_decision_id`, `workspace_id`, `reviewer_id`, `subject_type`, `subject_id`, `decision`, `notes`, `created_at`.
- Review subject type: `annotation`.
- Review decision value: `approved`, `rejected`, `uncertain`, `excluded`.
- Reviewer capability: a dev/internal authorization marker that is separate from the version-one `owner` Workspace Membership role unless a later decision explicitly folds reviewer into membership roles. Workspace ownership alone is not enough to create Review Decisions.
- Annotation evidence projection: existing Annotation fields plus optional `latest_review_decision`.

Minimum API shapes:

- Create Review Decision request: `workspace_id`, `subject_type`, `subject_id`, `decision`, `notes`.
- Create Review Decision response: `review_decision_id`, `workspace_id`, `reviewer_id`, `subject_type`, `subject_id`, `decision`, `notes`, `created_at`.
- Evidence response extension: each Annotation may include `latest_review_decision` with `decision`, `reviewer_id`, `notes`, and `created_at`.
- Blocked response codes: `not_authenticated`, `reviewer_access_required`, `workspace_access_denied`, `data_use_agreement_required`, `annotation_not_found`, `invalid_review_subject`, `invalid_review_decision`.

## Out Of Scope

- Real bee detection, real Varroa detection, confidence calibration, or model artifact loading.
- Beekeeper User Correction creation.
- Reviewing User Corrections.
- Drawing, moving, resizing, deleting, or creating Annotations.
- Bulk review, keyboard labelling, reviewer queues, assignment, sampling, consensus review, double review, adjudication, or audit dashboards.
- Dataset Role assignment such as training, validation, benchmark, or excluded dataset membership.
- Dataset Version creation, dataset export, benchmark evaluation, model training, model promotion, or model registry changes.
- Treating reviewed Annotations as ground truth.
- Automatic use of uploaded photos, Annotations, or Review Decisions for model improvement.
- Production admin identity, production auth provider integration, invitations, multi-user Workspace roles, or a full admin console.
- Durable database persistence if the in-memory/dev store remains sufficient for the slice.
- CI integration beyond the existing local slice verification command.
- UI-level Gherkin. Later Slice 0013 planning parked this as a future option; this slice continues to rely on plain Playwright for browser acceptance.

## Acceptance Criteria

- [ ] A Review Decision can be recorded against one existing bee Annotation from a completed deterministic stub Analysis Result.
- [ ] Review Decisions are stored as separate records and do not overwrite the original Annotation.
- [ ] The Review Decision records `workspace_id`, `reviewer_id`, `subject_type`, `subject_id`, `decision`, optional `notes`, and `created_at`.
- [ ] Supported Slice 4 decision values are `approved`, `rejected`, `uncertain`, and `excluded`.
- [ ] The Core API rejects invalid review subject types and invalid decision values.
- [ ] The Core API rejects review attempts for missing Annotations.
- [ ] The Core API rejects review attempts across Workspace boundaries.
- [ ] The Core API rejects review attempts when the Workspace Data Use Agreement gate is not satisfied.
- [ ] The Core API rejects review attempts from a User without internal reviewer capability.
- [ ] The Core API evidence response projects the latest review state for reviewed Annotations.
- [ ] The Web UI provides a minimal internal annotation review surface.
- [ ] The Web UI lets a Reviewer select an Annotation, choose a Review Decision, enter optional notes, submit the decision, and see the updated review state.
- [ ] The Web UI distinguishes unreviewed and reviewed Annotations without presenting reviewed evidence as training data or ground truth.
- [ ] API-level BDD scenarios cover at least one successful Review Decision and one blocked unauthorized review attempt.
- [ ] Browser acceptance covers the reviewer happy path through the existing Playwright harness.
- [ ] `pnpm verify:slice` includes the Slice 4 checks in the generated verification report.
- [ ] No Dataset Role, Dataset Version, benchmark, model training, or model promotion behaviour is implemented as part of this slice.
- [ ] The implementation preserves the target architecture: Web UI calls Core API; Core API owns review workflow and authorization; Analysis Service remains private and unchanged.

## Decisions From Slice Review

- The Reviewer capability is represented as a separate internal/dev capability in Slice 4, not as a real Workspace Membership `reviewer` role.
- The same dev User may review evidence from their own Workspace, but only when the internal reviewer capability is present. Workspace ownership alone is not enough.
- Review Decisions are append-only. The evidence view projects the latest Review Decision as the current review state.
- Review state is derived from Review Decision records. Slice 4 does not store a separate `review_status` field on Annotation records.
- Slice 4 supports Review Decision values `approved`, `rejected`, `uncertain`, and `excluded`.
- `approved` means the reviewer accepts the Annotation as correct for its current annotation type. It does not mean the Annotation is training-approved, benchmark-approved, or trusted ground truth.
- `rejected` means the Annotation is wrong for its current annotation type.
- `uncertain` means the reviewer cannot confidently decide.
- `excluded` means the evidence should not be used for review/model-improvement purposes, for example because of poor image quality, unsuitable subject, privacy concern, or ambiguous context. It does not assign a Dataset Role.
- Review Decisions may be recorded for both `complete_visible_bee` and `partial_visible_bee` Annotations.
- Review Decision creation requires an accepted Workspace Data Use Agreement.
- The Review Decision API includes `subject_type`, but Slice 4 accepts only `annotation`.
- The reviewer can select any visible Annotation in the evidence view and record a Review Decision for it.
- Slice 4 does not introduce a review queue. Review controls are added to the existing evidence view.
- Review controls are hidden unless the current User has reviewer capability.
- Optional review notes are supported with a maximum length of 500 characters.
- The API stores `reviewer_id`; the UI does not need to build a proper reviewer identity display in this slice.
- The reviewer UI includes a quiet internal cue that Review Decisions do not assign dataset use, for example `Review evidence only. Dataset use is not assigned in this slice.`
- Browser acceptance covers the reviewer happy path for now. Unauthorized review is covered by API and API-level BDD tests.
- Slice 4 continues with plain Playwright browser acceptance. UI-level Gherkin remains a follow-on testing slice soon after Slice 4.
- Slice 4 documentation should be reviewed before implementation begins.

## Open Questions

- None for implementation of this slice. UI-level Gherkin, production reviewer identity, real Workspace reviewer roles, review queues, User Correction review, Dataset Role assignment, and model training should be treated as follow-on slice decisions rather than blockers.
