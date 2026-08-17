import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const reportPath = resolve(repoRoot, "reports/slice-verification/latest.md");

const checks = [
  {
    name: "Acceptance catalogue - Core API",
    command:
      "./.venv/bin/python -m pytest -p no:cacheprovider -m api tests/test_visible_varroa_review_outcome_api_bdd.py tests/test_photo_visible_varroa_evidence_summary_api_bdd.py tests/test_varroa_photo_analysis_api_bdd.py tests/test_varroa_photo_analysis_workflow_api_bdd.py tests/test_product_photo_analysis_confidence_policy_api_bdd.py tests/test_hive_frame_slot_inspection_photo_context_api_bdd.py tests/test_advisor_treatment_recommendation_api_bdd.py",
    cwd: "services/core-api",
    args: [
      "./.venv/bin/python",
      "-m",
      "pytest",
      "-p",
      "no:cacheprovider",
      "-m",
      "api",
      "tests/test_visible_varroa_review_outcome_api_bdd.py",
      "tests/test_photo_visible_varroa_evidence_summary_api_bdd.py",
      "tests/test_varroa_photo_analysis_api_bdd.py",
      "tests/test_varroa_photo_analysis_workflow_api_bdd.py",
      "tests/test_product_photo_analysis_confidence_policy_api_bdd.py",
      "tests/test_hive_frame_slot_inspection_photo_context_api_bdd.py",
      "tests/test_advisor_treatment_recommendation_api_bdd.py"
    ],
    note:
      "Executes canonical acceptance-catalogue features that have a Core API binding.",
    bddAreas: [
      {
        area: "Varroa review outcome",
        capability: "varroa",
        seam: "Core API",
        tag: "api",
        featureFile: "acceptance/features/varroa/visible-varroa-review-outcome.feature",
        testFile: "tests/test_visible_varroa_review_outcome_api_bdd.py"
      },
      {
        area: "Photo-visible Varroa evidence summary",
        capability: "varroa",
        seam: "Core API",
        tag: "api",
        featureFile:
          "acceptance/features/varroa/photo-visible-varroa-evidence-summary.feature",
        testFile: "tests/test_photo_visible_varroa_evidence_summary_api_bdd.py"
      },
      {
        area: "Varroa Photo Analysis evidence and adapter readiness",
        capability: "varroa",
        seam: "Core API",
        tag: "api",
        featureFile:
          "acceptance/features/varroa/varroa-photo-analysis-evidence-and-adapter-readiness.feature",
        testFile: "tests/test_varroa_photo_analysis_api_bdd.py"
      },
      {
        area: "One-click Varroa Photo Analysis workflow",
        capability: "varroa",
        seam: "Core API",
        tag: "api",
        featureFile: "acceptance/features/varroa/varroa-photo-analysis-workflow.feature",
        testFile: "tests/test_varroa_photo_analysis_workflow_api_bdd.py"
      },
      {
        area: "Product Photo Analysis confidence policy",
        capability: "varroa",
        seam: "Core API",
        tag: "api",
        featureFile:
          "acceptance/features/varroa/product-photo-analysis-confidence-policy.feature",
        testFile: "tests/test_product_photo_analysis_confidence_policy_api_bdd.py"
      },
      {
        area: "Hive frame slot inspection photo context",
        capability: "varroa",
        seam: "Core API",
        tag: "api",
        featureFile:
          "acceptance/features/varroa/hive-frame-slot-inspection-photo-context.feature",
        testFile: "tests/test_hive_frame_slot_inspection_photo_context_api_bdd.py"
      },
      {
        area: "Advisor treatment recommendation intake",
        capability: "treatment",
        seam: "Core API",
        tag: "api",
        featureFile:
          "acceptance/features/treatment/advisor-treatment-recommendation-intake.feature",
        testFile: "tests/test_advisor_treatment_recommendation_api_bdd.py"
      }
    ]
  },
  {
    name: "Acceptance catalogue - Web UI",
    command: "pnpm --filter @hive-sight/web test:bdd",
    cwd: ".",
    args: ["pnpm", "--filter", "@hive-sight/web", "test:bdd"],
    note:
      "Executes canonical shared features that have a Web UI binding through playwright-bdd.",
    bddAreas: [
      {
        area: "Varroa review outcome",
        capability: "varroa",
        seam: "Web UI",
        tag: "web",
        featureFile: "acceptance/features/varroa/visible-varroa-review-outcome.feature"
      }
    ]
  },
  {
    name: "Core API tests",
    command: "./.venv/bin/python -m pytest -p no:cacheprovider",
    cwd: "services/core-api",
    args: ["./.venv/bin/python", "-m", "pytest", "-p", "no:cacheprovider"],
    note:
      "Includes API-level BDD scenarios. Real Bee Training adapters are only run through the explicit Bee Training QA lane."
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

for (const result of results) {
  result.bddAreaSummaries = await summarizeBddAreas(result);
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
        output,
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

async function summarizeBddAreas(result) {
  if (!result.bddAreas) return [];
  return Promise.all(
    result.bddAreas.map(async (area) => {
      const selected = await countTaggedScenarios(area.featureFile, area.tag);
      const execution = executionCountsForArea({
        output: result.output,
        testFile: area.testFile,
        selected,
        checkPassed: result.status === "passed"
      });
      return {
        ...area,
        selected,
        ...execution,
        result: execution.failed === 0 && execution.completed === selected ? "passed" : result.status
      };
    })
  );
}

async function countTaggedScenarios(featureFile, tag) {
  const text = await readFile(resolve(repoRoot, featureFile), "utf8");
  const wantedTag = tag.startsWith("@") ? tag : `@${tag}`;
  const lines = text.split(/\r?\n/);
  let featureTags = new Set();
  let pendingTags = [];
  let count = 0;

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) continue;
    if (line.startsWith("@")) {
      pendingTags = line.split(/\s+/);
      continue;
    }
    if (line.startsWith("Feature:")) {
      featureTags = new Set(pendingTags);
      pendingTags = [];
      continue;
    }
    if (line.startsWith("Scenario:") || line.startsWith("Scenario Outline:")) {
      const scenarioTags = new Set([...featureTags, ...pendingTags]);
      if (scenarioTags.has(wantedTag)) {
        count += 1;
      }
      pendingTags = [];
      continue;
    }
    pendingTags = [];
  }

  return count;
}

function executionCountsForArea({ output, testFile, selected, checkPassed }) {
  if (!testFile) {
    return checkPassed
      ? { run: selected, completed: selected, failed: 0, skipped: 0 }
      : { run: selected, completed: 0, failed: selected, skipped: 0 };
  }

  const line = output.split(/\r?\n/).find((candidate) => candidate.trim().startsWith(testFile));
  if (!line) {
    return checkPassed
      ? { run: selected, completed: selected, failed: 0, skipped: 0 }
      : { run: 0, completed: 0, failed: selected, skipped: 0 };
  }

  const symbols = line
    .slice(line.indexOf(testFile) + testFile.length)
    .replace(/\[[^\]]+\]/g, "")
    .replace(/\s+/g, "");
  const completed = countChars(symbols, ".");
  const failed = countChars(symbols, "F") + countChars(symbols, "E");
  const skipped = countChars(symbols, "s") + countChars(symbols, "S");
  const run = completed + failed + skipped + countChars(symbols, "x") + countChars(symbols, "X");
  return { run, completed, failed, skipped };
}

function countChars(text, char) {
  return [...text].filter((candidate) => candidate === char).length;
}

function renderReport({ generatedAt, overallPassed, results, startedAt }) {
  const lines = [
    "# HiveSight Slice Verification Report",
    "",
    `Generated: ${generatedAt.toISOString()}`,
    `Duration: ${generatedAt.getTime() - startedAt.getTime()} ms`,
    `Overall result: ${overallPassed ? "passed" : "failed"}`,
    ""
  ];

  const bddAreaSummaries = results.flatMap((result) => result.bddAreaSummaries ?? []);
  if (bddAreaSummaries.length) {
    lines.push("## BDD Feature Area Summary");
    lines.push("");
    for (const area of bddAreaSummaries) {
      lines.push(
        `- **${area.area}** (${area.capability}, ${area.seam}): ${area.completed}/${area.selected} complete; ${area.run} run; ${area.failed} failed; ${area.skipped} skipped; result ${area.result}.`
      );
    }
    lines.push("");
    lines.push(
      "`Selected` is the number of scenarios in the canonical feature tagged for that seam. `Complete` is the number that passed in the executed binding."
    );
    lines.push("");
  }

  lines.push(
    "## Checks",
    ""
  );

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
