import {
  Activity,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  BookOpen,
  Check,
  CircleAlert,
  CloudUpload,
  FileImage,
  FlaskConical,
  Image,
  LoaderCircle,
  Minus,
  Play,
  Plus,
  RotateCcw,
  RefreshCw,
  RotateCw,
  ShieldCheck,
  Trash2
} from "lucide-react";
import {
  type FormEvent,
  type MouseEvent,
  type ReactNode,
  useEffect,
  useMemo,
  useRef,
  useState
} from "react";
import {
  acceptWorkspaceDataUseAgreement,
  abandonTrainingRun,
  cancelBenchmarkEvaluation,
  cancelReviewWorkItem,
  cancelTrainingRun,
  completeReviewWorkItem,
  createTrainingCrop,
  createTrainingCropEllipse,
  createApiary,
  createHive,
  createInspection,
  createDatasetItem,
  createTrainingCropDatasetItem,
  createPhysicalYoloObbExport,
  createDatasetVersion,
  createYoloObbExport,
  createReviewDecision,
  deleteTrainingRun,
  deleteTrainingCropEllipse,
  fetchAnalysisEvidence,
  fetchApiaries,
  fetchCoreHealth,
  fetchDatasetLabellingEvidence,
  fetchDatasetRepositoryItemDetail,
  fetchDatasetRepositoryItems,
  fetchDevSession,
  fetchDevUsers,
  fetchFrameStandards,
  fetchHiveConfiguration,
  fetchHives,
  fetchHiveInspections,
  fetchInspectionPhotos,
  fetchInspectionPhotoObjectUrl,
  fetchBenchmarkEvaluationReadiness,
  fetchBenchmarkEvaluations,
  fetchModelCandidates,
  fetchModelTrainingReadiness,
  fetchRequestedReviews,
  fetchReviewHistory,
  fetchReviewQueueImageObjectUrl,
  fetchReviewWork,
  fetchReviewWorkItem,
  fetchTrainingRuns,
  fetchTrainingCropEvidence,
  fetchTrainingCropsForPhoto,
  processAnalysisRun,
  requestTrainingCropReview,
  startDatasetLabellingSession,
  startBenchmarkEvaluation,
  startModelTrainingRun,
  suggestTrainingCropBeeAnnotations,
  toCoreApiContentUrl,
  updateTrainingCrop,
  updateTrainingCropEllipse,
  upsertHiveConfiguration,
  updateDatasetLabellingSessionMetadata,
  uploadInspectionPhoto,
  type AnalysisEvidence,
  type AnalysisRunDetail,
  type Annotation,
  type Apiary,
  type ApiError,
  type BeeAnnotationType,
  type BeeAnnotationProposal,
  type BenchmarkEvaluation,
  type BenchmarkEvaluationReadiness,
  type DevSession,
  type HealthResponse,
  type Hive,
  type HiveConfiguration,
  type DatasetLabellingEvidence,
  type DatasetExclusionReason,
  type DatasetItem,
  type DatasetRepositoryItem,
  type DatasetRepositoryItemDetail,
  type DatasetRepositorySummary,
  type DatasetVersion,
  type DatasetVersionMembership,
  type DatasetRole,
  type DevUser,
  type ImageQualityStatus,
  type Inspection,
  type InspectionIntent,
  type InspectionPhoto,
  type FrameStandard,
  type OrientedBeeEllipse,
  type PhysicalYoloObbExport,
  type PhotoIntake,
  type ReviewDecisionValue,
  type ReviewQueueItem,
  type ReviewQueueOutcomeValue,
  type ModelTrainingReadiness,
  type ModelCandidate,
  type TrainingRun,
  type TrainingCrop,
  type TrainingCropEvidence,
  type TrainingCropExclusionReason,
  type VisibleBeeStatus,
  type YoloObbExport
} from "./coreApiClient";

const defaultDevUserId = "00000000-0000-0000-0000-000000000101";
const devUserStorageKey = "hivesight.developmentUserId";
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

type AppView = "inspection" | "repository" | "review-work";

