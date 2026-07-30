import {
  Activity,
  Check,
  CircleAlert,
  CloudUpload,
  FileImage,
  FlaskConical,
  Image,
  LoaderCircle,
  Plus,
  RefreshCw,
  ShieldCheck
} from "lucide-react";
import { type FormEvent, type ReactNode, useEffect, useMemo, useState } from "react";
import {
  acceptWorkspaceDataUseAgreement,
  createApiary,
  createHive,
  createInspection,
  createDatasetItem,
  createReviewDecision,
  fetchAnalysisEvidence,
  fetchCoreHealth,
  fetchDatasetLabellingEvidence,
  fetchDevSession,
  fetchInspectionPhotos,
  fetchInspectionPhotoObjectUrl,
  processAnalysisRun,
  startDatasetLabellingSession,
  updateDatasetLabellingSessionMetadata,
  uploadInspectionPhoto,
  type AnalysisEvidence,
  type AnalysisRunDetail,
  type Annotation,
  type Apiary,
  type ApiError,
  type DevSession,
  type HealthResponse,
  type Hive,
  type DatasetLabellingEvidence,
  type DatasetExclusionReason,
  type DatasetRole,
  type ImageQualityStatus,
  type Inspection,
  type InspectionIntent,
  type InspectionPhoto,
  type PhotoIntake,
  type ReviewDecisionValue
} from "./coreApiClient";

const devUserId = "00000000-0000-0000-0000-000000000101";
const currentTermsVersion = "2026-07-29";

type LoadState =
  | { kind: "loading" }
  | { kind: "ready"; health: HealthResponse; session: DevSession }
  | { kind: "error"; message: string };

type ActionState =
  | { kind: "idle" }
  | { kind: "working"; label: string }
  | { kind: "blocked"; code: string; message: string }
  | { kind: "accepted"; intake: PhotoIntake };

