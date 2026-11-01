# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: kanban.spec.js >> Kanban drag and drop >> keyboard users can move a card
- Location: e2e\kanban.spec.js:42:3

# Error details

```
Error: locator.click: Error: strict mode violation: getByRole('button', { name: /new project/i }) resolved to 2 elements:
    1) <button type="button" class="btn btn-primary btn-sm">+ New project</button> aka getByRole('button', { name: '+ New project' })
    2) <button type="button" class="text-start btn btn-outline-primary btn-sm">➕ Create New Project</button> aka getByRole('button', { name: '➕ Create New Project' })

Call log:
  - waiting for getByRole('button', { name: /new project/i })

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
          - heading "Welcome, kbd+1793527173364719" [level=1] [ref=f1e28]
          - paragraph [ref=f1e29]:
            - text: "Workspace:"
            - strong [ref=f1e30]: Keyboard Co
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
              - generic [ref=f1e91]: kbd+1793527173364719@e2e.test
              - generic [ref=f1e92]: owner
```

# Test source

```ts
  1  | import { expect } from "@playwright/test";
  2  | 
  3  | export const PASSWORD = "Pw-Str0ng-e2e-1!";
  4  | export const uniqueEmail = (tag) => `${tag}+${Date.now()}${Math.floor(Math.random() * 1000)}@e2e.test`;
  5  | 
  6  | export async function register(page, email) {
  7  |   await page.goto("/register");
  8  |   await page.getByLabel(/^email/i).fill(email);
  9  |   await page.getByLabel(/^password$/i).fill(PASSWORD);
  10 |   await page.getByLabel(/confirm password/i).fill(PASSWORD);
  11 |   await page.getByRole("button", { name: /create account/i }).click();
  12 |   await expect(page).toHaveURL(/\/login/);
  13 | }
  14 | 
  15 | export async function login(page, email) {
  16 |   await page.goto("/login");
  17 |   await page.getByLabel(/^email/i).fill(email);
  18 |   await page.getByLabel(/^password/i).fill(PASSWORD);
  19 |   await page.getByRole("button", { name: /^log in$/i }).click();
  20 | }
  21 | 
  22 | export async function onboard(page, workspaceName) {
  23 |   await expect(page).toHaveURL(/\/onboarding/);
  24 |   await page.getByLabel(/workspace name/i).fill(workspaceName);
  25 |   await page.getByRole("button", { name: /create workspace/i }).click();
  26 |   await expect(page).toHaveURL(/\/app$/);
  27 | }
  28 | 
  29 | export async function createProject(page, name, key) {
> 30 |   await page.getByRole("button", { name: /new project/i }).click();
     |                                                            ^ Error: locator.click: Error: strict mode violation: getByRole('button', { name: /new project/i }) resolved to 2 elements:
  31 |   await page.getByLabel(/^name/i).fill(name);
  32 |   await page.getByLabel(/^key/i).fill(key);
  33 |   await page.getByRole("button", { name: /create project/i }).click();
  34 |   await page.getByRole("link", { name }).click();
  35 | }
  36 | 
  37 | export async function createIssue(page, title) {
  38 |   await page.getByRole("button", { name: /new issue/i }).click();
  39 |   await page.getByLabel(/^title/i).fill(title);
  40 |   await page.getByRole("button", { name: /create issue/i }).click();
  41 | }
  42 | 
```