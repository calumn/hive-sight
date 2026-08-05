import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import { databaseTargetFromEnv, renderPostgresUnavailableMessage } from "./dev-preflight.mjs";

describe("dev server Postgres preflight", () => {
  it("uses the Core API default dev database target when no URL is set", () => {
    assert.deepEqual(databaseTargetFromEnv({}), {
      host: "localhost",
      port: 5432
    });
  });

  it("reads the configured Core API database target", () => {
    assert.deepEqual(
      databaseTargetFromEnv({
        CORE_API_DATABASE_URL: "postgresql://hive_sight:hive_sight@127.0.0.1:15432/hive_sight_core_dev"
      }),
      {
        host: "127.0.0.1",
        port: 15432
      }
    );
  });

  it("tells the developer to start Docker Desktop when the daemon is unavailable", () => {
    const message = renderPostgresUnavailableMessage({
      dockerAvailable: false,
      target: { host: "localhost", port: 5432 }
    });

    assert.match(message, /Docker Desktop does not appear to be running/);
    assert.match(message, /pnpm db:up/);
    assert.match(message, /pnpm dev:all:bee-training/);
    assert.match(message, /does not reset or wipe your database/);
  });

  it("tells the developer to start Postgres when Docker is already running", () => {
    const message = renderPostgresUnavailableMessage({
      dockerAvailable: true,
      target: { host: "localhost", port: 5432 }
    });

    assert.match(message, /Postgres container is probably stopped/);
    assert.match(message, /pnpm db:up/);
    assert.doesNotMatch(message, /Start Docker Desktop/);
  });

  it("exposes Bee Training commands without YOLO-named command aliases", () => {
    const packageJson = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf-8"));
    const scripts = packageJson.scripts;

    assert.ok(scripts["model:setup:bee"]);
    assert.ok(scripts["model:train:bee"]);
    assert.ok(scripts["dev:all:bee-training"]);
    assert.ok(scripts["dev:lan:bee-training"]);
    assert.equal(scripts["model:setup:yolo"], undefined);
    assert.equal(scripts["model:train:bee:yolo"], undefined);
    assert.equal(scripts["dev:all:yolo"], undefined);
    assert.equal(scripts["dev:all:yolo-training"], undefined);
  });

  it("keeps browser acceptance commands separate for stub and live API lanes", () => {
    const rootPackageJson = JSON.parse(
      readFileSync(new URL("../package.json", import.meta.url), "utf-8")
    );
    const webPackageJson = JSON.parse(
      readFileSync(new URL("../apps/web/package.json", import.meta.url), "utf-8")
    );
    const playwrightConfig = readFileSync(
      new URL("../apps/web/playwright.config.ts", import.meta.url),
      "utf-8"
    );

    assert.equal(
      rootPackageJson.scripts["test:acceptance:web"],
      "pnpm --filter @hive-sight/web test:acceptance"
    );
    assert.equal(
      rootPackageJson.scripts["test:acceptance:web:live-api"],
      "pnpm --filter @hive-sight/web test:acceptance:live-api"
    );
    assert.match(webPackageJson.scripts["test:acceptance:live-api"], /HIVESIGHT_PLAYWRIGHT_PROFILE=live-api/);
    assert.match(playwrightConfig, /profile === "live-api" \? "8030" : "8020"/);
    assert.match(playwrightConfig, /profile === "live-api" \? "5203" : "5193"/);
  });
});