export function App() {
  const [loadState, setLoadState] = useState<LoadState>({ kind: "loading" });
  const [actionState, setActionState] = useState<ActionState>({ kind: "idle" });
  const [apiary, setApiary] = useState<Apiary | null>(null);
  const [hive, setHive] = useState<Hive | null>(null);
  const [inspection, setInspection] = useState<Inspection | null>(null);
  const [inspectionPhotos, setInspectionPhotos] = useState<InspectionPhoto[]>([]);
  const [analysisDetail, setAnalysisDetail] = useState<AnalysisRunDetail | null>(null);
  const [analysisEvidence, setAnalysisEvidence] = useState<AnalysisEvidence | null>(null);
  const [evidenceImageUrl, setEvidenceImageUrl] = useState<string | null>(null);
  const [labellingEvidence, setLabellingEvidence] = useState<DatasetLabellingEvidence | null>(null);
  const [labellingImageUrl, setLabellingImageUrl] = useState<string | null>(null);
  const [reviewState, setReviewState] = useState<{ kind: "idle" | "working" | "done" } | null>(
    null
  );
  const [labellingState, setLabellingState] = useState<{
    kind: "idle" | "working" | "done";
    label?: string;
  } | null>(null);
  const [apiaryName, setApiaryName] = useState("Home apiary");
  const [hiveName, setHiveName] = useState("Hive A");
  const [inspectionDate, setInspectionDate] = useState(new Date().toISOString().slice(0, 10));
  const [inspectionIntent, setInspectionIntent] =
    useState<InspectionIntent>("varroa_assessment");
  const [file, setFile] = useState<File | null>(null);

  useEffect(() => {
    Promise.all([fetchCoreHealth(), fetchDevSession(devUserId)])
      .then(([health, session]) => setLoadState({ kind: "ready", health, session }))
      .catch((error: Error) => setLoadState({ kind: "error", message: error.message }));
  }, []);

  useEffect(() => {
    return () => {
      if (evidenceImageUrl) {
        URL.revokeObjectURL(evidenceImageUrl);
      }
      if (labellingImageUrl) {
        URL.revokeObjectURL(labellingImageUrl);
      }
    };
  }, [evidenceImageUrl, labellingImageUrl]);

  const session = loadState.kind === "ready" ? loadState.session : null;
  const termsAccepted = session?.workspaceDataUseAgreementStatus === "accepted";
  const canCreateHive = Boolean(apiary);
  const canCreateInspection = Boolean(hive);
  const canUpload = Boolean(termsAccepted && inspection && file);
  const isTrainingDataCollection = inspection?.intent === "training_data_collection";
  const isVarroaAssessment = inspection?.intent === "varroa_assessment";
  const selectedFileLabel = useMemo(() => {
    if (!file) {
      return "No photo selected";
    }
    return `${file.name} / ${Math.round(file.size / 1024)} KB`;
  }, [file]);

  async function refreshSession() {
    const nextSession = await fetchDevSession(devUserId);
    setLoadState((current) =>
      current.kind === "ready" ? { ...current, session: nextSession } : current
    );
    return nextSession;
  }

  async function onAcceptTerms() {
    if (!session) {
      return;
    }
    await runAction("Accepting terms", async () => {
      const nextSession = await acceptWorkspaceDataUseAgreement({
        devUserId,
        workspaceId: session.workspaceId,
        termsVersion: currentTermsVersion
      });
      setLoadState((current) =>
        current.kind === "ready" ? { ...current, session: nextSession } : current
      );
    });
  }

  async function onCreateApiary(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      return;
    }
    await runAction("Creating apiary", async () => {
      const created = await createApiary({
        devUserId,
        workspaceId: session.workspaceId,
        name: apiaryName
      });
      setApiary(created);
      setHive(null);
      setInspection(null);
      setInspectionPhotos([]);
      setAnalysisDetail(null);
      clearEvidenceImage();
      clearLabellingImage();
    });
  }

  async function onCreateHive(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!apiary) {
      return;
    }
    await runAction("Creating hive", async () => {
      const created = await createHive({ devUserId, apiaryId: apiary.apiaryId, name: hiveName });
      setHive(created);
      setInspection(null);
      setInspectionPhotos([]);
      setAnalysisDetail(null);
      clearEvidenceImage();
      clearLabellingImage();
    });
  }

  async function onCreateInspection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!hive) {
      return;
    }
    await runAction("Creating inspection", async () => {
      const created = await createInspection({
        devUserId,
        hiveId: hive.hiveId,
        inspectionDate,
        intent: inspectionIntent
      });
      setInspection(created);
      setInspectionPhotos([]);
      setAnalysisDetail(null);
      clearEvidenceImage();
      clearLabellingImage();
    });
  }

  async function onUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session || !inspection || !file) {
      return;
    }
    await runAction("Uploading photo", async () => {
      const intake = await uploadInspectionPhoto({
        devUserId,
        workspaceId: session.workspaceId,
        inspectionId: inspection.inspectionId,
        file
      });
      await refreshSession();
      await refreshInspectionPhotos();
      setAnalysisDetail(null);
      clearEvidenceImage();
      clearLabellingImage();
      setActionState({ kind: "accepted", intake });
    });
  }

  async function refreshInspectionPhotos() {
    if (!session || !inspection) {
      return;
    }
    const listing = await fetchInspectionPhotos({
      devUserId,
      workspaceId: session.workspaceId,
      inspectionId: inspection.inspectionId
    });
    setInspection(listing.inspection);
    setInspectionPhotos(listing.photos);
  }

  async function onProcessAnalysis() {
    if (!session || actionState.kind !== "accepted") {
      return;
    }
    const acceptedIntake = actionState.intake;
    await runAction("Processing analysis", async () => {
      const detail = await processAnalysisRun({
        devUserId,
        workspaceId: session.workspaceId,
        analysisRunId: acceptedIntake.analysisRun.analysisRunId
      });
      setAnalysisDetail(detail);
      if (detail.status === "completed") {
        const evidence = await fetchAnalysisEvidence({
          devUserId,
          workspaceId: session.workspaceId,
          analysisRunId: acceptedIntake.analysisRun.analysisRunId
        });
        const nextImageUrl = await fetchInspectionPhotoObjectUrl({
          devUserId,
          viewUrl: evidence.inspectionPhoto.viewUrl
        });
        setAnalysisEvidence(evidence);
        setEvidenceImageUrl((current) => {
          if (current) {
            URL.revokeObjectURL(current);
          }
          return nextImageUrl;
        });
      }
      setActionState({ kind: "accepted", intake: acceptedIntake });
    });
  }

  async function onSubmitReviewDecision({
    annotationId,
    decision,
    notes
  }: {
    annotationId: string;
    decision: ReviewDecisionValue;
    notes: string;
  }) {
    if (!session || !analysisEvidence) {
      return;
    }
    setReviewState({ kind: "working" });
    try {
      await createReviewDecision({
        devUserId,
        workspaceId: session.workspaceId,
        subjectId: annotationId,
        decision,
        notes
      });
      const refreshedEvidence = await fetchAnalysisEvidence({
        devUserId,
        workspaceId: session.workspaceId,
        analysisRunId: analysisEvidence.analysisRunId
      });
      setAnalysisEvidence(refreshedEvidence);
      setReviewState({ kind: "done" });
    } catch (error) {
      const apiError = toApiError(error);
      setReviewState(null);
      setActionState({ kind: "blocked", code: apiError.code, message: apiError.message });
    }
  }

  async function onStartDatasetLabelling() {
    if (!session || actionState.kind !== "accepted") {
      return;
    }
    setLabellingState({ kind: "working", label: "Starting dataset labelling" });
    try {
      const labellingSession = await startDatasetLabellingSession({
        devUserId,
        workspaceId: session.workspaceId,
        inspectionPhotoId: actionState.intake.inspectionPhoto.inspectionPhotoId
      });
      const evidence = await fetchDatasetLabellingEvidence({
        devUserId,
        workspaceId: session.workspaceId,
        labellingSessionId: labellingSession.labellingSessionId
      });
      const nextImageUrl = await fetchInspectionPhotoObjectUrl({
        devUserId,
        viewUrl: evidence.inspectionPhoto.viewUrl
      });
      setLabellingEvidence(evidence);
      setLabellingImageUrl((current) => {
        if (current) {
          URL.revokeObjectURL(current);
        }
        return nextImageUrl;
      });
      setLabellingState({ kind: "done" });
    } catch (error) {
      const apiError = toApiError(error);
      setLabellingState(null);
      setActionState({ kind: "blocked", code: apiError.code, message: apiError.message });
    }
  }

  async function onUpdateDatasetLabellingMetadata({
    labellingSessionId,
    sourceGroupKey,
    imageQualityStatus
  }: {
    labellingSessionId: string;
    sourceGroupKey: string;
    imageQualityStatus: ImageQualityStatus;
  }) {
    if (!session) {
      return;
    }
    setLabellingState({ kind: "working", label: "Saving labelling metadata" });
    try {
      const updatedSession = await updateDatasetLabellingSessionMetadata({
        devUserId,
        workspaceId: session.workspaceId,
        labellingSessionId,
        sourceGroupKey,
        imageQualityStatus
      });
      setLabellingEvidence((current) =>
        current ? { ...current, labellingSession: updatedSession } : current
      );
      setLabellingState({ kind: "done" });
    } catch (error) {
      const apiError = toApiError(error);
      setLabellingState(null);
      setActionState({ kind: "blocked", code: apiError.code, message: apiError.message });
    }
  }

  async function onSubmitDatasetLabellingReview({
    annotationId,
    decision,
    notes
  }: {
    annotationId: string;
    decision: ReviewDecisionValue;
    notes: string;
  }) {
    if (!session || !labellingEvidence) {
      return;
    }
    setLabellingState({ kind: "working", label: "Recording labelling review" });
    try {
      await createReviewDecision({
        devUserId,
        workspaceId: session.workspaceId,
        subjectId: annotationId,
        decision,
        notes
      });
      const refreshedEvidence = await fetchDatasetLabellingEvidence({
        devUserId,
        workspaceId: session.workspaceId,
        labellingSessionId: labellingEvidence.labellingSession.labellingSessionId
      });
      setLabellingEvidence(refreshedEvidence);
      setLabellingState({ kind: "done" });
    } catch (error) {
      const apiError = toApiError(error);
      setLabellingState(null);
      setActionState({ kind: "blocked", code: apiError.code, message: apiError.message });
    }
  }

  async function onAssignDatasetRole({
    labellingSessionId,
    datasetRole,
    assignmentNote,
    exclusionReason
  }: {
    labellingSessionId: string;
    datasetRole: DatasetRole;
    assignmentNote: string;
    exclusionReason: DatasetExclusionReason | null;
  }) {
    if (!session) {
      return;
    }
    setLabellingState({ kind: "working", label: "Assigning dataset role" });
    try {
      await createDatasetItem({
        devUserId,
        workspaceId: session.workspaceId,
        labellingSessionId,
        datasetRole,
        assignmentNote,
        exclusionReason
      });
      const refreshedEvidence = await fetchDatasetLabellingEvidence({
        devUserId,
        workspaceId: session.workspaceId,
        labellingSessionId
      });
      setLabellingEvidence(refreshedEvidence);
      setLabellingState({ kind: "done" });
    } catch (error) {
      const apiError = toApiError(error);
      setLabellingState(null);
      setActionState({ kind: "blocked", code: apiError.code, message: apiError.message });
    }
  }

  function clearEvidenceImage() {
    setAnalysisEvidence(null);
    setEvidenceImageUrl((current) => {
      if (current) {
        URL.revokeObjectURL(current);
      }
      return null;
    });
  }

  function clearLabellingImage() {
    setLabellingEvidence(null);
    setLabellingImageUrl((current) => {
      if (current) {
        URL.revokeObjectURL(current);
      }
      return null;
    });
  }

  async function runAction(label: string, action: () => Promise<void>) {
    setActionState({ kind: "working", label });
    try {
      await action();
      setActionState((current) => (current.kind === "accepted" ? current : { kind: "idle" }));
    } catch (error) {
      const apiError = toApiError(error);
      setActionState({ kind: "blocked", code: apiError.code, message: apiError.message });
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar" aria-label="Workspace status">
        <div>
          <p className="eyebrow">HiveSight</p>
          <h1>Inspection photo intake</h1>
        </div>
        <StatusPill loadState={loadState} />
      </header>

      {loadState.kind === "ready" ? (
        <section className="intake-layout" aria-label="Inspection photo intake workflow">
          <aside className="workspace-panel">
            <PanelHeading icon={<ShieldCheck size={20} />} title="Workspace gate" />
            <dl className="facts">
              <div>
                <dt>User</dt>
                <dd>{loadState.session.userId.slice(0, 8)}</dd>
              </div>
              <div>
                <dt>Workspace</dt>
                <dd>{loadState.session.workspaceId.slice(0, 8)}</dd>
              </div>
              <div>
                <dt>Role</dt>
                <dd>{loadState.session.role}</dd>
              </div>
            </dl>
            <button
              className="primary-action"
              type="button"
              onClick={onAcceptTerms}
              disabled={termsAccepted || actionState.kind === "working"}
              data-testid="accept-terms-button"
            >
              {termsAccepted ? <Check size={18} /> : <ShieldCheck size={18} />}
              {termsAccepted ? "Terms accepted" : "Accept terms"}
            </button>
          </aside>

          <section className="workflow-panel">
            <div className="form-grid">
              <form className="stacked-form" onSubmit={onCreateApiary}>
                <PanelHeading icon={<Plus size={20} />} title="Apiary" />
                <label>
                  <span>Name</span>
                <input
                  value={apiaryName}
                  onChange={(event) => setApiaryName(event.target.value)}
                  required
                  data-testid="apiary-name-input"
                />
                </label>
                <button
                  type="submit"
                  disabled={actionState.kind === "working"}
                  data-testid="create-apiary-button"
                >
                  Create apiary
                </button>
                <RecordBadge value={apiary?.apiaryId} />
              </form>

              <form className="stacked-form" onSubmit={onCreateHive}>
                <PanelHeading icon={<Plus size={20} />} title="Hive" />
                <label>
                  <span>Name</span>
                <input
                  value={hiveName}
                  onChange={(event) => setHiveName(event.target.value)}
                  required
                  data-testid="hive-name-input"
                />
                </label>
                <button
                  type="submit"
                  disabled={!canCreateHive || actionState.kind === "working"}
                  data-testid="create-hive-button"
                >
                  Create hive
                </button>
                <RecordBadge value={hive?.hiveId} />
              </form>

              <form className="stacked-form" onSubmit={onCreateInspection}>
                <PanelHeading icon={<Plus size={20} />} title="Inspection" />
                <label>
                  <span>Date</span>
                  <input
                    type="date"
                  value={inspectionDate}
                  onChange={(event) => setInspectionDate(event.target.value)}
                  required
                  data-testid="inspection-date-input"
                />
                </label>
                <label>
                  <span>Intent</span>
                  <select
                    value={inspectionIntent}
                    onChange={(event) =>
                      setInspectionIntent(event.target.value as InspectionIntent)
                    }
                    data-testid="inspection-intent-select"
                  >
                    <option value="varroa_assessment">Varroa assessment</option>
                    <option value="training_data_collection">Training data collection</option>
                  </select>
                </label>
                <button
                  type="submit"
                  disabled={!canCreateInspection || actionState.kind === "working"}
                  data-testid="create-inspection-button"
                >
                  Create inspection
                </button>
                <RecordBadge value={inspection?.inspectionId} />
                {inspection ? (
                  <p className="intent-badge" data-testid="inspection-intent-badge">
                    {formatInspectionIntent(inspection.intent)}
                  </p>
                ) : null}
              </form>
            </div>

            <form className="upload-panel" onSubmit={onUpload}>
              <PanelHeading icon={<CloudUpload size={20} />} title="Photo upload" />
              <label className="file-picker">
                <FileImage size={24} />
                <span>{selectedFileLabel}</span>
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                  data-testid="inspection-photo-input"
                />
              </label>
              <button
                className="primary-action"
                type="submit"
                disabled={!canUpload || actionState.kind === "working"}
                data-testid="upload-photo-button"
              >
                <CloudUpload size={18} />
                Upload photo
              </button>
            </form>

            {inspection ? (
              <InspectionPhotoListPanel photos={inspectionPhotos} intent={inspection.intent} />
            ) : null}

            <Outcome state={actionState} analysisDetail={analysisDetail} />
            {actionState.kind === "accepted" ? (
              <>
                {isVarroaAssessment ? (
                  <AnalysisPanel
                    analysisRunId={actionState.intake.analysisRun.analysisRunId}
                    queuedStatus={actionState.intake.analysisRun.status}
                    detail={analysisDetail}
                    evidence={analysisEvidence}
                    imageUrl={evidenceImageUrl}
                    reviewerCapability={loadState.session.reviewerCapability}
                    reviewState={reviewState}
                    onProcessAnalysis={onProcessAnalysis}
                    onSubmitReviewDecision={onSubmitReviewDecision}
                  />
                ) : null}
                {isTrainingDataCollection && loadState.session.datasetCuratorCapability ? (
                  <DatasetLabellingPanel
                    evidence={labellingEvidence}
                    imageUrl={labellingImageUrl}
                    labellingState={labellingState}
                    onStartDatasetLabelling={onStartDatasetLabelling}
                    onUpdateMetadata={onUpdateDatasetLabellingMetadata}
                    onSubmitReviewDecision={onSubmitDatasetLabellingReview}
                    onAssignDatasetRole={onAssignDatasetRole}
                  />
                ) : null}
              </>
            ) : null}
          </section>
        </section>
      ) : (
        <section className="loading-panel">
          {loadState.kind === "loading" ? <LoaderCircle className="spin" size={28} /> : null}
          <p>{loadState.kind === "error" ? loadState.message : "Loading workspace"}</p>
        </section>
      )}
    </main>
  );
}

