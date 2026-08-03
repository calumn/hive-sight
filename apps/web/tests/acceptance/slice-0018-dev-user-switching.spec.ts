import { expect, test } from "@playwright/test";

test("Development User switching reloads the selected User workspace and hides impossible capabilities", async ({
  page
}) => {
  await page.goto("/");
  await expect(page.getByText("core-api online")).toBeVisible();

  const userSelect = page.getByTestId("development-user-select");
  await expect(userSelect).toBeVisible();
  await expect(page.getByTestId("development-user-code")).toContainText("DEV-OWNER-CURATOR");
  await expect(page.getByTestId("bee-annotation-repository-page-button")).toBeVisible();

  await userSelect.selectOption("00000000-0000-0000-0000-000000000102");
  await expect(page.getByTestId("development-user-code")).toContainText("OWNER-A");
  await expect(page.getByTestId("development-user-capabilities")).toContainText("None");
  await expect(page.getByTestId("apiary-select")).toContainText("Owner A Apiary");
  await expect(page.getByTestId("apiary-select")).not.toContainText("Dev Owner Curator Apiary");
  await expect(page.getByTestId("hive-select")).toContainText("Owner A Hive");
  await expect(page.getByTestId("bee-annotation-repository-page-button")).toHaveCount(0);
  await expect(page.getByTestId("review-work-page-button")).toHaveCount(0);

  await userSelect.selectOption("00000000-0000-0000-0000-000000000104");
  await expect(page.getByTestId("development-user-code")).toContainText("CURATOR-1");
  await expect(page.getByTestId("development-user-capabilities")).toContainText(
    "Dataset Curator"
  );
  await expect(page.getByTestId("apiary-select")).toContainText("Dataset Curator Apiary");
  await expect(page.getByTestId("bee-annotation-repository-page-button")).toBeVisible();
  await expect(page.getByTestId("review-work-page-button")).toHaveCount(0);

  await userSelect.selectOption("00000000-0000-0000-0000-000000000105");
  await expect(page.getByTestId("development-user-code")).toContainText("REVIEWER-1");
  await expect(page.getByTestId("development-user-capabilities")).toContainText("Reviewer");
  await expect(page.getByTestId("bee-annotation-repository-page-button")).toHaveCount(0);
  await expect(page.getByTestId("review-work-page-button")).toBeVisible();

  await page.reload();
  await expect(page.getByText("core-api online")).toBeVisible();
  await expect(page.getByTestId("development-user-code")).toContainText("REVIEWER-1");
  await expect(userSelect).toHaveValue("00000000-0000-0000-0000-000000000105");
});