export function App() {
  const trainingCropPanelRef = useRef<HTMLDivElement | null>(null);
  const [loadState, setLoadState] = useState<LoadState>({ kind: "loading" });
  const [selectedDevUserId, setSelectedDevUserId] = useState(() => {
    return window.localStorage.getItem(devUserStorageKey) ?? defaultDevUserId;
  });
  const [devUsers, setDevUsers] = useState<DevUser[]>([]);
  const [devUserSwitchingAvailable, setDevUserSwitchingAvailable] = useState(false);
  const [appView, setAppView] = useState<AppView>("inspection");
  const [actionState, setActionState] = useState<ActionState>({ kind: "idle" });
  const [apiaries, setApiaries] = useState<Apiary[]>([]);
  const [apiary, setApiary] = useState<Apiary | null>(null);
  const [hives, setHives] = useState<Hive[]>([]);
  const [hive, setHive] = useState<Hive | null>(null);
  const [frameStandards, setFrameStandards] = useState<FrameStandard[]>([]);
  const [selectedFrameStandardId, setSelectedFrameStandardId] = useState(
    "british_national_deep_brood"
  );
  const [hiveConfigurationNotes, setHiveConfigurationNotes] = useState("");
  const [hiveConfiguration, setHiveConfiguration] = useState<HiveConfiguration | null>(null);
  const [trainingInspections, setTrainingInspections] = useState<Inspection[]>([]);
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
    useState<InspectionIntent>("training_data_collection");
  const [file, setFile] = useState<File | null>(null);
  const devUserId = selectedDevUserId;

  useEffect(() => {
    let cancelled = false;

    async function loadWorkspaceForDevelopmentUser() {
      setLoadState({ kind: "loading" });
      clearUserScopedState();
      try {
        const health = await fetchCoreHealth();
        let activeDevUserId = selectedDevUserId;
        try {
          const devUserListing = await fetchDevUsers();
          if (cancelled) {
            return;
          }
          setDevUsers(devUserListing.devUsers);
          setDevUserSwitchingAvailable(true);
          const selectedDevUserIsAvailable = devUserListing.devUsers.some(
            (devUser) => devUser.userId === activeDevUserId
          );
          if (!selectedDevUserIsAvailable) {
            const fallbackDevUserId =
              devUserListing.devUsers.find((devUser) => devUser.isDefault)?.userId ??
              defaultDevUserId;
            window.localStorage.setItem(devUserStorageKey, fallbackDevUserId);
            if (fallbackDevUserId !== selectedDevUserId) {
              setSelectedDevUserId(fallbackDevUserId);
              return;
            }
            activeDevUserId = fallbackDevUserId;
          }
        } catch (error) {
          if (cancelled) {
            return;
          }
          setDevUsers([]);
          setDevUserSwitchingAvailable(false);
          activeDevUserId = defaultDevUserId;
        }

        const [session, standards] = await Promise.all([
          fetchDevSession(activeDevUserId),
          fetchFrameStandards({ devUserId: activeDevUserId })
        ]);
        if (cancelled) {
          return;
        }
        setFrameStandards(standards);
        if (!standards.some((standard) => standard.frameStandardId === "british_national_deep_brood")) {
          setSelectedFrameStandardId(standards[0]?.frameStandardId ?? "");
        }
        await refreshWorkspaceContext(session.workspaceId, undefined, undefined, activeDevUserId);
        if (cancelled) {
          return;
        }
        setLoadState({ kind: "ready", health, session });
      } catch (error) {
        if (!cancelled) {
          setLoadState({ kind: "error", message: error instanceof Error ? error.message : "Loading failed" });
        }
      }
    }

    void loadWorkspaceForDevelopmentUser();

    return () => {
      cancelled = true;
    };
  }, [selectedDevUserId]);

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
  useEffect(() => {
    if (appView === "repository" && session && !session.datasetCuratorCapability) {
      setAppView("inspection");
    }
    if (appView === "review-work" && session && !session.reviewerCapability) {
      setAppView("inspection");
    }
  }, [appView, session]);
  const termsAccepted = session?.workspaceDataUseAgreementStatus === "accepted";
  const selectedFrameStandard = frameStandards.find(
    (standard) => standard.frameStandardId === selectedFrameStandardId
  );
  const hiveConfigurationNotesRequired = selectedFrameStandard?.status === "other";
  const canCreateHive = Boolean(
    apiary &&
      selectedFrameStandardId &&
      (!hiveConfigurationNotesRequired || hiveConfigurationNotes.trim().length > 0)
  );
  const canCreateInspection = Boolean(hive && hiveConfiguration);
  const canUpload = Boolean(termsAccepted && inspection && file);
  const isTrainingDataCollection = inspection?.intent === "training_data_collection";
  const isVarroaAssessment = inspection?.intent === "varroa_assessment";
  const showTrainingCropPanel = Boolean(
    isTrainingDataCollection && session?.datasetCuratorCapability
  );
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

  async function refreshWorkspaceContext(
    workspaceId: string,
    preferredApiaryId?: string,
    preferredHiveId?: string,
    activeDevUserId = devUserId
  ) {
    const listing = await fetchApiaries({ devUserId: activeDevUserId, workspaceId });
    setApiaries(listing.apiaries);
    const nextApiary =
      listing.apiaries.find((candidate) => candidate.apiaryId === preferredApiaryId) ??
      listing.apiaries[0] ??
      null;
    setApiary(nextApiary);
    if (!nextApiary) {
      setHives([]);
      setHive(null);
      setHiveConfiguration(null);
      setTrainingInspections([]);
      clearInspectionWorkflow();
      return;
    }
    await refreshHivesForApiary(workspaceId, nextApiary, preferredHiveId, activeDevUserId);
  }

  async function refreshHivesForApiary(
    workspaceId: string,
    selectedApiary: Apiary,
    preferredHiveId?: string,
    activeDevUserId = devUserId
  ) {
    const listing = await fetchHives({
      devUserId: activeDevUserId,
      workspaceId,
      apiaryId: selectedApiary.apiaryId
    });
    setHives(listing.hives);
    const nextHive =
      listing.hives.find((candidate) => candidate.hiveId === preferredHiveId) ??
      listing.hives[0] ??
      null;
    setHive(nextHive);
    setTrainingInspections([]);
    clearInspectionWorkflow();
    if (!nextHive) {
      setHiveConfiguration(null);
      return;
    }
    await loadHiveConfigurationForSelection(workspaceId, nextHive, activeDevUserId);
    await refreshTrainingInspections(workspaceId, nextHive, undefined, activeDevUserId);
  }

  async function loadHiveConfigurationForSelection(
    workspaceId: string,
    selectedHive: Hive,
    activeDevUserId = devUserId
  ) {
    try {
      const configuration = await fetchHiveConfiguration({
        devUserId: activeDevUserId,
        workspaceId,
        hiveId: selectedHive.hiveId
      });
      setHiveConfiguration(configuration);
      setSelectedFrameStandardId(configuration.frameStandardId);
      setHiveConfigurationNotes(configuration.notes ?? "");
    } catch (error) {
      const apiError = toApiError(error);
      if (apiError.code === "hive_configuration_required") {
        setHiveConfiguration(null);
        return;
      }
      throw error;
    }
  }

  async function onSelectApiary(apiaryId: string) {
    if (!session) {
      return;
    }
    const selectedApiary = apiaries.find((candidate) => candidate.apiaryId === apiaryId);
    if (!selectedApiary) {
      return;
    }
    await runAction("Selecting apiary", async () => {
      setApiary(selectedApiary);
      await refreshHivesForApiary(session.workspaceId, selectedApiary);
    });
  }

  async function onSelectHive(hiveId: string) {
    if (!session) {
      return;
    }
    const selectedHive = hives.find((candidate) => candidate.hiveId === hiveId);
    if (!selectedHive) {
      return;
    }
    await runAction("Selecting hive", async () => {
      setHive(selectedHive);
      setTrainingInspections([]);
      clearInspectionWorkflow();
      await loadHiveConfigurationForSelection(session.workspaceId, selectedHive);
      await refreshTrainingInspections(session.workspaceId, selectedHive);
    });
  }

  async function refreshTrainingInspections(
    workspaceId: string,
    selectedHive: Hive,
    preferredInspectionId?: string,
    activeDevUserId = devUserId
  ) {
    const listing = await fetchHiveInspections({
      devUserId: activeDevUserId,
      workspaceId,
      hiveId: selectedHive.hiveId,
      intent: "training_data_collection"
    });
    setTrainingInspections(listing.inspections);
    const nextInspection =
      listing.inspections.find(
        (candidate) => candidate.inspectionId === preferredInspectionId
      ) ??
      listing.inspections[0] ??
      null;
    if (!nextInspection) {
      clearInspectionWorkflow();
      return;
    }
    await selectInspection(workspaceId, nextInspection, true, activeDevUserId);
  }

  async function selectInspection(
    workspaceId: string,
    selectedInspection: Inspection,
    scrollToCrops: boolean,
    activeDevUserId = devUserId
  ) {
    setInspection(selectedInspection);
    setFile(null);
    setAnalysisDetail(null);
    setReviewState(null);
    setLabellingState(null);
    clearEvidenceImage();
    clearLabellingImage();
    setActionState({ kind: "idle" });
    const listing = await fetchInspectionPhotos({
      devUserId: activeDevUserId,
      workspaceId,
      inspectionId: selectedInspection.inspectionId
    });
    setInspection(listing.inspection);
    setInspectionPhotos(listing.photos);
    if (scrollToCrops && listing.photos.length > 0 && selectedInspection.intent === "training_data_collection") {
      window.setTimeout(() => {
        trainingCropPanelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 0);
    }
  }

  async function onSelectTrainingInspection(inspectionId: string) {
    if (!session) {
      return;
    }
    const selectedInspection = trainingInspections.find(
      (candidate) => candidate.inspectionId === inspectionId
    );
    if (!selectedInspection) {
      return;
    }
    await runAction("Resuming Training Inspection", async () => {
      await selectInspection(session.workspaceId, selectedInspection, true);
    });
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
      await refreshWorkspaceContext(session.workspaceId, created.apiaryId);
    });
  }

  async function onCreateHive(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!apiary) {
      return;
    }
    await runAction("Creating hive", async () => {
      const created = await createHive({ devUserId, apiaryId: apiary.apiaryId, name: hiveName });
      const configuration = await upsertHiveConfiguration({
        devUserId,
        workspaceId: created.workspaceId,
        hiveId: created.hiveId,
        frameStandardId: selectedFrameStandardId,
        notes: hiveConfigurationNotes
      });
      setHive(created);
      setHiveConfiguration(configuration);
      await refreshHivesForApiary(created.workspaceId, apiary, created.hiveId);
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
      if (hive && created.intent === "training_data_collection") {
        setInspection(created);
        setInspectionPhotos([]);
        setAnalysisDetail(null);
        clearEvidenceImage();
        clearLabellingImage();
        setTrainingInspections((current) =>
          sortInspectionsNewestFirst([
            created,
            ...current.filter(
              (candidate) => candidate.inspectionId !== created.inspectionId
            )
          ])
        );
      } else {
        setInspection(created);
        setInspectionPhotos([]);
        setAnalysisDetail(null);
        clearEvidenceImage();
        clearLabellingImage();
      }
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

  function clearInspectionWorkflow() {
    setInspection(null);
    setInspectionPhotos([]);
    setAnalysisDetail(null);
    setFile(null);
    setReviewState(null);
    setLabellingState(null);
    clearEvidenceImage();
    clearLabellingImage();
  }

  function clearUserScopedState() {
    setAppView("inspection");
    setActionState({ kind: "idle" });
    setApiaries([]);
    setApiary(null);
    setHives([]);
    setHive(null);
    setHiveConfiguration(null);
    setTrainingInspections([]);
    setInspection(null);
    setInspectionPhotos([]);
    setAnalysisDetail(null);
    setFile(null);
    setReviewState(null);
    setLabellingState(null);
    clearEvidenceImage();
    clearLabellingImage();
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

  function onSelectDevelopmentUser(nextDevUserId: string) {
    window.localStorage.setItem(devUserStorageKey, nextDevUserId);
    setSelectedDevUserId(nextDevUserId);
  }

  return (
    <main className="app-shell">
      <header className="topbar" aria-label="Workspace status">
        <div>
          <p className="eyebrow">HiveSight</p>
          <h1>
            {appView === "repository"
              ? "Bee Annotation Repository"
              : appView === "review-work"
                ? "Review Work"
                : "Inspection photo intake"}
          </h1>
        </div>
        <StatusPill loadState={loadState} />
      </header>

      {loadState.kind === "ready" ? (
        <section className="intake-layout" aria-label="Inspection photo intake workflow">
          <aside className="workspace-panel">
            <PanelHeading icon={<ShieldCheck size={20} />} title="Development session" />
            {devUserSwitchingAvailable ? (
              <DevelopmentUserSelector
                devUsers={devUsers}
                selectedDevUserId={devUserId}
                disabled={actionState.kind === "working"}
                onSelectDevelopmentUser={onSelectDevelopmentUser}
              />
            ) : null}
            <nav className="view-switcher" aria-label="HiveSight local pages">
              <button
                type="button"
                className={appView === "inspection" ? "selected" : ""}
                onClick={() => setAppView("inspection")}
                data-testid="inspection-page-button"
              >
                <FileImage size={18} />
                Inspection
              </button>
              {loadState.session.datasetCuratorCapability ? (
                <button
                  type="button"
                  className={appView === "repository" ? "selected" : ""}
                  onClick={() => setAppView("repository")}
                  data-testid="bee-annotation-repository-page-button"
                >
                  <BookOpen size={18} />
                  Repository
                </button>
              ) : null}
              {loadState.session.reviewerCapability ? (
                <button
                  type="button"
                  className={appView === "review-work" ? "selected" : ""}
                  onClick={() => setAppView("review-work")}
                  data-testid="review-work-page-button"
                >
                  <ShieldCheck size={18} />
                  Review Work
                </button>
              ) : null}
            </nav>
            <dl className="facts">
              {devUserSwitchingAvailable ? (
                <div>
                  <dt>Dev User</dt>
                  <dd data-testid="development-user-code">
                    {devUsers.find((devUser) => devUser.userId === devUserId)?.devUserCode ??
                      "unknown"}
                  </dd>
                </div>
              ) : null}
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
              <div>
                <dt>Capabilities</dt>
                <dd data-testid="development-user-capabilities">
                  {formatCapabilities(loadState.session)}
                </dd>
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
            {appView === "review-work" ? (
              <ReviewWorkPage
                devUserId={devUserId}
                workspaceId={loadState.session.workspaceId}
                onError={(error) =>
                  setActionState({
                    kind: "blocked",
                    code: error.code,
                    message: error.message
                  })
                }
              />
            ) : appView === "repository" ? (
              <BeeAnnotationRepositoryPage
                devUserId={devUserId}
                workspaceId={loadState.session.workspaceId}
                datasetCuratorCapability={loadState.session.datasetCuratorCapability}
                onError={(error) =>
                  setActionState({
                    kind: "blocked",
                    code: error.code,
                    message: error.message
                  })
                }
              />
            ) : (
              <>
            <div className="form-grid">
              <form className="stacked-form" onSubmit={onCreateApiary}>
                <PanelHeading icon={<Plus size={20} />} title="Apiary" />
                {apiaries.length > 0 ? (
                  <label>
                    <span>Selected Apiary</span>
                    <select
                      value={apiary?.apiaryId ?? ""}
                      onChange={(event) => void onSelectApiary(event.target.value)}
                      disabled={actionState.kind === "working"}
                      data-testid="apiary-select"
                    >
                      {apiaries.map((candidate) => (
                        <option key={candidate.apiaryId} value={candidate.apiaryId}>
                          {candidate.name}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : (
                  <p className="setup-copy" data-testid="apiary-empty-state">
                    Add an Apiary to start organising Hives in this Workspace.
                  </p>
                )}
                <label>
                  <span>{apiaries.length > 0 ? "New Apiary name" : "Name"}</span>
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
                  {apiaries.length > 0 ? "Add apiary" : "Create apiary"}
                </button>
                <RecordBadge value={apiary?.apiaryId} />
              </form>

              <form className="stacked-form" onSubmit={onCreateHive}>
                <PanelHeading icon={<Plus size={20} />} title="Hive Configuration" />
                {!apiary ? (
                  <p className="setup-copy" data-testid="hive-empty-state">
                    Select or add an Apiary before adding a Hive.
                  </p>
                ) : hives.length > 0 ? (
                  <label>
                    <span>Selected Hive</span>
                    <select
                      value={hive?.hiveId ?? ""}
                      onChange={(event) => void onSelectHive(event.target.value)}
                      disabled={actionState.kind === "working"}
                      data-testid="hive-select"
                    >
                      {hives.map((candidate) => (
                        <option key={candidate.hiveId} value={candidate.hiveId}>
                          {candidate.name}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : (
                  <p className="setup-copy" data-testid="hive-empty-state">
                    Add a Hive and its frame context before creating Inspections.
                  </p>
                )}
                <label>
                  <span>{hives.length > 0 ? "New Hive name" : "Name"}</span>
                <input
                  value={hiveName}
                  onChange={(event) => setHiveName(event.target.value)}
                  required
                  data-testid="hive-name-input"
                />
                </label>
                <label>
                  <span>Frame Standard</span>
                  <select
                    value={selectedFrameStandardId}
                    onChange={(event) => setSelectedFrameStandardId(event.target.value)}
                    required
                    data-testid="hive-configuration-frame-standard-select"
                  >
                    {frameStandards.map((standard) => (
                      <option key={standard.frameStandardId} value={standard.frameStandardId}>
                        {standard.displayName}
                      </option>
                    ))}
                  </select>
                </label>
                {selectedFrameStandard ? (
                  <dl
                    className="compact-facts"
                    data-testid="hive-configuration-dimensions"
                  >
                    <div>
                      <dt>Top bar</dt>
                      <dd>{formatFrameStandardDimension(selectedFrameStandard.topBarLengthMm)}</dd>
                    </div>
                    <div>
                      <dt>Bottom bar</dt>
                      <dd>{formatFrameStandardDimension(selectedFrameStandard.bottomBarLengthMm)}</dd>
                    </div>
                    <div>
                      <dt>Side bar</dt>
                      <dd>{formatFrameStandardDimension(selectedFrameStandard.sideBarHeightMm)}</dd>
                    </div>
                  </dl>
                ) : null}
                <label>
                  <span>{hiveConfigurationNotesRequired ? "Notes required" : "Notes"}</span>
                  <textarea
                    value={hiveConfigurationNotes}
                    onChange={(event) => setHiveConfigurationNotes(event.target.value)}
                    required={hiveConfigurationNotesRequired}
                    rows={3}
                    data-testid="hive-configuration-notes-input"
                  />
                </label>
                <button
                  type="submit"
                  disabled={!canCreateHive || actionState.kind === "working"}
                  data-testid="create-hive-button"
                >
                  {hives.length > 0 ? "Add hive" : "Create hive"}
                </button>
                <RecordBadge value={hive?.hiveId} />
                {hiveConfiguration ? (
                  <p className="intent-badge" data-testid="hive-configuration-state">
                    {hiveConfiguration.frameStandard.displayName}
                  </p>
                ) : hive ? (
                  <p className="setup-copy" data-testid="hive-configuration-state">
                    Hive Configuration is needed before this Hive can be used for Inspections.
                  </p>
                ) : null}
              </form>

              <form className="stacked-form" onSubmit={onCreateInspection}>
                <PanelHeading icon={<Plus size={20} />} title="Inspection" />
                {hive && trainingInspections.length > 0 ? (
                  <label>
                    <span>Resume Training Inspection</span>
                    <select
                      value={inspection?.inspectionId ?? ""}
                      onChange={(event) => void onSelectTrainingInspection(event.target.value)}
                      disabled={actionState.kind === "working"}
                      data-testid="resume-training-inspection-select"
                    >
                      {trainingInspections.map((candidate) => (
                        <option key={candidate.inspectionId} value={candidate.inspectionId}>
                          {formatInspectionOption(candidate)}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : hive ? (
                  <p className="setup-copy" data-testid="resume-training-inspection-empty-state">
                    No Training Data Collection Inspections to resume for this Hive.
                  </p>
                ) : null}
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
              </>
            ) : null}
            {showTrainingCropPanel ? (
              <div ref={trainingCropPanelRef}>
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
              </div>
            ) : null}
              </>
            )}
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

function DevelopmentUserSelector({
  devUsers,
  selectedDevUserId,
  disabled,
  onSelectDevelopmentUser
}: {
  devUsers: DevUser[];
  selectedDevUserId: string;
  disabled: boolean;
  onSelectDevelopmentUser: (devUserId: string) => void;
}) {
  return (
    <label className="development-user-select">
      <span>Acting as</span>
      <select
        value={selectedDevUserId}
        onChange={(event) => onSelectDevelopmentUser(event.target.value)}
        disabled={disabled}
        data-testid="development-user-select"
      >
        {devUsers.map((devUser) => (
          <option key={devUser.userId} value={devUser.userId}>
            {devUser.devUserCode} / {devUser.displayName}
          </option>
        ))}
      </select>
    </label>
  );
}

function PanelHeading({ icon, title }: { icon: ReactNode; title: string }) {
  return (
    <div className="panel-heading">
      <span aria-hidden="true">{icon}</span>
      <h2>{title}</h2>
    </div>
  );
}

function formatCapabilities(session: DevSession) {
  const capabilities = [
    session.datasetCuratorCapability ? "Dataset Curator" : null,
    session.reviewerCapability ? "Reviewer" : null
  ].filter((capability): capability is string => capability !== null);
  return capabilities.length > 0 ? capabilities.join(" / ") : "None";
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

function formatInspectionOption(inspection: Inspection) {
  return `${inspection.inspectionDate} / ${formatInspectionIntent(inspection.intent)} / ${inspection.inspectionId.slice(0, 8)}`;
}

function sortInspectionsNewestFirst(inspections: Inspection[]) {
  return [...inspections].sort((left, right) => {
    const dateComparison = right.inspectionDate.localeCompare(left.inspectionDate);
    return dateComparison === 0
      ? right.inspectionId.localeCompare(left.inspectionId)
      : dateComparison;
  });
}

function BeeAnnotationRepositoryPage({
  devUserId,
  workspaceId,
  datasetCuratorCapability,
  onError
}: {
  devUserId: string;
  workspaceId: string;
  datasetCuratorCapability: boolean;
  onError: (error: ApiError) => void;
}) {
  const [listing, setListing] = useState<{
    summary: DatasetRepositorySummary;
    items: DatasetRepositoryItem[];
  } | null>(null);
  const [selectedDatasetItemId, setSelectedDatasetItemId] = useState<string | null>(null);
  const [detail, setDetail] = useState<DatasetRepositoryItemDetail | null>(null);
  const [roleFilter, setRoleFilter] = useState<DatasetRole | "all">("all");
  const [membershipFilter, setMembershipFilter] = useState<"all" | "latest" | "new">("all");
  const [beeClassFilter, setBeeClassFilter] = useState<"all" | "complete" | "partial">("all");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);

  async function refreshRepository() {
    if (!datasetCuratorCapability) {
      return;
    }
    setLoading(true);
    try {
      const nextListing = await fetchDatasetRepositoryItems({ devUserId, workspaceId });
      setListing(nextListing);
      setSelectedDatasetItemId((current) => current ?? nextListing.items[0]?.datasetItemId ?? null);
    } catch (error) {
      onError(toApiError(error));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refreshRepository();
  }, [workspaceId, datasetCuratorCapability]);

  useEffect(() => {
    if (!selectedDatasetItemId) {
      setDetail(null);
      return;
    }
    setDetailLoading(true);
    fetchDatasetRepositoryItemDetail({ devUserId, workspaceId, datasetItemId: selectedDatasetItemId })
      .then(setDetail)
      .catch((error) => onError(toApiError(error)))
      .finally(() => setDetailLoading(false));
  }, [devUserId, workspaceId, selectedDatasetItemId]);

  const filteredItems = useMemo(() => {
    const searchTerm = search.trim().toLowerCase();
    return (listing?.items ?? []).filter((item) => {
      if (roleFilter !== "all" && item.datasetRole !== roleFilter) return false;
      if (membershipFilter === "latest" && item.isNewSinceLatestDatasetVersion) return false;
      if (membershipFilter === "new" && !item.isNewSinceLatestDatasetVersion) return false;
      if (beeClassFilter === "complete" && item.completeVisibleBeeCount === 0) return false;
      if (beeClassFilter === "partial" && item.partialVisibleBeeCount === 0) return false;
      if (!searchTerm) return true;
      return [
        item.humanReadableId,
        item.sourceFilename,
        item.hiveName,
        item.apiaryName,
        item.assignmentNote,
        item.sourceGroupKey
      ]
        .filter(Boolean)
        .some((value) => value!.toLowerCase().includes(searchTerm));
    });
  }, [beeClassFilter, listing, membershipFilter, roleFilter, search]);

  useEffect(() => {
    if (filteredItems.length === 0) {
      setSelectedDatasetItemId(null);
      return;
    }
    if (
      !filteredItems.some((item) => item.datasetItemId === selectedDatasetItemId)
    ) {
      setSelectedDatasetItemId(filteredItems[0].datasetItemId);
    }
  }, [filteredItems, selectedDatasetItemId]);

  if (!datasetCuratorCapability) {
    return (
      <section className="repository-page" data-testid="bee-annotation-repository-page">
        <PanelHeading icon={<BookOpen size={20} />} title="Bee Annotation Repository" />
        <p className="setup-copy">Dataset Curator capability is required.</p>
      </section>
    );
  }

  const summary = listing?.summary ?? null;

  return (
    <section className="repository-page" data-testid="bee-annotation-repository-page">
      <div className="repository-header">
        <div>
          <PanelHeading icon={<BookOpen size={20} />} title="Bee Annotation Repository" />
          <p className="setup-copy">
            Dataset items for training, validation, benchmark, and excluded evidence.
          </p>
        </div>
        <button type="button" onClick={() => void refreshRepository()} disabled={loading}>
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      {summary ? (
        <>
          <div className="repository-summary" data-testid="repository-summary">
            <Metric label="Training" value={summary.roleCounts.training ?? 0} />
            <Metric label="Validation" value={summary.roleCounts.validation ?? 0} />
            <Metric label="Benchmark" value={summary.roleCounts.benchmark ?? 0} />
            <Metric label="Excluded" value={summary.roleCounts.excluded ?? 0} />
            <Metric label="New items" value={summary.newSinceLatestDatasetVersionCount} />
            <Metric label="Unassigned crops" value={summary.unassignedCompletedCropCount} />
          </div>
          <div className="repository-chip-row" data-testid="repository-diversity-chips">
            <span>{Object.keys(summary.inspectionDistribution).length} inspections</span>
            <span>{Object.keys(summary.hiveDistribution).length} hives</span>
            <span>{Object.keys(summary.sourceImageDistribution).length} source images</span>
            <span>
              {summary.persistenceBackend} / {summary.databasePurpose}
            </span>
            {summary.latestDatasetVersion ? (
              <span>Latest {summary.latestDatasetVersion.humanReadableId}</span>
            ) : (
              <span>No Dataset Version</span>
            )}
          </div>
          {summary.warnings.length > 0 ? (
            <div className="repository-warnings" data-testid="repository-warnings">
              {summary.warnings.map((warning) => (
                <p key={warning.code}>
                  <CircleAlert size={16} />
                  {warning.message}
                </p>
              ))}
            </div>
          ) : null}
        </>
      ) : null}

      <div className="repository-filters">
        <label>
          <span>Dataset Role</span>
          <select
            value={roleFilter}
            onChange={(event) => setRoleFilter(event.target.value as DatasetRole | "all")}
            data-testid="repository-role-filter"
          >
            <option value="all">All roles</option>
            <option value="training">Training</option>
            <option value="validation">Validation</option>
            <option value="benchmark">Benchmark</option>
            <option value="excluded">Excluded</option>
          </select>
        </label>
        <label>
          <span>Dataset Version</span>
          <select
            value={membershipFilter}
            onChange={(event) => setMembershipFilter(event.target.value as "all" | "latest" | "new")}
            data-testid="repository-membership-filter"
          >
            <option value="all">All membership states</option>
            <option value="latest">In latest Dataset Version</option>
            <option value="new">New since latest version</option>
          </select>
        </label>
        <label>
          <span>Bee class</span>
          <select
            value={beeClassFilter}
            onChange={(event) => setBeeClassFilter(event.target.value as "all" | "complete" | "partial")}
            data-testid="repository-bee-class-filter"
          >
            <option value="all">All bee evidence</option>
            <option value="complete">Has complete bees</option>
            <option value="partial">Has partial bees</option>
          </select>
        </label>
        <label>
          <span>Search</span>
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="ID, filename, hive, source group, note"
            data-testid="repository-search-input"
          />
        </label>
      </div>

      {loading ? <p className="setup-copy">Loading repository</p> : null}
      {summary && summary.datasetItemCount === 0 ? (
        <p className="setup-copy" data-testid="repository-empty-state">
          {summary.unassignedCompletedCropCount > 0
            ? "Completed Training Crops exist but none have been assigned to a Dataset Role."
            : "Create and annotate Training Crops before reviewing the repository."}
        </p>
      ) : null}

      <div className="repository-browser">
        <div className="repository-list" data-testid="repository-item-list">
          {filteredItems.map((item) => (
            <button
              key={item.datasetItemId}
              type="button"
              className={item.datasetItemId === selectedDatasetItemId ? "selected" : ""}
              onClick={() => setSelectedDatasetItemId(item.datasetItemId)}
              data-testid="repository-item-card"
            >
              <RepositoryThumbnail item={item} />
              <span>
                <strong>{item.humanReadableId}</strong>
                <span>
                  {formatDatasetRoleLabel(item.datasetRole)} / {item.completeVisibleBeeCount} complete /{" "}
                  {item.partialVisibleBeeCount} partial
                </span>
                <span>{item.sourceFilename ?? item.inspectionPhotoId.slice(0, 8)}</span>
                <span>
                  {item.latestDatasetVersionMembership
                    ? `${item.latestDatasetVersionMembership.humanReadableId}: ${formatMembership(item.latestDatasetVersionMembership.membership)}`
                    : "Not versioned"}
                </span>
              </span>
            </button>
          ))}
        </div>

        <div className="repository-detail" data-testid="repository-item-detail">
          {detailLoading ? <p className="setup-copy">Loading item detail</p> : null}
          {detail ? (
            <>
              <div className="repository-detail-header">
                <div>
                  <h2>{detail.humanReadableId}</h2>
                  <p>
                    {formatDatasetRoleLabel(detail.datasetRole)} / {detail.exportEligibility}
                  </p>
                </div>
                {detail.benchmarkProtected ? (
                  <span className="intent-badge">Protected benchmark</span>
                ) : null}
              </div>
              <RepositoryCropPreview detail={detail} />
              <div className="repository-summary">
                <Metric label="Complete bees" value={detail.completeVisibleBeeCount} />
                <Metric label="Partial bees" value={detail.partialVisibleBeeCount} />
                <Metric label="Image" value={detail.previewStatus} />
                <Metric
                  label="Latest"
                  value={
                    detail.latestDatasetVersionMembership
                      ? formatMembership(detail.latestDatasetVersionMembership.membership)
                      : "not versioned"
                  }
                />
              </div>
              <dl className="compact-facts" data-testid="repository-item-provenance">
                <div>
                  <dt>Source</dt>
                  <dd>{detail.sourceFilename ?? detail.sourceImageId.slice(0, 8)}</dd>
                </div>
                <div>
                  <dt>Inspection</dt>
                  <dd>
                    {detail.inspectionDate ?? "n/a"} /{" "}
                    {detail.inspectionIntent ? formatInspectionIntent(detail.inspectionIntent) : "n/a"}
                  </dd>
                </div>
                <div>
                  <dt>Hive</dt>
                  <dd>{detail.hiveName ?? "n/a"}</dd>
                </div>
                <div>
                  <dt>Hive configuration</dt>
                  <dd>{detail.hiveConfigurationSummary ?? "n/a"}</dd>
                </div>
                <div>
                  <dt>Source group</dt>
                  <dd>{detail.sourceGroupKey ?? "n/a"}</dd>
                </div>
                <div>
                  <dt>Assigned</dt>
                  <dd>{formatDateTime(detail.assignedAt)}</dd>
                </div>
              </dl>
              <div className="repository-chip-row" data-testid="repository-provenance-chips">
                {Object.entries(detail.annotationSourceCounts).map(([source, count]) => (
                  <span key={source}>{source}: {count}</span>
                ))}
                {Object.entries(detail.reviewMethodCounts).map(([method, count]) => (
                  <span key={method}>{method}: {count}</span>
                ))}
              </div>
              <div className="repository-version-list" data-testid="repository-version-memberships">
                {detail.datasetVersionMemberships.length === 0 ? (
                  <p className="setup-copy">No Dataset Versions contain this item yet.</p>
                ) : (
                  detail.datasetVersionMemberships.map((membership) => (
                    <span key={membership.datasetVersionId}>
                      {membership.humanReadableId}: {formatMembership(membership.membership)}
                    </span>
                  ))
                )}
              </div>
            </>
          ) : (
            <p className="setup-copy">Select a Dataset Item to inspect its evidence.</p>
          )}
        </div>
      </div>
    </section>
  );
}

function RepositoryThumbnail({ item }: { item: DatasetRepositoryItem }) {
  if (!item.thumbnailUrl || item.previewStatus !== "available") {
    return (
      <span className="repository-thumbnail unavailable">
        <Image size={18} />
      </span>
    );
  }
  return (
    <span className="repository-thumbnail">
      <img src={toCoreApiContentUrl(item.thumbnailUrl)} alt="" />
    </span>
  );
}

function RepositoryCropPreview({ detail }: { detail: DatasetRepositoryItemDetail }) {
  const basis = detail.reviewedEllipseSnapshots[0];
  if (!detail.previewUrl || detail.previewStatus !== "available" || !basis) {
    return (
      <div className="repository-crop-preview unavailable" data-testid="repository-crop-preview">
        <Image size={24} />
        <span>Image unavailable</span>
      </div>
    );
  }
  return (
    <div
      className="repository-crop-preview"
      style={{
        aspectRatio: `${detail.cropWidth ?? detail.cropImageWidthPx ?? 1} / ${
          detail.cropHeight ?? detail.cropImageHeightPx ?? 1
        }`
      }}
      data-testid="repository-crop-preview"
    >
      <img
        src={toCoreApiContentUrl(detail.previewUrl)}
        alt=""
        style={repositoryCropImageStyle(detail, basis)}
      />
      {detail.reviewedEllipseSnapshots.map((ellipse) => (
        <span
          key={ellipse.annotationId}
          className={`repository-ellipse ${ellipse.annotationType}`}
          style={repositoryEllipseStyle(detail, ellipse)}
          data-testid="repository-crop-ellipse"
        >
          <span className="ellipse-head-arrow" data-testid="repository-crop-ellipse-head-arrow" />
        </span>
      ))}
    </div>
  );
}

function repositoryCropImageStyle(
  detail: DatasetRepositoryItemDetail,
  basis: OrientedBeeEllipse | DatasetRepositoryItemDetail["reviewedEllipseSnapshots"][number]
) {
  const cropWidth = detail.cropWidth ?? detail.cropImageWidthPx ?? basis.sourceImageWidthPx;
  const cropHeight = detail.cropHeight ?? detail.cropImageHeightPx ?? basis.sourceImageHeightPx;
  const cropX = detail.cropX ?? 0;
  const cropY = detail.cropY ?? 0;
  return {
    height: `${(basis.sourceImageHeightPx / cropHeight) * 100}%`,
    left: `${-(cropX / cropWidth) * 100}%`,
    position: "absolute" as const,
    top: `${-(cropY / cropHeight) * 100}%`,
    width: `${(basis.sourceImageWidthPx / cropWidth) * 100}%`
  };
}

function repositoryEllipseStyle(
  detail: DatasetRepositoryItemDetail,
  ellipse: DatasetRepositoryItemDetail["reviewedEllipseSnapshots"][number]
) {
  const cropWidth = detail.cropWidth ?? detail.cropImageWidthPx ?? ellipse.sourceImageWidthPx;
  const cropHeight = detail.cropHeight ?? detail.cropImageHeightPx ?? ellipse.sourceImageHeightPx;
  const cropX = detail.cropX ?? 0;
  const cropY = detail.cropY ?? 0;
  return {
    height: `${(ellipse.radiusY * 2 / cropHeight) * 100}%`,
    left: `${((ellipse.centerX - cropX - ellipse.radiusX) / cropWidth) * 100}%`,
    top: `${((ellipse.centerY - cropY - ellipse.radiusY) / cropHeight) * 100}%`,
    transform: `rotate(${ellipse.rotationDegrees}deg)`,
    width: `${(ellipse.radiusX * 2 / cropWidth) * 100}%`
  };
}

function formatMembership(membership: DatasetVersionMembership["membership"]) {
  if (membership === "protected_benchmark") return "protected benchmark";
  if (membership === "not_in_version") return "not in version";
  return membership.replaceAll("_", " ");
}

function formatMetric(value: unknown) {
  return typeof value === "number" ? value.toFixed(2) : "n/a";
}

function formatDatasetRoleLabel(role: DatasetRole | null) {
  if (role === "training") return "Training";
  if (role === "validation") return "Validation";
  if (role === "benchmark") return "Benchmark";
  if (role === "excluded") return "Excluded";
  return "Unassigned";
}

function formatDateTime(value: string | null) {
  return value ? new Date(value).toLocaleString() : "n/a";
}

function formatElapsedTime(startedAt: string | null, completedAt: string | null, tick: number) {
  if (!startedAt) {
    return "n/a";
  }
  void tick;
  const start = new Date(startedAt).getTime();
  const end = completedAt ? new Date(completedAt).getTime() : Date.now();
  const totalSeconds = Math.max(0, Math.floor((end - start) / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}m ${seconds.toString().padStart(2, "0")}s`;
}

function isActiveTrainingRun(run: TrainingRun) {
  return run.status === "queued" || run.status === "running" || run.status === "cancelling";
}

function isActiveBenchmarkEvaluation(evaluation: BenchmarkEvaluation) {
  return (
    evaluation.status === "queued" ||
    evaluation.status === "running" ||
    evaluation.status === "cancelling"
  );
}

function trainingRunCanBeDeleted(run: TrainingRun) {
  return (
    run.modelCandidateId === null &&
    run.artifactIds.length === 0 &&
    ["queued", "running", "cancelling", "cancelled", "abandoned"].includes(run.status)
  );
}

function trainingRunCanBeAbandoned(run: TrainingRun) {
  return isActiveTrainingRun(run) && (run.isStale || run.status === "cancelling");
}

function formatProgressPercent(value: number | null) {
  return value === null ? "n/a" : `${Math.round(value)}%`;
}

function formatFrameStandardDimension(value: number | null): string {
  return value === null ? "Unknown" : `${value} mm`;
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

function proposalStyle(crop: TrainingCrop, proposal: BeeAnnotationProposal) {
  return {
    left: `${((proposal.centerX - crop.cropX - proposal.radiusX) / crop.cropWidth) * 100}%`,
    top: `${((proposal.centerY - crop.cropY - proposal.radiusY) / crop.cropHeight) * 100}%`,
    width: `${((proposal.radiusX * 2) / crop.cropWidth) * 100}%`,
    height: `${((proposal.radiusY * 2) / crop.cropHeight) * 100}%`,
    transform: `rotate(${proposal.rotationDegrees}deg)`
  };
}

function reviewQueueImageStyle(item: ReviewQueueItem) {
  const snapshot = item.evidenceSnapshot;
  return {
    left: `${(-snapshot.cropX / snapshot.cropWidth) * 100}%`,
    top: `${(-snapshot.cropY / snapshot.cropHeight) * 100}%`,
    width: `${(snapshot.sourceImageWidthPx / snapshot.cropWidth) * 100}%`,
    height: `${(snapshot.sourceImageHeightPx / snapshot.cropHeight) * 100}%`
  };
}

function reviewQueueEllipseStyle(
  item: ReviewQueueItem,
  ellipse: ReviewQueueItem["evidenceSnapshot"]["reviewedEllipses"][number]
) {
  const snapshot = item.evidenceSnapshot;
  return {
    left: `${((ellipse.centerX - snapshot.cropX - ellipse.radiusX) / snapshot.cropWidth) * 100}%`,
    top: `${((ellipse.centerY - snapshot.cropY - ellipse.radiusY) / snapshot.cropHeight) * 100}%`,
    width: `${((ellipse.radiusX * 2) / snapshot.cropWidth) * 100}%`,
    height: `${((ellipse.radiusY * 2) / snapshot.cropHeight) * 100}%`,
    transform: `rotate(${ellipse.rotationDegrees}deg)`
  };
}

type EllipseGeometry = {
  annotationType: BeeAnnotationType;
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
    annotationType: values.annotationType ?? ellipse.annotationType,
    centerX: values.centerX ?? ellipse.centerX,
    centerY: values.centerY ?? ellipse.centerY,
    radiusX: values.radiusX ?? ellipse.radiusX,
    radiusY: values.radiusY ?? ellipse.radiusY,
    rotationDegrees: values.rotationDegrees ?? ellipse.rotationDegrees
  };
}

function ellipseIsAllowedForCrop(crop: TrainingCrop, ellipse: EllipseGeometry): boolean {
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
  const ellipseBounds = {
    left: ellipse.centerX - xExtent,
    top: ellipse.centerY - yExtent,
    right: ellipse.centerX + xExtent,
    bottom: ellipse.centerY + yExtent
  };
  const cropBounds = {
    left: crop.cropX,
    top: crop.cropY,
    right: crop.cropX + crop.cropWidth,
    bottom: crop.cropY + crop.cropHeight
  };
  if (ellipse.annotationType === "partial_visible_bee") {
    return boundsOverlap(ellipseBounds, cropBounds);
  }
  return boundsInside(ellipseBounds, cropBounds);
}

function canAdjustEllipse(
  crop: TrainingCrop | null,
  ellipse: OrientedBeeEllipse | null,
  values: Partial<EllipseGeometry>
): boolean {
  if (!crop || !ellipse) {
    return false;
  }
  return ellipseIsAllowedForCrop(crop, nextEllipseGeometry(ellipse, values));
}

function boundsInside(
  inner: { left: number; top: number; right: number; bottom: number },
  outer: { left: number; top: number; right: number; bottom: number }
): boolean {
  return (
    inner.left >= outer.left &&
    inner.top >= outer.top &&
    inner.right <= outer.right &&
    inner.bottom <= outer.bottom
  );
}

function boundsOverlap(
  left: { left: number; top: number; right: number; bottom: number },
  right: { left: number; top: number; right: number; bottom: number }
): boolean {
  return (
    left.right > right.left &&
    left.left < right.right &&
    left.bottom > right.top &&
    left.top < right.bottom
  );
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
  const cropViewportRef = useRef<HTMLDivElement | null>(null);
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
  const [datasetRole, setDatasetRole] = useState<DatasetRole>("training");
  const [datasetSourceGroupKey, setDatasetSourceGroupKey] = useState("");
  const [datasetAssignmentNote, setDatasetAssignmentNote] = useState(
    "Assigned from completed Training Crop review."
  );
  const [datasetExclusionReason, setDatasetExclusionReason] =
    useState<DatasetExclusionReason>("unsuitable_crop");
  const [trainingCropDatasetItem, setTrainingCropDatasetItem] = useState<DatasetItem | null>(null);
  const [requestedReviews, setRequestedReviews] = useState<ReviewQueueItem[]>([]);
  const [reviewRequestNotes, setReviewRequestNotes] = useState("");
  const [cancellationNotes, setCancellationNotes] = useState("");
  const [yoloObbExport, setYoloObbExport] = useState<YoloObbExport | null>(null);
  const [physicalYoloObbExport, setPhysicalYoloObbExport] =
    useState<PhysicalYoloObbExport | null>(null);
  const [modelTrainingReadiness, setModelTrainingReadiness] =
    useState<ModelTrainingReadiness | null>(null);
  const [datasetVersion, setDatasetVersion] = useState<DatasetVersion | null>(null);
  const [trainingRun, setTrainingRun] = useState<TrainingRun | null>(null);
  const [trainingRuns, setTrainingRuns] = useState<TrainingRun[]>([]);
  const [trainingRunsLastCheckedAt, setTrainingRunsLastCheckedAt] = useState<string | null>(null);
  const [trainingRunPollError, setTrainingRunPollError] = useState<string | null>(null);
  const [trainingRunClockTick, setTrainingRunClockTick] = useState(0);
  const [modelCandidates, setModelCandidates] = useState<ModelCandidate[]>([]);
  const [selectedModelCandidateId, setSelectedModelCandidateId] = useState<string | null>(null);
  const [benchmarkReadiness, setBenchmarkReadiness] =
    useState<BenchmarkEvaluationReadiness | null>(null);
  const [benchmarkEvaluation, setBenchmarkEvaluation] = useState<BenchmarkEvaluation | null>(null);
  const [benchmarkEvaluations, setBenchmarkEvaluations] = useState<BenchmarkEvaluation[]>([]);
  const [benchmarkEvaluationsLastCheckedAt, setBenchmarkEvaluationsLastCheckedAt] = useState<
    string | null
  >(null);
  const [benchmarkEvaluationPollError, setBenchmarkEvaluationPollError] = useState<string | null>(
    null
  );
  const [candidateThreshold, setCandidateThreshold] = useState(0.1);
  const [candidateProposals, setCandidateProposals] = useState<BeeAnnotationProposal[]>([]);
  const [selectedProposalId, setSelectedProposalId] = useState<string | null>(null);
  const [editedProposalIds, setEditedProposalIds] = useState<Set<string>>(() => new Set());
  const [candidateProposalMessage, setCandidateProposalMessage] = useState<string | null>(null);
  const [modelCandidateSelectionMessage, setModelCandidateSelectionMessage] = useState<string | null>(
    null
  );
  const [acknowledgeModelWarnings, setAcknowledgeModelWarnings] = useState(false);
  const [workingLabel, setWorkingLabel] = useState<string | null>(null);
  const [cropZoom, setCropZoom] = useState(1);
  const hasActiveTrainingRun = trainingRuns.some(isActiveTrainingRun);
  const hasActiveBenchmarkEvaluation = benchmarkEvaluations.some(isActiveBenchmarkEvaluation);
  const shouldPollTrainingRuns =
    hasActiveTrainingRun || workingLabel === "Starting Bee Detector training";
  const shouldPollBenchmarkEvaluations =
    hasActiveBenchmarkEvaluation || workingLabel === "Starting Benchmark Evaluation";
  const canStartModelTraining =
    Boolean(datasetVersion) &&
    (modelTrainingReadiness?.eligibleToStartTraining ?? true) &&
    !Boolean(workingLabel);
  const canStartBenchmarkEvaluation =
    Boolean(selectedModelCandidateId) &&
    (benchmarkReadiness?.eligibleToStartEvaluation ?? true) &&
    !Boolean(workingLabel);

  const selectedPhoto = photos.find((photo) => photo.inspectionPhotoId === selectedPhotoId) ?? null;
  const selectedCrop = evidence?.trainingCrop ?? crops.find((crop) => crop.trainingCropId === selectedCropId) ?? null;
  const selectedCropReviewItems = requestedReviews.filter(
    (item) => item.subjectId === selectedCrop?.trainingCropId
  );
  const selectedCropActiveReviewItem =
    selectedCropReviewItems.find((item) => item.status === "available") ?? null;
  const selectedCropDatasetRole = trainingCropDatasetItem?.datasetRole ?? selectedCrop?.datasetRole ?? null;
  const selectedCropDatasetItemId =
    trainingCropDatasetItem?.datasetItemId ?? selectedCrop?.datasetItemId ?? null;
  const selectedCropIsAssigned = Boolean(selectedCropDatasetItemId);
  const selectedEllipse =
    evidence?.beeEllipses.find((ellipse) => ellipse.annotationId === selectedEllipseId) ?? null;
  const selectedProposal =
    candidateProposals.find((proposal) => proposal.proposalId === selectedProposalId) ?? null;
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
  const canFlipHeadTail = canAdjustEllipse(selectedCrop, selectedEllipse, {
    rotationDegrees: (selectedEllipse?.rotationDegrees ?? 0) + 180
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
    void refreshCropsForPhoto(selectedPhoto.inspectionPhotoId);
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
      })
      .catch((error) => onError(toApiError(error)));

    return () => {
      cancelled = true;
    };
  }, [devUserId, onError, selectedPhoto, workspaceId]);

  useEffect(() => {
    if (!selectedCropId) {
      setEvidence(null);
      setTrainingCropDatasetItem(null);
      return;
    }
    setTrainingCropDatasetItem(null);
    setCropZoom(1);
    setCandidateProposals([]);
    setSelectedProposalId(null);
    setEditedProposalIds(new Set());
    setCandidateProposalMessage(null);
    void refreshEvidence(selectedCropId);
  }, [selectedCropId]);

  useEffect(() => {
    refreshTrainingRuns().catch((error) => onError(toApiError(error)));
    refreshModelCandidates().catch((error) => onError(toApiError(error)));
    refreshBenchmarkEvaluations().catch((error) => onError(toApiError(error)));
    refreshRequestedReviews().catch((error) => onError(toApiError(error)));
  }, [devUserId, workspaceId]);

  useEffect(() => {
    if (!selectedModelCandidateId) {
      setBenchmarkReadiness(null);
      return;
    }
    refreshBenchmarkReadiness(selectedModelCandidateId).catch((error) =>
      setBenchmarkEvaluationPollError(toApiError(error).message)
    );
  }, [selectedModelCandidateId, workspaceId]);

  useEffect(() => {
    if (!shouldPollTrainingRuns) {
      return;
    }
    const interval = window.setInterval(() => {
      setTrainingRunClockTick((current) => current + 1);
      refreshTrainingRuns().catch((error) => {
        setTrainingRunPollError(toApiError(error).message);
      });
    }, 3000);
    return () => window.clearInterval(interval);
  }, [shouldPollTrainingRuns, workspaceId]);

  useEffect(() => {
    if (!shouldPollBenchmarkEvaluations) {
      return;
    }
    const interval = window.setInterval(() => {
      setTrainingRunClockTick((current) => current + 1);
      refreshBenchmarkEvaluations().catch((error) => {
        setBenchmarkEvaluationPollError(toApiError(error).message);
      });
    }, 3000);
    return () => window.clearInterval(interval);
  }, [shouldPollBenchmarkEvaluations, workspaceId]);

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

  function updateCropZoom(nextZoom: number) {
    setCropZoom(clamp(Math.round(nextZoom * 4) / 4, 1, 4));
  }

  function panCropViewport(deltaX: number, deltaY: number) {
    cropViewportRef.current?.scrollBy({ left: deltaX, top: deltaY, behavior: "smooth" });
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

  async function suggestBeeAnnotationsForSelectedCrop() {
    if (!selectedCrop || cropLocked) {
      return;
    }
    await runCropAction("Suggesting bee ellipses", async () => {
      const response = await suggestTrainingCropBeeAnnotations({
        devUserId,
        workspaceId,
        trainingCropId: selectedCrop.trainingCropId,
        modelCandidateId: selectedModelCandidateId,
        confidenceThreshold: candidateThreshold,
        maxSuggestions: 50
      });
      setSelectedModelCandidateId(response.modelCandidateId);
      setCandidateProposals(response.suggestions);
      setEditedProposalIds(new Set());
      setSelectedProposalId(response.suggestions[0]?.proposalId ?? null);
      setCandidateProposalMessage(
        response.suggestions.length === 0
          ? `No suggestions above ${Math.round(response.threshold * 100)}% confidence.`
          : `${response.suggestions.length} suggestion${
              response.suggestions.length === 1 ? "" : "s"
            } from ${response.modelCandidateHumanReadableId}.`
      );
    });
  }

  function updateSelectedProposal(values: Partial<EllipseGeometry>) {
    if (!selectedCrop || !selectedProposal || cropLocked) {
      return;
    }
    const nextProposal: BeeAnnotationProposal = {
      ...selectedProposal,
      centerX: values.centerX ?? selectedProposal.centerX,
      centerY: values.centerY ?? selectedProposal.centerY,
      radiusX: values.radiusX ?? selectedProposal.radiusX,
      radiusY: values.radiusY ?? selectedProposal.radiusY,
      rotationDegrees: values.rotationDegrees ?? selectedProposal.rotationDegrees
    };
    if (!ellipseIsAllowedForCrop(selectedCrop, { ...nextProposal, annotationType: "partial_visible_bee" })) {
      return;
    }
    setCandidateProposals((current) =>
      current.map((proposal) =>
        proposal.proposalId === selectedProposal.proposalId ? nextProposal : proposal
      )
    );
    setEditedProposalIds((current) => new Set([...current, selectedProposal.proposalId]));
  }

  async function acceptSelectedProposal(annotationType: BeeAnnotationType) {
    if (!selectedCrop || !selectedProposal || cropLocked) {
      return;
    }
    const edited =
      editedProposalIds.has(selectedProposal.proposalId) ||
      annotationType !== selectedProposal.annotationType;
    await runCropAction("Accepting suggested bee ellipse", async () => {
      const ellipse = await createTrainingCropEllipse({
        devUserId,
        workspaceId,
        trainingCropId: selectedCrop.trainingCropId,
        annotationType,
        centerX: selectedProposal.centerX,
        centerY: selectedProposal.centerY,
        radiusX: selectedProposal.radiusX,
        radiusY: selectedProposal.radiusY,
        rotationDegrees: selectedProposal.rotationDegrees,
        provenance: {
          source: "model_candidate",
          reviewMethod: "human_reviewed_candidate",
          modelCandidateId: selectedProposal.modelCandidateId,
          candidateConfidence: selectedProposal.confidence,
          candidateThreshold: selectedProposal.threshold,
          rawModelClass: selectedProposal.rawModelClass,
          rawYoloObb: selectedProposal.rawYoloObb,
          candidateReviewDecision: edited ? "accepted_with_edits" : "accepted"
        }
      });
      setSelectedEllipseId(ellipse.annotationId);
      setCandidateProposals((current) =>
        current.filter((proposal) => proposal.proposalId !== selectedProposal.proposalId)
      );
      setEditedProposalIds((current) => {
        const next = new Set(current);
        next.delete(selectedProposal.proposalId);
        return next;
      });
      setSelectedProposalId(null);
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

  async function reopenCrop() {
    if (!selectedCrop) {
      return;
    }
    await runCropAction("Reopening Training Crop", async () => {
      await updateTrainingCrop({
        devUserId,
        workspaceId,
        trainingCropId: selectedCrop.trainingCropId,
        reviewStatus: "review_pending",
        notes: cropNotes
      });
      await refreshEvidence(selectedCrop.trainingCropId);
      if (selectedPhoto) await refreshCropsForPhoto(selectedPhoto.inspectionPhotoId);
    });
  }

  async function assignSelectedCropToDataset() {
    if (!selectedCrop) {
      return;
    }
    await runCropAction("Assigning Dataset Item", async () => {
      const datasetItem = await createTrainingCropDatasetItem({
        devUserId,
        workspaceId,
        trainingCropId: selectedCrop.trainingCropId,
        datasetRole,
        sourceGroupKey: datasetRole === "benchmark" ? datasetSourceGroupKey : "",
        assignmentNote: datasetAssignmentNote,
        exclusionReason: datasetRole === "excluded" ? datasetExclusionReason : null
      });
      setTrainingCropDatasetItem(datasetItem);
      await refreshEvidence(selectedCrop.trainingCropId);
      if (selectedPhoto) await refreshCropsForPhoto(selectedPhoto.inspectionPhotoId);
    });
  }

  async function createExportManifest() {
    await runCropAction("Creating YOLO OBB export", async () => {
      const manifest = await createYoloObbExport({ devUserId, workspaceId });
      setYoloObbExport(manifest);
    });
  }

  async function createPhysicalExportPackage() {
    await runCropAction("Creating physical export package", async () => {
      const physicalExport = await createPhysicalYoloObbExport({ devUserId, workspaceId });
      setPhysicalYoloObbExport(physicalExport);
    });
  }

  async function refreshModelTrainingReadiness() {
    await runCropAction("Checking model training readiness", async () => {
      const readiness = await fetchModelTrainingReadiness({ devUserId, workspaceId });
      setModelTrainingReadiness(readiness);
      await refreshTrainingRuns();
    });
  }

  async function refreshTrainingRuns() {
    const listing = await fetchTrainingRuns({ devUserId, workspaceId });
    setTrainingRuns(listing.trainingRuns);
    setTrainingRunsLastCheckedAt(new Date().toISOString());
    setTrainingRunPollError(null);
    setTrainingRun((current) => {
      const refreshedCurrent = current
        ? listing.trainingRuns.find((run) => run.trainingRunId === current.trainingRunId)
        : null;
      return refreshedCurrent ?? listing.trainingRuns.at(0) ?? null;
    });
    if (listing.trainingRuns.some((run) => run.modelCandidateId)) {
      await refreshModelCandidates();
    }
  }

  async function refreshModelCandidates() {
    const listing = await fetchModelCandidates({ devUserId, workspaceId });
    setModelCandidates(listing.modelCandidates);
    setSelectedModelCandidateId((current) =>
      current && listing.modelCandidates.some((candidate) => candidate.modelCandidateId === current)
        ? current
        : (listing.modelCandidates[0]?.modelCandidateId ?? null)
    );
    return listing.modelCandidates;
  }

  async function refreshBenchmarkReadiness(modelCandidateId: string) {
    const readiness = await fetchBenchmarkEvaluationReadiness({
      devUserId,
      workspaceId,
      modelCandidateId
    });
    setBenchmarkReadiness(readiness);
    setBenchmarkEvaluationPollError(null);
    return readiness;
  }

  async function refreshBenchmarkEvaluations() {
    const listing = await fetchBenchmarkEvaluations({ devUserId, workspaceId });
    setBenchmarkEvaluations(listing.benchmarkEvaluations);
    setBenchmarkEvaluationsLastCheckedAt(new Date().toISOString());
    setBenchmarkEvaluationPollError(null);
    setBenchmarkEvaluation((current) => {
      const refreshedCurrent = current
        ? listing.benchmarkEvaluations.find(
            (evaluation) => evaluation.benchmarkEvaluationId === current.benchmarkEvaluationId
          )
        : null;
      return refreshedCurrent ?? listing.benchmarkEvaluations.at(0) ?? null;
    });
    return listing.benchmarkEvaluations;
  }

  async function refreshRequestedReviews() {
    const listing = await fetchRequestedReviews({ devUserId, workspaceId });
    setRequestedReviews(listing.reviewQueueItems);
    return listing.reviewQueueItems;
  }

  async function requestSelectedCropReview() {
    if (!selectedCrop) {
      return;
    }
    await runCropAction("Requesting Training Crop review", async () => {
      await requestTrainingCropReview({
        devUserId,
        workspaceId,
        trainingCropId: selectedCrop.trainingCropId,
        requestNotes: reviewRequestNotes
      });
      setReviewRequestNotes("");
      await refreshRequestedReviews();
    });
  }

  async function cancelSelectedCropReview() {
    if (!selectedCropActiveReviewItem) {
      return;
    }
    await runCropAction("Cancelling Training Crop review request", async () => {
      await cancelReviewWorkItem({
        devUserId,
        reviewQueueItemId: selectedCropActiveReviewItem.reviewQueueItemId,
        cancellationNotes
      });
      setCancellationNotes("");
      await refreshRequestedReviews();
    });
  }

  async function useTrainingRunCandidateForCropYolo(candidateId: string) {
    const candidates = await refreshModelCandidates();
    setSelectedModelCandidateId(candidateId);
    const matchingCandidate =
      candidates.find((candidate) => candidate.modelCandidateId === candidateId) ?? null;
    const candidateLabel = matchingCandidate?.humanReadableId ?? candidateId;
    const message = `Now using ${candidateLabel} for crop YOLO.`;
    setModelCandidateSelectionMessage(message);
    setCandidateProposalMessage(message);
    await refreshBenchmarkReadiness(candidateId);
  }

  async function createModelDatasetVersion() {
    await runCropAction("Creating Dataset Version", async () => {
      const nextDatasetVersion = await createDatasetVersion({ devUserId, workspaceId });
      setDatasetVersion(nextDatasetVersion);
      setTrainingRun(null);
      const readiness = await fetchModelTrainingReadiness({ devUserId, workspaceId });
      setModelTrainingReadiness(readiness);
      await refreshTrainingRuns();
      await refreshModelCandidates();
    });
  }

  async function startBeeDetectorTrainingRun() {
    if (!datasetVersion) {
      return;
    }
    await runCropAction("Starting Bee Detector training", async () => {
      const nextTrainingRun = await startModelTrainingRun({
        devUserId,
        workspaceId,
        datasetVersionId: datasetVersion.datasetVersionId,
        acknowledgeHighSeverityWarnings: acknowledgeModelWarnings
      });
      setTrainingRun(nextTrainingRun);
      const readiness = await fetchModelTrainingReadiness({ devUserId, workspaceId });
      setModelTrainingReadiness(readiness);
      await refreshTrainingRuns();
    });
  }

  async function startSelectedBenchmarkEvaluation() {
    if (!selectedModelCandidateId) {
      return;
    }
    await runCropAction("Starting Benchmark Evaluation", async () => {
      const nextEvaluation = await startBenchmarkEvaluation({
        devUserId,
        workspaceId,
        modelCandidateId: selectedModelCandidateId,
        acknowledgeHighSeverityWarnings: acknowledgeModelWarnings
      });
      setBenchmarkEvaluation(nextEvaluation);
      await refreshBenchmarkReadiness(selectedModelCandidateId);
      await refreshBenchmarkEvaluations();
    });
  }

  async function cancelSelectedBenchmarkEvaluation() {
    if (!benchmarkEvaluation) {
      return;
    }
    await runCropAction("Cancelling Benchmark Evaluation", async () => {
      const cancelled = await cancelBenchmarkEvaluation({
        devUserId,
        workspaceId,
        benchmarkEvaluationId: benchmarkEvaluation.benchmarkEvaluationId,
        reason: "Cancelled from local benchmark evaluation UI."
      });
      setBenchmarkEvaluation(cancelled);
      if (selectedModelCandidateId) {
        await refreshBenchmarkReadiness(selectedModelCandidateId);
      }
      await refreshBenchmarkEvaluations();
    });
  }

  async function cancelSelectedTrainingRun() {
    if (!trainingRun) {
      return;
    }
    await runCropAction("Cancelling Bee Detector training", async () => {
      const cancelled = await cancelTrainingRun({
        devUserId,
        workspaceId,
        trainingRunId: trainingRun.trainingRunId,
        reason: "Cancelled from local training UI."
      });
      setTrainingRun(cancelled);
      const readiness = await fetchModelTrainingReadiness({ devUserId, workspaceId });
      setModelTrainingReadiness(readiness);
      await refreshTrainingRuns();
    });
  }

  async function abandonSelectedTrainingRun() {
    if (!trainingRun) {
      return;
    }
    await runCropAction("Abandoning stale Bee Detector training", async () => {
      const abandoned = await abandonTrainingRun({
        devUserId,
        workspaceId,
        trainingRunId: trainingRun.trainingRunId,
        reason:
          trainingRun.status === "cancelling"
            ? "Marked abandoned from local training UI after cancellation did not stop promptly."
            : "Marked abandoned from local training UI after stale heartbeat.",
        force: trainingRun.status === "cancelling"
      });
      setTrainingRun(abandoned);
      const readiness = await fetchModelTrainingReadiness({ devUserId, workspaceId });
      setModelTrainingReadiness(readiness);
      await refreshTrainingRuns();
    });
  }

  async function deleteSelectedTrainingRun() {
    if (!trainingRun) {
      return;
    }
    await runCropAction("Deleting unevidenced Bee Detector training run", async () => {
      await deleteTrainingRun({
        devUserId,
        workspaceId,
        trainingRunId: trainingRun.trainingRunId,
        reason: "Deleted unevidenced local training run from UI."
      });
      setTrainingRun(null);
      const readiness = await fetchModelTrainingReadiness({ devUserId, workspaceId });
      setModelTrainingReadiness(readiness);
      await refreshTrainingRuns();
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
                    Crop {index + 1} / {crop.reviewStatus} / {crop.visibleBeeStatus} /{" "}
                    {formatDatasetRoleLabel(crop.datasetRole)}
                  </button>
                </li>
              ))}
            </ul>
          ) : null}

          {selectedCrop && sourceImageUrl ? (
            <section className="crop-editor" aria-label="Selected Training Crop editor">
              <div className="crop-editing-tool" data-testid="training-crop-editing-tool">
                <div className="crop-workspace">
                  <div className="crop-viewport-toolbar" aria-label="Crop viewport controls">
                    <button
                      type="button"
                      onClick={() => updateCropZoom(cropZoom - 0.25)}
                      disabled={cropZoom <= 1}
                      data-testid="crop-zoom-out-button"
                      title="Zoom out"
                    >
                      <Minus size={18} />
                      Zoom
                    </button>
                    <label className="range-control">
                      <span>Zoom {Math.round(cropZoom * 100)}%</span>
                      <input
                        type="range"
                        min={1}
                        max={4}
                        step={0.25}
                        value={cropZoom}
                        onChange={(event) => updateCropZoom(Number(event.target.value))}
                        data-testid="crop-zoom-slider"
                      />
                    </label>
                    <button
                      type="button"
                      onClick={() => updateCropZoom(cropZoom + 0.25)}
                      disabled={cropZoom >= 4}
                      data-testid="crop-zoom-in-button"
                      title="Zoom in"
                    >
                      <Plus size={18} />
                      Zoom
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        updateCropZoom(1);
                        cropViewportRef.current?.scrollTo({ left: 0, top: 0, behavior: "smooth" });
                      }}
                      data-testid="crop-zoom-reset-button"
                      title="Reset crop view"
                    >
                      <RefreshCw size={18} />
                      Reset
                    </button>
                  </div>
                  <div className="crop-pan-controls" aria-label="Pan crop viewport">
                    <button
                      type="button"
                      onClick={() => panCropViewport(0, -120)}
                      data-testid="crop-pan-up-button"
                      title="Pan up"
                    >
                      <ArrowUp size={18} />
                    </button>
                    <button
                      type="button"
                      onClick={() => panCropViewport(-120, 0)}
                      data-testid="crop-pan-left-button"
                      title="Pan left"
                    >
                      <ArrowLeft size={18} />
                    </button>
                    <button
                      type="button"
                      onClick={() => panCropViewport(120, 0)}
                      data-testid="crop-pan-right-button"
                      title="Pan right"
                    >
                      <ArrowRight size={18} />
                    </button>
                    <button
                      type="button"
                      onClick={() => panCropViewport(0, 120)}
                      data-testid="crop-pan-down-button"
                      title="Pan down"
                    >
                      <ArrowDown size={18} />
                    </button>
                  </div>
                  <div
                    className="crop-surface-viewport"
                    ref={cropViewportRef}
                    data-testid="training-crop-surface-viewport"
                  >
                    <div
                      className="crop-surface"
                      style={{
                        aspectRatio: `${selectedCrop.cropWidth} / ${selectedCrop.cropHeight}`,
                        width: `${cropZoom * 100}%`
                      }}
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
                          aria-label={`${ellipse.annotationType} head direction ${formatGeometryValue(
                            normalizeRotation(ellipse.rotationDegrees)
                          )} degrees`}
                        >
                          <span className="ellipse-head-arrow" data-testid="training-crop-ellipse-head-arrow" />
                        </button>
                      ))}
                      {candidateProposals.map((proposal) => (
                        <button
                          key={proposal.proposalId}
                          type="button"
                          className={`bee-ellipse candidate ${
                            proposal.proposalId === selectedProposalId ? "selected" : ""
                          }`}
                          style={proposalStyle(selectedCrop, proposal)}
                          onClick={(event) => {
                            event.stopPropagation();
                            setSelectedProposalId(proposal.proposalId);
                            setSelectedEllipseId(null);
                          }}
                          data-testid="candidate-bee-proposal"
                          aria-label={`Suggested bee ${Math.round(proposal.confidence * 100)}% confidence`}
                        >
                          <span className="ellipse-head-arrow" data-testid="candidate-bee-proposal-head-arrow" />
                        </button>
                      ))}
                    </div>
                  </div>
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
                          )} degree head direction`
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
                    <button
                      type="button"
                      disabled={controlLocked || !canFlipHeadTail}
                      onClick={() =>
                        selectedEllipse &&
                        void updateSelectedEllipse({
                          rotationDegrees: selectedEllipse.rotationDegrees + 180
                        })
                      }
                      data-testid="flip-training-ellipse-head-tail-button"
                      title="Flip head/tail"
                    >
                      <RotateCw size={18} />
                      Flip head/tail
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
                <div
                  className="crop-ellipse-controls candidate-controls"
                  data-testid="candidate-prelabel-controls"
                  aria-label="Model Candidate pre-labelling controls"
                >
                  <div className="candidate-control-header">
                    <div>
                      <strong>YOLO crop pre-labels</strong>
                      <p data-testid="candidate-prelabel-message">
                        {candidateProposalMessage ??
                          "Run the selected Bee Detector Model Candidate on this crop."}
                      </p>
                    </div>
                    <button
                      type="button"
                      disabled={cropLocked || Boolean(workingLabel) || modelCandidates.length === 0}
                      onClick={() => void suggestBeeAnnotationsForSelectedCrop()}
                      data-testid="suggest-bees-button"
                    >
                      <Play size={18} />
                      YOLO this crop
                    </button>
                  </div>
                  <div className="review-state" data-testid="selected-crop-yolo-candidate-state">
                    {selectedModelCandidateId
                      ? `Using ${
                          modelCandidates.find(
                            (candidate) => candidate.modelCandidateId === selectedModelCandidateId
                          )?.humanReadableId ?? selectedModelCandidateId
                        } for crop YOLO.`
                      : "No Model Candidate selected. Train a baseline or refresh candidates first."}
                  </div>
                  <label>
                    <span>Model Candidate</span>
                    <select
                      value={selectedModelCandidateId ?? ""}
                      onChange={(event) => setSelectedModelCandidateId(event.target.value || null)}
                      disabled={cropLocked || Boolean(workingLabel) || modelCandidates.length === 0}
                      data-testid="candidate-model-select"
                    >
                      {modelCandidates.length === 0 ? (
                        <option value="">No candidates</option>
                      ) : null}
                      {modelCandidates.map((candidate) => (
                        <option key={candidate.modelCandidateId} value={candidate.modelCandidateId}>
                          {candidate.humanReadableId} / {candidate.adapterType}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="range-control">
                    <span>Confidence {Math.round(candidateThreshold * 100)}%</span>
                    <input
                      type="range"
                      min={0.01}
                      max={0.9}
                      step={0.01}
                      value={candidateThreshold}
                      onChange={(event) => setCandidateThreshold(Number(event.target.value))}
                      data-testid="candidate-confidence-threshold-slider"
                    />
                  </label>
                  {selectedProposal ? (
                    <>
                      <div className="export-summary candidate-summary" data-testid="selected-candidate-proposal">
                        <strong>{selectedProposal.modelCandidateHumanReadableId}</strong>
                        <span>Confidence {Math.round(selectedProposal.confidence * 100)}%</span>
                        <span>Threshold {Math.round(selectedProposal.threshold * 100)}%</span>
                        <span>{selectedProposal.rawModelClass}</span>
                        <span>
                          {editedProposalIds.has(selectedProposal.proposalId)
                            ? "edited"
                            : "unchanged"}
                        </span>
                      </div>
                      <div className="control-cluster" aria-label="Move selected candidate proposal">
                        <button
                          type="button"
                          disabled={cropLocked || Boolean(workingLabel)}
                          onClick={() =>
                            updateSelectedProposal({ centerY: selectedProposal.centerY - 5 })
                          }
                          data-testid="nudge-candidate-proposal-up-button"
                          title="Nudge suggestion up"
                        >
                          <ArrowUp size={18} />
                        </button>
                        <button
                          type="button"
                          disabled={cropLocked || Boolean(workingLabel)}
                          onClick={() =>
                            updateSelectedProposal({ centerX: selectedProposal.centerX - 5 })
                          }
                          data-testid="nudge-candidate-proposal-left-button"
                          title="Nudge suggestion left"
                        >
                          <ArrowLeft size={18} />
                        </button>
                        <button
                          type="button"
                          disabled={cropLocked || Boolean(workingLabel)}
                          onClick={() =>
                            updateSelectedProposal({ centerX: selectedProposal.centerX + 5 })
                          }
                          data-testid="nudge-candidate-proposal-right-button"
                          title="Nudge suggestion right"
                        >
                          <ArrowRight size={18} />
                        </button>
                        <button
                          type="button"
                          disabled={cropLocked || Boolean(workingLabel)}
                          onClick={() =>
                            updateSelectedProposal({ centerY: selectedProposal.centerY + 5 })
                          }
                          data-testid="nudge-candidate-proposal-down-button"
                          title="Nudge suggestion down"
                        >
                          <ArrowDown size={18} />
                        </button>
                      </div>
                      <div className="control-cluster" aria-label="Shape selected candidate proposal">
                        <button
                          type="button"
                          disabled={cropLocked || Boolean(workingLabel)}
                          onClick={() =>
                            updateSelectedProposal({
                              rotationDegrees: selectedProposal.rotationDegrees - 5
                            })
                          }
                          data-testid="rotate-candidate-proposal-anticlockwise-button"
                          title="Rotate suggestion anti-clockwise"
                        >
                          <RotateCcw size={18} />
                        </button>
                        <button
                          type="button"
                          disabled={cropLocked || Boolean(workingLabel)}
                          onClick={() =>
                            updateSelectedProposal({
                              rotationDegrees: selectedProposal.rotationDegrees + 5
                            })
                          }
                          data-testid="rotate-candidate-proposal-clockwise-button"
                          title="Rotate suggestion clockwise"
                        >
                          <RotateCw size={18} />
                        </button>
                        <button
                          type="button"
                          disabled={cropLocked || Boolean(workingLabel)}
                          onClick={() =>
                            updateSelectedProposal({
                              radiusX: Math.max(5, selectedProposal.radiusX - 5)
                            })
                          }
                          data-testid="shrink-candidate-proposal-x-button"
                          title="Reduce suggested horizontal radius"
                        >
                          <Minus size={18} />
                          Rx
                        </button>
                        <button
                          type="button"
                          disabled={cropLocked || Boolean(workingLabel)}
                          onClick={() =>
                            updateSelectedProposal({ radiusX: selectedProposal.radiusX + 5 })
                          }
                          data-testid="grow-candidate-proposal-x-button"
                          title="Increase suggested horizontal radius"
                        >
                          <Plus size={18} />
                          Rx
                        </button>
                      </div>
                      <div className="button-row">
                        <button
                          type="button"
                          disabled={cropLocked || Boolean(workingLabel)}
                          onClick={() => void acceptSelectedProposal("complete_visible_bee")}
                          data-testid="accept-candidate-proposal-complete-button"
                        >
                          <Check size={18} />
                          Accept complete
                        </button>
                        <button
                          type="button"
                          disabled={cropLocked || Boolean(workingLabel)}
                          onClick={() => void acceptSelectedProposal("partial_visible_bee")}
                          data-testid="accept-candidate-proposal-partial-button"
                        >
                          <Check size={18} />
                          Accept partial
                        </button>
                      </div>
                    </>
                  ) : null}
                </div>
              </div>

              <div className="result-grid crop-metrics" data-testid="training-crop-metrics">
                <Metric label="Review" value={selectedCrop.reviewStatus} />
                <Metric label="Visible bees" value={selectedCrop.visibleBeeStatus} />
                <Metric label="Dataset role" value={formatDatasetRoleLabel(selectedCropDatasetRole)} />
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
                {cropLocked ? (
                  <button
                    type="button"
                    disabled={Boolean(workingLabel)}
                    onClick={() => void reopenCrop()}
                    data-testid="reopen-training-crop-button"
                  >
                    <RotateCcw size={18} />
                    Reopen crop
                  </button>
                ) : null}
              </div>

              <div className="metadata-panel crop-dataset-controls">
                <div>
                  <strong>Bee Annotation Repository</strong>
                  <p>
                    Assign this completed Training Crop into the workspace dataset, then create a
                    YOLO OBB manifest from eligible items.
                  </p>
                </div>
                <label>
                  <span>Dataset role</span>
                  <select
                    value={datasetRole}
                    onChange={(event) => setDatasetRole(event.target.value as DatasetRole)}
                    disabled={selectedCropIsAssigned || Boolean(workingLabel)}
                    data-testid="training-crop-dataset-role-select"
                  >
                    <option value="training">Training</option>
                    <option value="validation">Validation</option>
                    <option value="benchmark">Benchmark</option>
                    <option value="excluded">Excluded</option>
                  </select>
                </label>
                <label>
                  <span>Assignment note</span>
                  <input
                    value={datasetAssignmentNote}
                    maxLength={500}
                    onChange={(event) => setDatasetAssignmentNote(event.target.value)}
                    disabled={selectedCropIsAssigned || Boolean(workingLabel)}
                    data-testid="training-crop-dataset-assignment-note-input"
                  />
                </label>
                {datasetRole === "benchmark" ? (
                  <label>
                    <span>Source group key</span>
                    <input
                      value={datasetSourceGroupKey}
                      maxLength={100}
                      onChange={(event) => setDatasetSourceGroupKey(event.target.value)}
                      disabled={selectedCropIsAssigned || Boolean(workingLabel)}
                      data-testid="training-crop-dataset-source-group-key-input"
                    />
                  </label>
                ) : null}
                {datasetRole === "excluded" ? (
                  <label>
                    <span>Dataset exclusion reason</span>
                    <select
                      value={datasetExclusionReason}
                      onChange={(event) =>
                        setDatasetExclusionReason(event.target.value as DatasetExclusionReason)
                      }
                      disabled={selectedCropIsAssigned || Boolean(workingLabel)}
                      data-testid="training-crop-dataset-exclusion-reason-select"
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
                <button
                  type="button"
                  disabled={
                    !selectedCrop ||
                    selectedCropIsAssigned ||
                    Boolean(workingLabel) ||
                    selectedCrop.reviewStatus === "review_pending" ||
                    (datasetRole === "benchmark" && datasetSourceGroupKey.trim().length === 0)
                  }
                  onClick={() => void assignSelectedCropToDataset()}
                  data-testid="assign-training-crop-dataset-role-button"
                >
                  <ShieldCheck size={18} />
                  Assign item
                </button>
                <button
                  type="button"
                  disabled={Boolean(workingLabel)}
                  onClick={() => void createExportManifest()}
                  data-testid="create-yolo-obb-export-button"
                >
                  <FileImage size={18} />
                  Export manifest
                </button>
                <button
                  type="button"
                  disabled={Boolean(workingLabel)}
                  onClick={() => void createPhysicalExportPackage()}
                  data-testid="create-physical-yolo-obb-export-button"
                >
                  <CloudUpload size={18} />
                  Export package
                </button>
                <div className="review-state" data-testid="training-crop-dataset-item-state">
                  {selectedCropDatasetRole
                    ? `Dataset item: ${formatDatasetRoleLabel(selectedCropDatasetRole)}${
                        trainingCropDatasetItem
                          ? ` / ${trainingCropDatasetItem.reviewedEllipseSnapshots.length} ellipse snapshots`
                          : ""
                      }`
                    : selectedCrop.reviewStatus === "review_pending"
                      ? "Complete or exclude the Training Crop before assigning a Dataset Item."
                      : "Ready for Dataset Item assignment."}
                </div>
                <div className="review-request-panel" data-testid="training-crop-review-request-panel">
                  <div>
                    <strong>Requested Reviews</strong>
                    <p>Make this completed Training Crop available to eligible Reviewers.</p>
                    <p>
                      Queue outcomes do not automatically change Dataset Items, Dataset Versions,
                      Training Runs, Model Candidates, or Benchmark Evaluations.
                    </p>
                  </div>
                  <label>
                    <span>Neutral request notes</span>
                    <input
                      value={reviewRequestNotes}
                      maxLength={500}
                      onChange={(event) => setReviewRequestNotes(event.target.value)}
                      disabled={
                        Boolean(workingLabel) ||
                        selectedCrop.reviewStatus !== "review_complete" ||
                        Boolean(selectedCropActiveReviewItem)
                      }
                      data-testid="review-request-notes-input"
                    />
                  </label>
                  <button
                    type="button"
                    disabled={
                      Boolean(workingLabel) ||
                      selectedCrop.reviewStatus !== "review_complete" ||
                      selectedCrop.visibleBeeStatus !== "has_visible_bees" ||
                      (evidence?.beeEllipses.length ?? 0) === 0 ||
                      Boolean(selectedCropActiveReviewItem)
                    }
                    onClick={() => void requestSelectedCropReview()}
                    data-testid="request-training-crop-review-button"
                  >
                    <ShieldCheck size={18} />
                    Request review
                  </button>
                  {selectedCropActiveReviewItem ? (
                    <>
                      <label>
                        <span>Cancellation notes</span>
                        <input
                          value={cancellationNotes}
                          maxLength={500}
                          onChange={(event) => setCancellationNotes(event.target.value)}
                          disabled={Boolean(workingLabel)}
                          data-testid="review-cancellation-notes-input"
                        />
                      </label>
                      <button
                        type="button"
                        disabled={Boolean(workingLabel) || cancellationNotes.trim().length === 0}
                        onClick={() => void cancelSelectedCropReview()}
                        data-testid="cancel-training-crop-review-button"
                      >
                        <CircleAlert size={18} />
                        Cancel request
                      </button>
                    </>
                  ) : null}
                  <div className="export-summary" data-testid="requested-reviews-summary">
                    {selectedCropReviewItems.length === 0 ? (
                      <span>No requested reviews for this crop</span>
                    ) : (
                      selectedCropReviewItems.map((item) => (
                        <span key={item.reviewQueueItemId}>
                          {item.humanReadableId} / {item.status}
                          {item.completedOutcome ? ` / ${item.completedOutcome}` : ""}
                          {item.completedReviewerDisplayIdentity
                            ? ` / ${item.completedReviewerDisplayIdentity}`
                            : ""}
                        </span>
                      ))
                    )}
                  </div>
                </div>
                {yoloObbExport ? (
                  <div className="export-summary" data-testid="yolo-obb-export-summary">
                    <strong>{yoloObbExport.exportFormat} manifest</strong>
                    <span>Training {yoloObbExport.trainingItemCount}</span>
                    <span>Validation {yoloObbExport.validationItemCount}</span>
                    <span>Benchmark protected {yoloObbExport.benchmarkItemCount}</span>
                    <span>Excluded {yoloObbExport.excludedDatasetItems.length}</span>
                    <span>Labels {yoloObbExport.labelEntries.length}</span>
                    <code>class x1 y1 x2 y2 x3 y3 x4 y4</code>
                  </div>
                ) : null}
                {physicalYoloObbExport ? (
                  <div
                    className="export-summary package-summary"
                    data-testid="physical-yolo-obb-export-summary"
                  >
                    <strong>{physicalYoloObbExport.exportFormat} package</strong>
                    <span>Training {physicalYoloObbExport.trainingItemCount}</span>
                    <span>Validation {physicalYoloObbExport.validationItemCount}</span>
                    <span>Benchmark protected {physicalYoloObbExport.benchmarkItemCount}</span>
                    <span>Excluded {physicalYoloObbExport.excludedItemCount}</span>
                    <span>Files {physicalYoloObbExport.generatedFiles.length}</span>
                    <code>{physicalYoloObbExport.packagePath}</code>
                    <code>{physicalYoloObbExport.manifestPath}</code>
                    <code>{physicalYoloObbExport.datasetYamlPath}</code>
                    <p>{physicalYoloObbExport.caveat}</p>
                  </div>
                ) : null}
                <div className="model-training-panel" data-testid="model-training-panel">
                  <div>
                    <strong>Bee Detector training baseline</strong>
                    <p>
                      Create a locked Dataset Version, then run the local YOLO OBB training adapter.
                    </p>
                  </div>
                  <div className="button-row">
                    <button
                      type="button"
                      disabled={Boolean(workingLabel)}
                      onClick={() => void refreshModelTrainingReadiness()}
                      data-testid="model-training-readiness-button"
                    >
                      <RefreshCw size={18} />
                      Check readiness
                    </button>
                    <button
                      type="button"
                      disabled={Boolean(workingLabel)}
                      onClick={() => void createModelDatasetVersion()}
                      data-testid="create-dataset-version-button"
                    >
                      <FileImage size={18} />
                      Dataset Version
                    </button>
                    <button
                      type="button"
                      disabled={!canStartModelTraining}
                      onClick={() => void startBeeDetectorTrainingRun()}
                      data-testid="start-model-training-run-button"
                    >
                      <Play size={18} />
                      Train baseline
                    </button>
                  </div>
                  <label className="checkbox-row">
                    <input
                      type="checkbox"
                      checked={acknowledgeModelWarnings}
                      onChange={(event) => setAcknowledgeModelWarnings(event.target.checked)}
                      data-testid="acknowledge-model-training-warnings-checkbox"
                    />
                    <span>Acknowledge high-severity dataset warnings for this baseline run</span>
                  </label>
                  {modelTrainingReadiness ? (
                    <div className="export-summary" data-testid="model-training-readiness-summary">
                      <strong>
                        {modelTrainingReadiness.adapterType} / {modelTrainingReadiness.databasePurpose}
                      </strong>
                      <span>Training {modelTrainingReadiness.trainingItemCount}</span>
                      <span>Validation {modelTrainingReadiness.validationItemCount}</span>
                      <span>Benchmark {modelTrainingReadiness.benchmarkItemCount}</span>
                      <span>
                        {modelTrainingReadiness.realAdapterAvailable
                          ? "Real adapter available"
                          : "Real adapter unavailable"}
                      </span>
                      {modelTrainingReadiness.warnings.map((warning) => (
                        <span key={warning.code}>
                          {warning.severity}: {warning.code}
                        </span>
                      ))}
                      {!modelTrainingReadiness.eligibleToStartTraining ? (
                        <p data-testid="model-training-blocker">
                          Training cannot start until readiness blockers are resolved.
                        </p>
                      ) : null}
                    </div>
                  ) : null}
                  {datasetVersion ? (
                    <div className="export-summary" data-testid="dataset-version-summary">
                      <strong>{datasetVersion.humanReadableId}</strong>
                      <span>Training {datasetVersion.trainingItemCount}</span>
                      <span>Validation {datasetVersion.validationItemCount}</span>
                      <span>Benchmark protected {datasetVersion.benchmarkItemCount}</span>
                      <span>Warnings {datasetVersion.warnings.length}</span>
                      <code>{datasetVersion.exportFormat}</code>
                    </div>
                  ) : null}
                  {trainingRun ? (
                    <div className="export-summary" data-testid="model-training-run-summary">
                      <strong>{trainingRun.humanReadableId}</strong>
                      <span>{trainingRun.status}</span>
                      <span>Phase {trainingRun.phase}</span>
                      <span>Progress {formatProgressPercent(trainingRun.progressPercent)}</span>
                      <span>{trainingRun.adapterType}</span>
                      <span>Candidate {trainingRun.modelCandidateId ?? "not created"}</span>
                      <span>Started {formatDateTime(trainingRun.startedAt)}</span>
                      <span>Last heartbeat {formatDateTime(trainingRun.lastHeartbeatAt)}</span>
                      <span>
                        Elapsed{" "}
                        {formatElapsedTime(
                          trainingRun.startedAt,
                          trainingRun.completedAt,
                          trainingRunClockTick
                        )}
                      </span>
                      <span>Precision {formatMetric(trainingRun.metricsSummary.precision)}</span>
                      <span>Recall {formatMetric(trainingRun.metricsSummary.recall)}</span>
                      {trainingRun.lastActivityMessage ? (
                        <p data-testid="model-training-activity">
                          Activity: {trainingRun.lastActivityMessage}
                        </p>
                      ) : null}
                      {isActiveTrainingRun(trainingRun) ? (
                        <p data-testid="model-training-active-status">
                          Training is active. Polling the Core API every 3 seconds for updates.
                        </p>
                      ) : null}
                      {trainingRun.isStale ? (
                        <p className="analysis-caveat failed" data-testid="model-training-stale">
                          No heartbeat within {trainingRun.staleAfterSeconds ?? "the configured"}{" "}
                          seconds. This run may be orphaned.
                        </p>
                      ) : null}
                      {trainingRun.status === "failed" ? (
                        <p className="analysis-caveat failed" data-testid="model-training-failure">
                          {trainingRun.failureCode ?? "training_failed"}:{" "}
                          {trainingRun.failureMessage ?? "Training failed before a model candidate was created."}
                        </p>
                      ) : null}
                      {trainingRun.cancelReason ? (
                        <p data-testid="model-training-cancel-reason">
                          Cancel reason: {trainingRun.cancelReason}
                        </p>
                      ) : null}
                      {trainingRun.abandonReason ? (
                        <p data-testid="model-training-abandon-reason">
                          Abandon reason: {trainingRun.abandonReason}
                        </p>
                      ) : null}
                      {trainingRun.latestLogExcerpt ? (
                        <pre className="training-log-excerpt" data-testid="model-training-log-excerpt">
                          {trainingRun.latestLogExcerpt}
                        </pre>
                      ) : null}
                      <div className="button-row">
                        {trainingRun.modelCandidateId ? (
                          <button
                            type="button"
                            disabled={Boolean(workingLabel)}
                            onClick={() =>
                              void useTrainingRunCandidateForCropYolo(trainingRun.modelCandidateId!)
                            }
                            data-testid="use-model-candidate-for-crop-yolo-button"
                          >
                            <Check size={18} />
                            Use candidate for crop YOLO
                          </button>
                        ) : null}
                        <button
                          type="button"
                          disabled={!isActiveTrainingRun(trainingRun) || Boolean(workingLabel)}
                          onClick={() => void cancelSelectedTrainingRun()}
                          data-testid="cancel-model-training-run-button"
                        >
                          <CircleAlert size={18} />
                          Cancel run
                        </button>
                        <button
                          type="button"
                          disabled={
                            !trainingRunCanBeAbandoned(trainingRun) || Boolean(workingLabel)
                          }
                          onClick={() => void abandonSelectedTrainingRun()}
                          data-testid="abandon-model-training-run-button"
                        >
                          <RotateCcw size={18} />
                          {trainingRun.status === "cancelling"
                            ? "Abandon cancelling run"
                            : "Abandon stale run"}
                        </button>
                        <button
                          type="button"
                          disabled={!trainingRunCanBeDeleted(trainingRun) || Boolean(workingLabel)}
                          onClick={() => void deleteSelectedTrainingRun()}
                          data-testid="delete-model-training-run-button"
                        >
                          <Trash2 size={18} />
                          Delete run
                        </button>
                      </div>
                      {modelCandidateSelectionMessage ? (
                        <p
                          className="review-state success"
                          role="status"
                          data-testid="model-candidate-selection-confirmation"
                        >
                          {modelCandidateSelectionMessage}
                        </p>
                      ) : null}
                      <p>Baseline only; not user-facing.</p>
                    </div>
                  ) : null}
                  <div
                    className="export-summary"
                    data-testid="benchmark-evaluation-panel"
                  >
                    <strong>Bee Detector benchmark evaluation</strong>
                    <span>Training Crop benchmark only</span>
                    {benchmarkReadiness ? (
                      <>
                        <span>Candidate {benchmarkReadiness.modelCandidateHumanReadableId}</span>
                        <span>Benchmark {benchmarkReadiness.benchmarkItemCount}</span>
                        <span>{benchmarkReadiness.evaluationAdapterType}</span>
                        <span>{benchmarkReadiness.databasePurpose}</span>
                        {benchmarkReadiness.activeModelJobId ? (
                          <span>
                            Active {benchmarkReadiness.activeModelJobType}{" "}
                            {benchmarkReadiness.activeModelJobId.slice(0, 8)}
                          </span>
                        ) : null}
                        {benchmarkReadiness.warnings.map((warning) => (
                          <span key={warning.code}>
                            {warning.severity}: {warning.code}
                          </span>
                        ))}
                        {!benchmarkReadiness.eligibleToStartEvaluation ? (
                          <p data-testid="benchmark-evaluation-blocker">
                            Evaluation cannot start until readiness blockers are resolved.
                          </p>
                        ) : null}
                      </>
                    ) : (
                      <span>Select a Model Candidate to check benchmark readiness.</span>
                    )}
                    <div className="button-row">
                      <button
                        type="button"
                        disabled={!selectedModelCandidateId || Boolean(workingLabel)}
                        onClick={() =>
                          selectedModelCandidateId
                            ? void refreshBenchmarkReadiness(selectedModelCandidateId)
                            : undefined
                        }
                        data-testid="benchmark-evaluation-readiness-button"
                      >
                        <RefreshCw size={18} />
                        Check benchmark
                      </button>
                      <button
                        type="button"
                        disabled={!canStartBenchmarkEvaluation}
                        onClick={() => void startSelectedBenchmarkEvaluation()}
                        data-testid="start-benchmark-evaluation-button"
                      >
                        <Play size={18} />
                        Run benchmark
                      </button>
                      <button
                        type="button"
                        disabled={
                          !benchmarkEvaluation ||
                          !isActiveBenchmarkEvaluation(benchmarkEvaluation) ||
                          Boolean(workingLabel)
                        }
                        onClick={() => void cancelSelectedBenchmarkEvaluation()}
                        data-testid="cancel-benchmark-evaluation-button"
                      >
                        <CircleAlert size={18} />
                        Cancel benchmark
                      </button>
                    </div>
                    {benchmarkEvaluation ? (
                      <div
                        className="training-run-row"
                        data-testid="benchmark-evaluation-summary"
                      >
                        <span>{benchmarkEvaluation.humanReadableId}</span>
                        <span>{benchmarkEvaluation.status}</span>
                        <span>Phase {benchmarkEvaluation.phase}</span>
                        <span>
                          Progress {formatProgressPercent(benchmarkEvaluation.progressPercent)}
                        </span>
                        <span>
                          Precision {formatMetric(benchmarkEvaluation.metricsSummary.precision)}
                        </span>
                        <span>
                          Recall {formatMetric(benchmarkEvaluation.metricsSummary.recall)}
                        </span>
                        <span>
                          Last heartbeat {formatDateTime(benchmarkEvaluation.lastHeartbeatAt)}
                        </span>
                        <span>
                          Elapsed{" "}
                          {formatElapsedTime(
                            benchmarkEvaluation.startedAt,
                            benchmarkEvaluation.completedAt,
                            trainingRunClockTick
                          )}
                        </span>
                        {benchmarkEvaluation.lastActivityMessage ? (
                          <p data-testid="benchmark-evaluation-activity">
                            Activity: {benchmarkEvaluation.lastActivityMessage}
                          </p>
                        ) : null}
                        {isActiveBenchmarkEvaluation(benchmarkEvaluation) ? (
                          <p data-testid="benchmark-evaluation-active-status">
                            Evaluation is active. Polling the Core API every 3 seconds for updates.
                          </p>
                        ) : null}
                        {benchmarkEvaluation.failureCode || benchmarkEvaluation.failureMessage ? (
                          <p
                            className="analysis-caveat failed"
                            data-testid="benchmark-evaluation-failure"
                          >
                            {benchmarkEvaluation.failureCode ?? "benchmark_evaluation_failed"}:{" "}
                            {benchmarkEvaluation.failureMessage ??
                              "Benchmark Evaluation failed before a report was created."}
                          </p>
                        ) : null}
                        {benchmarkEvaluation.latestLogExcerpt ? (
                          <pre
                            className="training-log-excerpt"
                            data-testid="benchmark-evaluation-log-excerpt"
                          >
                            {benchmarkEvaluation.latestLogExcerpt}
                          </pre>
                        ) : null}
                        <div className="button-row">
                          {benchmarkEvaluation.reportArtifactId ? (
                            <a
                              className="text-link"
                              href={toCoreApiContentUrl(
                                `/v1/model-training/artifacts/${benchmarkEvaluation.reportArtifactId}?workspace_id=${workspaceId}`
                              )}
                              target="_blank"
                              rel="noreferrer"
                              data-testid="benchmark-evaluation-report-link"
                            >
                              Report
                            </a>
                          ) : null}
                          {benchmarkEvaluation.rawPredictionArtifactId ? (
                            <a
                              className="text-link"
                              href={toCoreApiContentUrl(
                                `/v1/model-training/artifacts/${benchmarkEvaluation.rawPredictionArtifactId}?workspace_id=${workspaceId}`
                              )}
                              target="_blank"
                              rel="noreferrer"
                              data-testid="benchmark-evaluation-raw-predictions-link"
                            >
                              Raw predictions
                            </a>
                          ) : null}
                        </div>
                      </div>
                    ) : null}
                    {benchmarkEvaluationPollError ? (
                      <p
                        className="analysis-caveat failed"
                        data-testid="benchmark-evaluation-poll-error"
                      >
                        Could not refresh Benchmark Evaluations: {benchmarkEvaluationPollError}
                      </p>
                    ) : null}
                  </div>
                  {trainingRuns.length > 0 ? (
                    <div className="export-summary" data-testid="model-training-run-list">
                      <strong>Training runs</strong>
                      {trainingRunsLastCheckedAt ? (
                        <span data-testid="model-training-runs-last-checked">
                          Last checked {formatDateTime(trainingRunsLastCheckedAt)}
                        </span>
                      ) : null}
                      {hasActiveTrainingRun ? (
                        <span data-testid="model-training-runs-polling">Auto-refreshing</span>
                      ) : null}
                      {trainingRunPollError ? (
                        <p className="analysis-caveat failed" data-testid="model-training-poll-error">
                          Could not refresh Training Runs: {trainingRunPollError}
                        </p>
                      ) : null}
                      {trainingRuns.map((run) => (
                        <div
                          className="training-run-row"
                          data-testid="model-training-run-list-item"
                          key={run.trainingRunId}
                        >
                          <span>{run.humanReadableId}</span>
                          <span>{run.status}</span>
                          <span>Phase {run.phase}</span>
                          <span>Progress {formatProgressPercent(run.progressPercent)}</span>
                          <span>{run.adapterType}</span>
                          <span>Dataset {run.datasetVersionId.slice(0, 8)}</span>
                          <span>Candidate {run.modelCandidateId ?? "not created"}</span>
                          <span>Started {formatDateTime(run.startedAt)}</span>
                          <span>Heartbeat {formatDateTime(run.lastHeartbeatAt)}</span>
                          <span>
                            Elapsed{" "}
                            {formatElapsedTime(run.startedAt, run.completedAt, trainingRunClockTick)}
                          </span>
                          {run.lastActivityMessage ? <span>{run.lastActivityMessage}</span> : null}
                          {run.isStale ? <span>stale</span> : null}
                          {run.failureCode || run.failureMessage ? (
                            <span>
                              {run.failureCode ?? "training_failed"}:{" "}
                              {run.failureMessage ?? "No failure message recorded."}
                            </span>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  ) : null}
                  {benchmarkEvaluations.length > 0 ? (
                    <div className="export-summary" data-testid="benchmark-evaluation-list">
                      <strong>Benchmark evaluations</strong>
                      {benchmarkEvaluationsLastCheckedAt ? (
                        <span data-testid="benchmark-evaluations-last-checked">
                          Last checked {formatDateTime(benchmarkEvaluationsLastCheckedAt)}
                        </span>
                      ) : null}
                      {hasActiveBenchmarkEvaluation ? (
                        <span data-testid="benchmark-evaluations-polling">Auto-refreshing</span>
                      ) : null}
                      {benchmarkEvaluations.map((evaluation) => (
                        <div
                          className="training-run-row"
                          data-testid="benchmark-evaluation-list-item"
                          key={evaluation.benchmarkEvaluationId}
                        >
                          <span>{evaluation.humanReadableId}</span>
                          <span>{evaluation.status}</span>
                          <span>Phase {evaluation.phase}</span>
                          <span>Candidate {evaluation.modelCandidateHumanReadableId}</span>
                          <span>
                            Benchmark {String(evaluation.metricsSummary.benchmark_item_count ?? "n/a")}
                          </span>
                          <span>Precision {formatMetric(evaluation.metricsSummary.precision)}</span>
                          <span>Recall {formatMetric(evaluation.metricsSummary.recall)}</span>
                          {evaluation.lastActivityMessage ? (
                            <span>{evaluation.lastActivityMessage}</span>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
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

function ReviewWorkPage({
  devUserId,
  workspaceId,
  onError
}: {
  devUserId: string;
  workspaceId: string;
  onError: (error: ApiError) => void;
}) {
  const [availableItems, setAvailableItems] = useState<ReviewQueueItem[]>([]);
  const [historyItems, setHistoryItems] = useState<ReviewQueueItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<ReviewQueueItem | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [outcome, setOutcome] = useState<ReviewQueueOutcomeValue>("approved");
  const [notes, setNotes] = useState("");
  const [workingLabel, setWorkingLabel] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    void refreshReviewQueues();
  }, [devUserId]);

  useEffect(() => {
    if (!selectedItem) {
      setImageUrl((current) => {
        if (current) URL.revokeObjectURL(current);
        return null;
      });
      return;
    }
    let cancelled = false;
    fetchReviewQueueImageObjectUrl({
      devUserId,
      imageViewUrl: selectedItem.evidenceSnapshot.imageViewUrl
    })
      .then((nextImageUrl) => {
        if (cancelled) {
          URL.revokeObjectURL(nextImageUrl);
          return;
        }
        setImageUrl((current) => {
          if (current) URL.revokeObjectURL(current);
          return nextImageUrl;
        });
      })
      .catch((error) => onError(toApiError(error)));
    return () => {
      cancelled = true;
    };
  }, [devUserId, onError, selectedItem]);

  async function runReviewAction(label: string, action: () => Promise<void>) {
    setWorkingLabel(label);
    setStatusMessage(null);
    try {
      await action();
    } catch (error) {
      onError(toApiError(error));
    } finally {
      setWorkingLabel(null);
    }
  }

  async function refreshReviewQueues() {
    await runReviewAction("Refreshing Review Work", async () => {
      const [work, history] = await Promise.all([
        fetchReviewWork({ devUserId }),
        fetchReviewHistory({ devUserId })
      ]);
      setAvailableItems(work.reviewQueueItems);
      setHistoryItems(history.reviewQueueItems);
      setSelectedItem((current) =>
        current && work.reviewQueueItems.some((item) => item.reviewQueueItemId === current.reviewQueueItemId)
          ? current
          : (work.reviewQueueItems[0] ?? null)
      );
    });
  }

  async function openReviewItem(reviewQueueItemId: string) {
    await runReviewAction("Opening Review Queue Item", async () => {
      const item = await fetchReviewWorkItem({ devUserId, reviewQueueItemId });
      setSelectedItem(item);
      setNotes("");
      setOutcome("approved");
    });
  }

  async function completeSelectedReview() {
    if (!selectedItem) {
      return;
    }
    await runReviewAction("Completing Review Queue Item", async () => {
      const completed = await completeReviewWorkItem({
        devUserId,
        reviewQueueItemId: selectedItem.reviewQueueItemId,
        reviewOutcome: outcome,
        reviewNotes: notes
      });
      setStatusMessage(`${completed.humanReadableId} completed as ${completed.completedOutcome}.`);
      setSelectedItem(null);
      setNotes("");
      const [work, history] = await Promise.all([
        fetchReviewWork({ devUserId }),
        fetchReviewHistory({ devUserId })
      ]);
      setAvailableItems(work.reviewQueueItems);
      setHistoryItems(history.reviewQueueItems);
    });
  }

  const notesRequired = outcome === "changes_requested" || outcome === "not_determined";

  return (
    <section className="analysis-panel review-work-panel" data-testid="review-work-page">
      <div className="analysis-header">
        <PanelHeading icon={<ShieldCheck size={20} />} title="Review Work" />
        <span className="analysis-status status-queued">{availableItems.length} available</span>
      </div>
      <div className="button-row">
        <button
          type="button"
          disabled={Boolean(workingLabel)}
          onClick={() => void refreshReviewQueues()}
          data-testid="refresh-review-work-button"
        >
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      {availableItems.length === 0 ? (
        <p className="analysis-caveat" data-testid="review-work-empty-state">
          No review work is available for this Reviewer.
        </p>
      ) : (
        <ul className="crop-list" data-testid="review-work-list">
          {availableItems.map((item) => (
            <li key={item.reviewQueueItemId}>
              <button
                type="button"
                className={
                  item.reviewQueueItemId === selectedItem?.reviewQueueItemId ? "selected-row" : ""
                }
                onClick={() => void openReviewItem(item.reviewQueueItemId)}
                data-testid="review-work-list-item"
              >
                {item.humanReadableId} / {item.evidenceSnapshot.safeSourceLabel} /{" "}
                {item.evidenceSnapshot.reviewedEllipseCount} ellipses
              </button>
            </li>
          ))}
        </ul>
      )}

      {selectedItem && imageUrl ? (
        <section className="crop-editor review-work-evidence" data-testid="review-work-evidence">
          <div className="review-state" data-testid="review-work-safe-metadata">
            {selectedItem.humanReadableId} / {selectedItem.evidenceSnapshot.safeSourceLabel} /{" "}
            {selectedItem.evidenceSnapshot.cropWidth} x {selectedItem.evidenceSnapshot.cropHeight} /{" "}
            {selectedItem.evidenceSnapshot.completeVisibleBeeCount} complete /{" "}
            {selectedItem.evidenceSnapshot.partialVisibleBeeCount} partial
          </div>
          {selectedItem.requestNotes ? (
            <p className="analysis-caveat" data-testid="review-work-request-notes">
              {selectedItem.requestNotes}
            </p>
          ) : null}
          <div
            className="review-crop-surface"
            style={{
              aspectRatio: `${selectedItem.evidenceSnapshot.cropWidth} / ${selectedItem.evidenceSnapshot.cropHeight}`
            }}
            data-testid="review-work-crop-surface"
          >
            <img
              src={imageUrl}
              alt={selectedItem.evidenceSnapshot.safeSourceLabel}
              style={reviewQueueImageStyle(selectedItem)}
              draggable={false}
            />
            {selectedItem.evidenceSnapshot.reviewedEllipses.map((ellipse) => (
              <span
                key={ellipse.annotationId}
                className={`bee-ellipse review-evidence ${
                  ellipse.annotationType === "partial_visible_bee" ? "partial" : "complete"
                }`}
                style={reviewQueueEllipseStyle(selectedItem, ellipse)}
                data-testid="review-work-ellipse"
                aria-label={ellipse.annotationType}
              >
                <span className="ellipse-head-arrow" />
              </span>
            ))}
          </div>
          <form
            className="review-panel"
            data-testid="review-work-outcome-form"
            onSubmit={(event) => {
              event.preventDefault();
              void completeSelectedReview();
            }}
          >
            <label>
              <span>Outcome</span>
              <select
                value={outcome}
                onChange={(event) => setOutcome(event.target.value as ReviewQueueOutcomeValue)}
                data-testid="review-work-outcome-select"
              >
                <option value="approved">Approved</option>
                <option value="changes_requested">Changes requested</option>
                <option value="not_determined">Not determined</option>
              </select>
            </label>
            <label>
              <span>{notesRequired ? "Notes required" : "Notes"}</span>
              <textarea
                value={notes}
                maxLength={500}
                onChange={(event) => setNotes(event.target.value)}
                required={notesRequired}
                data-testid="review-work-notes-input"
              />
            </label>
            <button
              type="submit"
              disabled={Boolean(workingLabel) || (notesRequired && notes.trim().length === 0)}
              data-testid="complete-review-work-button"
            >
              <Check size={18} />
              Complete review
            </button>
          </form>
        </section>
      ) : null}

      {statusMessage ? (
        <p className="review-state success" role="status" data-testid="review-work-status-message">
          {statusMessage}
        </p>
      ) : null}
      {workingLabel ? (
        <div className="outcome working" role="status">
          <LoaderCircle className="spin" size={20} />
          <span>{workingLabel}</span>
        </div>
      ) : null}

      <section className="metadata-panel" data-testid="review-history-panel">
        <div>
          <strong>Review History</strong>
          <p>Completed queue reviews for this Reviewer.</p>
        </div>
        {historyItems.length === 0 ? (
          <span>No completed reviews</span>
        ) : (
          historyItems.map((item) => (
            <span key={item.reviewQueueItemId} className="record-badge ready">
              {item.humanReadableId} / {item.completedOutcome ?? item.status}
            </span>
          ))
        )}
      </section>
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

function prelabelerProviderLabel(_provider: "deterministic"): string {
  return "Deterministic";
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
