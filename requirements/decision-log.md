# Decision Log

## 2026-08-06 Treatment Recommendation And Treatment Course Are Separate Records

Decision: HiveSight will store a HiveSight Advisor response as a Treatment Recommendation and will store beekeeper-owned treatment activity as a separate Hive Treatment Course with one or more Treatment Applications. Accepting a recommendation may create a linked planned Hive Treatment Course, but the recommendation itself does not become the treatment record and the planned course does not imply treatment has been applied. The records must remain connected by a Treatment Evidence Chain from the source Varroa evidence, Advisor Varroa Context Snapshot, and Advisor request through the recommendation, beekeeper decision, treatment applications, and outcome.

Rationale: Advisor guidance, beekeeper decision-making, and real-world treatment activity have different provenance, actors, and lifecycle states. Keeping them separate preserves auditability and lets the beekeeper record treatments that were not Advisor-recommended. Keeping them linked preserves future value for review, field learning, and carefully governed Advisor improvement.

Implications:

- A Treatment Recommendation can be pending, accepted, declined, or retained for audit without implying that treatment occurred.
- Blocked or failed Advisor Treatment Advice Attempts can be retained for audit without creating a Treatment Recommendation.
- A Hive Treatment Course can be created from an accepted recommendation or manually recorded without Advisor provenance.
- A Hive Treatment Course created from an accepted recommendation may initially be only `planned`; dated Treatment Applications are a later treatment-lifecycle concern.
- Treatment Applications record dated real-world steps or doses inside a course.
- Treatment Outcomes and later inspection evidence link to the Hive Treatment Course without rewriting the original Advisor recommendation.
- The source Varroa evidence or Varroa Assessment context, Advisor Varroa Context Snapshot, Advisor request payload, Advisor response or failed attempt, beekeeper decision, actual applications, and outcome must remain traceable as one chain.
- Any future use of anonymised treatment/advice/outcome chains for HiveSight Advisor retrieval, evaluation, or learning needs its own permitted-use policy and data-minimisation contract.
- HiveSight remains the system of record for hive treatment history, while HiveSight Advisor remains the source of advisory suggestions.

## 2026-07-29 AI-Assisted Annotation Is The Initial Dataset Bootstrap Path

Decision: HiveSight will use AI-assisted annotation as the intended bootstrap path for creating the first reviewed bee and Varroa datasets. A model, hosted vision service, generative AI tool, or other candidate-generation mechanism may create Candidate Annotations, but those Candidate Annotations are not ground truth until a human reviewer checks, corrects, approves, rejects, marks uncertain, or excludes them.

Rationale: Manually drawing every bee and Varroa annotation from scratch across the initial dataset would be too slow and would make model viability hard to explore. Candidate-generation helpers can reduce annotation effort while preserving human review as the trust boundary.

Implications:

- Dataset-labelling workflows and beekeeper product-feedback workflows may reuse UI components, but their provenance and dataset-governance records must remain distinct.
- Original photos plus structured annotations are the model inputs; rendered overlay images are for human review and should not be used as training pixels.
- Reviewed Annotations require explicit Dataset Role assignment before they enter training, validation, or benchmark Dataset Versions.
- Benchmark Dataset Items must be protected from training, routine tuning, prompt iteration, threshold adjustment, and pre-labelling optimisation.
- The first model-oriented work should focus on bee-detection viability before full Varroa detection.
- Dataset Curators and model reviewers are registered Users with internal capabilities, not a separate identity system.
- Internal dataset/model governance capabilities are separate from ordinary Workspace Membership roles.
- The new requirements baseline is captured in `requirements/ai-assisted-annotation-and-model-training-baseline.md`.

## 2026-07-29 Inspection Photo Upload Preconditions

Decision: Version one requires a person to register as a User, log in, have an active Workspace Membership, and have an accepted Workspace Data Use Agreement before uploading an inspection photo.

Rationale: Uploading an inspection photo is not an anonymous action in version one. The system needs identity, Workspace authorization, and accepted data-use terms before storing photos for analysis.

