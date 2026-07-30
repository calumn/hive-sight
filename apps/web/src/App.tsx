import {
  Activity,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  Check,
  CircleAlert,
  CloudUpload,
  FileImage,
  FlaskConical,
  Image,
  LoaderCircle,
  Minus,
  Plus,
  RotateCcw,
  RefreshCw,
  RotateCw,
  ShieldCheck,
  Trash2
} from "lucide-react";
import { type FormEvent, type MouseEvent, type ReactNode, useEffect, useMemo, useState } from "react";
import {
  acceptWorkspaceDataUseAgreement,
  createTrainingCrop,
  createTrainingCropEllipse,
  createApiary,
  createHive,
  createInspection,
  createDatasetItem,
  createReviewDecision,
  deleteTrainingCropEllipse,
  fetchAnalysisEvidence,
  fetchCoreHealth,
  fetchDatasetLabellingEvidence,
  fetchDevSession,
  fetchInspectionPhotos,
  fetchInspectionPhotoObjectUrl,
  fetchTrainingCropEvidence,
  fetchTrainingCropsForPhoto,
  processAnalysisRun,
  startDatasetLabellingSession,
  updateTrainingCrop,
  updateTrainingCropEllipse,
  updateDatasetLabellingSessionMetadata,
  uploadInspectionPhoto,
  type AnalysisEvidence,
  type AnalysisRunDetail,
  type Annotation,
  type Apiary,
  type ApiError,
  type BeeAnnotationType,
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
  type OrientedBeeEllipse,
  type PhotoIntake,
  type ReviewDecisionValue,
  type TrainingCrop,
  type TrainingCropEvidence,
  type TrainingCropExclusionReason,
  type VisibleBeeStatus
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

type CropDraft = {
  cropX: number;
  cropY: number;
  cropWidth: number;
  cropHeight: number;
};

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
                  <>
                    <TrainingCropAnnotationPanel
                      devUserId={devUserId}
                      workspaceId={loadState.session.workspaceId}
                      photos={inspectionPhotos}
                      onError={(error) =>
                        setActionState({
                          kind: "blocked",
                          code: error.code,
                          message: error.message
                        })
                      }
                    />
                    <DatasetLabellingPanel
                      evidence={labellingEvidence}
                      imageUrl={labellingImageUrl}
                      labellingState={labellingState}
                      onStartDatasetLabelling={onStartDatasetLabelling}
                      onUpdateMetadata={onUpdateDatasetLabellingMetadata}
                      onSubmitReviewDecision={onSubmitDatasetLabellingReview}
                      onAssignDatasetRole={onAssignDatasetRole}
                    />
                  </>
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

function centerFixedCrop(sourceX: number, sourceY: number, sourceWidth: number, sourceHeight: number): CropDraft {
  const cropWidth = Math.min(640, sourceWidth);
  const cropHeight = Math.min(640, sourceHeight);
  return {
    cropX: Math.round(clamp(sourceX - cropWidth / 2, 0, sourceWidth - cropWidth)),
    cropY: Math.round(clamp(sourceY - cropHeight / 2, 0, sourceHeight - cropHeight)),
    cropWidth,
    cropHeight
  };
}

function clampDraft(
  draft: CropDraft,
  sourceImageSize: { width: number; height: number } | null
): CropDraft {
  if (!sourceImageSize) {
    return draft;
  }
  const cropWidth = Math.round(clamp(draft.cropWidth, 1, sourceImageSize.width));
  const cropHeight = Math.round(clamp(draft.cropHeight, 1, sourceImageSize.height));
  return {
    cropX: Math.round(clamp(draft.cropX, 0, sourceImageSize.width - cropWidth)),
    cropY: Math.round(clamp(draft.cropY, 0, sourceImageSize.height - cropHeight)),
    cropWidth,
    cropHeight
  };
}

function cropOverlayStyle(
  crop: CropDraft | TrainingCrop,
  sourceImageSize: { width: number; height: number } | null
) {
  if (!sourceImageSize) {
    return undefined;
  }
  return {
    left: `${(crop.cropX / sourceImageSize.width) * 100}%`,
    top: `${(crop.cropY / sourceImageSize.height) * 100}%`,
    width: `${(crop.cropWidth / sourceImageSize.width) * 100}%`,
    height: `${(crop.cropHeight / sourceImageSize.height) * 100}%`
  };
}

function cropImageStyle(crop: TrainingCrop) {
  return {
    left: `${(-crop.cropX / crop.cropWidth) * 100}%`,
    top: `${(-crop.cropY / crop.cropHeight) * 100}%`,
    width: `${(crop.sourceImageWidthPx / crop.cropWidth) * 100}%`,
    height: `${(crop.sourceImageHeightPx / crop.cropHeight) * 100}%`
  };
}

function ellipseStyle(crop: TrainingCrop, ellipse: OrientedBeeEllipse) {
  return {
    left: `${((ellipse.centerX - crop.cropX - ellipse.radiusX) / crop.cropWidth) * 100}%`,
    top: `${((ellipse.centerY - crop.cropY - ellipse.radiusY) / crop.cropHeight) * 100}%`,
    width: `${((ellipse.radiusX * 2) / crop.cropWidth) * 100}%`,
    height: `${((ellipse.radiusY * 2) / crop.cropHeight) * 100}%`,
    transform: `rotate(${ellipse.rotationDegrees}deg)`
  };
}

type EllipseGeometry = {
  centerX: number;
  centerY: number;
  radiusX: number;
  radiusY: number;
  rotationDegrees: number;
};

function nextEllipseGeometry(
  ellipse: OrientedBeeEllipse,
  values: Partial<EllipseGeometry>
): EllipseGeometry {
  return {
    centerX: values.centerX ?? ellipse.centerX,
    centerY: values.centerY ?? ellipse.centerY,
    radiusX: values.radiusX ?? ellipse.radiusX,
    radiusY: values.radiusY ?? ellipse.radiusY,
    rotationDegrees: values.rotationDegrees ?? ellipse.rotationDegrees
  };
}

function ellipseFitsInsideCrop(crop: TrainingCrop, ellipse: EllipseGeometry): boolean {
  if (ellipse.radiusX < 5 || ellipse.radiusY < 5) {
    return false;
  }
  const angle = (normalizeRotation(ellipse.rotationDegrees) * Math.PI) / 180;
  const xExtent = Math.sqrt(
    (ellipse.radiusX * Math.cos(angle)) ** 2 + (ellipse.radiusY * Math.sin(angle)) ** 2
  );
  const yExtent = Math.sqrt(
    (ellipse.radiusX * Math.sin(angle)) ** 2 + (ellipse.radiusY * Math.cos(angle)) ** 2
  );
  return (
    ellipse.centerX - xExtent >= crop.cropX &&
    ellipse.centerY - yExtent >= crop.cropY &&
    ellipse.centerX + xExtent <= crop.cropX + crop.cropWidth &&
    ellipse.centerY + yExtent <= crop.cropY + crop.cropHeight
  );
}

function canAdjustEllipse(
  crop: TrainingCrop | null,
  ellipse: OrientedBeeEllipse | null,
  values: Partial<EllipseGeometry>
): boolean {
  if (!crop || !ellipse) {
    return false;
  }
  return ellipseFitsInsideCrop(crop, nextEllipseGeometry(ellipse, values));
}

function normalizeRotation(rotationDegrees: number): number {
  return ((rotationDegrees % 360) + 360) % 360;
}

function formatGeometryValue(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.max(minimum, Math.min(maximum, value));
}

function CropOverlay({
  crop,
  sourceImageSize
}: {
  crop: CropDraft;
  sourceImageSize: { width: number; height: number } | null;
}) {
  return (
    <span
      className="crop-overlay draft"
      style={cropOverlayStyle(crop, sourceImageSize)}
      data-testid="training-draft-crop-overlay"
    />
  );
}

function NumberField({
  label,
  value,
  onChange,
  testId
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  testId: string;
}) {
  return (
    <label>
      <span>{label}</span>
      <input
        type="number"
        value={value}
        min={0}
        onChange={(event) => onChange(Number(event.target.value))}
        data-testid={testId}
      />
    </label>
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

function TrainingCropAnnotationPanel({
  devUserId,
  workspaceId,
  photos,
  onError
}: {
  devUserId: string;
  workspaceId: string;
  photos: InspectionPhoto[];
  onError: (error: ApiError) => void;
}) {
  const [selectedPhotoId, setSelectedPhotoId] = useState<string>("");
  const [sourceImageUrl, setSourceImageUrl] = useState<string | null>(null);
  const [sourceImageSize, setSourceImageSize] = useState<{ width: number; height: number } | null>(
    null
  );
  const [draftCrop, setDraftCrop] = useState<CropDraft | null>(null);
  const [crops, setCrops] = useState<TrainingCrop[]>([]);
  const [selectedCropId, setSelectedCropId] = useState<string | null>(null);
  const [evidence, setEvidence] = useState<TrainingCropEvidence | null>(null);
  const [selectedEllipseId, setSelectedEllipseId] = useState<string | null>(null);
  const [cropNotes, setCropNotes] = useState("Reviewed for bee annotation training evidence.");
  const [visibleBeeStatus, setVisibleBeeStatus] = useState<VisibleBeeStatus>("has_visible_bees");
  const [exclusionReason, setExclusionReason] =
    useState<TrainingCropExclusionReason>("unsuitable_crop");
  const [workingLabel, setWorkingLabel] = useState<string | null>(null);

  const selectedPhoto = photos.find((photo) => photo.inspectionPhotoId === selectedPhotoId) ?? null;
  const selectedCrop = evidence?.trainingCrop ?? crops.find((crop) => crop.trainingCropId === selectedCropId) ?? null;
  const selectedEllipse =
    evidence?.beeEllipses.find((ellipse) => ellipse.annotationId === selectedEllipseId) ?? null;
  const cropLocked =
    selectedCrop?.reviewStatus === "review_complete" || selectedCrop?.reviewStatus === "excluded";
  const controlLocked = !selectedEllipse || cropLocked || Boolean(workingLabel);
  const canNudgeLeft = canAdjustEllipse(selectedCrop, selectedEllipse, {
    centerX: (selectedEllipse?.centerX ?? 0) - 5
  });
  const canNudgeRight = canAdjustEllipse(selectedCrop, selectedEllipse, {
    centerX: (selectedEllipse?.centerX ?? 0) + 5
  });
  const canNudgeUp = canAdjustEllipse(selectedCrop, selectedEllipse, {
    centerY: (selectedEllipse?.centerY ?? 0) - 5
  });
  const canNudgeDown = canAdjustEllipse(selectedCrop, selectedEllipse, {
    centerY: (selectedEllipse?.centerY ?? 0) + 5
  });
  const canRotateClockwise = canAdjustEllipse(selectedCrop, selectedEllipse, {
    rotationDegrees: (selectedEllipse?.rotationDegrees ?? 0) + 5
  });
  const canRotateAntiClockwise = canAdjustEllipse(selectedCrop, selectedEllipse, {
    rotationDegrees: (selectedEllipse?.rotationDegrees ?? 0) - 5
  });
  const canShrinkRadiusX = canAdjustEllipse(selectedCrop, selectedEllipse, {
    radiusX: (selectedEllipse?.radiusX ?? 0) - 5
  });
  const canGrowRadiusX = canAdjustEllipse(selectedCrop, selectedEllipse, {
    radiusX: (selectedEllipse?.radiusX ?? 0) + 5
  });
  const canShrinkRadiusY = canAdjustEllipse(selectedCrop, selectedEllipse, {
    radiusY: (selectedEllipse?.radiusY ?? 0) - 5
  });
  const canGrowRadiusY = canAdjustEllipse(selectedCrop, selectedEllipse, {
    radiusY: (selectedEllipse?.radiusY ?? 0) + 5
  });

  useEffect(() => {
    if (photos.length === 0) {
      setSelectedPhotoId("");
      return;
    }
    setSelectedPhotoId((current) =>
      photos.some((photo) => photo.inspectionPhotoId === current)
        ? current
        : photos[0].inspectionPhotoId
    );
  }, [photos]);

  useEffect(() => {
    if (!selectedPhoto) {
      setSourceImageUrl((current) => {
        if (current) URL.revokeObjectURL(current);
        return null;
      });
      setSourceImageSize(null);
      setDraftCrop(null);
      setCrops([]);
      setEvidence(null);
      setSelectedCropId(null);
      return;
    }

    let cancelled = false;
    fetchInspectionPhotoObjectUrl({
      devUserId,
      viewUrl: `/v1/inspection-photos/${selectedPhoto.inspectionPhotoId}/content?workspace_id=${workspaceId}`
    })
      .then((nextImageUrl) => {
        if (cancelled) {
          URL.revokeObjectURL(nextImageUrl);
          return;
        }
        setSourceImageUrl((current) => {
          if (current) URL.revokeObjectURL(current);
          return nextImageUrl;
        });
        setSourceImageSize(null);
        setDraftCrop(null);
        setSelectedEllipseId(null);
        void refreshCropsForPhoto(selectedPhoto.inspectionPhotoId);
      })
      .catch((error) => onError(toApiError(error)));

    return () => {
      cancelled = true;
    };
  }, [devUserId, onError, selectedPhoto, workspaceId]);

  useEffect(() => {
    if (!selectedCropId) {
      setEvidence(null);
      return;
    }
    void refreshEvidence(selectedCropId);
  }, [selectedCropId]);

  async function runCropAction(label: string, action: () => Promise<void>) {
    setWorkingLabel(label);
    try {
      await action();
    } catch (error) {
      onError(toApiError(error));
    } finally {
      setWorkingLabel(null);
    }
  }

  async function refreshCropsForPhoto(inspectionPhotoId: string) {
    const listing = await fetchTrainingCropsForPhoto({
      devUserId,
      workspaceId,
      inspectionPhotoId
    });
    setCrops(listing.trainingCrops);
    setSelectedCropId((current) =>
      current && listing.trainingCrops.some((crop) => crop.trainingCropId === current)
        ? current
        : (listing.trainingCrops.at(-1)?.trainingCropId ?? null)
    );
  }

  async function refreshEvidence(trainingCropId: string) {
    const nextEvidence = await fetchTrainingCropEvidence({
      devUserId,
      workspaceId,
      trainingCropId
    });
    setEvidence(nextEvidence);
    setVisibleBeeStatus(nextEvidence.trainingCrop.visibleBeeStatus);
    setCropNotes(nextEvidence.trainingCrop.notes ?? "");
    setSelectedEllipseId((current) =>
      current && nextEvidence.beeEllipses.some((ellipse) => ellipse.annotationId === current)
        ? current
        : (nextEvidence.beeEllipses.at(-1)?.annotationId ?? null)
    );
  }

  function onSourceImageClick(event: MouseEvent<HTMLDivElement>) {
    if (!sourceImageSize) {
      return;
    }
    const rect = event.currentTarget.getBoundingClientRect();
    const sourceX = ((event.clientX - rect.left) / rect.width) * sourceImageSize.width;
    const sourceY = ((event.clientY - rect.top) / rect.height) * sourceImageSize.height;
    setDraftCrop(centerFixedCrop(sourceX, sourceY, sourceImageSize.width, sourceImageSize.height));
  }

  async function onSaveDraftCrop() {
    if (!selectedPhoto || !sourceImageSize || !draftCrop) {
      return;
    }
    await runCropAction("Saving Training Crop", async () => {
      const crop = await createTrainingCrop({
        devUserId,
        workspaceId,
        inspectionPhotoId: selectedPhoto.inspectionPhotoId,
        cropX: draftCrop.cropX,
        cropY: draftCrop.cropY,
        cropWidth: draftCrop.cropWidth,
        cropHeight: draftCrop.cropHeight,
        sourceImageWidthPx: sourceImageSize.width,
        sourceImageHeightPx: sourceImageSize.height,
        notes: cropNotes
      });
      setDraftCrop(null);
      await refreshCropsForPhoto(selectedPhoto.inspectionPhotoId);
      setSelectedCropId(crop.trainingCropId);
    });
  }

  async function onCropSurfaceClick(event: MouseEvent<HTMLDivElement>) {
    if (!selectedCrop || cropLocked || selectedCrop.visibleBeeStatus === "no_visible_bees") {
      return;
    }
    const rect = event.currentTarget.getBoundingClientRect();
    const centerX = selectedCrop.cropX + ((event.clientX - rect.left) / rect.width) * selectedCrop.cropWidth;
    const centerY =
      selectedCrop.cropY + ((event.clientY - rect.top) / rect.height) * selectedCrop.cropHeight;
    await runCropAction("Adding bee ellipse", async () => {
      const ellipse = await createTrainingCropEllipse({
        devUserId,
        workspaceId,
        trainingCropId: selectedCrop.trainingCropId,
        annotationType: "complete_visible_bee",
        centerX: clamp(centerX, selectedCrop.cropX + 40, selectedCrop.cropX + selectedCrop.cropWidth - 40),
        centerY: clamp(centerY, selectedCrop.cropY + 20, selectedCrop.cropY + selectedCrop.cropHeight - 20),
        radiusX: 40,
        radiusY: 20,
        rotationDegrees: 0
      });
      setSelectedEllipseId(ellipse.annotationId);
      await refreshEvidence(selectedCrop.trainingCropId);
    });
  }

  async function updateSelectedEllipse(values: Partial<OrientedBeeEllipse>) {
    if (!selectedCrop || !selectedEllipse || cropLocked) {
      return;
    }
    await runCropAction("Updating bee ellipse", async () => {
      await updateTrainingCropEllipse({
        devUserId,
        workspaceId,
        annotationId: selectedEllipse.annotationId,
        annotationType: values.annotationType,
        centerX: values.centerX,
        centerY: values.centerY,
        radiusX: values.radiusX,
        radiusY: values.radiusY,
        rotationDegrees: values.rotationDegrees
      });
      await refreshEvidence(selectedCrop.trainingCropId);
    });
  }

  async function deleteSelectedEllipse() {
    if (!selectedCrop || !selectedEllipse || cropLocked) {
      return;
    }
    await runCropAction("Deleting bee ellipse", async () => {
      await deleteTrainingCropEllipse({
        devUserId,
        workspaceId,
        annotationId: selectedEllipse.annotationId
      });
      setSelectedEllipseId(null);
      await refreshEvidence(selectedCrop.trainingCropId);
    });
  }

  async function completeCrop(reviewVisibleBeeStatus: VisibleBeeStatus) {
    if (!selectedCrop) {
      return;
    }
    await runCropAction("Completing Training Crop", async () => {
      await updateTrainingCrop({
        devUserId,
        workspaceId,
        trainingCropId: selectedCrop.trainingCropId,
        visibleBeeStatus: reviewVisibleBeeStatus,
        reviewStatus: "review_complete",
        notes: cropNotes
      });
      await refreshEvidence(selectedCrop.trainingCropId);
      if (selectedPhoto) await refreshCropsForPhoto(selectedPhoto.inspectionPhotoId);
    });
  }

  async function excludeCrop() {
    if (!selectedCrop) {
      return;
    }
    await runCropAction("Excluding Training Crop", async () => {
      await updateTrainingCrop({
        devUserId,
        workspaceId,
        trainingCropId: selectedCrop.trainingCropId,
        reviewStatus: "excluded",
        exclusionReason,
        notes: cropNotes
      });
      await refreshEvidence(selectedCrop.trainingCropId);
      if (selectedPhoto) await refreshCropsForPhoto(selectedPhoto.inspectionPhotoId);
    });
  }

  return (
    <section
      className="analysis-panel training-crop-panel"
      aria-label="Training Crop annotation"
      data-testid="training-crop-panel"
    >
      <div className="analysis-header">
        <PanelHeading icon={<Image size={20} />} title="Training crops" />
        <span className="analysis-status status-queued">{crops.length} crops</span>
      </div>

      {photos.length === 0 ? (
        <p className="analysis-caveat">Upload a training data photo before creating crops.</p>
      ) : (
        <>
          <div className="metadata-panel crop-photo-controls">
            <label>
              <span>Source photo</span>
              <select
                value={selectedPhotoId}
                onChange={(event) => setSelectedPhotoId(event.target.value)}
                data-testid="training-crop-photo-select"
              >
                {photos.map((photo) => (
                  <option key={photo.inspectionPhotoId} value={photo.inspectionPhotoId}>
                    {photo.filename}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Notes</span>
              <input
                value={cropNotes}
                maxLength={500}
                onChange={(event) => setCropNotes(event.target.value)}
                data-testid="training-crop-notes-input"
              />
            </label>
            <button type="button" onClick={() => selectedPhoto && void refreshCropsForPhoto(selectedPhoto.inspectionPhotoId)}>
              <RefreshCw size={18} />
              Refresh
            </button>
          </div>

          {sourceImageUrl ? (
            <div
              className="source-photo-preview"
              onClick={onSourceImageClick}
              data-testid="training-source-photo-preview"
            >
              <img
                src={sourceImageUrl}
                alt={selectedPhoto?.filename ?? "Training source"}
                onLoad={(event) =>
                  setSourceImageSize({
                    width: event.currentTarget.naturalWidth,
                    height: event.currentTarget.naturalHeight
                  })
                }
                data-testid="training-source-image"
              />
              {draftCrop ? <CropOverlay crop={draftCrop} sourceImageSize={sourceImageSize} /> : null}
              {crops.map((crop) => (
                <button
                  key={crop.trainingCropId}
                  type="button"
                  className={`crop-overlay saved ${crop.trainingCropId === selectedCropId ? "selected" : ""}`}
                  style={cropOverlayStyle(crop, sourceImageSize)}
                  onClick={(event) => {
                    event.stopPropagation();
                    setSelectedCropId(crop.trainingCropId);
                  }}
                  data-testid="saved-training-crop-overlay"
                  aria-label={`Training Crop ${crop.reviewStatus}`}
                />
              ))}
            </div>
          ) : null}

          {draftCrop ? (
            <div className="metadata-panel crop-draft-controls" data-testid="training-crop-draft-controls">
              <NumberField label="X" value={draftCrop.cropX} onChange={(cropX) => setDraftCrop(clampDraft({ ...draftCrop, cropX }, sourceImageSize))} testId="training-crop-x-input" />
              <NumberField label="Y" value={draftCrop.cropY} onChange={(cropY) => setDraftCrop(clampDraft({ ...draftCrop, cropY }, sourceImageSize))} testId="training-crop-y-input" />
              <NumberField label="Width" value={draftCrop.cropWidth} onChange={(cropWidth) => setDraftCrop(clampDraft({ ...draftCrop, cropWidth }, sourceImageSize))} testId="training-crop-width-input" />
              <NumberField label="Height" value={draftCrop.cropHeight} onChange={(cropHeight) => setDraftCrop(clampDraft({ ...draftCrop, cropHeight }, sourceImageSize))} testId="training-crop-height-input" />
              <button
                type="button"
                onClick={() => void onSaveDraftCrop()}
                disabled={Boolean(workingLabel)}
                data-testid="save-training-crop-button"
              >
                <Check size={18} />
                Save crop
              </button>
            </div>
          ) : null}

          {crops.length > 0 ? (
            <ul className="crop-list" data-testid="training-crop-list">
              {crops.map((crop, index) => (
                <li key={crop.trainingCropId}>
                  <button
                    type="button"
                    className={crop.trainingCropId === selectedCropId ? "selected-row" : ""}
                    onClick={() => setSelectedCropId(crop.trainingCropId)}
                    data-testid="training-crop-list-item"
                  >
                    Crop {index + 1} / {crop.reviewStatus} / {crop.visibleBeeStatus}
                  </button>
                </li>
              ))}
            </ul>
          ) : null}

          {selectedCrop && sourceImageUrl ? (
            <section className="crop-editor" aria-label="Selected Training Crop editor">
              <div className="crop-editing-tool" data-testid="training-crop-editing-tool">
                <div
                  className="crop-surface"
                  style={{ aspectRatio: `${selectedCrop.cropWidth} / ${selectedCrop.cropHeight}` }}
                  onClick={(event) => void onCropSurfaceClick(event)}
                  data-testid="training-crop-surface"
                >
                  <img
                    src={sourceImageUrl}
                    alt="Selected Training Crop"
                    style={cropImageStyle(selectedCrop)}
                    draggable={false}
                  />
                  {evidence?.beeEllipses.map((ellipse) => (
                    <button
                      key={ellipse.annotationId}
                      type="button"
                      className={`bee-ellipse ${
                        ellipse.annotationType === "partial_visible_bee" ? "partial" : "complete"
                      } ${ellipse.annotationId === selectedEllipseId ? "selected" : ""}`}
                      style={ellipseStyle(selectedCrop, ellipse)}
                      onClick={(event) => {
                        event.stopPropagation();
                        setSelectedEllipseId(ellipse.annotationId);
                      }}
                      data-testid="training-crop-ellipse"
                      aria-label={ellipse.annotationType}
                    />
                  ))}
                </div>

                <div
                  className="crop-ellipse-controls"
                  data-testid="training-crop-review-controls"
                  aria-label="Selected ellipse controls"
                >
                  <div>
                    <strong>Ellipse controls</strong>
                    <p data-testid="selected-training-ellipse-label">
                      {selectedEllipse
                        ? `${selectedEllipse.annotationType} / ${formatGeometryValue(
                            normalizeRotation(selectedEllipse.rotationDegrees)
                          )} degrees`
                        : "Click inside the crop to add a default bee ellipse."}
                    </p>
                  </div>
                  <dl className="geometry-values" data-testid="training-ellipse-geometry-values">
                    <div>
                      <dt>X</dt>
                      <dd data-testid="training-ellipse-center-x">
                        {selectedEllipse ? formatGeometryValue(selectedEllipse.centerX) : "-"}
                      </dd>
                    </div>
                    <div>
                      <dt>Y</dt>
                      <dd data-testid="training-ellipse-center-y">
                        {selectedEllipse ? formatGeometryValue(selectedEllipse.centerY) : "-"}
                      </dd>
                    </div>
                    <div>
                      <dt>Rx</dt>
                      <dd data-testid="training-ellipse-radius-x">
                        {selectedEllipse ? formatGeometryValue(selectedEllipse.radiusX) : "-"}
                      </dd>
                    </div>
                    <div>
                      <dt>Ry</dt>
                      <dd data-testid="training-ellipse-radius-y">
                        {selectedEllipse ? formatGeometryValue(selectedEllipse.radiusY) : "-"}
                      </dd>
                    </div>
                    <div>
                      <dt>Rot</dt>
                      <dd data-testid="training-ellipse-rotation">
                        {selectedEllipse
                          ? formatGeometryValue(normalizeRotation(selectedEllipse.rotationDegrees))
                          : "-"}
                      </dd>
                    </div>
                  </dl>
                  <label>
                    <span>Bee type</span>
                    <select
                      value={selectedEllipse?.annotationType ?? "complete_visible_bee"}
                      onChange={(event) =>
                        selectedEllipse &&
                        void updateSelectedEllipse({
                          annotationType: event.target.value as BeeAnnotationType
                        })
                      }
                      disabled={controlLocked}
                      data-testid="training-ellipse-type-select"
                    >
                      <option value="complete_visible_bee">Complete visible bee</option>
                      <option value="partial_visible_bee">Partial visible bee</option>
                    </select>
                  </label>
                  <div className="control-cluster" aria-label="Move selected ellipse">
                    <button
                      type="button"
                      disabled={controlLocked || !canNudgeUp}
                      onClick={() =>
                        selectedEllipse &&
                        void updateSelectedEllipse({ centerY: selectedEllipse.centerY - 5 })
                      }
                      data-testid="nudge-training-ellipse-up-button"
                      title="Nudge up"
                    >
                      <ArrowUp size={18} />
                      Up
                    </button>
                    <button
                      type="button"
                      disabled={controlLocked || !canNudgeLeft}
                      onClick={() =>
                        selectedEllipse &&
                        void updateSelectedEllipse({ centerX: selectedEllipse.centerX - 5 })
                      }
                      data-testid="nudge-training-ellipse-left-button"
                      title="Nudge left"
                    >
                      <ArrowLeft size={18} />
                      Left
                    </button>
                    <button
                      type="button"
                      disabled={controlLocked || !canNudgeRight}
                      onClick={() =>
                        selectedEllipse &&
                        void updateSelectedEllipse({ centerX: selectedEllipse.centerX + 5 })
                      }
                      data-testid="nudge-training-ellipse-right-button"
                      title="Nudge right"
                    >
                      <ArrowRight size={18} />
                      Right
                    </button>
                    <button
                      type="button"
                      disabled={controlLocked || !canNudgeDown}
                      onClick={() =>
                        selectedEllipse &&
                        void updateSelectedEllipse({ centerY: selectedEllipse.centerY + 5 })
                      }
                      data-testid="nudge-training-ellipse-down-button"
                      title="Nudge down"
                    >
                      <ArrowDown size={18} />
                      Down
                    </button>
                  </div>
                  <div className="control-cluster" aria-label="Rotate selected ellipse">
                    <button
                      type="button"
                      disabled={controlLocked || !canRotateAntiClockwise}
                      onClick={() =>
                        selectedEllipse &&
                        void updateSelectedEllipse({
                          rotationDegrees: selectedEllipse.rotationDegrees - 5
                        })
                      }
                      data-testid="rotate-training-ellipse-anticlockwise-button"
                      title="Rotate anti-clockwise"
                    >
                      <RotateCcw size={18} />
                      Rotate -
                    </button>
                    <button
                      type="button"
                      disabled={controlLocked || !canRotateClockwise}
                      onClick={() =>
                        selectedEllipse &&
                        void updateSelectedEllipse({
                          rotationDegrees: selectedEllipse.rotationDegrees + 5
                        })
                      }
                      data-testid="rotate-training-ellipse-button"
                      title="Rotate clockwise"
                    >
                      <RotateCw size={18} />
                      Rotate +
                    </button>
                  </div>
                  <div className="control-cluster" aria-label="Resize selected ellipse">
                    <button
                      type="button"
                      disabled={controlLocked || !canShrinkRadiusX}
                      onClick={() =>
                        selectedEllipse &&
                        void updateSelectedEllipse({ radiusX: selectedEllipse.radiusX - 5 })
                      }
                      data-testid="shrink-training-ellipse-x-button"
                      title="Reduce horizontal radius"
                    >
                      <Minus size={18} />
                      Rx
                    </button>
                    <button
                      type="button"
                      disabled={controlLocked || !canGrowRadiusX}
                      onClick={() =>
                        selectedEllipse &&
                        void updateSelectedEllipse({ radiusX: selectedEllipse.radiusX + 5 })
                      }
                      data-testid="grow-training-ellipse-x-button"
                      title="Increase horizontal radius"
                    >
                      <Plus size={18} />
                      Rx
                    </button>
                    <button
                      type="button"
                      disabled={controlLocked || !canShrinkRadiusY}
                      onClick={() =>
                        selectedEllipse &&
                        void updateSelectedEllipse({ radiusY: selectedEllipse.radiusY - 5 })
                      }
                      data-testid="shrink-training-ellipse-y-button"
                      title="Reduce vertical radius"
                    >
                      <Minus size={18} />
                      Ry
                    </button>
                    <button
                      type="button"
                      disabled={controlLocked || !canGrowRadiusY}
                      onClick={() =>
                        selectedEllipse &&
                        void updateSelectedEllipse({ radiusY: selectedEllipse.radiusY + 5 })
                      }
                      data-testid="grow-training-ellipse-y-button"
                      title="Increase vertical radius"
                    >
                      <Plus size={18} />
                      Ry
                    </button>
                  </div>
                  <button
                    type="button"
                    disabled={controlLocked}
                    onClick={() => void deleteSelectedEllipse()}
                    data-testid="delete-training-ellipse-button"
                  >
                    <Trash2 size={18} />
                    Delete ellipse
                  </button>
                </div>
              </div>

              <div className="result-grid crop-metrics" data-testid="training-crop-metrics">
                <Metric label="Review" value={selectedCrop.reviewStatus} />
                <Metric label="Visible bees" value={selectedCrop.visibleBeeStatus} />
                <Metric label="Ellipses" value={evidence?.beeEllipses.length ?? 0} />
                <Metric label="Coordinates" value="source px" />
              </div>

              <div className="metadata-panel crop-completion-controls">
                <label>
                  <span>Visible bee status</span>
                  <select
                    value={visibleBeeStatus}
                    onChange={(event) => setVisibleBeeStatus(event.target.value as VisibleBeeStatus)}
                    disabled={cropLocked}
                    data-testid="training-crop-visible-status-select"
                  >
                    <option value="has_visible_bees">Has visible bees</option>
                    <option value="no_visible_bees">No visible bees</option>
                    <option value="unassessed">Unassessed</option>
                  </select>
                </label>
                <label>
                  <span>Exclusion reason</span>
                  <select
                    value={exclusionReason}
                    onChange={(event) =>
                      setExclusionReason(event.target.value as TrainingCropExclusionReason)
                    }
                    disabled={cropLocked}
                    data-testid="training-crop-exclusion-reason-select"
                  >
                    <option value="poor_image_quality">Poor image quality</option>
                    <option value="no_visible_bees">No visible bees</option>
                    <option value="ambiguous_subject">Ambiguous subject</option>
                    <option value="unsuitable_crop">Unsuitable crop</option>
                    <option value="duplicate_or_near_duplicate">Duplicate or near duplicate</option>
                    <option value="other">Other</option>
                  </select>
                </label>
                <button
                  type="button"
                  disabled={cropLocked || Boolean(workingLabel)}
                  onClick={() => void completeCrop(visibleBeeStatus)}
                  data-testid="complete-training-crop-button"
                >
                  <Check size={18} />
                  Complete crop
                </button>
                <button
                  type="button"
                  disabled={cropLocked || Boolean(workingLabel)}
                  onClick={() => void excludeCrop()}
                  data-testid="exclude-training-crop-button"
                >
                  <CircleAlert size={18} />
                  Exclude
                </button>
              </div>
            </section>
          ) : null}

          {workingLabel ? (
            <div className="outcome working" role="status">
              <LoaderCircle className="spin" size={20} />
              <span>{workingLabel}</span>
            </div>
          ) : null}
        </>
      )}
    </section>
  );
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
