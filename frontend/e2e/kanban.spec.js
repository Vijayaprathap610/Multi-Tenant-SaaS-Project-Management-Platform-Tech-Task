import { expect, test } from "@playwright/test";
import { createIssue, createProject, login, onboard, register, uniqueEmail } from "./helpers";

async function drag(page, from, to) {
  const a = await from.boundingBox();
  const b = await to.boundingBox();
  await page.mouse.move(a.x + a.width / 2, a.y + a.height / 2);
  await page.mouse.down();
  await page.mouse.move(a.x + a.width / 2 + 10, a.y + a.height / 2 + 10, { steps: 4 });
  await page.mouse.move(b.x + b.width / 2, b.y + 100, { steps: 12 });
  await page.mouse.up();
}

test.describe("Kanban drag and drop", () => {
  test.skip(({ isMobile }) => isMobile, "pointer drag is exercised on the desktop project");

  test("allowed move persists after reload; disallowed move is rejected and reverted", async ({ page }) => {
    const email = uniqueEmail("kb");
    await register(page, email); await login(page, email); await onboard(page, "Kanban Co");
    await createProject(page, "Board test", "BRD");
    await createIssue(page, "Drag me");

    const card = page.getByTestId("card-BRD-1");
    await expect(page.getByTestId("column-To Do").getByTestId("card-BRD-1")).toBeVisible();

    // To Do -> In Progress is allowed by the default workflow
    await drag(page, card, page.getByTestId("column-In Progress"));
    await expect(page.getByTestId("column-In Progress").getByTestId("card-BRD-1")).toBeVisible();
    await page.reload();
    await expect(page.getByTestId("column-In Progress").getByTestId("card-BRD-1")).toBeVisible();

    // In Progress -> To Do is allowed; To Do -> Done is not
    await drag(page, page.getByTestId("card-BRD-1"), page.getByTestId("column-To Do"));
    await expect(page.getByTestId("column-To Do").getByTestId("card-BRD-1")).toBeVisible();
    await drag(page, page.getByTestId("card-BRD-1"), page.getByTestId("column-Done"));
    await expect(page.getByRole("alert")).toContainText(/move rejected/i);
    await expect(page.getByTestId("column-To Do").getByTestId("card-BRD-1")).toBeVisible();
    await page.reload();
    await expect(page.getByTestId("column-To Do").getByTestId("card-BRD-1")).toBeVisible();
  });

  test("keyboard users can move a card", async ({ page }) => {
    const email = uniqueEmail("kbd");
    await register(page, email); await login(page, email); await onboard(page, "Keyboard Co");
    await createProject(page, "Kbd test", "KBD");
    await createIssue(page, "Keyboard move");
    await page.getByTestId("card-KBD-1").focus();
    await page.keyboard.press("Space");
    await page.keyboard.press("ArrowRight");
    await page.keyboard.press("Space");
    await expect(page.getByTestId("column-In Progress").getByTestId("card-KBD-1")).toBeVisible();
  });
});
