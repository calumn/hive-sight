# HiveSight Product Spec

## Problem Statement

HiveSight is the product name, with hive-sight.com as the registered domain.

Hobbyist and small-scale beekeepers need a practical way to use inspection photos to assess possible Varroa mite presence in their hives. Raw photos are hard to evaluate consistently, and a simple count alone is not enough unless the beekeeper can see the evidence behind it.

The product should help a Beekeeper organise Workspace-owned apiaries, hives, inspections, and inspection photos, then provide an AI-assisted estimate of likely Varroa presence from uploaded images. It must avoid overstating the result as a diagnosis, treatment recommendation, or official infestation measurement.

The project also needs to document how AI affects the software development lifecycle, so requirements, decisions, implementation, tests, and production evidence should remain traceable.

## Solution

Build a web-first inspection support system for hobbyist and small-scale beekeepers.

The User registers, receives a default Workspace, and receives an owner Workspace Membership. Acting as the primary Beekeeper, that User creates an apiary, creates hives within that apiary, creates an inspection for a hive, uploads one or more inspection photos, and reviews analysis results. The system estimates complete visible bees, tracks partial visible bees separately, detects likely Varroa mites on or near bees, calculates likely mites per 100 complete visible bees, and presents tagged photos showing the evidence behind the estimate.

The Beekeeper can optionally view all detected bees and can lightly correct results by marking false Varroa detections or missed likely Varroa locations. The system stores the original inspection photo, structured annotation data, analysis results, and user corrections so tagged photos can be re-rendered and model accuracy can be evaluated later.

Version one assumes one registered User, one default Workspace, one owner Workspace Membership, and that User acting as the primary Beekeeper. Collaboration, invitations, advisor access, workspace switching, and organisation-level permissions are deferred.

A future acquisition workflow may allow a prospective user to submit a small number of trial photos before creating a Workspace. This is deferred from version one because it requires additional decisions around data-use terms, abuse prevention, rate limits, retention, deletion, and model-improvement eligibility.

## Gherkin Scenarios

Feature: Apiary and hive setup

  Scenario: User registers and receives a default workspace
    Given a prospective Beekeeper has not registered
    When the person registers as a User
    Then the system creates a default Workspace
    And the system creates an owner Workspace Membership for that User
    And the User can act as the primary Beekeeper in that Workspace

  Scenario: Beekeeper accepts the workspace data-use agreement
    Given a User has an owner Workspace Membership
    When the User accepts the current Workspace Data Use Agreement for the Workspace
    Then upload and analysis features are enabled for that Workspace
    And the accepted terms version is recorded

  Scenario: Beekeeper creates an apiary
    Given a User is acting as the primary Beekeeper in an active Workspace
    When the beekeeper creates an apiary with a name
    Then the apiary is saved
    And the apiary belongs to the Workspace
    And the Beekeeper can use the apiary to organise hives by real-world location or grouping

  Scenario: Beekeeper creates a hive within an apiary
    Given a User acting as the primary Beekeeper has created an apiary
    When the beekeeper creates a hive within that apiary
    Then the hive is saved under the selected apiary
    And future inspections can be associated with that hive

Feature: Hive inspection photo capture

  Scenario: Beekeeper creates an inspection for a hive
    Given a Beekeeper has an apiary with at least one hive
    When the Beekeeper creates an inspection for a selected hive
    Then the inspection is associated with that hive
    And the inspection can hold photos and analysis results

  Scenario: Beekeeper uploads multiple photos to an inspection
    Given a person has registered as a User
    And the User is logged in
    And the User has an active owner Workspace Membership
    And the User is acting as the primary Beekeeper in that Workspace
    And the Beekeeper has created an inspection
    And the Workspace has an accepted Workspace Data Use Agreement
    When the Beekeeper uploads one or more inspection photos
    Then each photo is associated with the inspection
    And the original uploaded photo is preserved for later review

  Scenario: Beekeeper optionally labels photos from the same frame
    Given a Beekeeper has uploaded multiple photos to an inspection
    When the Beekeeper labels two or more photos with the same frame label
    Then the system records that those photos may represent the same frame
    And the system does not require full frame inventory management

