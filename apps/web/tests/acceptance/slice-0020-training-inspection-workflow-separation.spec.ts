import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { createApiaryAndHive } from "./support/setup-workflow";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test("Dataset Curator works through separated Training Inspection stages", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("core-api online")).toBeVisible();

  const acceptTerms = page.getByTestId("accept-terms-button");
  if (await acceptTerms.isEnabled()) {
    await acceptTerms.click();
  }
  await expect(acceptTerms).toContainText("Terms accepted");

  const suffix = Date.now().toString();
  await createApiaryAndHive(page, `Slice 20 apiary ${suffix}`, `Slice 20 hive ${suffix}`);

  await page.getByTestId("inspection-date-input").fill("2026-08-03");
  await page.getByTestId("inspection-intent-select").selectOption("training_data_collection");
  await page.getByTestId("create-inspection-button").click();

  await expect(page.getByTestId("training-workflow-stage-nav")).toBeVisible();
  await expect(page.getByTestId("training-workflow-stage-nav")).toHaveAttribute("role", "tablist");
  await expect(page.getByTestId("workflow-stage-setup-button")).toHaveAttribute("aria-selected", "true");
  await expect(page.getByTestId("training-workflow-stage-setup")).toBeVisible();
  await expect(page.getByTestId("workflow-stage-crop-selection-button")).toContainText("0 crops");
  await expect(page.getByTestId("workflow-stage-bee-annotation-button")).toContainText("0 pending");
  await expect(page.getByTestId("workflow-stage-model-governance-button")).toContainText("jobs");

  await page.getByTestId("workflow-stage-crop-selection-button").click();
  await expect(page.getByTestId("workflow-stage-crop-selection-button")).toHaveAttribute("aria-selected", "true");
  await expect(page.getByTestId("training-workflow-stage-crop-selection")).toBeVisible();
  await expect(page.getByTestId("training-crop-review-controls")).toHaveCount(0);
  await expect(page.getByTestId("training-crop-review-request-panel")).toHaveCount(0);

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("training-source-image")).toBeVisible();

  await page.getByTestId("training-source-photo-preview").click({ position: { x: 180, y: 120 } });
  await page.getByTestId("save-training-crop-button").click();
  await expect(page.getByTestId("training-crop-list-item")).toHaveCount(1);
  await expect(page.getByTestId("workflow-stage-crop-selection-button")).toContainText("1 crop");

  await page.getByTestId("workflow-stage-bee-annotation-button").click();
  await expect(page.getByTestId("training-workflow-stage-bee-annotation")).toBeVisible();
  await expect(page.getByTestId("training-crop-review-controls")).toBeVisible();
  await expect(page.getByTestId("candidate-prelabel-controls")).toBeVisible();
  await expect(page.getByTestId("training-crop-review-request-panel")).toHaveCount(0);
  await expect(page.getByTestId("assign-training-crop-dataset-role-button")).toHaveCount(0);

  await page.getByTestId("training-crop-surface").click({ position: { x: 180, y: 120 } });
  await expect(page.getByTestId("training-crop-ellipse")).toHaveCount(1);
  await page.getByTestId("complete-training-crop-button").click();
  await expect(page.getByTestId("training-crop-list-item")).toContainText("review_complete");

  await page.getByTestId("workflow-stage-crop-governance-button").click();
  await expect(page.getByTestId("training-workflow-stage-crop-governance")).toBeVisible();
  await expect(page.getByTestId("workflow-stage-crop-governance-button")).toHaveAttribute("aria-selected", "true");
  await expect(page.getByTestId("crop-governance-list")).toHaveAttribute("role", "listbox");
  await expect(page.getByTestId("training-crop-list-item")).toHaveAttribute("role", "option");
  await expect(page.getByTestId("training-crop-list-item")).toHaveAttribute("aria-selected", "true");
  await expect(page.getByTestId("crop-governance-list")).toContainText("Crop 1");
  await expect(page.getByTestId("crop-governance-detail")).toContainText("Complete visible bees 1");
  await expect(page.getByTestId("request-training-crop-review-button")).toBeVisible();
  await expect(page.getByTestId("assign-training-crop-dataset-role-button")).toBeVisible();
  await expect(page.getByTestId("model-training-panel")).toHaveCount(0);

  await page.getByTestId("workflow-stage-model-governance-button").click();
  await expect(page.getByTestId("training-workflow-stage-model-governance")).toBeVisible();
  await expect(page.getByTestId("workflow-stage-model-governance-button")).toHaveAttribute("aria-selected", "true");
  await expect(page.getByTestId("model-training-panel")).toBeVisible();
  await expect(page.getByTestId("training-crop-dataset-role-select")).toHaveCount(0);

  await page.getByTestId("workflow-stage-bee-annotation-button").click();
  await expect(page.getByTestId("training-crop-ellipse")).toHaveCount(1);
});
