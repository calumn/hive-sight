Feature: Reviewer Work Queue

  Scenario: Queue evidence exposes only safe review metadata
    Given a Dataset Curator has requested review for a completed Training Crop
    When an eligible Reviewer opens the Review Queue Item
    Then the Reviewer sees the Training Crop image and reviewed bee ellipses
    And the Reviewer sees safe crop metadata
    And the Reviewer does not see unsafe Workspace metadata

  Scenario: First eligible completion closes the shared queue item
    Given two eligible Reviewers can see the same available Review Queue Item
    When one Reviewer completes the Review Queue Item as approved
    Then the Review Queue Item is no longer available to any Reviewer
    And another Reviewer cannot complete the same Review Queue Item

  Scenario: Dataset Curator cancels an available review request
    Given a Dataset Curator has an available Review Queue Item for a Training Crop
    When the Dataset Curator cancels the Review Queue Item with cancellation notes
    Then the Review Queue Item status becomes cancelled
    And the Dataset Curator can request a new review for the Training Crop
