Feature: Varroa Review Outcome Labelling

  Scenario: Dataset Curator records Varroa triage cues during bee annotation
    Given a Training Crop has an editable visible bee ellipse
    When the Dataset Curator marks the bee as body occluded or hard to assess for Varroa review
    And the Dataset Curator flags suspected visible Varroa on that bee
    Then HiveSight saves the Varroa review suitability cue for the bee
    And HiveSight saves the suspected visible Varroa cue for the bee
    And HiveSight records who last updated those cues and when
    And HiveSight does not treat either cue as a Varroa Review Outcome

  Scenario: Dataset Curator opens a Head-Up Normalized Bee Crop for Varroa review
    Given a completed Training Crop contains a reliable complete visible bee ellipse
    When the Dataset Curator opens that bee for Varroa review
    Then HiveSight shows a Head-Up Normalized Bee Crop for the selected bee
    And HiveSight shows the source Training Crop and bee annotation provenance
    And HiveSight shows any Varroa triage cues recorded during bee annotation
    And HiveSight labels the review purpose as model curation
    And HiveSight shows that this is not a Varroa assessment

  Scenario: Dataset Curator records an active negative Varroa Review Outcome
    Given a Head-Up Normalized Bee Crop is open for Varroa review
    When the Dataset Curator records no visible Varroa
    Then HiveSight saves a Varroa Review Outcome of no_visible_varroa
    And HiveSight records zero Varroa markers
    And HiveSight labels the evidence as an active negative judgement

  Scenario: Dataset Curator records an unresolved Varroa Review Outcome
    Given a Head-Up Normalized Bee Crop is open for Varroa review
    When the Dataset Curator records not determined with a note
    Then HiveSight saves a Varroa Review Outcome of not_determined
    And HiveSight does not treat the crop as negative training evidence
    And HiveSight keeps the crop visible as unresolved Varroa evidence

  Scenario: Ineligible bees cannot enter the first Varroa corpus
    Given a Training Crop contains a partial visible bee or an unreliable-orientation bee
    When the Dataset Curator reviews Varroa eligibility for that bee
    Then HiveSight explains that the bee is excluded from the first Head-Up Normalized Varroa corpus
    And HiveSight does not allow a Varroa Review Outcome to be saved for that bee in this slice

  Scenario: Visible Varroa Review requires marker evidence
    Given a Head-Up Normalized Bee Crop is open for Varroa review
    When the Dataset Curator tries to save visible Varroa present without a marker
    Then HiveSight blocks the save and explains that visible Varroa requires marker evidence

  Scenario: Not determined Varroa Review requires a note
    Given a Head-Up Normalized Bee Crop is open for Varroa review
    When the Dataset Curator tries to save not determined without a note
    Then HiveSight blocks the save and explains that not determined requires a note
