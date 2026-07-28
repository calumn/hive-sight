# BeehiveMonitor Product Spec

## Problem Statement

Hobbyist and small-scale beekeepers need a practical way to use inspection photos to assess possible Varroa mite presence in their hives. Raw photos are hard to evaluate consistently, and a simple count alone is not enough unless the beekeeper can see the evidence behind it.

The product should help the beekeeper organise apiaries, hives, inspections, and photos, then provide an AI-assisted estimate of likely Varroa presence from uploaded images. It must avoid overstating the result as a diagnosis, treatment recommendation, or official infestation measurement.

The project also needs to document how AI affects the software development lifecycle, so requirements, decisions, implementation, tests, and production evidence should remain traceable.

## Solution

Build a web-first inspection support system for hobbyist and small-scale beekeepers.

The user creates an apiary, creates hives within that apiary, creates an inspection event for a hive, uploads one or more photos, and reviews analysis results. The system estimates complete visible bees, tracks partial visible bees separately, detects likely Varroa mites on or near bees, calculates likely mites per 100 complete visible bees, and presents tagged-up photos showing the evidence behind the estimate.

The user can optionally view all detected bees and can lightly correct results by marking false Varroa detections or missed likely Varroa locations. The system stores the original photo, structured annotation data, analysis results, and user corrections so tagged images can be re-rendered and model accuracy can be evaluated later.

Version one assumes a single user account or simple account-owned workspace. Collaboration, advisor access, and organisation-level permissions are deferred.

## Gherkin Scenarios

Feature: Apiary and hive setup

  Scenario: Beekeeper creates an apiary
    Given a hobbyist beekeeper is using the system
    When the beekeeper creates an apiary with a name
    Then the apiary is saved
    And the beekeeper can use the apiary to organise hives by real-world location or grouping

  Scenario: Beekeeper creates a hive within an apiary
    Given a hobbyist beekeeper has created an apiary
    When the beekeeper creates a hive within that apiary
    Then the hive is saved under the selected apiary
    And future inspections can be associated with that hive

Feature: Hive inspection photo capture

  Scenario: Beekeeper creates an inspection event for a hive
    Given a hobbyist beekeeper has an apiary with at least one hive
    When the beekeeper creates an inspection event for a selected hive
    Then the inspection is associated with that hive
    And the inspection can hold photos and analysis results

  Scenario: Beekeeper uploads multiple photos to an inspection
    Given a hobbyist beekeeper has created an inspection event
    When the beekeeper uploads one or more frame photos
    Then each photo is associated with the inspection
    And the original uploaded photo is preserved for later review

  Scenario: Beekeeper optionally labels photos from the same frame
    Given a hobbyist beekeeper has uploaded multiple photos to an inspection
    When the beekeeper labels two or more photos with the same frame label
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

Feature: Model training consent and governance

  Scenario: User photos are not automatically used for training
    Given a beekeeper uploads photos for analysis
    When the system stores those photos and analysis results
    Then the photos are not automatically added to model training data
    And the user corrections are stored as review candidates rather than trusted ground truth

  Scenario: Consent status is stored before model improvement use
    Given a beekeeper has uploaded photos or corrections
    When the system considers those photos or corrections for model improvement
    Then the system checks consent status at photo or inspection level
    And the system excludes photos or corrections without recorded consent

  Scenario: Reviewed corrections become eligible for dataset use
    Given a user has flagged a false positive or missed likely Varroa detection
    When a human reviewer approves the correction
    Then the approved correction can be assigned to a training, validation, benchmark, or excluded dataset role
    And the dataset role is recorded for traceability

## Implementation Decisions

- The first version targets hobbyist and small-scale beekeepers.
- The first client is a web UI.
- The first version assumes a single user account or simple account-owned workspace.
- Android and Apple apps are future-facing concerns, not version-one delivery targets.
- The core domain model should include apiary, hive, inspection event, photo, analysis result, annotation, and user correction.
- Frame-level handling should be light in version one. Photos may have optional frame labels, but the system should not require full frame inventory management.
- The analysis output should include estimated complete visible bee count, partial visible bee count where possible, likely Varroa count, Varroa association state, and likely mites per 100 complete visible bees.
- The system should store original photos and structured annotation data rather than relying only on flattened annotated images.
- Tagged-up photos should be rendered from original photos plus annotation data.
- The first correction loop should support marking false Varroa detections and missed likely Varroa locations.
- User corrections should be review candidates, not automatic training data.
- The exact consent capture flow is deferred, but consent status must be traceable before model-improvement use.
- Image upload formats and size limits should be configurable.
- Model, dataset, training, evaluation, consent, and release-gate requirements are governed by the separate model requirements baseline.
- The product language must preserve the boundary that results are AI-assisted visual estimates, not diagnoses, treatment recommendations, or official infestation measurements.

## Testing Decisions

- Tests should focus on externally visible behaviour rather than implementation details.
- The primary product test seam is the full inspection workflow: create apiary, create hive, create inspection, upload photos, process analysis, view results, correct annotations.
- Domain-level tests should cover infection-rate calculation as likely Varroa detections associated with complete visible bees per 100 estimated complete visible bees.
- Data tests should verify that apiaries, hives, inspections, photos, annotations, analysis results, and corrections remain correctly associated.
- Data tests should verify that user corrections do not become training or benchmark data without review and explicit dataset role assignment.
- Data tests should verify that account-owned apiaries, hives, inspections, photos, analysis results, annotations, corrections, and consent records cannot be accessed across account boundaries.
- Upload tests should verify accepted formats, rejected formats, size-limit handling, and original-photo preservation.
- Consent tests should verify that photos and corrections without recorded consent cannot become model-improvement candidates.
- UI or acceptance tests should verify that result wording does not claim diagnosis, treatment guidance, or official infestation measurement.
- Future model evaluation tests should measure false positives, missed detections, confidence, and correction rates against reviewed image sets.

## Out Of Scope

- Treatment recommendations.
- Official Varroa diagnosis or certification.
- Full commercial apiary management.
- Full frame inventory management.
- Native Android or Apple applications in version one.
- Offline capture in version one.
- A full image annotation studio.
- Validated colony-level infestation estimates.
- Automatic use of user-submitted photos or corrections as training data.
- Multi-user collaboration, advisor access, and organisation-level permissions in version one.

## Further Notes

Multiple photos of the same frame are useful but risky for aggregation. Without careful grouping, the system may double-count bees or mites. Version one should allow optional frame labels and clearly caveat inspection-level aggregation when frame grouping is incomplete.

The annotation and correction loop is part of the product and part of the AI-SDLC evidence strategy. It gives users a way to inspect output quality while creating structured evidence for later model evaluation.

Detailed model, dataset, consent, benchmark, and promotion requirements live in `model-requirements.md`.
