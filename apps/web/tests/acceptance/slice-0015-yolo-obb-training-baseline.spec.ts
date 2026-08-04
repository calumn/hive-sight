import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { createApiaryAndHive } from "./support/setup-workflow";

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
  await createApiaryAndHive(page, `Slice 15 apiary ${suffix}`, `Slice 15 hive ${suffix}`);

  await page.getByTestId("inspection-date-input").fill("2026-07-31");
  await page.getByTestId("inspection-intent-select").selectOption("training_data_collection");
  await page.getByTestId("create-inspection-button").click();

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("training-crop-panel")).toBeVisible();

  await createCompletedDatasetCrop(page, { x: 170, y: 120 }, "training");
  await createCompletedDatasetCrop(page, { x: 650, y: 360 }, "validation");
  await expect(page.getByTestId("training-crop-list-item").nth(0)).toContainText("Training");
  await expect(page.getByTestId("training-crop-list-item").nth(1)).toContainText("Validation");

  await page.getByTestId("workflow-stage-model-governance-button").click();
  await expect(page.getByTestId("training-workflow-stage-model-governance")).toBeVisible();
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
  await expect(page.getByTestId("model-training-run-summary")).toContainText("Phase completed");
  await expect(page.getByTestId("model-training-run-summary")).toContainText("Progress 100%");
  await expect(page.getByTestId("model-training-run-summary")).toContainText("Started");
  await expect(page.getByTestId("model-training-run-summary")).toContainText("Last heartbeat");
  await expect(page.getByTestId("model-training-run-summary")).toContainText("Elapsed");
  await expect(page.getByTestId("model-training-activity")).toContainText(
    "Training completed and Model Candidate created."
  );
  await expect(page.getByTestId("model-training-log-excerpt")).toContainText(
    "Fake adapter completed"
  );
  await expect(page.getByTestId("model-training-run-summary")).toContainText("fake");
  await expect(page.getByTestId("model-training-run-list")).toContainText("Training runs");
  await expect(page.getByTestId("model-training-run-list")).toContainText("Last checked");
  await expect(page.getByTestId("model-training-run-list-item").first()).toContainText("HS-TR-");
  await expect(page.getByTestId("model-training-run-list-item").first()).toContainText(
    "completed"
  );
  await expect(page.getByTestId("model-training-run-list-item").first()).toContainText(
    "Phase completed"
  );
  await expect(page.getByTestId("model-training-run-list-item").first()).toContainText(
    "Progress 100%"
  );
  await expect(page.getByTestId("model-training-run-list-item").first()).toContainText(
    "Heartbeat"
  );
  await expect(page.getByTestId("model-training-run-list-item").first()).toContainText(
    "Candidate"
  );
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
  await expect(page.getByTestId("training-crop-list-item").nth(latestCropIndex)).toContainText(
    "Unassigned"
  );
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
  await expect(page.getByTestId("training-crop-list-item").nth(latestCropIndex)).toContainText(
    datasetRole === "training" ? "Training" : "Validation"
  );
}
