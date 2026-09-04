const jsonHeaders = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
  "x-content-type-options": "nosniff"
};

const BODY_LIMIT_BYTES = 3000;
const requestBuckets = new Map();

function json(statusCode, body) {
  return { statusCode, headers: jsonHeaders, body: JSON.stringify(body) };
}

function noContent(statusCode = 204, notificationStatus = "disabled") {
  return {
    statusCode,
    headers: {
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
      "x-route2zero-telegram-status": notificationStatus
    },
    body: ""
  };
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
  const client = boundedText(event.headers?.["x-nf-client-connection-ip"] || forwarded || "anonymous", 80);
  const now = Date.now();
  const bucket = requestBuckets.get(client);
  if (!bucket || now - bucket.startedAt >= 300000) {
    requestBuckets.set(client, { startedAt: now, count: 1 });
    return false;
  }
  bucket.count += 1;
  return bucket.count > 3;
}

function parsePayload(event) {
  if (Buffer.byteLength(event.body || "", "utf8") > BODY_LIMIT_BYTES) return { error: "Request is too large." };
  let payload;
  try {
    payload = JSON.parse(event.body || "{}");
  } catch {
    return { error: "Invalid JSON body." };
  }
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) return { error: "The request body must be a JSON object." };
  const allowed = new Set(["path", "locale", "viewport"]);
  if (Object.keys(payload).some((key) => !allowed.has(key))) return { error: "The request contains unsupported fields." };
  return {
    value: {
      path: boundedText(payload.path, 120) || "/",
      locale: boundedText(payload.locale, 40) || "unknown",
      viewport: boundedText(payload.viewport, 30) || "unknown"
    }
  };
}

export async function handler(event) {
  if (event.httpMethod !== "POST") return json(405, { error: "Use POST." });
  if (requestIsRateLimited(event)) return noContent(429, "rate_limited");

  const parsed = parsePayload(event);
  if (parsed.error) return json(400, { error: parsed.error });

  const botToken = String(process.env.TELEGRAM_BOT_TOKEN || "").trim();
  const chatId = String(process.env.TELEGRAM_CHAT_ID || "").trim();
  if (!botToken || !chatId) return json(503, { error: "Telegram notification is not configured.", notification_status: "not_configured" });

  const { path, locale, viewport } = parsed.value;
  const message = [
    "Route2Zero site opened",
    `Time: ${new Date().toISOString()}`,
    `Page: ${path}`,
    `Locale: ${locale}`,
    `Viewport: ${viewport}`
  ].join("\n");
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);

  try {
    const response = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
      method: "POST",
      signal: controller.signal,
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ chat_id: chatId, text: message, disable_web_page_preview: true })
    });
    if (!response.ok) {
      console.error("Telegram visit notification failed", response.status);
      return json(502, { error: "Telegram notification failed.", notification_status: "provider_http_" + response.status });
    }
  } catch (error) {
    console.error("Telegram visit notification failed", error?.name === "AbortError" ? "timeout" : "request error");
    return json(502, { error: "Telegram notification failed.", notification_status: error?.name === "AbortError" ? "timeout" : "provider_error" });
  } finally {
    clearTimeout(timeout);
  }
  return noContent(204, "sent");
}
