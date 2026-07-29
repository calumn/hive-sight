Feature: Vertical Slice 0002 Core API analysis handoff

  Scenario: Core API processes a queued stub analysis result
    Given the User is logged in with an owner Workspace Membership
    And the Workspace has accepted the Workspace Data Use Agreement
    And the Beekeeper has uploaded an Inspection Photo
    When the queued Analysis Run is processed
    Then the Core API returns the completed Analysis Run
    And the Core API returns the deterministic stub Analysis Result
    And the Core API identifies the result as a stub rather than a real Varroa estimate

  Scenario: Workspace access is required to process an Analysis Run
    Given the User is logged in with an owner Workspace Membership
    And the Workspace has accepted the Workspace Data Use Agreement
    And the Beekeeper has uploaded an Inspection Photo
    When another User tries to process the queued Analysis Run
    Then processing is blocked by Workspace authorization