Feature: Varroa image analysis

  Scenario: System estimates visible bees in each photo
    Given an inspection photo has been uploaded
    When the system analyses the photo
    Then the system estimates the number of complete visible bees in the photo
    And the system tracks partial visible bees separately where possible
    And the bee count is stored with the photo analysis result

  Scenario: System detects likely Varroa mites on bees
    Given an inspection photo has been uploaded
    When the system analyses the photo
    Then the system identifies likely visible Varroa mites on or near bees
    And the system associates each likely Varroa detection with a complete bee, partial bee, or unassociated visible Varroa state where possible
    And the likely Varroa count is stored with the photo analysis result

  Scenario: System calculates mites per 100 complete visible bees
    Given an inspection has analysed photos
    And the system has estimated complete visible bees
    And the system has counted likely Varroa detections
    When the system presents the inspection result
    Then the system shows likely Varroa detections associated with complete visible bees per 100 estimated complete visible bees
    And the system states that the estimate is based only on bees visible in the uploaded photos

Feature: Tagged photo review

  Scenario: Beekeeper reviews likely infected bees on a tagged photo
    Given an inspection photo has analysis results
    When the beekeeper opens the analysed photo
    Then the system shows a tagged-up version of the photo
    And likely Varroa detections are visually marked on the relevant bees or image regions

  Scenario: Beekeeper optionally views all detected bees
    Given an analysed photo has detected bee annotations
    When the beekeeper enables the detected-bees overlay
    Then the system shows the other bees it identified
    And the beekeeper can inspect how the visible bee count was derived

  Scenario: Beekeeper marks a Varroa tag as incorrect
    Given an analysed photo shows a likely Varroa marker
    When the beekeeper marks that marker as incorrect
    Then the correction is stored with the photo annotation data
    And the correction can be used as evidence for later model evaluation

  Scenario: Beekeeper marks a missed likely Varroa location
    Given an analysed photo does not mark a likely Varroa location noticed by the beekeeper
    When the beekeeper marks the missed location
    Then the missed detection is stored with the photo annotation data
    And the correction can be used as evidence for later model evaluation

Feature: Evidence storage and re-rendering

  Scenario: System stores original photos and reusable annotation data
    Given a beekeeper uploads a photo for inspection analysis
    When the system stores the analysis output
    Then the original photo is preserved
    And structured annotation data is stored separately from the original image
    And user corrections are stored as structured data

  Scenario: System re-renders tagged photos from stored annotations
    Given an original photo has stored annotation data
    When the beekeeper opens the tagged-up photo view
    Then the system renders the tagged view from the original photo and annotation data
    And the system does not depend only on a flattened edited image

Feature: Claim boundaries and user trust

  Scenario: System avoids diagnostic claims
    Given an inspection has Varroa analysis results
    When the system displays those results to the beekeeper
    Then the system presents them as AI-assisted visual estimates
    And the system does not present them as a diagnosis
    And the system does not recommend treatment
    And the system does not describe the result as an official infestation measurement

  Scenario: System warns when image evidence is limited
    Given an inspection has limited, low-quality, or low-confidence photo evidence
    When the system presents the Varroa estimate
    Then the system clearly indicates that the estimate may be unreliable
    And the system encourages the beekeeper to use normal inspection methods alongside the AI-assisted estimate

Feature: Requirements traceability and AI-SDLC evidence

  Scenario: Requirement evidence is traceable through the project
    Given a requirement has been approved for the product
    When the project records acceptance criteria, design decisions, implementation, tests, or production evidence
    Then those records can be traced back to the requirement
    And the project can study how AI affected the software development lifecycle

  Scenario: AI contributions and human corrections are recorded
    Given AI has helped generate requirements, analysis outputs, or annotations
    When a human accepts, rejects, corrects, or refines that output
    Then the human action is recorded as AI-SDLC evidence
    And later project reviews can distinguish AI contribution from human judgment

Feature: AI-assisted annotation and dataset bootstrap

  Scenario: Reviewer creates reviewed bee annotations from AI-assisted draft annotations
    Given an original inspection photo is selected for dataset labelling
    When the system creates AI-assisted Draft Annotations for visible bees
    And a human reviewer corrects and approves the useful annotations
    Then the approved annotations become Reviewed Annotations
    And the system records the Annotation Source for each annotation
    And the reviewed annotations are not automatically assigned to training, validation, or benchmark data

  Scenario: Reviewer marks an ambiguous bee as uncertain
    Given an inspection photo has an ambiguous bee-like object
    When the reviewer cannot confidently classify it as complete or partial
    Then the reviewer can mark the annotation as an uncertain bee
    And the uncertain bee is excluded from the complete visible bee denominator
    And the uncertainty is preserved for future model evaluation

  Scenario: Reviewed annotations are assigned to dataset roles
    Given an inspection photo has Reviewed Annotations
    When a dataset curator assigns the reviewed image and annotations to a Dataset Role
    Then the system records a Dataset Item
    And the Dataset Item role is training, validation, benchmark, or excluded
    And the Dataset Item can be included in a traceable Dataset Version

  Scenario: Benchmark data is protected from model training
    Given a Dataset Item has been assigned to the benchmark role
    When the project trains, tunes, or selects a Model Candidate
    Then the benchmark Dataset Item is excluded from training and routine tuning
    And the benchmark item is used only for protected Benchmark Evaluation

  Scenario: Model candidate is evaluated before product use
    Given a Training Run has produced a Model Candidate
    When the project evaluates the candidate against a protected benchmark Dataset Version
    Then the Benchmark Evaluation records bee and Varroa metrics separately
    And a human reviewer must approve the candidate before it becomes user-facing

