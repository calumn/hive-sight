# Varroa Evidence Methodology

Status: proposed research and governance protocol

## Purpose

This document defines how HiveSight will construct Varroa evidence, train and validate its staged models, and determine whether a sampled photo-based result is useful enough to present to a beekeeper.

It is deliberately separate from a model implementation plan. A detector can be trained on an informative, positive-enriched corpus. A beekeeper-facing rate, by contrast, needs probability sampling, an explicit target population, and quantified uncertainty. The same labelled bee crop may support both activities, but its selection purpose must never be lost.

The governing requirements are MR-018C through MR-018J and MR-030A in `requirements/model-requirements.md`.

## Core Claims And Boundaries

HiveSight has three connected but distinct evidence questions:

| Question | Evidence needed | What it can support |
| --- | --- | --- |
| Can the Varroa Detector find visible mites on an eligible Head-Up Normalized Bee Crop? | Informative labelled crops, including positives, hard negatives, and representative negatives. | Detector development and component evaluation. |
| Does the combined localisation, orientation, and Varroa pipeline work across a real frame? | Protected full-depth whole-frame evidence. | End-to-end coverage, error, and model-promotion evidence. |
| What photo-visible mite burden is plausible in this declared photographed frame population? | A probability-selected Inspection-Rate Sample and its Sampling Plan. | A caveated photo-visible estimate with uncertainty. |

The initial user-facing target, if eventually supported, is:

> Estimated visible Varroa marker burden per 100 eligible complete visible bees in the declared photographed frame evidence.

HiveSight may additionally report the estimated proportion of eligible complete bees with one or more visible markers. These are different measures: one bee can have more than one marker.

Neither measure is a diagnosis, a whole-colony infestation rate, or an alcohol-wash result. A photograph samples visible bees in a particular visual context; an alcohol wash samples a different population at a different time and with different detection properties.

## Evidence Architecture

### 1. Model-Curation Corpus

This corpus makes the Varroa Detector learn effectively. It has two deliberately labelled streams:

- **Representative stream:** probability-selected eligible bees across predefined frame region, hive, inspection, image quality, bee density, orientation, and source-camera strata. It supplies ordinary negatives and real nuisance variation.
- **Positive-enrichment stream:** curator-targeted or later model-assisted candidates, high-burden inspections, and difficult plausible false positives. It supplies the rare positive examples and hard negatives a detector needs.

Positive enrichment is desirable for training efficiency. Its class balance must never be used to infer field prevalence. Every item records `human_selected` or `upstream_model_selected`, plus its curation stream and stratum values.

Training, validation, component benchmarks, and the Gold-Standard Full-Frame Corpus are split by source group, not merely by crop or image. Near-duplicate or overlapping images of the same physical frame must remain in the same partition.

### 2. Gold-Standard Full-Frame Corpus

The Gold-Standard Full-Frame Corpus is small, protected, full-depth evidence. It establishes the reference result against which sampling and the composed pipeline are measured.

For every included source frame:

1. Reconcile every in-scope physical bee at source-frame level. Do not treat crop-edge fragments or overlapping crops as separate bees.
2. Record complete, partial, and uncertain visibility classes.
3. Record the directed Oriented Bee Ellipse and Orientation Reliability for every localised bee where it can be assessed.
4. For every eligible complete bee, record one explicit Varroa Review Outcome: `visible_varroa_present`, `no_visible_varroa`, or `not_determined`.
5. Record a point marker or tight bounding box for every visible mite outcome.
6. Retain `not_determined`, incomplete, and orientation-unreliable evidence as explicit coverage limits rather than converting them to negatives.

The corpus must span independent hives and inspections, low/medium/high apparent visible burden, dense and sparse frames, lighting, image quality, equipment context, and capture devices where available. These are coverage targets, not quotas that justify cherry-picking easy or dramatic frames.

An initial planning target is a pilot of roughly 8-12 full-depth frames to measure annotation workload, agreement, duplicate-reconciliation difficulty, and the first sampling simulations. Only after that pilot should the project freeze a larger protected corpus, provisionally on the order of 20-40 independent full-depth frames. The final count is a decision based on observed variation, independence across hives and inspections, review agreement, and the precision required for the operational decisions, not an arbitrary image total.

The corpus has two protected uses which must be separately frozen:

- **Development calibration set:** used during the sampling-plan study and clearly identified as such. It cannot become the final untouched promotion set after repeated decisions have been made from it.
- **Locked end-to-end set:** source-group disjoint from all development, calibration, component benchmark, and training data. It is used once to confirm the selected pipeline and sampling policy before any user-facing claim.

### 3. Field Reference Cohort

Where feasible, a subset of inspections can be paired prospectively with a Field Reference Measurement, such as a recorded alcohol-wash result. The record must include method, date/time, hive, bee population sampled, sample size, units, observer/provenance, and the temporal relation to photography.

This cohort answers a calibration question: how does HiveSight's photo-visible measure relate to a practical field measurement under stated capture conditions? It does not relabel photos and does not allow the project to describe image results as an alcohol wash or colony-wide infestation rate.

## Full-Depth Annotation And Review Protocol

### Selection Before Annotation

Select candidate full-frame images from a predeclared frame-level plan before reviewing the labels. Record inclusion and exclusion reasons, source-group key, frame identity, capture date, inspection/hive context, known field-reference availability, expected density/quality stratum, and whether a near-duplicate exists.

The plan may use an external field observation to seek burden diversity, but it may not promote a frame into the corpus because a model later succeeds or fails on it.

### Annotation Sequence

