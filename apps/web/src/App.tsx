import {
  Check,
  CircleAlert,
  CloudUpload,
  FileImage,
  LoaderCircle,
  Plus,
  ShieldCheck
} from "lucide-react";
import { type FormEvent, type ReactNode, useEffect, useMemo, useState } from "react";
import {
  acceptWorkspaceDataUseAgreement,
  createApiary,
  createHive,
  createInspection,
  fetchCoreHealth,
  fetchDevSession,
  uploadInspectionPhoto,
  type Apiary,
  type ApiError,
  type DevSession,
  type HealthResponse,
  type Hive,
  type Inspection,
  type PhotoIntake
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
  const [apiaryName, setApiaryName] = useState("Home apiary");
  const [hiveName, setHiveName] = useState("Hive A");
  const [inspectionDate, setInspectionDate] = useState(new Date().toISOString().slice(0, 10));
  const [file, setFile] = useState<File | null>(null);

  useEffect(() => {
    Promise.all([fetchCoreHealth(), fetchDevSession(devUserId)])
      .then(([health, session]) => setLoadState({ kind: "ready", health, session }))
      .catch((error: Error) => setLoadState({ kind: "error", message: error.message }));
  }, []);

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
      setActionState({ kind: "accepted", intake });
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
                  />
                </label>
                <button type="submit" disabled={actionState.kind === "working"}>
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
                  />
                </label>
                <button type="submit" disabled={!canCreateHive || actionState.kind === "working"}>
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
                  />
                </label>
                <button
                  type="submit"
                  disabled={!canCreateInspection || actionState.kind === "working"}
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
                />
              </label>
              <button
                className="primary-action"
                type="submit"
                disabled={!canUpload || actionState.kind === "working"}
              >
                <CloudUpload size={18} />
                Upload photo
              </button>
            </form>

            <Outcome state={actionState} />
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

function Outcome({ state }: { state: ActionState }) {
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
          <p>Analysis {state.intake.analysisRun.status}</p>
        </div>
      </div>
    );
  }

  return null;
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
