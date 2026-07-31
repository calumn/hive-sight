import { expect, test, type Page } from "@playwright/test";
import { fileURLToPath } from "node:url";

const fixtureImagePath = fileURLToPath(new URL("../fixtures/bee-frame-test.png", import.meta.url));

test("Dataset Curator resumes saved Training Inspection crops and ellipses after reload", async ({
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
  const apiaryName = ` Slice 17 apiary ${suffix}`;
  const hiveName = ` Slice 17 hive ${suffix}`;

  await page.getByTestId("apiary-name-input").fill(apiaryName);
  await page.getByTestId("create-apiary-button").click();
  await page.getByTestId("hive-name-input").fill(hiveName);
  await page.getByTestId("create-hive-button").click();

  await page.getByTestId("inspection-date-input").fill("2026-07-31");
  await page.getByTestId("inspection-intent-select").selectOption("training_data_collection");
  await page.getByTestId("create-inspection-button").click();
  await expect(page.getByTestId("resume-training-inspection-select")).toContainText(
    "2026-07-31 / Training data collection"
  );

  await page.getByTestId("inspection-photo-input").setInputFiles(fixtureImagePath);
  await page.getByTestId("upload-photo-button").click();
  await expect(page.getByTestId("training-crop-panel")).toBeVisible();

  await page.getByTestId("training-source-photo-preview").click({ position: { x: 180, y: 120 } });
  await page.getByTestId("save-training-crop-button").click();
  await expect(page.getByTestId("training-crop-list-item")).toHaveCount(1);
  await page.getByTestId("training-crop-surface").click({ position: { x: 180, y: 120 } });
  await expect(page.getByTestId("training-crop-ellipse")).toHaveCount(1);
  const savedCenterX = await readGeometryValue(page, "training-ellipse-center-x");

  await page.reload();
  await expect(page.getByText("core-api online")).toBeVisible();
  await expect(page.getByTestId("apiary-select")).toContainText(apiaryName);
  await expect(page.getByTestId("hive-select")).toContainText(hiveName);
  await expect(page.getByTestId("resume-training-inspection-select")).toContainText(
    "2026-07-31 / Training data collection"
  );
  await expect(page.getByTestId("inspection-photo-list")).toContainText("bee-frame-test.png");
  await expect(page.getByTestId("training-crop-panel")).toBeVisible();
  await expect(page.getByTestId("training-crop-list-item")).toContainText("review_pending");
  await expect(page.getByTestId("training-crop-ellipse")).toHaveCount(1);
  await page.getByTestId("training-crop-ellipse").click();
  await expectGeometryValue(page, "training-ellipse-center-x", savedCenterX);

  await page.getByTestId("nudge-training-ellipse-right-button").click();
  await expectGeometryValue(page, "training-ellipse-center-x", savedCenterX + 5);
});

async function readGeometryValue(page: Page, testId: string): Promise<number> {
  const text = await page.getByTestId(testId).innerText();
  const value = Number(text);
  expect(Number.isFinite(value)).toBe(true);
  return value;
}

async function expectGeometryValue(
  page: Page,
  testId: string,
  expectedValue: number
): Promise<void> {
  await expect.poll(() => readGeometryValue(page, testId)).toBe(expectedValue);
}
