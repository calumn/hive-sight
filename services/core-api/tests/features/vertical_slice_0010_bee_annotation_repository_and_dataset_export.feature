Feature: Vertical Slice 0010 Bee Annotation Repository and Dataset export

  Scenario: Dataset Curator assigns a completed Training Crop to the Bee Annotation Repository
    Given the User is logged in with dataset curator capability for Bee Annotation Repository export
    And the Dataset Curator has completed a Training Crop with a visible bee ellipse
    When the Dataset Curator assigns the Training Crop to training
    Then the Core API creates a Dataset Item from the Training Crop
    And the Dataset Item snapshots the reviewed bee ellipse evidence

  Scenario: YOLO OBB export protects benchmark and excluded Dataset Items
    Given the User is logged in with dataset curator capability for Bee Annotation Repository export
    And the Dataset Curator has assigned Training Crops to training validation benchmark and excluded roles
    When the Dataset Curator creates a YOLO OBB manifest export
    Then the manifest includes training and validation label rows
    And the manifest reports benchmark and excluded items without exporting them for training
