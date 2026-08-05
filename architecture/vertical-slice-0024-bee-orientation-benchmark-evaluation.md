# Vertical Slice 0024: Bee Orientation Benchmark Evaluation

Status: planned; acceptance scenarios signed off on 2026-08-05.

## Purpose

Let a Dataset Curator evaluate a completed Bee Orientation Model Candidate against protected Benchmark evidence and produce a purpose-limited benchmark report for head-direction prediction.

Slice 0023 proves HiveSight can train Bee Localisation and Bee Orientation in tandem from one shared Marked-Bee Dataset Version. Slice 0024 proves the next trust step: a Bee Orientation candidate can be measured separately from Bee Localisation and Varroa Detection, using only protected reliable complete visible bee evidence.

This slice does not decide whether the binary Head Up / Head Down classifier is good enough for Varroa. It creates the evaluation path, report shape, raw prediction artifact, and UI affordance needed to inspect that evidence later.

## Source Inputs

- `CONTEXT.md`: Bee Orientation, Model Purpose, Marked-Bee Dataset Version, Benchmark Evaluation, Complete Visible Bee, Partial Visible Bee, Orientation Reliability, Varroa Assessment.
- `requirements/model-requirements.md`: MR-001A Bee Head Direction, MR-008B Orientation Reliability, MR-018 Protected Benchmark, MR-029 Training Run and Model Candidate records, Bee Orientation Metrics, MR-030 Benchmark Evaluation Before Promotion.
- `requirements/roadmap.md`: Bee Orientation Benchmark Report.
- `architecture/adr/0007-three-stage-bee-localisation-orientation-and-varroa-pipeline.md`: Bee Localisation, Bee Orientation, and Varroa Detection remain separately governed Model Purposes.
- `architecture/bee-orientation-classifier-design.md`: Bee Orientation benchmark and evaluation design.
- `architecture/vertical-slice-0022-bee-orientation-training-baseline.md`: shared Marked-Bee Dataset Version and orientation package builder.
- `architecture/vertical-slice-0023-real-bee-training-baseline.md`: real Bee Orientation Model Candidate created from the shared source Dataset Version.
- `architecture/parking-lot.md`: PARK-0028 Automated Bee Head Direction Prediction and PARK-0036 Benchmark Dataset Version Lifecycle.

## Accepted Acceptance Scenarios

These scenarios were accepted for implementation on 2026-08-05.

```gherkin
Feature: Bee Orientation Benchmark Evaluation

  Scenario: Dataset Curator checks Bee Orientation benchmark readiness
    Given a completed Bee Orientation Model Candidate exists
    And its shared Marked-Bee Dataset Version contains protected Benchmark evidence
    When the Dataset Curator checks Bee Orientation benchmark readiness
    Then HiveSight reports the eligible reliable complete benchmark bee count
    And HiveSight reports excluded unreliable-orientation bees
    And HiveSight reports excluded partial visible bees
    And HiveSight blocks the benchmark when no eligible benchmark bees exist

  Scenario: Dataset Curator runs a Bee Orientation Benchmark Evaluation
    Given Bee Orientation benchmark readiness is satisfied
    When the Dataset Curator runs the Bee Orientation benchmark
    Then HiveSight evaluates the Bee Orientation Model Candidate against protected Benchmark evidence from the candidate's source Dataset Version
    And HiveSight records one raw prediction row per evaluated benchmark bee
    And HiveSight reports Head Up and Head Down accuracy evidence
    And HiveSight reports a Head Up / Head Down confusion matrix
    And the Benchmark Evaluation names Model Purpose Bee Orientation

  Scenario: Bee Orientation benchmark evidence remains purpose-limited
    Given a completed Bee Orientation Benchmark Evaluation exists
    When the Dataset Curator opens the benchmark report
    Then the report states that it evaluates head-direction prediction only
    And it does not claim Bee Localisation quality
    And it does not claim Varroa Detection quality
    And it does not make the candidate available for Varroa Assessment

  Scenario: Fake and real orientation candidates are labelled honestly
    Given a Bee Orientation Model Candidate was created by a fake adapter
    When the Dataset Curator runs a Bee Orientation benchmark
    Then HiveSight allows the benchmark workflow to complete
    And the report labels fake-adapter results as workflow evidence only
    And the report does not present fake-adapter metrics as real model quality

  Scenario: Developer runs an optional local orientation benchmark QA command
    Given a completed Bee Orientation Model Candidate exists in the dev database
    When the developer runs the Bee Orientation benchmark QA command
    Then HiveSight evaluates the latest eligible Bee Orientation candidate without resetting or seeding the database
    And the command prints the candidate id, evaluated bee count, accuracy, report artifact id, and raw predictions artifact id
```

## User Path

