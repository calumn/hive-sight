import { expect, test, type Page } from "@playwright/test";
import { fileURLToPath } from "node:url";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test.skip("Dataset Curator reviews AI-assisted bee draft annotations", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("core-api online")).toBeVisible();

  const acceptTerms = page.getByTestId("accept-terms-button");
  if (await acceptTerms.isEnabled()) {
    await acceptTerms.click();
  }
  await expect(acceptTerms).toContainText("Terms accepted");

  const suffix = Date.now().toString();
  await page.getByTestId("apiary-name-input").fill(`Dataset apiary ${suffix}`);
  await page.getByTestId("create-apiary-button").click();
  await expect(page.getByTestId("create-hive-button")).toBeEnabled();

  await page.getByTestId("hive-name-input").fill(`Dataset hive ${suffix}`);
  await page.getByTestId("create-hive-button").click();
  await expect(page.getByTestId("create-inspection-button")).toBeEnabled();

  await page.getByTestId("inspection-date-input").fill("2026-07-29");
  await page.getByTestId("inspection-intent-select").selectOption("training_data_collection");
  await page.getByTestId("create-inspection-button").click();

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await expect(page.getByText("bee-frame-test.png")).toBeVisible();
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("inspection-photo-list")).toContainText("bee-frame-test.png");

  const labellingPanel = page.getByTestId("dataset-labelling-panel");
  await expect(labellingPanel).toBeVisible();
  await page.getByTestId("start-dataset-labelling-button").click();

  await expect(page.getByTestId("dataset-evidence-panel")).toBeVisible();
  await expect(page.getByTestId("dataset-evidence-image")).toBeVisible();
  await expect(page.getByTestId("dataset-evidence-summary")).toContainText(
    "1 complete visible bee and 1 partial visible bee"
  );
  await expect(page.getByTestId("dataset-evidence-caveat")).toContainText(
    "Dataset use is not assigned"
  );

  await expect(page.locator('[data-testid="annotation-box"]')).toHaveCount(2);
  await expect(
    page.locator('[data-testid="annotation-box"][data-annotation-type="complete_visible_bee"]')
  ).toHaveCount(1);
  await expect(
    page.locator('[data-testid="annotation-box"][data-annotation-type="partial_visible_bee"]')
  ).toHaveCount(1);
  expect(await annotationBoxesAreInsideDatasetPhoto(page)).toBe(true);

  await page.getByTestId("source-group-key-input").fill("frame-a-side-1");
  await page.getByTestId("image-quality-select").selectOption("usable");
  await page.getByTestId("save-labelling-metadata-button").click();
  await expect(page.getByTestId("image-quality-select")).toHaveValue("usable");

  await page.getByTestId("dataset-review-annotation-select").selectOption({ index: 1 });
  await page.getByTestId("submit-dataset-review-decision-button").click();
  await expect(page.getByTestId("dataset-review-state")).toContainText("Latest decision: approved");

  await page.getByTestId("dataset-review-annotation-select").selectOption({ index: 2 });
  await page.getByTestId("submit-dataset-review-decision-button").click();
  await expect(
    page.locator('[data-testid="annotation-box"][data-review-decision="approved"]')
  ).toHaveCount(2);
  await expect(labellingPanel.getByText("review_in_progress")).toBeVisible();
});

async function annotationBoxesAreInsideDatasetPhoto(page: Page): Promise<boolean> {
  return page.getByTestId("dataset-photo-evidence").evaluate((photo) => {
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
