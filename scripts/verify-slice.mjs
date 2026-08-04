import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const reportPath = resolve(repoRoot, "reports/slice-verification/latest.md");

const checks = [
  {
    name: "Core API tests",
    command: "./.venv/bin/python -m pytest -p no:cacheprovider",
    cwd: "services/core-api",
    args: ["./.venv/bin/python", "-m", "pytest", "-p", "no:cacheprovider"],
    note:
      "Includes API-level BDD scenarios. Slice 15 covers Dataset Version creation and fake Bee Detector training; real YOLO OBB training is only run through the explicit QA lane."
  },
  {
    name: "Analysis Service tests",
    command: "./.venv/bin/python -m pytest -p no:cacheprovider",
    cwd: "services/analysis-service",
    args: ["./.venv/bin/python", "-m", "pytest", "-p", "no:cacheprovider"]
  },
  {
    name: "Web TypeScript check",
    command: "pnpm --filter @hive-sight/web check",
    cwd: ".",
    args: ["pnpm", "--filter", "@hive-sight/web", "check"]
  },
  {
    name: "Dev script tests",
    command: "node --test scripts/dev-preflight.test.mjs",
    cwd: ".",
    args: ["node", "--test", "scripts/dev-preflight.test.mjs"]
  },
  {
    name: "Web browser acceptance tests",
    command: "pnpm --filter @hive-sight/web test:acceptance",
    cwd: ".",
    args: ["pnpm", "--filter", "@hive-sight/web", "test:acceptance"],
    note: "Playwright failure artifacts are under apps/web/test-results and apps/web/playwright-report."
  }
];

const startedAt = new Date();
const results = [];

for (const check of checks) {
  process.stdout.write(`Running ${check.name}...\n`);
  results.push(await runCheck(check));
}

const overallPassed = results.every((result) => result.status === "passed");
const report = renderReport({
  generatedAt: new Date(),
  overallPassed,
  results,
  startedAt
});

await mkdir(dirname(reportPath), { recursive: true });
await writeFile(reportPath, report);

process.stdout.write(`\nSlice verification report: ${reportPath}\n`);
process.exitCode = overallPassed ? 0 : 1;

function runCheck(check) {
  return new Promise((resolveRun) => {
    const started = new Date();
    const [command, ...args] = check.args;
    const child = spawn(command, args, {
      cwd: resolve(repoRoot, check.cwd),
      env: { ...process.env },
      stdio: ["ignore", "pipe", "pipe"]
    });

    let output = "";
    child.stdout.on("data", (chunk) => {
      const text = chunk.toString();
      output += text;
      process.stdout.write(text);
    });
    child.stderr.on("data", (chunk) => {
      const text = chunk.toString();
      output += text;
      process.stderr.write(text);
    });
    child.on("close", (code) => {
      resolveRun({
        ...check,
        status: code === 0 ? "passed" : "failed",
        exitCode: code,
        durationMs: Date.now() - started.getTime(),
        summary: summarizeOutput(output),
        outputTail: tail(output)
      });
    });
  });
}

function summarizeOutput(output) {
  const lines = output
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  const summaryLine = [...lines]
    .reverse()
    .find(
      (line) =>
        /\bpassed\b/.test(line) ||
        /\bfailed\b/.test(line) ||
        /All checks passed/.test(line) ||
        /tsc --noEmit/.test(line)
    );
  return summaryLine ?? "No concise summary was detected.";
}

function tail(output) {
  return output
    .split(/\r?\n/)
    .slice(-20)
    .join("\n")
    .trim();
}

function renderReport({ generatedAt, overallPassed, results, startedAt }) {
  const lines = [
    "# HiveSight Slice Verification Report",
    "",
    `Generated: ${generatedAt.toISOString()}`,
    `Duration: ${generatedAt.getTime() - startedAt.getTime()} ms`,
    `Overall result: ${overallPassed ? "passed" : "failed"}`,
    "",
    "## Checks",
    ""
  ];

  for (const result of results) {
    lines.push(`### ${result.name}`);
    lines.push("");
    lines.push(`- Status: ${result.status}`);
    lines.push(`- Command: \`${result.command}\``);
    lines.push(`- Working directory: \`${result.cwd}\``);
    lines.push(`- Exit code: ${result.exitCode}`);
    lines.push(`- Duration: ${result.durationMs} ms`);
    if (result.note) {
      lines.push(`- Note: ${result.note}`);
    }
    lines.push(`- Summary: ${result.summary}`);
    if (result.outputTail) {
      lines.push("");
      lines.push("```text");
      lines.push(result.outputTail);
      lines.push("```");
    }
    lines.push("");
  }

  lines.push("## Coverage Note");
  lines.push("");
  lines.push(
    "This report summarizes checks that were executed. It does not claim formal code coverage percentages."
  );
  lines.push("");
  return `${lines.join("\n")}\n`;
}
