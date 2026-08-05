import { defineConfig, devices } from "@playwright/test";

const reuseExistingServer = process.env.HIVESIGHT_PLAYWRIGHT_REUSE_SERVERS === "true";
const profile = process.env.HIVESIGHT_PLAYWRIGHT_PROFILE ?? "stub";
const apiPort =
  process.env.HIVESIGHT_PLAYWRIGHT_API_PORT ?? (profile === "live-api" ? "8030" : "8020");
const webPort =
  process.env.HIVESIGHT_PLAYWRIGHT_WEB_PORT ?? (profile === "live-api" ? "5203" : "5193");
const coreApiUrl = `http://127.0.0.1:${apiPort}`;
const webUrl = `http://127.0.0.1:${webPort}`;
process.env.HIVESIGHT_PLAYWRIGHT_CORE_API_URL = coreApiUrl;
const coreApiEnv =
  profile === "live-api"
    ? {
        HIVESIGHT_PERSISTENCE_BACKEND: "postgres",
        HIVESIGHT_DATABASE_PURPOSE: "dev",
        CORE_API_DATABASE_URL:
          process.env.CORE_API_DATABASE_URL ??
          "postgresql://hive_sight:hive_sight@localhost:5432/hive_sight_core_dev"
      }
    : {};

export default defineConfig({
  testDir: "./tests/acceptance",
  fullyParallel: false,
  workers: 1,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  use: {
    baseURL: webUrl,
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
        `cd ../../services/core-api && ./.venv/bin/python -m uvicorn hive_sight_core_api.main:app --host 127.0.0.1 --port ${apiPort}`,
      env: {
        ...coreApiEnv,
        HIVESIGHT_DEV_USERS_ENABLED: "true",
        HIVESIGHT_PRELABELER: "deterministic",
        CORE_API_ALLOWED_ORIGINS: `http://localhost:${webPort},${webUrl}`
      },
      reuseExistingServer,
      timeout: 30_000,
      url: `${coreApiUrl}/healthz`
    },
    {
      command: `pnpm dev --host 127.0.0.1 --port ${webPort}`,
      env: {
        VITE_CORE_API_URL: coreApiUrl
      },
      reuseExistingServer,
      timeout: 30_000,
      url: webUrl
    }
  ]
});
