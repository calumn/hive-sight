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
  createReviewDecision,
  fetchAnalysisEvidence,
  fetchCoreHealth,
  fetchDevSession,
  fetchInspectionPhotoObjectUrl,
  processAnalysisRun,
  uploadInspectionPhoto,
  type AnalysisEvidence,
  type AnalysisRunDetail,
  type Annotation,
  type Apiary,
  type ApiError,
  type DevSession,
  type HealthResponse,
  type Hive,
  type Inspection,
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
  const [analysisDetail, setAnalysisDetail] = useState<AnalysisRunDetail | null>(null);
  const [analysisEvidence, setAnalysisEvidence] = useState<AnalysisEvidence | null>(null);
  const [evidenceImageUrl, setEvidenceImageUrl] = useState<string | null>(null);
  const [reviewState, setReviewState] = useState<{ kind: "idle" | "working" | "done" } | null>(
    null
  );
  const [apiaryName, setApiaryName] = useState("Home apiary");
  const [hiveName, setHiveName] = useState("Hive A");
  const [inspectionDate, setInspectionDate] = useState(new Date().toISOString().slice(0, 10));
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
    };
  }, [evidenceImageUrl]);

  const session = loadState.kind === "ready" ? loadState.session : null;
  const termsAccepted = session?.workspaceDataUseAgreementStatus === "accepted";
  const canCreateHive = Boolean(apiary);
  const canCreateInspection = Boolean(hive);
  const canUpload = Boolean(termsAccepted && inspection && file);
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
      setAnalysisDetail(null);
      clearEvidenceImage();
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
      setAnalysisDetail(null);
      clearEvidenceImage();
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
        inspectionDate
      });
      setInspection(created);
      setAnalysisDetail(null);
      clearEvidenceImage();
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
      setAnalysisDetail(null);
      clearEvidenceImage();
      setActionState({ kind: "accepted", intake });
    });
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

  function clearEvidenceImage() {
    setAnalysisEvidence(null);
    setEvidenceImageUrl((current) => {
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
                <button
                  type="submit"
                  disabled={!canCreateInspection || actionState.kind === "working"}
                  data-testid="create-inspection-button"
                >
                  Create inspection
                </button>
                <RecordBadge value={inspection?.inspectionId} />
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

            <Outcome state={actionState} analysisDetail={analysisDetail} />
            {actionState.kind === "accepted" ? (
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
