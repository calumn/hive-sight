Feature: Varroa Detector adapter seam

  Scenario: Dataset Curator previews likely Varroa detections on one eligible bee crop
    Given a completed Training Crop contains a reliable complete visible bee
    And HiveSight can generate a Head-Up Normalized Bee Crop for that bee
    When the Dataset Curator runs the Varroa Detector preview for the bee
    Then HiveSight sends the Head-Up Normalized Bee Crop through the configured Varroa Detector adapter
    And HiveSight shows one deterministic Likely Varroa Detection as a model-preview box
    And HiveSight shows the detection location, size, confidence, and elapsed time in the preview details
    And HiveSight labels the result as model preview evidence only
    And HiveSight does not save a Varroa Review Outcome

  Scenario: The stub adapter is visibly replaceable and non-promotable
    Given HiveSight is using the deterministic stub Varroa Detector adapter
    When the Dataset Curator runs the Varroa Detector preview
    Then HiveSight returns adapter provenance including workspace, model purpose, adapter type, adapter version, model reference, and input transform version
    And HiveSight labels the detections as deterministic stub output
    And HiveSight marks the output as not user-facing and not eligible for promotion

  Scenario: Ineligible bees are not sent to the Varroa Detector adapter
    Given a Training Crop contains a partial visible bee or an unreliable-orientation bee
    When the Dataset Curator tries to run the Varroa Detector preview for that bee
    Then HiveSight returns a detector preview status of not_assessed
    And HiveSight does not call the Varroa Detector adapter
    And HiveSight explains why the bee is not assessed for Varroa Detection
    And HiveSight does not treat the bee as a negative Varroa result

  Scenario: Model preview detections do not overwrite human review evidence
    Given a bee already has a saved human Varroa Review Outcome
    When the Dataset Curator runs the Varroa Detector preview for that bee
    Then HiveSight shows the model preview separately from the saved human outcome
    And HiveSight leaves the human Varroa Review Outcome and markers unchanged
    And HiveSight does not change the photo-visible Varroa evidence summary

  Scenario: Adapter failure is visible without creating evidence
    Given the configured Varroa Detector adapter cannot process the Head-Up Normalized Bee Crop
    When the Dataset Curator runs the Varroa Detector preview
    Then HiveSight clears any previous model-preview boxes
    And HiveSight returns a detector preview status of failed
    And HiveSight reports the adapter failure reason
    And HiveSight records no Likely Varroa Detections
    And HiveSight does not create or change a Varroa Review Outcome
