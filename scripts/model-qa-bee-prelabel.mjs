const coreApiUrl = process.env.CORE_API_URL ?? "http://127.0.0.1:8000";
const devUserId = process.env.HIVESIGHT_DEV_USER_ID ?? "00000000-0000-0000-0000-000000000101";
const threshold = Number(process.env.HIVESIGHT_PRELABEL_CONFIDENCE_THRESHOLD ?? "0.1");

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

  const candidate = await latestModelCandidate(workspaceId);
  const crop = await firstEditableTrainingCrop(workspaceId);
  const result = await requestJson(
    `/v1/training-crops/${crop.training_crop_id}/candidate-bee-annotations`,
    {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({
        workspace_id: workspaceId,
        model_candidate_id: candidate.model_candidate_id,
        confidence_threshold: threshold,
        max_suggestions: 50
      })
    }
  );

  process.stdout.write(`Model Candidate: ${candidate.human_readable_id}\n`);
  process.stdout.write(`Training Crop: ${crop.training_crop_id}\n`);
  process.stdout.write(`Threshold: ${Math.round(result.threshold * 100)}%\n`);
  process.stdout.write(`Suggestions: ${result.suggestions.length}\n`);
  for (const suggestion of result.suggestions.slice(0, 10)) {
    process.stdout.write(
      [
        `- ${suggestion.proposal_id}`,
        `confidence ${Math.round(suggestion.confidence * 100)}%`,
        `center ${Math.round(suggestion.center_x)},${Math.round(suggestion.center_y)}`,
        `radii ${Math.round(suggestion.radius_x)}x${Math.round(suggestion.radius_y)}`,
        `rotation ${Math.round(suggestion.rotation_degrees)}`
      ].join("; ") + "\n"
    );
  }
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.stderr.write(
    "Start the real model stack with: pnpm dev:all:yolo-training, then make sure at least one completed Model Candidate and one editable Training Crop exist.\n"
  );
  process.exitCode = 1;
}

async function latestModelCandidate(workspaceId) {
  const listing = await requestJson(
    `/v1/model-training/model-candidates?workspace_id=${encodeURIComponent(workspaceId)}`,
    { headers: devHeaders() }
  );
  const candidate = listing.model_candidates.find(
    (item) => item.status === "created" && item.model_purpose === "bee_detector"
  );
  if (!candidate) {
    throw new Error("No completed Bee Detector Model Candidate found in this workspace.");
  }
  return candidate;
}

async function firstEditableTrainingCrop(workspaceId) {
  const apiaries = await requestJson(
    `/v1/apiaries?workspace_id=${encodeURIComponent(workspaceId)}`,
    { headers: devHeaders() }
  );
  for (const apiary of apiaries.apiaries) {
    const hives = await requestJson(
      `/v1/apiaries/${apiary.apiary_id}/hives?workspace_id=${encodeURIComponent(workspaceId)}`,
      { headers: devHeaders() }
    );
    for (const hive of hives.hives) {
      const inspections = await requestJson(
        `/v1/hives/${hive.hive_id}/inspections?workspace_id=${encodeURIComponent(
          workspaceId
        )}&intent=training_data_collection`,
        { headers: devHeaders() }
      );
      for (const inspection of inspections.inspections) {
        const photos = await requestJson(
          `/v1/inspections/${inspection.inspection_id}/photos?workspace_id=${encodeURIComponent(
            workspaceId
          )}`,
          { headers: devHeaders() }
        );
        for (const photo of photos.inspection_photos) {
          const crops = await requestJson(
            `/v1/inspection-photos/${photo.inspection_photo_id}/training-crops?workspace_id=${encodeURIComponent(
              workspaceId
            )}`,
            { headers: devHeaders() }
          );
          const crop = crops.training_crops.find((item) => item.review_status === "review_pending");
          if (crop) {
            return crop;
          }
        }
      }
    }
  }
  throw new Error("No editable Training Crop found in this workspace.");
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
