Feature: Vertical Slice 0012 - Hive Configuration and Frame Standard metadata

  Scenario: Hive Configuration is required before creating an Inspection
    Given the User has created a Hive without Hive Configuration
    When the User creates a training data collection Inspection for that Hive
    Then the Core API rejects the Inspection because Hive Configuration is required
    When the User records British National deep brood Hive Configuration
    And the User creates a training data collection Inspection for that Hive
    Then the Core API accepts the configured Inspection

  Scenario: Dataset Item provenance snapshots Hive Configuration for export
    Given the User has created a configured British National deep brood Hive
    And the User has assigned a reviewed bee Training Crop to the training Dataset
    When the User later changes the Hive Configuration to Langstroth deep brood
    And the User creates a physical YOLO OBB dataset package
    Then the physical export manifest keeps the Dataset Item Hive Configuration snapshot
