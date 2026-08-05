import { expect, test, type Page } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { createApiaryAndHive } from "./support/setup-workflow";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test("Dataset Curator evaluates a Bee Orientation candidate against protected benchmark bees", async ({
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
  await createApiaryAndHive(page, `Slice 24 apiary ${suffix}`, `Slice 24 hive ${suffix}`);

  await page.getByTestId("inspection-date-input").fill("2026-08-05");
  await page.getByTestId("inspection-intent-select").selectOption("training_data_collection");
  await page.getByTestId("create-inspection-button").click();

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("training-crop-panel")).toBeVisible();

  await createCompletedDatasetCrop(page, { x: 170, y: 120 }, "training");
  await createCompletedDatasetCrop(page, { x: 650, y: 360 }, "validation");
  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("inspection-photo-list-item")).toHaveCount(2);
  await page.getByTestId("workflow-stage-crop-selection-button").click();
  await page.getByTestId("training-crop-photo-select").selectOption({ index: 1 });
  await createCompletedDatasetCrop(page, { x: 420, y: 220 }, "benchmark");

  await page.getByTestId("workflow-stage-model-governance-button").click();
  await page.getByTestId("create-dataset-version-button").click();
  await expect(page.getByTestId("dataset-version-summary")).toContainText(
    /Benchmark protected [1-9]/
  );
  await page.getByTestId("acknowledge-model-training-warnings-checkbox").check();
  const trainingRunCountBefore = await page.getByTestId("model-training-run-list-item").count();
  await page.getByTestId("start-model-training-run-button").click();
  await expect(page.getByTestId("model-training-run-list")).toContainText("Bee Localisation");
  await expect
    .poll(
      async () => {
        await page.getByTestId("model-training-readiness-button").click();
        return page.getByTestId("model-training-run-list-item").count();
      },
      { timeout: 10000 }
    )
    .toBeGreaterThanOrEqual(trainingRunCountBefore + 2);
  await expect(page.getByTestId("model-training-run-list")).toContainText("Bee Orientation");
  await expect(page.getByTestId("model-training-run-list")).toContainText("completed");

  await page.getByTestId("orientation-benchmark-readiness-button").click();
  await expect(page.getByTestId("orientation-benchmark-readiness-summary")).toContainText(
    /Eligible bees [1-9]/
  );
  await expect(page.getByTestId("orientation-benchmark-readiness-summary")).toContainText(
    "SMALL_ORIENTATION_BENCHMARK_SET"
  );
  await page.getByTestId("start-orientation-benchmark-evaluation-button").click();
  await expect(page.getByTestId("orientation-benchmark-evaluation-summary")).toContainText(
    "HS-OB-"
  );
  await expect(page.getByTestId("orientation-benchmark-evaluation-summary")).toContainText(
    "completed"
  );
  await expect(page.getByTestId("orientation-benchmark-evaluation-summary")).toContainText(
    "Accuracy"
  );
  await expect(page.getByTestId("orientation-benchmark-evaluation-summary")).toContainText(
    /Examples [1-9]/
  );
  await expect(page.getByTestId("orientation-benchmark-evaluation-activity")).toContainText(
    "Bee Orientation Benchmark Evaluation completed."
  );
  await expect(page.getByTestId("orientation-benchmark-evaluation-report-link")).toBeVisible();
  await expect(
    page.getByTestId("orientation-benchmark-evaluation-raw-predictions-link")
  ).toBeVisible();
  await expect(page.getByTestId("benchmark-evaluation-list")).toContainText("Bee Orientation");
  await expect(page.getByTestId("benchmark-evaluation-list")).not.toContainText("Varroa");
});

async function createCompletedDatasetCrop(
  page: Page,
  position: { x: number; y: number },
  datasetRole: "training" | "validation" | "benchmark"
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
  if (datasetRole === "benchmark") {
    await page
      .getByTestId("training-crop-dataset-source-group-key-input")
      .fill("slice-0024-orientation-benchmark");
  }
  await page
    .getByTestId("training-crop-dataset-assignment-note-input")
    .fill(`Accepted as ${datasetRole} orientation benchmark crop.`);
  await expect(page.getByTestId("assign-training-crop-dataset-role-button")).toBeEnabled();
  await page.getByTestId("assign-training-crop-dataset-role-button").click();
  await expect(page.getByTestId("training-crop-dataset-item-state")).toContainText(
    `Dataset item: ${formatDatasetRole(datasetRole)}`
  );
}

function formatDatasetRole(role: "training" | "validation" | "benchmark") {
  if (role === "training") return "Training";
  if (role === "validation") return "Validation";
  return "Benchmark";
}
