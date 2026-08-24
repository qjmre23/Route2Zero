import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "file:///C:/Users/LENOVO/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";

const root = path.resolve(import.meta.dirname, "..");
const output = path.join(root, "output", "submission", "assets", "2.1");
const legacyOutput = path.join(root, "tmp", "route2zero-submission", "screenshots");
const baseUrl = process.env.ROUTE2ZERO_PREVIEW_URL || "http://127.0.0.1:8899/";

console.log("Preparing screenshot output");
await fs.mkdir(output, { recursive: true });
await fs.mkdir(legacyOutput, { recursive: true });

const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_BROWSER_PATH || "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  args: ["--no-sandbox", "--disable-gpu"],
});
console.log("Browser launched");
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
const failures = [];

page.on("pageerror", (error) => failures.push(`page: ${error.message}`));
page.on("console", (message) => {
  if (message.type() === "error") failures.push(`console: ${message.text()}`);
});

async function save(name, locator) {
  const target = locator || page;
  const file = path.join(output, name);
  await target.screenshot({ path: file, animations: "disabled" });
  await fs.copyFile(file, path.join(legacyOutput, name));
}

await page.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: 20000 });
console.log("Page loaded");
await page.waitForFunction(() => document.querySelector("#routesMetric")?.textContent?.includes("1,522"));
await page.waitForTimeout(2500);

await save("overview.png");
await page.locator("#mapLayer").selectOption("typology");
await page.waitForTimeout(350);
await save("map.png", page.locator("#corridor-map"));
await page.locator("#mapLayer").selectOption("equity");
await page.waitForTimeout(350);
await save("equity-map.png", page.locator("#corridor-map"));
await page.locator("#mapLayer").selectOption("priority");
await page.waitForTimeout(350);
await save("route-lens.png", page.locator("#route-lens"));
await save("feasibility.png", page.locator("#feasibility"));
await save("scenario-lab.png", page.locator("#scenario-lab"));
await save("portfolio.png", page.locator("#phase1-portfolio"));
await save("evidence-ai.png", page.locator("#evidence-ai"));

await page.locator("#methodDetails summary").click();
await page.waitForTimeout(250);
await save("method-sources.png", page.locator("#method-sources"));

await page.locator("#routeFinder").selectOption("LTFRB_PUJ1034");
await page.locator("#mapLayer").selectOption("validation");
await page.waitForFunction(() => document.querySelector("#routeName")?.textContent?.includes("Alabang"));
await page.waitForTimeout(2500);
await save("current-validation.png", page.locator("#route-lens"));
await save("validation-map.png", page.locator("#corridor-map"));

const metrics = await page.locator(".metrics").innerText();
const validation = await page.locator("#validationEvidence").innerText();
const roadStatus = await page.locator("#roadStatus").innerText();
const claimBadges = await page.locator(".claim-badge").count();

const mobile = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
await mobile.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: 20000 });
await mobile.waitForFunction(() => document.querySelector("#routesMetric")?.textContent?.includes("1,522"));
await mobile.waitForTimeout(500);
const mobileFile = path.join(output, "mobile-overview.png");
await mobile.screenshot({ path: mobileFile, animations: "disabled" });
await fs.copyFile(mobileFile, path.join(legacyOutput, "mobile-overview.png"));

await browser.close();

if (!validation.includes("OSM relation 11521406") || !validation.includes("2026-08-24")) {
  throw new Error(`Current validation evidence was not visible: ${validation}`);
}
if (!roadStatus.includes("Observed OSM member-way geometry")) {
  throw new Error(`Observed road geometry was not active: ${roadStatus}`);
}
if (claimBadges < 10) {
  throw new Error(`Expected visible claim badges; found ${claimBadges}`);
}
if (failures.length) {
  throw new Error(`Browser errors:\n${failures.join("\n")}`);
}

console.log(JSON.stringify({ metrics, validation, roadStatus, claimBadges, output }, null, 2));
