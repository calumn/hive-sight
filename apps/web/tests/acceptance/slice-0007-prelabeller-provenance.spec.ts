import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test.skip("Dataset Curator sees pre-labelling helper provenance before reviewing Draft Annotations", async ({
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
  await page.getByTestId("apiary-name-input").fill(`Prelabel apiary ${suffix}`);
  await page.getByTestId("create-apiary-button").click();
  await expect(page.getByTestId("create-hive-button")).toBeEnabled();

  await page.getByTestId("hive-name-input").fill(`Prelabel hive ${suffix}`);
  await page.getByTestId("create-hive-button").click();
  await expect(page.getByTestId("create-inspection-button")).toBeEnabled();

  await page.getByTestId("inspection-date-input").fill("2026-07-29");
  await page.getByTestId("inspection-intent-select").selectOption("training_data_collection");
  await page.getByTestId("create-inspection-button").click();

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("inspection-photo-list")).toContainText("bee-frame-test.png");

  await page.getByTestId("start-dataset-labelling-button").click();
  await expect(page.getByTestId("prelabeler-provenance-panel")).toBeVisible();
  await expect(page.getByTestId("prelabeler-provider")).toContainText("Deterministic");
  await expect(page.getByTestId("prelabeler-model")).toContainText("deterministic-fixture");
  await expect(page.getByTestId("prelabeler-run-status")).toContainText("succeeded / 2 suggestions");
  await expect(page.getByTestId("dataset-evidence-summary")).toContainText("Draft Annotations");
  await expect(page.getByTestId("dataset-item-state")).toContainText(
    "Review at least one bee suggestion"
  );

  await page.getByTestId("dataset-review-annotation-select").selectOption({ index: 1 });
  await page.getByTestId("submit-dataset-review-decision-button").click();

  await expect(page.getByTestId("dataset-review-state")).toContainText("Latest decision: approved");
  await expect(page.getByTestId("dataset-item-state")).toContainText("1 reviewed annotations ready");
});
