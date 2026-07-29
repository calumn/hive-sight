Feature: Vertical Slice 0006 Dataset Role assignment

  Scenario: Dataset Curator assigns reviewed labelling evidence to benchmark
    Given the User is logged in with dataset curator capability for Dataset Role assignment
    And the Workspace has accepted the Workspace Data Use Agreement for Dataset Role assignment
    And the Dataset Curator has reviewed bee Draft Annotations in a Dataset Labelling Session
    When the Dataset Curator assigns the reviewed labelling evidence to benchmark
    Then the Core API creates a protected benchmark Dataset Item
    And the labelling evidence projects the Dataset Item
    And no Dataset Version or Training Run is created

  Scenario: Dataset Curator capability is required for Dataset Role assignment
    Given the User is logged in without dataset curator capability for Dataset Role assignment
    And the Workspace has accepted the Workspace Data Use Agreement for Dataset Role assignment
    And the Dataset Curator has reviewed bee Draft Annotations in a Dataset Labelling Session
    When the User tries to assign the reviewed labelling evidence to training
    Then Dataset Role assignment is blocked by dataset curator authorization
