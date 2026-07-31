import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test("Dataset Curator creates a Dataset Version and fake Bee Detector training baseline", async ({
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
  await page.getByTestId("apiary-name-input").fill(`Slice 15 apiary ${suffix}`);
  await page.getByTestId("create-apiary-button").click();
  await page.getByTestId("hive-name-input").fill(`Slice 15 hive ${suffix}`);
  await page.getByTestId("create-hive-button").click();

  await page.getByTestId("inspection-date-input").fill("2026-07-31");
  await page.getByTestId("inspection-intent-select").selectOption("training_data_collection");
  await page.getByTestId("create-inspection-button").click();

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("training-crop-panel")).toBeVisible();

  await createCompletedDatasetCrop(page, { x: 170, y: 120 }, "training");
  await createCompletedDatasetCrop(page, { x: 650, y: 360 }, "validation");

  await page.getByTestId("model-training-readiness-button").click();
  await expect(page.getByTestId("model-training-readiness-summary")).toContainText(/Training [1-9]/);
  await expect(page.getByTestId("model-training-readiness-summary")).toContainText(
    /Validation [1-9]/
  );

  await page.getByTestId("create-dataset-version-button").click();
  await expect(page.getByTestId("dataset-version-summary")).toContainText("HS-DV-");
  await expect(page.getByTestId("dataset-version-summary")).toContainText("Warnings");

  await page.getByTestId("acknowledge-model-training-warnings-checkbox").check();
  await page.getByTestId("start-model-training-run-button").click();
  await expect(page.getByTestId("model-training-run-summary")).toContainText("HS-TR-");
  await expect(page.getByTestId("model-training-run-summary")).toContainText("completed");
  await expect(page.getByTestId("model-training-run-summary")).toContainText("fake");
});

async function createCompletedDatasetCrop(
  page,
  position: { x: number; y: number },
  datasetRole: "training" | "validation"
) {
  await page.getByTestId("training-source-photo-preview").click({ position });
  await page.getByTestId("save-training-crop-button").click();
  await page.getByTestId("training-crop-surface").click({ position: { x: 180, y: 120 } });
  await expect(page.getByTestId("training-crop-ellipse")).toHaveCount(1);
  await page.getByTestId("complete-training-crop-button").click();
  await page.getByTestId("training-crop-dataset-role-select").selectOption(datasetRole);
  await page
    .getByTestId("training-crop-dataset-assignment-note-input")
    .fill(`Accepted as ${datasetRole} baseline crop.`);
  await page.getByTestId("assign-training-crop-dataset-role-button").click();
  await expect(page.getByTestId("training-crop-dataset-item-state")).toContainText(
    `Dataset item: ${datasetRole}`
  );
}
