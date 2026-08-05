Feature: Bee Orientation training baseline

  Scenario: Dataset Curator creates a Bee Orientation baseline from a shared Marked-Bee Dataset Version
    Given the User is logged in with dataset curator capability for Bee Orientation training
    And the Dataset Curator has reliable complete marked bees in training and validation
    When the Dataset Curator creates a shared Marked-Bee Dataset Version
    And the Dataset Curator checks Bee Orientation readiness for that Dataset Version
    And the Dataset Curator starts the fake Bee Orientation Training Run
    Then the Bee Orientation Training Run completes without predictive training metrics
    And the non-user-facing Bee Orientation Model Candidate is recorded
