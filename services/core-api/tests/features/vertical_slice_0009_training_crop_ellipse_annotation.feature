Feature: Vertical Slice 0009 Training crop ellipse annotation

  Scenario: Dataset Curator completes a Training Crop with a reviewed bee ellipse
    Given the User is logged in with dataset curator capability for Training Crop annotation
    And the Beekeeper has uploaded an Inspection Photo for Training Crop annotation
    When the Dataset Curator creates a Training Crop from that photo
    And the Dataset Curator adds a complete visible bee ellipse to that crop
    And the Dataset Curator marks the Training Crop review complete with visible bees
    Then the Core API shows completed Training Crop evidence
    And the Training Crop evidence is not assigned to dataset use

  Scenario: Dataset Curator completes a no-visible-bees Training Crop
    Given the User is logged in with dataset curator capability for Training Crop annotation
    And the Beekeeper has uploaded an Inspection Photo for Training Crop annotation
    When the Dataset Curator creates a Training Crop from that photo
    And the Dataset Curator marks the Training Crop review complete with no visible bees
    Then the Core API shows a completed no-visible-bees Training Crop with no ellipses

  Scenario: Training Crop creation is blocked for Varroa assessment Inspections
    Given the User is logged in with dataset curator capability for Training Crop annotation
    And the Beekeeper has uploaded an Inspection Photo for Varroa assessment
    When the Dataset Curator tries to create a Training Crop from that photo
    Then Training Crop creation is blocked because the Inspection intent is Varroa assessment
