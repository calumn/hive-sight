Feature: Vertical Slice 0005 AI-assisted bee annotation bootstrap

  Scenario: Dataset Curator creates reviewed bee annotations from AI-assisted drafts
    Given the User is logged in with dataset curator capability
    And the Workspace has accepted the Workspace Data Use Agreement for dataset labelling
    And the Beekeeper has uploaded an Inspection Photo for dataset labelling
    When the Dataset Curator starts AI-assisted dataset labelling for that photo
    And the Dataset Curator records source grouping and image quality metadata
    And the Dataset Curator approves complete and partial bee draft annotations
    Then the Core API shows reviewed dataset-labelling bee annotations
    And the labelling evidence preserves draft source and curator provenance
    And the labelling evidence does not assign dataset use

  Scenario: Dataset Curator capability is required for dataset labelling
    Given the User is logged in without dataset curator capability
    And the Workspace has accepted the Workspace Data Use Agreement for dataset labelling
    And the Beekeeper has uploaded an Inspection Photo for dataset labelling
    When the User tries to start AI-assisted dataset labelling for that photo
    Then dataset labelling is blocked by dataset curator authorization

  Scenario: Uncertain bee annotation type is still a documented gap
    Given an uploaded Inspection Photo contains an ambiguous bee-like object
    When the Dataset Curator needs to mark an uncertain bee
    Then uncertain bee annotation type support remains a documented gap
