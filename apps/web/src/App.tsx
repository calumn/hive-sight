import { Activity, Database, Image, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchCoreHealth, type HealthResponse } from "./coreApiClient";

type HealthState =
  | { kind: "loading" }
  | { kind: "ready"; health: HealthResponse }
  | { kind: "error"; message: string };

export function App() {
  const [healthState, setHealthState] = useState<HealthState>({ kind: "loading" });

  useEffect(() => {
    fetchCoreHealth()
      .then((health) => setHealthState({ kind: "ready", health }))
      .catch((error: Error) => setHealthState({ kind: "error", message: error.message }));
  }, []);

  return (
    <main className="app-shell">
      <section className="topbar" aria-label="Application status">
        <div>
          <p className="eyebrow">HiveSight</p>
          <h1>Inspection workspace</h1>
        </div>
        <StatusPill state={healthState} />
      </section>

      <section className="workflow-grid" aria-label="Core workflow">
        <WorkflowItem
          icon={<ShieldCheck size={22} aria-hidden="true" />}
          title="Protected Core API"
          body="The web app talks to one product-facing API boundary for workspace and inspection workflows."
        />
        <WorkflowItem
          icon={<Image size={22} aria-hidden="true" />}
          title="Inspection Photos"
          body="Photo upload and tagged-image viewing will move through short-lived object-scoped URLs."
        />
        <WorkflowItem
          icon={<Activity size={22} aria-hidden="true" />}
          title="Async Analysis"
          body="Image analysis runs behind a private service boundary and reports status back to the Core API."
        />
        <WorkflowItem
          icon={<Database size={22} aria-hidden="true" />}
          title="Model Traceability"
          body="Each analysis run records the model version that produced its visible Varroa evidence."
        />
      </section>
    </main>
  );
}

function StatusPill({ state }: { state: HealthState }) {
  if (state.kind === "loading") {
    return <span className="status-pill status-loading">Checking Core API</span>;
  }

  if (state.kind === "error") {
    return <span className="status-pill status-error">Core API offline</span>;
  }

  return <span className="status-pill status-ready">{state.health.service} online</span>;
}

function WorkflowItem({
  icon,
  title,
  body
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
}) {
  return (
    <article className="workflow-item">
      <div className="workflow-icon">{icon}</div>
      <div>
        <h2>{title}</h2>
        <p>{body}</p>
      </div>
    </article>
  );
}

