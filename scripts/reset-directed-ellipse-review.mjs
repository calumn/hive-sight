#!/usr/bin/env node

const coreApiUrl = process.env.HIVESIGHT_CORE_API_URL ?? "http://127.0.0.1:8000";
const devUserId =
  process.env.HIVESIGHT_DEV_USER_ID ?? "00000000-0000-0000-0000-000000000101";
const headers = { "x-hivesight-dev-user-id": devUserId };

async function request(path, options = {}) {
  const response = await fetch(`${coreApiUrl}${path}`, {
    ...options,
    headers: {
      ...headers,
      ...(options.headers ?? {})
    }
  });
  const contentType = response.headers.get("content-type") ?? "";
  const body = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const message = typeof body === "string" ? body : body.detail?.message ?? JSON.stringify(body);
    throw new Error(`${response.status} ${message}`);
  }
  return body;
}

try {
  const session = await request("/v1/dev/session");
  const result = await request("/v1/dev/directed-ellipse-orientation-cleanup", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      workspace_id: session.workspace_id,
      reason: "Slice 0015.35 directed bee ellipse orientation reset.",
      confirm_remove_dataset_and_model_evidence: true
    })
  });

  console.log("Directed ellipse review reset complete.");
  console.log(`Dataset Items removed: ${result.dataset_items_removed}`);
  console.log(`Dataset Versions removed: ${result.dataset_versions_removed}`);
  console.log(`Training Runs removed: ${result.training_runs_removed}`);
  console.log(`Model Candidates removed: ${result.model_candidates_removed}`);
  console.log(`Artifacts removed: ${result.artifacts_removed}`);
  console.log(`Artifact paths removed: ${result.artifact_paths_removed}`);
  console.log(`Training Crops reopened: ${result.training_crops_reopened}`);
  console.log(`Bee ellipses preserved: ${result.training_crop_ellipses_preserved}`);
  console.log(`Inspection Photos preserved: ${result.inspection_photos_preserved}`);
} catch (error) {
  console.error(`Directed ellipse review reset failed: ${error.message}`);
  process.exitCode = 1;
}
