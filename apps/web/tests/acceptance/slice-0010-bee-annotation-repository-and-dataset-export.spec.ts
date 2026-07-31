import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test("Dataset Curator assigns a completed Training Crop and sees a YOLO OBB export summary", async ({
  page
}) => {
  await page.goto("/");
  await expect(page.getByText("core-api online")).toBeVisible();

  const acceptTerms = page.getByTestId("accept-terms-button");
  if (await acceptTerms.isEnabled()) {
    await acceptTerms.click();
  }
  await expect(acceptTerms).toContainText("Terms accepted");

  const suffix = Date.now().toString();
  await page.getByTestId("apiary-name-input").fill(`Slice 10 apiary ${suffix}`);
  await page.getByTestId("create-apiary-button").click();
  await page.getByTestId("hive-name-input").fill(`Slice 10 hive ${suffix}`);
  await page.getByTestId("create-hive-button").click();

  await page.getByTestId("inspection-date-input").fill("2026-07-30");
  await page.getByTestId("inspection-intent-select").selectOption("training_data_collection");
  await page.getByTestId("create-inspection-button").click();

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("training-crop-panel")).toBeVisible();
  await expect(page.getByTestId("training-source-image")).toBeVisible();

  await page.getByTestId("training-source-photo-preview").click({ position: { x: 180, y: 120 } });
  await page.getByTestId("save-training-crop-button").click();
  await expect(page.getByTestId("training-crop-list-item")).toHaveCount(1);
  await expect(page.getByTestId("training-crop-list-item")).toContainText("Unassigned");

  await page.getByTestId("training-crop-surface").click({ position: { x: 180, y: 120 } });
  await expect(page.getByTestId("training-crop-ellipse")).toHaveCount(1);

  await page.getByTestId("complete-training-crop-button").click();
  await expect(page.getByTestId("training-crop-list-item")).toContainText("review_complete");

  await page.getByTestId("training-crop-dataset-role-select").selectOption("training");
  await page
    .getByTestId("training-crop-dataset-assignment-note-input")
    .fill("Accepted as first training crop for YOLO OBB export.");
  await page.getByTestId("assign-training-crop-dataset-role-button").click();

  await expect(page.getByTestId("training-crop-dataset-item-state")).toContainText(
    "Dataset item: Training"
  );
  await expect(page.getByTestId("training-crop-list-item")).toContainText("Training");
  await expect(page.getByTestId("training-crop-dataset-item-state")).toContainText(
    "1 ellipse snapshots"
  );
  await expect(page.getByTestId("assign-training-crop-dataset-role-button")).toBeDisabled();

  await page.getByTestId("create-yolo-obb-export-button").click();
  await expect(page.getByTestId("yolo-obb-export-summary")).toContainText("Training 1");
  await expect(page.getByTestId("yolo-obb-export-summary")).toContainText("Labels 1");
  await expect(page.getByTestId("yolo-obb-export-summary")).toContainText(
    "class x1 y1 x2 y2 x3 y3 x4 y4"
  );
});
