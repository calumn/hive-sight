# Requirements

This document captures early candidate requirements. Requirement IDs are provisional until the first baseline.

Detailed AI model, dataset, training, evaluation, and release-gate requirements are captured separately in `model-requirements.md`.

Version one assumes one registered User, one default Workspace created at registration, one owner Workspace Membership, and that User acting as the primary Beekeeper. Multi-user collaboration, invitations, advisor access, and organisation-level permissions are deferred unless explicitly brought into scope.

## Functional Requirements

### FR-023 User Registration And Default Workspace

The system shall allow a User to register and shall create a default Workspace with an owner Workspace Membership for that User.

Rationale: A User needs a login identity before upload and analysis can be authorized, while the Workspace remains the ownership boundary for apiaries, hives, inspections, photos, and data-use terms.

Version: V1.

### FR-024 Workspace Membership

The system shall represent the relationship between a User and a Workspace as a Workspace Membership.

Rationale: Version one only needs one owner membership, but the model should not hard-code a permanent one-user-one-workspace assumption.

Version: V1 with only the `owner` role; additional roles and invitations are deferred.

### FR-001 Apiary Management

The system shall allow a Beekeeper to define an apiary within a Workspace.

Rationale: Photos and inspections need to be organised by Workspace-owned apiary location or grouping.

### FR-002 Hive Management

The system shall allow a Beekeeper to define hives within an apiary.

Rationale: Varroa assessment is meaningful at hive level, not only at Workspace or apiary level.

### FR-003 Inspections

The system shall allow a Beekeeper to create an inspection for an individual hive.

Rationale: Photos, observations, and Varroa analysis need to be associated with a specific inspection.

### FR-004 Photo Association

The system shall allow an authenticated User acting as the primary Beekeeper to associate one or more inspection photos with a hive inspection only when the User has an active Workspace Membership and the Workspace has an accepted Workspace Data Use Agreement.

Rationale: A person must register, log in, be authorized for the Workspace, and accept the data-use terms before inspection photos can be uploaded. A single frame may have multiple photos, and one inspection may cover multiple frames.

### FR-005 Multiple Photos Per Frame

The system should support optional frame labels so multiple photos can be marked as belonging to the same frame without requiring heavy frame management in version one.

Rationale: Varroa detection may benefit from additional image coverage, but the first version should avoid slowing the product with complex frame modelling.

### FR-006 Bee Counting

The system shall estimate the number of complete visible bees in each submitted photo and report partial visible bees separately where possible.

Rationale: Complete visible bee count is needed for the headline Varroa estimate. Partial bees are useful evidence but should not silently distort the denominator.

### FR-007 Varroa Detection

The system shall detect likely visible Varroa mites on bees in submitted photos.

Rationale: Varroa detection is the core purpose of the system.

### FR-008 Infection-Rate Estimate

When the required model, coverage, and sampling evidence exists, the system shall calculate a stated photo-visible Varroa estimate as likely Varroa detections associated with eligible complete visible bees per 100 eligible complete visible bees in a declared, reconciled photographed-frame population. A sampled result shall identify its Varroa Sampling Plan and uncertainty; the system shall not aggregate potentially overlapping photos of the same frame into one rate without reconciliation.

Rationale: The user needs a summary measure that can support decision-making without implying a whole-hive rate or hiding the uncertainty introduced by partial visual evidence and sampling.

### FR-009 Result Review

The system should present image-level and inspection-level analysis results in a way that allows the user to understand what was counted or detected.

Rationale: AI image analysis requires transparency to support user trust and correction.

### FR-010 Tagged Photo Output

The system shall present a tagged photo for each analysed inspection photo showing likely Varroa detections on bees.

Rationale: The user needs visual evidence behind the estimate to judge whether the model appears accurate.

### FR-011 Optional Bee Detection Overlay

The system should allow the user to view other detected bees in the image in addition to likely infected bees.

Rationale: Showing the denominator visually gives the user an empirical sense of how the bee count was derived.

### FR-012 Human Correction Loop

The system shall allow a user to mark a likely Varroa tag as incorrect and mark a missed likely Varroa location.

Rationale: Lightweight corrections provide trust, reviewability, and future model-evaluation evidence without requiring a full annotation studio.

### FR-013 Photo And Annotation Storage

The system shall store original photos, analysis results, and reusable annotation data.

Rationale: Original images and structured annotations are needed for auditability, re-rendering tagged images, and later model evaluation.

### FR-025 Advisor Treatment Recommendation Intake

