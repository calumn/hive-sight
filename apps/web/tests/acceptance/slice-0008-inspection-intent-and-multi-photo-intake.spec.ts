import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test("Beekeeper creates an Inspection with intent and sees repeated photo uploads listed", async ({
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
  await page.getByTestId("apiary-name-input").fill(`Slice 8 apiary ${suffix}`);
  await page.getByTestId("create-apiary-button").click();
  await expect(page.getByTestId("create-hive-button")).toBeEnabled();

  await page.getByTestId("hive-name-input").fill(`Slice 8 hive ${suffix}`);
  await page.getByTestId("create-hive-button").click();
  await expect(page.getByTestId("create-inspection-button")).toBeEnabled();

  await page.getByTestId("inspection-date-input").fill("2026-07-29");
  await expect(page.getByTestId("inspection-intent-select")).toHaveValue("varroa_assessment");
  await page.getByTestId("create-inspection-button").click();
  await expect(page.getByTestId("inspection-intent-badge")).toContainText("Varroa assessment");

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("inspection-photo-list-item")).toHaveCount(1);

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("inspection-photo-list-item")).toHaveCount(2);
  await expect(page.getByTestId("inspection-photo-list")).toContainText("bee-frame-test.png");
  await expect(page.getByTestId("process-analysis-button")).toBeVisible();
  await expect(page.getByTestId("dataset-labelling-panel")).toHaveCount(0);
});

test("Training-data collection intent exposes dataset labelling instead of analysis controls", async ({
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
  await page.getByTestId("apiary-name-input").fill(`Training apiary ${suffix}`);
  await page.getByTestId("create-apiary-button").click();
  await page.getByTestId("hive-name-input").fill(`Training hive ${suffix}`);
  await page.getByTestId("create-hive-button").click();

  await page.getByTestId("inspection-date-input").fill("2026-07-29");
  await page.getByTestId("inspection-intent-select").selectOption("training_data_collection");
  await page.getByTestId("create-inspection-button").click();
  await expect(page.getByTestId("inspection-intent-badge")).toContainText(
    "Training data collection"
  );

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("inspection-photo-list-item")).toHaveCount(1);
  await expect(page.getByTestId("dataset-labelling-panel")).toBeVisible();
  await expect(page.getByTestId("process-analysis-button")).toHaveCount(0);
});
