import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";
const useExternalServer = Boolean(process.env.PLAYWRIGHT_BASE_URL);

export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL,
    trace: "retain-on-failure",
  },
  webServer: useExternalServer
    ? undefined
    : [
        {
          command:
            ".venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000",
          cwd: "..",
          url: "http://127.0.0.1:8000/api/health",
          reuseExistingServer: false,
          timeout: 120_000,
        },
        {
          command: "npm run dev -- --hostname 127.0.0.1 --port 3000",
          env: {
            ...process.env,
            NEXT_PUBLIC_API_BASE_URL: "http://127.0.0.1:8000",
          },
          url: "http://127.0.0.1:3000",
          reuseExistingServer: false,
          timeout: 120_000,
        },
      ],
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