When HiveSight requests treatment guidance from HiveSight Advisor, the system shall be able to store the returned Treatment Recommendation as an advisory record linked to the Workspace, Apiary, Hive, source Inspection or Varroa evidence context, recommendation date/time, Advisor contract version, and Advisor provenance.

Rationale: A recommendation must be traceable to the hive, evidence, and Advisor response that produced it, without pretending that advice has already been accepted or applied.

Version: Deferred until HiveSight Advisor integration.

### FR-026 Treatment Recommendation Decision

The system shall let the Beekeeper accept, decline, or leave pending a stored Treatment Recommendation. The decision shall record actor, timestamp, decision state, and optional notes. Declining a recommendation shall preserve the original recommendation for audit rather than deleting or overwriting it.

Rationale: The Beekeeper remains responsible for deciding whether to act on advice, and HiveSight needs to distinguish "Advisor suggested" from "beekeeper accepted".

Version: Deferred until HiveSight Advisor integration.

### FR-027 Hive Treatment Course

When a Beekeeper accepts a Treatment Recommendation or manually records treatment activity, the system shall create or update a beekeeper-owned Hive Treatment Course linked to one Hive. A Treatment Recommendation shall not itself become the treatment course; it may be the provenance source for a separate course.

Rationale: Keeping the advisory suggestion separate from the beekeeper-owned treatment course preserves responsibility, auditability, and the ability to record treatments that were not Advisor-recommended.

Version: Deferred until treatment history implementation.

### FR-028 Treatment Applications

A Hive Treatment Course shall support one or more dated Treatment Applications, each representing one application, dose, or step in the treatment schedule. The course shall support single-step and multi-step schedules without forcing every treatment into one event.

Rationale: Some treatments are applied once, while others require a sequence; HiveSight needs enough structure to record what actually happened.

Version: Deferred until treatment history implementation.

### FR-029 Treatment Outcome And Follow-Up Evidence

The system shall allow a Beekeeper to record a Treatment Outcome for a Hive Treatment Course and link later inspection evidence where relevant, without rewriting the original Treatment Recommendation or the originally planned course.

Rationale: Treatment effectiveness should be reviewable against later evidence, while preserving the history of what was advised, accepted, planned, and actually done.

Version: Deferred until treatment follow-up implementation.

### FR-030 Treatment Evidence Chain

The system shall preserve a Treatment Evidence Chain from the Varroa evidence or Varroa Assessment context that triggered an Advisor request, through the request payload sent to HiveSight Advisor, the returned Treatment Recommendation, the Beekeeper's decision, any resulting Hive Treatment Course, Treatment Applications, and Treatment Outcome.

Rationale: Future review, audit, and learning need to know which Varroa count or assessment context led to which advice, what the Beekeeper actually did, and what later evidence suggested about the result.

Version: Deferred until HiveSight Advisor integration and treatment history implementation.

### FR-031 Advisor Learning Dataset Governance

The system may later expose anonymised or governed Treatment Evidence Chain records for HiveSight Advisor learning, retrieval, evaluation, or quality review, but only through an explicit permitted-use policy, data minimisation rules, and provenance-preserving export or integration contract. HiveSight shall not automatically use identifiable hive, apiary, Beekeeper, or Workspace treatment history as Advisor RAG material without that policy.

Rationale: Treatment recommendation, application, and outcome history may become valuable evidence for improving Advisor guidance, but it is sensitive operational history and must be governed separately from product treatment records.

Version: Deferred until Advisor learning governance is designed.

### FR-016 Workspace Data Use Agreement

The system shall require the Workspace owner to accept the Workspace Data Use Agreement before upload and analysis features can be used.

Rationale: Version one treats the data-use agreement as a condition of service for analysis features.

### FR-017 Ownership And Access Boundary

The system shall associate apiaries, hives, inspections, inspection photos, analysis results, annotations, corrections, workspace data-use agreements, and data deletion requests with a Workspace boundary, and shall authorize User access through Workspace Membership.

Rationale: Even a lightweight version needs a clear ownership model before storage, upload, and review workflows are implemented.

### FR-018 Image Upload Constraints

The system shall enforce configurable image format and upload size constraints.

Rationale: Exact limits can change, but architecture and user experience must handle accepted formats, rejected files, and large original photo storage.

### FR-019 Data Use Agreement Traceability

The system shall store the accepted Workspace Data Use Agreement version and status before any inspection photo or user correction becomes eligible for model-improvement workflows.

Rationale: Dataset eligibility must be traceable to the Workspace's accepted data-use terms.

