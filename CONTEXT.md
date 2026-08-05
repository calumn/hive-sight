# HiveSight

HiveSight is a Varroa-focused inspection support system for hobbyist and small-scale beekeepers. The registered product domain is hive-sight.com. This glossary defines the project language used across requirements, architecture, tests, and future implementation.

## Language

### Beekeeping Context

**User**:
A registered login identity that can authenticate and be authorized to act in one or more workspaces.
_Avoid_: Beekeeper when the point is login, registration, authentication, or identity.

**Development User**:
A seeded local testing User used by HiveSight's development stack to simulate logging in as a distinct identity. Development Users have stable User ids, display codes, Workspaces, Workspace Memberships, and capabilities. Switching Development User is a local QA tool and is not real authentication, not a product role, and not a security boundary.
_Avoid_: Role switcher when the point is selecting a different User identity.

**Workspace**:
The ownership boundary for apiaries, hives, inspections, photos, corrections, and model-use terms.
_Avoid_: Account when the ownership container, not login identity, is the point.

**Workspace Membership**:
The relationship that gives a User access to a Workspace with a role. Version one supports a single `owner` membership created during registration.
_Avoid_: User ownership when the relationship between identity and workspace is meant.

**Contributor Contribution Permission**:
A registered contributor's explicit permission for their identified image, annotation, or review contribution to support model-data curation. It is distinct from the Workspace Data Use Agreement and can be withdrawn by that contributor through their own HiveSight identity.
_Avoid_: Workspace agreement when the permission belongs to a helper rather than the Workspace owner.

**Contribution Bundle**:
A named, immutable collection of one contributor's identified images, annotations, or reviews covered by one Contributor Contribution Permission. Every included Dataset Item retains the bundle reference.
_Avoid_: Dataset Version when referring to the contributor's consent boundary rather than a frozen training selection.

In the first release, withdrawal applies to the whole Contribution Bundle. A contributor who wants distinct withdrawal boundaries creates distinct bundles before accepting permission.

**Contributor Access Scope**:
The narrowly assigned annotation tasks and Contribution Bundles a contributor may view or work on. It never grants general access to a Workspace, its inspections, or another contributor's evidence.
_Avoid_: Workspace Membership when the access exists only for an assigned contribution.

**Contributor Pseudonym**:
The contributor-selected display identity used in contribution provenance and curator-facing views. It does not require disclosure of the contributor's real name to a Workspace owner or other contributors.
_Avoid_: Legal name when the system needs only an accountable HiveSight identity.

**Contribution Usage Record**:
A contributor-visible, read-only account of a Contribution Bundle's accepted terms, permission/deletion status, and derived Dataset Versions, Training Runs, and model artifacts. It does not reveal other contributors' evidence or the wider Workspace.
_Avoid_: Dataset lineage when the view is specifically the contributor's transparent account of use.

**Beekeeper**:
A beekeeping actor or persona who records inspections or reviews analysis results. In version one, the registered User with the owner Workspace Membership acts as the primary Beekeeper.
_Avoid_: User when the point is beekeeping work rather than login identity.

**Apiary**:
A beekeeper-defined grouping or location that contains hives.
_Avoid_: Site, yard, location unless specifically referring to geography.

**Hive**:
An individual managed colony record within an apiary.
_Avoid_: Colony when referring to the system record rather than the biological colony.

**Hive Configuration**:
The beekeeper-recorded equipment context for a Hive, such as hive type, box use, and expected frame standard.
_Avoid_: Hive Type when the point includes more than the named hive family.

**Frame Standard**:
The expected physical frame dimensions for a Hive Configuration and frame use, such as brood, super, or extra deep.
_Avoid_: Frame Label when referring to physical equipment dimensions rather than grouping photos.

**Inspection**:
A dated review of one hive, containing photos and analysis evidence.
_Avoid_: Inspection event, visit, session.

**Inspection Intent**:
The declared purpose of an Inspection, such as training data collection or Varroa assessment. One Inspection has one intent and must not mix dataset-building and product-assessment workflows.
_Avoid_: Mode when the domain purpose of the inspection is meant.

**Training Data Collection**:
An Inspection Intent for gathering reviewed image and annotation evidence to improve HiveSight models.
_Avoid_: Real inspection when the purpose is dataset creation rather than beekeeper assessment.

