const jsonHeaders = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
  "x-content-type-options": "nosniff"
};

function json(statusCode, body) {
  return { statusCode, headers: jsonHeaders, body: JSON.stringify(body) };
}

function finite(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function boundedText(value, limit) {
  return String(value == null ? "" : value).trim().slice(0, limit);
}

function normalizePayload(payload) {
  const scenarioInput = payload?.scenario || {};
  const routeInput = payload?.route || null;
  const portfolioInput = payload?.portfolio || {};
  const weightsInput = scenarioInput.weights || {};
  const weights = Object.fromEntries(["climate", "equity", "charging", "operator"].map((key) => [key, finite(weightsInput[key])]));
  const selectedRouteIds = Array.isArray(portfolioInput.selected_route_ids)
    ? portfolioInput.selected_route_ids.slice(0, 20).map((value) => boundedText(value, 80))
    : [];
  return {
    question: boundedText(payload?.question, 500),
    scenario: {
      scenario_id: boundedText(scenarioInput.scenario_id, 80),
      build_id: boundedText(scenarioInput.build_id, 80),
      policy_model_version: boundedText(scenarioInput.policy_model_version, 80),
      city_scope: boundedText(scenarioInput.city_scope, 100),
      historic_baseline_included: Boolean(scenarioInput.historic_baseline_included),
      weights
    },
    route: routeInput ? {
      route_id: boundedText(routeInput.route_id, 80),
      route_long_name: boundedText(routeInput.route_long_name, 240),
      live_rank: finite(routeInput.live_rank),
      live_priority_score: finite(routeInput.live_priority_score),
      evidence_grade: boundedText(routeInput.evidence_grade, 8),
      evidence_confidence: finite(routeInput.evidence_confidence),
      robustness_label: boundedText(routeInput.robustness_label, 80),
      top_10_probability: finite(routeInput.top_10_probability),
      rank_p10: finite(routeInput.rank_p10),
      rank_p90: finite(routeInput.rank_p90),
      climate_low_t_year: finite(routeInput.climate_low_t_year),
      climate_base_t_year: finite(routeInput.climate_base_t_year),
      climate_high_t_year: finite(routeInput.climate_high_t_year),
      equity_score: finite(routeInput.equity_score),
      charging_readiness_score: finite(routeInput.charging_readiness_score),
      operator_effective_score: finite(routeInput.operator_effective_score),
      highest_value_missing_evidence: boundedText(routeInput.highest_value_missing_evidence, 140),
      maximum_rank_swing: finite(routeInput.maximum_rank_swing),
      portfolio_flip_possible: Boolean(routeInput.portfolio_flip_possible),
      validation_priority_reason: boundedText(routeInput.validation_priority_reason, 300),
      claim_statuses: {
        climate: boundedText(routeInput.claim_statuses?.climate, 40),
        equity: boundedText(routeInput.claim_statuses?.equity, 40),
        charging: boundedText(routeInput.claim_statuses?.charging, 40),
        operator: boundedText(routeInput.claim_statuses?.operator, 40)
      }
    } : null,
    portfolio: {
      portfolio_scenario_id: boundedText(portfolioInput.portfolio_scenario_id, 80),
      mode: boundedText(portfolioInput.mode, 80),
      selected_route_ids: selectedRouteIds,
      constraints: {
        max_corridors: finite(portfolioInput.constraints?.max_corridors),
        minimum_evidence_grade: boundedText(portfolioInput.constraints?.minimum_evidence_grade, 8),
        minimum_equity_score: finite(portfolioInput.constraints?.minimum_equity_score)
      }
    }
  };
}

function deterministicActions(context) {
  const missing = context.route?.highest_value_missing_evidence?.replaceAll("_", " ") || "current route status and service";
  return [
    `Validate ${missing} with a named source and date.`,
    "Request utility evidence before making any claim about available charging capacity.",
    "Collect consent-based operator, depot and financing evidence before implementation."
  ];
}

function fallbackAnswer(context) {
  const route = context.route;
  if (!route) return "No corridor is available under the current scope. Restore the historic screening baseline or change the city filter before requesting an evidence brief.";
  const missing = route.highest_value_missing_evidence?.replaceAll("_", " ") || "current route validation";
  const swing = route.maximum_rank_swing == null ? "an unquantified" : `up to ${Math.round(route.maximum_rank_swing)}`;
  const portfolio = route.portfolio_flip_possible ? " and could change Phase-1 membership" : "";
  return `${route.route_long_name} is rank #${route.live_rank ?? "—"} under ${context.scenario.scenario_id || "the active scenario"}, with evidence grade ${route.evidence_grade || "unavailable"}. Validate ${missing} first because the deterministic evidence test shows ${swing} places of possible rank movement${portfolio}.`;
}

function responseBody(context, answer, source) {
  return {
    answer,
    actions: deterministicActions(context),
    source,
    scenario_id: context.scenario.scenario_id,
    build_id: context.scenario.build_id,
    route_id: context.route?.route_id || null,
    cited_fields: [
      "live_rank",
      "live_priority_score",
      "evidence_grade",
      "top_10_probability",
      "rank_p10",
      "rank_p90",
      "highest_value_missing_evidence",
      "maximum_rank_swing",
      "portfolio_flip_possible"
    ],
    llm_ranking_influence: false,
    policy_weights_human_controlled: true
  };
}

export async function handler(event) {
  if (event.httpMethod !== "POST") return json(405, { error: "Use POST." });
  if (Number(event.headers?.["content-length"] || 0) > 30000) return json(413, { error: "Request is too large." });

  let payload;
  try {
    payload = JSON.parse(event.body || "{}");
  } catch {
    return json(400, { error: "Invalid JSON body." });
  }
  const context = normalizePayload(payload);
  if (!context.question) return json(400, { error: "Question is required." });
  if (!context.scenario.scenario_id || !context.scenario.build_id) return json(400, { error: "Scenario ID and build ID are required." });

  const fallback = fallbackAnswer(context);
  const enabled = String(process.env.AI_EXPLANATIONS_ENABLED || "true").toLowerCase();
  const apiKey = String(process.env.ABSK_KEY || "").trim();
  const baseUrl = String(process.env.BASE_URL || "").trim().replace(/\/+$/, "");
  const model = String(process.env.MODEL || "").trim();
  if (!apiKey || !baseUrl || !model || !["1", "true", "yes"].includes(enabled)) {
    return json(200, responseBody(context, fallback, "deterministic_fallback"));
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);
  try {
    const evidence = JSON.stringify({ scenario: context.scenario, route: context.route, portfolio: context.portfolio });
    const response = await fetch(`${baseUrl}/chat/completions`, {
      method: "POST",
      signal: controller.signal,
      headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
      body: JSON.stringify({
        model,
        messages: [
          {
            role: "system",
            content: "You are Route2Zero's evidence-triage assistant. Use only the supplied structured evidence. Never invent a number, source, current service claim, settlement claim, utility-capacity claim or operator fact. Never recommend procurement as an automatic consequence of rank. Explain in no more than three short sentences for a city official. The policy weights and ranks are human-controlled/deterministic and cannot be edited by you."
          },
          {
            role: "user",
            content: `Question: ${context.question}\nStructured evidence: ${evidence}`
          }
        ],
        max_tokens: 190,
        temperature: 0.2
      })
    });
    if (!response.ok) return json(200, responseBody(context, fallback, "deterministic_fallback"));
    const data = await response.json();
    const answer = boundedText(data?.choices?.[0]?.message?.content, 1200);
    return json(200, responseBody(context, answer || fallback, answer ? "netlify_function_api" : "deterministic_fallback"));
  } catch {
    return json(200, responseBody(context, fallback, "deterministic_fallback"));
  } finally {
    clearTimeout(timeout);
  }
}
