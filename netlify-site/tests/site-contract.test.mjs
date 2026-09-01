import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import test from "node:test";
import { readFile, stat } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { TOUR_NARRATION } from "../public/tour-audio.js";

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

test("phone tour reserves a visible stage and keeps controls usable", async () => {
  const [app, css] = await Promise.all([
    readFile(join(siteRoot, "public", "app.js"), "utf8"),
    readFile(join(siteRoot, "public", "styles.css"), "utf8")
  ]);

  assert.match(app, /function tourViewportBounds\(\)/);
  assert.match(app, /function tourScrollableAncestor\(element\)/);
  assert.match(app, /compactTourQuery\.matches \? 3 : 5/);
  assert.match(css, /grid-template-columns: repeat\(6, minmax\(0, 1fr\)\)/);
  assert.match(css, /body\.tour-running \{ scroll-padding-bottom: 46svh; \}/);
  assert.match(css, /body\.tour-running\.controls-open \.sidebar \{ padding-bottom: calc\(22px \+ min\(43svh, 244px\)\); \}/);
  assert.match(css, /height: 100dvh; max-height: 100dvh; overflow-y: auto; overscroll-behavior: contain/);
  assert.match(css, /\.tour-cursor\.label-left span/);
  assert.match(css, /@media \(max-width: 360px\), \(max-height: 620px\) and \(max-width: 700px\)/);
});

test("tour launch is discoverable and clears its invitation cursor", async () => {
  const [app, css, html, schema] = await Promise.all([
    readFile(join(siteRoot, "public", "app.js"), "utf8"),
    readFile(join(siteRoot, "public", "styles.css"), "utf8"),
    readFile(join(siteRoot, "public", "index.html"), "utf8"),
    readFile(join(siteRoot, "public", "templates", "field_observation.schema.json"), "utf8")
  ]);

  assert.match(html, /id="startWalkthroughHero"/);
  assert.match(app, /function startTourInvite\(\)/);
  assert.match(app, /function stopTourInvite\(\)/);
  assert.match(app, /els\.tourCursor\.classList\.add\("invite"\)/);
  assert.match(app, /els\.tourCursor\.classList\.remove\("invite"\)/);
  assert.match(app, /const target = \[els\.startWalkthroughTop, els\.startWalkthroughHero\]/);
  assert.match(css, /\.tour-cursor\.visible, \.tour-cursor\.invite/);
  assert.equal(JSON.parse(schema).$id, "https://route2zero.netlify.app/templates/field_observation.schema.json");
});

test("climate validation queue preserves scenario claim status", async () => {
  const app = await readFile(join(siteRoot, "public", "app.js"), "utf8");
  assert.match(app, /value\.includes\("climate"\) \|\| value\.includes\("efficiency"\) \|\| value\.includes\("emission"\)\) return row\.climate_claim_status \|\| "SCENARIO"/);
});

test("deterministic tour steps use committed MP3 narration while the live assistant stays dynamic", async () => {
  const recorded = TOUR_NARRATION.filter((entry) => !entry.dynamic);
  const dynamic = TOUR_NARRATION.filter((entry) => entry.dynamic);
  const manifest = JSON.parse(await readFile(join(siteRoot, "public", "audio", "tour", "manifest.json"), "utf8"));

  assert.equal(TOUR_NARRATION.length, 15);
  assert.equal(recorded.length, 14);
  assert.deepEqual(dynamic.map((entry) => entry.step), [13]);
  assert.equal(dynamic[0].audioSrc, undefined);
  assert.equal(manifest.provider, "ElevenLabs");
  assert.equal(manifest.deterministic_steps, 14);
  assert.deepEqual(manifest.dynamic_steps, [13]);

  for (const entry of recorded) {
    assert.match(entry.audioSrc, /^\/audio\/tour\/\d{2}-[a-z0-9-]+\.mp3$/);
    const filePath = join(siteRoot, "public", entry.audioSrc.slice(1));
    const [info, bytes] = await Promise.all([stat(filePath), readFile(filePath)]);
    const recordedFile = manifest.files.find((item) => item.step === entry.step);
    assert.ok(info.size > 10000, `${entry.audioSrc} is unexpectedly small`);
    assert.equal(recordedFile.audioSrc, entry.audioSrc);
    assert.equal(recordedFile.bytes, info.size);
    assert.equal(recordedFile.sha256, createHash("sha256").update(bytes).digest("hex"));
  }
});