**Training Inspection Workflow**:
The staged Web UI workflow used for a Training Data Collection Inspection. Its current stages are Inspection Setup, Crop Selection, Bee Annotation, Crop Governance, Varroa Review, and Model Governance. Stage changes are navigation only; saved photos, crops, ellipses, Varroa review cues, Varroa Review Outcomes, review requests, Dataset Items, Dataset Versions, Training Runs, Model Candidates, and Benchmark Evaluations remain the durable state.
_Avoid_: Treating the selected UI stage as domain state or persisted inspection status.

**Crop Governance**:
The Training Inspection Workflow stage where a Dataset Curator reviews the selected Inspection's completed Training Crops, requests independent review, cancels pending review requests, assigns Dataset Roles, and sees why governance actions are unavailable.
_Avoid_: Bee Annotation when the actor is governing completed crop evidence rather than drawing or editing ellipses.

**Model Governance**:
The Training Inspection Workflow stage where a Dataset Curator checks workspace-level dataset readiness, creates shared Marked-Bee Dataset Versions, starts Bee Detector and Bee Orientation Training Runs, selects Bee Detector Model Candidates for crop pre-labelling, and runs Benchmark Evaluations. It operates across Dataset Items rather than one selected Training Crop.
_Avoid_: Crop Governance when the actor is governing cross-crop model evidence rather than one crop's review or Dataset Role assignment.

**Varroa Review**:
The Training Inspection Workflow stage where a Dataset Curator reviews one eligible Head-Up Normalized Bee Crop at a time and records a Varroa Review Outcome with marker evidence when visible Varroa is present. In Slice 0025 this is model-curation evidence only, scoped to the selected Training Crop; it is not a beekeeper-facing Varroa Assessment, Sampling Plan, Dataset Role assignment, or treatment trigger.
_Avoid_: Varroa Assessment when the work is internal model-curation labelling.

**Varroa Corpus Governance**:
The Model Governance work where a Dataset Curator reviews saved Varroa Review Outcomes across the Workspace and records whether each outcome is included, excluded, or deferred for the first Varroa Detection model-curation corpus. It operates across Training Crops and keeps positive, active negative, unresolved, stale, and quality-warning evidence separate.
_Avoid_: Varroa Review when the actor is labelling one bee-relative crop rather than governing corpus membership.

**Varroa Corpus Curation Decision**:
A Dataset Curator's current decision about whether one Varroa Review Outcome may contribute to the Varroa model-curation corpus: `included`, `excluded`, or `deferred`. It preserves the original Varroa Review Outcome and records the corpus decision separately.
_Avoid_: Dataset Version when the evidence has not yet been frozen for training, validation, or benchmark use.

**Varroa Assessment**:
An Inspection Intent for estimating visible Varroa evidence from inspection photos for beekeeper-facing support.
_Avoid_: Training data collection when the purpose is product analysis.

**Treatment Recommendation**:
An advisory suggestion for managing a Hive health concern, such as Varroa, that has not yet been accepted or applied by the Beekeeper.
_Avoid_: Treatment Course when the recommendation is not yet the beekeeper's own treatment record.

**Hive Treatment Course**:
A beekeeper-owned treatment plan or record for one Hive, covering the intended purpose and lifecycle of a treatment from planning through completion or cancellation.
_Avoid_: Treatment Recommendation when the beekeeper has not accepted responsibility for carrying out or recording the treatment.

**Treatment Application**:
One dated application or dose within a Hive Treatment Course.
_Avoid_: Treatment Course when referring to a single event in a multi-step schedule.

**Treatment Outcome**:
The beekeeper-recorded or inspection-supported result observed after a Hive Treatment Course.
_Avoid_: Cure, success, diagnosis.

**Frame Label**:
An optional label that groups photos believed to show the same frame during one inspection.
_Avoid_: Frame record, frame inventory.

**Source Image**:
The underlying original image evidence record used by inspection, dataset, and model-governance workflows. In Slice 0014, every Source Image is an Inspection Photo source image. Later, imported, public, or bootstrap Source Images may exist outside the inspection workflow.
_Avoid_: Inspection Photo when referring to image file evidence that may later come from non-inspection sources.

