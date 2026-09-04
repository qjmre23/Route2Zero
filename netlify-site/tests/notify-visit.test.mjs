import assert from "node:assert/strict";
import test from "node:test";

import { handler } from "../netlify/functions/notify-visit.mjs";

function event(body = { path: "/#overview", locale: "en-US", viewport: "390x844" }, headers = {}) {
  return {
    httpMethod: "POST",
    headers,
    body: JSON.stringify(body)
  };
}

async function withEnvironment(values, callback) {
  const names = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"];
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

test("requires POST and rejects malformed payloads", async () => {
  const method = await handler({ ...event(), httpMethod: "GET" });
  assert.equal(method.statusCode, 405);
  const unsupported = await handler(event({ path: "/", extra: "nope" }));
  assert.equal(unsupported.statusCode, 400);
});

test("does nothing when Telegram configuration is absent", { concurrency: false }, async () => {
  const response = await withEnvironment({ TELEGRAM_BOT_TOKEN: "", TELEGRAM_CHAT_ID: "" }, () => handler(event({}, { "x-forwarded-for": "test-missing-config" })));
  assert.equal(response.statusCode, 503);
  assert.equal(JSON.parse(response.body).notification_status, "not_configured");
});

test("sends a bounded site-open message through the server-side Telegram API", { concurrency: false }, async () => {
  const originalFetch = globalThis.fetch;
  let requestUrl = "";
  let requestOptions;
  globalThis.fetch = async (url, options) => {
    requestUrl = String(url);
    requestOptions = options;
    return new Response(JSON.stringify({ ok: true }), { status: 200 });
  };
  try {
    const response = await withEnvironment({
      TELEGRAM_BOT_TOKEN: "test-token",
      TELEGRAM_CHAT_ID: "7474049767"
    }, () => handler(event({ path: "/#evidence", locale: "en-PH", viewport: "1440x900" }, { "x-forwarded-for": "test-configured" })));
    assert.equal(response.statusCode, 204);
    assert.equal(response.headers["x-route2zero-telegram-status"], "sent");
    assert.equal(requestUrl, "https://api.telegram.org/bottest-token/sendMessage");
    const body = JSON.parse(requestOptions.body);
    assert.equal(body.chat_id, "7474049767");
    assert.match(body.text, /Route2Zero site opened/);
    assert.match(body.text, /Page: \/#evidence/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("surfaces Telegram provider failures without exposing credentials", { concurrency: false }, async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response("bot token detail", { status: 401 });
  try {
    const response = await withEnvironment({
      TELEGRAM_BOT_TOKEN: "server-secret",
      TELEGRAM_CHAT_ID: "7474049767"
    }, () => handler(event({ path: "/", locale: "en-US", viewport: "1280x720" }, { "x-forwarded-for": "test-provider-failure" })));
    assert.equal(response.statusCode, 502);
    assert.equal(JSON.parse(response.body).notification_status, "provider_http_401");
    assert.doesNotMatch(response.body, /server-secret|bot token detail/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
