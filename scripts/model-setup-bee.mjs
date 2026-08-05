import { spawnSync } from "node:child_process";

const install = spawnSync("./.venv/bin/python", ["-m", "pip", "install", "-e", ".[bee-training]"], {
  cwd: "services/core-api",
  stdio: "inherit"
});

if (install.status !== 0) {
  process.exitCode = install.status ?? 1;
}