**Source Rights Record**:
The recorded provenance and licence or other lawful-use basis for a Source Image, such as a public/open dataset licence, a Workspace Data Use Agreement, or a Contributor Contribution Permission. It is separate from annotation provenance.
_Avoid_: Contributor permission when use is instead authorised by a public/open licence.

Required attribution travels with the relevant Dataset Version, export, evaluation report, and released model documentation.

Public/open source does not imply permission for user-facing deployment, sharing/publication, or commercial use. Those uses require explicit Permitted Use Scopes on an approved Source Rights Record.

**Permitted Use Scope**:
An explicitly authorised purpose for evidence, such as model development, evaluation, user-facing deployment, sharing/publication, or commercial use. An unlisted use is not permitted.
_Avoid_: General model use when the permitted purpose is the important boundary.

**Inspection Photo**:
The beekeeper/product-facing role a Source Image plays when it is attached to an Inspection.
_Avoid_: Source Image when the product workflow context of an inspection upload is meant.

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

**Not Assessed For Varroa**:
An explicit outcome for a localised bee that the first Varroa pipeline did not evaluate because required orientation was unreliable. It is not evidence that no mite is visible.
_Avoid_: No Varroa, negative result.

**Varroa Review Outcome**:
A human judgement about one bee-relative crop: `visible_varroa_present`, `no_visible_varroa`, or `not_determined`. `no_visible_varroa` is an active negative judgement; `not_determined` is not a negative result.
_Avoid_: No annotation when the absence of a marker has not been reviewed.

**Varroa Marker**:
A human-placed point marker identifying a visible Varroa mite location within a Head-Up Normalized Bee Crop. In Slice 0025 markers use normalized 0-1 crop coordinates and belong to a Varroa Review Outcome.
_Avoid_: Bee-level positive when the exact visible mite location is required.

**Blind Independent Review**:
A second review performed without showing the first reviewer's outcome or Varroa marker positions. Disagreement is resolved through a documented adjudication outcome.
_Avoid_: A second click after seeing the first review.

**Third-Party Adjudication**:
Resolution of a disagreement between two Blind Independent Reviews by a third reviewer who did not perform either original review. The adjudicator records a fresh blind judgement before seeing anonymised prior reviews and recording the final outcome. If the disagreement remains unresolved, the canonical outcome is `not_determined`.
_Avoid_: One original reviewer deciding their own disagreement.

**Review Agreement Metrics**:
Reported evidence of how consistently Varroa reviewers agree on outcomes and marker locations, including the count of items without independent second review. Marker-location agreement uses one-to-one matched markers in bee-relative coordinates; unmatched markers are reported separately. Audit results are separated by Annotation Source, including human-from-scratch and AI-assisted-reviewed evidence.
_Avoid_: Treating a model score as meaningful without showing the reliability of its benchmark labels.

**Audit Disposition**:
A Dataset Curator's recorded decision about a quality-audit concern and its effect on a Dataset Version. A Model Approver must acknowledge it when promoting a candidate that relies on the affected version.
_Avoid_: An unrecorded acknowledgement of a warning.

**Visible Varroa Rate**:
The stated photo-visible estimate of likely Varroa markers associated with eligible complete visible bees per 100 eligible complete visible bees in the photographed frame evidence. It records whether the evidence was full-depth or sampled, the sampling-plan version, assessment coverage, and uncertainty. It is not a diagnosis, colony-level rate, or alcohol-wash result.
_Avoid_: Infestation rate, diagnosis, colony-level rate.

**Varroa Sampling Plan**:
A versioned, predeclared protocol that defines the target population, sampling unit, strata, selection method, inclusion and exclusion rules, randomization, stopping rule, estimator, and uncertainty method for either model curation or inspection-rate estimation.
_Avoid_: A generic dataset filter when probability selection or a reported rate is meant.

**Model-Curation Sample**:
Bee-relative evidence selected to make Varroa Detector training, validation, or benchmark data informative. It may combine representative probability-selected evidence with deliberately enriched positive or difficult evidence, and is not by itself a prevalence sample.
_Avoid_: Inspection-Rate Sample when the sample is used to state a beekeeper-facing rate.

