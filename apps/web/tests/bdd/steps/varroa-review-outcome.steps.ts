import { expect } from "@playwright/test";
import { createBdd } from "playwright-bdd";
import { fileURLToPath } from "node:url";
import { createApiaryAndHive } from "../../acceptance/support/setup-workflow";

const { Given, When, Then } = createBdd();
const fixtureImagePath = fileURLToPath(
  new URL("../../fixtures/bee-frame-test.png", import.meta.url)
);

Given("a Dataset Curator has opened an eligible bee for Varroa review", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("core-api online")).toBeVisible();

  const acceptTerms = page.getByTestId("accept-terms-button");
  if (await acceptTerms.isEnabled()) {
    await acceptTerms.click();
  }
  await expect(acceptTerms).toContainText("Terms accepted");

  const suffix = Date.now().toString();
  await createApiaryAndHive(page, `BDD apiary ${suffix}`, `BDD hive ${suffix}`);

  await page.getByTestId("inspection-date-input").fill("2026-08-05");
  await page.getByTestId("inspection-intent-select").selectOption("training_data_collection");
  await page.getByTestId("create-inspection-button").click();
  await expect(page.getByTestId("workflow-stage-varroa-review-button")).toBeVisible();

  await page.getByTestId("workflow-stage-crop-selection-button").click();
  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("training-source-image")).toBeVisible();

  await page.getByTestId("training-source-photo-preview").click({ position: { x: 180, y: 120 } });
  await page.getByTestId("save-training-crop-button").click();
  await page.getByTestId("workflow-stage-bee-annotation-button").click();
  await page.getByTestId("training-crop-surface").click({ position: { x: 180, y: 120 } });
  await expect(page.getByTestId("training-crop-ellipse")).toHaveCount(1);
  await page.getByTestId("complete-training-crop-button").click();

  await page.getByTestId("workflow-stage-varroa-review-button").click();
  await expect(page.getByTestId("training-workflow-stage-varroa-review")).toBeVisible();
  await expect(page.getByTestId("varroa-review-candidate")).toHaveCount(1);
  await expect(page.getByTestId("head-up-normalized-bee-crop")).toBeVisible();
});

When("the Dataset Curator records visible Varroa with two mite markers", async ({ page }) => {
  await page.getByTestId("varroa-review-place-marker-mode-button").click();
  const imagePlane = page.getByTestId("head-up-normalized-bee-crop-image-plane");
  await expect(imagePlane).toBeVisible();

  const planeBox = await imagePlane.boundingBox();
  expect(planeBox).not.toBeNull();
  const markerCenterX = Number(await imagePlane.getAttribute("data-marker-center-x"));
  const markerCenterY = Number(await imagePlane.getAttribute("data-marker-center-y"));

  await page.mouse.click(
    planeBox!.x + planeBox!.width * markerCenterX,
    planeBox!.y + planeBox!.height * markerCenterY
  );
  await page.mouse.click(
    planeBox!.x + planeBox!.width * Math.min(markerCenterX + 0.02, 0.98),
    planeBox!.y + planeBox!.height * Math.min(markerCenterY + 0.02, 0.98)
  );
  await expect(page.getByTestId("varroa-marker")).toHaveCount(2);

  await expect(page.getByTestId("varroa-review-outcome-select")).toHaveValue(
    "visible_varroa_present"
  );
  await page.getByTestId("save-varroa-review-outcome-button").click();
});

Then("HiveSight preserves a visible-Varroa review outcome for that bee", async ({ page }) => {
  await expect(page.getByTestId("varroa-review-candidate").first()).toContainText(
    "visible_varroa_present"
  );
});

Then("HiveSight preserves two mite markers for that bee", async ({ page }) => {
  await expect(page.getByTestId("varroa-marker")).toHaveCount(2);
  await expect(page.getByTestId("varroa-marker-list")).toContainText("Marker 1:");
  await expect(page.getByTestId("varroa-marker-list")).toContainText("Marker 2:");
});

Then("HiveSight reports one visible-Varroa bee and two visible Varroa markers", async ({ page }) => {
  await expect(page.getByTestId("varroa-review-summary")).toContainText("Visible Varroa bees 1");
  await expect(page.getByTestId("varroa-review-summary")).toContainText("Markers 2");
});

Then("HiveSight shows the saved markers when the review is reopened", async ({ page }) => {
  await page.getByTestId("workflow-stage-bee-annotation-button").click();
  await page.getByTestId("workflow-stage-varroa-review-button").click();
  await expect(page.getByTestId("training-workflow-stage-varroa-review")).toBeVisible();
  await expect(page.getByTestId("varroa-marker")).toHaveCount(2);
});
