Feature: Vertical Slice 0004 Core API annotation review decision

  Scenario: Reviewer records a Review Decision for an Annotation
    Given the User is logged in with reviewer capability for annotation review
    And the Workspace has accepted the Workspace Data Use Agreement for annotation review
    And the Beekeeper has completed stub analysis with bee Annotations
    When the Reviewer approves one bee Annotation
    Then the Core API records the Review Decision
    And the analysis evidence shows the latest review state for that Annotation
    And the review state does not assign dataset use

  Scenario: Reviewer capability is required for Annotation review
    Given the User is logged in without reviewer capability for annotation review
    And the Workspace has accepted the Workspace Data Use Agreement for annotation review
    And the Beekeeper has completed stub analysis with bee Annotations
    When the User tries to approve one bee Annotation
    Then Annotation review is blocked by reviewer authorization
