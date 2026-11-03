import { expect, test } from "@playwright/test";
import {
  createProject,
  login,
  onboard,
  register,
  uniqueEmail,
} from "./helpers";

test("registration, onboarding, logout and unauthorized navigation", async ({
  page,
  isMobile,
}) => {
  const email = uniqueEmail("owner");

  // Registration and login
  await register(page, email);
  await login(page, email);

  // Workspace onboarding
  await onboard(page, "Acme E2E");

  await expect(
    page.getByRole("heading", {
      name: /all workspace projects|projects in/i,
    })
  ).toBeVisible();

  // Mobile navbar
  if (isMobile) {
    const navbarToggle = page.locator(".navbar-toggler");
    const navbarCollapse = page.locator(".navbar-collapse");

    await expect(navbarToggle).toBeVisible();

    console.log("BEFORE CLICK:", {
      collapseClass: await navbarCollapse.getAttribute("class"),
    });

    await navbarToggle.click();

    await expect(navbarCollapse).toHaveClass(/show/);

    console.log("AFTER CLICK:", {
      collapseClass: await navbarCollapse.getAttribute("class"),
    });
  }

  // User dropdown
  const userMenu = page.locator("#user-menu");

  await expect(userMenu).toBeVisible();
  await userMenu.click();

  // Logout
  const logoutButton = page.getByText("Log out", {
    exact: true,
  });

  await expect(logoutButton).toBeVisible();
  await logoutButton.click();

  await expect(page).toHaveURL(/\/login/);

  // Protected route verification
  await page.goto("/app");

  await expect(page).toHaveURL(/\/login/);
});

test("a user from another company cannot reach a project by URL", async ({
  browser,
}) => {
  const contextA = await browser.newContext();
  const pageA = await contextA.newPage();

  const emailA = uniqueEmail("a");

  await register(pageA, emailA);
  await login(pageA, emailA);
  await onboard(pageA, "Company A");
  await createProject(pageA, "Secret", "SEC");

  const projectUrl = pageA.url().replace(/\/board$/, "");

  const contextB = await browser.newContext();
  const pageB = await contextB.newPage();

  const emailB = uniqueEmail("b");

  await register(pageB, emailB);
  await login(pageB, emailB);
  await onboard(pageB, "Company B");

  await pageB.goto(projectUrl);

  await expect(
    pageB.getByText(/not found or you do not have access/i)
  ).toBeVisible();

  await contextA.close();
  await contextB.close();
});

test("password reset page rejects an incomplete link", async ({ page }) => {
  await page.goto("/reset-password");

  await expect(
    page.getByText(/incomplete/i)
  ).toBeVisible();
});

test("responsive: mobile layout collapses the navigation", async ({
  page,
  isMobile,
}) => {
  test.skip(!isMobile, "Mobile project only");

  const email = uniqueEmail("m");

  await register(page, email);
  await login(page, email);
  await onboard(page, "Mobile Co");

  await expect(
    page.locator(".navbar-toggler")
  ).toBeVisible();

  await expect(
    page.locator(".navbar-collapse")
  ).not.toHaveClass(/show/);
});
