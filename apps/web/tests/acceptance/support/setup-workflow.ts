import { expect, type Page } from "@playwright/test";

export async function createApiary(page: Page, name: string) {
  const form = page.getByTestId("apiary-setup-form");
  if ((await form.count()) === 0 || !(await form.isVisible())) {
    await page.getByTestId("show-apiary-setup-button").click();
  }
  await expect(form).toBeVisible();
  await page.getByTestId("apiary-name-input").fill(name);
  await page.getByTestId("create-apiary-button").click();
  await expect(page.getByTestId("selected-apiary-summary")).toContainText(name);
}

export async function createHive(page: Page, name: string) {
  const form = page.getByTestId("hive-setup-form");
  const showFormButton = page.getByTestId("show-hive-setup-button");
  await expect
    .poll(async () => {
      if ((await form.count()) > 0 && (await form.isVisible())) {
        return "form";
      }
      if ((await showFormButton.count()) > 0 && (await showFormButton.isVisible())) {
        return "button";
      }
      return "waiting";
    })
    .not.toBe("waiting");
  if (!(await form.isVisible())) {
    await showFormButton.click();
  }
  await expect(form).toBeVisible();
  await page.getByTestId("hive-name-input").fill(name);
  await page.getByTestId("create-hive-button").click();
  await expect(page.getByTestId("hive-list")).toContainText(name);
}

export async function createApiaryAndHive(page: Page, apiaryName: string, hiveName: string) {
  await createApiary(page, apiaryName);
  await createHive(page, hiveName);
}
