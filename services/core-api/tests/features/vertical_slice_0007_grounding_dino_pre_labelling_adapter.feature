Feature: Vertical Slice 0007 Grounding DINO pre-labelling adapter

  Scenario: Dataset Curator starts labelling with a separate Grounding DINO helper
    Given the User is logged in with dataset curator capability for Grounding DINO labelling
    And the Workspace has accepted the Workspace Data Use Agreement for Grounding DINO labelling
    And the Beekeeper has uploaded an Inspection Photo for Grounding DINO labelling
    When the Dataset Curator starts labelling with a fake Grounding DINO helper
    Then the Core API shows Grounding DINO pre-labeller provenance
    And the helper suggestions remain Draft Annotations requiring review
    And no Dataset Item is assigned by pre-labelling

  Scenario: Grounding DINO helper failure is observable
    Given the User is logged in with dataset curator capability for Grounding DINO labelling
    And the Workspace has accepted the Workspace Data Use Agreement for Grounding DINO labelling
    And the Beekeeper has uploaded an Inspection Photo for Grounding DINO labelling
    When the Dataset Curator starts labelling with an unavailable Grounding DINO helper
    Then the Core API records pre-labelling failure evidence
    And no Draft Annotations or Dataset Items are created
