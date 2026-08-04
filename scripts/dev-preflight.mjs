import { spawn } from "node:child_process";
import { Socket } from "node:net";
import { once } from "node:events";

const defaultDatabaseUrl = "postgresql://hive_sight:hive_sight@localhost:5432/hive_sight_core_dev";

export async function runDevPreflight({ env = process.env } = {}) {
  if (env.HIVESIGHT_PERSISTENCE_BACKEND !== "postgres") {
    return true;
  }

  const target = databaseTargetFromEnv(env);
  const postgresReachable = await canConnectToTcpPort(target);
  if (postgresReachable) {
    return true;
  }

  const dockerAvailable = await isDockerDaemonAvailable();
  process.stderr.write(renderPostgresUnavailableMessage({ dockerAvailable, target }));
  return false;
}

export function databaseTargetFromEnv(env = process.env) {
  const databaseUrl = new URL(env.CORE_API_DATABASE_URL ?? defaultDatabaseUrl);
  return {
    host: databaseUrl.hostname,
    port: Number(databaseUrl.port || 5432)
  };
}

export function renderPostgresUnavailableMessage({ dockerAvailable, target }) {
  const location = `${target.host}:${target.port}`;
  const lines = [
    "",
    `HiveSight is configured to use Postgres, but it cannot reach ${location}.`
  ];

  if (dockerAvailable) {
    lines.push("Docker is running, so the Postgres container is probably stopped.");
    lines.push("Run: pnpm db:up");
  } else {
    lines.push("Docker Desktop does not appear to be running.");
    lines.push("Start Docker Desktop, then run: pnpm db:up");
  }

  lines.push("Then start HiveSight again: pnpm dev:all:yolo-training");
  lines.push("This check does not reset or wipe your database.");
  lines.push("");
  return `${lines.join("\n")}\n`;
}

async function canConnectToTcpPort({ host, port }) {
  const socket = new Socket();
  socket.setTimeout(1000);

  try {
    await new Promise((resolve, reject) => {
      socket.once("connect", resolve);
      socket.once("timeout", () => reject(new Error("Connection timed out")));
      socket.once("error", reject);
      socket.connect(port, host);
    });
    return true;
  } catch {
    return false;
  } finally {
    socket.destroy();
  }
}

async function isDockerDaemonAvailable() {
  try {
    const child = spawn("docker", ["info"], {
      stdio: ["ignore", "ignore", "ignore"]
    });
    const [code] = await once(child, "close");
    return code === 0;
  } catch {
    return false;
  }
}
