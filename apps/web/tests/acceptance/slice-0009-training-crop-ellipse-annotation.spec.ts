import { expect, type Page, test } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { createApiaryAndHive } from "./support/setup-workflow";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test("Dataset Curator creates a crop, adds an oriented bee ellipse, and completes review", async ({
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
  await createApiaryAndHive(page, `Slice 9 apiary ${suffix}`, `Slice 9 hive ${suffix}`);

  await page.getByTestId("inspection-date-input").fill("2026-07-30");
  await page.getByTestId("inspection-intent-select").selectOption("training_data_collection");
  await page.getByTestId("create-inspection-button").click();
  await expect(page.getByTestId("inspection-intent-badge")).toContainText(
    "Training data collection"
  );

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("training-crop-panel")).toBeVisible();
  await expect(page.getByTestId("training-source-image")).toBeVisible();
  await expect.poll(() => sourcePhotoPreviewShowsWholeImage(page)).toBe(true);

  await page.getByTestId("training-source-photo-preview").click({ position: { x: 180, y: 120 } });
  await expect(page.getByTestId("training-draft-crop-overlay")).toBeVisible();
  await page.getByTestId("save-training-crop-button").click();
  await expect(page.getByTestId("training-crop-list-item")).toHaveCount(1);

  const initialCropSurfaceBox = await page.getByTestId("training-crop-surface").boundingBox();
  expect(initialCropSurfaceBox).not.toBeNull();
  await expect(page.getByTestId("crop-zoom-slider")).toHaveValue("1");
  await page.getByTestId("crop-zoom-in-button").click();
  await expect(page.getByTestId("crop-zoom-slider")).toHaveValue("1.25");
  const zoomedCropSurfaceBox = await page.getByTestId("training-crop-surface").boundingBox();
  expect(zoomedCropSurfaceBox).not.toBeNull();
  expect(zoomedCropSurfaceBox!.width).toBeGreaterThan(initialCropSurfaceBox!.width);
  await page.getByTestId("crop-pan-right-button").click();
  await expect.poll(() => cropImageIsClippedToSurface(page)).toBe(true);
  await page.getByTestId("crop-zoom-reset-button").click();
  await expect(page.getByTestId("crop-zoom-slider")).toHaveValue("1");

  await page.getByTestId("training-crop-surface").click({ position: { x: 180, y: 120 } });
  await expect(page.getByTestId("training-crop-ellipse")).toHaveCount(1);
  await expect(page.getByTestId("training-ellipse-head-direction-reliable-checkbox")).toBeChecked();
  await expect.poll(() => headShadingIsObvious(page)).toBe(true);

  await page.getByTestId("training-ellipse-type-select").selectOption("partial_visible_bee");
  await expect(page.getByTestId("selected-training-ellipse-label")).toContainText(
    "partial_visible_bee"
  );
  const boundaryStartX = await readGeometryValue(page, "training-ellipse-center-x");
  const boundaryStartRadiusX = await readGeometryValue(page, "training-ellipse-radius-x");
  const crossBoundaryClicks = Math.max(1, Math.ceil((boundaryStartX - boundaryStartRadiusX + 5) / 5));
  for (let index = 0; index < crossBoundaryClicks; index += 1) {
    await page.getByTestId("nudge-training-ellipse-left-button").click();
  }
  await expect
    .poll(() => readGeometryValue(page, "training-ellipse-center-x"))
    .toBeLessThan(boundaryStartRadiusX);
  for (let index = 0; index < crossBoundaryClicks; index += 1) {
    await page.getByTestId("nudge-training-ellipse-right-button").click();
  }
  await expectGeometryValue(page, "training-ellipse-center-x", boundaryStartX);
  await page.getByTestId("training-ellipse-type-select").selectOption("complete_visible_bee");

  const cropSurfaceBox = await page.getByTestId("training-crop-surface").boundingBox();
  const cropViewportBox = await page.getByTestId("training-crop-surface-viewport").boundingBox();
  const controlsBox = await page.getByTestId("training-crop-review-controls").boundingBox();
  const metricsBox = await page.getByTestId("training-crop-metrics").boundingBox();
  expect(cropSurfaceBox).not.toBeNull();
  expect(cropViewportBox).not.toBeNull();
  expect(controlsBox).not.toBeNull();
  expect(metricsBox).not.toBeNull();
  expect(controlsBox!.width).toBeGreaterThan(280);
  expect(metricsBox!.y).toBeGreaterThan(
    Math.max(cropViewportBox!.y + cropViewportBox!.height, controlsBox!.y + controlsBox!.height) - 1
  );

  const initialX = await readGeometryValue(page, "training-ellipse-center-x");
  const initialY = await readGeometryValue(page, "training-ellipse-center-y");
  const initialRadiusX = await readGeometryValue(page, "training-ellipse-radius-x");
  const initialRadiusY = await readGeometryValue(page, "training-ellipse-radius-y");
  const initialRotation = await readGeometryValue(page, "training-ellipse-rotation");

  await page.getByTestId("nudge-training-ellipse-left-button").click();
  await expectGeometryValue(page, "training-ellipse-center-x", initialX - 5);
  await page.getByTestId("nudge-training-ellipse-right-button").click();
  await expectGeometryValue(page, "training-ellipse-center-x", initialX);
  const repeatStartX = await readGeometryValue(page, "training-ellipse-center-x");
  const rightNudgeBox = await page.getByTestId("nudge-training-ellipse-right-button").boundingBox();
  expect(rightNudgeBox).not.toBeNull();
  await page.mouse.move(
    rightNudgeBox!.x + rightNudgeBox!.width / 2,
    rightNudgeBox!.y + rightNudgeBox!.height / 2
  );
  await page.mouse.down();
  await page.waitForTimeout(750);
  await page.mouse.up();
  await expect
    .poll(() => readGeometryValue(page, "training-ellipse-center-x"))
    .toBeGreaterThan(repeatStartX + 5);

  await page.getByTestId("nudge-training-ellipse-up-button").click();
  await expectGeometryValue(page, "training-ellipse-center-y", initialY - 5);
  await page.getByTestId("nudge-training-ellipse-down-button").click();
  await expectGeometryValue(page, "training-ellipse-center-y", initialY);

  await page.getByTestId("shrink-training-ellipse-x-button").click();
  await expectGeometryValue(page, "training-ellipse-radius-x", initialRadiusX - 5);
  await page.getByTestId("grow-training-ellipse-x-button").click();
  await expectGeometryValue(page, "training-ellipse-radius-x", initialRadiusX);

  await page.getByTestId("shrink-training-ellipse-y-button").click();
  await expectGeometryValue(page, "training-ellipse-radius-y", initialRadiusY - 5);
  await page.getByTestId("grow-training-ellipse-y-button").click();
  await expectGeometryValue(page, "training-ellipse-radius-y", initialRadiusY);

  await page.getByTestId("rotate-training-ellipse-button").click();
  await expectGeometryValue(page, "training-ellipse-rotation", initialRotation + 5);
  await expect(page.getByTestId("training-crop-review-controls")).toContainText(
    "5 degree head direction"
  );
  await page.getByTestId("rotate-training-ellipse-anticlockwise-button").click();
  await expectGeometryValue(page, "training-ellipse-rotation", initialRotation);
  await page.getByTestId("flip-training-ellipse-head-tail-button").click();
  await expectGeometryValue(page, "training-ellipse-rotation", initialRotation + 180);
  await expect(page.getByTestId("training-crop-ellipse")).toHaveAttribute(
    "aria-label",
    /head direction 180 degrees/
  );
  await page.getByTestId("training-ellipse-head-direction-reliable-checkbox").uncheck();
  await expect(page.getByTestId("training-ellipse-head-direction-reliable-checkbox")).not.toBeChecked();

  await expect(page.getByTestId("training-crop-visible-status-select")).toHaveValue(
    "has_visible_bees"
  );
  await page.getByTestId("complete-training-crop-button").click();
  await expect(page.getByTestId("training-crop-list-item")).toContainText("review_complete");
  await expect(page.getByTestId("training-crop-list-item")).toContainText("has_visible_bees");
  await expect(page.getByTestId("delete-training-ellipse-button")).toBeDisabled();
  await page.getByTestId("workflow-stage-crop-governance-button").click();
  await expect(page.getByTestId("crop-governance-orientation-reliable-count")).toContainText(
    "Head direction reliable 0"
  );
  await expect(page.getByTestId("crop-governance-orientation-unreliable-count")).toContainText(
    "Orientation export excluded 1"
  );
  await page.getByTestId("workflow-stage-bee-annotation-button").click();
  await page.getByTestId("reopen-training-crop-button").click();
  await expect(page.getByTestId("training-crop-list-item")).toContainText("review_pending");
  await expect(page.getByTestId("delete-training-ellipse-button")).toBeEnabled();
});

