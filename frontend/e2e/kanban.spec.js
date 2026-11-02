import { expect, test } from "@playwright/test";
import { createIssue, createProject, login, onboard, register, uniqueEmail } from "./helpers";

async function drag(page, from, to) {
  await from.scrollIntoViewIfNeeded();
  await to.scrollIntoViewIfNeeded();

  const source = await from.boundingBox();
  const target = await to.boundingBox();

  if (!source || !target) {
    throw new Error("Kanban card or destination column is not visible");
  }

  const startX = source.x + source.width / 2;
  const startY = source.y + source.height / 2;
  const endX = target.x + target.width / 2;
  const endY = target.y + Math.min(120, target.height - 20);

  await page.mouse.move(startX, startY);
  await page.mouse.down();
  await page.mouse.move(startX + 20, startY + 20, { steps: 5 });
  await page.waitForTimeout(200);
  await page.mouse.move(endX, endY, { steps: 25 });
  await page.waitForTimeout(300);
  await page.mouse.up();
  await page.waitForTimeout(500);
}

test.describe("Kanban drag and drop", () => {
  test.beforeEach(async ({ isMobile }) => {
    test.skip(isMobile, "pointer drag is exercised on the desktop project");
  });

  test("allowed move persists after reload; disallowed move is rejected and reverted", async ({ page }) => {
    const email = uniqueEmail("kb");
    await register(page, email); await login(page, email); await onboard(page, "Kanban Co");
    await createProject(page, "Board test", "BRD");
    await createIssue(page, "Drag me");
    await expect(page.getByRole("dialog")).toBeHidden();
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

    await register(page, email);
    await login(page, email);
    await onboard(page, "Keyboard Co");
    await createProject(page, "Kbd test", "KBD");
    await createIssue(page, "Keyboard move");

    const card = page.getByTestId("card-KBD-1");

    // Confirm the dialog is closed and the card is visible.
    await expect(page.getByRole("dialog")).toBeHidden();
    await expect(card).toBeVisible();

    // Focus the card.
    await card.focus();
    await expect(card).toBeFocused();

    // Move the card using keyboard controls.
    await page.keyboard.press("Space");
    await page.keyboard.press("ArrowRight");
    await page.keyboard.press("Space");

    // Verify that the card moved to In Progress.
    await expect(
      page.getByTestId("column-In Progress").getByTestId("card-KBD-1")
    ).toBeVisible();

  });
});
