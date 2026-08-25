import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { TOUR_NARRATION } from "../public/tour-audio.js";

const siteRoot = dirname(fileURLToPath(new URL("../package.json", import.meta.url)));
const publicRoot = join(siteRoot, "public");
const endpoint = String(process.env.TOUR_NARRATION_ENDPOINT || "https://route2zero.netlify.app/.netlify/functions/narrate").trim();
const providerKey = String(process.env.ELEVENLABS_API_KEY || "").trim();
const providerVoice = String(process.env.ELEVENLABS_VOICE_ID || "pNInz6obpgDQGcFmaJgB").trim();
const providerModel = String(process.env.ELEVENLABS_MODEL_ID || "eleven_flash_v2_5").trim();
const stepArgument = process.argv.find((value) => value.startsWith("--steps="));
const selectedSteps = stepArgument
  ? new Set(stepArgument.slice("--steps=".length).split(",").map(Number).filter(Number.isFinite))
  : null;
const manifestPath = join(publicRoot, "audio", "tour", "manifest.json");
let previous = { files: [] };
try {
  previous = JSON.parse(await readFile(manifestPath, "utf8"));
} catch {}
const generatedByStep = new Map((previous.files || []).map((entry) => [entry.step, entry]));

async function requestNarration(text) {
  if (!providerKey) {
    return fetch(endpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text })
    });
  }
  return fetch(
    `https://api.elevenlabs.io/v1/text-to-speech/${encodeURIComponent(providerVoice)}/stream?output_format=mp3_22050_32&enable_logging=false`,
    {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "xi-api-key": providerKey
      },
      body: JSON.stringify({
        text,
        model_id: providerModel,
        voice_settings: {
          stability: 0.52,
          similarity_boost: 0.78,
          style: 0,
          use_speaker_boost: false,
          speed: 1.07
        }
      })
    }
  );
}

for (const entry of TOUR_NARRATION.filter((item) => !item.dynamic && (!selectedSteps || selectedSteps.has(item.step)))) {
  const response = await requestNarration(entry.text);
  if (!response.ok) {
    throw new Error(`Narration step ${entry.step} failed with HTTP ${response.status}: ${await response.text()}`);
  }
  const bytes = Buffer.from(await response.arrayBuffer());
  if (!String(response.headers.get("content-type") || "").startsWith("audio/") || bytes.length < 10000) {
    throw new Error(`Narration step ${entry.step} returned invalid audio.`);
  }
  const target = join(publicRoot, entry.audioSrc.replace(/^\//, ""));
  await mkdir(dirname(target), { recursive: true });
  await writeFile(target, bytes);
  generatedByStep.set(entry.step, {
    step: entry.step,
    key: entry.key,
    audioSrc: entry.audioSrc,
    bytes: bytes.length,
    sha256: createHash("sha256").update(bytes).digest("hex")
  });
}

const generated = TOUR_NARRATION
  .filter((item) => !item.dynamic)
  .map((item) => generatedByStep.get(item.step));
if (generated.some((entry) => !entry)) {
  throw new Error("The tour narration manifest is incomplete.");
}
await writeFile(manifestPath, `${JSON.stringify({
  provider: "ElevenLabs",
  deterministic_steps: generated.length,
  dynamic_steps: TOUR_NARRATION.filter((item) => item.dynamic).map((item) => item.step),
  generated_at_utc: new Date().toISOString(),
  files: generated
}, null, 2)}\n`, "utf8");

console.log(`Saved ${generated.length} recorded tour narrations to ${dirname(manifestPath)}`);
