import { expect, test, type APIRequestContext, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));
const coreApiUrl =
  process.env.HIVESIGHT_PLAYWRIGHT_CORE_API_URL ??
  process.env.VITE_CORE_API_URL ??
  "http://127.0.0.1:8000";
const devUserId = "00000000-0000-0000-0000-000000000101";

test("Dataset Curator browses Bee Annotation Repository across inspections", async ({ page }) => {
  const setup = await setupRepositoryDataset(page);

  await page.goto("/");
  await expect(page.getByText("core-api online")).toBeVisible();
  await page.getByTestId("bee-annotation-repository-page-button").click();

  await expect(page.getByTestId("bee-annotation-repository-page")).toBeVisible();
  await expect(page.getByTestId("repository-summary")).toContainText("Training");
  await expect(page.getByTestId("repository-summary")).toContainText("Validation");
  await expect(page.getByTestId("repository-diversity-chips")).toContainText("inspections");
  await expect(page.getByTestId("repository-diversity-chips")).toContainText("Latest HS-DV-");
  await page.getByTestId("repository-search-input").fill(setup.runKey);
  await expect(page.getByTestId("repository-item-card")).toHaveCount(2);
  await expect(page.getByTestId("repository-item-detail")).toContainText("Complete bees");
  await expect(page.getByTestId("repository-crop-preview")).toBeVisible();
  await expectLoadedImage(page, "repository-thumbnail-image");
  await expectLoadedImage(page, "repository-crop-preview-image");
  await expect(page.getByTestId("repository-crop-ellipse")).toHaveCount(1);

  await page.getByTestId("repository-role-filter").selectOption("validation");
  await expect(page.getByTestId("repository-item-card")).toHaveCount(1);
  await expect(page.getByTestId("repository-item-list")).toContainText("validation-frame");
  await expect(page.getByTestId("repository-version-memberships")).toContainText("validation");

  await page.getByTestId("repository-search-input").fill(`${setup.runKey}-missing`);
  await expect(page.getByTestId("repository-item-card")).toHaveCount(0);
});

async function setupRepositoryDataset(page: Page): Promise<{ workspaceId: string; runKey: string }> {
  const runKey = `repo-${Date.now()}`;
  const session = await page.request.get(`${coreApiUrl}/v1/dev/session`, {
    headers: devHeaders()
  });
  expect(session.ok()).toBeTruthy();
  const workspaceId = (await session.json()).workspace_id as string;
  await page.request.post(`${coreApiUrl}/v1/workspace-data-use-agreements/acceptances`, {
    data: { workspace_id: workspaceId, terms_version: "2026-08-01" },
    headers: jsonHeaders()
  });
  await createReviewedItem(page.request, workspaceId, runKey, "training", "training-frame.png", "2026-08-01", 10);
  await createReviewedItem(page.request, workspaceId, runKey, "validation", "validation-frame.png", "2026-08-02", 40);
  const version = await page.request.post(`${coreApiUrl}/v1/model-training/dataset-versions`, {
    data: { workspace_id: workspaceId },
    headers: jsonHeaders()
  });
  expect(version.status()).toBe(201);
  return { workspaceId, runKey };
}

async function createReviewedItem(
  request: APIRequestContext,
  workspaceId: string,
  runKey: string,
  datasetRole: "training" | "validation",
  filename: string,
  inspectionDate: string,
  cropX: number
) {
  const suffix = `${runKey}-${datasetRole}`;
  const apiary = await request.post(`${coreApiUrl}/v1/apiaries`, {
    data: { workspace_id: workspaceId, name: `Repository ${suffix}` },
    headers: jsonHeaders()
  });
  const apiaryId = (await apiary.json()).apiary_id as string;
  const hive = await request.post(`${coreApiUrl}/v1/hives`, {
    data: { apiary_id: apiaryId, name: `Hive ${suffix}` },
    headers: jsonHeaders()
  });
  const hiveId = (await hive.json()).hive_id as string;
  await request.put(`${coreApiUrl}/v1/hives/${hiveId}/configuration`, {
    data: { workspace_id: workspaceId, frame_standard_id: "british_national_deep_brood" },
    headers: jsonHeaders()
  });
  const inspection = await request.post(`${coreApiUrl}/v1/inspections`, {
    data: {
      hive_id: hiveId,
      inspection_date: inspectionDate,
      intent: "training_data_collection"
    },
    headers: jsonHeaders()
  });
  const inspectionId = (await inspection.json()).inspection_id as string;
  const intake = await request.post(
    `${coreApiUrl}/v1/inspection-photos/intake?workspace_id=${workspaceId}&inspection_id=${inspectionId}`,
    {
      data: readFileSync(fixtureImagePath),
      headers: {
        ...devHeaders(),
        "content-type": "image/png",
        "x-hivesight-filename": filename
      }
    }
  );
  const inspectionPhotoId = (await intake.json()).inspection_photo.inspection_photo_id as string;
  const crop = await request.post(`${coreApiUrl}/v1/training-crops`, {
    data: {
      workspace_id: workspaceId,
      inspection_photo_id: inspectionPhotoId,
      crop_x: cropX,
      crop_y: 20,
      crop_width: 90,
      crop_height: 80,
      source_image_width_px: 160,
      source_image_height_px: 120
    },
    headers: jsonHeaders()
  });
  const trainingCropId = (await crop.json()).training_crop_id as string;
  await request.post(`${coreApiUrl}/v1/training-crops/${trainingCropId}/bee-ellipses`, {
    data: {
      workspace_id: workspaceId,
      annotation_type: "complete_visible_bee",
      center_x: cropX + 45,
      center_y: 60,
      radius_x: 16,
      radius_y: 8,
      rotation_degrees: 12
    },
    headers: jsonHeaders()
  });
  await request.patch(`${coreApiUrl}/v1/training-crops/${trainingCropId}`, {
    data: {
      workspace_id: workspaceId,
      visible_bee_status: "has_visible_bees",
      review_status: "review_complete"
    },
    headers: jsonHeaders()
  });
  await request.post(`${coreApiUrl}/v1/training-crops/${trainingCropId}/dataset-item`, {
    data: {
      workspace_id: workspaceId,
      dataset_role: datasetRole,
      source_group_key: `${runKey}-${datasetRole}-${filename}`,
      assignment_note: `${runKey}: accepted as ${datasetRole} repository evidence.`
    },
    headers: jsonHeaders()
  });
}

function devHeaders() {
  return { "x-hivesight-dev-user-id": devUserId };
}

function jsonHeaders() {
  return { ...devHeaders(), "content-type": "application/json" };
}

async function expectLoadedImage(page: Page, testId: string) {
  const image = page.getByTestId(testId).first();
  await expect(image).toBeVisible();
  await expect
    .poll(async () =>
      image.evaluate((element) => {
        const img = element as HTMLImageElement;
        return img.complete && img.naturalWidth > 0 && img.naturalHeight > 0;
      })
    )
    .toBe(true);
}
