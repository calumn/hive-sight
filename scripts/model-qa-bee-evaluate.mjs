const coreApiUrl = process.env.CORE_API_URL ?? "http://127.0.0.1:8000";
const devUserId = process.env.HIVESIGHT_DEV_USER_ID ?? "00000000-0000-0000-0000-000000000101";
const timeoutMs = Number(process.env.HIVESIGHT_MODEL_QA_TIMEOUT_MS ?? "600000");
const pollMs = Number(process.env.HIVESIGHT_MODEL_QA_POLL_MS ?? "3000");

let startedEvaluationId = null;
let workspaceId = null;

try {
  const session = await requestJson("/v1/dev/session", { headers: devHeaders() });
  workspaceId = session.workspace_id;
  await requestJson(
    "/v1/workspace-data-use-agreements/acceptances",
    {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({ workspace_id: workspaceId, terms_version: "2026-07-31" })
    },
    [200]
  );

  const candidate = await latestRealModelCandidate(workspaceId);
  const readiness = await requestJson(
    `/v1/model-training/model-candidates/${candidate.model_candidate_id}/benchmark-readiness?workspace_id=${encodeURIComponent(
      workspaceId
    )}`,
    { headers: devHeaders() }
  );
  if (readiness.benchmark_item_count < 1) {
    throw new Error("At least one protected benchmark Dataset Item is required before QA evaluation.");
  }
  const hasHighWarnings = readiness.warnings.some((warning) => warning.severity === "high");
  const evaluation = await requestJson(
    "/v1/model-training/benchmark-evaluations",
    {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({
        workspace_id: workspaceId,
        model_candidate_id: candidate.model_candidate_id,
        confidence_threshold: 0.1,
        acknowledge_high_severity_warnings: hasHighWarnings
      })
    },
    [202]
  );
  startedEvaluationId = evaluation.benchmark_evaluation_id;
  process.stdout.write(`Started Benchmark Evaluation ${evaluation.human_readable_id}\n`);
  process.stdout.write(`Model Candidate ${candidate.human_readable_id}\n`);

  const completed = await waitForEvaluation(workspaceId, startedEvaluationId);
  process.stdout.write(`Status: ${completed.status}\n`);
  process.stdout.write(`Benchmark Evaluation id: ${completed.benchmark_evaluation_id}\n`);
  process.stdout.write(`Report artifact id: ${completed.report_artifact_id ?? "not created"}\n`);
  process.stdout.write(
    `Raw predictions artifact id: ${completed.raw_prediction_artifact_id ?? "not created"}\n`
  );
  process.stdout.write(`Precision: ${formatMetric(completed.metrics_summary.precision)}\n`);
  process.stdout.write(`Recall: ${formatMetric(completed.metrics_summary.recall)}\n`);
  if (completed.status !== "completed") {
    process.exitCode = 1;
  }
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  if (startedEvaluationId && workspaceId) {
    try {
      await requestJson(
        `/v1/model-training/benchmark-evaluations/${startedEvaluationId}/cancel`,
        {
          method: "POST",
          headers: jsonHeaders(),
          body: JSON.stringify({
            workspace_id: workspaceId,
            reason: "Cancelled by model:qa:bee:evaluate after failure or timeout."
          })
        },
        [200, 409]
      );
    } catch (cancelError) {
      process.stderr.write(`Could not cancel Benchmark Evaluation: ${cancelError.message}\n`);
    }
  }
  process.stderr.write(
    "Start the real model stack with: pnpm dev:all:yolo, then make sure at least one real completed Model Candidate and protected benchmark Dataset Item exist.\n"
  );
  process.exitCode = 1;
}

async function latestRealModelCandidate(workspaceId) {
  const listing = await requestJson(
    `/v1/model-training/model-candidates?workspace_id=${encodeURIComponent(workspaceId)}`,
    { headers: devHeaders() }
  );
  const candidate = listing.model_candidates.find(
    (item) =>
      item.status === "created" &&
      item.model_purpose === "bee_detector" &&
      item.adapter_type === "ultralytics_yolo_obb"
  );
  if (!candidate) {
    throw new Error("No completed real Bee Detector Model Candidate found in this workspace.");
  }
  return candidate;
}

async function waitForEvaluation(workspaceId, evaluationId) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    const evaluation = await requestJson(
      `/v1/model-training/benchmark-evaluations/${evaluationId}?workspace_id=${encodeURIComponent(
        workspaceId
      )}`,
      { headers: devHeaders() }
    );
    process.stdout.write(
      `${evaluation.human_readable_id} ${evaluation.status} ${evaluation.phase} ${formatProgress(
        evaluation.progress_percent
      )}: ${evaluation.last_activity_message ?? "no activity"}\n`
    );
    if (["completed", "failed", "cancelled"].includes(evaluation.status)) {
      return evaluation;
    }
    await sleep(pollMs);
  }
  await requestJson(
    `/v1/model-training/benchmark-evaluations/${evaluationId}/cancel`,
    {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({
        workspace_id: workspaceId,
        reason: `Timed out after ${Math.round(timeoutMs / 1000)} seconds.`
      })
    },
    [200]
  );
  throw new Error(`Benchmark Evaluation timed out after ${Math.round(timeoutMs / 1000)} seconds.`);
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

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function formatProgress(value) {
  return value === null || value === undefined ? "progress n/a" : `progress ${Math.round(value)}%`;
}

function formatMetric(value) {
  return typeof value === "number" ? value.toFixed(3) : "n/a";
}