Implications:

- Upload authorization should use User and Workspace Membership language.
- Product copy may still describe the actor as a Beekeeper when the person is doing inspection work.
- A Workspace without accepted data-use terms cannot upload photos or receive analysis.
- Guest or trial upload remains deferred to V2 and would need its own explicit terms and limits.


## 2026-07-29 Product Renamed To HiveSight

Decision: The project and product name is now HiveSight, with hive-sight.com as the registered domain.

Rationale: The new name is available and more product-like than the initial working title. Renaming early reduces future churn across documentation, package names, local service defaults, and user-facing copy.

Implications:

- User-facing product language should use HiveSight.
- Technical package and workspace names should use `hive-sight` for JavaScript package names and `hive_sight_*` for Python import packages.
- Domain terms such as apiary, hive, beehive, beekeeper, inspection, bee, and Varroa remain unchanged.
- The current local folder may remain `BeehiveMonitor` until it is convenient to rename the physical workspace folder.


## 2026-07-28 Varroa Detection Is The Primary Product Focus

Decision: HiveSight will focus primarily on Varroa mite detection from hive inspection photos.

Rationale: The user clarified that the core value is detecting Varroa mites, counting bees, and estimating visible Varroa rate from submitted frame photos.

Implications:

- Image upload and analysis are central capabilities.
- Apiary and hive management should support inspection context rather than become a full beekeeping management suite.
- Requirements should prioritise inspections, photo association, bee counting, Varroa detection, and visible Varroa rate estimation.

## 2026-07-28 Web UI First, Mobile Later

Decision: The first version should likely be a web UI, with Android and Apple apps considered later.

Rationale: A web UI supports faster initial validation. Mobile apps are likely useful for field capture but can follow once core workflows and APIs are clearer.

Implications:

- The data model and backend should not be tightly coupled to the web UI.
- Future mobile workflows should be considered when designing photo capture and upload.

## 2026-07-28 Lightweight Apiary Management

Decision: The system should include lightweight apiary management: apiaries, hives, inspections, and photo associations.

Rationale: Varroa analysis needs to be tied to a specific hive and inspection.

Implications:

- The first data model should include apiary, hive, inspection, photo, and analysis result entities.
- Full beekeeping operations management is not assumed for the first version.

## 2026-07-28 Version-One User Is Hobbyist Or Small-Scale Beekeeper

Decision: Version one will target hobbyist or small-scale beekeepers managing their own apiaries and hives.

Rationale: This keeps the first version focused on a practical inspection-support workflow rather than a professional, advisory, research, or regulatory workflow.

Implications:

- The product should optimise for low-friction recording and review.
- The language should support beekeeper decision-making without claiming clinical or official authority.
- The first requirements baseline does not assume multi-tenant commercial operations, formal advisory reporting, or regulated diagnostic use.

## 2026-07-28 AI Estimate Boundary

Decision: Varroa outputs will be presented as AI-assisted visual estimates, not diagnoses, treatment recommendations, or official infestation measurements.

Rationale: Version one has not established field validation, accuracy thresholds, or treatment protocols.

Implications:

- UI copy must avoid diagnostic and prescriptive claims.
- Results should include confidence, caveats, and visible evidence.
- Acceptance criteria should verify that result wording preserves this boundary.

## 2026-07-28 Tagged Image Evidence And Correction Loop

Decision: Analysis output will include tagged-up photos showing likely Varroa detections, with optional display of all detected bees and lightweight user correction.

Rationale: Tagged photos give the beekeeper an empirical sense of model accuracy, and corrections create useful evidence for future model evaluation.

Implications:

- The system should store original images and structured annotation data.
- The first correction tools should cover false Varroa detections and missed likely Varroa locations.
- Version one should not attempt to become a full annotation studio.

## 2026-07-28 Initial Metric Is Mites Per 100 Visible Bees

