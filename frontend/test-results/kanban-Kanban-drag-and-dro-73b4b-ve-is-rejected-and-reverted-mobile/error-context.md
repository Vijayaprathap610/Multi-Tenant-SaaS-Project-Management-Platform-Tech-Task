# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: kanban.spec.js >> Kanban drag and drop >> allowed move persists after reload; disallowed move is rejected and reverted
- Location: e2e\kanban.spec.js:33:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByTestId('column-In Progress').getByTestId('card-BRD-1')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByTestId('column-In Progress').getByTestId('card-BRD-1') with timeout 5000ms
  - waiting for getByTestId('column-In Progress').getByTestId('card-BRD-1')

```

```yaml
- navigation:
  - link "Tech Task home":
    - /url: /app
    - img "Tech Task logo"
    - text: Tech Task
  - button "Toggle navigation"
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
  - heading "Board test BRD" [level=1]
  - link "Board":
    - /url: /app/projects/6128eee0-e75d-4ecd-a091-af2a7d8ce556/board
  - link "Issues":
    - /url: /app/projects/6128eee0-e75d-4ecd-a091-af2a7d8ce556/issues
  - link "Sprints":
    - /url: /app/projects/6128eee0-e75d-4ecd-a091-af2a7d8ce556/sprints
  - link "Workflow":
    - /url: /app/projects/6128eee0-e75d-4ecd-a091-af2a7d8ce556/workflow
  - link "Members":
    - /url: /app/projects/6128eee0-e75d-4ecd-a091-af2a7d8ce556/members
  - link "Reports":
    - /url: /app/projects/6128eee0-e75d-4ecd-a091-af2a7d8ce556/reports
  - textbox "Search issues"
  - combobox "Filter by assignee":
    - option "All assignees" [selected]
    - option "kb+1793531783654944@e2e.test"
  - combobox "Filter by priority":
    - option "All priorities" [selected]
    - option "low"
    - option "medium"
    - option "high"
    - option "urgent"
  - button "New issue"
  - region "To Do column":
    - heading "To Do 1" [level=2]
    - button "BRD-1 Drag me. Press space to pick up, arrow keys to move, space to drop.":
      - link "BRD-1":
        - /url: /app/projects/6128eee0-e75d-4ecd-a091-af2a7d8ce556/issues/7ae706dc-5c18-450e-8070-bb90f0d2c1cc
      - text: medium Drag me Unassigned
  - region "In Progress column":
    - heading "In Progress 0" [level=2]
  - region "Done column":
    - heading "Done 0" [level=2]
```

# Test source

```ts
  1  | import { expect, test } from "@playwright/test";
  2  | import { createIssue, createProject, login, onboard, register, uniqueEmail } from "./helpers";
  3  | 
  4  | async function drag(page, from, to) {
  5  |   await from.scrollIntoViewIfNeeded();
  6  |   await to.scrollIntoViewIfNeeded();
  7  | 
  8  |   const source = await from.boundingBox();
  9  |   const target = await to.boundingBox();
  10 | 
  11 |   if (!source || !target) {
  12 |     throw new Error("Kanban card or destination column is not visible");
  13 |   }
  14 | 
  15 |   const startX = source.x + source.width / 2;
  16 |   const startY = source.y + source.height / 2;
  17 |   const endX = target.x + target.width / 2;
  18 |   const endY = target.y + Math.min(120, target.height - 20);
  19 | 
  20 |   await page.mouse.move(startX, startY);
  21 |   await page.mouse.down();
  22 |   await page.mouse.move(startX + 20, startY + 20, { steps: 5 });
  23 |   await page.waitForTimeout(200);
  24 |   await page.mouse.move(endX, endY, { steps: 25 });
  25 |   await page.waitForTimeout(300);
  26 |   await page.mouse.up();
  27 |   await page.waitForTimeout(500);
  28 | }
  29 | 
  30 | test.describe("Kanban drag and drop", () => {
  31 |   test.skip(({ isMobile }) => isMobile, "pointer drag is exercised on the desktop project");
  32 | 
  33 |   test("allowed move persists after reload; disallowed move is rejected and reverted", async ({ page }) => {
  34 |     const email = uniqueEmail("kb");
  35 |     await register(page, email); await login(page, email); await onboard(page, "Kanban Co");
  36 |     await createProject(page, "Board test", "BRD");
  37 |     await createIssue(page, "Drag me");
  38 |     await expect(page.getByRole("dialog")).toBeHidden();
  39 |     const card = page.getByTestId("card-BRD-1");
  40 |     await expect(page.getByTestId("column-To Do").getByTestId("card-BRD-1")).toBeVisible();
  41 | 
  42 |     // To Do -> In Progress is allowed by the default workflow
  43 |     await drag(page, card, page.getByTestId("column-In Progress"));
> 44 |     await expect(page.getByTestId("column-In Progress").getByTestId("card-BRD-1")).toBeVisible();
     |                                                                                    ^ Error: expect(locator).toBeVisible() failed
  45 |     await page.reload();
  46 |     await expect(page.getByTestId("column-In Progress").getByTestId("card-BRD-1")).toBeVisible();
  47 | 
  48 |     // In Progress -> To Do is allowed; To Do -> Done is not
  49 |     await drag(page, page.getByTestId("card-BRD-1"), page.getByTestId("column-To Do"));
  50 |     await expect(page.getByTestId("column-To Do").getByTestId("card-BRD-1")).toBeVisible();
  51 |     await drag(page, page.getByTestId("card-BRD-1"), page.getByTestId("column-Done"));
  52 |     await expect(page.getByRole("alert")).toContainText(/move rejected/i);
  53 |     await expect(page.getByTestId("column-To Do").getByTestId("card-BRD-1")).toBeVisible();
  54 |     await page.reload();
  55 |     await expect(page.getByTestId("column-To Do").getByTestId("card-BRD-1")).toBeVisible();
  56 |   });
  57 | 
  58 |   test("keyboard users can move a card", async ({ page }) => {
  59 |     const email = uniqueEmail("kbd");
  60 | 
  61 |     await register(page, email);
  62 |     await login(page, email);
  63 |     await onboard(page, "Keyboard Co");
  64 |     await createProject(page, "Kbd test", "KBD");
  65 |     await createIssue(page, "Keyboard move");
  66 | 
  67 |     const card = page.getByTestId("card-KBD-1");
  68 | 
  69 |     // Confirm the dialog is closed and the card is visible.
  70 |     await expect(page.getByRole("dialog")).toBeHidden();
  71 |     await expect(card).toBeVisible();
  72 | 
  73 |     // Focus the card.
  74 |     await card.focus();
  75 |     await expect(card).toBeFocused();
  76 | 
  77 |     // Move the card using keyboard controls.
  78 |     await page.keyboard.press("Space");
  79 |     await page.keyboard.press("ArrowRight");
  80 |     await page.keyboard.press("Space");
  81 | 
  82 |     // Verify that the card moved to In Progress.
  83 |     await expect(
  84 |       page.getByTestId("column-In Progress").getByTestId("card-KBD-1")
  85 |     ).toBeVisible();
  86 | 
  87 |   });
  88 | });
  89 | 
```