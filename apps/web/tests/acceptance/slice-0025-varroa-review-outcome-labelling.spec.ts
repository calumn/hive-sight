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
  await page.getByTestId("training-crop-surface").click({ position: { x: 320, y: 220 } });
  await expect(page.getByTestId("training-crop-ellipse")).toHaveCount(2);
  await page.getByTestId("training-crop-surface").click({ position: { x: 80, y: 80 } });
  await expect(page.getByTestId("training-crop-ellipse")).toHaveCount(3);
  await page.getByTestId("training-ellipse-type-select").selectOption("partial_visible_bee");
  await page.getByTestId("complete-training-crop-button").click();

  await page.getByTestId("workflow-stage-varroa-review-button").click();
  await expect(page.getByTestId("training-workflow-stage-varroa-review")).toBeVisible();
  await expect(page.getByTestId("varroa-review-summary")).toContainText("Suspected cues 1");
  await expect(page.getByTestId("varroa-review-candidate")).toHaveCount(2);
  await expect(page.getByTestId("varroa-review-hidden-ineligible-count")).toContainText(
    "1 ineligible bee is hidden"
  );
  await expect(page.getByTestId("include-ineligible-varroa-bees-checkbox")).not.toBeChecked();
  await page.getByRole("option", { name: /suspected/ }).click();
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
  await expect(page.getByTestId("head-up-normalized-bee-crop-clean")).toBeVisible();
  await expect(page.getByTestId("head-up-normalized-bee-crop-clean-image")).toBeVisible();
  await expect(page.getByTestId("varroa-review-place-marker-mode-button")).toHaveClass(/active/);
  await expect(page.getByText("Zoom 300%")).toBeVisible();
  await expect(page.getByTestId("varroa-detector-preview-panel")).toContainText(
    "No model preview run for this bee"
  );
  await page.getByTestId("run-varroa-detector-preview-button").click();
  await expect(page.getByTestId("varroa-detector-preview-details")).toContainText(
    "varroa_detection"
  );
  await expect(page.getByTestId("varroa-detector-preview-details")).toContainText(
    "deterministic_stub"
  );
  await expect(page.getByTestId("varroa-detector-preview-box")).toHaveCount(1);
  await expect(
    page
      .getByTestId("head-up-normalized-bee-crop-clean")
      .getByTestId("varroa-detector-preview-box")
  ).toHaveCount(0);
  await page.getByTestId("varroa-review-pan-mode-button").click();
  await expect(page.getByTestId("varroa-review-pan-mode-button")).toHaveClass(/active/);
  const cleanSurface = page.getByTestId("head-up-normalized-bee-crop-clean");
  const cleanBox = await cleanSurface.boundingBox();
  expect(cleanBox).not.toBeNull();
  await page.mouse.move(cleanBox!.x + cleanBox!.width / 2, cleanBox!.y + cleanBox!.height / 2);
  await page.mouse.down();
  await page.mouse.move(cleanBox!.x + cleanBox!.width / 2 + 40, cleanBox!.y + cleanBox!.height / 2 + 20);
  await page.mouse.up();
  await expect(cleanSurface).not.toHaveAttribute("data-pan-x", "0");
  await expect(page.getByTestId("head-up-normalized-bee-crop")).toHaveAttribute(
    "data-pan-x",
    await cleanSurface.getAttribute("data-pan-x") ?? ""
  );
  await page.getByTestId("varroa-review-place-marker-mode-button").click();
  await expect(page.getByTestId("varroa-source-crop-context")).toBeVisible();
  await expect(page.getByTestId("varroa-source-context-selected-bee")).toBeVisible();
  await expect(page.getByTestId("varroa-source-context-bee")).toHaveCount(1);
  await page.getByTestId("include-ineligible-varroa-bees-checkbox").check();
  await expect(page.getByTestId("varroa-review-candidate")).toHaveCount(3);
  await expect(page.getByRole("option", { name: /ineligible/ })).toBeVisible();
  await expect(page.getByTestId("varroa-source-context-bee")).toHaveCount(2);
  await page.getByTestId("varroa-source-context-bee").first().click();
  await expect(page.getByTestId("varroa-source-context-selected-bee")).toHaveCount(1);
  await expect(page.getByTestId("varroa-detector-preview-box")).toHaveCount(0);
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
  await expect(page.getByTestId("photo-visible-varroa-summary")).toContainText(
    "Photo-visible Varroa evidence"
  );
  await expect(page.getByTestId("photo-visible-varroa-summary")).toContainText(
    "Visible Varroa bees 1"
  );
  await expect(page.getByTestId("photo-visible-varroa-summary")).toContainText(
    "Visible mite markers 1"
  );
  await expect(page.getByTestId("photo-visible-varroa-summary")).toContainText(
    "Active negatives 0"
  );
  await expect(page.getByTestId("photo-visible-varroa-summary")).toContainText(
    "Determinate coverage"
  );
  await expect(page.getByTestId("photo-visible-varroa-readiness")).toContainText(
    "Advisor context available with caveats"
  );
  await expect(page.getByTestId("photo-visible-varroa-caveats")).toContainText(
    "Photo-visible evidence only; not treatment advice."
  );
  await expect(page.getByTestId("workflow-stage-varroa-review-button")).toContainText("1 reviewed");
});
