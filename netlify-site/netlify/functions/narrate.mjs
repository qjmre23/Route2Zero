const jsonHeaders = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
  "x-content-type-options": "nosniff"
};

const BODY_LIMIT_BYTES = 5000;
const TEXT_LIMIT = 700;
const PROVIDER_TIMEOUT_MS = 12000;
const AUDIO_LIMIT_BYTES = 2500000;
const DEFAULT_VOICE_ID = "pNInz6obpgDQGcFmaJgB";
const DEFAULT_MODEL_ID = "eleven_flash_v2_5";
const requestBuckets = new Map();

function json(statusCode, body) {
  return { statusCode, headers: jsonHeaders, body: JSON.stringify(body) };
}

function boundedText(value, limit) {
  return String(value == null ? "" : value)
    .replace(/[\u0000-\u001f\u007f]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, limit);
}

function requestIsRateLimited(event) {
  const forwarded = String(event.headers?.["x-forwarded-for"] || "").split(",")[0].trim();
  const client = boundedText(event.headers?.["x-nf-client-connection-ip"] || forwarded, 80);
  if (!client) return false;
  const now = Date.now();
  const bucket = requestBuckets.get(client);
  if (!bucket || now - bucket.startedAt >= 60000) {
    requestBuckets.set(client, { startedAt: now, count: 1 });
    return false;
  }
  bucket.count += 1;
  return bucket.count > 40;
}

function safeIdentifier(value, fallback) {
  const identifier = boundedText(value, 80);
  return /^[A-Za-z0-9_-]{8,80}$/.test(identifier) ? identifier : fallback;
}

export async function handler(event) {
  if (event.httpMethod !== "POST") return json(405, { error: "Use POST." });
  if (Buffer.byteLength(event.body || "", "utf8") > BODY_LIMIT_BYTES) {
    return json(413, { error: "Request is too large." });
  }
  if (requestIsRateLimited(event)) {
    return json(429, { error: "Narration rate limit reached. Try again shortly." });
  }

  let payload;
  try {
    payload = JSON.parse(event.body || "{}");
  } catch {
    return json(400, { error: "Invalid JSON body." });
  }
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return json(400, { error: "The request body must be a JSON object." });
  }
  if (Object.keys(payload).some((key) => key !== "text")) {
    return json(400, { error: "The request contains unsupported fields." });
  }
  if (typeof payload.text !== "string" || !payload.text.trim()) {
    return json(400, { error: "Narration text is required." });
  }
  if (payload.text.length > TEXT_LIMIT) {
    return json(400, { error: "Narration text must be " + TEXT_LIMIT + " characters or fewer." });
  }

  const apiKey = String(process.env.ELEVENLABS_API_KEY || "").trim();
  if (!apiKey) {
    return json(503, {
      error: "Premium narration is not configured.",
      narration_status: "missing_api_key"
    });
  }

  const voiceId = safeIdentifier(process.env.ELEVENLABS_VOICE_ID, DEFAULT_VOICE_ID);
  const modelId = safeIdentifier(process.env.ELEVENLABS_MODEL_ID, DEFAULT_MODEL_ID);
  const text = boundedText(payload.text, TEXT_LIMIT);
  const endpoint = "https://api.elevenlabs.io/v1/text-to-speech/"
    + encodeURIComponent(voiceId)
    + "/stream?output_format=mp3_22050_32&enable_logging=false";
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), PROVIDER_TIMEOUT_MS);

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      signal: controller.signal,
      headers: {
        "content-type": "application/json",
        "xi-api-key": apiKey
      },
      body: JSON.stringify({
        text,
        model_id: modelId,
        voice_settings: {
          stability: 0.52,
          similarity_boost: 0.78,
          style: 0,
          use_speaker_boost: false,
          speed: 1.07
        }
      })
    });
    if (!response.ok) {
      return json(502, {
        error: "Premium narration is temporarily unavailable.",
        narration_status: "provider_http_" + response.status
      });
    }
    const audio = Buffer.from(await response.arrayBuffer());
    if (!audio.length || audio.length > AUDIO_LIMIT_BYTES) {
      return json(502, {
        error: "Premium narration returned an invalid audio response.",
        narration_status: "invalid_audio"
      });
    }
    return {
      statusCode: 200,
      isBase64Encoded: true,
      headers: {
        "content-type": "audio/mpeg",
        "cache-control": "private, max-age=86400",
        "x-content-type-options": "nosniff",
        "x-route2zero-narration": "elevenlabs"
      },
      body: audio.toString("base64")
    };
  } catch (error) {
    return json(502, {
      error: "Premium narration is temporarily unavailable.",
      narration_status: error?.name === "AbortError" ? "timeout" : "provider_error"
    });
  } finally {
    clearTimeout(timeout);
  }
}
