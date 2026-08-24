import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const siteRoot = dirname(fileURLToPath(new URL("../package.json", import.meta.url)));
const repoRoot = join(siteRoot, "..");

test("static first paint carries the canonical build summary", async () => {
  const [html, manifestText] = await Promise.all([
    readFile(join(siteRoot, "public", "index.html"), "utf8"),
    readFile(join(repoRoot, "data", "processed", "build_manifest.json"), "utf8")
  ]);
  const manifest = JSON.parse(manifestText);
  const report = manifest.pipeline_report;

  assert.match(html, new RegExp(`<strong id="routesMetric">${report.rows_processed.toLocaleString("en-US")}</strong>`));
  assert.match(html, new RegExp(`<strong id="validatedMetric">${report.current_validation_count}</strong>`));
  assert.match(html, new RegExp(`<strong id="robustMetric">${report.robust_priority_count}</strong>`));
  assert.match(html, new RegExp(`<strong id="scenarioMetric" class="metric-code">${manifest.default_scenario_id}</strong>`));
  assert.match(html, new RegExp(`<span id="heroRobustCount">${report.robust_priority_count}</span>`));
  assert.match(html, /0 field-confirmed active routes/);
});

test("judge view uses progressive evidence disclosure and no tour timer", async () => {
  const [html, app] = await Promise.all([
    readFile(join(siteRoot, "public", "index.html"), "utf8"),
    readFile(join(siteRoot, "public", "app.js"), "utf8")
  ]);

  assert.match(html, /id="decisionSummary"/);
  assert.match(html, /id="evidenceSignalDetails"/);
  assert.doesNotMatch(html, /walkthroughTime|1:25/);
  assert.doesNotMatch(app, /walkthroughTime|formatTourClock|updateTourClock|speechSynthesis/);
});
