import assert from "node:assert/strict";
import test from "node:test";

import { handler } from "../netlify/functions/narrate.mjs";

function event(body = { text: "Welcome to Route2Zero." }) {
  return {
    httpMethod: "POST",
    headers: {},
    body: JSON.stringify(body)
  };
}

async function withEnvironment(values, callback) {
  const names = ["ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID", "ELEVENLABS_MODEL_ID"];
  const before = Object.fromEntries(names.map((name) => [name, process.env[name]]));
  Object.assign(process.env, values);
  try {
    return await callback();
  } finally {
    for (const name of names) {
      if (before[name] == null) delete process.env[name];
      else process.env[name] = before[name];
    }
  }
}

test("requires POST and bounded narration text", async () => {
  const method = await handler({ ...event(), httpMethod: "GET" });
  assert.equal(method.statusCode, 405);
  const unsupported = await handler(event({ text: "Hello", voice: "custom" }));
  assert.equal(unsupported.statusCode, 400);
  const tooLong = await handler(event({ text: "a".repeat(701) }));
  assert.equal(tooLong.statusCode, 400);
});

test("reports missing server narration configuration without exposing secrets", async () => {
  const response = await withEnvironment({ ELEVENLABS_API_KEY: "" }, () => handler(event()));
  assert.equal(response.statusCode, 503);
  assert.equal(JSON.parse(response.body).narration_status, "missing_api_key");
});

test("calls the ElevenLabs streaming endpoint and returns base64 audio", { concurrency: false }, async () => {
  const originalFetch = globalThis.fetch;
  let requestUrl = "";
  let requestOptions;
  globalThis.fetch = async (url, options) => {
    requestUrl = String(url);
    requestOptions = options;
    return new Response(new Uint8Array([73, 68, 51, 4, 0, 0]), {
      status: 200,
      headers: { "content-type": "audio/mpeg" }
    });
  };
  try {
    const response = await withEnvironment({
      ELEVENLABS_API_KEY: "server-secret",
      ELEVENLABS_VOICE_ID: "pNInz6obpgDQGcFmaJgB",
      ELEVENLABS_MODEL_ID: "eleven_flash_v2_5"
    }, () => handler(event()));
    assert.equal(response.statusCode, 200);
    assert.equal(response.isBase64Encoded, true);
    assert.equal(response.headers["content-type"], "audio/mpeg");
    assert.match(requestUrl, /\/v1\/text-to-speech\/pNInz6obpgDQGcFmaJgB\/stream/);
    assert.equal(requestOptions.headers["xi-api-key"], "server-secret");
    assert.equal(JSON.parse(requestOptions.body).model_id, "eleven_flash_v2_5");
    assert.doesNotMatch(response.body, /server-secret/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("sanitizes provider failures", { concurrency: false }, async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response("provider secret detail", { status: 429 });
  try {
    const response = await withEnvironment({
      ELEVENLABS_API_KEY: "server-secret"
    }, () => handler(event()));
    assert.equal(response.statusCode, 502);
    assert.equal(JSON.parse(response.body).narration_status, "provider_http_429");
    assert.doesNotMatch(response.body, /server-secret|provider secret detail/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
