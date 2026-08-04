import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { createApiaryAndHive } from "./support/setup-workflow";

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
  await createApiaryAndHive(page, `Slice 8 apiary ${suffix}`, `Slice 8 hive ${suffix}`);
  await expect(page.getByTestId("create-inspection-button")).toBeEnabled();

  await page.getByTestId("inspection-date-input").fill("2026-07-29");
  await page.getByTestId("inspection-intent-select").selectOption("varroa_assessment");
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

test("Training-data collection intent exposes crop annotation instead of analysis controls", async ({
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
  await createApiaryAndHive(page, `Training apiary ${suffix}`, `Training hive ${suffix}`);

  await page.getByTestId("inspection-date-input").fill("2026-07-29");
  await page.getByTestId("inspection-intent-select").selectOption("training_data_collection");
  await page.getByTestId("create-inspection-button").click();
  await expect(page.getByTestId("inspection-intent-badge")).toContainText(
    "Training data collection"
  );

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("inspection-photo-list-item")).toHaveCount(1);
  await expect(page.getByTestId("training-crop-panel")).toBeVisible();
  await expect(page.getByTestId("start-dataset-labelling-button")).toHaveCount(0);
  await expect(page.getByTestId("process-analysis-button")).toHaveCount(0);
});

test("Beekeeper resumes a processed Varroa assessment after switching Users", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("core-api online")).toBeVisible();

  const userSelect = page.getByTestId("development-user-select");
  await userSelect.selectOption("00000000-0000-0000-0000-000000000103");
  await expect(page.getByTestId("development-user-code")).toContainText("OWNER-B");
  await expect(page.getByTestId("inspection-intent-select")).toHaveValue("varroa_assessment");

  await expect(page.getByTestId("hive-setup-form")).toBeVisible();
  await page
    .getByTestId("hive-configuration-frame-standard-select")
    .selectOption("british_national_deep_brood");
  await page.getByTestId("create-hive-button").click();
  await expect(page.getByTestId("create-inspection-button")).toBeEnabled();

  await page.getByTestId("inspection-date-input").fill("2026-08-04");
  await page.getByTestId("create-inspection-button").click();
  await expect(page.getByTestId("inspection-intent-badge")).toContainText("Varroa assessment");

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await page.getByTestId("process-analysis-button").click();
  await expect(page.getByText("Likely Varroa detections", { exact: true })).toBeVisible();
  await expect(page.getByTestId("evidence-panel")).toBeVisible();

  await userSelect.selectOption("00000000-0000-0000-0000-000000000101");
  await expect(page.getByTestId("development-user-code")).toContainText("DEV-OWNER-CURATOR");
  await userSelect.selectOption("00000000-0000-0000-0000-000000000103");

  await expect(page.getByTestId("development-user-code")).toContainText("OWNER-B");
  await expect(page.getByTestId("inspection-list")).toContainText("Varroa assessment");
  await expect(page.getByTestId("inspection-intent-badge")).toContainText("Varroa assessment");
  await expect(page.getByText("Likely Varroa detections", { exact: true })).toBeVisible();
  await expect(page.getByTestId("evidence-panel")).toBeVisible();
});
