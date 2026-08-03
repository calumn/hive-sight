import { expect, test, type Page } from "@playwright/test";
import { fileURLToPath } from "node:url";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test("Dataset Curator previews Model Candidate bee suggestions before accepting reviewed ellipses", async ({
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
  await page.getByTestId("apiary-name-input").fill(`Slice 15.2 apiary ${suffix}`);
  await page.getByTestId("create-apiary-button").click();
  await page.getByTestId("hive-name-input").fill(`Slice 15.2 hive ${suffix}`);
  await page.getByTestId("create-hive-button").click();

  await page.getByTestId("inspection-date-input").fill("2026-07-31");
  await page.getByTestId("inspection-intent-select").selectOption("training_data_collection");
  await page.getByTestId("create-inspection-button").click();

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("training-crop-panel")).toBeVisible();

  await createCompletedDatasetCrop(page, { x: 170, y: 120 }, "training");
  await createCompletedDatasetCrop(page, { x: 650, y: 360 }, "validation");
  await page.getByTestId("create-dataset-version-button").click();
  await expect(page.getByTestId("dataset-version-summary")).toContainText("HS-DV-");
  await page.getByTestId("acknowledge-model-training-warnings-checkbox").check();
  await page.getByTestId("start-model-training-run-button").click();
  await expect(page.getByTestId("model-training-run-summary")).toContainText("completed");
  await page.getByTestId("use-model-candidate-for-crop-yolo-button").click();
  await expect(page.getByTestId("model-candidate-selection-confirmation")).toContainText(
    "Now using HS-MC-"
  );
  await page.getByTestId("workflow-stage-bee-annotation-button").click();
  await expect(page.getByTestId("selected-crop-yolo-candidate-state")).toContainText(
    "Using HS-MC-"
  );

  await page.getByTestId("workflow-stage-crop-selection-button").click();
  await page.getByTestId("training-source-photo-preview").click({ position: { x: 720, y: 300 } });
  const latestCropIndex = await page.getByTestId("training-crop-list-item").count();
  await page.getByTestId("save-training-crop-button").click();
  await expect(page.getByTestId("training-crop-list-item")).toHaveCount(latestCropIndex + 1);
  await page.getByTestId("training-crop-list-item").nth(latestCropIndex).click();

  await page.getByTestId("candidate-prelabel-controls").scrollIntoViewIfNeeded();
  await expect(page.getByTestId("suggest-bees-button")).toBeInViewport();
  await page.getByTestId("suggest-bees-button").click();
  await expect(page.getByTestId("candidate-prelabel-message")).toContainText("suggestions");
  await expect(page.getByTestId("candidate-bee-proposal")).toHaveCount(2);
  await expect(page.getByTestId("training-crop-ellipse")).toHaveCount(0);

  await page.getByTestId("nudge-candidate-proposal-right-button").click();
  await page.getByTestId("accept-candidate-proposal-partial-button").click();
  await expect(page.getByTestId("training-crop-ellipse")).toHaveCount(1);
  await expect(page.getByTestId("candidate-bee-proposal")).toHaveCount(1);
  await expect(page.getByTestId("selected-training-ellipse-label")).toContainText(
    "partial_visible_bee"
  );
});

async function createCompletedDatasetCrop(
  page: Page,
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
    .fill(`Accepted as ${datasetRole} baseline crop.`);
  await page.getByTestId("assign-training-crop-dataset-role-button").click();
  await expect(page.getByTestId("training-crop-dataset-item-state")).toContainText(
    `Dataset item: ${datasetRole === "training" ? "Training" : "Validation"}`
  );
}