Decision: The first Varroa metric will be likely Varroa detections associated with complete visible bees per 100 estimated complete visible bees in uploaded photos.

Rationale: This is understandable and aligned with the image evidence the system actually has.

Implications:

- The system must clearly say the estimate is based only on visible bees in uploaded photos.
- The metric should not be presented as a whole-hive infestation rate.
- Multiple photos of the same frame require careful caveats or grouping to avoid misleading aggregation.
- Partial visible bees and unassociated visible Varroa should be reported as additional evidence rather than silently included in the headline metric.

## 2026-08-05 Photo-Visible Metric Requires A Sampling Methodology

Decision: The first possible beekeeper-facing Varroa metric remains likely Varroa detections associated with eligible complete visible bees per 100 eligible complete visible bees, but it is scoped to declared reconciled photographed-frame evidence. A sampled result requires a versioned Varroa Sampling Plan, recorded coverage and uncertainty, and validation against protected full-depth frame evidence.

Rationale: The project can train a detector efficiently with enriched labelled crops, but that evidence cannot by itself support a statistical claim about a photographed frame or a colony. Full-depth frames are needed to quantify the sampling and pipeline error before a production sample size or stopping rule is chosen.

Implications:

- The result is not a colony-wide mite prevalence, diagnosis, or alcohol-wash equivalent.
- Potentially overlapping photos of the same frame cannot be aggregated until source-frame reconciliation exists.
- Gold-Standard Full-Frame Corpus work, model-corpus curation, and inspection-rate sampling have distinct protected roles and source-group splits.
- `requirements/varroa-evidence-methodology.md` governs the research protocol and future implementation gates.

## 2026-07-28 Model Requirements Are Separate From Product Requirements

Decision: AI model training, dataset, evaluation, privacy, consent, and release-gate requirements will live in a separate `model-requirements.md` document.

Rationale: Product requirements define what the beekeeper-facing system must do. Model requirements define what evidence and governance are needed before trusting the AI capability.

Implications:

- The product requirements can reference model capability without carrying all training and evaluation detail.
- Model provenance, annotation quality, benchmark separation, and promotion gates remain explicit and auditable.
- Future architecture and implementation work should treat model lifecycle as a first-class concern.

## 2026-07-28 Logical Two-Stage Model Pipeline

Decision: The model requirements will define a logical two-stage pipeline: detect bees first, then detect Varroa on or near detected bees.

Rationale: Bee detection and Varroa detection have different difficulty, metrics, and failure modes.

Implications:

- The implementation may still use one model or multiple models.
- Evaluation must measure bee detection and Varroa detection separately.
- The denominator for the headline estimate should use complete visible bees, while partial bees are tracked separately.

## 2026-07-28 User Corrections Require Review Before Dataset Use

Decision: User corrections will be stored as review candidates, not automatically used as training data.

Rationale: Corrections are valuable evidence but may be wrong, uncertain, accidental, or based on unsuitable images.

Implications:

- A human reviewer can approve, reject, mark uncertain, exclude, or assign corrected annotations to training, validation, or benchmark roles.
- User-submitted photos and corrections require an accepted Workspace Data Use Agreement and human review before model-improvement use.
- Benchmark data should remain protected from training and routine threshold tuning.

## 2026-07-28 Version-One Ownership Assumption

Decision: Version one uses Workspace as the canonical ownership boundary. A Beekeeper is a product persona/actor, not the ownership container or login identity.

Rationale: The first product may target an individual beekeeper, but future versions may support small businesses, clubs, advisors, or multiple beekeepers. Workspace remains stable as the owner of apiaries, hives, inspections, photos, analysis results, annotations, corrections, data-use agreements, and deletion requests.

Implications:

- Domain modelling should use Workspace for ownership.
- Domain modelling should use User for registration, authentication, and authorization.
- Domain modelling should use Beekeeper for the persona performing beekeeping work such as inspections or result review.
- Multi-user collaboration, advisor access, and organisation-level permissions are out of scope for version one.
- Tests should verify that workspace-owned records are not accessible across workspace boundaries.

