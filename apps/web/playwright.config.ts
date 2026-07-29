import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/acceptance",
  fullyParallel: false,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  use: {
    baseURL: "http://127.0.0.1:5173",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "retain-on-failure"
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] }
    }
  ],
  webServer: [
    {
      command:
        "cd ../../services/core-api && ./.venv/bin/python -m uvicorn hive_sight_core_api.main:app --host 127.0.0.1 --port 8000",
      env: {
        HIVESIGHT_PRELABELER: "deterministic"
      },
      reuseExistingServer: false,
      timeout: 30_000,
      url: "http://127.0.0.1:8000/healthz"
    },
    {
      command: "pnpm dev --host 127.0.0.1 --port 5173",
      env: {
        VITE_CORE_API_URL: "http://127.0.0.1:8000"
      },
      reuseExistingServer: false,
      timeout: 30_000,
      url: "http://127.0.0.1:5173"
    }
  ]
});
