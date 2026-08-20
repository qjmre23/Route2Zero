import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { handler } from "../netlify/functions/explain.mjs";

const appSource = readFileSync(new URL("../public/app.js", import.meta.url), "utf8");
const styleSource = readFileSync(new URL("../public/styles.css", import.meta.url), "utf8");

const payload = {
  question: "What should the city validate first?",
  scenario: {
    scenario_id: "scn-test-001",
    build_id: "r2z-test-001",
    weights: { climate: 0.4, equity: 0.3, charging: 0.15, operator: 0.15 }
  },
  route: {
    route_id: "route-test-001",
    route_long_name: "Test corridor",
    live_rank: 1,
    live_priority_score: 80,
    evidence_grade: "C",
    maximum_rank_swing: 5,
    highest_value_missing_evidence: "current_service_validation"
  },
  portfolio: { selected_route_ids: [], constraints: {} }
};

function event() {
  return { httpMethod: "POST", headers: {}, body: JSON.stringify(payload) };
}

function responseJson(response) {
  return JSON.parse(response.body);
}

async function withProviderEnvironment(values, callback) {
  const names = ["ABSK_KEY", "BASE_URL", "MODEL", "AI_EXPLANATIONS_ENABLED"];
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

test("uses a complete chat-completions endpoint without duplicating its path", { concurrency: false }, async () => {
  const originalFetch = globalThis.fetch;
  let requestedUrl = "";
  globalThis.fetch = async (url) => {
    requestedUrl = String(url);
    return new Response(JSON.stringify({ choices: [{ message: { content: "Test corridor is rank 1 with priority 80." } }] }), { status: 200 });
  };
  try {
    const response = await withProviderEnvironment({
      ABSK_KEY: "test-key",
      BASE_URL: "https://provider.example/v1/chat/completions",
      MODEL: "test-model",
      AI_EXPLANATIONS_ENABLED: "true"
    }, () => handler(event()));
    const body = responseJson(response);
    assert.equal(requestedUrl, "https://provider.example/v1/chat/completions");
    assert.equal(body.source, "netlify_function_api");
    assert.equal(body.ai_status, "ok");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("accepts array-form provider content", { concurrency: false }, async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({
    choices: [{ message: { content: [{ type: "text", text: "Test corridor is rank 1." }] } }]
  }), { status: 200 });
  try {
    const response = await withProviderEnvironment({
      ABSK_KEY: "test-key",
      BASE_URL: "https://provider.example/v1",
      MODEL: "test-model",
      AI_EXPLANATIONS_ENABLED: "true"
    }, () => handler(event()));
    assert.equal(responseJson(response).source, "netlify_function_api");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("does not treat named Phase-1 and top-10 labels as unsupported numeric claims", { concurrency: false }, async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({
    choices: [{ message: { content: "Keep this corridor in the Phase-1 review because it remains a top-10 candidate." } }]
  }), { status: 200 });
  try {
    const response = await withProviderEnvironment({
      ABSK_KEY: "test-key",
      BASE_URL: "https://provider.example/v1",
      MODEL: "test-model",
      AI_EXPLANATIONS_ENABLED: "true"
    }, () => handler(event()));
    assert.equal(responseJson(response).source, "netlify_function_api");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("reports provider failures without exposing configuration values", { concurrency: false }, async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response("rate limited", { status: 429 });
  try {
    const response = await withProviderEnvironment({
      ABSK_KEY: "test-key",
      BASE_URL: "https://provider.example/v1",
      MODEL: "test-model",
      AI_EXPLANATIONS_ENABLED: "true"
    }, () => handler(event()));
    const body = responseJson(response);
    assert.equal(body.source, "deterministic_fallback");
    assert.equal(body.ai_status, "provider_http_429");
    assert.doesNotMatch(response.body, /test-key|provider\.example|test-model/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("renders one high-contrast assistant paragraph without repeated action bullets", () => {
  const renderFunction = appSource.slice(
    appSource.indexOf("function renderAssistantAnswer"),
    appSource.indexOf("async function askQuestion")
  );
  assert.match(renderFunction, /answerText\.innerHTML = `<p>\$\{answer\}<\/p>`/);
  assert.doesNotMatch(renderFunction, /<ul>|data\.actions/);
  assert.match(styleSource, /\.ask-panel \.answer p \{[^}]*color: #f5fffc;/);
});