## 2026-07-28 Upload Limits Are Configurable

Decision: Accepted image formats, upload size limits, and storage limits will be configurable rather than fixed in the requirements baseline.

Rationale: Real inspection image sizes, formats, hosting costs, and model constraints are not yet known.

Implications:

- Architecture should include a configuration point for upload constraints.
- The product must handle rejected files clearly.
- Original uploaded photos remain part of the storage baseline.

## 2026-07-28 Workspace Data Use Agreement Required For Upload And Analysis

Decision: Version one requires a workspace-level data-use agreement before upload and analysis features can be used.

Rationale: The intended product policy is that use of the service depends on accepting data-use terms for uploaded photos and corrections. Per-photo consent would add friction and does not match the intended version-one service model.

Implications:

- A workspace without an accepted data-use agreement cannot upload new photos or receive new analysis.
- If the agreement is withdrawn, new upload and analysis are disabled.
- Existing inspection history may remain viewable unless a deletion process applies.
- User corrections remain review candidates and do not automatically become ground truth or training data.

## 2026-07-28 Data Withdrawal And Deletion Gap Captured

Decision: The project will explicitly track the unresolved privacy gap around withdrawal, previously uploaded photos, data deletion, and already-trained model artifacts.

Rationale: Inspection photos and metadata may be personally identifiable or sensitive because they can contain GPS metadata, timestamps, apiary names, business-sensitive hive health information, or incidental background detail. The project should not silently assume that withdrawal or deletion semantics are simple.

Implications:

- The domain model includes Data Deletion Request as a deferred concept.
- Workspace data-use withdrawal stops future upload, analysis, and future model-improvement use from the point of withdrawal, subject to final policy.
- The project still needs a policy/legal decision on whether previously uploaded photos can continue to be used after withdrawal.
- The project still needs a policy/legal decision on whether already-created dataset versions or already-trained model artifacts can or must be affected by later withdrawal or deletion requests.

## 2026-07-28 Service-Oriented Architecture For V1

Decision: Version one will use a service-oriented architecture in a monorepo, with a TypeScript web frontend, protected Python Core API, private Python Analysis Service, asynchronous queue, S3-compatible object storage, and a lightweight Model Registry.

Rationale: The project needs separate frontend and backend evolution, future support for mobile clients, independent scaling of image analysis, and clean separation between product workflow and model/runtime concerns without prematurely splitting every domain concept into its own service.

Implications:

- The frontend and future mobile clients call the Core API through a protected API Gateway or edge layer.
- The Core API is internet-reachable but not public-open; user-facing operations require user identity and Workspace authorization.
- The Analysis Service is private and receives work through a queue or trusted service boundary.
- Original photos and tagged images live in object storage, with short-lived object-scoped upload and view URLs as the target pattern.
- Analysis is asynchronous, and one Inspection Photo may have multiple preserved analysis runs.
- Model training and evaluation remain separate from V1 runtime services.
- The decision is captured in `architecture/adr/0001-service-oriented-architecture.md` and visualised in `architecture/system-context.md`.

## 2026-07-28 Guest Trial Photo Analysis Deferred To V2

Decision: The project will capture guest or trial photo analysis as a deferred / V2 acquisition workflow, not a version-one feature.

Rationale: Letting a prospective user upload a small number of photos before registration could demonstrate the value of tagged Varroa analysis and reduce adoption friction. It also introduces policy and architecture questions around data-use terms, abuse prevention, usage limits, retention, deletion, and model-improvement eligibility.

Implications:

- Version one remains focused on authenticated Workspace-based inspection workflows.
- A future trial workflow may allow a small number of photo analyses before Workspace registration.
- Trial use must still require accepted data-use terms before upload and analysis.
- Trial usage limits should be configurable and may consider image count, time window, user/browser/IP signals, or other abuse-prevention controls.
- Trial photos and results should have explicit retention and deletion rules.
- Trial photos and corrections should be excluded from model-improvement workflows by default unless future policy explicitly allows use with accepted terms and human review.

