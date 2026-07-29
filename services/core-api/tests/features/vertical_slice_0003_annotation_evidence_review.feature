Feature: Vertical Slice 0003 Core API annotation evidence review

  Scenario: Core API returns bee annotation evidence for a completed stub result
    Given the User is logged in with an owner Workspace Membership for evidence review
    And the Workspace has accepted the Workspace Data Use Agreement for evidence review
    And the Beekeeper has uploaded and processed an Inspection Photo
    When the Beekeeper requests analysis evidence for the Analysis Run
    Then the Core API returns the original Inspection Photo evidence reference
    And the Core API returns complete and partial visible bee Annotations
    And the Core API returns counts that match the bee Annotations
    And the Core API identifies the evidence as deterministic stub evidence

  Scenario: Workspace access is required to view analysis evidence
    Given the User is logged in with an owner Workspace Membership for evidence review
    And the Workspace has accepted the Workspace Data Use Agreement for evidence review
    And the Beekeeper has uploaded and processed an Inspection Photo
    When another User requests analysis evidence for the Analysis Run
    Then evidence viewing is blocked by Workspace authorization
