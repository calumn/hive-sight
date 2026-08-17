@api
Feature: Varroa photo analysis workflow

  Scenario: A beekeeper analyses one Varroa Assessment photo
    Given a Workspace member has a Varroa Assessment Inspection with an uploaded photo
    And that photo has no prior Photo Analysis
    When the Workspace member requests photo analysis
    Then HiveSight starts one Photo Analysis for that Inspection Photo
    And HiveSight reports the Photo Analysis as unreviewed
    And HiveSight reports the number of analysed eligible bees and bees with likely visible Varroa
    And HiveSight does not require a Training Crop

  Scenario: A partial result remains reviewable with its caveat
    Given a Photo Analysis localises complete bees
    And orientation or Varroa Detection cannot process one of those bees
    When HiveSight completes the Photo Analysis
    Then HiveSight reports the Photo Analysis as partial
    And HiveSight reports the failed-bee count and caveat
    And a Workspace member can accept the result

  Scenario: No bees found cannot become accepted evidence
    Given a Photo Analysis finds no complete bees in an Inspection Photo
    When HiveSight completes the Photo Analysis
    Then HiveSight reports no bees found
    And a Workspace member cannot accept the result

  Scenario: Review status controls later Advisor evidence eligibility
    Given a completed or partial Photo Analysis is unreviewed
    When a Workspace member marks it accepted
    Then HiveSight marks it as development integration evidence for later Advisor integration testing
    When a Workspace member changes it to needs expert review with a note
    Then HiveSight marks it ineligible for later Advisor evidence
