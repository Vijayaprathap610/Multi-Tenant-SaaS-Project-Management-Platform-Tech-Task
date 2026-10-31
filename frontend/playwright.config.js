import { defineConfig } from "@playwright/test";

// Requires the full stack running (docker compose up) on http://localhost:5173.
export default defineConfig({
  testDir: "./e2e",
  timeout: 60000,
  use: { baseURL: process.env.E2E_BASE_URL || "http://localhost:5173", trace: "retain-on-failure" },
  projects: [
    { name: "desktop", use: { viewport: { width: 1280, height: 800 } } },
    { name: "mobile", use: { viewport: { width: 390, height: 844 } } },
  ],
});
