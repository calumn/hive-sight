import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test("Dataset Curator creates a crop, adds an oriented bee ellipse, and completes review", async ({
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
  await page.getByTestId("apiary-name-input").fill(`Slice 9 apiary ${suffix}`);
  await page.getByTestId("create-apiary-button").click();
  await page.getByTestId("hive-name-input").fill(`Slice 9 hive ${suffix}`);
  await page.getByTestId("create-hive-button").click();

  await page.getByTestId("inspection-date-input").fill("2026-07-30");
  await page.getByTestId("inspection-intent-select").selectOption("training_data_collection");
  await page.getByTestId("create-inspection-button").click();
  await expect(page.getByTestId("inspection-intent-badge")).toContainText(
    "Training data collection"
  );

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("training-crop-panel")).toBeVisible();
  await expect(page.getByTestId("training-source-image")).toBeVisible();

  await page.getByTestId("training-source-photo-preview").click({ position: { x: 180, y: 120 } });
  await expect(page.getByTestId("training-draft-crop-overlay")).toBeVisible();
  await page.getByTestId("save-training-crop-button").click();
  await expect(page.getByTestId("training-crop-list-item")).toHaveCount(1);

  await page.getByTestId("training-crop-surface").click({ position: { x: 180, y: 120 } });
  await expect(page.getByTestId("training-crop-ellipse")).toHaveCount(1);
  await page.getByTestId("rotate-training-ellipse-button").click();
  await expect(page.getByTestId("training-crop-review-controls")).toContainText("5 degrees");

  await expect(page.getByTestId("training-crop-visible-status-select")).toHaveValue(
    "has_visible_bees"
  );
  await page.getByTestId("complete-training-crop-button").click();
  await expect(page.getByTestId("training-crop-list-item")).toContainText("review_complete");
  await expect(page.getByTestId("training-crop-list-item")).toContainText("has_visible_bees");
});
