# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth-and-tenancy.spec.js >> registration, onboarding, logout and unauthorized navigation
- Location: e2e\auth-and-tenancy.spec.js:4:1

# Error details

```
Test timeout of 60000ms exceeded.
```

```
Error: locator.click: Test timeout of 60000ms exceeded.
Call log:
  - waiting for getByRole('button', { name: 'owner+1793531715927499@e2e.test' })

```

# Page snapshot

```yaml
- generic [ref=f1e2]:
  - navigation [ref=f1e3]:
    - generic [ref=f1e4]:
      - link "Tech Task home" [ref=f1e6] [cursor=pointer]:
        - /url: /app
        - img "Tech Task logo" [ref=f1e7]
        - generic [ref=f1e13]: Tech Task
      - button "Toggle navigation" [ref=f1e14] [cursor=pointer]
  - generic [ref=f1e17]:
    - navigation "Workspace" [ref=f1e18]:
      - link "Dashboard" [ref=f1e19] [cursor=pointer]:
        - /url: /app
      - link "Notifications" [ref=f1e20] [cursor=pointer]:
        - /url: /app/notifications
      - link "Workspace settings" [ref=f1e21] [cursor=pointer]:
        - /url: /app/settings
      - link "Billing" [ref=f1e22] [cursor=pointer]:
        - /url: /app/billing
      - link "Profile" [ref=f1e23] [cursor=pointer]:
        - /url: /app/profile
    - main [ref=f1e24]:
      - generic [ref=f1e26]:
        - generic [ref=f1e27]:
          - heading "Welcome, owner+1793531715927499" [level=1] [ref=f1e28]
          - paragraph [ref=f1e29]:
            - text: "Workspace:"
            - strong [ref=f1e30]: Acme E2E
            - text: "· Role:"
            - generic [ref=f1e31]: owner
        - generic [ref=f1e32]:
          - button "+ New project" [ref=f1e33] [cursor=pointer]
          - link "Workspace settings" [ref=f1e34] [cursor=pointer]:
            - /url: /app/settings
      - generic [ref=f1e35]:
        - generic [ref=f1e38]:
          - generic [ref=f1e39]: Total Projects
          - generic [ref=f1e40]: "0"
          - generic [ref=f1e41]: 0 active
        - generic [ref=f1e44]:
          - generic [ref=f1e45]: Assigned To Me
          - generic [ref=f1e46]: "0"
          - text: Tasks across projects
        - generic [ref=f1e49]:
          - generic [ref=f1e50]: Team Members
          - generic [ref=f1e51]: "1"
          - text: In this workspace
        - generic [ref=f1e54]:
          - generic [ref=f1e55]: Recent Alerts
          - generic [ref=f1e56]: "0"
          - link "View notifications" [ref=f1e58] [cursor=pointer]:
            - /url: /app/notifications
      - generic [ref=f1e59]:
        - generic [ref=f1e60]:
          - tablist [ref=f1e61]:
            - tab "Projects (0)" [selected] [ref=f1e62] [cursor=pointer]
            - tab "My Tasks (0)" [ref=f1e63] [cursor=pointer]
            - tab "Activity Feed" [ref=f1e64] [cursor=pointer]
          - tabpanel "Projects (0)" [ref=f1e66]:
            - generic [ref=f1e67]:
              - heading "All Workspace Projects" [level=2] [ref=f1e68]
              - generic [ref=f1e69]:
                - combobox "Filter status" [ref=f1e70]:
                  - option "All statuses" [selected]
                  - option "Active"
                  - option "Archived"
                - textbox "Search projects" [ref=f1e71]:
                  - /placeholder: Filter by name…
            - generic [ref=f1e72]:
              - heading "No projects found" [level=2] [ref=f1e73]
              - generic [ref=f1e74]: Create your first project to begin organizing work.
        - generic [ref=f1e75]:
          - generic [ref=f1e76]:
            - generic [ref=f1e77]: Quick Actions
            - generic [ref=f1e78]:
              - button "➕ Create New Project" [ref=f1e79] [cursor=pointer]
              - link "🔔 View Notifications (0)" [ref=f1e80] [cursor=pointer]:
                - /url: /app/notifications
              - link "⚙️ Workspace Settings & Team" [ref=f1e81] [cursor=pointer]:
                - /url: /app/settings
              - link "💳 Subscription & Plan" [ref=f1e82] [cursor=pointer]:
                - /url: /app/billing
              - link "👤 My Profile Settings" [ref=f1e83] [cursor=pointer]:
                - /url: /app/profile
          - generic [ref=f1e84]:
            - generic [ref=f1e85]:
              - generic [ref=f1e86]: Workspace Members
              - link "Manage" [ref=f1e87] [cursor=pointer]:
                - /url: /app/settings
            - generic [ref=f1e90]:
              - generic [ref=f1e91]: owner+1793531715927499@e2e.test
              - generic [ref=f1e92]: owner
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
  9  |   await expect(page.getByRole("heading", { name: /all workspace projects/i })).toBeVisible();
  10 | 
> 11 |   await page.getByRole("button", { name: email }).click();
     |                                                   ^ Error: locator.click: Test timeout of 60000ms exceeded.
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
  44 | 
  45 | 
```