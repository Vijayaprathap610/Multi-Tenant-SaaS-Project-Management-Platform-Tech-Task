import { expect } from "@playwright/test";

export const PASSWORD = "Pw-Str0ng-e2e-1!";
export const uniqueEmail = (tag) => `${tag}+${Date.now()}${Math.floor(Math.random() * 1000)}@e2e.test`;

export async function register(page, email) {
  await page.goto("/register");
  await page.getByLabel(/^email/i).fill(email);
  await page.getByLabel(/^password$/i).fill(PASSWORD);
  await page.getByLabel(/confirm password/i).fill(PASSWORD);
  await page.getByRole("button", { name: /create account/i }).click();
  await expect(page).toHaveURL(/\/login/);
}

export async function login(page, email) {
  await page.goto("/login");
  await page.getByLabel(/^email/i).fill(email);
  await page.getByLabel(/^password/i).fill(PASSWORD);
  await page.getByRole("button", { name: /^log in$/i }).click();
}

export async function onboard(page, workspaceName) {
  await expect(page).toHaveURL(/\/onboarding/);
  await page.getByLabel(/workspace name/i).fill(workspaceName);
  await page.getByRole("button", { name: /create workspace/i }).click();
  await expect(page).toHaveURL(/\/app$/);
}

export async function createProject(page, name, key) {
  await page.getByRole("button", { name: /^\+ New project$/i }).click();
  await page.getByRole("textbox", { name: "Project name" }).fill(name);
  await page.getByRole("textbox", { name: "Project key" }).fill(key);
  await page.getByRole("button", { name: /^create project$/i }).click();
  await page.getByRole("link", { name }).click();
}

export async function createIssue(page, title) {
  await page.getByRole("button", { name: /new issue/i }).click();
  await page.getByLabel(/^title/i).fill(title);
  await page.getByRole("button", { name: /create issue/i }).click();

  // Wait until the issue creation dialog is completely closed.
  await expect(page.getByRole("dialog")).toBeHidden();
}



