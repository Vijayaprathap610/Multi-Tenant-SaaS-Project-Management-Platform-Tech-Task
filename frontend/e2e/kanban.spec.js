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
  await from.scrollIntoViewIfNeeded();
  await to.scrollIntoViewIfNeeded();

  const source = await from.boundingBox();
  const target = await to.boundingBox();

  if (!source || !target) {
    throw new Error("Kanban card or destination column is not visible");
  }

  // Calculate a drop point inside the visible portion
  // of the destination column.
  const viewport = page.viewportSize();

  const visibleLeft = Math.max(target.x, 5);
  const visibleRight = Math.min(
    target.x + target.width,
    viewport.width - 5
  );

  const visibleTop = Math.max(target.y, 5);
  const visibleBottom = Math.min(
    target.y + target.height,
    viewport.height - 5
  );

  if (
    visibleRight <= visibleLeft ||
    visibleBottom <= visibleTop
  ) {
    throw new Error("Destination column is outside the visible viewport");
  }

  const startX = source.x + source.width / 2;
  const startY = source.y + source.height / 2;

  const endX = (visibleLeft + visibleRight) / 2;
  const endY = (visibleTop + visibleBottom) / 2;

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

    async function drag(page, from, to) {
      await from.scrollIntoViewIfNeeded();
      await to.scrollIntoViewIfNeeded();

      await page.waitForTimeout(300);

      const source = await from.boundingBox();
      const target = await to.boundingBox();

      if (!source || !target) {
        throw new Error(
          "Kanban card or destination column is not visible"
        );
      }

      const startX = source.x + source.width / 2;
      const startY = source.y + source.height / 2;

      const endX = target.x + target.width / 2;
      const endY = target.y + Math.min(120, target.height - 20);

      const isMobile = page.viewportSize().width <= 767;

      // Mobile diagnostic information
      if (isMobile) {
        const debug = await page.evaluate(() => {
          const card = document.querySelector(
            '[data-testid="card-BRD-1"]'
          );

          const column = document.querySelector(
            '[data-testid="column-In Progress"]'
          );

          const kanban = document.querySelector(".tt-kanban");

          const cardRect = card?.getBoundingClientRect();
          const columnRect = column?.getBoundingClientRect();

          return {
            viewport: {
              width: window.innerWidth,
              height: window.innerHeight,
            },
            card: cardRect
              ? {
                x: cardRect.x,
                y: cardRect.y,
                width: cardRect.width,
                height: cardRect.height,
              }
              : null,
            destination: columnRect
              ? {
                x: columnRect.x,
                y: columnRect.y,
                width: columnRect.width,
                height: columnRect.height,
              }
              : null,
            scrollLeft: kanban?.scrollLeft,
            scrollWidth: kanban?.scrollWidth,
            clientWidth: kanban?.clientWidth,
          };
        });

        console.log("MOBILE DRAG DEBUG:", debug);
      }

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

          await page.waitForTimeout(300);

          for (let step = 1; step <= 30; step++) {
            const progress = step / 30;

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

            await page.waitForTimeout(15);
          }

          await cdp.send("Input.dispatchTouchEvent", {
            type: "touchEnd",
            touchPoints: [],
          });

        } finally {
          await cdp.detach();
        }
      } else {
        // Desktop mouse drag
        await page.mouse.move(startX, startY);

        await page.mouse.down();

        await page.mouse.move(
          startX + 20,
          startY + 20,
          { steps: 5 }
        );

        await page.waitForTimeout(200);

        await page.mouse.move(
          endX,
          endY,
          { steps: 25 }
        );

        await page.waitForTimeout(300);

        await page.mouse.up();
      }

      await page.waitForTimeout(1000);
    }


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
