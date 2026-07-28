# BeehiveMonitor

BeehiveMonitor is a Varroa-focused inspection support system for hobbyist and small-scale beekeepers. This glossary defines the project language used across requirements, architecture, tests, and future implementation.

## Language

### Beekeeping Context

**Workspace**:
The ownership boundary for apiaries, hives, inspections, photos, corrections, and model-use terms.
_Avoid_: Account when the ownership container, not login identity, is the point.

**Beekeeper**:
A person who keeps bees and uses the workspace to record inspections or review analysis results.
_Avoid_: Workspace when referring to the human actor.

**Apiary**:
A beekeeper-defined grouping or location that contains hives.
_Avoid_: Site, yard, location unless specifically referring to geography.

**Hive**:
An individual managed colony record within an apiary.
_Avoid_: Colony when referring to the system record rather than the biological colony.

**Inspection**:
A dated review of one hive, containing photos and analysis evidence.
_Avoid_: Inspection event, visit, session.

**Frame Label**:
An optional label that groups photos believed to show the same frame during one inspection.
_Avoid_: Frame record, frame inventory.

**Inspection Photo**:
An original uploaded image associated with one inspection.
_Avoid_: Image when the original uploaded inspection evidence is meant.

### Analysis Evidence

**Analysis Result**:
Model output for one inspection photo, including counts, quality status, and annotation references.
_Avoid_: Diagnosis, assessment when referring to raw model output.

**Inspection Summary**:
A derived roll-up across one inspection's photo analysis results.
_Avoid_: Hive health score, infestation diagnosis.

**Complete Visible Bee**:
A visible bee with enough of the body shown to count confidently as one bee.
_Avoid_: Bee when denominator precision matters.

**Partial Visible Bee**:
A bee that is visible but occluded, cropped, overlapped, or only partly in frame.
_Avoid_: Half bee.

**Uncertain Bee**:
A possible bee that is not reliable enough for confident counting.
_Avoid_: Maybe bee.

**Likely Varroa Detection**:
A model or reviewed marker for a visible Varroa mite on or near a bee.
_Avoid_: Confirmed mite, infection.

**Visible Varroa Rate**:
The photo-visible estimate of likely Varroa detections associated with complete visible bees per 100 estimated complete visible bees.
_Avoid_: Infestation rate, diagnosis, colony-level rate.

**Tagged Photo**:
A rendered view of an inspection photo with annotation overlays.
_Avoid_: Annotated original when the original file is unchanged.

### Review And Model Governance

**Annotation**:
Structured marker data that can be rendered over an inspection photo.
_Avoid_: Label when the distinction from review status matters.

**User Correction**:
A beekeeper flag that marks a model annotation as wrong or marks a missed likely Varroa location.
_Avoid_: Ground truth, training label.

**Review Decision**:
A human decision about whether a prediction, correction, annotation, or model release is approved, rejected, uncertain, excluded, or eligible for dataset use.
_Avoid_: Approval when the exact decision status matters.

**Workspace Data Use Agreement**:
A workspace-level acceptance of the service's data-use terms, required in version one before upload and analysis features can be used.
_Avoid_: Consent record when referring to the service-level agreement.

**Data Deletion Request**:
A request to delete or purge workspace-held data.
_Avoid_: Consent withdrawal when the user is asking for deletion rather than stopping future use.

**Model Version**:
A named version of the model or model pipeline that produced analysis output.
_Avoid_: Model when traceability to output matters.

**Dataset Version**:
A named version of a dataset used for training, validation, or benchmark evaluation.
_Avoid_: Dataset when traceability to an evaluation matters.

**Dataset Role**:
The approved use of reviewed data: training, validation, benchmark, or excluded.
_Avoid_: Data split when governance status is meant.

**Benchmark Evaluation**:
A documented evaluation of one model version against one protected benchmark dataset version.
_Avoid_: Test run, accuracy check.
