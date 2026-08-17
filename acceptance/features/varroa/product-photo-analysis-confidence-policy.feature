@api
Feature: Product Photo Analysis confidence policy

  Scenario: Accepted deterministic Photo Analysis is development-integration evidence only
    Given a Varroa Assessment Photo Analysis was produced by the deterministic development adapter
    When a Workspace member views the Photo Analysis confidence policy
    Then HiveSight labels the run as development model evidence only
    And HiveSight reports the Advisor evidence eligibility as ineligible
    When the Workspace member marks the Photo Analysis accepted
    Then HiveSight reports the Advisor evidence eligibility as development integration only
    And HiveSight does not label the run as product-candidate evidence

  Scenario: A complete non-stub Photo Analysis can become product-candidate evidence after review
    Given a Varroa Assessment Photo Analysis was produced by a replaceable non-stub adapter
    And every localised complete bee has usable orientation and Varroa Detector evidence
    And the Varroa Detector evidence satisfies product photo confidence policy version "product_photo_confidence_policy_v1"
    When a Workspace member views the Photo Analysis confidence policy
    Then HiveSight records the confidence policy status as advisor candidate possible
    And HiveSight reports that accepted review is required before later Advisor use
    When the Workspace member marks the Photo Analysis accepted
    Then HiveSight reports the Advisor evidence eligibility as product candidate

  Scenario: Low-confidence-only Varroa evidence blocks Advisor eligibility without hiding markers
    Given a Varroa Assessment Photo Analysis includes a bee with only Varroa detections below the policy confidence floor
    When HiveSight applies the Product Photo Analysis Confidence Policy
    Then HiveSight keeps the detection visible in the evidence detail
    And HiveSight reports a confidence warning for Varroa Detection
    And HiveSight reports the Advisor evidence eligibility as ineligible

  Scenario: Zero likely Varroa detections can be product-candidate evidence
    Given a completed non-stub Varroa Assessment Photo Analysis has zero likely Varroa detections
    And every eligible complete bee has a completed detector call with acceptable provenance
    When a Workspace member marks the Photo Analysis accepted
    Then HiveSight reports the Advisor evidence eligibility as product candidate
    And HiveSight does not state that no Varroa is present in the hive

  Scenario: Incomplete bee processing remains explicit coverage limitation
    Given a Varroa Assessment Photo Analysis has eligible complete bees that were not assessed for Varroa
    When HiveSight applies the Product Photo Analysis Confidence Policy
    Then HiveSight reports the unassessed bee count as a coverage limitation
    And HiveSight does not treat unassessed bees as no-visible-Varroa evidence
    And HiveSight reports the Advisor evidence eligibility as ineligible