Given a Dataset Curator has a completed Bee Orientation Model Candidate and protected Benchmark evidence in that candidate's shared Marked-Bee Dataset Version,
When they check readiness and run the Bee Orientation benchmark from Model Governance,
Then HiveSight reports purpose-limited head-direction benchmark evidence and raw prediction artifacts without making Varroa readiness claims.

## Preconditions

- Slice 0023 is implemented.
- The selected User has Dataset Curator capability.
- Workspace Data Use Agreement requirements remain enforced.
- A completed Bee Orientation Model Candidate exists.
- The candidate references a shared Marked-Bee Dataset Version.
- That Dataset Version contains Benchmark Dataset Items.
- Scored benchmark evidence is limited to reliable complete visible bee annotations.
- Partial visible bees and unreliable-orientation bees are reported as excluded or deferred, not silently treated as failures or negatives.

## Grilled Design Decisions

- Allow both fake and real Bee Orientation candidates so the workflow and report shape stay fast-testable, while clearly labelling fake-adapter results as workflow evidence only.
- Use Benchmark Dataset Items already frozen inside the candidate's source Marked-Bee Dataset Version.
- Do not introduce a separate reusable Benchmark Dataset Version lifecycle in this slice.
- Score only reliable complete visible bees.
- Count unreliable-orientation and partial visible bees as excluded/deferred evidence.
- Report classifier-style metrics only: Head Up / Head Down accuracy, confusion matrix, evaluated count, optional confidence distribution when available, and exclusions.
- Do not calculate angular error in this slice.
- Do not add promotion thresholds or pass/fail decisions.
- Add a separate Bee Orientation benchmark section inside Model Governance, in a modest Model Benchmarking area alongside Bee Localisation benchmarking.
- Add a narrow Bee Orientation benchmark workflow first; generalise benchmark plumbing later only when the shared abstraction is proven.
- Use the candidate's training Dataset Version's protected Benchmark items only.
- Store both aggregate report evidence and a raw JSON artifact with one row per evaluated benchmark bee.
- Keep the current one-active-model-job guard.
- Block readiness when Benchmark items exist but none contain eligible reliable complete visible bees, with a clear explanation.
- Add an optional local QA command if small, append-only, and non-resetting.
- Leave PARK-0028 parked but update its note to say benchmark machinery now exists; inference, Head-Up Normalized Bee Crop generation, and classifier-sufficiency decisions remain deferred.
- Require `pnpm verify:slice`; live Postgres orientation-benchmark verification is recommended but not mandatory unless implementation changes persistence schema or migrations.

## End-To-End Behaviour

Model Governance gains a clearer Model Benchmarking area with separate Bee Localisation and Bee Orientation sections.

For Bee Orientation, the Dataset Curator selects or uses a completed Bee Orientation Model Candidate. HiveSight checks benchmark readiness against the candidate's own source Marked-Bee Dataset Version. The readiness response reports:

- candidate id and human-readable id;
- source Dataset Version id and human-readable id;
- eligible reliable complete benchmark bee count;
- excluded unreliable-orientation bee count;
- excluded partial visible bee count;
- benchmark Dataset Item count;
- warnings, including small benchmark set;
- blockers when no eligible reliable complete benchmark bees exist or when the candidate is not a Bee Orientation candidate.

When readiness is satisfied, HiveSight creates a Bee Orientation Benchmark Evaluation. The evaluation runs against protected Benchmark evidence from the same shared source Dataset Version. It records expected Head Up / Head Down labels from the human-reviewed directed ellipse orientation package convention and obtains predicted labels from the selected candidate.

The first fake-adapter path may deterministically replay expected labels or otherwise produce deterministic workflow evidence. The report must label this as fake-adapter workflow evidence only. A real-adapter path may use the candidate artifact and record confidence values when available.

The completed Benchmark Evaluation produces:

- aggregate metrics summary;
- report artifact;
- raw predictions JSON artifact;
- latest activity and job status in Model Governance;
- purpose-limited caveats stating that this evaluates Bee Orientation only.

## Layers Touched

- Web UI: Add Bee Orientation benchmark readiness, run action, run summary, report/raw artifact links, and modest Model Benchmarking structure inside Model Governance.
- Core API: Add Bee Orientation benchmark readiness and start endpoints or extend existing benchmark workflow while preserving explicit Model Purpose.
- Analysis Service: Not touched.
- Storage: Reuse existing Benchmark Evaluation, Model Candidate, Dataset Version, Dataset Item, and artifact records where possible. Add fields only if required to represent orientation metrics safely.
- Queue or async boundary: Reuse existing one-active-model-job guard and local benchmark worker pattern.
- Contracts: Add purpose-specific readiness/start responses and metrics fields for Bee Orientation evaluation.
- Observability: Record readiness blockers, benchmark queued/running/completed/failed, artifact creation, candidate id, Dataset Version id, evaluated count, and fake-vs-real adapter labelling.
- Tooling: Add optional `pnpm model:qa:bee:orientation-evaluate` if implementation cost stays small.

