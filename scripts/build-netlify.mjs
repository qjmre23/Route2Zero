import { copyFile, mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(new URL("../package.json", import.meta.url)));
const outputDir = join(root, "public", "data");

const files = [
  "route2zero_scores.csv",
  "route_cities.csv",
  "city_summary.csv",
  "route2zero_scores.geojson",
  "route_explanations.json"
];

await mkdir(outputDir, { recursive: true });

for (const file of files) {
  await copyFile(join(root, "data", "processed", file), join(outputDir, file));
  console.log(`Copied ${file}`);
}
