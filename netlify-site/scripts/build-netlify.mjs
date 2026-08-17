import { copyFile, mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const siteRoot = dirname(fileURLToPath(new URL("../package.json", import.meta.url)));
const repoRoot = join(siteRoot, "..");
const outputDir = join(siteRoot, "public", "data");
const mapboxToken = String(process.env.MAPBOX_TOKEN || "").trim();

if (!mapboxToken) {
  throw new Error("MAPBOX_TOKEN is required. Add it to Netlify with Builds scope before deploying.");
}

const files = [
  "route2zero_scores.csv",
  "route_cities.csv",
  "city_summary.csv",
  "route2zero_scores.geojson",
  "route_explanations.json"
];

await mkdir(outputDir, { recursive: true });
await writeFile(
  join(siteRoot, "public", "config.js"),
  `window.ROUTE2ZERO_CONFIG = ${JSON.stringify({ mapboxToken })};\n`,
  "utf8"
);
console.log("Generated public Mapbox runtime configuration");

for (const file of files) {
  await copyFile(join(repoRoot, "data", "processed", file), join(outputDir, file));
  console.log(`Copied ${file}`);
}
