import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { createApiaryAndHive } from "./support/setup-workflow";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test("Dataset Curator runs a fake Bee Orientation baseline from a shared Marked-Bee Dataset Version", async ({
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
  await createApiaryAndHive(page, `Slice 22 apiary ${suffix}`, `Slice 22 hive ${suffix}`);

  await page.getByTestId("inspection-date-input").fill("2026-08-04");
  await page.getByTestId("inspection-intent-select").selectOption("training_data_collection");
  await page.getByTestId("create-inspection-button").click();

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("training-crop-panel")).toBeVisible();

  await createCompletedDatasetCrop(page, { x: 170, y: 120 }, "training");
  await createCompletedDatasetCrop(page, { x: 650, y: 360 }, "validation");

  await page.getByTestId("workflow-stage-model-governance-button").click();
  await page.getByTestId("create-dataset-version-button").click();
  await expect(page.getByTestId("dataset-version-summary")).toContainText("HS-DV-");
  await expect(page.getByTestId("dataset-version-summary")).toContainText("marked_bee");
  await expect(page.getByTestId("dataset-version-summary")).toContainText(
    "marked_bee_dataset_v1"
  );

  await page.getByTestId("bee-orientation-readiness-button").click();
  await expect(page.getByTestId("bee-orientation-readiness-summary")).toContainText(
    /Training bees [1-9]/
  );
  await expect(page.getByTestId("bee-orientation-readiness-summary")).toContainText(
    /Validation bees [1-9]/
  );
  await expect(page.getByTestId("bee-orientation-readiness-summary")).toContainText(
    /Generated train [1-9]/
  );

  await page.getByTestId("acknowledge-model-training-warnings-checkbox").check();
  await page.getByTestId("start-bee-orientation-training-run-button").click();
  await expect(page.getByTestId("bee-orientation-training-run-summary")).toContainText("HS-TR-");
  await expect(page.getByTestId("bee-orientation-training-run-summary")).toContainText(
    "completed"
  );
  await expect(page.getByTestId("bee-orientation-training-run-summary")).toContainText(
    "Bee Orientation"
  );
  await expect(page.getByTestId("bee-orientation-training-run-summary")).toContainText(
    /Train examples [1-9]/
  );
  await expect(page.getByTestId("bee-orientation-training-activity")).toContainText(
    "Bee Orientation package validated"
  );
  await expect(page.getByTestId("bee-orientation-training-report-link")).toBeVisible();
  await expect(page.getByTestId("model-training-run-list")).toContainText("Bee Orientation");
});

async function createCompletedDatasetCrop(
  page,
  position: { x: number; y: number },
  datasetRole: "training" | "validation"
) {
  await page.getByTestId("workflow-stage-crop-selection-button").click();
  await page.getByTestId("training-source-photo-preview").click({ position });
  const latestCropIndex = await page.getByTestId("training-crop-list-item").count();
  await page.getByTestId("save-training-crop-button").click();
  await expect(page.getByTestId("training-crop-list-item")).toHaveCount(latestCropIndex + 1);
  await page.getByTestId("training-crop-surface").click({ position: { x: 180, y: 120 } });
  await expect(page.getByTestId("training-crop-ellipse")).toHaveCount(1);
  await page.getByTestId("complete-training-crop-button").click();
  await page.getByTestId("workflow-stage-crop-governance-button").click();
  await page.getByTestId("training-crop-dataset-role-select").selectOption(datasetRole);
  await page
    .getByTestId("training-crop-dataset-assignment-note-input")
    .fill(`Accepted as ${datasetRole} orientation baseline crop.`);
  await page.getByTestId("assign-training-crop-dataset-role-button").click();
  await expect(page.getByTestId("training-crop-list-item").nth(latestCropIndex)).toContainText(
    datasetRole === "training" ? "Training" : "Validation"
  );
}
