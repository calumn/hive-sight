import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test("Dataset Curator creates a physical YOLO OBB package from a completed Training Crop", async ({
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
  await page.getByTestId("apiary-name-input").fill(`Slice 11 apiary ${suffix}`);
  await page.getByTestId("create-apiary-button").click();
  await page.getByTestId("hive-name-input").fill(`Slice 11 hive ${suffix}`);
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

  await page.getByTestId("training-crop-surface").click({ position: { x: 180, y: 120 } });
  await expect(page.getByTestId("training-crop-ellipse")).toHaveCount(1);

  await page.getByTestId("complete-training-crop-button").click();
  await expect(page.getByTestId("training-crop-list-item")).toContainText("review_complete");

  await page.getByTestId("workflow-stage-crop-governance-button").click();
  await page.getByTestId("training-crop-dataset-role-select").selectOption("training");
  await page
    .getByTestId("training-crop-dataset-assignment-note-input")
    .fill("Accepted as first physical export package crop.");
  await page.getByTestId("assign-training-crop-dataset-role-button").click();

  await expect(page.getByTestId("training-crop-dataset-item-state")).toContainText(
    "Dataset item: Training"
  );

  await page.getByTestId("create-physical-yolo-obb-export-button").click();
  await expect(page.getByTestId("physical-yolo-obb-export-summary")).toContainText("Training");
  await expect(page.getByTestId("physical-yolo-obb-export-summary")).toContainText("Files");
  await expect(page.getByTestId("physical-yolo-obb-export-summary")).toContainText(
    "dataset-export-"
  );
  await expect(page.getByTestId("physical-yolo-obb-export-summary")).toContainText(
    "manifest.json"
  );
  await expect(page.getByTestId("physical-yolo-obb-export-summary")).toContainText(
    "dataset.yaml"
  );
});
