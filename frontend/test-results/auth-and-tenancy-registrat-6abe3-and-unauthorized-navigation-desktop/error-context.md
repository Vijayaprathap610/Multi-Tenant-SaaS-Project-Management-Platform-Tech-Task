# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth-and-tenancy.spec.js >> registration, onboarding, logout and unauthorized navigation
- Location: e2e\auth-and-tenancy.spec.js:4:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('heading', { name: /projects in acme e2e/i })
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByRole('heading', { name: /projects in acme e2e/i }) with timeout 5000ms
  - waiting for getByRole('heading', { name: /projects in acme e2e/i })

```

```yaml
- navigation:
  - link "Tech Task home":
    - /url: /app
    - img "Tech Task logo"
    - text: Tech Task
  - button "Switch workspace": Acme E2E
  - link "Notifications, 0 unread":
    - /url: /app/notifications
    - text: Notifications
  - button "owner+1793527166831574@e2e.test"
- navigation "Workspace":
  - link "Dashboard":
    - /url: /app
  - link "Notifications":
    - /url: /app/notifications
  - link "Workspace settings":
    - /url: /app/settings
  - link "Billing":
    - /url: /app/billing
  - link "Profile":
    - /url: /app/profile
- main:
  - heading "Welcome, owner+1793527166831574" [level=1]
  - paragraph:
    - text: "Workspace:"
    - strong: Acme E2E
    - text: "· Role: owner"
  - button "+ New project"
  - link "Workspace settings":
    - /url: /app/settings
  - text: Total Projects 0 0 active Assigned To Me 0 Tasks across projects Team Members 1 In this workspace Recent Alerts 0
  - link "View notifications":
    - /url: /app/notifications
  - tablist:
    - tab "Projects (0)" [selected]
    - tab "My Tasks (0)"
    - tab "Activity Feed"
  - tabpanel "Projects (0)":
    - heading "All Workspace Projects" [level=2]
    - combobox "Filter status":
      - option "All statuses" [selected]
      - option "Active"
      - option "Archived"
    - textbox "Search projects":
      - /placeholder: Filter by name…
    - heading "No projects found" [level=2]
    - text: Create your first project to begin organizing work.
  - text: Quick Actions
  - button "➕ Create New Project"
  - link "🔔 View Notifications (0)":
    - /url: /app/notifications
  - link "⚙️ Workspace Settings & Team":
    - /url: /app/settings
  - link "💳 Subscription & Plan":
    - /url: /app/billing
  - link "👤 My Profile Settings":
    - /url: /app/profile
  - text: Workspace Members
  - link "Manage":
    - /url: /app/settings
  - text: owner+1793527166831574@e2e.test owner
```

# Test source

```ts
  1  | import { expect, test } from "@playwright/test";
  2  | import { createProject, login, onboard, register, uniqueEmail } from "./helpers";
  3  | 
  4  | test("registration, onboarding, logout and unauthorized navigation", async ({ page }) => {
  5  |   const email = uniqueEmail("owner");
  6  |   await register(page, email);
  7  |   await login(page, email);
  8  |   await onboard(page, "Acme E2E");
> 9  |   await expect(page.getByRole("heading", { name: /projects in acme e2e/i })).toBeVisible();
     |                                                                              ^ Error: expect(locator).toBeVisible() failed
  10 | 
  11 |   await page.getByRole("button", { name: email }).click();
  12 |   await page.getByText("Log out", { exact: true }).click();
  13 |   await expect(page).toHaveURL(/\/login/);
  14 |   await page.goto("/app");
  15 |   await expect(page).toHaveURL(/\/login/);       // unauthenticated navigation is redirected
  16 | });
  17 | 
  18 | test("a user from another company cannot reach a project by URL", async ({ browser }) => {
  19 |   const a = await (await browser.newContext()).newPage();
  20 |   const emailA = uniqueEmail("a");
  21 |   await register(a, emailA); await login(a, emailA); await onboard(a, "Company A");
  22 |   await createProject(a, "Secret", "SEC");
  23 |   const projectUrl = a.url().replace(/\/board$/, "");
  24 | 
  25 |   const b = await (await browser.newContext()).newPage();
  26 |   const emailB = uniqueEmail("b");
  27 |   await register(b, emailB); await login(b, emailB); await onboard(b, "Company B");
  28 |   await b.goto(projectUrl);
  29 |   await expect(b.getByText(/not found or you do not have access/i)).toBeVisible();
  30 | });
  31 | 
  32 | test("password reset page rejects an incomplete link", async ({ page }) => {
  33 |   await page.goto("/reset-password");
  34 |   await expect(page.getByText(/incomplete/i)).toBeVisible();
  35 | });
  36 | 
  37 | test("responsive: mobile layout collapses the navigation", async ({ page, isMobile }) => {
  38 |   test.skip(!isMobile, "mobile project only");
  39 |   const email = uniqueEmail("m");
  40 |   await register(page, email); await login(page, email); await onboard(page, "Mobile Co");
  41 |   await expect(page.getByRole("button", { name: /toggle navigation/i })).toBeVisible();
  42 | });
  43 | 
```