**Inspection-Rate Sample**:
A probability-selected set of eligible complete bees from one declared photographed frame population, used with its Varroa Sampling Plan to estimate a Visible Varroa Rate. It is not a claim about the whole colony.
_Avoid_: Model-Curation Sample, alcohol wash sample.

**Gold-Standard Full-Frame Corpus**:
A protected collection of whole-frame source images in which every in-scope visible bee is reconciled, orientation-reviewed, and given an explicit Varroa Review Outcome with marker evidence where present. It supports end-to-end evaluation, sampling-strategy experiments, and calibration; it is separate from model development and routine tuning.
_Avoid_: A large positive-enriched training set.

**Field Reference Measurement**:
An independently recorded colony or hive measurement, such as an alcohol-wash mite count, retained for calibration research. It measures a related but different target from photo-visible Varroa evidence and must not be treated as photo-label ground truth.
_Avoid_: Gold-standard photo annotation.

**Human-Reviewed Inspection Result**:
A separately provenanced inspection result calculated after a human recovery review. The reviewer may resolve previously unassessed bees and correct any model-produced bee, orientation, or Varroa decision. The latest completed revision is the inspection's current result by default. It carries its own assessment coverage and is suppressed when that coverage remains inadequate. It is shown alongside, not instead of, the immutable original model-only result.
_Avoid_: Overwriting the model-only result.

**Review Completion**:
The proportion of in-scope bees for which a reviewer has recorded an explicit outcome, including `not_determined`.
_Avoid_: Determinate Varroa Coverage.

**Determinate Varroa Coverage**:
The proportion of in-scope bees with a positive or active negative Varroa outcome. `not_determined` does not contribute to it and cannot support a Visible Varroa Rate.
_Avoid_: Review Completion.

**Result Evidence Breakdown**:
The counts behind an inspection result: positive, active negative, `not_determined`, and unassessed complete visible bees, shown with Review Completion and Determinate Varroa Coverage.
_Avoid_: A bare percentage with no explanation of its evidence.

**Inspection Recovery Review**:
A distinct, named, saveable, and resumable human review session for recovering or correcting a fixed snapshot of a model-only inspection result and its photo evidence. Its evidence is always reported as AI-assisted-reviewed because the model output was visible. It remains available for an owner’s retained inspection after data-use withdrawal but cannot contribute to model improvement without an active agreement and independent curation. In the first release, only the Workspace owner may create, resume, or complete it. The owner may complete it at any coverage level after explicit confirmation. Once completed it is immutable; a later correction starts a new linked review and result revision.
_Avoid_: An unstructured collection of edits with no review provenance.

Recovery evidence created while the Workspace Data Use Agreement is withdrawn remains product-only. A later agreement is prospective; model use requires a separate explicit dataset-contribution decision and independent curation.

**Dataset Contribution Decision**:
An explicit Workspace owner decision allowing one named completed recovery-result revision to be considered for model-data curation. It is not a workspace-wide opt-in and does not itself assign a Dataset Role.
_Avoid_: Treating agreement acceptance as permission to use all retained evidence.

**Contribution Withdrawal**:
A contributor's withdrawal of permission for their training contribution to support future model use. It withdraws affected Dataset Items, quarantines affected Dataset Versions and model artifacts, and requires a replacement trained without the contribution before future use resumes.
_Avoid_: Treating withdrawal as merely a future-upload preference.

**Historical Reanalysis**:
An explicit request to analyse an existing Inspection Photo with a newer model. It creates a new model-only result and never rewrites earlier model-only or human-reviewed results.
_Avoid_: Automatic reanalysis after model promotion.

**Tagged Photo**:
A rendered view of an inspection photo with annotation overlays.
_Avoid_: Annotated original when the original file is unchanged.

### Review And Model Governance

**Annotation**:
Structured marker data that can be rendered over an inspection photo.
_Avoid_: Label when the distinction from review status matters.

**Oriented Bee Ellipse**:
The canonical reviewed geometry for a visible bee, represented by center point, two radii, and directed body-axis rotation. The rotation points from the ellipse center toward the bee's head along the major axis; the opposite end is the tail.
_Avoid_: Bounding box when the human-reviewed bee shape and orientation are meant.

