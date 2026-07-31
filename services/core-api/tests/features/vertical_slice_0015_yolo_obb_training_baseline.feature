Feature: YOLO OBB Bee Detector training baseline

  Scenario: Dataset Curator creates a Bee Detector training baseline
    Given the User is logged in with dataset curator capability for model training
    And the Dataset Curator has active reviewed Training Crop Dataset Items for training and validation
    When the Dataset Curator creates a Bee Detector Dataset Version
    And the Dataset Curator starts a fake Bee Detector Training Run with warning acknowledgement
    Then the Training Run creates a non-user-facing Bee Detector Model Candidate
    And the Dataset Version report protects benchmark data from training input

  Scenario: Ordinary Beekeeper cannot start model training
    Given an ordinary Beekeeper has an accepted Workspace Data Use Agreement
    When the ordinary Beekeeper checks model training readiness
    Then the Core API rejects the model training request
