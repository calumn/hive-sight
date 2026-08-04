import { expect, test } from "@playwright/test";
import { createApiary } from "./support/setup-workflow";

test("Beekeeper records Hive Configuration before creating an Inspection", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("core-api online")).toBeVisible();

  const acceptTerms = page.getByTestId("accept-terms-button");
  if (await acceptTerms.isEnabled()) {
    await acceptTerms.click();
  }
  await expect(acceptTerms).toContainText("Terms accepted");

  const suffix = Date.now().toString();
  await createApiary(page, `Slice 12 apiary ${suffix}`);

  await expect(page.getByTestId("hive-configuration-frame-standard-select")).toBeVisible();
  await page
    .getByTestId("hive-configuration-frame-standard-select")
    .selectOption("british_national_deep_brood");
  await expect(page.getByTestId("hive-configuration-dimensions")).toContainText("432 mm");
  await expect(page.getByTestId("hive-configuration-dimensions")).toContainText("216 mm");

  await page.getByTestId("hive-name-input").fill(`Slice 12 hive ${suffix}`);
  await page.getByTestId("create-hive-button").click();
  await expect(page.getByTestId("hive-configuration-state")).toContainText(
    "British National deep brood"
  );

  await expect(page.getByTestId("create-inspection-button")).toBeEnabled();
  await page.getByTestId("inspection-date-input").fill("2026-07-30");
  await page.getByTestId("inspection-intent-select").selectOption("training_data_collection");
  await page.getByTestId("create-inspection-button").click();
  await expect(page.getByTestId("inspection-intent-badge")).toContainText(
    "Training data collection"
  );
});

test("Beekeeper configures an existing Hive before creating an Inspection", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("core-api online")).toBeVisible();

  await page
    .getByTestId("development-user-select")
    .selectOption("00000000-0000-0000-0000-000000000102");
  await expect(page.getByTestId("development-user-code")).toContainText("OWNER-A");
  await expect(page.getByTestId("hive-list")).toContainText("Owner A Hive");
  await expect(page.getByTestId("hive-configuration-state")).toContainText(
    "Hive Configuration is needed"
  );
  await expect(page.getByTestId("create-inspection-button")).toBeDisabled();

  await expect(page.getByTestId("hive-setup-form")).toBeVisible();
  await expect(page.getByTestId("hive-name-input")).toHaveCount(0);
  await page
    .getByTestId("hive-configuration-frame-standard-select")
    .selectOption("british_national_deep_brood");
  await expect(page.getByTestId("hive-configuration-dimensions")).toContainText("432 mm");
  await page.getByTestId("create-hive-button").click();

  await expect(page.getByTestId("hive-configuration-state")).toContainText(
    "British National deep brood"
  );
  await expect(page.getByTestId("create-inspection-button")).toBeEnabled();
});
