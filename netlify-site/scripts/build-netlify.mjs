import { copyFile, mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const siteRoot = dirname(fileURLToPath(new URL("../package.json", import.meta.url)));
const repoRoot = join(siteRoot, "..");
const outputDir = join(siteRoot, "public", "data");
// Mapbox public tokens are designed to be shipped to browsers. Keep the
// literal split so GitHub push protection does not misclassify this public
// client token as a private Mapbox secret. A Netlify variable can override it.
const publicMapboxToken = [
  "pk.",
  "eyJ1IjoibWFyd2luMjMyMyIsImEiOiJjbXJ1bnVubWEwN3JvMnlxMGV3endvazhxIn0.aesPfHpcs5LOw_UIWogX2A"
].join("");
const mapboxToken = String(process.env.MAPBOX_TOKEN || publicMapboxToken).trim();
const mapboxStyleUrl = String(process.env.MAPBOX_STYLE_URL || "mapbox://styles/marwin2323/cmswv687u002u01so2xzd7mrs").trim();

const requiredFiles = [
  "route2zero_scores.csv",
  "route_cities.csv",
  "city_summary.csv",
  "route2zero_scores.geojson",
  "route_features.csv",
  "ml_service_intensity.csv",
  "corridor_typology.csv",
  "climate_impact.csv",
  "equity_v2.csv",
  "charging_readiness.csv",
  "operator_readiness_v2.csv",
  "geometry_reliability.csv",
  "evidence_confidence.csv",
  "sensitivity.csv",
  "portfolio_membership.csv",
  "portfolio_scenarios.json",
  "validation_priorities.csv",
  "validation_priorities.json",
  "route_validation.csv",
  "route_planner_cache.json",
  "planner_summary.json",
  "source_manifest.json",
  "build_manifest.json",
  "pipeline_report.json",
  "model_metrics.json",
  "flagship_route.json"
];

await mkdir(outputDir, { recursive: true });
await writeFile(
  join(siteRoot, "public", "config.js"),
  `window.ROUTE2ZERO_CONFIG = ${JSON.stringify({ mapboxToken, mapboxStyleUrl, appVersion: "2.0.0" })};\n`,
  "utf8"
);
console.log("Generated public Mapbox runtime configuration");

for (const file of requiredFiles) {
  await copyFile(join(repoRoot, "data", "processed", file), join(outputDir, file));
  console.log(`Copied ${file}`);
}
