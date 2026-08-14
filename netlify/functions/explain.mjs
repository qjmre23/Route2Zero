const jsonHeaders = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store"
};

function json(statusCode, body) {
  return {
    statusCode,
    headers: jsonHeaders,
    body: JSON.stringify(body)
  };
}

function fallbackAnswer(facts) {
  if (!facts) {
    return "No ranked routes were available for the current filters. The dashboard scores remain deterministic, and operator readiness is still a placeholder.";
  }
  return `Based on the current filters, the leading routes are ${facts}. These are deterministic weighted scores; operator readiness remains a placeholder.`;
}

export async function handler(event) {
  if (event.httpMethod !== "POST") {
    return json(405, { error: "Use POST." });
  }

  let payload;
  try {
    payload = JSON.parse(event.body || "{}");
  } catch {
    return json(400, { error: "Invalid JSON body." });
  }

  const question = String(payload.question || "").trim().slice(0, 500);
  const facts = String(payload.facts || "").trim().slice(0, 1200);
  const fallback = fallbackAnswer(facts);

  if (!question) {
    return json(400, { error: "Question is required." });
  }

  const enabled = String(process.env.AI_EXPLANATIONS_ENABLED || "true").toLowerCase();
  const apiKey = String(process.env.ABSK_KEY || "").trim();
  const baseUrl = String(process.env.BASE_URL || "").trim().replace(/\/+$/, "");
  const model = String(process.env.MODEL || "").trim();

  if (!apiKey || !baseUrl || !model || !["1", "true", "yes"].includes(enabled)) {
    return json(200, { answer: fallback, source: "deterministic_fallback" });
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);

  try {
    const response = await fetch(`${baseUrl}/chat/completions`, {
      method: "POST",
      signal: controller.signal,
      headers: {
        "authorization": `Bearer ${apiKey}`,
        "content-type": "application/json"
      },
      body: JSON.stringify({
        model,
        messages: [
          {
            role: "user",
            content: `Answer in no more than three short sentences for a city official. Question: ${question}. Ranked facts: ${facts}. Do not add external facts, change ranking, or call proxies measurements. Mention that operator readiness is a placeholder.`
          }
        ],
        max_tokens: 150,
        temperature: 0.3
      })
    });

    if (!response.ok) {
      return json(200, { answer: fallback, source: "deterministic_fallback" });
    }

    const data = await response.json();
    const answer = data?.choices?.[0]?.message?.content?.trim();
    return json(200, {
      answer: answer || fallback,
      source: answer ? "netlify_function_api" : "deterministic_fallback"
    });
  } catch {
    return json(200, { answer: fallback, source: "deterministic_fallback" });
  } finally {
    clearTimeout(timeout);
  }
}
