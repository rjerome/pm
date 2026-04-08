import { expect, test } from "@playwright/test";

const login = async (page: Parameters<typeof test>[0]["page"]) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
};

test("rejects invalid credentials", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("wrong");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByText("Invalid credentials.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).not.toBeVisible();
});

test("loads the kanban board after sign in", async ({ page }) => {
  await login(page);
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("restores the signed-in session after reload", async ({ page }) => {
  await login(page);
  await page.reload();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("logs out and returns to the login screen", async ({ page }) => {
  await login(page);
  await page.getByRole("button", { name: /log out/i }).click();
  await expect(
    page.getByRole("heading", { name: /sign in to open your kanban workspace/i })
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).not.toBeVisible();
});

test("adds a card to a column after sign in", async ({ page }) => {
  await login(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
  await page.reload();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("edits a card and keeps the change after reload", async ({ page }) => {
  await login(page);
  const card = page.getByTestId("card-card-1");
  await card.getByLabel(/edit align roadmap themes/i).click();
  await card.getByLabel(/edit align roadmap themes title/i).fill("Roadmap alignment");
  await card.getByLabel(/edit align roadmap themes details/i).fill(
    "Updated through Playwright."
  );
  await card.getByRole("button", { name: /save/i }).click();
  await expect(page.getByText("Roadmap alignment")).toBeVisible();
  await page.reload();
  await expect(page.getByText("Roadmap alignment")).toBeVisible();
});

test("moves a card between columns after sign in", async ({ page }) => {
  await login(page);
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("shows AI-driven board changes in the sidebar flow", async ({ page }) => {
  await page.route("**/api/ai/chat", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        model: "openai/gpt-oss-120b",
        reply: "I renamed the first column and added a review card.",
        operations: [
          {
            type: "rename_column",
            columnId: "col-backlog",
            title: "Ideas",
          },
          {
            type: "create_card",
            columnId: "col-review",
            title: "Prepare stakeholder recap",
            details: "Summarize the release review outcomes.",
            beforeCardId: null,
            afterCardId: "card-6",
          },
        ],
        boardUpdated: true,
        board: {
          version: 3,
          columns: [
            {
              id: "col-backlog",
              slotKey: "backlog",
              title: "Ideas",
              position: 0,
              version: 2,
              cardIds: ["card-1", "card-2"],
            },
            {
              id: "col-discovery",
              slotKey: "discovery",
              title: "Discovery",
              position: 1,
              version: 1,
              cardIds: ["card-3"],
            },
            {
              id: "col-progress",
              slotKey: "progress",
              title: "In Progress",
              position: 2,
              version: 1,
              cardIds: ["card-4", "card-5"],
            },
            {
              id: "col-review",
              slotKey: "review",
              title: "Review",
              position: 3,
              version: 1,
              cardIds: ["card-6", "card-ai"],
            },
            {
              id: "col-done",
              slotKey: "done",
              title: "Done",
              position: 4,
              version: 1,
              cardIds: ["card-7", "card-8"],
            },
          ],
          cards: {
            "card-1": {
              id: "card-1",
              columnId: "col-backlog",
              title: "Align roadmap themes",
              details: "Draft quarterly themes with impact statements and metrics.",
              sortOrder: 1000,
              version: 1,
            },
            "card-2": {
              id: "card-2",
              columnId: "col-backlog",
              title: "Gather customer signals",
              details: "Review support tags, sales notes, and churn feedback.",
              sortOrder: 2000,
              version: 1,
            },
            "card-3": {
              id: "card-3",
              columnId: "col-discovery",
              title: "Prototype analytics view",
              details: "Sketch initial dashboard layout and key drill-downs.",
              sortOrder: 1000,
              version: 1,
            },
            "card-4": {
              id: "card-4",
              columnId: "col-progress",
              title: "Refine status language",
              details: "Standardize column labels and tone across the board.",
              sortOrder: 1000,
              version: 1,
            },
            "card-5": {
              id: "card-5",
              columnId: "col-progress",
              title: "Design card layout",
              details: "Add hierarchy and spacing for scanning dense lists.",
              sortOrder: 2000,
              version: 1,
            },
            "card-6": {
              id: "card-6",
              columnId: "col-review",
              title: "QA micro-interactions",
              details: "Verify hover, focus, and loading states.",
              sortOrder: 1000,
              version: 1,
            },
            "card-7": {
              id: "card-7",
              columnId: "col-done",
              title: "Ship marketing page",
              details: "Final copy approved and asset pack delivered.",
              sortOrder: 1000,
              version: 1,
            },
            "card-8": {
              id: "card-8",
              columnId: "col-done",
              title: "Close onboarding sprint",
              details: "Document release notes and share internally.",
              sortOrder: 2000,
              version: 1,
            },
            "card-ai": {
              id: "card-ai",
              columnId: "col-review",
              title: "Prepare stakeholder recap",
              details: "Summarize the release review outcomes.",
              sortOrder: 1500,
              version: 1,
            },
          },
        },
      }),
    });
  });

  await login(page);

  await page
    .getByLabel("Ask the AI assistant")
    .fill("Rename backlog to Ideas and add a review card.");
  await page.getByRole("button", { name: /^send$/i }).click();

  await expect(page.getByText("I renamed the first column and added a review card.")).toBeVisible();
  await expect(page.getByTestId("column-col-backlog").getByLabel("Column title")).toHaveValue(
    "Ideas"
  );
  await expect(page.getByTestId("column-col-review").getByText("Prepare stakeholder recap")).toBeVisible();
  await expect(page.getByText(/board updated/i)).toBeVisible();
});
