Feature: Vertical Slice 0007 retired Grounding DINO pre-labelling adapter

  Scenario: Grounding DINO is not an active pre-labelling provider
    Given Grounding DINO has been retired by ADR 0005
    When the Core API pre-labeller dependency is configured for Grounding DINO
    Then the Core API rejects that pre-labeller configuration
    And deterministic pre-labelling remains the supported local default
