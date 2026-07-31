const coreApiUrl = process.env.CORE_API_URL ?? "http://127.0.0.1:8000";
const devUserId = process.env.HIVESIGHT_DEV_USER_ID ?? "00000000-0000-0000-0000-000000000101";

try {
  const session = await requestJson("/v1/dev/session", { headers: devHeaders() });
  const workspaceId = session.workspace_id;
  await requestJson(
    "/v1/workspace-data-use-agreements/acceptances",
    {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({ workspace_id: workspaceId, terms_version: "2026-07-31" })
    },
    [200]
  );
  const readiness = await requestJson(
    `/v1/model-training/readiness?workspace_id=${encodeURIComponent(workspaceId)}`,
    { headers: devHeaders() }
  );
  process.stdout.write(
    `Readiness: ${readiness.adapter_type} / ${readiness.database_purpose}; training ${readiness.dataset_item_counts.training ?? 0}, validation ${readiness.dataset_item_counts.validation ?? 0}\n`
  );
  const datasetVersion = await requestJson(
    "/v1/model-training/dataset-versions",
    {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({ workspace_id: workspaceId })
    },
    [201]
  );
  process.stdout.write(`Dataset Version: ${datasetVersion.human_readable_id}\n`);
  const trainingRun = await requestJson(
    "/v1/model-training/training-runs",
    {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({
        workspace_id: workspaceId,
        dataset_version_id: datasetVersion.dataset_version_id,
        acknowledge_high_severity_warnings: true
      })
    },
    [202]
  );
  process.stdout.write(
    `Training Run: ${trainingRun.human_readable_id} ${trainingRun.status}; candidate ${trainingRun.model_candidate_id ?? "not created"}\n`
  );
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.stderr.write("Start the stack first with: pnpm dev:all:yolo-training\n");
  process.exitCode = 1;
}

function devHeaders() {
  return { "x-hivesight-dev-user-id": devUserId };
}

function jsonHeaders() {
  return { ...devHeaders(), "content-type": "application/json" };
}

async function requestJson(path, init = {}, expectedStatuses = [200]) {
  const response = await fetch(`${coreApiUrl}${path}`, init);
  if (!expectedStatuses.includes(response.status)) {
    let detail = "";
    try {
      detail = JSON.stringify(await response.json());
    } catch {
      detail = await response.text();
    }
    throw new Error(`Core API returned ${response.status} for ${path}: ${detail}`);
  }
  return response.json();
}
