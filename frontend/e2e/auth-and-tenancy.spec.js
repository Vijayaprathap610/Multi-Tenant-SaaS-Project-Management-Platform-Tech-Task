import { expect, test } from "@playwright/test";
import { createProject, login, onboard, register, uniqueEmail } from "./helpers";

test("registration, onboarding, logout and unauthorized navigation", async ({ page }) => {
  const email = uniqueEmail("owner");
  await register(page, email);
  await login(page, email);
  await onboard(page, "Acme E2E");
  await expect(page.getByRole("heading", { name: /projects in acme e2e/i })).toBeVisible();

  await page.getByRole("button", { name: email }).click();
  await page.getByText("Log out", { exact: true }).click();
  await expect(page).toHaveURL(/\/login/);
  await page.goto("/app");
  await expect(page).toHaveURL(/\/login/);       // unauthenticated navigation is redirected
});

test("a user from another company cannot reach a project by URL", async ({ browser }) => {
  const a = await (await browser.newContext()).newPage();
  const emailA = uniqueEmail("a");
  await register(a, emailA); await login(a, emailA); await onboard(a, "Company A");
  await createProject(a, "Secret", "SEC");
  const projectUrl = a.url().replace(/\/board$/, "");

  const b = await (await browser.newContext()).newPage();
  const emailB = uniqueEmail("b");
  await register(b, emailB); await login(b, emailB); await onboard(b, "Company B");
  await b.goto(projectUrl);
  await expect(b.getByText(/not found or you do not have access/i)).toBeVisible();
});

test("password reset page rejects an incomplete link", async ({ page }) => {
  await page.goto("/reset-password");
  await expect(page.getByText(/incomplete/i)).toBeVisible();
});

test("responsive: mobile layout collapses the navigation", async ({ page, isMobile }) => {
  test.skip(!isMobile, "mobile project only");
  const email = uniqueEmail("m");
  await register(page, email); await login(page, email); await onboard(page, "Mobile Co");
  await expect(page.getByRole("button", { name: /toggle navigation/i })).toBeVisible();
});
