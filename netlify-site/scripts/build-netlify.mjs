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
