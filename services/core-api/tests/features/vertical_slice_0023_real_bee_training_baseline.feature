Feature: Real Bee Training Baseline

  Scenario: Bee Training uses one shared source Dataset Version
    Given the Dataset Curator has enough marked bees for real Bee Training
    When the Dataset Curator creates a shared Marked-Bee Dataset Version
    And the Dataset Curator checks Bee Training readiness for that Dataset Version
    And the Dataset Curator starts Bee Training
    Then Bee Localisation and Bee Orientation Training Runs complete from the same Dataset Version
    And the Bee Orientation Training Run records training-run validation metrics only

  Scenario: Insufficient orientation data blocks real orientation training
    Given the Dataset Curator has too little orientation evidence for real Bee Training
    When the Dataset Curator creates a shared Marked-Bee Dataset Version
    And the Dataset Curator checks Bee Training readiness for that Dataset Version
    Then Bee Training is blocked by the Bee Orientation minimum evidence rule
