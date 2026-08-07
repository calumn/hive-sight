const coreApiUrl = process.env.CORE_API_URL ?? "http://127.0.0.1:8000";
const devUserId = process.env.HIVESIGHT_DEV_USER_ID ?? "00000000-0000-0000-0000-000000000101";

try {
  const readiness = await requestJson("/v1/model-runtime/varroa-detector/readiness", {
    headers: devHeaders()
  });
  process.stdout.write(`Adapter: ${readiness.adapter_type}\n`);
  process.stdout.write(`Adapter version: ${readiness.adapter_version}\n`);
  process.stdout.write(`Model reference: ${readiness.model_reference}\n`);
  process.stdout.write(`Available: ${readiness.available ? "yes" : "no"}\n`);
  if (!readiness.available) {
    throw new Error(`Varroa Detector adapter unavailable: ${readiness.unavailable_reason}`);
  }

  const session = await requestJson("/v1/dev/session", { headers: devHeaders() });
  const workspaceId = session.workspace_id;
  await requestJson(
    "/v1/workspace-data-use-agreements/acceptances",
    {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({ workspace_id: workspaceId, terms_version: "2026-08-07" })
    },
    [200]
  );

  const fixture = await firstEligibleVarroaFixture(workspaceId);
  if (!fixture) {
    process.stdout.write(
      "Single-crop detector smoke test: skipped; no completed eligible Head-Up crop fixture found.\n"
    );
    process.stdout.write(
      "Photo Analysis path: skipped; no completed eligible photo fixture found.\n"
    );
    process.exit(0);
  }

  const preview = await requestJson(
    `/v1/training-crops/${fixture.trainingCropId}/varroa-review-candidates/${fixture.beeAnnotationId}/detector-preview`,
    {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({ workspace_id: workspaceId })
    }
  );
  process.stdout.write(`Single-crop detector smoke test: ${preview.status}\n`);
  process.stdout.write(`Preview detections: ${preview.detection_count}\n`);
  if (preview.status !== "completed") {
    throw new Error(`Detector preview failed: ${preview.failure_code ?? preview.not_assessed_reason}`);
  }

  const analysis = await requestJson(
    `/v1/inspection-photos/${fixture.inspectionPhotoId}/varroa-photo-analyses`,
    {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({ workspace_id: workspaceId })
    },
    [201]
  );
  process.stdout.write(`Photo Analysis path: ${analysis.status}\n`);
  process.stdout.write(`Analysed bees: ${analysis.analysed_bees}\n`);
  process.stdout.write(`Failed bees: ${analysis.failed_bees}\n`);
  process.stdout.write(`Mites found: ${analysis.mites_found}\n`);
  if (analysis.status === "failed") {
    process.exitCode = 1;
  }
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.stderr.write(
    "Start the Core API with the desired Varroa adapter configuration, then ensure at least one completed eligible Varroa review crop exists for full QA.\n"
  );
  process.exitCode = 1;
}

async function firstEligibleVarroaFixture(workspaceId) {
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
          for (const crop of crops.training_crops) {
            if (crop.review_status !== "review_complete") continue;
            const candidates = await requestJson(
              `/v1/training-crops/${crop.training_crop_id}/varroa-review-candidates?workspace_id=${encodeURIComponent(
                workspaceId
              )}`,
              { headers: devHeaders() }
            );
            const candidate = candidates.candidates.find((item) => item.eligibility === "eligible");
            if (candidate) {
              return {
                inspectionPhotoId: photo.inspection_photo_id,
                trainingCropId: crop.training_crop_id,
                beeAnnotationId: candidate.bee_annotation.annotation_id
              };
            }
          }
        }
      }
    }
  }
  return null;
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
