Feature: Vertical Slice 0011 Physical Dataset Export Package

  Scenario: Dataset Curator creates a physical YOLO OBB package
    Given the User is logged in with dataset curator capability for physical dataset export
    And the Dataset Curator has assigned Training Crops to training and validation roles
    When the Dataset Curator creates a physical YOLO OBB dataset export package
    Then the Core API writes crop images labels manifest and dataset YAML files
    And the package response reports the generated package summary

  Scenario: Physical package protects benchmark and excluded Dataset Items
    Given the User is logged in with dataset curator capability for physical dataset export
    And the Dataset Curator has assigned Training Crops to training validation benchmark and excluded roles for physical export
    When the Dataset Curator creates a physical YOLO OBB dataset export package
    Then the physical package contains only training and validation files
    And the manifest reports benchmark and excluded items as metadata only
