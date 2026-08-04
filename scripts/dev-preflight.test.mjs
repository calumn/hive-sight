import { describe, it } from "node:test";
import assert from "node:assert/strict";

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
});