## Test Seams

- Seam: Bee Orientation benchmark readiness
- Behaviour verified: candidate purpose, source Dataset Version, eligible reliable complete benchmark bee count, exclusions, warnings, and blockers are reported.
- Test style: focused Core API tests and API-level BDD.

- Seam: Bee Orientation benchmark evaluation
- Behaviour verified: completed evaluation records purpose, metrics summary, confusion matrix, report artifact, and raw prediction artifact.
- Test style: workflow/service tests and API-level BDD.

- Seam: Fake vs real candidate labelling
- Behaviour verified: fake-adapter evaluation completes but is labelled as workflow evidence only; real-adapter evaluation is allowed through explicit local lanes.
- Test style: workflow tests, report-content assertions, and optional real-adapter QA command.

- Seam: UI Model Benchmarking
- Behaviour verified: Dataset Curator sees separate Bee Localisation and Bee Orientation benchmark sections and cannot mistake orientation benchmark evidence for Varroa readiness.
- Test style: Playwright browser acceptance.

- Seam: QA command
- Behaviour verified: command evaluates the latest eligible Bee Orientation candidate in dev without resetting or seeding the database and prints useful ids/metrics.
- Test style: script/static command guard plus focused smoke where practical.

## Data Shape

Minimum additions or generalizations:

- Bee Orientation benchmark readiness response:
  - `model_candidate_id`;
  - `model_candidate_human_readable_id`;
  - `dataset_version_id`;
  - `dataset_version_human_readable_id`;
  - `eligible_benchmark_bee_count`;
  - `excluded_unreliable_orientation_count`;
  - `excluded_partial_visible_bee_count`;
  - `benchmark_dataset_item_count`;
  - `eligible_to_start_benchmark`;
  - warnings and blockers.
- Bee Orientation benchmark metrics:
  - `evaluated_bee_count`;
  - `accuracy`;
  - confusion matrix with `head_up` and `head_down`;
  - optional confidence distribution;
  - `metric_scope`;
  - fake/real adapter label.
- Raw prediction artifact row:
  - source ids: Dataset Item, Training Crop, Source Image or Inspection Photo, bee annotation id;
  - expected label;
  - predicted label;
  - confidence when available;
  - adapter type;
  - exclusion reason when recorded in the raw artifact.

## Out Of Scope

- Reusable named Benchmark Dataset Version lifecycle.
- Model Candidate comparison across a shared reusable benchmark.
- Promotion thresholds or pass/fail release decisions.
- Angular error metrics.
- Orientation inference in live Varroa Assessment.
- Head-Up Normalized Bee Crop generation for Varroa.
- Varroa Review Outcome labelling.
- Varroa Detection training, benchmark, or report.
- End-to-End Pipeline Evaluation.
- Job scheduler redesign or concurrent model jobs.
- User-facing Model Version promotion.

## Acceptance Criteria

- [ ] Model Governance contains a distinct Bee Orientation benchmark section in a clearer Model Benchmarking area.
- [ ] Readiness accepts completed Bee Orientation Model Candidates and rejects other Model Purposes.
- [ ] Readiness uses the candidate's source Marked-Bee Dataset Version.
- [ ] Readiness reports eligible reliable complete benchmark bees.
- [ ] Readiness reports excluded unreliable-orientation and partial visible bees.
- [ ] Readiness blocks when no eligible reliable complete benchmark bees exist.
- [ ] A Bee Orientation Benchmark Evaluation can run against protected Benchmark evidence.
- [ ] The evaluation records Model Purpose Bee Orientation.
- [ ] The evaluation records one raw prediction row per evaluated benchmark bee.
- [ ] The report includes Head Up / Head Down accuracy evidence.
- [ ] The report includes a Head Up / Head Down confusion matrix.
- [ ] Confidence distribution is shown only when available; otherwise it is clearly `n/a`.
- [ ] Fake-adapter results are labelled as workflow evidence only, not real model quality.
- [ ] The report states that it evaluates head-direction prediction only.
- [ ] The report does not claim Bee Localisation quality.
- [ ] The report does not claim Varroa Detection quality.
- [ ] The benchmark does not make the candidate available for Varroa Assessment.
- [ ] The existing one-active-model-job guard still applies.
- [ ] Optional QA command is added if small and does not reset, seed, or migrate the database.
- [ ] Focused tests, API-level BDD, browser acceptance, and `pnpm verify:slice` pass before closeout.
- [ ] Relevant docs are updated: `requirements/roadmap.md`, `docs/user-guide.md`, this slice document, `architecture/parking-lot.md`, and `requirements/ai-sdlc-observations.md`.

## Open Questions

- None after Slice 0024 grilling and acceptance scenario signoff.
