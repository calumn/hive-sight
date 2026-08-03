Feature: Model Candidate Evaluation and Benchmark Report
  Protected benchmark evidence must be evaluated separately from Bee Detector training evidence.

  Scenario: Dataset Curator evaluates a Bee Detector Model Candidate against protected benchmark crops
    Given the User is logged in with dataset curator capability for benchmark evaluation
    And the Dataset Curator has a completed Bee Detector Model Candidate with protected benchmark Training Crops
    When the Dataset Curator starts a Benchmark Evaluation for that Model Candidate
    Then the Benchmark Evaluation completes with metrics and a benchmark report

  Scenario: Ordinary Beekeeper cannot run model benchmark evaluation
    Given an ordinary Beekeeper has an accepted Workspace Data Use Agreement for benchmark evaluation
    When the ordinary Beekeeper starts a Benchmark Evaluation
    Then the Core API rejects the benchmark evaluation request
