Feature: Bee Orientation Benchmark Evaluation

  Scenario: Dataset Curator runs a Bee Orientation Benchmark Evaluation
    Given the Dataset Curator has a completed Bee Orientation Model Candidate with protected Benchmark evidence
    When the Dataset Curator checks Bee Orientation benchmark readiness
    And the Dataset Curator runs the Bee Orientation benchmark
    Then the Bee Orientation Benchmark Evaluation completes with head direction metrics
    And the Bee Orientation benchmark report remains purpose-limited

  Scenario: No eligible orientation benchmark bees blocks the benchmark
    Given the Dataset Curator has a completed Bee Orientation Model Candidate with only unreliable Benchmark bees
    When the Dataset Curator checks Bee Orientation benchmark readiness
    Then Bee Orientation benchmark readiness is blocked by the eligible bee rule