1. One annotator creates or corrects full-frame bee evidence and directed head geometry.
2. A qualified reviewer independently reviews the Varroa outcome and marker location without seeing the first Varroa outcome or markers.
3. A disagreement receives Third-Party Adjudication according to the established blind-review rule.
4. An unresolved case remains `not_determined`; it is not a negative and is excluded from detector negative labels and determinate rate calculations.
5. Freeze the full-frame record, review provenance, source rights, contribution permissions, and methodology version before it enters a protected use.

The pilot may use one active review to establish feasibility, but its reports must label that limitation. Evidence used for a user-facing promotion claim follows MR-018E: Blind Independent Review and adjudication.

## Inspection-Rate Sampling Methodology

### Population And Sampling Unit

The initial population is the set of eligible complete visible bees in one declared photographed frame population. A frame label is not enough to aggregate multiple photographs: overlapping or duplicate views must be reconciled first. Until then, each analysis result is framed as evidence from one source frame/photo rather than a whole inspection or colony.

The sampling unit is one eligible Head-Up Normalized Bee Crop. A selected bee that cannot be assessed remains in the sample and records why; replacing it silently would bias the result.

### Candidate Designs

The first experiment compares, on the full-depth reference frames:

- simple random sampling of eligible bees;
- spatially stratified random sampling over occupied frame regions;
- spatial plus quality-stratified random sampling, if quality attributes prove reliable;
- fixed sample sizes such as 25, 50, 100, 150, 200, and 300;
- predeclared sequential versions that sample in batches and stop only on rules fixed before the draw.

Sequential stopping is promising, but it is not assumed safe by default. Its decision and interval properties must be simulated and reported. The stopping rule cannot be tuned on the locked end-to-end set.

### Estimation And Reporting

For an equal-probability fixed sample, the initial estimator can scale observed visible marker counts and mite-positive-bee counts by the sampled eligible-bee denominator. For unequal strata, the estimator must account for each bee's selection probability; HiveSight should not average stratum rates without their population weights.

Every experimental and eventual product result records:

- the Sampling Plan version and target population;
- total detected, eligible, selected, completed, excluded, unassessed, determinate-negative, mite-positive, and visible-marker counts;
- strata and selection probabilities or allocation rule;
- estimate(s), interval method, interval, and any threshold decision;
- model/pipeline versions, source-frame identity, and image-quality warnings.

The headline remains suppressed when declared coverage or precision rules are not met. Those numerical rules are deferred until the pilot and gold-standard experiment show what is achievable.

## Sampling-Plan Experiment

For every full-depth reference frame, repeatedly simulate each candidate plan using recorded random seeds. Compare the sampled estimate to the frame's full-depth value.

Required outputs:

- absolute and relative error for visible marker burden and mite-positive-bee rate;
- probability of seeing no positives when the full-depth frame contains positives;
- interval coverage and width;
- wrong-side-of-threshold probability for each proposed operational threshold;
- variation over repeated draws;
- unusable/indeterminate crop rate and stage-specific loss;
- compute time and human-review effort;
- outcomes by burden, density, lighting, image quality, Hive Configuration, and source group, with sparse-group warnings.

The output is a versioned research report, not merely a dashboard. It recommends a production candidate plan only when it states the trade-off it makes between speed, low-burden sensitivity, uncertainty, and coverage. The locked end-to-end set then evaluates that chosen policy once, without hindsight tuning.

## Model Training And Validation Sequence

1. Implement Varroa Review Outcome labelling and marker provenance.
2. Run the full-depth annotation pilot and publish its feasibility/agreement report.
3. Freeze the development calibration and locked end-to-end source-group partitions.
4. Construct representative and positive-enriched model-curation streams under the approved protocol.
5. Train and evaluate the Varroa Detector on its own protected component benchmark.
6. Run composed-pipeline evaluation on full-depth frames, including localisation and orientation losses.
7. Use sampling simulations to choose the initial rate-estimation policy.
8. Confirm the fixed pipeline and policy on the locked end-to-end set.
9. Only then consider a caveated model-only assessment result and, later, paired field-reference calibration work.

This sequence avoids a familiar trap: treating high detector precision on hand-selected bee crops as proof that a frame-level or beekeeper-facing estimate is accurate.

## Reproducibility And Governance

Every corpus selection, annotation package, review round, simulation, Dataset Version, model run, benchmark, and end-to-end evaluation retains:

- protocol/methodology version;
- source-group split and duplicate-handling decision;
- sampling-plan manifest, allocation, seed, and achieved sample;
- annotation, review, adjudication, and selection provenance;
- source rights, contribution permission, and permitted-use status;
- code, model, artifact, and environment identities;
- exclusions and the reason each item could not contribute.

No protected evidence is added because a candidate's result is attractive or disappointing. A methodology change produces a new plan and a new frozen selection; it never rewrites an earlier report.

## Explicit Non-Claims

Until the sequence above has been completed, HiveSight does not claim:

- an accurate colony-wide mite prevalence or official infestation measurement;
- equivalence to an alcohol wash;
- a production-safe sample size, sequential stopping rule, or treatment threshold;
- that all visible bees on a multi-photo inspection are unique physical bees;
- that a detector's enriched-training score represents real-world prevalence or inspection accuracy.

## Open Decisions For Slice Planning

- Which frame-level strata can be captured reliably enough to drive selection and reporting?
- Which minimum review strength is practical for the pilot, and when does every gold-standard frame move to blind independent review?
- What operational decision thresholds should the simulation assess before any are shown to a beekeeper?
- Which field-reference method and capture-time window are acceptable for a prospective calibration cohort?
- What precision and coverage evidence would justify presenting a sampled photo-visible result rather than a tagged-evidence-only result?
