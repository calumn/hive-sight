Feature: Photo-visible Varroa evidence summary

  Scenario: Dataset Curator sees a photo-visible result from reviewed bee outcomes
    Given a Training Data Collection Inspection Photo has completed Training Crops
    And eligible complete bees on those crops have Varroa Review Outcomes
    When the Dataset Curator opens the Varroa Review stage
    Then HiveSight reports reviewed bee count, visible-Varroa bee count, visible mite marker count, active negative count, not-determined count, unreviewed eligible count, and ineligible bee count
    And HiveSight shows review completion and determinate Varroa coverage
    And HiveSight labels the result as photo-visible evidence, not a treatment recommendation

  Scenario: Visible mite marker count is separated from bee-positive count
    Given one reviewed bee has two Varroa markers
    And another reviewed bee has no visible Varroa
    When HiveSight calculates the photo-visible Varroa evidence summary
    Then HiveSight reports one visible-Varroa bee
    And HiveSight reports two visible mite markers
    And HiveSight does not treat marker count and positive bee count as the same measure

  Scenario: Unresolved or unreviewed bees reduce coverage
    Given a photo has eligible complete bees without determinate Varroa outcomes
    When HiveSight calculates the photo-visible Varroa evidence summary
    Then HiveSight includes those bees in the eligible denominator
    And HiveSight reports review completion and determinate Varroa coverage below 100%
    And HiveSight shows a coverage warning

  Scenario: Ineligible bees are excluded from the visible Varroa denominator
    Given a photo has partial visible bees or bees with unreliable orientation
    When HiveSight calculates the photo-visible Varroa evidence summary
    Then HiveSight reports them as ineligible or not assessed for Varroa
    And HiveSight excludes them from the eligible complete-bee denominator
    And HiveSight keeps their count visible in the evidence breakdown

  Scenario: Unfinished crops are disclosed but not counted
    Given a Training Data Collection Inspection Photo has one completed Training Crop
    And the same photo has one unfinished Training Crop
    When HiveSight calculates the photo-visible Varroa evidence summary
    Then HiveSight includes the completed crop in the evidence counts
    And HiveSight excludes the unfinished crop from bee, marker, positive, negative, and coverage counts
    And HiveSight shows that one unfinished crop was not included

  Scenario: Advisor context is available only as evidence, not advice
    Given a photo has a photo-visible Varroa evidence summary with at least one determinate eligible bee outcome
    When an integration client checks whether Advisor-ready Varroa context exists
    Then HiveSight reports that Varroa evidence context is available with caveats
    And HiveSight does not produce a treatment recommendation