async function readGeometryValue(page: Page, testId: string): Promise<number> {
  const text = await page.getByTestId(testId).innerText();
  const value = Number(text);
  expect(Number.isFinite(value)).toBe(true);
  return value;
}

async function cropImageIsClippedToSurface(page: Page): Promise<boolean> {
  return page.getByTestId("training-crop-surface").evaluate((surface) => {
    const image = surface.querySelector("img");
    if (!image) {
      return false;
    }
    const surfaceStyle = window.getComputedStyle(surface);
    const surfaceBox = surface.getBoundingClientRect();
    const imageBox = image.getBoundingClientRect();
    return (
      surfaceStyle.overflow === "hidden" &&
      imageBox.width >= surfaceBox.width &&
      imageBox.height >= surfaceBox.height
    );
  });
}

async function sourcePhotoPreviewShowsWholeImage(page: Page): Promise<boolean> {
  return page.getByTestId("training-source-photo-preview").evaluate((preview) => {
    const image = preview.querySelector("img");
    if (!image) {
      return false;
    }
    const previewBox = preview.getBoundingClientRect();
    const imageBox = image.getBoundingClientRect();
    return previewBox.height + 1 >= imageBox.height;
  });
}

async function headShadingIsObvious(page: Page): Promise<boolean> {
  return page.getByTestId("training-crop-ellipse").evaluate((ellipse) => {
    const marker = ellipse.querySelector(".ellipse-head-arrow");
    const style = window.getComputedStyle(ellipse);
    const markerStyle = marker ? window.getComputedStyle(marker) : null;
    return (
      style.backgroundImage.includes("255, 215, 64") &&
      style.backgroundImage.includes("linear-gradient") &&
      markerStyle?.display === "none"
    );
  });
}

async function expectGeometryValue(
  page: Page,
  testId: string,
  expectedValue: number
): Promise<void> {
  await expect.poll(() => readGeometryValue(page, testId)).toBe(expectedValue);
}