### FR-020 Data Use Withdrawal

The system shall disable new upload and analysis features when a Workspace Data Use Agreement is not accepted or has been withdrawn.

Rationale: Version one requires active accepted data-use terms for service use.

### FR-021 Data Deletion Request Capture

The system should recognise Data Deletion Request as a deferred domain concept for deleting or purging Workspace-held data.

Rationale: Inspection photos and metadata may be personally identifiable or sensitive, and deletion semantics need explicit policy and architecture decisions before production use.

### FR-014 Web UI

The system shall provide a web user interface for the first version.

Rationale: A web UI is the most practical initial interface for rapid development and validation.

### FR-015 Future Mobile Apps

The system should be designed so Android and Apple applications can be added later.

Rationale: Mobile capture is likely valuable during real hive inspections.

### FR-022 Deferred Trial Photo Analysis

The system may later offer a limited guest or trial photo analysis workflow that allows a prospective user to upload a small number of photos without first creating a Workspace.

Rationale: A constrained trial could help prospective users understand the value of tagged Varroa analysis before registering, while preserving version-one focus on authenticated Workspace-based inspection workflows.

Version: Deferred / V2.

Notes:

- The trial workflow is not part of version one.
- Trial use would still require accepted data-use terms before upload and analysis.
- Trial photos should not create long-term inspection history unless the user later creates a Workspace and explicitly saves or imports the result.
- Trial uploads should be constrained by configurable usage limits, such as a small number of images per user, browser, IP address, time window, or other abuse-prevention mechanism.
- Trial photos and results should have explicit retention and deletion rules.
- Trial photos and corrections should be excluded from model-improvement workflows unless a future policy explicitly allows them with appropriate agreement and review.

## Non-Functional Requirements

### NFR-001 Traceability

The project shall maintain traceability from stakeholder needs to requirements, design decisions, implementation, tests, and production evidence.

Rationale: The project is also an AI-SDLC study.

### NFR-002 Explainability

The system should communicate uncertainty, confidence, and limitations for AI-generated Varroa analysis.

Rationale: Incorrect Varroa assessment could mislead treatment decisions.

### NFR-005 Claim Boundary

The system shall present Varroa analysis as an AI-assisted visual estimate, not as a diagnosis, treatment recommendation, or official infestation measurement.

Rationale: Version one is decision support and model-learning evidence, not a validated diagnostic product.

### NFR-003 Data Organisation

The system shall preserve relationships between Users, Workspace Memberships, Workspaces, apiaries, hives, inspections, frame labels, inspection photos, analysis results, annotations, user corrections, and model-governance records.

Rationale: Historical inspection context is central to the product.

### NFR-004 Extensibility

The system should separate core data and analysis capabilities from UI-specific implementation choices.

Rationale: Future web, Android, and Apple clients should be able to share the same underlying data and analysis services.

### NFR-007 Privacy Gap Traceability

The project shall explicitly track unresolved policy decisions around Workspace Data Use Agreement withdrawal, prior uploads, existing dataset versions, already-trained model artifacts, and Data Deletion Requests.

Rationale: Uploaded photos and metadata may be personally identifiable or sensitive; the project should not hide this risk behind generic consent language.

### NFR-006 Upload Configurability

Accepted image formats, upload size limits, and storage limits should be configurable rather than hard-coded.

Rationale: The project should be able to adjust limits as real inspection photos and hosting constraints become clearer.

## Open Requirements Questions

- Should infection rate be calculated per image, per frame, per inspection, or all three?
- What exact registration, default workspace naming, and owner membership creation flow should version one use?
- What future Workspace Membership roles and invitation lifecycle should be supported after version one?
- What wording should be used consistently for "mites per 100 complete visible bees"?
- What exact image formats and maximum upload sizes should be supported initially?
- What level of model confidence is needed before a detection is shown to the user?
- Should the system support offline capture later?
- Should the system support a deferred guest trial workflow with a limited number of photo analyses before Workspace registration?
- What limits, abuse prevention, consent, retention, deletion, and model-improvement eligibility rules would apply to guest trial photos?
- What field evidence is needed to validate the Varroa detection approach?
- What should the Workspace Data Use Agreement say, and how should accepted terms versions be tracked?
- How should Workspace Data Use Agreement withdrawal affect previously uploaded photos, existing dataset versions, and already-trained model artifacts?
- What Data Deletion Request or purge workflow is required before production use?
- Are uploaded photos and inspection metadata legally or operationally personally identifiable or sensitive in the target markets?
