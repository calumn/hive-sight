import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { createApiaryAndHive } from "./support/setup-workflow";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test("Dataset Curator records Varroa review cues and a visible Varroa outcome", async ({
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
  await createApiaryAndHive(page, `Slice 25 apiary ${suffix}`, `Slice 25 hive ${suffix}`);

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

  await page
    .getByTestId("training-ellipse-varroa-suitability-select")
    .selectOption("body_occluded_or_hard_to_assess");
  await page.getByTestId("training-ellipse-suspected-varroa-checkbox").check();
  await page.getByTestId("complete-training-crop-button").click();

  await page.getByTestId("workflow-stage-varroa-review-button").click();
  await expect(page.getByTestId("training-workflow-stage-varroa-review")).toBeVisible();
  await expect(page.getByTestId("varroa-review-summary")).toContainText("Suspected cues 1");
  await expect(page.getByTestId("varroa-review-provenance")).toContainText("human_selected");
  await expect(page.getByTestId("varroa-review-provenance")).toContainText(
    "body_occluded_or_hard_to_assess"
  );

  await expect(page.getByTestId("head-up-normalized-bee-crop")).toBeVisible();
  await expect(page.getByTestId("varroa-selected-crop-summary")).toContainText("Crop 1");
  await expect(page.getByTestId("change-varroa-review-crop-button")).toHaveCount(0);
  const cropSelect = page.getByTestId("varroa-review-crop-select");
  await expect(cropSelect).toBeVisible();
  await expect(cropSelect).toHaveValue(/.+/);
  await cropSelect.selectOption(await cropSelect.inputValue());
  await expect(page.getByTestId("training-workflow-stage-varroa-review")).toBeVisible();
  await expect(page.getByTestId("head-up-normalized-bee-head-end")).toHaveCount(0);
  await expect(page.getByTestId("head-up-normalized-bee-crop-image")).toBeVisible();
  await expect(page.getByTestId("head-up-normalized-bee-crop-image-plane")).toHaveAttribute(
    "data-marker-center-x",
    /^0\.\d+/
  );
  await expect(page.getByTestId("varroa-source-crop-context")).toBeVisible();
  await expect(page.getByTestId("varroa-source-context-selected-bee")).toBeVisible();
  const previewBoxBeforeZoom = await page.getByTestId("head-up-normalized-bee-crop").boundingBox();
  const previewPlaneBeforeZoom = await page
    .getByTestId("head-up-normalized-bee-crop-image-plane")
    .boundingBox();
  expect(previewBoxBeforeZoom).not.toBeNull();
  expect(previewPlaneBeforeZoom).not.toBeNull();
  await page.getByTitle("Zoom in").click();
  const previewBoxAfterZoom = await page.getByTestId("head-up-normalized-bee-crop").boundingBox();
  const previewPlaneAfterZoom = await page
    .getByTestId("head-up-normalized-bee-crop-image-plane")
    .boundingBox();
  expect(previewBoxAfterZoom).not.toBeNull();
  expect(previewPlaneAfterZoom).not.toBeNull();
  expect(Math.round(previewBoxAfterZoom!.width)).toBe(Math.round(previewBoxBeforeZoom!.width));
  expect(Math.round(previewBoxAfterZoom!.height)).toBe(Math.round(previewBoxBeforeZoom!.height));
  expect(Math.abs(previewPlaneAfterZoom!.x - previewPlaneBeforeZoom!.x)).toBeLessThan(80);
  expect(previewPlaneAfterZoom!.width).toBeGreaterThan(previewPlaneBeforeZoom!.width);
  await page.getByTestId("head-up-normalized-bee-crop").click({ position: { x: 24, y: 24 } });
  await expect(page.getByTestId("varroa-marker")).toHaveCount(0);
  const markerCenterX = Number(
    await page.getByTestId("head-up-normalized-bee-crop-image-plane").getAttribute("data-marker-center-x")
  );
  const markerCenterY = Number(
    await page.getByTestId("head-up-normalized-bee-crop-image-plane").getAttribute("data-marker-center-y")
  );
  await page.mouse.click(
    previewPlaneAfterZoom!.x + previewPlaneAfterZoom!.width * markerCenterX,
    previewPlaneAfterZoom!.y + previewPlaneAfterZoom!.height * markerCenterY
  );
  await expect(page.getByTestId("varroa-marker")).toHaveCount(1);
  await expect(page.getByTestId("varroa-review-outcome-select")).toHaveValue(
    "visible_varroa_present"
  );
  await page.getByTestId("save-varroa-review-outcome-button").click();

  await expect(page.getByTestId("varroa-review-summary")).toContainText("Visible Varroa bees 1");
  await expect(page.getByTestId("varroa-review-summary")).toContainText("Markers 1");
  await expect(page.getByTestId("workflow-stage-varroa-review-button")).toContainText("1 reviewed");
});