**Orientation Reliability**:
The reviewed assessment of whether a Bee Annotation's directed head/tail orientation is trustworthy: `reliable` or `unreliable`.
_Avoid_: Confidence when the value is about head/tail direction rather than whether a bee is present.

**Varroa Review Suitability**:
A lightweight Bee Annotation triage cue recorded during bee annotation to say whether the bee appears assessable for visible Varroa review: `unassessed`, `appears_assessable`, or `body_occluded_or_hard_to_assess`. It helps prioritise and warn during Varroa Review; it is not itself a Varroa Review Outcome and does not override Slice 0025 eligibility rules.
_Avoid_: Varroa Review Outcome when no active mite review has been saved.

**Suspected Visible Varroa Cue**:
A lightweight Bee Annotation triage flag set when the annotator notices possible visible Varroa while annotating bees. It helps pull the bee forward in Varroa Review, but it is not ground truth, not a positive Varroa Review Outcome, and does not make an ineligible bee eligible for the first Varroa corpus.
_Avoid_: visible_varroa_present when the bee-relative crop has not been actively reviewed and marked.

**Candidate Annotation**:
A proposed Annotation awaiting human review. It may come from a model candidate, imported public dataset, previous draft, or future helper.
_Avoid_: AI guess, pre-label, ground truth, reviewed label.

**Draft Annotation**:
A historical or implementation-facing term for a proposed Annotation before human review. Prefer Candidate Annotation in new product, architecture, and API language.
_Avoid_: Ground truth, reviewed label.

**Reviewed Annotation**:
An Annotation that has been accepted by a human Review Decision for its current type and geometry.
_Avoid_: Training data unless a Dataset Role has also been assigned.

**Annotation Source**:
The provenance of an Annotation or Candidate Annotation, such as human-from-scratch, model candidate, imported public dataset, user correction, or reviewer correction.
_Avoid_: Source when referring only to storage location or file path.

**Review Method**:
How reviewed annotation evidence was produced, such as human from scratch, human reviewed candidate, or imported reviewed.
_Avoid_: Annotation Source when the point is the human review path rather than the original proposal source.

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
A tracked request to delete or purge workspace-held data or a contributor's own Contribution Bundle.
_Avoid_: Consent withdrawal when the user is asking for deletion rather than stopping future use.

**Model Version**:
A named version of the model or model pipeline that produced analysis output.
_Avoid_: Model when traceability to output matters.

**Model Purpose**:
The logical role a model serves: Bee Localisation, Bee Orientation, or Varroa Detection. A Model Purpose is independent of the particular model family used to implement it.
_Avoid_: Model type when the point is product/domain role rather than implementation family.

**Dataset Version**:
A named version of a dataset used for training, validation, or benchmark evaluation.
A Dataset Version freezes governed source evidence. For marked oriented-bee evidence, the same Dataset Version is the source for Bee Localisation and Bee Orientation projections; model-specific exports may differ, but the promoted source dataset must stay in lockstep.
_Avoid_: Dataset when traceability to an evaluation matters. Avoid separate YOLO dataset and orientation dataset when both are projections of the same marked oriented-bee evidence.

**Dataset Item**:
A reviewed image-and-annotation unit assigned to a Dataset Role and eligible for inclusion in a Dataset Version.
_Avoid_: Photo when the dataset eligibility decision is meant.

**Dataset Selection Method**:
The provenance of how an item was chosen for a dataset. `human_selected` means the curator selected it before seeing upstream model suggestions; `upstream_model_selected` means any upstream model output influenced selection. It is distinct from Annotation Source and Review Method.
_Avoid_: Annotation source when the point is why the crop was chosen rather than who proposed its labels.

**Sampling Purpose**:
The statistical purpose of a set of Varroa reviews: `model_curation` builds representative training or benchmark evidence, while `inspection_rate_estimation` supports a future rate estimate with a stated sampling plan.
_Avoid_: Dataset role when the point is the statistical goal rather than eligibility for a particular model split.

**Sampling Method**:
How a Varroa review was selected within its Sampling Purpose. The first model-curation methods are `stratified_random` and `curator_targeted` for deliberately added difficult examples.
_Avoid_: Dataset Selection Method when the question is random/stratified versus targeted selection within an already-defined population.

