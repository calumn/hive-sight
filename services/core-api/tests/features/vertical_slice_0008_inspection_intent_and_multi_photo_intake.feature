Feature: Vertical Slice 0008 Inspection intent and multi-photo intake

  Scenario: Beekeeper creates a Varroa assessment Inspection with multiple photos
    Given the User is logged in with an accepted Workspace Data Use Agreement
    And the Beekeeper has created a Varroa assessment Inspection
    When the Beekeeper uploads two Inspection Photos to that Inspection
    Then the Core API lists both Inspection Photos for that Inspection
    And the Inspection intent is shown as Varroa assessment

  Scenario: Dataset labelling is available only for training data collection Inspections
    Given the User is logged in with an accepted Workspace Data Use Agreement
    And the Beekeeper has uploaded a photo to a Varroa assessment Inspection
    When the Dataset Curator tries to start dataset labelling for that photo
    Then dataset labelling is blocked because the Inspection intent is Varroa assessment

  Scenario: Dataset labelling can start from a training data collection Inspection
    Given the User is logged in with an accepted Workspace Data Use Agreement
    And the Beekeeper has uploaded a photo to a training data collection Inspection
    When the Dataset Curator starts dataset labelling for that photo
    Then the Core API creates a Dataset Labelling Session