## 2026-07-29 User, Workspace Membership, And Beekeeper Language

Decision: The domain model will distinguish User, Workspace Membership, Workspace, and Beekeeper.

Rationale: Registration, login, authentication, and authorization need a clear identity concept. Workspace remains the ownership boundary for apiaries, hives, inspections, photos, corrections, and data-use terms. Beekeeper remains useful product language for the person doing beekeeping work, but it should not carry login identity or ownership semantics.

Implications:

- `User` means registered login identity.
- `Workspace Membership` connects a User to a Workspace with a role.
- Version one registration creates one default Workspace and one `owner` Workspace Membership for the registered User.
- Version one UI exposes one active/default Workspace and no workspace switcher.
- Version one supports only the `owner` membership role.
- Future roles such as `member`, `inspector`, `advisor`, and `reviewer` are deferred.
- Workspace invitations and multi-user collaboration are deferred.
- `Beekeeper` remains a product/persona term and is not a persisted version-one entity.
- The Workspace owner accepts the Workspace Data Use Agreement on behalf of the Workspace in version one.

## 2026-07-29 Bee Annotation Geometry And First Detector Baseline

Decision: Human-reviewed bee annotations will use oriented bee ellipses as the canonical domain geometry. The first trainable HiveSight Bee Detector baseline will use YOLO OBB nano or small as a model-specific oriented object detection projection derived from those ellipses.

Rationale: Bees are elongated and appear at many rotations. Axis-aligned boxes are a poor fit for dense frame photos, while segmentation masks are too costly for the first dataset bootstrap. YOLO OBB gives a practical local baseline that can learn rotated objects while preserving the option to change model family later.

Implications:

- Grounding DINO was initially treated as an experimental pre-labelling adapter and comparison point, but ADR 0005 later retired it from the active solution after poor brood-frame bee localisation results.
- Candidate Annotation output is never ground truth without human review.
- The annotation UI must support fast creation and adjustment of rotated ellipses.
- Dataset exports must distinguish canonical reviewed annotation evidence from model-specific training labels.
- The first dataset bootstrap should start with small reviewed Training Crops and grow toward larger crops, frame regions, and full frame sides.

## 2026-07-31 Grounding DINO Retired From Active Model Direction

Decision: HiveSight will remove Grounding DINO from the active pre-labelling/model-training solution. The replacement direction is a project-owned Bee Detector trained from reviewed HiveSight annotation evidence, with YOLO OBB as the first implementation candidate behind an adapter seam.

Rationale: Real brood-frame trial images showed that Grounding DINO was not useful enough at localising bees in HiveSight's target imagery. Continuing to tune it would distract from the stronger path: build a detector that can improve from reviewed Oriented Bee Ellipse evidence governed inside HiveSight.

Implications:

- Active docs, commands, adapter registration, and dependencies should stop presenting Grounding DINO as supported.
- Historical Slice 0007 documentation may remain as a record of the spike.
- New domain language should prefer Candidate Annotation over Grounding DINO-specific pre-labelling language.
- YOLO OBB is the first Bee Detector baseline, not a permanent commitment to one model family.
- The decision is captured in `architecture/adr/0005-retire-grounding-dino-for-bee-candidate-annotation.md`.

## 2026-07-29 Inspection Intent And Multi-Photo Inspections

Decision: Each Inspection will have one explicit intent. Initial intents are `training_data_collection` and `varroa_assessment`. An Inspection may contain multiple photos.

Rationale: Dataset collection and beekeeper-facing Varroa assessment have different workflows, provenance, and statistical meaning. A real inspection may also involve many frame photos, including both sides of brood frames.

Implications:

- Dataset labelling workflows should appear for training-data collection inspections.
- Varroa assessment workflows should appear for beekeeper-facing assessment inspections.
- One Inspection must not mix training-data collection and Varroa assessment intent.
- The photo intake model must support multiple photos per Inspection.
