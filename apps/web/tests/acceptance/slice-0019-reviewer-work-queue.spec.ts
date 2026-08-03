import { expect, test, type APIRequestContext } from "@playwright/test";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));
const coreApiUrl = process.env.VITE_CORE_API_URL ?? "http://127.0.0.1:8000";
const curatorUserId = "00000000-0000-0000-0000-000000000104";
const reviewerOneUserId = "00000000-0000-0000-0000-000000000105";
const reviewerTwoUserId = "00000000-0000-0000-0000-000000000106";

test("Reviewer completes shared Review Queue work without seeing private source metadata", async ({
  page
}) => {
  const setup = await setupReviewQueueItem(page.request);

  await page.goto("/");
  await expect(page.getByText("core-api online")).toBeVisible();
  await page.getByTestId("development-user-select").selectOption(reviewerOneUserId);
  await expect(page.getByTestId("development-user-code")).toContainText("REVIEWER-1");
  await page.getByTestId("review-work-page-button").click();

  await expect(page.getByTestId("review-work-page")).toBeVisible();
  await expect(page.getByTestId("review-work-list")).toContainText(setup.reviewQueueHumanReadableId);
  await expect(page.getByTestId("review-work-safe-metadata")).toContainText("Training Crop");
  await expect(page.getByTestId("review-work-safe-metadata")).not.toContainText(
    setup.privateFilename
  );
  await expect(page.getByTestId("review-work-ellipse")).toHaveCount(2);

  await page.getByTestId("review-work-outcome-select").selectOption("approved");
  await page.getByTestId("complete-review-work-button").click();
  await expect(page.getByTestId("review-work-status-message")).toContainText("approved");
  await expect(page.getByTestId("review-history-panel")).toContainText(
    setup.reviewQueueHumanReadableId
  );
  await expect(page.getByTestId("review-work-empty-state")).toBeVisible();

  await page.getByTestId("development-user-select").selectOption(reviewerTwoUserId);
  await page.getByTestId("review-work-page-button").click();
  await expect(page.getByTestId("review-work-empty-state")).toBeVisible();
});

async function setupReviewQueueItem(request: APIRequestContext) {
  const runKey = `review-queue-${Date.now()}`;
  const session = await request.get(`${coreApiUrl}/v1/dev/session`, {
    headers: devHeaders(curatorUserId)
  });
  expect(session.ok()).toBeTruthy();
  const workspaceId = (await session.json()).workspace_id as string;
  await request.post(`${coreApiUrl}/v1/workspace-data-use-agreements/acceptances`, {
    data: { workspace_id: workspaceId, terms_version: "2026-08-01" },
    headers: jsonHeaders(curatorUserId)
  });
  const privateFilename = `${runKey}-private-frame-name.png`;
  const crop = await createCompletedTrainingCrop(request, workspaceId, runKey, privateFilename);
  const reviewRequest = await request.post(`${coreApiUrl}/v1/review-queue/items`, {
    data: {
      workspace_id: workspaceId,
      training_crop_id: crop.trainingCropId,
      request_notes: "Please verify these bee ellipses."
    },
    headers: jsonHeaders(curatorUserId)
  });
  expect(reviewRequest.status()).toBe(201);
  const reviewQueueItem = await reviewRequest.json();
  return {
    privateFilename,
    reviewQueueHumanReadableId: reviewQueueItem.human_readable_id as string
  };
}

async function createCompletedTrainingCrop(
  request: APIRequestContext,
  workspaceId: string,
  runKey: string,
  filename: string
) {
  const apiary = await request.post(`${coreApiUrl}/v1/apiaries`, {
    data: { workspace_id: workspaceId, name: `Review Queue ${runKey}` },
    headers: jsonHeaders(curatorUserId)
  });
  expect(apiary.status()).toBe(201);
  const apiaryId = (await apiary.json()).apiary_id as string;
  const hive = await request.post(`${coreApiUrl}/v1/hives`, {
    data: { apiary_id: apiaryId, name: `Hive ${runKey}` },
    headers: jsonHeaders(curatorUserId)
  });
  expect(hive.status()).toBe(201);
  const hiveId = (await hive.json()).hive_id as string;
  await request.put(`${coreApiUrl}/v1/hives/${hiveId}/configuration`, {
    data: { workspace_id: workspaceId, frame_standard_id: "british_national_deep_brood" },
    headers: jsonHeaders(curatorUserId)
  });
  const inspection = await request.post(`${coreApiUrl}/v1/inspections`, {
    data: {
      hive_id: hiveId,
      inspection_date: "2026-08-03",
      intent: "training_data_collection"
    },
    headers: jsonHeaders(curatorUserId)
  });
  expect(inspection.status()).toBe(201);
  const inspectionId = (await inspection.json()).inspection_id as string;
  const intake = await request.post(
    `${coreApiUrl}/v1/inspection-photos/intake?workspace_id=${workspaceId}&inspection_id=${inspectionId}`,
    {
      data: readFileSync(fixtureImagePath),
      headers: {
        ...devHeaders(curatorUserId),
        "content-type": "image/png",
        "x-hivesight-filename": filename
      }
    }
  );
  expect(intake.status()).toBe(202);
  const inspectionPhotoId = (await intake.json()).inspection_photo.inspection_photo_id as string;
  const crop = await request.post(`${coreApiUrl}/v1/training-crops`, {
    data: {
      workspace_id: workspaceId,
      inspection_photo_id: inspectionPhotoId,
      crop_x: 10,
      crop_y: 20,
      crop_width: 90,
      crop_height: 80,
      source_image_width_px: 160,
      source_image_height_px: 120
    },
    headers: jsonHeaders(curatorUserId)
  });
  expect(crop.status()).toBe(201);
  const trainingCropId = (await crop.json()).training_crop_id as string;
  for (const [annotationType, centerX] of [
    ["complete_visible_bee", 45],
    ["partial_visible_bee", 20]
  ] as const) {
    const ellipse = await request.post(
      `${coreApiUrl}/v1/training-crops/${trainingCropId}/bee-ellipses`,
      {
        data: {
          workspace_id: workspaceId,
          annotation_type: annotationType,
          center_x: centerX,
          center_y: 50,
          radius_x: 16,
          radius_y: 8,
          rotation_degrees: 20
        },
        headers: jsonHeaders(curatorUserId)
      }
    );
    expect(ellipse.status()).toBe(201);
  }
  const completed = await request.patch(`${coreApiUrl}/v1/training-crops/${trainingCropId}`, {
    data: {
      workspace_id: workspaceId,
      visible_bee_status: "has_visible_bees",
      review_status: "review_complete"
    },
    headers: jsonHeaders(curatorUserId)
  });
  expect(completed.status()).toBe(200);
  return { trainingCropId };
}

function devHeaders(devUserId: string) {
  return { "x-hivesight-dev-user-id": devUserId };
}

function jsonHeaders(devUserId: string) {
  return { ...devHeaders(devUserId), "content-type": "application/json" };
}
