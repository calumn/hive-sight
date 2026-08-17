@api
Feature: Varroa Photo Analysis evidence and adapter readiness

  Scenario: Configuring a real adapter never silently falls back to the stub
    Given HiveSight is configured with an unavailable local command Varroa Detector adapter
    And a photo has an eligible Head-Up Normalized Bee Crop
    When a developer runs a Varroa Detector preview for that bee
    Then HiveSight reports that the Varroa Detector failed
    And HiveSight does not return deterministic stub detections

  Scenario: Photo Analysis persists photo-level and per-bee evidence
    Given a Varroa assessment photo has two eligible Head-Up Normalized Bee Crops
    And one bee detector call fails during Photo Analysis
    When HiveSight runs Varroa Photo Analysis for that photo
    Then HiveSight persists one Photo Analysis run for the photo
    And HiveSight persists one per-bee analysis record for each attempted eligible bee
    And the Photo Analysis is marked partial with analysed bees, failed bees, and mites found

  Scenario: Photo Analysis with no usable bees is not acceptable evidence
    Given a Varroa assessment photo has no bees eligible for Varroa evaluation
    When HiveSight runs Varroa Photo Analysis for that photo
    Then HiveSight records the Photo Analysis as no usable bees
    And the Photo Analysis cannot be accepted as Advisor evidence

  Scenario: Human review controls Advisor eligibility
    Given a completed Varroa Photo Analysis is unreviewed
    When the Beekeeper marks the Photo Analysis as accepted
    Then HiveSight marks that Photo Analysis as development integration evidence
