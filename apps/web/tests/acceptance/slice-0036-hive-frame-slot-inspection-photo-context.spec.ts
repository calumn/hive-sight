import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { createApiaryAndHive, prepareFirstBroodSlotForUpload } from "./support/setup-workflow";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test("Varroa assessment photos are attached to inspected brood slot sides", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("core-api online")).toBeVisible();

  const acceptTerms = page.getByTestId("accept-terms-button");
  if (await acceptTerms.isEnabled()) {
    await acceptTerms.click();
  }
  await expect(acceptTerms).toContainText("Terms accepted");

  const suffix = Date.now().toString();
  await createApiaryAndHive(page, `Slice 36 apiary ${suffix}`, `Slice 36 hive ${suffix}`);

  await page.getByTestId("inspection-date-input").fill("2026-08-17");
  await page.getByTestId("inspection-intent-select").selectOption("varroa_assessment");
  await page.getByTestId("create-inspection-button").click();

  await expect(page.getByTestId("brood-slot-observation")).toHaveCount(10);
  await expect(page.getByTestId("brood-slot-coverage-panel")).toContainText("Pending");
  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await expect(page.getByTestId("upload-photo-button")).toBeDisabled();

  await prepareFirstBroodSlotForUpload(page);
  await page.getByTestId("inspection-photo-frame-side-select").selectOption("side_a");
  await expect(page.getByTestId("upload-photo-button")).toBeEnabled();
  await page.getByTestId("upload-photo-button").click();

  await expect(page.getByTestId("inspection-photo-list-item")).toHaveCount(1);
  await expect(page.getByTestId("brood-slot-coverage-panel")).toContainText("Side A");
  await expect(page.getByTestId("brood-slot-coverage-panel")).toContainText("bee-frame-test.png");
});
