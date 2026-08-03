import { expect, test, type Page } from "@playwright/test";
import { fileURLToPath } from "node:url";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test("Dataset Curator runs a fake Model Candidate benchmark evaluation", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("core-api online")).toBeVisible();

  const acceptTerms = page.getByTestId("accept-terms-button");
  if (await acceptTerms.isEnabled()) {
    await acceptTerms.click();
  }
  await expect(acceptTerms).toContainText("Terms accepted");

  const suffix = Date.now().toString();
  await page.getByTestId("apiary-name-input").fill(`Slice 15.4 apiary ${suffix}`);
  await page.getByTestId("create-apiary-button").click();
  await page.getByTestId("hive-name-input").fill(`Slice 15.4 hive ${suffix}`);
  await page.getByTestId("create-hive-button").click();

  await page.getByTestId("inspection-date-input").fill("2026-07-31");
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
  await page.getByTestId("training-crop-photo-select").selectOption({ index: 1 });
  await createCompletedDatasetCrop(page, { x: 420, y: 220 }, "benchmark");

  await page.getByTestId("create-dataset-version-button").click();
  await expect(page.getByTestId("dataset-version-summary")).toContainText("Benchmark protected 1");
  await page.getByTestId("acknowledge-model-training-warnings-checkbox").check();
  await page.getByTestId("start-model-training-run-button").click();
  await expect(page.getByTestId("model-training-run-summary")).toContainText("completed");
  await page.getByTestId("use-model-candidate-for-crop-yolo-button").click();

  await page.getByTestId("benchmark-evaluation-readiness-button").click();
  await expect(page.getByTestId("benchmark-evaluation-panel")).toContainText("Benchmark 1");
  await expect(page.getByTestId("benchmark-evaluation-panel")).toContainText(
    "SMALL_BENCHMARK_SET"
  );
  await page.getByTestId("start-benchmark-evaluation-button").click();
  await expect(page.getByTestId("benchmark-evaluation-summary")).toContainText("HS-BE-");
  await expect(page.getByTestId("benchmark-evaluation-summary")).toContainText("completed");
  await expect(page.getByTestId("benchmark-evaluation-summary")).toContainText("Precision");
  await expect(page.getByTestId("benchmark-evaluation-summary")).toContainText("Recall");
  await expect(page.getByTestId("benchmark-evaluation-activity")).toContainText(
    "Benchmark Evaluation completed."
  );
  await expect(page.getByTestId("benchmark-evaluation-report-link")).toBeVisible();
  await expect(page.getByTestId("benchmark-evaluation-raw-predictions-link")).toBeVisible();
  await expect(page.getByTestId("benchmark-evaluation-list")).toContainText(
    "Benchmark evaluations"
  );
});

async function createCompletedDatasetCrop(
  page: Page,
  position: { x: number; y: number },
  datasetRole: "training" | "validation" | "benchmark"
) {
  await page.getByTestId("training-source-photo-preview").click({ position });
  const latestCropIndex = await page.getByTestId("training-crop-list-item").count();
  await page.getByTestId("save-training-crop-button").click();
  await expect(page.getByTestId("training-crop-list-item")).toHaveCount(latestCropIndex + 1);
  await page.getByTestId("training-crop-surface").click({ position: { x: 180, y: 120 } });
  await expect(page.getByTestId("training-crop-ellipse")).toHaveCount(1);
  await page.getByTestId("complete-training-crop-button").click();
  await expect(page.getByTestId("training-crop-list-item").nth(latestCropIndex)).toContainText(
    "review_complete"
  );
  await page.getByTestId("training-crop-dataset-role-select").selectOption(datasetRole);
  if (datasetRole === "benchmark") {
    await page
      .getByTestId("training-crop-dataset-source-group-key-input")
      .fill("slice-0015-4-benchmark");
  }
  await page
    .getByTestId("training-crop-dataset-assignment-note-input")
    .fill(`Accepted as ${datasetRole} benchmark evaluation crop.`);
  await expect(page.getByTestId("assign-training-crop-dataset-role-button")).toBeEnabled();
  const assignmentResponsePromise = page.waitForResponse((response) =>
    response.url().includes("/dataset-item")
  );
  await page.getByTestId("assign-training-crop-dataset-role-button").click();
  const assignmentResponse = await assignmentResponsePromise;
  const assignmentBody = await assignmentResponse.json();
  expect(assignmentResponse.status(), JSON.stringify(assignmentBody)).toBe(201);
  await expect(page.getByTestId("training-crop-dataset-item-state")).toContainText(
    `Dataset item: ${formatDatasetRole(datasetRole)}`
  );
}

function formatDatasetRole(role: "training" | "validation" | "benchmark") {
  if (role === "training") return "Training";
  if (role === "validation") return "Validation";
  return "Benchmark";
}
