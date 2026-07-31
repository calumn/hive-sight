import { spawnSync } from "node:child_process";
import { resolve } from "node:path";

const repoRoot = resolve(new URL("..", import.meta.url).pathname);
const coreApiDir = resolve(repoRoot, "services/core-api");

const install = spawnSync("./.venv/bin/python", ["-m", "pip", "install", "-e", ".[yolo-training]"], {
  cwd: coreApiDir,
  stdio: "inherit"
});

if (install.status !== 0) {
  process.exitCode = install.status ?? 1;
} else {
  process.stdout.write("\nYOLO OBB optional dependencies are installed for the Core API venv.\n");
}
