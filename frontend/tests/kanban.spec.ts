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
