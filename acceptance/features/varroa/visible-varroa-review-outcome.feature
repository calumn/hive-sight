@api @web
Feature: Varroa review outcome

  Scenario: Dataset Curator records visible Varroa evidence with two mite markers
    Given a Dataset Curator has opened an eligible bee for Varroa review
    When the Dataset Curator records visible Varroa with two mite markers
    Then HiveSight preserves a visible-Varroa review outcome for that bee
    And HiveSight preserves two mite markers for that bee
    And HiveSight reports one visible-Varroa bee and two visible Varroa markers
    And HiveSight shows the saved markers when the review is reopened
