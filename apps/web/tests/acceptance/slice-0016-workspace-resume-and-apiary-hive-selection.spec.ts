import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test("Workspace resumes existing Apiary and Hive selection for training data collection", async ({
  page
}) => {
  await page.goto("/");
  await expect(page.getByText("core-api online")).toBeVisible();
  await expect(page.getByTestId("inspection-intent-select")).toHaveValue("training_data_collection");

  const suffix = Date.now().toString();
  const apiaryName = `! Slice 16 apiary ${suffix}`;
  const hiveName = `! Slice 16 hive ${suffix}`;

  await page.getByTestId("apiary-name-input").fill(apiaryName);
  await page.getByTestId("create-apiary-button").click();
  await expect(page.getByTestId("apiary-select")).toHaveValue(/.+/);
  await expect(page.getByTestId("apiary-select")).toContainText(apiaryName);

  await page.getByTestId("hive-name-input").fill(hiveName);
  await page.getByTestId("create-hive-button").click();
  await expect(page.getByTestId("hive-select")).toHaveValue(/.+/);
  await expect(page.getByTestId("hive-select")).toContainText(hiveName);
  await expect(page.getByTestId("hive-configuration-state")).toContainText(
    "British National deep brood"
  );

  await page.reload();
  await expect(page.getByText("core-api online")).toBeVisible();
  await expect(page.getByTestId("apiary-select")).toContainText(apiaryName);
  await expect(page.getByTestId("hive-select")).toContainText(hiveName);
  await expect(page.getByTestId("create-inspection-button")).toBeEnabled();
  await expect(page.getByTestId("inspection-intent-select")).toHaveValue("training_data_collection");

  const acceptTerms = page.getByTestId("accept-terms-button");
  if (await acceptTerms.isEnabled()) {
    await acceptTerms.click();
  }
  await page.getByTestId("create-inspection-button").click();
  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();

  await expect(page.getByTestId("training-crop-panel")).toBeVisible();
  await expect(page.getByTestId("start-dataset-labelling-button")).toHaveCount(0);
});
