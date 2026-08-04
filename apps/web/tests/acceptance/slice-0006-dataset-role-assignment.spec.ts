import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { createApiaryAndHive } from "./support/setup-workflow";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test.skip("Dataset Curator assigns reviewed bee evidence to a protected benchmark item", async ({
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
  await createApiaryAndHive(page, `Role apiary ${suffix}`, `Role hive ${suffix}`);
  await expect(page.getByTestId("create-inspection-button")).toBeEnabled();

  await page.getByTestId("inspection-date-input").fill("2026-07-29");
  await page.getByTestId("inspection-intent-select").selectOption("training_data_collection");
  await page.getByTestId("create-inspection-button").click();

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("inspection-photo-list")).toContainText("bee-frame-test.png");

  await page.getByTestId("start-dataset-labelling-button").click();
  await expect(page.getByTestId("dataset-evidence-panel")).toBeVisible();
  await expect(page.getByTestId("dataset-item-state")).toContainText(
    "Review at least one bee suggestion"
  );
  await expect(page.getByTestId("assign-dataset-role-button")).toBeDisabled();

  await page.getByTestId("source-group-key-input").fill("role-frame-a");
  await page.getByTestId("image-quality-select").selectOption("usable");
  await page.getByTestId("save-labelling-metadata-button").click();
  await expect(page.getByTestId("image-quality-select")).toHaveValue("usable");

  await page.getByTestId("dataset-review-annotation-select").selectOption({ index: 1 });
  await page.getByTestId("submit-dataset-review-decision-button").click();
  await expect(page.getByTestId("dataset-item-state")).toContainText("1 reviewed annotations ready");

  await page.getByTestId("dataset-role-select").selectOption("benchmark");
  await page
    .getByTestId("dataset-assignment-note-input")
    .fill("Reserved as a benchmark frame after curator review.");
  await page.getByTestId("assign-dataset-role-button").click();

  await expect(page.getByTestId("dataset-item-state")).toContainText("Dataset item: benchmark");
  await expect(page.getByTestId("dataset-item-state")).toContainText("protected benchmark");
  await expect(page.getByTestId("dataset-role-select")).toBeDisabled();
  await expect(page.getByTestId("assign-dataset-role-button")).toBeDisabled();
});
