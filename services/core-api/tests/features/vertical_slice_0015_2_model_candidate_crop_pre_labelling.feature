Feature: Vertical Slice 0015.2 Model Candidate Crop Pre-Labelling
  Candidate pre-labelling helps a Dataset Curator review editable Training Crops without turning
  unreviewed model output into dataset evidence.

  Scenario: Dataset Curator previews and accepts candidate bee suggestions for an editable crop
    Given a completed Bee Detector Model Candidate exists
    And an editable Training Crop was not included in that Model Candidate Dataset Version
    When the Dataset Curator asks the Model Candidate to suggest bees for the crop
    Then the Core API returns transient candidate bee proposals
    When the Dataset Curator accepts a candidate proposal as a reviewed partial bee
    Then the Training Crop evidence records model-candidate provenance

  Scenario: Dataset Curator cannot pre-label a crop from the candidate's own Dataset Version
    Given a completed Bee Detector Model Candidate exists
    And an editable Training Crop was included in that Model Candidate Dataset Version
    When the Dataset Curator asks the Model Candidate to suggest bees for the crop
    Then candidate pre-labelling is blocked by the frozen Dataset Version boundary
