import { expect, test } from "@playwright/test";

test("landing page explains the product and reaches registration", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Ask your archive. Verify every answer." })).toBeVisible();
  await expect(page.getByText("Evidence attached")).toBeVisible();
  await page.getByRole("link", { name: "Create free account" }).click();
  await expect(page).toHaveURL(/\/register$/);
  await expect(page.getByRole("heading", { name: "Create account" })).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
});

test("login form exposes accessible controls", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Log in" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Log in" })).toBeEnabled();
});