Feature: Workspace data-use agreement and model governance

  Scenario: Workspace data-use agreement is required for upload and analysis
    Given a Workspace has not accepted the current Workspace Data Use Agreement
    When a User with an owner Workspace Membership tries to upload inspection photos
    Then the upload is blocked
    And the system indicates that upload and analysis require accepted data-use terms

  Scenario: Data-use withdrawal disables new upload and analysis
    Given a Workspace previously accepted the Workspace Data Use Agreement
    When the agreement is withdrawn
    Then new inspection photo upload is disabled
    And new analysis is disabled
    And existing inspection history may remain viewable unless a deletion process applies

  Scenario: User photos are not automatically trusted training data
    Given a beekeeper uploads photos for analysis
    When the system stores those photos and analysis results
    Then the photos are not automatically treated as reviewed ground truth
    And the user corrections are stored as review candidates rather than trusted ground truth

  Scenario: Workspace data-use agreement status is checked before model improvement use
    Given a Beekeeper has uploaded inspection photos or corrections
    When the system considers those photos or corrections for model improvement
    Then the system checks the Workspace Data Use Agreement status and terms version
    And the system excludes photos or corrections when the Workspace does not have an active accepted agreement

  Scenario: Reviewed corrections become eligible for dataset use
    Given a Beekeeper has flagged a false positive or missed likely Varroa detection
    When a human reviewer approves the correction
    Then the approved correction can be assigned to a training, validation, benchmark, or excluded dataset role
    And the dataset role is recorded for traceability

  Scenario: Data deletion request is captured as a deferred privacy workflow
    Given a Beekeeper asks to delete or purge Workspace-held data
    When the request is recorded
    Then the request is treated as a Data Deletion Request
    And the project records that deletion behaviour for prior uploads, dataset versions, and already-trained model artifacts requires a policy decision

Feature: Deferred guest trial analysis

  Scenario: Prospective user submits a limited trial photo
    Given guest trial analysis is enabled in a future version
    And the prospective user has accepted the required trial data-use terms
    And the prospective user has not exceeded the configured trial usage limit
    When the prospective user uploads a photo for trial Varroa analysis
    Then the system analyses the photo as an AI-assisted visual estimate
    And the system returns tagged visual evidence and a visible Varroa estimate
    And the system does not create a long-term inspection history unless the user later creates a Workspace and explicitly saves or imports the result

  Scenario: Prospective user exceeds the trial photo limit
    Given guest trial analysis is enabled in a future version
    And the prospective user has already used the configured trial allowance
    When the prospective user tries to upload another trial photo
    Then the upload is blocked
    And the system indicates that further analysis requires registration or a later allowed trial window

  Scenario: Trial photo is excluded from model improvement by default
    Given a prospective user uploads a trial photo
    When the system stores the trial analysis result
    Then the photo and result are excluded from model-improvement workflows by default
    And any future model-improvement use requires an explicit policy, accepted terms, and human review

## Implementation Decisions

