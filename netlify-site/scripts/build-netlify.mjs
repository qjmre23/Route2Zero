import { copyFile, mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const siteRoot = dirname(fileURLToPath(new URL("../package.json", import.meta.url)));
const repoRoot = join(siteRoot, "..");
const outputDir = join(siteRoot, "public", "data");

const files = [
  "route2zero_scores.csv",
  "route_cities.csv",
  "city_summary.csv",
  "route2zero_scores.geojson",
  "route_explanations.json"
];

await mkdir(outputDir, { recursive: true });

for (const file of files) {
  await copyFile(join(repoRoot, "data", "processed", file), join(outputDir, file));
  console.log(`Copied ${file}`);
}
