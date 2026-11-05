import { expect, test } from "@playwright/test";
import {
  createIssue,
  createProject,
  login,
  onboard,
  register,
  uniqueEmail,
} from "./helpers";

async function drag(page, from, to) {
  // Ensure the source card is in view first
  await from.scrollIntoViewIfNeeded();
  await page.waitForTimeout(200);

  const source = await from.boundingBox();
  if (!source) {
    throw new Error("Kanban card is not visible");
  }

  const viewport = page.viewportSize();
  const startX = source.x + source.width / 2;
  const startY = source.y + source.height / 2;

  // Now inspect destination
  let target = await to.boundingBox();
  if (!target) {
    throw new Error("Destination column is not visible");
  }

  // Calculate destination X inside viewport
  let endX;
  if (target.x > startX) {
    // Dragging right
    if (target.x + 50 < viewport.width - 60) {
      // Destination is adjacent and already partially visible:
      // Drop inside its visible left side without triggering auto-scroll!
      endX = target.x + 45;
    } else {
      // Destination is further away (e.g. column 3 'Done'):
      // Push to the right edge to trigger auto-scroll
      endX = viewport.width - 20;
    }
  } else {
    // Dragging left (e.g. In Progress -> To Do)
    if (target.x + target.width - 50 > 60) {
      endX = target.x + target.width - 50;
    } else {
      endX = 20;
    }
  }

  const endY = Math.min(target.y + 100, viewport.height - 30);

  const isMobile = viewport.width <= 767;

  if (isMobile) {
    const cdp = await page.context().newCDPSession(page);
    try {
      await cdp.send("Input.dispatchTouchEvent", {
        type: "touchStart",
        touchPoints: [
          {
            x: startX,
            y: startY,
            id: 1,
          },
        ],
      });

      // @hello-pangea/dnd touch sensor requires a ~120ms hold delay before drag begins
      await page.waitForTimeout(300);

      const steps = 30;
      for (let step = 1; step <= steps; step++) {
        const progress = step / steps;
        await cdp.send("Input.dispatchTouchEvent", {
          type: "touchMove",
          touchPoints: [
            {
              x: startX + (endX - startX) * progress,
              y: startY + (endY - startY) * progress,
              id: 1,
            },
          ],
        });
        await page.waitForTimeout(20);
      }

      // If destination column was scrolled offscreen to the right (e.g. column 3 'Done')
      let finalX = endX;
      if (target.x > viewport.width) {
        await page.evaluate(() => {
          const kb = document.querySelector('.tt-kanban');
          if (kb) kb.scrollLeft = 400;
        });
        await page.waitForTimeout(200);
        finalX = 220;
        await cdp.send("Input.dispatchTouchEvent", {
          type: "touchMove",
          touchPoints: [
            {
              x: finalX,
              y: endY,
              id: 1,
            },
          ],
        });
        await page.waitForTimeout(100);
      }

      await cdp.send("Input.dispatchTouchEvent", {
        type: "touchEnd",
        touchPoints: [
          {
            x: finalX,
            y: endY,
            id: 1,
          },
        ],
      });
      await page.waitForTimeout(600);
    } finally {
      await cdp.detach();
    }
  } else {
    await page.mouse.move(startX, startY);
    await page.mouse.down();

    // Activate drag sensor.
    await page.mouse.move(
      startX + 15,
      startY + 15,
      { steps: 5 }
    );

    await page.mouse.move(
      endX,
      endY,
      { steps: 30 }
    );

    await page.mouse.up();
    await page.waitForTimeout(300);
  }
}

test.describe("Kanban drag and drop", () => {

  // Test 1: Allowed move, persistence and rejected transition
  test("allowed move persists after reload; disallowed move is rejected and reverted", async ({ page }) => {
    const email = uniqueEmail("kb");

    await register(page, email);
    await login(page, email);
    await onboard(page, "Kanban Co");
    await createProject(page, "Board test", "BRD");
    await createIssue(page, "Drag me");

    await expect(page.getByRole("dialog")).toBeHidden();

    const dragCard = page.getByTestId("card-BRD-1");

    await expect(
      page.getByTestId("column-To Do").getByTestId("card-BRD-1")
    ).toBeVisible();

    // To Do -> In Progress
    await drag(page, dragCard, page.getByTestId("column-In Progress"));

    await expect(
      page.getByTestId("column-In Progress").getByTestId("card-BRD-1")
    ).toBeVisible();

    // Verify persistence after reload
    await page.reload();

    await expect(
      page.getByTestId("column-In Progress").getByTestId("card-BRD-1")
    ).toBeVisible();

    // In Progress -> To Do
    await drag(
      page,
      page.getByTestId("card-BRD-1"),
      page.getByTestId("column-To Do")
    );

    await expect(
      page.getByTestId("column-To Do").getByTestId("card-BRD-1")
    ).toBeVisible();

    // To Do -> Done (disallowed)
    await drag(
      page,
      page.getByTestId("card-BRD-1"),
      page.getByTestId("column-Done")
    );

    await expect(page.getByRole("alert")).toContainText(/move rejected/i);

    // Verify rejected move is reverted
    await expect(
      page.getByTestId("column-To Do").getByTestId("card-BRD-1")
    ).toBeVisible();

    await page.reload();

    await expect(
      page.getByTestId("column-To Do").getByTestId("card-BRD-1")
    ).toBeVisible();


  });

  // Test 2: Keyboard accessibility
  test("keyboard users can move a card", async ({ page }) => {
    const email = uniqueEmail("kbd");


    await register(page, email);
    await login(page, email);
    await onboard(page, "Keyboard Co");
    await createProject(page, "Kbd test", "KBD");
    await createIssue(page, "Keyboard move");

    const card = page.getByTestId("card-KBD-1");

    await expect(page.getByRole("dialog")).toBeHidden();
    await expect(card).toBeVisible();

    // Focus the card
    await card.focus();
    await expect(card).toBeFocused();

    // Pick up, move right and drop
    await page.keyboard.press("Space");
    await page.keyboard.press("ArrowRight");
    await page.keyboard.press("Space");

    // Verify card moved to In Progress
    await expect(
      page.getByTestId("column-In Progress").getByTestId("card-KBD-1")
    ).toBeVisible();

  });
});