- The first version targets hobbyist and small-scale beekeepers.
- The first client is a web UI.
- The first version assumes one registered User, one default Workspace, one owner Workspace Membership, and that User acting as the primary Beekeeper.
- Beekeeper is a product/persona term in version one, not a separate persisted entity.
- Workspace Membership is persisted from version one, but only the `owner` role is supported.
- Android and Apple apps are future-facing concerns, not version-one delivery targets.
- Guest or trial photo analysis is a deferred / V2 acquisition workflow, not a version-one delivery target.
- The core domain model should include User, Workspace, Workspace Membership, apiary, hive, inspection, inspection photo, analysis result, annotation, user correction, Workspace Data Use Agreement, Data Deletion Request, model version, dataset version, and benchmark evaluation.
- Frame-level handling should be light in version one. Photos may have optional frame labels, but the system should not require full frame inventory management.
- The analysis output should include estimated complete visible bee count, partial visible bee count where possible, likely Varroa count, Varroa association state, and likely mites per 100 complete visible bees.
- The system should store original photos and structured annotation data rather than relying only on flattened annotated images.
- Tagged-up photos should be rendered from original photos plus annotation data.
- AI-assisted annotation is the intended bootstrap path for the first reviewed datasets, but Draft Annotations require human review before they become Reviewed Annotations.
- Dataset-labelling workflows and beekeeper product-feedback workflows may reuse UI components, but their provenance and dataset-governance records must remain distinct.
- The first correction loop should support marking false Varroa detections and missed likely Varroa locations.
- User corrections should be review candidates, not automatic training data.
- Workspace Data Use Agreement acceptance is required before upload and analysis features can be used.
- Workspace Data Use Agreement withdrawal disables new upload and analysis.
- The privacy/deletion gap around prior uploads, dataset versions, and already-trained model artifacts is explicitly deferred and tracked.
- Image upload formats and size limits should be configurable.
- Model, dataset, training, evaluation, data-use agreement, privacy/deletion, and release-gate requirements are governed by the separate model requirements baseline and domain model.
- The product language must preserve the boundary that results are AI-assisted visual estimates, not diagnoses, treatment recommendations, or official infestation measurements.

## Testing Decisions

- Tests should focus on externally visible behaviour rather than implementation details.
- The primary product test seam is the full inspection workflow: create apiary, create hive, create inspection, upload photos, process analysis, view results, correct annotations.
- Domain-level tests should cover infection-rate calculation as likely Varroa detections associated with complete visible bees per 100 estimated complete visible bees.
- Data tests should verify that apiaries, hives, inspections, photos, annotations, analysis results, and corrections remain correctly associated.
- Data tests should verify that user corrections do not become training or benchmark data without review and explicit dataset role assignment.
- Data tests should verify that Workspace-owned apiaries, hives, inspections, photos, analysis results, annotations, corrections, data-use agreements, and deletion requests cannot be accessed across Workspace boundaries.
- Upload tests should verify accepted formats, rejected formats, size-limit handling, and original-photo preservation.
- Data-use agreement tests should verify that upload and analysis require an active accepted Workspace Data Use Agreement.
- Data-use withdrawal tests should verify that withdrawal disables new upload and analysis.
- Privacy tests should verify that Data Deletion Requests can be recorded even while deletion workflow details are deferred.
- UI or acceptance tests should verify that result wording does not claim diagnosis, treatment guidance, or official infestation measurement.
- Browser acceptance tests should exercise the Web UI path for implemented vertical slices, including the photo intake, stub analysis, and annotation evidence review workflow.
- API-level Gherkin scenarios should remain distinct from UI-level browser acceptance tests. UI-level Gherkin is deferred briefly while the Playwright harness stabilizes, but must be introduced within the next few slices.
- A slice verification report should summarize the checks run before a slice is closed, including service tests, API-level BDD scenarios, Web TypeScript checks, and browser acceptance tests where available.
- Slice verification reports summarize executed checks and failure artifacts; they should not claim formal code coverage percentages until separate coverage tooling exists.
- Future model evaluation tests should measure false positives, missed detections, confidence, and correction rates against reviewed image sets.

## Out Of Scope

- Treatment recommendations.
- Official Varroa diagnosis or certification.
- Full commercial apiary management.
- Full frame inventory management.
- Native Android or Apple applications in version one.
- Guest or trial photo analysis before Workspace registration in version one.
- Offline capture in version one.
- A full image annotation studio.
- Validated colony-level infestation estimates.
- Automatic use of user-submitted photos or corrections as training data.
- Multi-user collaboration, advisor access, and organisation-level permissions in version one.
- Workspace invitations, workspace switching, and non-owner Workspace Membership roles in version one.
- Continuing to upload or analyse new photos after Workspace Data Use Agreement withdrawal.
- Full implementation of data deletion or purge workflows in version one.
- Production rules for trial usage limits, abuse prevention, guest retention/deletion, and guest model-improvement eligibility.

## Further Notes

Multiple photos of the same frame are useful but risky for aggregation. Without careful grouping, the system may double-count bees or mites. Version one should allow optional frame labels and clearly caveat inspection-level aggregation when frame grouping is incomplete.

The annotation and correction loop is part of the product and part of the AI-SDLC evidence strategy. It gives users a way to inspect output quality while creating structured evidence for later model evaluation.

Detailed model, dataset, data-use agreement, privacy/deletion, benchmark, and promotion requirements live in `model-requirements.md` and `architecture/domain-model.md`.