function StatusPill({ loadState }: { loadState: LoadState }) {
  if (loadState.kind === "loading") {
    return <span className="status-pill status-loading">Checking Core API</span>;
  }

  if (loadState.kind === "error") {
    return <span className="status-pill status-error">Core API offline</span>;
  }

  return <span className="status-pill status-ready">{loadState.health.service} online</span>;
}

function PanelHeading({ icon, title }: { icon: ReactNode; title: string }) {
  return (
    <div className="panel-heading">
      <span aria-hidden="true">{icon}</span>
      <h2>{title}</h2>
    </div>
  );
}

function RecordBadge({ value }: { value: string | undefined }) {
  return (
    <p className={value ? "record-badge ready" : "record-badge"}>{value ? value : "Pending"}</p>
  );
}

function InspectionPhotoListPanel({
  photos,
  intent
}: {
  photos: InspectionPhoto[];
  intent: InspectionIntent;
}) {
  return (
    <section
      className="photo-list-panel"
      aria-label="Inspection photos"
      data-testid="inspection-photo-list"
    >
      <div className="analysis-header">
        <PanelHeading icon={<Image size={20} />} title="Inspection photos" />
        <span className="analysis-status status-queued">{formatInspectionIntent(intent)}</span>
      </div>
      {photos.length === 0 ? (
        <p className="analysis-caveat">No photos uploaded for this Inspection yet.</p>
      ) : (
        <ul className="photo-list">
          {photos.map((photo) => (
            <li key={photo.inspectionPhotoId} data-testid="inspection-photo-list-item">
              <FileImage size={18} />
              <div>
                <strong>{photo.filename}</strong>
                <p>
                  {photo.uploadStatus} / {Math.round(photo.sizeBytes / 1024)} KB /{" "}
                  {new Date(photo.uploadedAt).toLocaleString()}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function formatInspectionIntent(intent: InspectionIntent) {
  return intent === "training_data_collection" ? "Training data collection" : "Varroa assessment";
}

function Outcome({
  state,
  analysisDetail
}: {
  state: ActionState;
  analysisDetail: AnalysisRunDetail | null;
}) {
  if (state.kind === "working") {
    return (
      <div className="outcome working" role="status">
        <LoaderCircle className="spin" size={20} />
        <span>{state.label}</span>
      </div>
    );
  }

  if (state.kind === "blocked") {
    return (
      <div className="outcome blocked" role="alert">
        <CircleAlert size={20} />
        <div>
          <strong>{state.code}</strong>
          <p>{state.message}</p>
        </div>
      </div>
    );
  }

  if (state.kind === "accepted") {
    return (
      <div className="outcome accepted" role="status">
        <Check size={20} />
        <div>
          <strong>{state.intake.inspectionPhoto.uploadStatus}</strong>
          <p>Analysis {analysisDetail?.status ?? state.intake.analysisRun.status}</p>
        </div>
      </div>
    );
  }

  return null;
}

function AnalysisPanel({
  analysisRunId,
  queuedStatus,
  detail,
  evidence,
  imageUrl,
  reviewerCapability,
  reviewState,
  onProcessAnalysis,
  onSubmitReviewDecision
}: {
  analysisRunId: string;
  queuedStatus: string;
  detail: AnalysisRunDetail | null;
  evidence: AnalysisEvidence | null;
  imageUrl: string | null;
  reviewerCapability: boolean;
  reviewState: { kind: "idle" | "working" | "done" } | null;
  onProcessAnalysis: () => void;
  onSubmitReviewDecision: (request: {
    annotationId: string;
    decision: ReviewDecisionValue;
    notes: string;
  }) => Promise<void>;
}) {
  const status = detail?.status ?? queuedStatus;
  const result = detail?.analysisResult ?? null;

  return (
    <section className="analysis-panel" aria-label="Analysis result">
      <div className="analysis-header">
        <PanelHeading icon={<Activity size={20} />} title="Analysis" />
        <span className={`analysis-status status-${status}`}>{status}</span>
      </div>
      <p className="run-id">Run {analysisRunId}</p>
      <button
        type="button"
        onClick={onProcessAnalysis}
        disabled={status !== "queued"}
        data-testid="process-analysis-button"
      >
        {status === "queued" ? <FlaskConical size={18} /> : <RefreshCw size={18} />}
        Process stub analysis
      </button>

      {result ? (
        <div className="result-grid">
          <Metric label="Complete visible bees" value={result.completeVisibleBeeCount} />
          <Metric label="Partial visible bees" value={result.partialVisibleBeeCount} />
          <Metric label="Likely Varroa detections" value={result.likelyVarroaDetections} />
          <Metric label="Model version" value={result.modelVersion} />
        </div>
      ) : null}

      {evidence && imageUrl ? (
        <EvidencePanel
          evidence={evidence}
          imageUrl={imageUrl}
          reviewerCapability={reviewerCapability}
          reviewState={reviewState}
          onSubmitReviewDecision={onSubmitReviewDecision}
        />
      ) : null}

      {detail?.failureMessage ? (
        <p className="analysis-caveat failed">{detail.failureMessage}</p>
      ) : (
        <p className="analysis-caveat">
          Completed results in this slice are deterministic stubs for handoff testing, not a real
          AI-assisted Varroa estimate.
        </p>
      )}
    </section>
  );
}

function DatasetLabellingPanel({
  evidence,
  imageUrl,
  labellingState,
  onStartDatasetLabelling,
  onUpdateMetadata,
  onSubmitReviewDecision,
  onAssignDatasetRole
}: {
  evidence: DatasetLabellingEvidence | null;
  imageUrl: string | null;
  labellingState: { kind: "idle" | "working" | "done"; label?: string } | null;
  onStartDatasetLabelling: () => void;
  onUpdateMetadata: (request: {
    labellingSessionId: string;
    sourceGroupKey: string;
    imageQualityStatus: ImageQualityStatus;
  }) => Promise<void>;
  onSubmitReviewDecision: (request: {
    annotationId: string;
    decision: ReviewDecisionValue;
    notes: string;
  }) => Promise<void>;
  onAssignDatasetRole: (request: {
    labellingSessionId: string;
    datasetRole: DatasetRole;
    assignmentNote: string;
    exclusionReason: DatasetExclusionReason | null;
  }) => Promise<void>;
}) {
  const [selectedAnnotationId, setSelectedAnnotationId] = useState<string | null>(null);
  const [sourceGroupKey, setSourceGroupKey] = useState("");
  const [imageQualityStatus, setImageQualityStatus] =
    useState<ImageQualityStatus>("unassessed");
  const [notes, setNotes] = useState("Accepted for dataset labelling evidence.");
  const [datasetRole, setDatasetRole] = useState<DatasetRole>("training");
  const [assignmentNote, setAssignmentNote] = useState("");
  const [exclusionReason, setExclusionReason] =
    useState<DatasetExclusionReason>("poor_image_quality");

  useEffect(() => {
    if (!evidence) {
      return;
    }
    setSourceGroupKey(evidence.labellingSession.sourceGroupKey ?? "");
    setImageQualityStatus(evidence.labellingSession.imageQualityStatus);
    if (evidence.datasetItem) {
      setDatasetRole(evidence.datasetItem.datasetRole);
      setAssignmentNote(evidence.datasetItem.assignmentNote ?? "");
      setExclusionReason(evidence.datasetItem.exclusionReason ?? "poor_image_quality");
    }
  }, [evidence]);

  const selectedAnnotation = evidence?.draftAnnotations.find(
    (annotation) => annotation.annotationId === selectedAnnotationId
  );
  const completeBeeCount =
    evidence?.draftAnnotations.filter(
      (annotation) => annotation.annotationType === "complete_visible_bee"
    ).length ?? 0;
  const partialBeeCount =
    evidence?.draftAnnotations.filter(
      (annotation) => annotation.annotationType === "partial_visible_bee"
    ).length ?? 0;
  const datasetItem = evidence?.datasetItem ?? null;
  const hasReviewedAnnotations = (evidence?.reviewedAnnotations.length ?? 0) > 0;
  const assignmentRequiresNote = datasetRole === "excluded" && exclusionReason === "other";
  const canAssignDatasetRole =
    Boolean(evidence) &&
    hasReviewedAnnotations &&
    !datasetItem &&
    labellingState?.kind !== "working" &&
    (!assignmentRequiresNote || assignmentNote.trim().length > 0);

  return (
    <section
      className="analysis-panel dataset-labelling-panel"
      aria-label="Dataset labelling"
      data-testid="dataset-labelling-panel"
    >
      <div className="analysis-header">
        <PanelHeading icon={<FlaskConical size={20} />} title="Dataset labelling" />
        <span className={`analysis-status status-${evidence?.labellingSession.status ?? "queued"}`}>
          {evidence?.labellingSession.status ?? "not started"}
        </span>
      </div>
      <p className="analysis-caveat">
        Internal dataset-labelling workflow. Machine suggestions require curator review and do not
        assign dataset use.
      </p>
      <button
        type="button"
        onClick={onStartDatasetLabelling}
        disabled={labellingState?.kind === "working"}
        data-testid="start-dataset-labelling-button"
      >
        <FlaskConical size={18} />
        {evidence ? "Reload dataset labelling" : "Start dataset labelling"}
      </button>

      {labellingState?.kind === "working" ? (
        <div className="outcome working" role="status">
          <LoaderCircle className="spin" size={20} />
          <span>{labellingState.label}</span>
        </div>
      ) : null}

      {evidence && imageUrl ? (
        <>
          <div
            className="prelabeler-panel"
            aria-label="Pre-labelling helper provenance"
            data-testid="prelabeler-provenance-panel"
          >
            <div>
              <span>Helper</span>
              <strong data-testid="prelabeler-provider">
                {prelabelerProviderLabel(evidence.labellingSession.prelabelerRun.provider)}
              </strong>
            </div>
            <div>
              <span>Model</span>
              <strong data-testid="prelabeler-model">
                {evidence.labellingSession.prelabelerRun.modelId ?? "Not configured"}
              </strong>
            </div>
            <div>
              <span>Prompt</span>
              <strong data-testid="prelabeler-prompt">
                {evidence.labellingSession.prelabelerRun.promptText ?? "None"}
              </strong>
            </div>
            <div>
              <span>Status</span>
              <strong data-testid="prelabeler-run-status">
                {evidence.labellingSession.prelabelerRun.status} /{" "}
                {evidence.labellingSession.prelabelerRun.suggestionCount} suggestions
              </strong>
            </div>
          </div>
          {evidence.labellingSession.prelabelerRun.status === "failed" ? (
            <div className="outcome blocked" role="alert" data-testid="prelabeler-failure-state">
              <CircleAlert size={20} />
              <span>
                {evidence.labellingSession.prelabelerRun.errorMessage ??
                  "Pre-labelling helper failed before suggestions were created."}
              </span>
            </div>
          ) : null}
          <div className="metadata-panel" aria-label="Labelling metadata">
            <label>
              <span>Source group key</span>
              <input
                value={sourceGroupKey}
                maxLength={100}
                onChange={(event) => setSourceGroupKey(event.target.value)}
                placeholder="Optional"
                data-testid="source-group-key-input"
              />
            </label>
            <label>
              <span>Image quality</span>
              <select
                value={imageQualityStatus}
                onChange={(event) => setImageQualityStatus(event.target.value as ImageQualityStatus)}
                data-testid="image-quality-select"
              >
                <option value="unassessed">Unassessed</option>
                <option value="usable">Usable</option>
                <option value="poor_quality">Poor quality</option>
                <option value="exclude">Exclude</option>
              </select>
            </label>
            <button
              type="button"
              onClick={() =>
                void onUpdateMetadata({
                  labellingSessionId: evidence.labellingSession.labellingSessionId,
                  sourceGroupKey,
                  imageQualityStatus
                })
              }
              disabled={labellingState?.kind === "working"}
              data-testid="save-labelling-metadata-button"
            >
              <Check size={18} />
              Save metadata
            </button>
          </div>

          <section
            className="evidence-panel"
            aria-label="AI-assisted draft annotations"
            data-testid="dataset-evidence-panel"
          >
            <div className="evidence-heading">
              <PanelHeading icon={<Image size={20} />} title="Draft suggestions" />
              <div className="evidence-legend" aria-label="Dataset overlay legend">
                <span className="legend-item complete">Complete visible bee</span>
                <span className="legend-item partial">Partial visible bee</span>
              </div>
            </div>
            <div
              className="photo-evidence"
              style={{
                aspectRatio: `${evidence.inspectionPhoto.width} / ${evidence.inspectionPhoto.height}`
              }}
              data-testid="dataset-photo-evidence"
            >
              <img
                src={imageUrl}
                alt={evidence.inspectionPhoto.filename}
                data-testid="dataset-evidence-image"
              />
              {evidence.draftAnnotations.map((annotation) => (
                <AnnotationBox
                  key={annotation.annotationId}
                  annotation={annotation}
                  selected={annotation.annotationId === selectedAnnotationId}
                  reviewerCapability
                  onSelect={() => setSelectedAnnotationId(annotation.annotationId)}
                />
              ))}
            </div>
            <p className="evidence-summary" data-testid="dataset-evidence-summary">
              {completeBeeCount} complete visible bee and {partialBeeCount} partial visible bee
              Draft Annotations from {evidence.labellingSession.prelabelerRun.prelabelerName}.
            </p>
          </section>

          <form
            className="review-panel"
            aria-label="Dataset labelling review decision"
            data-testid="dataset-review-controls"
            onSubmit={(event) => {
              event.preventDefault();
              if (!selectedAnnotationId) {
                return;
              }
              void onSubmitReviewDecision({
                annotationId: selectedAnnotationId,
                decision: "approved",
                notes
              });
            }}
          >
            <div>
              <strong>Curator review</strong>
              <p>Approve draft bee suggestions as reviewed annotation evidence only.</p>
            </div>
            <label>
              <span>Selected draft</span>
              <select
                value={selectedAnnotationId ?? ""}
                onChange={(event) => setSelectedAnnotationId(event.target.value || null)}
                data-testid="dataset-review-annotation-select"
              >
                <option value="">Choose a draft annotation</option>
                {evidence.draftAnnotations.map((annotation, index) => (
                  <option key={annotation.annotationId} value={annotation.annotationId}>
                    {index + 1}. {annotationLabel(annotation)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Notes</span>
              <textarea
                value={notes}
                maxLength={500}
                onChange={(event) => setNotes(event.target.value)}
                data-testid="dataset-review-notes-input"
              />
            </label>
            <button
              type="submit"
              disabled={!selectedAnnotationId || labellingState?.kind === "working"}
              data-testid="submit-dataset-review-decision-button"
            >
              <Check size={18} />
              Approve draft
            </button>
            <p className="review-state" data-testid="dataset-review-state">
              {selectedAnnotation?.latestReviewDecision
                ? `Latest decision: ${selectedAnnotation.latestReviewDecision.decision}`
                : `${evidence.reviewedAnnotations.length} reviewed annotations`}
            </p>
          </form>
          <form
            className="dataset-assignment-panel"
            aria-label="Dataset role assignment"
            data-testid="dataset-role-assignment-controls"
            onSubmit={(event) => {
              event.preventDefault();
              if (!evidence || !canAssignDatasetRole) {
                return;
              }
              void onAssignDatasetRole({
                labellingSessionId: evidence.labellingSession.labellingSessionId,
                datasetRole,
                assignmentNote,
                exclusionReason: datasetRole === "excluded" ? exclusionReason : null
              });
            }}
          >
            <div>
              <strong>Dataset assignment</strong>
              <p>
                Assign reviewed bee evidence to a dataset role once curator review is complete
                enough for this frame.
              </p>
            </div>
            <label>
              <span>Dataset role</span>
              <select
                value={datasetRole}
                onChange={(event) => setDatasetRole(event.target.value as DatasetRole)}
                disabled={Boolean(datasetItem)}
                data-testid="dataset-role-select"
              >
                <option value="training">Training</option>
                <option value="validation">Validation</option>
                <option value="benchmark">Benchmark</option>
                <option value="excluded">Excluded</option>
              </select>
            </label>
            {datasetRole === "excluded" ? (
              <label>
                <span>Exclusion reason</span>
                <select
                  value={exclusionReason}
                  onChange={(event) =>
                    setExclusionReason(event.target.value as DatasetExclusionReason)
                  }
                  disabled={Boolean(datasetItem)}
                  data-testid="dataset-exclusion-reason-select"
                >
                  <option value="poor_image_quality">Poor image quality</option>
                  <option value="ambiguous_subject">Ambiguous subject</option>
                  <option value="duplicate_or_near_duplicate">Duplicate or near duplicate</option>
                  <option value="privacy_concern">Privacy concern</option>
                  <option value="unsuitable_crop">Unsuitable crop</option>
                  <option value="insufficient_review_confidence">
                    Insufficient review confidence
                  </option>
                  <option value="other">Other</option>
                </select>
              </label>
            ) : null}
            <label>
              <span>Assignment note</span>
              <textarea
                value={assignmentNote}
                maxLength={500}
                onChange={(event) => setAssignmentNote(event.target.value)}
                disabled={Boolean(datasetItem)}
                data-testid="dataset-assignment-note-input"
              />
            </label>
            <button
              type="submit"
              disabled={!canAssignDatasetRole}
              data-testid="assign-dataset-role-button"
            >
              <ShieldCheck size={18} />
              Assign role
            </button>
            <p className="review-state" data-testid="dataset-item-state">
              {datasetItem
                ? `Dataset item: ${datasetItem.datasetRole}${
                    datasetItem.benchmarkProtected ? " / protected benchmark" : ""
                  } / ${datasetItem.reviewedAnnotationIds.length} reviewed annotations`
                : hasReviewedAnnotations
                  ? `${evidence.reviewedAnnotations.length} reviewed annotations ready`
                  : "Review at least one bee suggestion before assignment"}
            </p>
          </form>
          <p className="analysis-caveat" data-testid="dataset-evidence-caveat">
            {evidence.caveat}
          </p>
        </>
      ) : null}
    </section>
  );
}

function EvidencePanel({
  evidence,
  imageUrl,
  reviewerCapability,
  reviewState,
  onSubmitReviewDecision
}: {
  evidence: AnalysisEvidence;
  imageUrl: string;
  reviewerCapability: boolean;
  reviewState: { kind: "idle" | "working" | "done" } | null;
  onSubmitReviewDecision: (request: {
    annotationId: string;
    decision: ReviewDecisionValue;
    notes: string;
  }) => Promise<void>;
}) {
  const [selectedAnnotationId, setSelectedAnnotationId] = useState<string | null>(null);
  const [decision, setDecision] = useState<ReviewDecisionValue>("approved");
  const [notes, setNotes] = useState("");
  const completeBeeCount = evidence.annotations.filter(
    (annotation) => annotation.annotationType === "complete_visible_bee"
  ).length;
  const partialBeeCount = evidence.annotations.filter(
    (annotation) => annotation.annotationType === "partial_visible_bee"
  ).length;
  const selectedAnnotation = evidence.annotations.find(
    (annotation) => annotation.annotationId === selectedAnnotationId
  );

  return (
    <section className="evidence-panel" aria-label="Annotation evidence" data-testid="evidence-panel">
      <div className="evidence-heading">
        <PanelHeading icon={<Image size={20} />} title="Evidence" />
        <div className="evidence-legend" aria-label="Overlay legend">
          <span className="legend-item complete">Complete visible bee</span>
          <span className="legend-item partial">Partial visible bee</span>
        </div>
      </div>
      <div
        className="photo-evidence"
        style={{ aspectRatio: `${evidence.inspectionPhoto.width} / ${evidence.inspectionPhoto.height}` }}
        data-testid="photo-evidence"
      >
        <img src={imageUrl} alt={evidence.inspectionPhoto.filename} data-testid="evidence-image" />
        {evidence.annotations.map((annotation) => (
          <AnnotationBox
            key={annotation.annotationId}
            annotation={annotation}
            selected={annotation.annotationId === selectedAnnotationId}
            reviewerCapability={reviewerCapability}
            onSelect={() => setSelectedAnnotationId(annotation.annotationId)}
          />
        ))}
      </div>
      <p className="evidence-summary" data-testid="evidence-summary">
        {completeBeeCount} complete visible bees and {partialBeeCount} partial visible bee are
        shown from deterministic stub evidence.
      </p>
      {reviewerCapability ? (
        <form
          className="review-panel"
          aria-label="Annotation review decision"
          data-testid="annotation-review-controls"
          onSubmit={(event) => {
            event.preventDefault();
            if (!selectedAnnotationId) {
              return;
            }
            void onSubmitReviewDecision({ annotationId: selectedAnnotationId, decision, notes });
          }}
        >
          <div>
            <strong>Annotation review</strong>
            <p>Review evidence only. Dataset use is not assigned in this slice.</p>
          </div>
          <label>
            <span>Selected annotation</span>
            <select
              value={selectedAnnotationId ?? ""}
              onChange={(event) => setSelectedAnnotationId(event.target.value || null)}
              data-testid="review-annotation-select"
            >
              <option value="">Choose an annotation</option>
              {evidence.annotations.map((annotation, index) => (
                <option key={annotation.annotationId} value={annotation.annotationId}>
                  {index + 1}. {annotationLabel(annotation)}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Decision</span>
            <select
              value={decision}
              onChange={(event) => setDecision(event.target.value as ReviewDecisionValue)}
              data-testid="review-decision-select"
            >
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="uncertain">Uncertain</option>
              <option value="excluded">Excluded</option>
            </select>
          </label>
          <label>
            <span>Notes</span>
            <textarea
              value={notes}
              maxLength={500}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Optional"
              data-testid="review-notes-input"
            />
          </label>
          <button
            type="submit"
            disabled={!selectedAnnotationId || reviewState?.kind === "working"}
            data-testid="submit-review-decision-button"
          >
            <Check size={18} />
            {reviewState?.kind === "working" ? "Recording review" : "Record decision"}
          </button>
          <p className="review-state" data-testid="review-state">
            {selectedAnnotation?.latestReviewDecision
              ? `Latest decision: ${selectedAnnotation.latestReviewDecision.decision}`
              : reviewState?.kind === "done"
                ? "Review decision recorded"
                : "Selected annotation is unreviewed"}
          </p>
        </form>
      ) : null}
      <p className="analysis-caveat" data-testid="evidence-caveat">
        {evidence.caveat}
      </p>
    </section>
  );
}

function AnnotationBox({
  annotation,
  selected,
  reviewerCapability,
  onSelect
}: {
  annotation: Annotation;
  selected: boolean;
  reviewerCapability: boolean;
  onSelect: () => void;
}) {
  const className =
    annotation.annotationType === "complete_visible_bee"
      ? "annotation-box complete"
      : "annotation-box partial";
  const label =
    annotation.annotationType === "complete_visible_bee"
      ? "Complete visible bee"
      : "Partial visible bee";

  const style = {
    left: `${annotation.x * 100}%`,
    top: `${annotation.y * 100}%`,
    width: `${annotation.width * 100}%`,
    height: `${annotation.height * 100}%`
  };
  const title = `${label}, confidence ${Math.round(annotation.confidence * 100)}%`;

  if (!reviewerCapability) {
    return (
      <span
        className={className}
        data-testid="annotation-box"
        data-annotation-type={annotation.annotationType}
        data-review-decision={annotation.latestReviewDecision?.decision ?? "unreviewed"}
        style={style}
        title={title}
        aria-label={label}
      />
    );
  }

  return (
    <button
      type="button"
      className={`${className} ${selected ? "selected" : ""}`}
      data-testid="annotation-box"
      data-annotation-type={annotation.annotationType}
      data-review-decision={annotation.latestReviewDecision?.decision ?? "unreviewed"}
      style={style}
      title={title}
      aria-label={`${label}. ${annotation.latestReviewDecision?.decision ?? "Unreviewed"}`}
      onClick={onSelect}
    />
  );
}

function annotationLabel(annotation: Annotation): string {
  const type =
    annotation.annotationType === "complete_visible_bee"
      ? "Complete visible bee"
      : "Partial visible bee";
  return `${type} / ${annotation.latestReviewDecision?.decision ?? "unreviewed"}`;
}

function prelabelerProviderLabel(provider: "deterministic" | "grounding_dino"): string {
  return provider === "grounding_dino" ? "Grounding DINO" : "Deterministic";
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function toApiError(error: unknown): ApiError {
  if (
    typeof error === "object" &&
    error !== null &&
    "message" in error &&
    "code" in error &&
    "status" in error
  ) {
    return error as ApiError;
  }

  if (error instanceof Error) {
    return { code: "unexpected_error", message: error.message, status: 500 };
  }

  return { code: "unexpected_error", message: "The request could not be completed.", status: 500 };
}