**Bee Annotation Repository**:
The growing set of reviewed bee annotation evidence, including Source Images, crop provenance, canonical oriented bee ellipses, and dataset roles.
_Avoid_: Training set when validation, benchmark, excluded, or unassigned reviewed evidence is also included.

**Training Crop**:
A cropped region from a Source Image used for manageable bee annotation and curriculum training.
_Avoid_: Photo when the dataset item is a crop derived from a larger Source Image.

**Curriculum Stage**:
The training-data difficulty stage for an image or crop, such as small crop, medium crop, large crop, full-frame region, or full-frame side.
_Avoid_: Dataset split when the point is annotation difficulty rather than training/validation/benchmark role.

**Dataset Curator**:
A registered User with internal dataset/model governance capability who can perform dataset labelling, annotation review, dataset role assignment, and model-governance work.
_Avoid_: Beekeeper when the actor is doing internal dataset/model governance work.

**Internal Capability**:
An authorization grant separate from ordinary Workspace Membership, used for internal workflows such as annotation review, dataset curation, model review, or model approval.
_Avoid_: Workspace role when the permission is not tied to ordinary Workspace access.

**Dataset Role**:
The approved use of reviewed data: training, validation, benchmark, or excluded.
_Avoid_: Data split when governance status is meant.

**Training Run**:
A recorded execution that trains or fine-tunes a Model Candidate using specified Dataset Versions and training settings.
_Avoid_: Experiment when traceability to a model artifact is required.

**Model Candidate**:
A model or model pipeline version under evaluation before approval for user-facing analysis.
_Avoid_: Model Version when release approval status matters.

**HiveSight Bee Detector**:
The project-owned model used to propose bee Candidate Annotations. The first version implements the Bee Localisation Model; its output must be human reviewed before entering the Bee Annotation Repository as trusted evidence.
_Avoid_: Grounding DINO when referring to the intended trainable HiveSight model.

**Bee Localisation Model**:
The model purpose that finds visible bees and estimates their body geometry in a frame or crop. It does not by itself establish which end of the body is the head.
_Avoid_: Bee orientation model, Varroa detector.

**Bee Orientation Model**:
The model purpose that determines the head/tail direction of a localised bee. The first planned implementation is a classifier that decides whether a body-axis-normalized bee crop is `head_up` or `head_down`, so downstream crops can be normalized with the bee's head at the top.
_Avoid_: Oriented bounding-box rotation when biological head direction is meant.

**Head-Up Normalized Bee Crop**:
A bee-relative image crop rotated so the bee's head is at the top of the crop. It is the intended input convention for Varroa Detection when Bee Orientation is reliable. In Slice 0025 it is generated on demand as a review image and coordinate frame from source image bytes, Training Crop geometry, a reliable complete Bee Annotation, and transform metadata; it is not yet stored as a standalone derived image artifact.
_Avoid_: Oriented crop when the direction of the bee's head is the important convention.

**Varroa Detector**:
The future model purpose for detecting likely visible Varroa mites on or near a bee, preferably from a Head-Up Normalized Bee Crop.
_Avoid_: Mite Detector when the intended product scope is specifically Varroa.

**YOLO OBB**:
The first selected model-family baseline for the HiveSight Bee Detector's Bee Localisation Model, using oriented bounding boxes exported from canonical oriented bee ellipses. Its geometric rotation does not carry biological head/tail direction.
_Avoid_: Canonical annotation geometry when referring to the model-specific training label format.

**Pre-Labelling Model Version**:
The model version that generated Candidate Annotations for human review during dataset labelling.
_Avoid_: Model Version without specifying that it is used for pre-labelling rather than user-facing analysis.

**Benchmark Evaluation**:
A documented evaluation of one Model Candidate, for one Model Purpose, against one protected benchmark dataset version or selection snapshot.
_Avoid_: Test run, accuracy check.

**End-to-End Pipeline Evaluation**:
A protected evaluation of the composed Bee Localisation, Bee Orientation, and Varroa Detection pipeline against a separate full-frame selection snapshot, frozen before candidate selection or tuning, with complete human-reviewed bee, orientation-reliability, and relevant Varroa evidence.
_Avoid_: A single-model benchmark when the question is real workflow performance.
