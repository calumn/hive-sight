import { expect, test, type Page } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { createApiaryAndHive } from "./support/setup-workflow";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test.skip("Reviewer records an annotation Review Decision", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("core-api online")).toBeVisible();

  const acceptTerms = page.getByTestId("accept-terms-button");
  if (await acceptTerms.isEnabled()) {
    await acceptTerms.click();
  }
  await expect(acceptTerms).toContainText("Terms accepted");

  const suffix = Date.now().toString();
  await createApiaryAndHive(page, `Acceptance apiary ${suffix}`, `Hive ${suffix}`);
  await expect(page.getByTestId("create-inspection-button")).toBeEnabled();

  await page.getByTestId("inspection-date-input").fill("2026-07-29");
  await page.getByTestId("inspection-intent-select").selectOption("varroa_assessment");
  await page.getByTestId("create-inspection-button").click();

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await expect(page.getByText("bee-frame-test.png")).toBeVisible();
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByText("Analysis queued")).toBeVisible();

  await page.getByTestId("process-analysis-button").click();

  await expect(page.getByText("Complete visible bees", { exact: true })).toBeVisible();
  await expect(page.getByText("Likely Varroa detections", { exact: true })).toBeVisible();
  const evidencePanel = page.getByTestId("evidence-panel");
  await expect(evidencePanel).toBeVisible();
  await expect(page.getByTestId("evidence-image")).toBeVisible();
  await expect(page.getByTestId("evidence-caveat")).toContainText("Deterministic stub evidence");
  await expect(page.getByTestId("evidence-summary")).toContainText(
    "3 complete visible bees and 1 partial visible bee"
  );

  await expect(page.locator('[data-testid="annotation-box"]')).toHaveCount(4);
  await expect(
    page.locator('[data-testid="annotation-box"][data-annotation-type="complete_visible_bee"]')
  ).toHaveCount(3);
  await expect(
    page.locator('[data-testid="annotation-box"][data-annotation-type="partial_visible_bee"]')
  ).toHaveCount(1);

  expect(await annotationBoxesAreInsidePhoto(page)).toBe(true);

  await page.getByTestId("review-annotation-select").selectOption({ index: 1 });
  await page.getByTestId("review-decision-select").selectOption("approved");
  await page.getByTestId("review-notes-input").fill("Accepted as a complete visible bee.");
  await page.getByTestId("submit-review-decision-button").click();
  await expect(page.getByTestId("review-state")).toContainText("Latest decision: approved");
  await expect(page.locator('[data-testid="annotation-box"][data-review-decision="approved"]')).toHaveCount(1);
  await expect(page.getByText("Review evidence only. Dataset use is not assigned in this slice.")).toBeVisible();

  await page.setViewportSize({ width: 390, height: 844 });
  expect(await annotationBoxesAreInsidePhoto(page)).toBe(true);
});

async function annotationBoxesAreInsidePhoto(page: Page): Promise<boolean> {
  return page.getByTestId("photo-evidence").evaluate((photo) => {
    const photoBox = photo.getBoundingClientRect();
    const boxes = Array.from(photo.querySelectorAll('[data-testid="annotation-box"]'));
    if (photoBox.width <= 0 || photoBox.height <= 0 || boxes.length === 0) {
      return false;
    }

    return boxes.every((box) => {
      const annotationBox = box.getBoundingClientRect();
      return (
        annotationBox.width > 0 &&
        annotationBox.height > 0 &&
        annotationBox.left >= photoBox.left &&
        annotationBox.top >= photoBox.top &&
        annotationBox.right <= photoBox.right &&
        annotationBox.bottom <= photoBox.bottom
      );
    });
  });
}
